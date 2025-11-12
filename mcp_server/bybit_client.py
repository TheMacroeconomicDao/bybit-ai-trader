"""
Bybit API Client
Обёртка для взаимодействия с Bybit API (REST + WebSocket)
"""

import asyncio
import hashlib
import hmac
import time
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

import ccxt.async_support as ccxt
from loguru import logger


class BybitClient:
    """Клиент для работы с Bybit API"""
    
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
        
        # Инициализация CCXT exchange
        self.exchange = ccxt.bybit({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'spot',  # По умолчанию spot
                'testnet': testnet
            }
        })
        
        logger.info(f"Bybit client initialized ({'testnet' if testnet else 'mainnet'})")
    
    async def get_market_overview(self, market_type: str = "both") -> Dict[str, Any]:
        """
        Получить обзор всего рынка
        
        Args:
            market_type: "spot", "futures", или "both"
            
        Returns:
            Детальный обзор рынка включая sentiment, топ движения, условия
        """
        logger.info(f"Getting market overview for {market_type}")
        
        try:
            # Получаем все тикеры
            spot_tickers = []
            futures_tickers = []
            
            if market_type in ["spot", "both"]:
                self.exchange.options['defaultType'] = 'spot'
                spot_tickers = await self.exchange.fetch_tickers()
            
            if market_type in ["futures", "both"]:
                self.exchange.options['defaultType'] = 'swap'
                futures_tickers = await self.exchange.fetch_tickers()
            
            # Получаем BTC данные (лидер рынка)
            btc_ticker = await self.exchange.fetch_ticker('BTC/USDT')
            btc_price = btc_ticker['last']
            btc_change_24h = btc_ticker['percentage']
            
            # Вычисляем market sentiment
            all_tickers = list(spot_tickers.values()) + list(futures_tickers.values())
            positive_changes = sum(1 for t in all_tickers if t['percentage'] > 0)
            negative_changes = sum(1 for t in all_tickers if t['percentage'] < 0)
            
            if positive_changes > negative_changes * 1.5:
                sentiment = "bullish"
            elif negative_changes > positive_changes * 1.5:
                sentiment = "bearish"
            else:
                sentiment = "neutral"
            
            # Топ gainers и losers
            sorted_by_change = sorted(
                [t for t in all_tickers if t['quoteVolume'] > 100000],  # Минимум $100k объём
                key=lambda x: x['percentage'],
                reverse=True
            )
            
            top_gainers = sorted_by_change[:20]
            top_losers = sorted_by_change[-20:]
            
            # Топ по объёму
            sorted_by_volume = sorted(
                all_tickers,
                key=lambda x: x['quoteVolume'],
                reverse=True
            )
            top_volume = sorted_by_volume[:20]
            
            # Расчёт общей волатильности
            volatilities = [abs(t['percentage']) for t in all_tickers if t['percentage'] is not None]
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
                        "symbol": t['symbol'],
                        "price": t['last'],
                        "change_24h": t['percentage'],
                        "volume_24h": t['quoteVolume']
                    }
                    for t in top_gainers
                ],
                "top_losers": [
                    {
                        "symbol": t['symbol'],
                        "price": t['last'],
                        "change_24h": t['percentage'],
                        "volume_24h": t['quoteVolume']
                    }
                    for t in top_losers
                ],
                "top_volume": [
                    {
                        "symbol": t['symbol'],
                        "price": t['last'],
                        "volume_24h": t['quoteVolume'],
                        "change_24h": t['percentage']
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
            logger.error(f"Error getting market overview: {e}", exc_info=True)
            raise
    
    async def get_all_tickers(self, market_type: str = "spot", sort_by: str = "volume") -> List[Dict[str, Any]]:
        """
        Получить все торговые пары
        
        Args:
            market_type: "spot" или "futures"
            sort_by: "volume", "change", или "name"
            
        Returns:
            Массив всех торговых пар с базовой информацией
        """
        logger.info(f"Getting all {market_type} tickers, sorted by {sort_by}")
        
        try:
            self.exchange.options['defaultType'] = 'swap' if market_type == 'futures' else 'spot'
            tickers = await self.exchange.fetch_tickers()
            
            # Преобразуем в список
            ticker_list = [
                {
                    "symbol": symbol,
                    "price": ticker['last'],
                    "change_24h": ticker['percentage'],
                    "volume_24h": ticker['quoteVolume'],
                    "high_24h": ticker['high'],
                    "low_24h": ticker['low'],
                    "bid": ticker['bid'],
                    "ask": ticker['ask']
                }
                for symbol, ticker in tickers.items()
            ]
            
            # Сортировка
            if sort_by == "volume":
                ticker_list.sort(key=lambda x: x['volume_24h'], reverse=True)
            elif sort_by == "change":
                ticker_list.sort(key=lambda x: x['change_24h'], reverse=True)
            else:  # name
                ticker_list.sort(key=lambda x: x['symbol'])
            
            return ticker_list
            
        except Exception as e:
            logger.error(f"Error getting all tickers: {e}", exc_info=True)
            raise
    
    async def get_asset_price(self, symbol: str) -> Dict[str, Any]:
        """
        Получить текущую цену актива
        
        Args:
            symbol: Торговая пара (например "BTC/USDT")
            
        Returns:
            Цена, объём, изменение за 24h
        """
        logger.info(f"Getting price for {symbol}")
        
        try:
            ticker = await self.exchange.fetch_ticker(symbol)
            
            return {
                "symbol": symbol,
                "price": ticker['last'],
                "change_24h": ticker['percentage'],
                "volume_24h": ticker['quoteVolume'],
                "high_24h": ticker['high'],
                "low_24h": ticker['low'],
                "bid": ticker['bid'],
                "ask": ticker['ask'],
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting asset price: {e}", exc_info=True)
            raise
    
    async def get_ohlcv(self, symbol: str, timeframe: str = "1h", limit: int = 100) -> List[List]:
        """
        Получить OHLCV данные (свечи)
        
        Args:
            symbol: Торговая пара
            timeframe: Таймфрейм (1m, 5m, 15m, 1h, 4h, 1d)
            limit: Количество свечей
            
        Returns:
            Массив OHLCV данных
        """
        try:
            ohlcv = await self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            return ohlcv
            
        except Exception as e:
            logger.error(f"Error getting OHLCV: {e}", exc_info=True)
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
    
    async def close(self):
        """Закрыть соединение"""
        await self.exchange.close()
        logger.info("Bybit client closed")

