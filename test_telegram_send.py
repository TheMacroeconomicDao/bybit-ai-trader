#!/usr/bin/env python3
"""
Тестовый скрипт для проверки отправки сообщений в Telegram
"""
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from mcp_server.telegram_bot import TelegramBot


async def test_telegram_send():
    """Тест отправки сообщения в Telegram"""
    
    # Получаем токен и chat_id из переменных окружения или используем дефолтные
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "8003689195:AAGxQsopKvlLS34H2TZ0S1a0K7s4yV4iOBY")
    chat_ids_str = os.getenv("TELEGRAM_CHAT_IDS", "-1003382613825,-1003484839912")
    
    if not bot_token:
        print("❌ TELEGRAM_BOT_TOKEN не установлен!")
        return False
    
    if not chat_ids_str:
        print("❌ TELEGRAM_CHAT_IDS не установлен!")
        return False
    
    chat_ids = [cid.strip() for cid in chat_ids_str.split(",") if cid.strip()]
    
    if not chat_ids:
        print("❌ Нет валидных chat_ids!")
        return False
    
    print(f"🔍 Тестирование отправки в Telegram...")
    print(f"   Bot Token: {bot_token[:20]}...")
    print(f"   Chat IDs: {chat_ids}")
    print()
    
    # Тестовое сообщение
    test_message = """🧪 ТЕСТОВОЕ СООБЩЕНИЕ

Это тестовое сообщение от квен агента для проверки работы системы отправки сигналов.

✅ Если вы видите это сообщение, значит система работает корректно!

Время: {time}
""".format(time=asyncio.get_event_loop().time())
    
    bot = TelegramBot(bot_token)
    
    try:
        results = []
        for chat_id in chat_ids:
            try:
                print(f"📤 Отправка в чат {chat_id}...")
                result = await bot.send_message(
                    chat_id=chat_id,
                    text=test_message,
                    parse_mode=None
                )
                print(f"✅ Успешно отправлено в {chat_id}")
                results.append({"chat_id": chat_id, "success": True})
            except Exception as e:
                print(f"❌ Ошибка отправки в {chat_id}: {e}")
                results.append({"chat_id": chat_id, "success": False, "error": str(e)})
        
        # Итоги
        print()
        print("=" * 60)
        print("📊 РЕЗУЛЬТАТЫ ТЕСТА")
        print("=" * 60)
        success_count = sum(1 for r in results if r.get("success"))
        total_count = len(results)
        
        for result in results:
            status = "✅" if result.get("success") else "❌"
            print(f"{status} Chat {result['chat_id']}: {result.get('error', 'OK')}")
        
        print()
        print(f"Итого: {success_count}/{total_count} успешно")
        
        return success_count == total_count
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await bot.close()


if __name__ == "__main__":
    success = asyncio.run(test_telegram_send())
    sys.exit(0 if success else 1)

