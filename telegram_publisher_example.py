"""
Пример класса для интеграции с ботом автоматизации анализа
Готовый к использованию код для публикации торговых сигналов
"""
import asyncio
from typing import List, Dict, Optional
from mcp_server.telegram_bot import TelegramBot


class TelegramSignalPublisher:
    """
    Класс для публикации торговых сигналов в Telegram каналы
    
    Использование:
        async with TelegramSignalPublisher() as publisher:
            await publisher.publish_signal(
                symbol="ZEN/USDT",
                entry=15.89,
                stop_loss=13.58,
                take_profit=20.52,
                risk_reward="1:2.0"
            )
    """
    
    def __init__(
        self,
        bot_token: str = "8003689195:AAGxQsopKvlLS34H2TZ0S1a0K7s4yV4iOBY",
        default_channels: Optional[List[str]] = None
    ):
        """
        Инициализация публикатора
        
        Args:
            bot_token: Токен Telegram бота
            default_channels: Список chat_id каналов по умолчанию
        """
        self.bot_token = bot_token
        self.default_channels = default_channels or [
            "-1003382613825",  # DIAMOND HEADZH
            "-1003484839912",  # Hypov Hedge Fund (AI Signals)
        ]
        self.bot: Optional[TelegramBot] = None
    
    async def __aenter__(self):
        """Вход в контекстный менеджер"""
        self.bot = TelegramBot(self.bot_token)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Выход из контекстного менеджера"""
        if self.bot:
            await self.bot.close()
    
    def format_signal_message(
        self,
        symbol: str,
        entry: float,
        stop_loss: float,
        take_profit: float,
        risk_reward: str,
        additional_info: Optional[Dict] = None,
        language: str = "en"
    ) -> str:
        """
        Форматирует данные сигнала в HTML сообщение
        
        Args:
            symbol: Торговая пара (например, "ZEN/USDT")
            entry: Цена входа
            stop_loss: Стоп-лосс
            take_profit: Тейк-профит
            risk_reward: Соотношение риск/награда
            additional_info: Дополнительная информация (confidence, time_window, etc.)
            language: Язык сообщения ("en" или "ru")
        
        Returns:
            str: Отформатированное HTML сообщение
        """
        if language == "ru":
            header = "⚡ ТОРГОВЫЙ СИГНАЛ"
            trade_label = "СДЕЛКА"
            entry_label = "Entry"
            sl_label = "Stop-Loss"
            tp_label = "Take-Profit"
            rr_label = "Risk/Reward"
        else:
            header = "⚡ TRADING SIGNAL"
            trade_label = "TRADE"
            entry_label = "Entry"
            sl_label = "Stop-Loss"
            tp_label = "Take-Profit"
            rr_label = "Risk/Reward"
        
        message = f"""<b>{header}</b>

<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>

<b>📊 {trade_label}: {symbol}</b>

<b>{entry_label}:</b> ${entry}
<b>{sl_label}:</b> ${stop_loss}
<b>{tp_label}:</b> ${take_profit}

<b>{rr_label}:</b> {risk_reward}"""
        
        # Добавляем дополнительную информацию если есть
        if additional_info:
            if additional_info.get("confidence"):
                conf_label = "CONFIDENCE" if language == "en" else "УВЕРЕННОСТЬ"
                message += f"\n\n<b>🎯 {conf_label}:</b> {additional_info['confidence']}/10"
            
            if additional_info.get("time_window"):
                tw_label = "Safe Time Window" if language == "en" else "Безопасное окно"
                message += f"\n<b>⏰ {tw_label}:</b> {additional_info['time_window']}"
            
            if additional_info.get("notes"):
                message += f"\n\n<b>📝 Notes:</b>\n{additional_info['notes']}"
        
        message += "\n\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"
        
        return message
    
    async def publish_signal(
        self,
        symbol: str,
        entry: float,
        stop_loss: float,
        take_profit: float,
        risk_reward: str,
        additional_info: Optional[Dict] = None,
        channels: Optional[List[str]] = None,
        language: str = "en"
    ) -> Dict:
        """
        Публикует торговый сигнал в указанные каналы
        
        Args:
            symbol: Торговая пара
            entry: Цена входа
            stop_loss: Стоп-лосс
            take_profit: Тейк-профит
            risk_reward: Соотношение риск/награда
            additional_info: Дополнительная информация
            channels: Список chat_id каналов (если None, используются default_channels)
            language: Язык сообщения ("en" или "ru")
        
        Returns:
            dict: Результаты отправки
                {
                    "success": bool,
                    "sent_to": List[str],
                    "failed": List[Dict],
                    "total": int
                }
        """
        if channels is None:
            channels = self.default_channels
        
        message = self.format_signal_message(
            symbol, entry, stop_loss, take_profit, risk_reward,
            additional_info, language
        )
        
        results = {
            "success": True,
            "sent_to": [],
            "failed": [],
            "total": len(channels)
        }
        
        for chat_id in channels:
            try:
                await self.bot.send_message(chat_id, message, parse_mode="HTML")
                results["sent_to"].append(chat_id)
            except Exception as e:
                results["success"] = False
                results["failed"].append({
                    "chat_id": chat_id,
                    "error": str(e)
                })
        
        return results
    
    async def publish_multiple_signals(
        self,
        signals: List[Dict],
        language: str = "en",
        channels: Optional[List[str]] = None
    ) -> Dict:
        """
        Публикует несколько сигналов в один пост
        
        Args:
            signals: Список словарей с данными сигналов
            language: Язык сообщения
            channels: Список каналов
        
        Returns:
            dict: Результаты отправки
        """
        if channels is None:
            channels = self.default_channels
        
        # Формируем сообщение со всеми сигналами
        if language == "ru":
            header = "⚡ ДЕТАЛЬНЫЙ ПЛАН СДЕЛОК"
        else:
            header = "⚡ DETAILED TRADING PLAN"
        
        message = f"<b>{header}</b>\n\n"
        message += "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n\n"
        
        for idx, signal in enumerate(signals, 1):
            signal_msg = self.format_signal_message(
                signal["symbol"],
                signal["entry"],
                signal["stop_loss"],
                signal["take_profit"],
                signal["risk_reward"],
                signal.get("additional_info"),
                language
            )
            # Убираем заголовок и разделители из каждого сигнала
            signal_lines = signal_msg.split("\n")
            signal_lines = [line for line in signal_lines if not line.startswith("<b>⚡")]
            signal_msg = "\n".join(signal_lines)
            message += signal_msg.replace("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", "")
            if idx < len(signals):
                message += "\n\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n\n"
        
        results = {
            "success": True,
            "sent_to": [],
            "failed": [],
            "total": len(channels)
        }
        
        for chat_id in channels:
            try:
                await self.bot.send_message(chat_id, message, parse_mode="HTML")
                results["sent_to"].append(chat_id)
            except Exception as e:
                results["success"] = False
                results["failed"].append({
                    "chat_id": chat_id,
                    "error": str(e)
                })
        
        return results


# Пример использования
async def example_single_signal():
    """Пример отправки одного сигнала"""
    async with TelegramSignalPublisher() as publisher:
        result = await publisher.publish_signal(
            symbol="ZEN/USDT",
            entry=15.89,
            stop_loss=13.58,
            take_profit=20.52,
            risk_reward="1:2.0",
            additional_info={
                "confidence": 8.0,
                "time_window": "12-18 hours",
                "notes": "Outperforming BTC by 15%"
            },
            language="en"
        )
        print(f"Результат: {result}")


async def example_multiple_signals():
    """Пример отправки нескольких сигналов"""
    signals = [
        {
            "symbol": "ZEN/USDT",
            "entry": 15.89,
            "stop_loss": 13.58,
            "take_profit": 20.52,
            "risk_reward": "1:2.0",
            "additional_info": {"confidence": 8.0}
        },
        {
            "symbol": "XPL/USDT",
            "entry": 0.240,
            "stop_loss": 0.210,
            "take_profit": 0.300,
            "risk_reward": "1:2.0",
            "additional_info": {"confidence": 7.5}
        },
        {
            "symbol": "MINA/USDT",
            "entry": 0.143,
            "stop_loss": 0.120,
            "take_profit": 0.190,
            "risk_reward": "1:2.04",
            "additional_info": {"confidence": 7.0}
        }
    ]
    
    async with TelegramSignalPublisher() as publisher:
        result = await publisher.publish_multiple_signals(
            signals=signals,
            language="en"
        )
        print(f"Результат: {result}")


if __name__ == "__main__":
    # Запуск примеров
    print("Пример 1: Один сигнал")
    asyncio.run(example_single_signal())
    
    print("\nПример 2: Несколько сигналов")
    asyncio.run(example_multiple_signals())

