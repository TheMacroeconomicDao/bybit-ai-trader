"""
Signal Price Monitor
Автоматический мониторинг цены для отслеживания результатов сигналов
"""

import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from loguru import logger

from mcp_server.signal_tracker import SignalTracker
from mcp_server.bybit_client import BybitClient


class SignalPriceMonitor:
    """Мониторинг цены для сигналов"""
    
    # Максимальное время отслеживания по таймфреймам (в часах)
    TIMEFRAME_TIMEOUTS = {
        "5m": 1,      # 1 час для 5m
        "15m": 3,     # 3 часа для 15m
        "1h": 6,      # 6 часов для 1h
        "4h": 24,     # 24 часа для 4h
        "1d": 72,     # 3 дня для 1d
        "default": 12  # По умолчанию 12 часов
    }
    
    def __init__(
        self,
        signal_tracker: SignalTracker,
        bybit_client: BybitClient,
        check_interval: int = 300  # 5 минут по умолчанию
    ):
        """
        Инициализация монитора цены
        
        Args:
            signal_tracker: Экземпляр SignalTracker
            bybit_client: Экземпляр BybitClient для получения цены
            check_interval: Интервал проверки в секундах (по умолчанию 5 минут)
        """
        self.tracker = signal_tracker
        self.client = bybit_client
        self.check_interval = check_interval
        self.monitoring = False
        self.monitor_task: Optional[asyncio.Task] = None
        
        logger.info(f"Signal Price Monitor initialized (check_interval: {check_interval}s)")
    
    async def start_monitoring(self, check_interval: Optional[int] = None):
        """
        Начать мониторинг активных сигналов
        
        Args:
            check_interval: Интервал проверки (если не указан, используется self.check_interval)
        """
        if self.monitoring:
            logger.warning("Monitoring already started")
            return
        
        if check_interval:
            self.check_interval = check_interval
        
        self.monitoring = True
        self.monitor_task = asyncio.create_task(self._monitoring_loop())
        
        logger.info(f"Signal Price Monitor started (interval: {self.check_interval}s)")
    
    async def stop_monitoring(self):
        """Остановить мониторинг"""
        if not self.monitoring:
            return
        
        self.monitoring = False
        
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Signal Price Monitor stopped")
    
    async def _monitoring_loop(self):
        """Основной цикл мониторинга"""
        while self.monitoring:
            try:
                # Получаем активные сигналы
                active_signals = await self.tracker.get_active_signals()
                
                if not active_signals:
                    await asyncio.sleep(self.check_interval)
                    continue
                
                logger.debug(f"Checking {len(active_signals)} active signals")
                
                # Проверяем каждый сигнал
                tasks = [self.check_signal(signal["signal_id"]) for signal in active_signals]
                await asyncio.gather(*tasks, return_exceptions=True)
                
                # Ждем перед следующей проверкой
                await asyncio.sleep(self.check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}", exc_info=True)
                await asyncio.sleep(self.check_interval)
    
    async def check_signal(self, signal_id: str) -> Dict[str, Any]:
        """
        Проверить один сигнал
        
        Args:
            signal_id: ID сигнала
            
        Returns:
            Результат проверки
        """
        try:
            # Получаем данные сигнала
            signal = await self.tracker.get_signal(signal_id)
            if not signal:
                return {"error": "Signal not found"}
            
            if signal["status"] != "active":
                return {"status": "not_active", "signal_status": signal["status"]}
            
            # Получаем текущую цену
            symbol = signal["symbol"]
            try:
                price_data = await self.client.get_asset_price(symbol)
                current_price = float(price_data.get("price", 0))
            except Exception as e:
                logger.warning(f"Failed to get price for {symbol}: {e}")
                return {"error": f"Price fetch failed: {e}"}
            
            if current_price == 0:
                return {"error": "Invalid price"}
            
            # Записываем snapshot
            await self.tracker.record_price_snapshot(signal_id, current_price)
            
            # Определяем результат
            result = await self.determine_result(signal, current_price)
            
            if result:
                # Рассчитываем метрики
                created_at = datetime.fromisoformat(signal["created_at"])
                time_to_result = int((datetime.now() - created_at).total_seconds())
                
                # Получаем последние snapshots для расчета max excursions
                snapshots = await self.tracker.get_price_snapshots(signal_id, limit=1000)
                
                max_fav = signal.get("max_favorable_excursion") or 0
                max_adv = signal.get("max_adverse_excursion") or 0
                
                # Рассчитываем actual_rr
                actual_rr = None
                if result == "tp_hit":
                    # Цена достигла TP
                    if signal["side"].lower() == "long":
                        actual_rr = abs(signal["take_profit"] - signal["entry_price"]) / abs(signal["entry_price"] - signal["stop_loss"])
                    else:
                        actual_rr = abs(signal["entry_price"] - signal["take_profit"]) / abs(signal["stop_loss"] - signal["entry_price"])
                elif result == "sl_hit":
                    # Цена достигла SL
                    actual_rr = -1.0  # Убыток
                
                # Обновляем результат сигнала
                await self.tracker.update_signal_result(
                    signal_id=signal_id,
                    result=result,
                    actual_rr=actual_rr,
                    max_favorable_excursion=max_fav if max_fav != 0 else None,
                    max_adverse_excursion=max_adv if max_adv != 0 else None,
                    time_to_result=time_to_result
                )
                
                logger.info(f"Signal {signal_id} ({symbol}) completed: {result} | Price: {current_price} | Time: {time_to_result}s")
                
                return {
                    "signal_id": signal_id,
                    "result": result,
                    "current_price": current_price,
                    "time_to_result": time_to_result,
                    "actual_rr": actual_rr
                }
            
            return {
                "signal_id": signal_id,
                "status": "active",
                "current_price": current_price
            }
            
        except Exception as e:
            logger.error(f"Error checking signal {signal_id}: {e}", exc_info=True)
            return {"error": str(e)}
    
    async def determine_result(
        self,
        signal: Dict[str, Any],
        current_price: float
    ) -> Optional[str]:
        """
        Определить результат сигнала на основе текущей цены
        
        Args:
            signal: Данные сигнала
            current_price: Текущая цена
            
        Returns:
            Результат ('tp_hit', 'sl_hit', 'timeout') или None если сигнал еще активен
        """
        side = signal["side"].lower()
        entry_price = signal["entry_price"]
        stop_loss = signal["stop_loss"]
        take_profit = signal["take_profit"]
        
        # Проверка TP hit
        if side == "long":
            tp_hit = current_price >= take_profit
            sl_hit = current_price <= stop_loss
        else:  # short
            tp_hit = current_price <= take_profit
            sl_hit = current_price >= stop_loss
        
        if tp_hit:
            return "tp_hit"
        
        if sl_hit:
            return "sl_hit"
        
        # Проверка timeout
        created_at = datetime.fromisoformat(signal["created_at"])
        elapsed_hours = (datetime.now() - created_at).total_seconds() / 3600
        
        # Определяем максимальное время на основе timeframe
        timeframe = signal.get("timeframe") or "default"
        max_hours = self.TIMEFRAME_TIMEOUTS.get(timeframe) or self.TIMEFRAME_TIMEOUTS["default"]
        
        if elapsed_hours >= max_hours:
            # Определяем результат на основе текущей цены
            if side == "long":
                if current_price > entry_price:
                    return "timeout_profit"  # В прибыли но не достиг TP
                else:
                    return "timeout_loss"  # В убытке но не достиг SL
            else:  # short
                if current_price < entry_price:
                    return "timeout_profit"
                else:
                    return "timeout_loss"
        
        # Сигнал еще активен
        return None
    
    async def check_all_active(self) -> Dict[str, Any]:
        """
        Проверить все активные сигналы (ручной вызов)
        
        Returns:
            Статистика проверки
        """
        active_signals = await self.tracker.get_active_signals()
        
        if not active_signals:
            return {
                "checked": 0,
                "completed": 0,
                "still_active": 0
            }
        
        completed = 0
        still_active = 0
        
        for signal in active_signals:
            result = await self.check_signal(signal["signal_id"])
            if result.get("result"):
                completed += 1
            else:
                still_active += 1
        
        return {
            "checked": len(active_signals),
            "completed": completed,
            "still_active": still_active
        }

