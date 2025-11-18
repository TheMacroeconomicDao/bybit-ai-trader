"""
Telegram Signal Updater
Система обновления Telegram постов с индикаторами состояния сигналов в реальном времени
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from loguru import logger

try:
    from .telegram_bot import TelegramBot
    from .signal_tracker import SignalTracker
except ImportError:
    from telegram_bot import TelegramBot
    from signal_tracker import SignalTracker


class TelegramSignalUpdater:
    """Обновление Telegram постов с индикаторами состояния сигналов"""
    
    def __init__(
        self,
        signal_tracker: SignalTracker,
        telegram_bot: TelegramBot,
        bot_token: str
    ):
        """
        Инициализация updater
        
        Args:
            signal_tracker: Экземпляр SignalTracker
            telegram_bot: Экземпляр TelegramBot
            bot_token: Telegram Bot Token
        """
        self.tracker = signal_tracker
        self.bot = telegram_bot
        self.bot_token = bot_token
        
        logger.info("Telegram Signal Updater initialized")
    
    def generate_status_indicator(
        self,
        signal: Dict[str, Any],
        current_price: Optional[float] = None
    ) -> str:
        """
        Генерация индикатора состояния сигнала для Telegram поста
        
        Args:
            signal: Данные сигнала
            current_price: Текущая цена (опционально)
            
        Returns:
            HTML строка с индикатором состояния
        """
        status = signal.get("status", "active")
        side = signal.get("side", "").upper()
        symbol = signal.get("symbol", "")
        entry_price = signal.get("entry_price", 0)
        stop_loss = signal.get("stop_loss", 0)
        take_profit = signal.get("take_profit", 0)
        
        # Получаем последний snapshot если цена не указана
        if current_price is None:
            snapshots = self.tracker.conn.cursor().execute("""
                SELECT price FROM price_snapshots
                WHERE signal_id = ?
                ORDER BY timestamp DESC
                LIMIT 1
            """, (signal.get("signal_id"),)).fetchone()
            
            if snapshots:
                current_price = snapshots["price"]
            else:
                current_price = entry_price
        
        # Расчет прогресса
        if side == "LONG":
            if current_price >= take_profit:
                progress_pct = 100
                status_emoji = "✅"
                status_text = "TP HIT"
                status_color = "🟢"
            elif current_price <= stop_loss:
                progress_pct = 0
                status_emoji = "❌"
                status_text = "SL HIT"
                status_color = "🔴"
            else:
                # Прогресс от Entry к TP
                total_range = take_profit - entry_price
                current_progress = current_price - entry_price
                progress_pct = min(100, max(0, (current_progress / total_range) * 100))
                
                # Определяем статус по прогрессу
                if progress_pct >= 75:
                    status_emoji = "🟢"
                    status_text = "NEAR TP"
                    status_color = "🟢"
                elif progress_pct >= 50:
                    status_emoji = "🟡"
                    status_text = "IN PROGRESS"
                    status_color = "🟡"
                elif progress_pct >= 25:
                    status_emoji = "🟠"
                    status_text = "EARLY STAGE"
                    status_color = "🟠"
                else:
                    status_emoji = "🔴"
                    status_text = "NEAR SL"
                    status_color = "🔴"
        else:  # SHORT
            if current_price <= take_profit:
                progress_pct = 100
                status_emoji = "✅"
                status_text = "TP HIT"
                status_color = "🟢"
            elif current_price >= stop_loss:
                progress_pct = 0
                status_emoji = "❌"
                status_text = "SL HIT"
                status_color = "🔴"
            else:
                # Прогресс от Entry к TP (для SHORT)
                total_range = entry_price - take_profit
                current_progress = entry_price - current_price
                progress_pct = min(100, max(0, (current_progress / total_range) * 100))
                
                # Определяем статус по прогрессу
                if progress_pct >= 75:
                    status_emoji = "🟢"
                    status_text = "NEAR TP"
                    status_color = "🟢"
                elif progress_pct >= 50:
                    status_emoji = "🟡"
                    status_text = "IN PROGRESS"
                    status_color = "🟡"
                elif progress_pct >= 25:
                    status_emoji = "🟠"
                    status_text = "EARLY STAGE"
                    status_color = "🟠"
                else:
                    status_emoji = "🔴"
                    status_text = "NEAR SL"
                    status_color = "🔴"
        
        # Расчет P/L
        if side == "LONG":
            pnl_pct = ((current_price - entry_price) / entry_price) * 100 if entry_price > 0 else 0
        else:
            pnl_pct = ((entry_price - current_price) / entry_price) * 100 if entry_price > 0 else 0
        
        pnl_emoji = "📈" if pnl_pct >= 0 else "📉"
        pnl_color = "🟢" if pnl_pct >= 0 else "🔴"
        
        # Время в сделке
        created_at = datetime.fromisoformat(signal.get("created_at", datetime.now().isoformat()))
        time_in_trade = datetime.now() - created_at
        hours = int(time_in_trade.total_seconds() / 3600)
        minutes = int((time_in_trade.total_seconds() % 3600) / 60)
        time_str = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
        
        # Генерация прогресс-бара
        progress_bar_length = 20
        filled = int(progress_pct / 100 * progress_bar_length)
        progress_bar = "█" * filled + "░" * (progress_bar_length - filled)
        
        # Формируем индикатор
        indicator = f"""
<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>

<b>📊 СТАТУС СИГНАЛА: {symbol}</b>

{status_color} <b>{status_text}</b> {status_emoji}

<b>Прогресс к TP:</b>
<code>{progress_bar}</code> <b>{progress_pct:.1f}%</b>

<b>Текущая цена:</b> ${current_price:,.2f}
<b>Entry:</b> ${entry_price:,.2f}
<b>Stop-Loss:</b> ${stop_loss:,.2f}
<b>Take-Profit:</b> ${take_profit:,.2f}

<b>P/L:</b> {pnl_color} {pnl_emoji} <b>{pnl_pct:+.2f}%</b>

<b>⏱️ Время в сделке:</b> {time_str}

<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>
"""
        
        return indicator.strip()
    
    def generate_updated_message(
        self,
        original_message: str,
        signal: Dict[str, Any],
        current_price: Optional[float] = None
    ) -> str:
        """
        Генерация обновленного сообщения с индикатором состояния
        
        Args:
            original_message: Оригинальное сообщение
            signal: Данные сигнала
            current_price: Текущая цена
            
        Returns:
            Обновленное сообщение с индикатором
        """
        # Находим место для вставки индикатора (после заголовка сигнала)
        symbol = signal.get("symbol", "")
        
        # Ищем секцию сигнала в сообщении
        signal_section_start = original_message.find(f"📊 СДЕЛКА")
        if signal_section_start == -1:
            signal_section_start = original_message.find(f"📊 TRADE")
        
        if signal_section_start == -1:
            # Если не нашли секцию, добавляем в конец
            indicator = self.generate_status_indicator(signal, current_price)
            return f"{original_message}\n\n{indicator}"
        
        # Находим конец секции сигнала (следующий разделитель или конец)
        next_separator = original_message.find("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", signal_section_start + 1)
        if next_separator == -1:
            next_separator = len(original_message)
        
        # Вставляем индикатор перед следующим разделителем
        indicator = self.generate_status_indicator(signal, current_price)
        
        updated_message = (
            original_message[:next_separator] +
            "\n" + indicator + "\n" +
            original_message[next_separator:]
        )
        
        return updated_message
    
    async def update_signal_post(
        self,
        signal_id: str,
        current_price: Optional[float] = None,
        original_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Обновить Telegram пост для сигнала
        
        Args:
            signal_id: ID сигнала
            current_price: Текущая цена
            original_message: Оригинальное сообщение (если не указано, будет использовано из БД)
            
        Returns:
            Результат обновления
        """
        try:
            # Получаем данные сигнала
            signal = await self.tracker.get_signal(signal_id)
            if not signal:
                return {"error": "Signal not found"}
            
            # Получаем message_ids
            message_ids = await self.tracker.get_telegram_message_ids(signal_id)
            if not message_ids:
                logger.warning(f"No Telegram message IDs found for signal {signal_id}")
                return {"error": "No Telegram messages found"}
            
            # Получаем текущую цену если не указана
            if current_price is None:
                snapshots = await self.tracker.get_price_snapshots(signal_id, limit=1)
                if snapshots:
                    current_price = snapshots[0]["price"]
                else:
                    current_price = signal.get("entry_price", 0)
            
            # Генерируем индикатор
            indicator = self.generate_status_indicator(signal, current_price)
            
            # Если оригинальное сообщение не указано, используем только индикатор
            if original_message:
                updated_message = self.generate_updated_message(original_message, signal, current_price)
            else:
                updated_message = indicator
            
            # Обновляем сообщения во всех каналах
            results = {}
            for chat_id, message_id in message_ids.items():
                try:
                    await self.bot.edit_message(
                        chat_id=str(chat_id),
                        message_id=int(message_id),
                        text=updated_message,
                        parse_mode="HTML"
                    )
                    results[chat_id] = {"success": True, "message_id": message_id}
                    logger.info(f"✅ Updated Telegram post for signal {signal_id} in chat {chat_id}")
                except Exception as e:
                    results[chat_id] = {"success": False, "error": str(e)}
                    logger.error(f"❌ Failed to update Telegram post in chat {chat_id}: {e}")
            
            return {
                "signal_id": signal_id,
                "updated": True,
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Error updating Telegram post for signal {signal_id}: {e}", exc_info=True)
            return {"error": str(e)}
    
    async def update_all_active_signals(self) -> Dict[str, Any]:
        """
        Обновить все активные сигналы
        
        Returns:
            Статистика обновления
        """
        active_signals = await self.tracker.get_active_signals()
        
        if not active_signals:
            return {
                "updated": 0,
                "failed": 0,
                "total": 0
            }
        
        updated = 0
        failed = 0
        
        for signal in active_signals:
            result = await self.update_signal_post(signal["signal_id"])
            if result.get("updated"):
                updated += 1
            else:
                failed += 1
        
        return {
            "updated": updated,
            "failed": failed,
            "total": len(active_signals)
        }


