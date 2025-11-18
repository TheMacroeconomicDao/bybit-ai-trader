"""
Position Monitor
Real-time мониторинг позиций через WebSocket
"""

import asyncio
from typing import Dict, Any, Callable, Optional
from datetime import datetime
from pybit.unified_trading import WebSocket
from loguru import logger


class PositionMonitor:
    """Real-time мониторинг позиций"""
    
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        testnet: bool = False
    ):
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        
        # WebSocket connection
        self.ws = None
        self.monitoring = False
        
        # Callbacks
        self.on_price_update: Optional[Callable] = None
        self.on_action_taken: Optional[Callable] = None
        self.on_exit_signal: Optional[Callable] = None
        self.on_warning: Optional[Callable] = None
        
        # Monitored positions
        self.positions: Dict[str, Dict] = {}
        
        logger.info("Position Monitor initialized")
    
    async def start_monitoring(
        self,
        auto_actions: Optional[Dict[str, Any]] = None
    ):
        """
        Начать мониторинг позиций
        
        Args:
            auto_actions: Правила автоматических действий
            {
                "move_to_breakeven_at": 1.0,  # При 1:1 R:R
                "enable_trailing_at": 2.0,     # При 2:1 R:R
                "exit_on_reversal": True,
                "max_time_in_trade": 12        # Часов
            }
        """
        logger.info("Starting position monitoring...")
        
        self.monitoring = True
        self.auto_actions = auto_actions or {}
        
        try:
            # Инициализация WebSocket
            channel = "position"
            
            self.ws = WebSocket(
                testnet=self.testnet,
                channel_type="private",
                api_key=self.api_key,
                api_secret=self.api_secret
            )
            
            # Подписка на position updates
            self.ws.position_stream(
                callback=self._handle_position_update
            )
            
            logger.info("✅ WebSocket monitoring started")
            
            # Monitoring loop
            while self.monitoring:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Error in monitoring: {e}", exc_info=True)
            self.monitoring = False
    
    def _handle_position_update(self, message: Dict):
        """Обработка WebSocket updates позиций"""
        
        try:
            data = message.get("data", [])
            
            for position in data:
                symbol = position.get("symbol")
                
                if not symbol:
                    continue
                
                # Update position data
                self.positions[symbol] = {
                    "symbol": symbol,
                    "side": position.get("side"),
                    "size": float(position.get("size", 0)),
                    "entry_price": float(position.get("avgPrice", 0)),
                    "current_price": float(position.get("markPrice", 0)),
                    "unrealized_pnl": float(position.get("unrealisedPnl", 0)),
                    "unrealized_pnl_pct": float(position.get("unrealisedPnlPct", 0)) * 100,
                    "leverage": position.get("leverage"),
                    "stop_loss": float(position.get("stopLoss", 0)),
                    "take_profit": float(position.get("takeProfit", 0)),
                    "updated_at": datetime.now().isoformat()
                }
                
                # Emit price update event
                if self.on_price_update:
                    asyncio.create_task(self.on_price_update(self.positions[symbol]))
                
                # Check auto-actions
                asyncio.create_task(self._check_auto_actions(symbol))
                
        except Exception as e:
            logger.error(f"Error handling position update: {e}")
    
    async def _check_auto_actions(self, symbol: str):
        """Проверка и выполнение автоматических действий"""
        
        position = self.positions.get(symbol)
        if not position:
            return
        
        entry_price = position["entry_price"]
        current_price = position["current_price"]
        unrealized_pnl_pct = position["unrealized_pnl_pct"]
        
        # Расчёт R:R achieved
        if entry_price > 0:
            profit_pct = ((current_price - entry_price) / entry_price) * 100
            
            # Action 1: Move to breakeven
            breakeven_threshold = self.auto_actions.get("move_to_breakeven_at", 1.0)
            if profit_pct >= breakeven_threshold and position["stop_loss"] < entry_price:
                logger.info(f"{symbol}: Moving to breakeven (profit: {profit_pct:.2f}%)")
                
                if self.on_action_taken:
                    await self.on_action_taken({
                        "action": "move_to_breakeven",
                        "symbol": symbol,
                        "reason": f"Reached {profit_pct:.2f}% profit (threshold: {breakeven_threshold}%)",
                        "new_sl": entry_price
                    })
            
            # Action 2: Enable trailing
            trailing_threshold = self.auto_actions.get("enable_trailing_at", 2.0)
            if profit_pct >= trailing_threshold:
                logger.info(f"{symbol}: Ready for trailing stop (profit: {profit_pct:.2f}%)")
                
                if self.on_action_taken:
                    await self.on_action_taken({
                        "action": "enable_trailing",
                        "symbol": symbol,
                        "reason": f"Reached {profit_pct:.2f}% profit (threshold: {trailing_threshold}%)",
                        "trailing_pct": 2.0  # 2% trailing
                    })
    
    async def stop_monitoring(self):
        """Остановить мониторинг"""
        logger.info("Stopping position monitoring...")
        
        self.monitoring = False
        
        if self.ws:
            # Закрыть WebSocket
            # Note: pybit WebSocket не имеет явного close, закроется при exit
            self.ws = None
        
        logger.info("✅ Monitoring stopped")
    
    def set_callbacks(
        self,
        on_price_update: Optional[Callable] = None,
        on_action_taken: Optional[Callable] = None,
        on_exit_signal: Optional[Callable] = None,
        on_warning: Optional[Callable] = None
    ):
        """Установить callback функции для событий"""
        
        self.on_price_update = on_price_update
        self.on_action_taken = on_action_taken
        self.on_exit_signal = on_exit_signal
        self.on_warning = on_warning
        
        logger.info("Callbacks configured")
