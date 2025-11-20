"""
Bybit API Client
Обёртка для взаимодействия с Bybit API (REST + WebSocket)
"""

import asyncio
import hashlib
import hmac
import time
import socket
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

import ccxt.async_support as ccxt
import aiohttp
from aiohttp import ClientTimeout, TCPConnector
from loguru import logger
import json
import re

# Условный импорт для поддержки как пакета, так и прямого запуска
try:
    from .cache_manager import get_cache_manager
except ImportError:
    from cache_manager import get_cache_manager


def parse_ccxt_error(error: Exception) -> Dict[str, Any]:
    """
    Парсит ошибки CCXT, которые могут содержать JSON строки вида:
    'bybit {"retCode":10003,"retMsg":"API key is invalid.",...}'
    
    Returns:
        {
            "retCode": int or None,
            "retMsg": str,
            "parsed": bool,
            "original_error": str
        }
    """
    error_str = str(error)
    
    # Ищем JSON в строке ошибки (формат: "bybit {...}" или просто "{...}")
    json_match = re.search(r'\{[^{}]*"retCode"[^{}]*\}', error_str)
    
    if json_match:
        try:
            json_str = json_match.group(0)
            error_data = json.loads(json_str)
            
            return {
                "retCode": error_data.get("retCode"),
                "retMsg": error_data.get("retMsg", "Unknown error"),
                "parsed": True,
                "original_error": error_str
            }
        except (json.JSONDecodeError, KeyError) as e:
            logger.debug(f"Failed to parse JSON from error: {e}")
    
    # Если не нашли JSON, возвращаем оригинальную ошибку
    return {
        "retCode": None,
        "retMsg": error_str,
        "parsed": False,
        "original_error": error_str
    }


class BybitClient:
    """Клиент для работы с Bybit API"""
    
    # Кеш тикеров (класс-уровень для всех экземпляров)
    _tickers_cache: Dict[str, List[Dict[str, Any]]] = {}
    _cache_timestamps: Dict[str, datetime] = {}
    _cache_ttl = timedelta(seconds=30)  # 30 секунд кеш
    
    def __init__(self, api_key: str, api_secret: str, testnet: bool = False):
        """
        Инициализация клиента
        
        Args:
            api_key: API ключ Bybit
            api_secret: API секрет Bybit
            testnet: Использовать testnet (default: False)
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        
        # Инициализация CCXT exchange с улучшенными настройками для DNS/сети
        self.exchange = ccxt.bybit({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
            'timeout': 30000,  # 30 секунд таймаут
            'options': {
                'defaultType': 'spot',  # По умолчанию spot
                'testnet': testnet
            },
            # Улучшенные настройки для сетевых запросов
            'headers': {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'
            }
        })
        
        # Создаём aiohttp сессию с улучшенными настройками DNS и таймаутов
        self._http_session: Optional[aiohttp.ClientSession] = None
        
        logger.info(f"Bybit client initialized ({'testnet' if testnet else 'mainnet'})")
    
    async def validate_api_credentials(self) -> Dict[str, Any]:
        """
        Валидация API credentials при старте системы.
        
        Returns:
            {
                "valid": bool,
                "permissions": List[str],  # ["READ", "WRITE"] или ошибка
                "accounts": List[str],     # Доступные типы счетов
                "error": Optional[str]
            }
        
        Raises:
            Exception: Если API ключи невалидные (fail-fast)
        """
        logger.info("🔍 Validating Bybit API credentials...")
        
        try:
            # Простой тест: получаем server time (не требует auth)
            test_ticker = await self.exchange.fetch_ticker('BTC/USDT')
            if not test_ticker:
                raise Exception("API не вернул данные для BTC/USDT")
            
            logger.info("✅ API доступен (public endpoints)")
            
            # Тест authenticated endpoint: get account balance
            try:
                balance = await self.exchange.fetch_balance()
                logger.info("✅ API Key валиден (authenticated endpoints работают)")
                
                # Проверяем какие балансы доступны
                available_accounts = []
                if balance.get('free'):
                    available_accounts.append("SPOT")
                if balance.get('total'):
                    available_accounts.append("UNIFIED")
                
                return {
                    "valid": True,
                    "permissions": ["READ", "WRITE"],
                    "accounts": available_accounts,
                    "error": None
                }
                
            except Exception as auth_error:
                error_msg = str(auth_error)
                
                # Проверяем специфичные ошибки
                if "10003" in error_msg or "invalid" in error_msg.lower():
                    logger.error("❌ API Key INVALID (retCode 10003)")
                    raise Exception(
                        "Bybit API Key is INVALID! "
                        "Please check your BYBIT_API_KEY and BYBIT_API_SECRET in GitHub Secrets. "
                        f"Error: {error_msg}"
                    )
                elif "10004" in error_msg or "permission" in error_msg.lower():
                    logger.error("❌ API Key has NO PERMISSIONS (retCode 10004)")
                    raise Exception(
                        "Bybit API Key has insufficient permissions! "
                        "Please enable READ permissions on Bybit API Management page. "
                        f"Error: {error_msg}"
                    )
                elif "10005" in error_msg or "ip" in error_msg.lower():
                    logger.error("❌ IP NOT WHITELISTED (retCode 10005)")
                    raise Exception(
                        "IP address is not whitelisted! "
                        "Please add your server's IP to Bybit API whitelist. "
                        f"Error: {error_msg}"
                    )
                else:
                    logger.error(f"❌ API authentication failed: {error_msg}")
                    raise Exception(f"Bybit API authentication failed: {error_msg}")
                    
        except Exception as e:
            logger.error(f"❌ API validation failed: {e}")
            raise
    
    async def _get_http_session(self) -> aiohttp.ClientSession:
        """Получить или создать aiohttp сессию с улучшенными настройками DNS"""
        if self._http_session is None or self._http_session.closed:
            # DNS resolver с fallback на публичные DNS серверы
            resolver = aiohttp.resolver.DefaultResolver()
            
            # TCP connector с улучшенными настройками
            connector = TCPConnector(
                resolver=resolver,
                limit=100,  # Максимум соединений
                limit_per_host=30,  # Максимум соединений на хост
                ttl_dns_cache=300,  # Кеш DNS на 5 минут
                use_dns_cache=True,
                keepalive_timeout=30,
                enable_cleanup_closed=True
            )
            
            # Таймауты: connect (DNS + TCP + SSL), read, total
            timeout = ClientTimeout(
                total=60,  # Общий таймаут 60 секунд
                connect=30,  # 30 секунд на подключение (включая DNS)
                sock_read=30  # 30 секунд на чтение
            )
            
            self._http_session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'
                }
            )
        
        return self._http_session
    
    async def get_market_overview(self, market_type: str = "both") -> Dict[str, Any]:
        """
        Получить обзор всего рынка
        
        Args:
            market_type: "spot", "futures", или "both"
            
        Returns:
            Детальный обзор рынка включая sentiment, топ движения, условия
        """
        logger.info(f"Getting market overview for {market_type}")
        
        # Retry логика с экспоненциальной задержкой
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                # Получаем все тикеры
                spot_tickers = {}
                futures_tickers = {}
                
                if market_type in ["spot", "both"]:
                    try:
                        self.exchange.options['defaultType'] = 'spot'
                        spot_tickers = await self.exchange.fetch_tickers()
                    except Exception as e:
                        error_msg = str(e)
                        if "asset/coin/query-info" in error_msg.lower() or "query-info" in error_msg.lower():
                            logger.warning(f"CCXT error with query-info for spot tickers: {e}")
                            spot_tickers = {}
                        else:
                            raise
                
                if market_type in ["futures", "both"]:
                    try:
                        self.exchange.options['defaultType'] = 'swap'
                        futures_tickers = await self.exchange.fetch_tickers()
                    except Exception as e:
                        error_msg = str(e)
                        if "asset/coin/query-info" in error_msg.lower() or "query-info" in error_msg.lower():
                            logger.warning(f"CCXT error with query-info for futures tickers: {e}")
                            futures_tickers = {}
                        else:
                            raise
                
                # Получаем BTC данные (лидер рынка)
                try:
                    btc_ticker = await self.exchange.fetch_ticker('BTC/USDT')
                    btc_price = btc_ticker.get('last', 0) or 0
                    btc_change_24h = btc_ticker.get('percentage', 0) or 0
                except Exception as e:
                    logger.warning(f"Error getting BTC ticker: {e}")
                    btc_price = 0
                    btc_change_24h = 0
                
                # Вычисляем market sentiment
                all_tickers = list(spot_tickers.values()) + list(futures_tickers.values())
                
                # Проверяем, что есть данные
                if not all_tickers:
                    logger.error("No tickers received from API - this indicates a critical error")
                    raise Exception("API Error: No tickers received from Bybit API. This may indicate API connectivity issues or rate limiting.")
                
                positive_changes = sum(1 for t in all_tickers if t.get('percentage', 0) and t.get('percentage', 0) > 0)
                negative_changes = sum(1 for t in all_tickers if t.get('percentage', 0) and t.get('percentage', 0) < 0)
                
                if positive_changes > negative_changes * 1.5:
                    sentiment = "bullish"
                elif negative_changes > positive_changes * 1.5:
                    sentiment = "bearish"
                else:
                    sentiment = "neutral"
                
                # Топ gainers и losers
                sorted_by_change = sorted(
                    [t for t in all_tickers if t.get('quoteVolume', 0) and t.get('quoteVolume', 0) > 100000],  # Минимум $100k объём
                    key=lambda x: x.get('percentage', 0) or 0,
                    reverse=True
                )
                
                top_gainers = sorted_by_change[:20]
                top_losers = sorted_by_change[-20:]
                
                # Топ по объёму
                sorted_by_volume = sorted(
                    all_tickers,
                    key=lambda x: x.get('quoteVolume', 0) or 0,
                    reverse=True
                )
                top_volume = sorted_by_volume[:20]
                
                # Расчёт общей волатильности
                volatilities = [abs(t.get('percentage', 0) or 0) for t in all_tickers if t.get('percentage') is not None]
                avg_volatility = sum(volatilities) / len(volatilities) if volatilities else 0
                
                if avg_volatility > 5:
                    volatility_level = "high"
                elif avg_volatility > 2:
                    volatility_level = "medium"
                else:
                    volatility_level = "low"
                
                return {
                    "timestamp": datetime.now().isoformat(),
                    "market_type": market_type,
                    "sentiment": sentiment,
                    "btc": {
                        "price": btc_price,
                        "change_24h": btc_change_24h,
                        "dominance": "N/A"  # TODO: Calculate from market caps
                    },
                    "statistics": {
                        "total_pairs": len(all_tickers),
                        "positive_changes": positive_changes,
                        "negative_changes": negative_changes,
                        "avg_volatility": round(avg_volatility, 2),
                        "volatility_level": volatility_level
                    },
                    "top_gainers": [
                        {
                            "symbol": t.get('symbol', ''),
                            "price": t.get('last', 0) or 0,
                            "change_24h": t.get('percentage', 0) or 0,
                            "volume_24h": t.get('quoteVolume', 0) or 0
                        }
                        for t in top_gainers
                    ],
                    "top_losers": [
                        {
                            "symbol": t.get('symbol', ''),
                            "price": t.get('last', 0) or 0,
                            "change_24h": t.get('percentage', 0) or 0,
                            "volume_24h": t.get('quoteVolume', 0) or 0
                        }
                        for t in top_losers
                    ],
                    "top_volume": [
                        {
                            "symbol": t.get('symbol', ''),
                            "price": t.get('last', 0) or 0,
                            "volume_24h": t.get('quoteVolume', 0) or 0,
                            "change_24h": t.get('percentage', 0) or 0
                        }
                        for t in top_volume
                    ],
                    "market_conditions": {
                        "trend": "bullish" if btc_change_24h > 2 else "bearish" if btc_change_24h < -2 else "ranging",
                        "volatility": volatility_level,
                        "phase": self._determine_market_phase(sentiment, volatility_level)
                    }
                }
                
            except Exception as e:
                error_msg = str(e).lower()
                
                # Проверяем на DNS ошибки
                if any(keyword in error_msg for keyword in ["dns", "could not contact dns", "name resolution", "gaierror", "cannot connect to host"]):
                    logger.warning(f"DNS/Network error (attempt {attempt + 1}/{max_retries}): {e}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(retry_delay * (2 ** attempt))
                        continue
                    else:
                        logger.error(f"DNS resolution failed after {max_retries} attempts: {e}")
                        raise Exception(f"DNS/Network Error: Failed to connect to Bybit API after {max_retries} attempts. Error: {e}")
                
                # Фильтруем ошибки, связанные с asset/coin/query-info
                elif "asset/coin/query-info" in error_msg or "query-info" in error_msg:
                    logger.warning(f"CCXT error with query-info endpoint (attempt {attempt + 1}/{max_retries}): {e}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(retry_delay * (2 ** attempt))
                        continue
                    else:
                        # Пробрасываем исключение вместо возврата пустых данных
                        logger.error(f"Failed to get market overview after {max_retries} attempts")
                        raise Exception(f"API Error: Failed to fetch market overview after {max_retries} attempts. CCXT query-info endpoint issue: {e}")
                else:
                    # Другие ошибки - пробуем retry
                    logger.warning(f"Error getting market overview (attempt {attempt + 1}/{max_retries}): {e}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(retry_delay * (2 ** attempt))
                        continue
                    else:
                        logger.error(f"Failed to get market overview after {max_retries} attempts: {e}", exc_info=True)
                        raise
    
    async def get_all_tickers(self, market_type: str = "spot", sort_by: str = "volume") -> List[Dict[str, Any]]:
        """
        Получить все торговые пары с кешированием
        С fallback механизмом при ошибках CCXT
        
        Args:
            market_type: "spot" или "futures"
            sort_by: "volume", "change", или "name"
            
        Returns:
            Массив всех торговых пар с базовой информацией
        """
        # Проверяем кеш
        cache_key = f"{market_type}_{sort_by}"
        now = datetime.now()
        
        if (cache_key in self._tickers_cache and 
            cache_key in self._cache_timestamps and
            now - self._cache_timestamps[cache_key] < self._cache_ttl):
            logger.debug(f"Using cached tickers for {cache_key}")
            return self._tickers_cache[cache_key]
        
        logger.info(f"Getting all {market_type} tickers, sorted by {sort_by}")
        
        # Retry логика с экспоненциальной задержкой
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                self.exchange.options['defaultType'] = 'swap' if market_type == 'futures' else 'spot'
                
                # Пытаемся получить тикеры через CCXT
                tickers = await self.exchange.fetch_tickers()
                
                # Преобразуем в список с безопасной обработкой
                ticker_list = []
                for symbol, ticker in tickers.items():
                    try:
                        ticker_list.append({
                            "symbol": symbol,
                            "price": ticker.get('last', 0) or 0,
                            "change_24h": ticker.get('percentage', 0) or 0,
                            "volume_24h": ticker.get('quoteVolume', 0) or 0,
                            "high_24h": ticker.get('high', 0) or 0,
                            "low_24h": ticker.get('low', 0) or 0,
                            "bid": ticker.get('bid', 0) or 0,
                            "ask": ticker.get('ask', 0) or 0
                        })
                    except Exception as ticker_err:
                        logger.warning(f"Error processing ticker {symbol}: {ticker_err}")
                        continue
                
                # Сортировка
                if sort_by == "volume":
                    ticker_list.sort(key=lambda x: x['volume_24h'], reverse=True)
                elif sort_by == "change":
                    ticker_list.sort(key=lambda x: x['change_24h'], reverse=True)
                else:  # name
                    ticker_list.sort(key=lambda x: x['symbol'])
                
                # Обновляем кеш
                self._tickers_cache[cache_key] = ticker_list
                self._cache_timestamps[cache_key] = now
                logger.debug(f"Cached tickers for {cache_key}")
                
                return ticker_list
                
            except Exception as e:
                error_msg = str(e).lower()
                
                # Проверяем на DNS ошибки
                if any(keyword in error_msg for keyword in ["dns", "could not contact dns", "name resolution", "gaierror", "cannot connect to host"]):
                    logger.warning(f"DNS/Network error (attempt {attempt + 1}/{max_retries}): {e}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(retry_delay * (2 ** attempt))
                        continue
                    else:
                        # Последняя попытка - используем прямой HTTP запрос к Bybit API
                        logger.info(f"CCXT failed due to DNS/Network error, trying direct HTTP request to Bybit API for tickers")
                        try:
                            ticker_list = await self._get_tickers_direct_http(market_type)
                            if ticker_list and len(ticker_list) > 0:
                                # Обновляем кеш
                                self._tickers_cache[cache_key] = ticker_list
                                self._cache_timestamps[cache_key] = now
                                logger.debug(f"Cached tickers from direct HTTP for {cache_key}")
                                return ticker_list
                            else:
                                raise Exception(f"Empty tickers list from direct HTTP")
                        except Exception as http_error:
                            logger.error(f"Direct HTTP also failed for tickers: {http_error}")
                            raise Exception(f"API Error: Failed to fetch tickers after {max_retries} attempts and direct HTTP fallback. DNS/Network error: {e}, HTTP error: {http_error}")
                
                # Фильтруем ошибки, связанные с asset/coin/query-info
                elif "asset/coin/query-info" in error_msg or "query-info" in error_msg:
                    logger.warning(f"CCXT error with query-info endpoint (attempt {attempt + 1}/{max_retries}): {e}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(retry_delay * (2 ** attempt))
                        continue
                    else:
                        # Последняя попытка - используем прямой HTTP запрос к Bybit API
                        logger.info(f"CCXT failed, trying direct HTTP request to Bybit API for tickers")
                        try:
                            ticker_list = await self._get_tickers_direct_http(market_type)
                            if ticker_list and len(ticker_list) > 0:
                                # Обновляем кеш
                                self._tickers_cache[cache_key] = ticker_list
                                self._cache_timestamps[cache_key] = now
                                logger.debug(f"Cached tickers from direct HTTP for {cache_key}")
                                return ticker_list
                            else:
                                raise Exception(f"Empty tickers list from direct HTTP")
                        except Exception as http_error:
                            logger.error(f"Direct HTTP also failed for tickers: {http_error}")
                            raise Exception(f"API Error: Failed to fetch tickers after {max_retries} attempts and direct HTTP fallback. CCXT error: {e}, HTTP error: {http_error}")
                else:
                    # Другие ошибки - пробуем retry
                    logger.warning(f"Error getting all tickers (attempt {attempt + 1}/{max_retries}): {e}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(retry_delay * (2 ** attempt))
                        continue
                    else:
                        logger.error(f"Failed to get tickers after {max_retries} attempts: {e}", exc_info=True)
                        raise
        
        # Если дошли сюда, это не должно произойти, но на всякий случай
        raise Exception("Unexpected error: get_all_tickers failed without proper error handling")
    
    async def get_asset_price(self, symbol: str) -> Dict[str, Any]:
        """
        Получить текущую цену актива
        С retry логикой и обработкой ошибок
        
        Args:
            symbol: Торговая пара (например "BTC/USDT")
            
        Returns:
            Цена, объём, изменение за 24h
        """
        logger.info(f"Getting price for {symbol}")
        
        # Retry логика с экспоненциальной задержкой
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                ticker = await self.exchange.fetch_ticker(symbol)
                
                return {
                    "symbol": symbol,
                    "price": ticker.get('last', 0) or 0,
                    "change_24h": ticker.get('percentage', 0) or 0,
                    "volume_24h": ticker.get('quoteVolume', 0) or 0,
                    "high_24h": ticker.get('high', 0) or 0,
                    "low_24h": ticker.get('low', 0) or 0,
                    "bid": ticker.get('bid', 0) or 0,
                    "ask": ticker.get('ask', 0) or 0,
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                # Парсим ошибку CCXT для извлечения retCode
                parsed_error = parse_ccxt_error(e)
                error_msg = str(e).lower()
                
                # Если нашли retCode в ошибке - обрабатываем специфично
                if parsed_error["parsed"] and parsed_error["retCode"]:
                    ret_code = parsed_error["retCode"]
                    ret_msg = parsed_error["retMsg"]
                    
                    if ret_code == 10003:
                        logger.error(f"❌ API Key INVALID (retCode=10003) for {symbol}")
                        raise Exception(
                            f"Bybit API Key is INVALID! "
                            f"Please check your BYBIT_API_KEY and BYBIT_API_SECRET. "
                            f"Error: {ret_msg}"
                        )
                    elif ret_code == 10004:
                        logger.error(f"❌ API Key has NO PERMISSIONS (retCode=10004) for {symbol}")
                        raise Exception(
                            f"Bybit API Key has insufficient permissions! "
                            f"Please enable READ permissions on Bybit API Management page. "
                            f"Error: {ret_msg}"
                        )
                    elif ret_code == 10005:
                        logger.error(f"❌ IP NOT WHITELISTED (retCode=10005) for {symbol}")
                        raise Exception(
                            f"IP address is not whitelisted! "
                            f"Please add your server's IP to Bybit API whitelist. "
                            f"Error: {ret_msg}"
                        )
                    else:
                        logger.error(f"Bybit API error (retCode={ret_code}) for {symbol}: {ret_msg}")
                        raise Exception(f"Bybit API error (retCode={ret_code}): {ret_msg}")
                
                # Проверяем на DNS ошибки
                if any(keyword in error_msg for keyword in ["dns", "could not contact dns", "name resolution", "gaierror", "cannot connect to host"]):
                    logger.warning(f"DNS/Network error for {symbol} (attempt {attempt + 1}/{max_retries}): {e}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(retry_delay * (2 ** attempt))
                        continue
                    else:
                        logger.error(f"DNS resolution failed for {symbol} after {max_retries} attempts: {e}")
                        raise Exception(f"DNS/Network Error: Failed to connect to Bybit API for {symbol} after {max_retries} attempts. Error: {e}")
                
                # Фильтруем ошибки, связанные с asset/coin/query-info
                elif "asset/coin/query-info" in error_msg or "query-info" in error_msg:
                    logger.warning(f"CCXT error with query-info endpoint for {symbol} (attempt {attempt + 1}/{max_retries}): {e}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(retry_delay * (2 ** attempt))
                        continue
                    else:
                        # Пробрасываем исключение вместо возврата пустых данных
                        logger.error(f"Failed to get price for {symbol} after {max_retries} attempts")
                        raise Exception(f"API Error: Failed to fetch price for {symbol} after {max_retries} attempts. Error: {e}")
                else:
                    # Другие ошибки - пробуем retry
                    logger.warning(f"Error getting asset price for {symbol} (attempt {attempt + 1}/{max_retries}): {e}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(retry_delay * (2 ** attempt))
                        continue
                    else:
                        logger.error(f"Failed to get price for {symbol} after {max_retries} attempts: {e}", exc_info=True)
                        raise
    
    async def get_ohlcv(self, symbol: str, timeframe: str = "1h", limit: int = 100) -> List[List]:
        """
        Получить OHLCV данные (свечи)
        С кэшированием для ускорения повторных запросов
        С retry логикой и обработкой ошибок
        
        Args:
            symbol: Торговая пара
            timeframe: Таймфрейм (1m, 5m, 15m, 1h, 4h, 1d)
            limit: Количество свечей
            
        Returns:
            Массив OHLCV данных
        """
        # Проверяем кэш
        cache = get_cache_manager()
        cached_result = cache.get("get_ohlcv", symbol=symbol, timeframe=timeframe, limit=limit)
        if cached_result is not None:
            logger.debug(f"Cache hit for get_ohlcv: {symbol} {timeframe}")
            return cached_result
        
        # Retry логика с экспоненциальной задержкой
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                ohlcv = await self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
                
                # Проверяем, что получили данные
                if not ohlcv or len(ohlcv) == 0:
                    raise ValueError(f"Empty OHLCV data for {symbol}")
                
                # Сохраняем в кэш (TTL зависит от таймфрейма: меньшие таймфреймы = короче кэш)
                ttl_map = {
                    "1m": 10,   # 10 секунд для 1m
                    "5m": 30,   # 30 секунд для 5m
                    "15m": 60,  # 1 минута для 15m
                    "1h": 120,  # 2 минуты для 1h
                    "4h": 300,  # 5 минут для 4h
                    "1d": 600   # 10 минут для 1d
                }
                ttl = ttl_map.get(timeframe, 60)  # По умолчанию 60 секунд
                
                cache.set("get_ohlcv", ohlcv, ttl=ttl, symbol=symbol, timeframe=timeframe, limit=limit)
                
                return ohlcv
                
            except Exception as e:
                error_msg = str(e).lower()
                
                # Проверяем на DNS ошибки
                if any(keyword in error_msg for keyword in ["dns", "could not contact dns", "name resolution", "gaierror", "cannot connect to host"]):
                    logger.warning(f"DNS/Network error for {symbol} (attempt {attempt + 1}/{max_retries}): {e}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(retry_delay * (2 ** attempt))
                        continue
                    else:
                        # Последняя попытка - используем прямой HTTP запрос к Bybit API
                        logger.info(f"CCXT failed due to DNS/Network error, trying direct HTTP request to Bybit API for {symbol}")
                        try:
                            # Определяем category по символу (можно расширить логику)
                            category = "spot"  # По умолчанию spot, можно определить по символу
                            ohlcv = await self._get_ohlcv_direct_http(symbol, timeframe, limit, category)
                            if ohlcv and len(ohlcv) > 0:
                                # Сохраняем в кэш
                                ttl_map = {
                                    "1m": 10, "5m": 30, "15m": 60,
                                    "1h": 120, "4h": 300, "1d": 600
                                }
                                ttl = ttl_map.get(timeframe, 60)
                                cache.set("get_ohlcv", ohlcv, ttl=ttl, symbol=symbol, timeframe=timeframe, limit=limit)
                                return ohlcv
                            else:
                                raise Exception(f"Empty OHLCV data from direct HTTP for {symbol}")
                        except Exception as http_error:
                            logger.error(f"Direct HTTP also failed for {symbol}: {http_error}")
                            raise Exception(f"API Error: Failed to fetch OHLCV for {symbol} after {max_retries} attempts and direct HTTP fallback. DNS/Network error: {e}, HTTP error: {http_error}")
                
                # Фильтруем ошибки, связанные с asset/coin/query-info
                elif "asset/coin/query-info" in error_msg or "query-info" in error_msg:
                    logger.warning(f"CCXT error with query-info endpoint for {symbol} (attempt {attempt + 1}/{max_retries}): {e}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(retry_delay * (2 ** attempt))
                        continue
                    else:
                        # Последняя попытка - используем прямой HTTP запрос к Bybit API
                        logger.info(f"CCXT failed, trying direct HTTP request to Bybit API for {symbol}")
                        try:
                            # Определяем category по символу (можно расширить логику)
                            category = "spot"  # По умолчанию spot, можно определить по символу
                            ohlcv = await self._get_ohlcv_direct_http(symbol, timeframe, limit, category)
                            if ohlcv and len(ohlcv) > 0:
                                # Сохраняем в кэш
                                ttl_map = {
                                    "1m": 10, "5m": 30, "15m": 60,
                                    "1h": 120, "4h": 300, "1d": 600
                                }
                                ttl = ttl_map.get(timeframe, 60)
                                cache.set("get_ohlcv", ohlcv, ttl=ttl, symbol=symbol, timeframe=timeframe, limit=limit)
                                return ohlcv
                            else:
                                raise Exception(f"Empty OHLCV data from direct HTTP for {symbol}")
                        except Exception as http_error:
                            logger.error(f"Direct HTTP also failed for {symbol}: {http_error}")
                            raise Exception(f"API Error: Failed to fetch OHLCV for {symbol} after {max_retries} attempts and direct HTTP fallback. CCXT error: {e}, HTTP error: {http_error}")
                else:
                    # Другие ошибки - пробуем retry
                    logger.warning(f"Error getting OHLCV for {symbol} (attempt {attempt + 1}/{max_retries}): {e}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(retry_delay * (2 ** attempt))
                        continue
                    else:
                        logger.error(f"Failed to get OHLCV for {symbol} after {max_retries} attempts: {e}", exc_info=True)
                        raise
    
    async def _get_ohlcv_direct_http(self, symbol: str, timeframe: str, limit: int, category: str = "spot") -> List[List]:
        """
        Получить OHLCV данные через прямой HTTP запрос к Bybit API v5
        Обходит проблемы CCXT с query-info endpoint
        
        Args:
            symbol: Торговая пара
            timeframe: Таймфрейм
            limit: Количество свечей
            category: "spot", "linear", или "inverse"
        """
        # Маппинг таймфреймов для Bybit API
        interval_map = {
            "1m": "1", "3m": "3", "5m": "5", "15m": "15", "30m": "30",
            "1h": "60", "2h": "120", "4h": "240", "6h": "360", "12h": "720",
            "1d": "D", "1w": "W", "1M": "M"
        }
        
        interval = interval_map.get(timeframe, "60")
        base_url = "https://api-testnet.bybit.com" if self.testnet else "https://api.bybit.com"
        endpoint = "/v5/market/kline"
        url = f"{base_url}{endpoint}"
        
        # Определяем category автоматически по символу если не указан
        if category == "spot" and ("USDT" in symbol or "USDC" in symbol):
            # Для spot используем spot
            pass
        elif category in ["linear", "inverse"]:
            # Для фьючерсов используем указанный category
            pass
        else:
            # По умолчанию spot
            category = "spot"
        
        params = {
            "category": category,
            "symbol": symbol,
            "interval": interval,
            "limit": str(limit)
        }
        
        # Retry логика с обработкой DNS ошибок
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                session = await self._get_http_session()
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("retCode") == 0:
                            result = data.get("result", {})
                            klines = result.get("list", [])
                            
                            # Конвертируем в формат CCXT: [[timestamp, open, high, low, close, volume], ...]
                            ohlcv_list = []
                            for kline in reversed(klines):  # Bybit возвращает в обратном порядке
                                ohlcv_list.append([
                                    int(kline[0]),  # timestamp
                                    float(kline[1]),  # open
                                    float(kline[2]),  # high
                                    float(kline[3]),  # low
                                    float(kline[4]),  # close
                                    float(kline[5])   # volume
                                ])
                            
                            return ohlcv_list
                        else:
                            raise Exception(f"Bybit API error: {data.get('retMsg', 'Unknown error')}")
                    else:
                        raise Exception(f"HTTP {response.status}: {await response.text()}")
            except (aiohttp.ClientError, socket.gaierror, OSError) as e:
                error_msg = str(e).lower()
                # Проверяем на DNS ошибки
                if any(keyword in error_msg for keyword in ["dns", "could not contact dns", "name resolution", "gaierror"]):
                    logger.warning(f"DNS error on attempt {attempt + 1}/{max_retries}: {e}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(retry_delay * (2 ** attempt))
                        continue
                    else:
                        raise Exception(f"DNS resolution failed after {max_retries} attempts: {e}")
                else:
                    # Другие сетевые ошибки
                    logger.warning(f"Network error on attempt {attempt + 1}/{max_retries}: {e}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(retry_delay * (2 ** attempt))
                        continue
                    else:
                        raise
            except Exception as e:
                logger.error(f"Direct HTTP request for OHLCV failed: {e}")
                raise
    
    async def _get_tickers_direct_http(self, market_type: str) -> List[Dict[str, Any]]:
        """
        Получить тикеры через прямой HTTP запрос к Bybit API v5
        Обходит проблемы CCXT с query-info endpoint
        """
        category = "linear" if market_type == "futures" else "spot"
        base_url = "https://api-testnet.bybit.com" if self.testnet else "https://api.bybit.com"
        endpoint = "/v5/market/tickers"
        url = f"{base_url}{endpoint}"
        
        params = {
            "category": category,
            "limit": "1000"  # Максимум для одного запроса
        }
        
        # Retry логика с обработкой DNS ошибок
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                session = await self._get_http_session()
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("retCode") == 0:
                            result = data.get("result", {})
                            tickers = result.get("list", [])
                            
                            # Конвертируем в формат, совместимый с CCXT
                            ticker_list = []
                            for ticker in tickers:
                                try:
                                    ticker_list.append({
                                        "symbol": ticker.get("symbol", ""),
                                        "price": float(ticker.get("lastPrice", 0)) or 0,
                                        "change_24h": float(ticker.get("price24hPcnt", 0)) * 100 or 0,  # Конвертируем в проценты
                                        "volume_24h": float(ticker.get("volume24h", 0)) or 0,
                                        "high_24h": float(ticker.get("highPrice24h", 0)) or 0,
                                        "low_24h": float(ticker.get("lowPrice24h", 0)) or 0,
                                        "bid": float(ticker.get("bid1Price", 0)) or 0,
                                        "ask": float(ticker.get("ask1Price", 0)) or 0
                                    })
                                except Exception as ticker_err:
                                    logger.warning(f"Error processing ticker from direct HTTP: {ticker_err}")
                                    continue
                            
                            return ticker_list
                        else:
                            raise Exception(f"Bybit API error: {data.get('retMsg', 'Unknown error')}")
                    else:
                        raise Exception(f"HTTP {response.status}: {await response.text()}")
            except (aiohttp.ClientError, socket.gaierror, OSError) as e:
                error_msg = str(e).lower()
                # Проверяем на DNS ошибки
                if any(keyword in error_msg for keyword in ["dns", "could not contact dns", "name resolution", "gaierror"]):
                    logger.warning(f"DNS error on attempt {attempt + 1}/{max_retries}: {e}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(retry_delay * (2 ** attempt))
                        continue
                    else:
                        raise Exception(f"DNS resolution failed after {max_retries} attempts: {e}")
                else:
                    # Другие сетевые ошибки
                    logger.warning(f"Network error on attempt {attempt + 1}/{max_retries}: {e}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(retry_delay * (2 ** attempt))
                        continue
                    else:
                        raise
            except Exception as e:
                logger.error(f"Direct HTTP request for tickers failed: {e}")
                raise
    
    async def get_orderbook(self, symbol: str, limit: int = 25) -> Dict[str, Any]:
        """
        Получить orderbook (глубину рынка) для анализа ликвидности
        
        Args:
            symbol: Торговая пара
            limit: Количество уровней (25, 50, 100, 200)
            
        Returns:
            Orderbook данные с bids и asks
        """
        logger.info(f"Getting orderbook for {symbol} (limit={limit})")
        
        try:
            orderbook = await self.exchange.fetch_order_book(symbol, limit=limit)
            
            return {
                "symbol": symbol,
                "bids": orderbook['bids'],  # [[price, size], ...]
                "asks": orderbook['asks'],  # [[price, size], ...]
                "timestamp": datetime.now().isoformat(),
                "bid_price": orderbook['bids'][0][0] if orderbook['bids'] else None,
                "ask_price": orderbook['asks'][0][0] if orderbook['asks'] else None,
                "spread": (orderbook['asks'][0][0] - orderbook['bids'][0][0]) if (orderbook['asks'] and orderbook['bids']) else None
            }
            
        except Exception as e:
            logger.error(f"Error getting orderbook: {e}", exc_info=True)
            raise
    
    async def get_account_info(self) -> Dict[str, Any]:
        """
        Получить информацию о счёте
        
        Returns:
            Balance, positions, risk metrics
        """
        logger.info("Getting account info")
        
        try:
            # Получаем баланс
            balance = await self.exchange.fetch_balance()
            
            # Получаем открытые позиции
            positions = await self.get_open_positions()
            
            # Расчёт risk metrics
            total_equity = balance['total'].get('USDT', 0)
            used_margin = sum(p.get('margin', 0) for p in positions)
            unrealized_pnl = sum(p.get('unrealized_pnl', 0) for p in positions)
            
            return {
                "balance": {
                    "total": total_equity,
                    "available": balance['free'].get('USDT', 0),
                    "used_margin": used_margin,
                    "unrealized_pnl": unrealized_pnl
                },
                "positions": positions,
                "risk_metrics": {
                    "total_risk_pct": (used_margin / total_equity * 100) if total_equity > 0 else 0,
                    "positions_count": len(positions),
                    "max_drawdown": "N/A"  # TODO: Calculate from trade history
                }
            }
            
        except Exception as e:
            # Парсим ошибку CCXT для извлечения retCode
            parsed_error = parse_ccxt_error(e)
            
            if parsed_error["parsed"] and parsed_error["retCode"]:
                ret_code = parsed_error["retCode"]
                ret_msg = parsed_error["retMsg"]
                
                if ret_code == 10003:
                    logger.error(f"❌ API Key INVALID (retCode=10003) when getting account info")
                    raise Exception(
                        f"Bybit API Key is INVALID! "
                        f"Please check your BYBIT_API_KEY and BYBIT_API_SECRET. "
                        f"Error: {ret_msg}"
                    )
                else:
                    logger.error(f"Bybit API error (retCode={ret_code}) when getting account info: {ret_msg}")
                    raise Exception(f"Bybit API error (retCode={ret_code}): {ret_msg}")
            
            logger.error(f"Error getting account info: {e}", exc_info=True)
            raise
    
    async def get_open_positions(self) -> List[Dict[str, Any]]:
        """
        Получить все открытые позиции
        
        Returns:
            Массив открытых позиций
        """
        logger.info("Getting open positions")
        
        try:
            positions = await self.exchange.fetch_positions()
            
            # Фильтруем только открытые позиции
            open_positions = [
                {
                    "symbol": p['symbol'],
                    "side": p['side'],
                    "size": p['contracts'],
                    "entry_price": p['entryPrice'],
                    "current_price": p['markPrice'],
                    "unrealized_pnl": p['unrealizedPnl'],
                    "unrealized_pnl_pct": p['percentage'],
                    "leverage": p['leverage'],
                    "margin": p['initialMargin'],
                    "liquidation_price": p['liquidationPrice']
                }
                for p in positions if p['contracts'] > 0
            ]
            
            return open_positions
            
        except Exception as e:
            logger.error(f"Error getting open positions: {e}", exc_info=True)
            raise
    
    async def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: Optional[float] = None,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Открыть новую позицию
        
        Args:
            symbol: Торговая пара
            side: "buy" или "sell"
            order_type: "market" или "limit"
            quantity: Размер позиции
            price: Цена (для limit ордера)
            stop_loss: Стоп-лосс
            take_profit: Тейк-профит
            
        Returns:
            Детали размещённого ордера
        """
        logger.info(f"Placing {side} {order_type} order for {symbol}: {quantity}")
        
        try:
            # Размещаем основной ордер
            order_params = {}
            
            if stop_loss:
                order_params['stopLoss'] = {'triggerPrice': stop_loss}
            
            if take_profit:
                order_params['takeProfit'] = {'triggerPrice': take_profit}
            
            order = await self.exchange.create_order(
                symbol=symbol,
                type=order_type,
                side=side,
                amount=quantity,
                price=price,
                params=order_params
            )
            
            logger.info(f"Order placed successfully: {order['id']}")
            
            return {
                "order_id": order['id'],
                "symbol": symbol,
                "side": side,
                "type": order_type,
                "quantity": quantity,
                "price": price or order.get('average'),
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "status": order['status'],
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error placing order: {e}", exc_info=True)
            raise
    
    async def get_funding_rate(self, symbol: str) -> Dict[str, Any]:
        """
        Получить funding rate для фьючерсов
        
        Args:
            symbol: Торговая пара (например "BTC/USDT:USDT")
            
        Returns:
            Funding rate, next funding time, market bias
        """
        logger.info(f"Getting funding rate for {symbol}")
        
        try:
            # Для фьючерсов нужно использовать swap тип
            self.exchange.options['defaultType'] = 'swap'
            
            # Получаем funding rate через CCXT
            ticker = await self.exchange.fetch_ticker(symbol)
            
            # Funding rate обычно в info или отдельным запросом
            funding_rate = ticker.get('info', {}).get('fundingRate', None)
            next_funding_time = ticker.get('info', {}).get('nextFundingTime', None)
            
            # Если нет в ticker, пытаемся получить через fetchFundingRate
            if funding_rate is None:
                try:
                    funding_info = await self.exchange.fetch_funding_rate(symbol)
                    funding_rate = funding_info.get('fundingRate', 0) if funding_info else 0
                    next_funding_time = funding_info.get('fundingTimestamp', None) if funding_info else None
                except:
                    funding_rate = 0
            
            # Конвертируем в проценты
            funding_rate_pct = float(funding_rate) * 100 if funding_rate else 0
            
            # Определяем market bias
            if funding_rate_pct > 0.01:
                bias = "very_bullish"
                message = f"Очень бычий funding rate ({funding_rate_pct:.4f}%). Long позиции платят short."
            elif funding_rate_pct > 0.005:
                bias = "bullish"
                message = f"Бычий funding rate ({funding_rate_pct:.4f}%). Long позиции платят short."
            elif funding_rate_pct < -0.01:
                bias = "very_bearish"
                message = f"Очень медвежий funding rate ({funding_rate_pct:.4f}%). Short позиции платят long."
            elif funding_rate_pct < -0.005:
                bias = "bearish"
                message = f"Медвежий funding rate ({funding_rate_pct:.4f}%). Short позиции платят long."
            else:
                bias = "neutral"
                message = f"Нейтральный funding rate ({funding_rate_pct:.4f}%)."
            
            return {
                "symbol": symbol,
                "funding_rate": round(funding_rate_pct, 4),
                "funding_rate_raw": float(funding_rate) if funding_rate else 0,
                "next_funding_time": next_funding_time,
                "market_bias": bias,
                "message": message,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting funding rate for {symbol}: {e}", exc_info=True)
            return {
                "symbol": symbol,
                "funding_rate": 0.0,
                "market_bias": "unknown",
                "message": f"Ошибка получения funding rate: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    async def get_open_interest(self, symbol: str, category: str = "linear") -> Dict[str, Any]:
        """
        Получить Open Interest для futures
        
        Args:
            symbol: Торговая пара (например "BTCUSDT")
            category: "linear" или "inverse" (default: "linear")
            
        Returns:
            Open Interest данные с анализом тренда и интерпретацией
        """
        logger.info(f"Getting Open Interest for {symbol} ({category})")
        
        # Retry логика с обработкой DNS ошибок
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                # Используем прямой HTTP запрос к Bybit API v5
                base_url = "https://api-testnet.bybit.com" if self.testnet else "https://api.bybit.com"
                endpoint = "/v5/market/open-interest"
                url = f"{base_url}{endpoint}"
                
                params = {
                    "category": category,
                    "symbol": symbol,
                    "intervalTime": "5min"  # Исправлено: intervalTime вместо intervalType
                }
                
                session = await self._get_http_session()
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("retCode") == 0:
                            result = data.get("result", {})
                            oi_list = result.get("list", [])
                            
                            if not oi_list:
                                raise ValueError(f"No Open Interest data for {symbol}")
                            
                            # Текущий OI (последний элемент)
                            current_oi = float(oi_list[-1].get("openInterest", 0))
                            
                            # Получаем историю для анализа тренда
                            # Запрашиваем больше данных для анализа
                            params_history = {
                                "category": category,
                                "symbol": symbol,
                                "intervalTime": "5min",  # Исправлено: intervalTime вместо intervalType
                                "limit": "50"  # 50 точек = ~4 часа истории
                            }
                            
                            async with session.get(url, params=params_history) as hist_response:
                                if hist_response.status == 200:
                                    hist_data = await hist_response.json()
                                    if hist_data.get("retCode") == 0:
                                        hist_result = hist_data.get("result", {})
                                        hist_oi_list = hist_result.get("list", [])
                                        
                                        if len(hist_oi_list) >= 2:
                                            # Первый элемент (старый)
                                            old_oi = float(hist_oi_list[0].get("openInterest", 0))
                                            
                                            # Изменение за период
                                            oi_change = current_oi - old_oi
                                            oi_change_pct = (oi_change / old_oi * 100) if old_oi > 0 else 0
                                            
                                            # Изменение за 24 часа (если есть достаточно данных)
                                            if len(hist_oi_list) >= 10:
                                                oi_24h_ago = float(hist_oi_list[0].get("openInterest", 0))
                                                oi_change_24h = current_oi - oi_24h_ago
                                                oi_change_24h_pct = (oi_change_24h / oi_24h_ago * 100) if oi_24h_ago > 0 else 0
                                            else:
                                                oi_change_24h = 0
                                                oi_change_24h_pct = 0
                                        else:
                                            oi_change = 0
                                            oi_change_pct = 0
                                            oi_change_24h = 0
                                            oi_change_24h_pct = 0
                                    else:
                                        oi_change = 0
                                        oi_change_pct = 0
                                        oi_change_24h = 0
                                        oi_change_24h_pct = 0
                                else:
                                    oi_change = 0
                                    oi_change_pct = 0
                                    oi_change_24h = 0
                                    oi_change_24h_pct = 0
                            
                            # Интерпретация изменения OI
                            if oi_change_24h_pct > 5:
                                interpretation = "Сильное накопление позиций. Вероятен сильный движение."
                                trend = "accumulation"
                                signal_strength = "strong"
                            elif oi_change_24h_pct > 2:
                                interpretation = "Умеренное накопление. Поддержка текущего тренда."
                                trend = "accumulation"
                                signal_strength = "moderate"
                            elif oi_change_24h_pct < -5:
                                interpretation = "Сильное распределение. Возможен разворот."
                                trend = "distribution"
                                signal_strength = "strong"
                            elif oi_change_24h_pct < -2:
                                interpretation = "Умеренное распределение. Ослабление тренда."
                                trend = "distribution"
                                signal_strength = "moderate"
                            else:
                                interpretation = "Стабильный OI. Консолидация."
                                trend = "stable"
                                signal_strength = "weak"
                            
                            return {
                                "symbol": symbol,
                                "category": category,
                                "open_interest": current_oi,
                                "change_24h": round(oi_change_24h, 2),
                                "change_24h_pct": round(oi_change_24h_pct, 2),
                                "change_recent": round(oi_change, 2),
                                "change_recent_pct": round(oi_change_pct, 2),
                                "trend": trend,
                                "signal_strength": signal_strength,
                                "interpretation": interpretation,
                                "timestamp": datetime.now().isoformat()
                            }
                        else:
                            raise Exception(f"Bybit API error: {data.get('retMsg', 'Unknown error')}")
                    else:
                        raise Exception(f"HTTP {response.status}: {await response.text()}")
                        
            except (aiohttp.ClientError, socket.gaierror, OSError) as e:
                error_msg = str(e).lower()
                # Проверяем на DNS ошибки
                if any(keyword in error_msg for keyword in ["dns", "could not contact dns", "name resolution", "gaierror"]):
                    logger.warning(f"DNS error on attempt {attempt + 1}/{max_retries}: {e}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(retry_delay * (2 ** attempt))
                        continue
                    else:
                        logger.error(f"DNS resolution failed after {max_retries} attempts: {e}")
                        return {
                            "symbol": symbol,
                            "category": category,
                            "open_interest": 0.0,
                            "change_24h_pct": 0.0,
                            "trend": "unknown",
                            "interpretation": f"DNS/Network Error: Failed to connect to Bybit API after {max_retries} attempts. Error: {e}",
                            "timestamp": datetime.now().isoformat()
                        }
                else:
                    # Другие сетевые ошибки
                    logger.warning(f"Network error on attempt {attempt + 1}/{max_retries}: {e}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(retry_delay * (2 ** attempt))
                        continue
                    else:
                        raise
            except Exception as e:
                logger.error(f"Error getting Open Interest for {symbol}: {e}", exc_info=True)
                return {
                    "symbol": symbol,
                    "category": category,
                    "open_interest": 0.0,
                    "change_24h_pct": 0.0,
                    "trend": "unknown",
                    "interpretation": f"Ошибка получения Open Interest: {str(e)}",
                    "timestamp": datetime.now().isoformat()
                }
    
    async def close_position(self, symbol: str, reason: str = "Manual close") -> Dict[str, Any]:
        """
        Закрыть открытую позицию
        
        Args:
            symbol: Торговая пара
            reason: Причина закрытия
            
        Returns:
            Детали закрытой позиции
        """
        logger.info(f"Closing position for {symbol}. Reason: {reason}")
        
        try:
            # Получаем текущую позицию
            positions = await self.exchange.fetch_positions([symbol])
            position = next((p for p in positions if p['symbol'] == symbol and p['contracts'] > 0), None)
            
            if not position:
                raise ValueError(f"No open position found for {symbol}")
            
            # Закрываем позицию (размещаем противоположный ордер)
            close_side = 'sell' if position['side'] == 'long' else 'buy'
            close_order = await self.exchange.create_market_order(
                symbol=symbol,
                side=close_side,
                amount=position['contracts']
            )
            
            logger.info(f"Position closed successfully: {close_order['id']}")
            
            return {
                "symbol": symbol,
                "closed_at": datetime.now().isoformat(),
                "reason": reason,
                "pnl": position['unrealizedPnl'],
                "pnl_pct": position['percentage'],
                "order_id": close_order['id']
            }
            
        except Exception as e:
            logger.error(f"Error closing position: {e}", exc_info=True)
            raise
    
    def _determine_market_phase(self, sentiment: str, volatility: str) -> str:
        """Определить фазу рынка на основе sentiment и volatility"""
        if sentiment == "bullish" and volatility == "low":
            return "accumulation"
        elif sentiment == "bullish" and volatility in ["medium", "high"]:
            return "markup"
        elif sentiment == "bearish" and volatility == "low":
            return "distribution"
        elif sentiment == "bearish" and volatility in ["medium", "high"]:
            return "markdown"
        else:
            return "consolidation"
    
    async def get_public_trade_history(self, symbol: str, limit: int = 1000) -> List[Dict[str, Any]]:
        """
        Получить историю публичных сделок для анализа Order Flow (CVD)
        
        Args:
            symbol: Торговая пара
            limit: Количество сделок
            
        Returns:
            Список сделок
        """
        logger.info(f"Getting public trades for {symbol} (limit={limit})")
        
        try:
            # Используем CCXT fetch_trades
            trades = await self.exchange.fetch_trades(symbol, limit=limit)
            return trades
        except Exception as e:
            # Парсим ошибку CCXT для извлечения retCode
            parsed_error = parse_ccxt_error(e)
            
            if parsed_error["parsed"] and parsed_error["retCode"]:
                ret_code = parsed_error["retCode"]
                ret_msg = parsed_error["retMsg"]
                
                if ret_code == 10003:
                    logger.error(f"❌ API Key INVALID (retCode=10003) when getting public trades for {symbol}")
                    raise Exception(
                        f"Bybit API Key is INVALID! "
                        f"Please check your BYBIT_API_KEY and BYBIT_API_SECRET. "
                        f"Error: {ret_msg}"
                    )
                else:
                    logger.error(f"Bybit API error (retCode={ret_code}) when getting public trades: {ret_msg}")
                    raise Exception(f"Bybit API error (retCode={ret_code}): {ret_msg}")
            
            logger.error(f"Error getting public trades: {e}")
            raise

    async def close(self):
        """Закрыть соединение"""
        await self.exchange.close()
        
        # Закрываем HTTP сессию если она была создана
        if self._http_session and not self._http_session.closed:
            await self._http_session.close()
            self._http_session = None
        
        logger.info("Bybit client closed")
