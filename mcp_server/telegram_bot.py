"""
Telegram Bot модуль для отправки торговых сигналов в группу
"""
import asyncio
import aiohttp
from typing import Optional
from loguru import logger


class TelegramBot:
    """Класс для работы с Telegram Bot API"""
    
    def __init__(self, token: str):
        """
        Инициализация бота
        
        Args:
            token: Telegram Bot Token
        """
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Получить или создать aiohttp сессию"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close(self):
        """Закрыть сессию"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def send_message(
        self,
        chat_id: str,
        text: str,
        parse_mode: Optional[str] = "HTML",
        disable_web_page_preview: bool = True
    ) -> dict:
        """
        Отправить сообщение в чат/группу
        
        Args:
            chat_id: ID чата или группы (может быть числом или строкой)
            text: Текст сообщения
            parse_mode: Режим парсинга (Markdown, HTML, None)
            disable_web_page_preview: Отключить превью ссылок
        
        Returns:
            dict: Ответ от Telegram API
        """
        session = await self._get_session()
        
        url = f"{self.base_url}/sendMessage"
        
        payload = {
            "chat_id": str(chat_id),
            "text": text,
            "disable_web_page_preview": disable_web_page_preview
        }
        
        if parse_mode:
            payload["parse_mode"] = parse_mode
        
        try:
            async with session.post(url, json=payload) as response:
                result = await response.json()
                
                if response.status == 200 and result.get("ok"):
                    logger.info(f"✅ Сообщение успешно отправлено в чат {chat_id}")
                    return result
                else:
                    error_msg = result.get("description", "Unknown error")
                    logger.error(f"❌ Ошибка отправки сообщения: {error_msg}")
                    raise Exception(f"Telegram API error: {error_msg}")
                    
        except aiohttp.ClientError as e:
            logger.error(f"❌ Ошибка сети при отправке сообщения: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Неожиданная ошибка: {e}")
            raise
    
    async def get_updates(self, offset: Optional[int] = None, timeout: int = 10) -> dict:
        """
        Получить обновления от бота (для получения chat_id группы)
        
        Args:
            offset: Идентификатор первого обновления для получения
            timeout: Таймаут в секундах
        
        Returns:
            dict: Обновления от Telegram API
        """
        session = await self._get_session()
        
        url = f"{self.base_url}/getUpdates"
        params = {"timeout": timeout}
        
        if offset:
            params["offset"] = offset
        
        try:
            async with session.get(url, params=params) as response:
                result = await response.json()
                
                if response.status == 200 and result.get("ok"):
                    return result
                else:
                    error_msg = result.get("description", "Unknown error")
                    logger.error(f"❌ Ошибка получения обновлений: {error_msg}")
                    raise Exception(f"Telegram API error: {error_msg}")
                    
        except aiohttp.ClientError as e:
            logger.error(f"❌ Ошибка сети при получении обновлений: {e}")
            raise
    
    async def get_chat_info(self, chat_id: str) -> dict:
        """
        Получить информацию о чате
        
        Args:
            chat_id: ID чата или группы
        
        Returns:
            dict: Информация о чате
        """
        session = await self._get_session()
        
        url = f"{self.base_url}/getChat"
        params = {"chat_id": str(chat_id)}
        
        try:
            async with session.get(url, params=params) as response:
                result = await response.json()
                
                if response.status == 200 and result.get("ok"):
                    return result.get("result", {})
                else:
                    error_msg = result.get("description", "Unknown error")
                    logger.error(f"❌ Ошибка получения информации о чате: {error_msg}")
                    raise Exception(f"Telegram API error: {error_msg}")
                    
        except aiohttp.ClientError as e:
            logger.error(f"❌ Ошибка сети: {e}")
            raise


async def send_trading_signal(
    token: str,
    chat_id: str,
    message: str
) -> bool:
    """
    Удобная функция для отправки торгового сигнала
    
    Args:
        token: Telegram Bot Token
        chat_id: ID группы/чата
        message: Текст сообщения
    
    Returns:
        bool: True если успешно отправлено
    """
    bot = TelegramBot(token)
    try:
        await bot.send_message(chat_id, message)
        return True
    except Exception as e:
        logger.error(f"❌ Не удалось отправить сообщение: {e}")
        return False
    finally:
        await bot.close()


if __name__ == "__main__":
    # Пример использования
    import sys
    
    if len(sys.argv) < 3:
        print("Использование: python telegram_bot.py <TOKEN> <CHAT_ID> [MESSAGE]")
        print("\nДля получения CHAT_ID:")
        print("1. Добавьте бота в группу")
        print("2. Отправьте любое сообщение в группу")
        print("3. Используйте: python telegram_bot.py <TOKEN> get_updates")
        sys.exit(1)
    
    token = sys.argv[1]
    bot = TelegramBot(token)
    
    if sys.argv[2] == "get_updates":
        # Получить обновления для определения chat_id
        async def get_chat_ids():
            result = await bot.get_updates()
            updates = result.get("result", [])
            
            if not updates:
                print("❌ Нет обновлений. Отправьте сообщение в группу и попробуйте снова.")
                return
            
            print("\n📋 Найденные чаты/группы:\n")
            chat_ids = set()
            
            for update in updates:
                if "message" in update:
                    chat = update["message"].get("chat", {})
                    chat_id = chat.get("id")
                    chat_type = chat.get("type")
                    chat_title = chat.get("title") or chat.get("first_name", "Unknown")
                    
                    if chat_id:
                        chat_ids.add((chat_id, chat_type, chat_title))
            
            for chat_id, chat_type, chat_title in sorted(chat_ids):
                print(f"  {chat_type.upper()}: {chat_title}")
                print(f"    CHAT_ID: {chat_id}\n")
        
        asyncio.run(get_chat_ids())
    else:
        # Отправить сообщение
        chat_id = sys.argv[2]
        message = sys.argv[3] if len(sys.argv) > 3 else "Тестовое сообщение"
        
        async def send():
            await bot.send_message(chat_id, message)
            print(f"✅ Сообщение отправлено в чат {chat_id}")
        
        asyncio.run(send())
    
    asyncio.run(bot.close())

