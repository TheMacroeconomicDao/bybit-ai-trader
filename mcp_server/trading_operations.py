"""
Trading Operations Module
Полная реализация торговых операций для Bybit
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from pybit.unified_trading import HTTP
from loguru import logger
import asyncio


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
    
    async def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: Optional[float] = None,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        category: str = "spot"
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
        
        try:
            # Параметры ордера
            # Для spot используем точное форматирование количества
            if category == "spot":
                # Для spot: qty должно быть строкой с правильной точностью
                # Используем форматирование до 8 знаков после запятой
                qty_str = f"{quantity:.8f}".rstrip('0').rstrip('.')
            else:
                # Для futures: стандартное форматирование
                qty_str = str(quantity)
            
            order_params = {
                "category": category,
                "symbol": symbol,
                "side": side,
                "orderType": order_type,
                "qty": qty_str
            }
            
            # Добавляем цену для Limit
            if order_type == "Limit" and price:
                order_params["price"] = str(price)
            
            # Для futures можем добавить SL/TP сразу
            if category in ["linear", "inverse"]:
                if stop_loss:
                    order_params["stopLoss"] = str(stop_loss)
                if take_profit:
                    order_params["takeProfit"] = str(take_profit)
            
            # Размещаем ордер
            logger.debug(f"Order params: {order_params}")
            response = self.session.place_order(**order_params)
            logger.debug(f"API response: {response}")
            
            # Проверяем формат ответа
            if not isinstance(response, dict):
                raise Exception(f"Unexpected response type: {type(response)}")
            
            # Проверяем наличие retCode
            if "retCode" not in response:
                # Возможно, это другой формат ответа
                logger.error(f"Response missing retCode: {response}")
                raise Exception(f"Invalid API response format: {response}")
            
            ret_code = response.get("retCode")
            
            if ret_code == 0:
                order_data = response.get("result", {})
                if not order_data:
                    raise Exception(f"Response missing result: {response}")
                    
                logger.info(f"Order placed successfully: {order_data.get('orderId')}")
                
                # Для spot: размещаем отдельные SL/TP ордера если нужно
                if category == "spot" and (stop_loss or take_profit):
                    await self._place_spot_sl_tp(
                        symbol, side, quantity, 
                        order_data.get('orderId'),
                        stop_loss, take_profit
                    )
                
                return {
                    "success": True,
                    "order_id": order_data.get("orderId"),
                    "symbol": symbol,
                    "side": side,
                    "type": order_type,
                    "quantity": quantity,
                    "price": price or order_data.get("price"),
                    "stop_loss": stop_loss,
                    "take_profit": take_profit,
                    "status": order_data.get("orderStatus"),
                    "timestamp": datetime.now().isoformat(),
                    "message": "Order placed successfully"
                }
            else:
                ret_msg = response.get('retMsg', 'Unknown error')
                ret_ext_info = response.get('retExtInfo', {})
                logger.error(f"Order failed: retCode={ret_code}, retMsg={ret_msg}, retExtInfo={ret_ext_info}")
                raise Exception(f"Order failed (retCode={ret_code}): {ret_msg}")
                
        except Exception as e:
            logger.error(f"Error placing order: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to place order: {str(e)}"
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
                if sl_response["retCode"] == 0:
                    logger.info(f"Stop-Loss placed: {sl_response['result'].get('orderId')}")
            
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
                if tp_response["retCode"] == 0:
                    logger.info(f"Take-Profit placed: {tp_response['result'].get('orderId')}")
                    
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
        logger.info(f"Closing position: {symbol}. Reason: {reason}")
        
        try:
            # Получаем текущую позицию
            positions = self.session.get_positions(
                category=category,
                symbol=symbol
            )
            
            if positions["retCode"] != 0:
                raise Exception(f"Failed to get positions: {positions.get('retMsg')}")
            
            position_list = positions["result"]["list"]
            
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
            
            if response["retCode"] == 0:
                logger.info(f"Position closed successfully: {symbol}")
                
                return {
                    "success": True,
                    "symbol": symbol,
                    "closed_at": datetime.now().isoformat(),
                    "reason": reason,
                    "size": position_size,
                    "pnl": position.get("unrealisedPnl"),
                    "pnl_pct": position.get("unrealisedPnlPct"),
                    "order_id": response["result"].get("orderId"),
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
            params = {
                "category": category,
                "symbol": symbol
            }
            
            if stop_loss:
                params["stopLoss"] = str(stop_loss)
            if take_profit:
                params["takeProfit"] = str(take_profit)
            
            response = self.session.set_trading_stop(**params)
            
            if response["retCode"] == 0:
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
                raise Exception(f"Modify failed: {response.get('retMsg')}")
                
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
            response = self.session.cancel_order(
                category=category,
                symbol=symbol,
                orderId=order_id
            )
            
            if response["retCode"] == 0:
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
                    if response["retCode"] == 0:
                        tickers = response["result"]["list"]
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
        
        # Добавляем небольшой buffer для fees
        breakeven_price = entry_price * 1.001  # +0.1% для комиссий
        
        return await self.modify_position(
            symbol=symbol,
            stop_loss=breakeven_price,
            category=category
        )
    
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
            # Bybit поддерживает trailing stop для futures
            # Получаем текущую позицию
            positions = self.session.get_positions(
                category=category,
                symbol=symbol
            )
            
            if positions["retCode"] != 0:
                raise Exception("Failed to get position")
            
            position = positions["result"]["list"][0]
            current_price = float(position["markPrice"])
            side = position["side"]
            
            # Рассчитываем trailing stop
            if side == "Buy":
                trailing_stop = current_price * (1 - trailing_distance / 100)
            else:
                trailing_stop = current_price * (1 + trailing_distance / 100)
            
            # Устанавливаем trailing
            params = {
                "category": category,
                "symbol": symbol,
                "trailingStop": str(trailing_distance)
            }
            
            response = self.session.set_trading_stop(**params)
            
            if response["retCode"] == 0:
                return {
                    "success": True,
                    "symbol": symbol,
                    "trailing_distance": trailing_distance,
                    "current_stop": trailing_stop,
                    "timestamp": datetime.now().isoformat(),
                    "message": "Trailing stop activated"
                }
            else:
                raise Exception(f"Failed: {response.get('retMsg')}")
                
        except Exception as e:
            logger.error(f"Error activating trailing stop: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
