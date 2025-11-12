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
            if leverage and (leverage < 1 or leverage > 125):
                raise ValueError(f"Leverage must be between 1 and 125. Got: {leverage}")
            
            # Параметры ордера
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
            
            # Добавляем цену для Limit
            if order_type == "Limit" and price:
                order_params["price"] = str(price)
            
            # Для futures можем добавить SL/TP сразу
            if category in ["linear", "inverse"]:
                if stop_loss:
                    order_params["stopLoss"] = str(stop_loss)
                if take_profit:
                    order_params["takeProfit"] = str(take_profit)
                
                # Устанавливаем leverage перед открытием позиции
                if leverage:
                    try:
                        leverage_response = self.session.set_leverage(
                            category=category,
                            symbol=symbol,
                            buyLeverage=str(leverage),
                            sellLeverage=str(leverage)
                        )
                        if leverage_response["retCode"] != 0:
                            logger.warning(f"Failed to set leverage: {leverage_response.get('retMsg')}")
                        else:
                            logger.info(f"Leverage set to {leverage}x for {symbol}")
                    except Exception as e:
                        logger.warning(f"Error setting leverage: {e}")
            
            # Размещаем ордер
            response = self.session.place_order(**order_params)
            
            # Логируем полный ответ для отладки
            logger.debug(f"Place order response: {response}")
            
            if response.get("retCode") == 0:
                order_data = response["result"]
                logger.info(f"Order placed successfully: {order_data.get('orderId')}")
                
                # Инвалидируем кэш баланса после размещения ордера
                account_type = get_account_type_for_category(category, prefer_unified=True)
                self.invalidate_balance_cache(account_type=account_type)
                
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
                raise Exception(f"Order failed: {response.get('retMsg', 'Unknown error')}")
                
        except KeyError as e:
            logger.error(f"KeyError in place_order: {e}. Response structure may be different.")
            return {
                "success": False,
                "error": f"KeyError: {str(e)}",
                "message": f"Failed to place order: KeyError accessing {str(e)}. Check API response format."
            }
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
