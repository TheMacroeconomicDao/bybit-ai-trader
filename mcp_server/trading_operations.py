"""
Trading Operations Module
Полная реализация торговых операций для Bybit
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from pybit.unified_trading import HTTP
from loguru import logger
import threading
import time
import traceback
import requests
import hmac
import hashlib
import json


class BalanceCache:
    """
    Кэш для балансов счетов с TTL (Time To Live)
    Уменьшает количество API запросов к Bybit
    """
    
    def __init__(self, ttl_seconds: int = 30):
        """
        Инициализация кэша
        
        Args:
            ttl_seconds: Время жизни кэша в секундах (по умолчанию 30 сек)
        """
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()
        self.ttl_seconds = ttl_seconds
        logger.info(f"BalanceCache initialized with TTL={ttl_seconds}s")
    
    def _make_key(self, account_type: str, coin: Optional[str] = None) -> str:
        """Создает ключ для кэша"""
        coin_part = coin or "ALL"
        return f"{account_type}:{coin_part}"
    
    def get(self, account_type: str, coin: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Получить баланс из кэша
        
        Args:
            account_type: Тип счета (SPOT, CONTRACT, UNIFIED)
            coin: Монета (опционально)
        
        Returns:
            Данные баланса или None если кэш истек или отсутствует
        """
        key = self._make_key(account_type, coin)
        
        with self._lock:
            if key not in self._cache:
                return None
            
            cached_data = self._cache[key]
            cached_time = cached_data.get("timestamp", 0)
            current_time = time.time()
            
            # Проверяем TTL
            if current_time - cached_time > self.ttl_seconds:
                # Кэш истек, удаляем
                del self._cache[key]
                logger.debug(f"Cache expired for {key}")
                return None
            
            logger.debug(f"Cache hit for {key}")
            return cached_data.get("data")
    
    def set(self, account_type: str, data: Dict[str, Any], coin: Optional[str] = None) -> None:
        """
        Сохранить баланс в кэш
        
        Args:
            account_type: Тип счета (SPOT, CONTRACT, UNIFIED)
            data: Данные баланса
            coin: Монета (опционально)
        """
        key = self._make_key(account_type, coin)
        
        with self._lock:
            self._cache[key] = {
                "data": data,
                "timestamp": time.time()
            }
            logger.debug(f"Cached balance for {key}")
    
    def clear(self) -> None:
        """Очистить весь кэш"""
        with self._lock:
            self._cache.clear()
            logger.info("BalanceCache cleared")
    
    def invalidate(self, account_type: Optional[str] = None, coin: Optional[str] = None) -> None:
        """
        Инвалидировать кэш для конкретного счета/монеты
        
        Args:
            account_type: Тип счета (если None - инвалидирует все)
            coin: Монета (если None - инвалидирует все монеты для account_type)
        """
        with self._lock:
            if account_type is None:
                # Инвалидируем все
                self._cache.clear()
                logger.info("All cache invalidated")
            else:
                if coin is None:
                    # Инвалидируем все монеты для account_type
                    keys_to_remove = [k for k in self._cache.keys() if k.startswith(f"{account_type}:")]
                    for key in keys_to_remove:
                        del self._cache[key]
                    logger.info(f"Cache invalidated for {account_type}")
                else:
                    # Инвалидируем конкретную монету
                    key = self._make_key(account_type, coin)
                    if key in self._cache:
                        del self._cache[key]
                        logger.info(f"Cache invalidated for {key}")


# Глобальный экземпляр кэша
_balance_cache = BalanceCache(ttl_seconds=30)


def get_balance_cache() -> BalanceCache:
    """Получить глобальный экземпляр кэша"""
    return _balance_cache


def get_account_type_for_category(category: str, prefer_unified: bool = True) -> str:
    """
    Определяет правильный accountType для category
    
    Логика:
    - Для spot: SPOT (или UNIFIED если включен UTA)
    - Для linear/inverse: CONTRACT (или UNIFIED если включен UTA)
    
    Args:
        category: "spot", "linear", "inverse"
        prefer_unified: Если True, предпочитает UNIFIED для всех категорий (UTA режим)
    
    Returns:
        "SPOT", "CONTRACT", или "UNIFIED"
    """
    if category == "spot":
        # Для spot можно использовать SPOT или UNIFIED (если включен UTA)
        return "UNIFIED" if prefer_unified else "SPOT"
    elif category in ["linear", "inverse"]:
        # Для futures можно использовать CONTRACT или UNIFIED (если включен UTA)
        return "UNIFIED" if prefer_unified else "CONTRACT"
    else:
        # По умолчанию UNIFIED (наиболее универсальный)
        return "UNIFIED"


def get_all_account_balances(
    session: HTTP, 
    coin: Optional[str] = None,
    use_cache: bool = True,
    cache: Optional[BalanceCache] = None
) -> Dict[str, Any]:
    """
    Получает балансы со всех типов счетов (SPOT, CONTRACT, UNIFIED)
    С поддержкой кэширования для уменьшения количества API запросов
    
    Args:
        session: Pybit HTTP session
        coin: Опционально, конкретная монета (например "USDT")
        use_cache: Использовать кэш (по умолчанию True)
        cache: Экземпляр кэша (если None, используется глобальный)
    
    Returns:
        Словарь с балансами по типам счетов:
        {
            "spot": {"total": 0.0, "available": 0.0, "success": True/False},
            "contract": {"total": 0.0, "available": 0.0, "success": True/False},
            "unified": {"total": 0.0, "available": 0.0, "success": True/False},
            "total": 0.0,
            "available": 0.0
        }
    """
    if cache is None:
        cache = get_balance_cache()
    
    account_types = ["SPOT", "CONTRACT", "UNIFIED"]
    balances = {
        "spot": {"total": 0.0, "available": 0.0, "success": False},
        "contract": {"total": 0.0, "available": 0.0, "success": False},
        "unified": {"total": 0.0, "available": 0.0, "success": False},
        "total": 0.0,
        "available": 0.0
    }
    
    for account_type in account_types:
        # Пробуем получить из кэша
        cached_balance = None
        if use_cache:
            cached_balance = cache.get(account_type, coin)
        
        if cached_balance is not None:
            # Используем кэшированные данные
            key = account_type.lower()
            if key in balances:
                balances[key] = cached_balance
                balances["total"] += cached_balance.get("total", 0.0)
                balances["available"] += cached_balance.get("available", 0.0)
            continue
        
        # Кэш не найден или истек, делаем API запрос
        try:
            wallet_response = session.get_wallet_balance(
                accountType=account_type,
                coin=coin
            )
            
            if wallet_response.get("retCode") == 0:
                wallet_data = wallet_response.get("result", {}).get("list", [{}])
                
                if wallet_data:
                    # Получаем данные первой записи (обычно одна запись)
                    account_data = wallet_data[0]
                    coin_list = account_data.get("coin", [])
                    
                    # Если указана монета, ищем её, иначе берем первую доступную
                    if coin:
                        target_coin = next((c for c in coin_list if c.get("coin") == coin), {})
                    else:
                        # Без указания монеты суммируем все монеты или берем первую
                        target_coin = coin_list[0] if coin_list else {}
                    
                    if target_coin:
                        wallet_balance_str = target_coin.get("walletBalance", "0")
                        available_str = target_coin.get("availableToWithdraw", "0")
                        
                        total = float(wallet_balance_str) if wallet_balance_str and wallet_balance_str != "" else 0.0
                        available = float(available_str) if available_str and available_str != "" else 0.0
                        
                        # Сохраняем в правильный ключ
                        key = account_type.lower()
                        balance_data = {
                            "total": total,
                            "available": available,
                            "success": True
                        }
                        
                        if key == "spot":
                            balances["spot"] = balance_data
                        elif key == "contract":
                            balances["contract"] = balance_data
                        elif key == "unified":
                            balances["unified"] = balance_data
                        
                        # Кэшируем результат
                        if use_cache:
                            cache.set(account_type, balance_data, coin)
                        
                        # Суммируем общий баланс
                        balances["total"] += total
                        balances["available"] += available
                        
        except Exception as e:
            logger.debug(f"Failed to get balance for {account_type}: {e}")
            # Продолжаем проверку других типов счетов
            continue
    
    return balances


class TradingOperations:
    """Управление торговыми операциями на Bybit"""
    
    def __init__(self, api_key: str, api_secret: str, testnet: bool = False):
        """
        Инициализация trading client
        
        Args:
            api_key: Bybit API key
            api_secret: Bybit API secret
            testnet: Use testnet (default: False)
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        
        # Инициализация Bybit HTTP client
        self.session = HTTP(
            testnet=testnet,
            api_key=api_key,
            api_secret=api_secret
        )
        
        logger.info(f"Trading Operations initialized ({'testnet' if testnet else 'mainnet'})")
        
        # Базовый URL для API
        self.base_url = "https://api-testnet.bybit.com" if testnet else "https://api.bybit.com"
    
    def _generate_signature(self, params: Dict[str, Any], timestamp: int, recv_window: int = 5000, use_json_body: bool = True) -> str:
        """Генерация подписи для Bybit API v5
        
        Для POST запросов с JSON body (use_json_body=True):
        - Используем сырой JSON body: timestamp + api_key + recv_window + json_string
        
        Для GET запросов (use_json_body=False):
        - Формат: timestamp + api_key + recv_window + query_string
        """
        if use_json_body:
            # Для POST: используем JSON строку напрямую
            json_body = json.dumps(params, separators=(',', ':'))  # Без пробелов
            sign_string = f"{timestamp}{self.api_key}{recv_window}{json_body}"
        else:
            # Для GET: формат key=value&key2=value2
            param_str = ""
            if params:
                sorted_params = sorted(params.items())
                param_str = "&".join([f"{k}={v}" for k, v in sorted_params])
            sign_string = f"{timestamp}{self.api_key}{recv_window}{param_str}"
        
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            sign_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    def _place_order_direct_http(self, order_params: Dict[str, Any]) -> Dict[str, Any]:
        """Размещение ордера через прямой HTTP запрос к Bybit API v5"""
        endpoint = "/v5/order/create"
        url = f"{self.base_url}{endpoint}"
        
        timestamp = int(time.time() * 1000)
        recv_window = 5000
        
        # Параметры запроса - сохраняем оригинальные типы для JSON
        # Bybit API v5 ожидает правильные типы в JSON (не все строки)
        params = {}
        for k, v in order_params.items():
            if v is not None:
                # Сохраняем оригинальные типы, но конвертируем некоторые значения
                if isinstance(v, bool):
                    params[k] = v  # Boolean остается boolean
                elif isinstance(v, (int, float)):
                    # Числа конвертируем в строки для Bybit API
                    params[k] = str(v)
                else:
                    params[k] = str(v)
        
        # Генерируем подпись используя JSON body
        signature = self._generate_signature(params, timestamp, recv_window, use_json_body=True)
        
        # Заголовки для Bybit API v5
        headers = {
            "X-BAPI-API-KEY": self.api_key,
            "X-BAPI-TIMESTAMP": str(timestamp),
            "X-BAPI-RECV-WINDOW": str(recv_window),
            "X-BAPI-SIGN": signature,
            "Content-Type": "application/json"
        }
        
        # Отправляем запрос с retry механизмом
        logger.info(f"Direct HTTP request to {url}")
        logger.info(f"Request params: {params}")
        logger.info(f"Request headers: {dict((k, v if k != 'X-BAPI-SIGN' else '***') for k, v in headers.items())}")
        
        max_retries = 3
        # Используем tuple timeout: (connect_timeout, read_timeout)
        # connect_timeout - для установки соединения и SSL handshake
        # read_timeout - для чтения ответа
        timeout = (15, 30)  # 15 сек на подключение, 30 сек на чтение
        
        # Создаем сессию с настройками для лучшей работы с SSL
        session = requests.Session()
        # Увеличиваем количество повторных попыток для SSL
        session.mount('https://', requests.adapters.HTTPAdapter(max_retries=2))
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Attempt {attempt + 1}/{max_retries} to {url}")
                logger.debug(f"Request params: {json.dumps(params, indent=2)}")
                
                # Используем session.post для лучшего контроля
                response = session.post(
                    url, 
                    json=params, 
                    headers=headers, 
                    timeout=timeout,
                    verify=True  # Проверяем SSL сертификат
                )
                response.raise_for_status()
                logger.info(f"Request successful: HTTP {response.status_code}")
                break  # Успешно, выходим из цикла
            except requests.exceptions.SSLError as ssl_err:
                logger.error(f"SSL error on attempt {attempt + 1}: {ssl_err}")
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 3
                    logger.warning(f"Retrying SSL connection in {wait_time}s...")
                    time.sleep(wait_time)
                    # Обновляем timestamp и подпись
                    timestamp = int(time.time() * 1000)
                    headers["X-BAPI-TIMESTAMP"] = str(timestamp)
                    signature = self._generate_signature(params, timestamp, recv_window, use_json_body=True)
                    headers["X-BAPI-SIGN"] = signature
                else:
                    raise Exception(f"SSL connection failed after {max_retries} attempts: {str(ssl_err)}")
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2  # Экспоненциальная задержка: 2, 4, 6 секунд
                    logger.warning(f"Request failed (attempt {attempt + 1}/{max_retries}): {e}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    # Обновляем timestamp и подпись для нового запроса
                    timestamp = int(time.time() * 1000)
                    headers["X-BAPI-TIMESTAMP"] = str(timestamp)
                    signature = self._generate_signature(params, timestamp, recv_window, use_json_body=True)
                    headers["X-BAPI-SIGN"] = signature
                else:
                    raise Exception(f"HTTP request failed after {max_retries} attempts: {str(e)}")
        
        # Закрываем сессию после успешного запроса
        try:
            session.close()
        except:
            pass
        
        # Обрабатываем успешный ответ с безопасным парсингом
        try:
            # Безопасный парсинг JSON ответа
            response_text = response.text
            logger.debug(f"Raw HTTP response text: {response_text[:500]}")  # Логируем первые 500 символов
            
            # Проверяем, что ответ - это валидный JSON
            if isinstance(response_text, str):
                try:
                    result = json.loads(response_text)
                except json.JSONDecodeError as json_err:
                    logger.error(f"Failed to parse JSON response: {json_err}")
                    logger.error(f"Response text: {response_text}")
                    raise Exception(f"Invalid JSON response from API: {str(json_err)}")
            else:
                # Если response.text уже не строка, пробуем response.json()
                result = response.json()
            
            # Проверяем, что result - это словарь
            if not isinstance(result, dict):
                logger.error(f"Unexpected response type: {type(result)}, value: {result}")
                raise Exception(f"Expected dict response, got {type(result)}")
            
            logger.info(f"Direct HTTP response: {result}")
            
            # Безопасное извлечение retCode и retMsg
            ret_code = result.get("retCode")
            ret_msg = result.get("retMsg", "Unknown error")
            
            if ret_code != 0:
                error_msg = f"Bybit API error (retCode={ret_code}): {ret_msg}"
                logger.error(error_msg)
                raise Exception(error_msg)
            
            return result
            
        except KeyError as ke:
            # Если возникает KeyError при обработке ответа, логируем детали
            error_key = str(ke)
            logger.error(f"KeyError processing API response: {error_key}")
            logger.error(f"Response keys: {list(result.keys()) if isinstance(result, dict) else 'N/A'}")
            logger.error(f"Response type: {type(result)}")
            logger.error(f"Response value: {result}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise Exception(f"KeyError processing API response: {error_key}. Response structure may be unexpected.")
    
    def _set_leverage_direct_http(self, leverage_params: Dict[str, Any]) -> Dict[str, Any]:
        """Установка leverage через прямой HTTP запрос к Bybit API v5"""
        endpoint = "/v5/position/set-leverage"
        url = f"{self.base_url}{endpoint}"
        
        timestamp = int(time.time() * 1000)
        recv_window = 5000
        
        # Параметры запроса
        params = {}
        for k, v in leverage_params.items():
            if v is not None:
                params[k] = str(v)
        
        # Генерируем подпись используя JSON body
        signature = self._generate_signature(params, timestamp, recv_window, use_json_body=True)
        
        # Заголовки для Bybit API v5
        headers = {
            "X-BAPI-API-KEY": self.api_key,
            "X-BAPI-TIMESTAMP": str(timestamp),
            "X-BAPI-RECV-WINDOW": str(recv_window),
            "X-BAPI-SIGN": signature,
            "Content-Type": "application/json"
        }
        
        # Отправляем запрос с улучшенной обработкой SSL
        logger.info(f"Setting leverage via direct HTTP: {params}")
        
        # Используем сессию с настройками для SSL
        session = requests.Session()
        session.mount('https://', requests.adapters.HTTPAdapter(max_retries=2))
        timeout = (15, 30)  # 15 сек на подключение, 30 сек на чтение
        
        try:
            response = session.post(
                url, 
                json=params, 
                headers=headers, 
                timeout=timeout,
                verify=True
            )
            response.raise_for_status()
            
            # Безопасный парсинг JSON ответа
            try:
                response_text = response.text
                logger.debug(f"Raw leverage response text: {response_text[:500]}")
                
                # Проверяем, что ответ - это валидный JSON
                if isinstance(response_text, str):
                    try:
                        result = json.loads(response_text)
                    except json.JSONDecodeError as json_err:
                        logger.error(f"Failed to parse JSON response: {json_err}")
                        logger.error(f"Response text: {response_text}")
                        raise Exception(f"Invalid JSON response from API: {str(json_err)}")
                else:
                    result = response.json()
                
                # Проверяем, что result - это словарь
                if not isinstance(result, dict):
                    logger.error(f"Unexpected leverage response type: {type(result)}, value: {result}")
                    raise Exception(f"Expected dict response, got {type(result)}")
                
                logger.info(f"Leverage response: {result}")
                
                # Безопасное извлечение retCode и retMsg
                ret_code = result.get("retCode")
                ret_msg = result.get("retMsg", "Unknown error")
                
                if ret_code != 0:
                    error_msg = f"Bybit API error (retCode={ret_code}): {ret_msg}"
                    logger.error(error_msg)
                    raise Exception(error_msg)
                
                return result
                
            except KeyError as ke:
                # Если возникает KeyError при обработке ответа, логируем детали
                error_key = str(ke)
                logger.error(f"KeyError processing leverage API response: {error_key}")
                logger.error(f"Response keys: {list(result.keys()) if isinstance(result, dict) else 'N/A'}")
                logger.error(f"Response type: {type(result)}")
                logger.error(f"Response value: {result}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                raise Exception(f"KeyError processing leverage API response: {error_key}. Response structure may be unexpected.")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_body = e.response.json()
                    logger.error(f"Error response body: {error_body}")
                except:
                    logger.error(f"Error response text: {e.response.text}")
            raise Exception(f"HTTP request failed: {str(e)}")
        finally:
            # Закрываем сессию в любом случае
            try:
                session.close()
            except:
                pass
    
    def invalidate_balance_cache(self, account_type: Optional[str] = None, coin: Optional[str] = None) -> None:
        """
        Инвалидировать кэш балансов
        
        Используйте после торговых операций для обновления балансов
        
        Args:
            account_type: Тип счета (SPOT, CONTRACT, UNIFIED) или None для всех
            coin: Монета (опционально)
        """
        cache = get_balance_cache()
        cache.invalidate(account_type, coin)
        logger.info(f"Balance cache invalidated: account_type={account_type}, coin={coin}")
    
    async def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: Optional[float] = None,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        category: str = "spot",
        leverage: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Разместить ордер на Bybit
        
        Args:
            symbol: Торговая пара (BTCUSDT, ETHUSDT)
            side: "Buy" или "Sell"
            order_type: "Market" или "Limit"
            quantity: Размер позиции
            price: Цена (для Limit)
            stop_loss: Stop-loss price
            take_profit: Take-profit price
            category: "spot", "linear", "inverse"
            
        Returns:
            Детали размещённого ордера
        """
        logger.info(f"Placing order: {side} {quantity} {symbol} @ {price or 'Market'}")
        logger.info(f"Order parameters: category={category}, order_type={order_type}, leverage={leverage}")
        logger.info(f"Category type: {type(category)}, value: {repr(category)}")
        
        try:
            # Валидация входных параметров
            if not symbol or not symbol.strip():
                raise ValueError("Symbol is required and cannot be empty")
            if side not in ["Buy", "Sell"]:
                raise ValueError(f"Side must be 'Buy' or 'Sell'. Got: {side}")
            if order_type not in ["Market", "Limit"]:
                raise ValueError(f"Order type must be 'Market' or 'Limit'. Got: {order_type}")
            if quantity <= 0:
                raise ValueError(f"Quantity must be positive. Got: {quantity}")
            if order_type == "Limit" and (not price or price <= 0):
                raise ValueError(f"Price is required for Limit orders and must be positive. Got: {price}")
            if category not in ["spot", "linear", "inverse"]:
                raise ValueError(f"Category must be 'spot', 'linear', or 'inverse'. Got: {category}")
            
            logger.info(f"Validation passed. Proceeding with order placement for category: {category}")
            if leverage and (leverage < 1 or leverage > 125):
                raise ValueError(f"Leverage must be between 1 and 125. Got: {leverage}")
            
            # Параметры ордера
            # ВАЖНО: Для фьючерсов Pybit может требовать другие параметры
            order_params = {
                "category": category,
                "symbol": symbol,
                "side": side,
                "orderType": order_type,
                "qty": str(quantity)
            }
            
            # Для spot ордеров добавляем timeInForce
            if category == "spot":
                if order_type == "Market":
                    order_params["timeInForce"] = "IOC"  # Immediate or Cancel для Market
                elif order_type == "Limit":
                    order_params["timeInForce"] = "GTC"  # Good Till Cancel для Limit
            
            # Для futures добавляем timeInForce и другие обязательные параметры
            if category in ["linear", "inverse"]:
                # Для фьючерсов timeInForce обязателен
                if order_type == "Market":
                    order_params["timeInForce"] = "IOC"  # Immediate or Cancel для Market
                elif order_type == "Limit":
                    order_params["timeInForce"] = "GTC"  # Good Till Cancel для Limit
                
                # Для фьючерсов может потребоваться positionIdx (0=one-way, 1=Buy side, 2=Sell side)
                # По умолчанию используем 0 (one-way mode)
                order_params["positionIdx"] = 0
                
                # Дополнительные параметры для фьючерсов
                order_params["reduceOnly"] = False
                order_params["closeOnTrigger"] = False
                
                if stop_loss:
                    order_params["stopLoss"] = str(stop_loss)
                if take_profit:
                    order_params["takeProfit"] = str(take_profit)
            
            # Добавляем цену для Limit
            if order_type == "Limit" and price:
                order_params["price"] = str(price)
            
            # Устанавливаем leverage перед открытием позиции
            # Для фьючерсов используем прямой HTTP запрос
            # ВАЖНО: Делаем это ДО размещения ордера, но после формирования order_params
            if leverage and category in ["linear", "inverse"]:
                try:
                    logger.info(f"Setting leverage {leverage}x for {symbol} ({category})")
                    # Используем прямой HTTP запрос для установки leverage
                    leverage_params = {
                        "category": category,
                        "symbol": symbol,
                        "buyLeverage": str(leverage),
                        "sellLeverage": str(leverage)
                    }
                    logger.debug(f"Leverage params: {leverage_params}")
                    leverage_response = self._set_leverage_direct_http(leverage_params)
                    logger.debug(f"Leverage response: {leverage_response}")
                    
                    # Безопасная проверка ответа с детальным логированием
                    logger.debug(f"Leverage response type: {type(leverage_response)}")
                    logger.debug(f"Leverage response value: {leverage_response}")
                    
                    if isinstance(leverage_response, dict):
                        # Безопасное извлечение retCode
                        ret_code = leverage_response.get("retCode")
                        if ret_code is not None and ret_code != 0:
                            ret_msg = leverage_response.get("retMsg", "Unknown error")
                            logger.warning(f"Failed to set leverage: {ret_msg} (retCode={ret_code})")
                        else:
                            logger.info(f"Leverage set to {leverage}x for {symbol}")
                    elif isinstance(leverage_response, str):
                        # Если ответ - строка, пробуем распарсить как JSON
                        logger.warning(f"Leverage response is string, attempting to parse as JSON")
                        try:
                            leverage_response = json.loads(leverage_response)
                            if isinstance(leverage_response, dict):
                                ret_code = leverage_response.get("retCode")
                                if ret_code is not None and ret_code != 0:
                                    ret_msg = leverage_response.get("retMsg", "Unknown error")
                                    logger.warning(f"Failed to set leverage: {ret_msg} (retCode={ret_code})")
                                else:
                                    logger.info(f"Leverage set to {leverage}x for {symbol}")
                        except json.JSONDecodeError as json_err:
                            logger.error(f"Failed to parse leverage response as JSON: {json_err}")
                            logger.warning(f"Leverage setup failed, continuing with order placement")
                    else:
                        logger.warning(f"Unexpected leverage response format: {type(leverage_response)}")
                except KeyError as ke:
                    error_key = str(ke)
                    logger.error(f"KeyError in leverage setup: {error_key}", exc_info=True)
                    logger.error(f"Leverage response at error: {leverage_response if 'leverage_response' in locals() else 'N/A'}")
                    logger.error(f"Leverage response type: {type(leverage_response) if 'leverage_response' in locals() else 'N/A'}")
                    # Не прерываем выполнение, продолжаем с размещением ордера
                    logger.warning(f"Leverage setup failed with KeyError, continuing with order placement")
                except Exception as e:
                    logger.warning(f"Error setting leverage: {e}", exc_info=True)
                    # Не прерываем выполнение, продолжаем с размещением ордера
            elif leverage and category == "spot":
                # Для spot leverage не используется
                logger.info("Leverage is not applicable for spot trading")
            
            # Размещаем ордер с детальным логированием
            logger.info(f"Placing order with params: {order_params}")
            logger.info(f"Params type: {type(order_params)}")
            logger.info(f"Params keys: {list(order_params.keys())}")
            logger.info(f"Params values: {list(order_params.values())}")
            
            # КРИТИЧНО: Для ВСЕХ категорий используем прямой HTTP запрос
            # так как Pybit имеет проблемы с обработкой ответов (особенно для фьючерсов)
            # Это более надежный метод, который работает для всех категорий
            logger.info(f"Using direct HTTP request for {category} order (more reliable than Pybit)")
            try:
                response = self._place_order_direct_http(order_params)
                logger.info("Direct HTTP request successful")
            except Exception as http_error:
                logger.error(f"Direct HTTP request failed: {http_error}")
                # Fallback: пробуем через Pybit только для spot
                if category == "spot":
                    logger.info("Trying Pybit as fallback for spot order")
                    try:
                        # Убираем category из параметров для Pybit (spot по умолчанию)
                        order_params_no_cat = {k: v for k, v in order_params.items() if k != "category"}
                        response = self.session.place_order(**order_params_no_cat)
                        logger.info("Pybit fallback successful")
                    except Exception as pybit_error:
                        logger.error(f"Pybit fallback also failed: {pybit_error}")
                        raise Exception(f"Failed to place order via both direct HTTP and Pybit: {str(http_error)}")
                else:
                    raise Exception(f"Failed to place {category} order via direct HTTP: {str(http_error)}")
            
            # Безопасная проверка и нормализация ответа
            # Pybit может возвращать ответ в разных форматах
            normalized_response = None
            
            # Если response - строка, пробуем распарсить как JSON
            if isinstance(response, str):
                logger.warning(f"Response is string, attempting to parse as JSON")
                try:
                    normalized_response = json.loads(response)
                except json.JSONDecodeError as json_err:
                    logger.error(f"Failed to parse response as JSON: {json_err}")
                    logger.error(f"Response text: {response[:500]}")
                    raise Exception(f"Invalid JSON response: {str(json_err)}")
            elif isinstance(response, dict):
                normalized_response = response
            else:
                logger.error(f"Unexpected response type: {type(response)}")
                logger.error(f"Response value: {response}")
                raise Exception(f"Unexpected response type: {type(response)}. Expected dict or str.")
            
            # Теперь работаем с нормализованным ответом
            response = normalized_response
            
            # Логируем полный ответ для отладки
            logger.info(f"Place order response: {response}")
            logger.info(f"Response type: {type(response)}")
            if isinstance(response, dict):
                logger.info(f"Response keys: {list(response.keys())}")
                logger.info(f"Response retCode: {response.get('retCode')}")
                logger.info(f"Response retMsg: {response.get('retMsg')}")
                if 'result' in response:
                    result = response.get('result')
                    logger.info(f"Result type: {type(result)}")
                    if isinstance(result, dict):
                        logger.info(f"Result keys: {list(result.keys())}")
                    elif isinstance(result, list) and len(result) > 0:
                        logger.info(f"Result[0] type: {type(result[0])}")
                        if isinstance(result[0], dict):
                            logger.info(f"Result[0] keys: {list(result[0].keys())}")
            
            # Безопасная проверка структуры ответа
            if not isinstance(response, dict):
                raise Exception(f"Unexpected response type after normalization: {type(response)}. Expected dict.")
            
            # Безопасное извлечение retCode и retMsg
            ret_code = response.get("retCode")
            ret_msg = response.get("retMsg", "Unknown error")
            
            logger.info(f"Response retCode: {ret_code}, retMsg: {ret_msg}")
            logger.info(f"Response keys: {list(response.keys())}")
            
            # Если ответ пришел от прямого HTTP запроса, он уже обработан
            # и имеет правильную структуру
            if ret_code == 0:
                # Безопасное извлечение result
                result = response.get("result")
                if result is None:
                    logger.warning("Response has retCode=0 but no 'result' field. Response: " + str(response))
                    # Пробуем найти orderId в самом response
                    order_id = response.get("orderId") or response.get("order_id")
                    if order_id:
                        logger.info(f"Found orderId in response root: {order_id}")
                        order_data = response
                    else:
                        raise Exception("Response has retCode=0 but no 'result' field and no orderId in root")
                else:
                    # Если result - это список, берем первый элемент
                    if isinstance(result, list):
                        if len(result) > 0:
                            order_data = result[0]
                        else:
                            raise Exception("Response result is empty list")
                    elif isinstance(result, dict):
                        order_data = result
                    else:
                        raise Exception(f"Unexpected result type: {type(result)}")
                
                # Безопасное извлечение orderId
                order_id = order_data.get("orderId") or order_data.get("order_id") or order_data.get("id")
                if not order_id:
                    logger.warning(f"Order ID not found in response. Available keys: {order_data.keys()}")
                    # Пытаемся использовать symbol + timestamp как временный ID
                    order_id = f"{symbol}_{int(time.time())}"
                
                logger.info(f"Order placed successfully: {order_id}")
                
                # Инвалидируем кэш баланса после размещения ордера
                account_type = get_account_type_for_category(category, prefer_unified=True)
                self.invalidate_balance_cache(account_type=account_type)
                
                # Для spot: размещаем отдельные SL/TP ордера если нужно
                if category == "spot" and (stop_loss or take_profit) and order_id:
                    await self._place_spot_sl_tp(
                        symbol, side, quantity, 
                        order_id,
                        stop_loss, take_profit
                    )
                
                return {
                    "success": True,
                    "order_id": order_id,
                    "symbol": symbol,
                    "side": side,
                    "type": order_type,
                    "quantity": quantity,
                    "price": price or order_data.get("price") or order_data.get("avgPrice"),
                    "stop_loss": stop_loss,
                    "take_profit": take_profit,
                    "status": order_data.get("orderStatus") or order_data.get("status") or "filled",
                    "timestamp": datetime.now().isoformat(),
                    "message": "Order placed successfully",
                    "raw_response": order_data  # Добавляем для отладки
                }
            else:
                error_msg = f"Order failed (retCode={ret_code}): {ret_msg}"
                logger.error(error_msg)
                raise Exception(error_msg)
                
        except KeyError as e:
            error_key = str(e)
            logger.error(f"KeyError in place_order: {error_key}")
            logger.error(f"KeyError type: {type(e)}")
            logger.error(f"KeyError args: {e.args if hasattr(e, 'args') else 'N/A'}")
            logger.error(f"KeyError repr: {repr(e)}")
            # Логируем traceback для понимания где именно произошла ошибка
            logger.error(f"Traceback: {traceback.format_exc()}")
            logger.error(f"Category at error time: {category}")
            logger.error(f"Order params at error time: {order_params if 'order_params' in locals() else 'N/A'}")
            
            # КРИТИЧНО: Если ошибка связана с category и это фьючерсы, пробуем прямой HTTP
            if ('"category"' in error_key or "'category'" in error_key) and category in ["linear", "inverse"]:
                logger.info("KeyError related to category for futures, trying direct HTTP as fallback")
                try:
                    if 'order_params' in locals():
                        logger.info("Attempting direct HTTP fallback with order_params")
                        response = self._place_order_direct_http(order_params)
                        logger.info("Direct HTTP fallback successful")
                        # Продолжаем обработку ответа
                        ret_code = response.get("retCode")
                        if ret_code == 0:
                            result = response.get("result")
                            if isinstance(result, list) and len(result) > 0:
                                order_data = result[0]
                            elif isinstance(result, dict):
                                order_data = result
                            else:
                                raise Exception("Unexpected result format")
                            order_id = order_data.get("orderId") or order_data.get("order_id")
                            return {
                                "success": True,
                                "order_id": order_id,
                                "symbol": symbol,
                                "side": side,
                                "type": order_type,
                                "quantity": quantity,
                                "message": "Order placed successfully via direct HTTP fallback"
                            }
                except Exception as fallback_err:
                    logger.error(f"Direct HTTP fallback also failed: {fallback_err}", exc_info=True)
            
            # Если не удалось исправить через fallback, возвращаем ошибку
            return {
                "success": False,
                "error": f"KeyError: {error_key}",
                "message": f"Failed to place order: KeyError accessing {error_key}. Check API response format.",
                "error_type": "KeyError",
                "error_details": {
                    "key": error_key,
                    "type": str(type(e)),
                    "args": list(e.args) if hasattr(e, 'args') else []
                }
            }
        except Exception as e:
            error_msg = str(e)
            error_type = type(e).__name__
            logger.error(f"Error placing order: {error_type}: {error_msg}", exc_info=True)
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return {
                "success": False,
                "error": error_msg,
                "error_type": error_type,
                "message": f"Failed to place order: {error_type}: {error_msg}",
                "traceback": traceback.format_exc()
            }
    
    async def _place_spot_sl_tp(
        self,
        symbol: str,
        side: str,
        quantity: float,
        parent_order_id: str,
        stop_loss: Optional[float],
        take_profit: Optional[float]
    ):
        """Разместить SL/TP для spot ордера"""
        
        opposite_side = "Sell" if side == "Buy" else "Buy"
        
        try:
            # Stop-Loss (Stop-Market order)
            if stop_loss:
                sl_params = {
                    "category": "spot",
                    "symbol": symbol,
                    "side": opposite_side,
                    "orderType": "Market",
                    "qty": str(quantity),
                    "triggerPrice": str(stop_loss),
                    "triggerBy": "LastPrice"
                }
                sl_response = self.session.place_order(**sl_params)
                if isinstance(sl_response, dict) and sl_response.get("retCode") == 0:
                    logger.info(f"Stop-Loss placed: {sl_response.get('result', {}).get('orderId')}")
            
            # Take-Profit (Limit order)
            if take_profit:
                tp_params = {
                    "category": "spot",
                    "symbol": symbol,
                    "side": opposite_side,
                    "orderType": "Limit",
                    "qty": str(quantity),
                    "price": str(take_profit)
                }
                tp_response = self.session.place_order(**tp_params)
                if isinstance(tp_response, dict) and tp_response.get("retCode") == 0:
                    logger.info(f"Take-Profit placed: {tp_response.get('result', {}).get('orderId')}")
                    
        except Exception as e:
            logger.warning(f"Failed to place SL/TP orders: {e}")
    
    async def close_position(
        self,
        symbol: str,
        category: str = "linear",
        reason: str = "Manual close"
    ) -> Dict[str, Any]:
        """
        Закрыть открытую позицию
        
        Args:
            symbol: Торговая пара
            category: "spot", "linear", "inverse"
            reason: Причина закрытия
            
        Returns:
            Детали закрытой позиции
        """
        logger.info(f"Closing position: {symbol} ({category}). Reason: {reason}")
        
        try:
            # Для spot - получаем баланс и продаём актив
            if category == "spot":
                # Получаем баланс базовой монеты
                # Убираем USDT, USDC, BUSD и другие стейблкоины из символа
                base_coin = symbol.replace("USDT", "").replace("USDC", "").replace("BUSD", "").replace("DAI", "")
                
                if not base_coin:
                    raise Exception(f"Could not extract base coin from symbol: {symbol}")
                
                # Определяем правильный accountType для spot категории
                # Пробуем сначала SPOT (для Classic Account), затем UNIFIED (для UTA)
                account_types_to_try = [
                    get_account_type_for_category("spot", prefer_unified=False),  # SPOT
                    get_account_type_for_category("spot", prefer_unified=True)   # UNIFIED
                ]
                
                wallet_response = None
                for account_type in account_types_to_try:
                    try:
                        wallet_response = self.session.get_wallet_balance(accountType=account_type, coin=base_coin)
                        if wallet_response.get("retCode") == 0:
                            logger.info(f"Successfully retrieved balance from {account_type} account")
                            break
                    except Exception as e:
                        logger.debug(f"Failed to get balance from {account_type}: {e}")
                        continue
                
                # Если все попытки не удались, пробуем CONTRACT (на случай если это futures spot)
                if not wallet_response or wallet_response.get("retCode") != 0:
                    try:
                        wallet_response = self.session.get_wallet_balance(accountType="CONTRACT", coin=base_coin)
                        if wallet_response.get("retCode") == 0:
                            logger.info("Successfully retrieved balance from CONTRACT account")
                    except Exception as e:
                        logger.debug(f"Failed to get balance from CONTRACT: {e}")
                
                # Проверяем что получили валидный ответ
                if not wallet_response or wallet_response.get("retCode") != 0:
                    error_msg = wallet_response.get('retMsg', 'Unknown error') if wallet_response else 'No response from API'
                    logger.error(f"Failed to get wallet balance: {error_msg}")
                    return {
                        "success": False,
                        "error": f"Failed to get wallet balance: {error_msg}",
                        "message": f"Could not retrieve {base_coin} balance from any account type (SPOT, UNIFIED, CONTRACT)"
                    }
                
                # Извлекаем баланс из ответа
                result = wallet_response.get("result", {})
                coin_list = result.get("list", [])
                
                if not coin_list:
                    return {
                        "success": False,
                        "error": "No wallet data found",
                        "message": f"No wallet data available for {base_coin}"
                    }
                
                # Ищем монету в списке
                account_coins = coin_list[0].get("coin", [])
                base_coin_data = next((c for c in account_coins if c.get("coin") == base_coin), None)
                
                if not base_coin_data:
                    return {
                        "success": False,
                        "error": f"No {base_coin} found in wallet",
                        "message": f"No {base_coin} balance available"
                    }
                
                # Получаем доступный баланс (приоритет: availableToWithdraw > walletBalance)
                # availableToWithdraw - доступно для вывода/торговли
                # walletBalance - общий баланс (может быть заблокирован)
                available_to_withdraw = base_coin_data.get("availableToWithdraw", "")
                wallet_balance = base_coin_data.get("walletBalance", "")
                
                # Конвертируем в float с безопасной обработкой пустых строк
                available_balance = 0.0
                if available_to_withdraw and available_to_withdraw != "":
                    try:
                        available_balance = float(available_to_withdraw)
                    except (ValueError, TypeError):
                        pass
                
                # Если availableToWithdraw не доступен, используем walletBalance
                if available_balance <= 0 and wallet_balance and wallet_balance != "":
                    try:
                        available_balance = float(wallet_balance)
                    except (ValueError, TypeError):
                        pass
                
                if available_balance <= 0:
                    return {
                        "success": False,
                        "error": f"No {base_coin} balance available",
                        "message": f"No {base_coin} balance available to sell (balance: {available_balance})"
                    }
                
                # Продаём весь доступный баланс
                close_order = {
                    "category": "spot",
                    "symbol": symbol,
                    "side": "Sell",
                    "orderType": "Market",
                    "qty": str(available_balance),
                    "timeInForce": "IOC"  # Immediate or Cancel для Market ордеров
                }
                
                response = self.session.place_order(**close_order)
                
                if response.get("retCode") == 0:
                    order_data = response.get("result", {})
                    logger.info(f"Spot position closed successfully: {symbol}, order: {order_data.get('orderId')}")
                    
                    # Инвалидируем кэш баланса после закрытия позиции
                    self.invalidate_balance_cache(account_type="SPOT", coin=base_coin)
                    
                    return {
                        "success": True,
                        "symbol": symbol,
                        "closed_at": datetime.now().isoformat(),
                        "reason": reason,
                        "size": available_balance,
                        "order_id": order_data.get("orderId"),
                        "message": "Spot position closed successfully"
                    }
                else:
                    error_msg = response.get('retMsg', 'Unknown error')
                    logger.error(f"Close order failed: {error_msg}")
                    raise Exception(f"Close failed: {error_msg}")
            
            # Для futures - используем стандартную логику
            else:
                # Получаем текущую позицию
                positions = self.session.get_positions(
                    category=category,
                    symbol=symbol
                )
                
                if positions.get("retCode") != 0:
                    # Если нет позиций - это нормально
                    if "10001" in str(positions.get("retMsg", "")) or "not found" in str(positions.get("retMsg", "")).lower():
                        return {
                            "success": False,
                            "message": f"No open position found for {symbol}"
                        }
                    raise Exception(f"Failed to get positions: {positions.get('retMsg')}")
                
                position_list = positions.get("result", {}).get("list", [])
                
                if not position_list or len(position_list) == 0:
                    return {
                        "success": False,
                        "message": f"No open position found for {symbol}"
                    }
                
                position = position_list[0]
                position_size = float(position.get("size", 0))
                
                if position_size == 0:
                    return {
                        "success": False,
                        "message": f"Position size is 0 for {symbol}"
                    }
                
                # Определяем сторону для закрытия
                position_side = position.get("side")
                close_side = "Sell" if position_side == "Buy" else "Buy"
                
                # Закрываем позицию market ордером
                close_order = {
                    "category": category,
                    "symbol": symbol,
                    "side": close_side,
                    "orderType": "Market",
                    "qty": str(position_size),
                    "reduceOnly": True  # Важно для futures
                }
                
                response = self.session.place_order(**close_order)
                
                if response.get("retCode") == 0:
                    logger.info(f"Position closed successfully: {symbol}")
                    
                    return {
                        "success": True,
                        "symbol": symbol,
                        "closed_at": datetime.now().isoformat(),
                        "reason": reason,
                        "size": position_size,
                        "pnl": position.get("unrealisedPnl"),
                        "pnl_pct": position.get("unrealisedPnlPct"),
                        "order_id": response.get("result", {}).get("orderId"),
                        "message": "Position closed successfully"
                    }
                else:
                    raise Exception(f"Close failed: {response.get('retMsg')}")
                
        except Exception as e:
            logger.error(f"Error closing position: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to close position: {str(e)}"
            }
    
    async def modify_position(
        self,
        symbol: str,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        category: str = "linear"
    ) -> Dict[str, Any]:
        """
        Изменить SL/TP открытой позиции
        
        Args:
            symbol: Торговая пара
            stop_loss: Новый stop-loss
            take_profit: Новый take-profit
            category: "linear", "inverse"
            
        Returns:
            Результат изменения
        """
        logger.info(f"Modifying position {symbol}: SL={stop_loss}, TP={take_profit}")
        
        try:
            # Для futures нужно получить positionIdx
            position_idx = 0
            if category in ["linear", "inverse"]:
                positions = self.session.get_positions(
                    category=category,
                    symbol=symbol
                )
                
                if positions.get("retCode") != 0:
                    raise Exception(f"Failed to get position: {positions.get('retMsg')}")
                
                position_list = positions.get("result", {}).get("list", [])
                if not position_list or len(position_list) == 0:
                    raise Exception(f"No open position found for {symbol}")
                
                # Получаем positionIdx из позиции
                position = position_list[0]
                position_idx = position.get("positionIdx", 0)
            
            params = {
                "category": category,
                "symbol": symbol,
                "positionIdx": position_idx
            }
            
            if stop_loss:
                params["stopLoss"] = str(stop_loss)
            if take_profit:
                params["takeProfit"] = str(take_profit)
            
            # Проверяем что хотя бы один параметр указан
            if not stop_loss and not take_profit:
                raise Exception("At least one of stop_loss or take_profit must be provided")
            
            # Валидация значений SL/TP
            if stop_loss and stop_loss <= 0:
                raise Exception(f"Stop loss must be positive. Got: {stop_loss}")
            if take_profit and take_profit <= 0:
                raise Exception(f"Take profit must be positive. Got: {take_profit}")
            
            logger.debug(f"Modifying position params: {params}")
            response = self.session.set_trading_stop(**params)
            
            # Безопасная проверка ответа
            if not isinstance(response, dict):
                raise Exception(f"Unexpected response type: {type(response)}")
            
            if response.get("retCode") == 0:
                logger.info(f"Position modified successfully: {symbol}")
                return {
                    "success": True,
                    "symbol": symbol,
                    "stop_loss": stop_loss,
                    "take_profit": take_profit,
                    "timestamp": datetime.now().isoformat(),
                    "message": "Position modified successfully"
                }
            else:
                error_msg = response.get('retMsg', 'Unknown error')
                logger.error(f"Modify failed: {error_msg}")
                raise Exception(f"Modify failed: {error_msg}")
                
        except Exception as e:
            logger.error(f"Error modifying position: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to modify position: {str(e)}"
            }
    
    async def cancel_order(
        self,
        order_id: str,
        symbol: str,
        category: str = "spot"
    ) -> Dict[str, Any]:
        """
        Отменить ордер
        
        Args:
            order_id: ID ордера
            symbol: Торговая пара
            category: Категория рынка
            
        Returns:
            Результат отмены
        """
        logger.info(f"Cancelling order: {order_id} for {symbol}")
        
        try:
            # Валидация параметров
            if not order_id or not order_id.strip():
                raise ValueError("Order ID is required and cannot be empty")
            if not symbol or not symbol.strip():
                raise ValueError("Symbol is required and cannot be empty")
            if category not in ["spot", "linear", "inverse"]:
                raise ValueError(f"Category must be 'spot', 'linear', or 'inverse'. Got: {category}")
            
            response = self.session.cancel_order(
                category=category,
                symbol=symbol,
                orderId=order_id
            )
            
            # Безопасная проверка ответа
            if not isinstance(response, dict):
                raise Exception(f"Unexpected response type: {type(response)}")
            
            if response.get("retCode") == 0:
                logger.info(f"Order cancelled successfully: {order_id}")
                return {
                    "success": True,
                    "order_id": order_id,
                    "symbol": symbol,
                    "timestamp": datetime.now().isoformat(),
                    "message": "Order cancelled successfully"
                }
            else:
                raise Exception(f"Cancel failed: {response.get('retMsg')}")
                
        except Exception as e:
            logger.error(f"Error cancelling order: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to cancel order: {str(e)}"
            }
    
    async def get_market_overview(
        self,
        market_type: str = "both"
    ) -> Dict[str, Any]:
        """
        ПОЛНЫЙ обзор рынка
        
        Args:
            market_type: "spot", "linear", или "both"
            
        Returns:
            Comprehensive market overview
        """
        logger.info(f"Getting comprehensive market overview for {market_type}")
        
        try:
            overview = {
                "timestamp": datetime.now().isoformat(),
                "market_type": market_type
            }
            
            # Получаем tickers для подсчёта sentiment
            categories = []
            if market_type in ["spot", "both"]:
                categories.append("spot")
            if market_type in ["linear", "both"]:
                categories.append("linear")
            
            all_tickers = []
            
            for cat in categories:
                try:
                    response = self.session.get_tickers(category=cat)
                    # Безопасная проверка ответа
                    if isinstance(response, dict) and response.get("retCode") == 0:
                        tickers = response.get("result", {}).get("list", [])
                        all_tickers.extend(tickers)
                except Exception as e:
                    logger.warning(f"Failed to get {cat} tickers: {e}")
            
            # Анализ sentiment
            gainers = [t for t in all_tickers if float(t.get("price24hPcnt", 0)) > 0]
            losers = [t for t in all_tickers if float(t.get("price24hPcnt", 0)) < 0]
            
            if len(gainers) > len(losers) * 1.5:
                sentiment = "bullish"
            elif len(losers) > len(gainers) * 1.5:
                sentiment = "bearish"
            else:
                sentiment = "neutral"
            
            # Top gainers/losers
            sorted_tickers = sorted(
                [t for t in all_tickers if float(t.get("volume24h", 0)) > 100000],
                key=lambda x: float(x.get("price24hPcnt", 0)),
                reverse=True
            )
            
            top_gainers = sorted_tickers[:20]
            top_losers = sorted_tickers[-20:]
            
            # Top by volume
            by_volume = sorted(
                all_tickers,
                key=lambda x: float(x.get("volume24h", 0)),
                reverse=True
            )[:20]
            
            # Волатильность
            changes = [abs(float(t.get("price24hPcnt", 0))) for t in all_tickers]
            avg_volatility = sum(changes) / len(changes) if changes else 0
            
            if avg_volatility > 5:
                volatility = "high"
            elif avg_volatility > 2:
                volatility = "medium"
            else:
                volatility = "low"
            
            overview.update({
                "sentiment": sentiment,
                "statistics": {
                    "total_pairs": len(all_tickers),
                    "gainers": len(gainers),
                    "losers": len(losers),
                    "avg_volatility": round(avg_volatility, 2),
                    "volatility_level": volatility
                },
                "top_gainers": [
                    {
                        "symbol": t["symbol"],
                        "price": float(t["lastPrice"]),
                        "change_24h": float(t.get("price24hPcnt", 0)) * 100,
                        "volume_24h": float(t.get("volume24h", 0))
                    }
                    for t in top_gainers
                ],
                "top_losers": [
                    {
                        "symbol": t["symbol"],
                        "price": float(t["lastPrice"]),
                        "change_24h": float(t.get("price24hPcnt", 0)) * 100,
                        "volume_24h": float(t.get("volume24h", 0))
                    }
                    for t in top_losers
                ],
                "top_volume": [
                    {
                        "symbol": t["symbol"],
                        "price": float(t["lastPrice"]),
                        "volume_24h": float(t.get("volume24h", 0)),
                        "change_24h": float(t.get("price24hPcnt", 0)) * 100
                    }
                    for t in by_volume
                ],
                "market_conditions": {
                    "trend": sentiment,
                    "volatility": volatility,
                    "phase": self._determine_phase(sentiment, volatility)
                }
            })
            
            return overview
            
        except Exception as e:
            logger.error(f"Error getting market overview: {e}", exc_info=True)
            raise
    
    def _determine_phase(self, sentiment: str, volatility: str) -> str:
        """Определить фазу рынка"""
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
    
    async def move_to_breakeven(
        self,
        symbol: str,
        entry_price: float,
        category: str = "linear"
    ) -> Dict[str, Any]:
        """
        Автоматически перевести SL в breakeven
        
        Args:
            symbol: Торговая пара
            entry_price: Цена входа
            category: Категория
            
        Returns:
            Результат операции
        """
        logger.info(f"Moving {symbol} to breakeven (entry: {entry_price})")
        
        try:
            # Валидация параметров
            if not symbol or not symbol.strip():
                raise ValueError("Symbol is required and cannot be empty")
            if entry_price <= 0:
                raise ValueError(f"Entry price must be positive. Got: {entry_price}")
            if category not in ["spot", "linear", "inverse"]:
                raise ValueError(f"Category must be 'spot', 'linear', or 'inverse'. Got: {category}")
            
            # Добавляем небольшой buffer для fees
            breakeven_price = entry_price * 1.001  # +0.1% для комиссий
            
            return await self.modify_position(
                symbol=symbol,
                stop_loss=breakeven_price,
                category=category
            )
        except Exception as e:
            logger.error(f"Error in move_to_breakeven: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to move to breakeven: {str(e)}"
            }
    
    async def activate_trailing_stop(
        self,
        symbol: str,
        trailing_distance: float,
        category: str = "linear"
    ) -> Dict[str, Any]:
        """
        Активировать trailing stop
        
        Args:
            symbol: Торговая пара
            trailing_distance: Расстояние trailing в %
            category: Категория
            
        Returns:
            Результат активации
        """
        logger.info(f"Activating trailing stop for {symbol}: {trailing_distance}%")
        
        try:
            # Валидация trailing_distance (Bybit обычно поддерживает 0.1% - 10%)
            if trailing_distance < 0.1 or trailing_distance > 10:
                raise Exception(f"Trailing distance must be between 0.1% and 10%. Got: {trailing_distance}%")
            
            # Bybit поддерживает trailing stop только для futures
            if category == "spot":
                raise Exception("Trailing stop is not supported for spot trading. Use futures (linear/inverse).")
            
            # Получаем текущую позицию
            positions = self.session.get_positions(
                category=category,
                symbol=symbol
            )
            
            if positions.get("retCode") != 0:
                error_msg = positions.get('retMsg', 'Unknown error')
                raise Exception(f"Failed to get position: {error_msg}")
            
            position_list = positions.get("result", {}).get("list", [])
            if not position_list or len(position_list) == 0:
                raise Exception(f"No open position found for {symbol}")
            
            position = position_list[0]
            position_size = float(position.get("size", 0))
            
            if position_size == 0:
                raise Exception(f"Position size is 0 for {symbol}")
            
            current_price = float(position.get("markPrice", 0))
            side = position.get("side")
            position_idx = position.get("positionIdx", 0)
            
            # Рассчитываем trailing stop для информации
            if side == "Buy":
                trailing_stop = current_price * (1 - trailing_distance / 100)
            else:
                trailing_stop = current_price * (1 + trailing_distance / 100)
            
            # Устанавливаем trailing stop в Bybit API
            # trailingStop должен быть строкой с процентом
            params = {
                "category": category,
                "symbol": symbol,
                "positionIdx": position_idx,
                "trailingStop": str(trailing_distance)  # В процентах
            }
            
            response = self.session.set_trading_stop(**params)
            
            if response.get("retCode") == 0:
                logger.info(f"Trailing stop activated successfully for {symbol}")
                return {
                    "success": True,
                    "symbol": symbol,
                    "trailing_distance": trailing_distance,
                    "current_stop": trailing_stop,
                    "current_price": current_price,
                    "side": side,
                    "timestamp": datetime.now().isoformat(),
                    "message": "Trailing stop activated successfully"
                }
            else:
                error_msg = response.get('retMsg', 'Unknown error')
                logger.error(f"Failed to activate trailing stop: {error_msg}")
                raise Exception(f"Failed to activate trailing stop: {error_msg}")
                
        except Exception as e:
            logger.error(f"Error activating trailing stop: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to activate trailing stop: {str(e)}"
            }
