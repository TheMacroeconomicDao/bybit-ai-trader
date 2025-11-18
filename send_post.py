#!/usr/bin/env python3
"""
Простой скрипт для отправки поста в Telegram группу
Использование: python send_post.py <CHAT_ID>
"""
import asyncio
import aiohttp
import sys

BOT_TOKEN = "8003689195:AAGxQsopKvlLS34H2TZ0S1a0K7s4yV4iOBY"

MESSAGE = """<b>⚡ ДЕТАЛЬНЫЙ ПЛАН СДЕЛОК</b>

<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>

<b>📊 СДЕЛКА #1: ZEN/USDT</b>

<b>Entry:</b> $15.89
<b>Stop-Loss:</b> $13.58
<b>Take-Profit:</b> $20.52

<b>Risk/Reward:</b> 1:2.0

<b>Position Size:</b> Рассчитать на основе вашего депозита:

• <b>Риск на сделку:</b> 1-2% от депозита (рекомендуется 1%)
• <b>Расчёт:</b> (Ваш риск в $) / (Entry - SL = $2.31) = количество ZEN
• <b>Пример:</b> При риске 1% и депозите $X → риск = $X × 0.01 → Position size = риск / $2.31

<b>⏰ Safe Time Window:</b> 12-18 часов
<b>⏱️ Максимум:</b> 24 часа

<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>

<b>📊 СДЕЛКА #2: XPL/USDT</b>

<b>Entry:</b> $0.240
<b>Stop-Loss:</b> $0.210
<b>Take-Profit:</b> $0.300

<b>Risk/Reward:</b> 1:2.0

<b>Position Size:</b> Рассчитать на основе вашего депозита:

• <b>Риск на сделку:</b> 1-2% от депозита (рекомендуется 1%)
• <b>Расчёт:</b> (Ваш риск в $) / (Entry - SL = $0.030) = количество XPL
• <b>Пример:</b> При риске 1% и депозите $X → риск = $X × 0.01 → Position size = риск / $0.030

<b>⏰ Safe Time Window:</b> 8-12 часов
<b>⏱️ Максимум:</b> 18 часов

<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>

<b>📊 СДЕЛКА #3: MINA/USDT</b>

<b>Entry:</b> $0.143
<b>Stop-Loss:</b> $0.120
<b>Take-Profit:</b> $0.190

<b>Risk/Reward:</b> 1:2.04

<b>Position Size:</b> Рассчитать на основе вашего депозита:

• <b>Риск на сделку:</b> 1-2% от депозита (рекомендуется 1%)
• <b>Расчёт:</b> (Ваш риск в $) / (Entry - SL = $0.023) = количество MINA
• <b>Пример:</b> При риске 1% и депозите $X → риск = $X × 0.01 → Position size = риск / $0.023

<b>⏰ Safe Time Window:</b> 8-12 часов
<b>⏱️ Максимум:</b> 16 часов

<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>

<b>💰 ОБЩИЙ РИСК ПОРТФЕЛЯ</b>

Если открыть все 3 позиции одновременно:

• <b>Общий риск:</b> 3-6% от депозита (при риске 1-2% на сделку)
• <b>Рекомендация:</b> Не превышать 5% общего риска портфеля
• <b>Максимум позиций:</b> 2-3 одновременно (в зависимости от размера депозита)

<b>Формула для расчёта:</b>
<code>Общий риск = (Риск на сделку %) × (Количество позиций)
Пример: 1% × 3 = 3% общего риска</code>

<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>

<b>🎯 CONFIDENCE В АНАЛИЗЕ: 8.0/10</b>

Все 3 актива:

✅ Outperforming BTC на 10-27%
✅ Multi-TF alignment bullish
✅ R:R ≥ 1:2
✅ Probability ≥ 95%
✅ Хорошая ликвидность

<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>

<b>🤔 ОТКРЫВАТЬ?</b>

<b>Моя рекомендация:</b> ДА, но с осторожностью

<b>Почему:</b>

1️⃣ BTC в медвежьем тренде — основной риск
2️⃣ Все 3 актива outperforming BTC — показывает силу
3️⃣ Confluence ≥ 7.0/10 для всех
4️⃣ R:R ≥ 1:2 для всех
5️⃣ Probability ≥ 95% для всех

<b>Стратегия входа:</b>

🎯 Начать с <b>ZEN/USDT</b> (лучший confluence 8.0/10)
🎯 Затем <b>XPL/USDT</b> (отличная ликвидность)
🎯 <b>MINA/USDT</b> — только если первые 2 работают

<b>⚠️ Важно:</b>

• Мониторить BTC каждые 30-60 минут
• Exit при первых признаках слабости BTC
• Не превышать safe time window
• Использовать риск 1-2% на сделку (не более 5% общего риска портфеля)

<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"""


async def send_message(chat_id: str):
    """Отправить сообщение в Telegram группу"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    payload = {
        "chat_id": chat_id,
        "text": MESSAGE,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as response:
            result = await response.json()
            
            if response.status == 200 and result.get("ok"):
                print(f"✅ Сообщение успешно отправлено в группу (CHAT_ID: {chat_id})")
                return True
            else:
                error_msg = result.get("description", "Unknown error")
                print(f"❌ Ошибка: {error_msg}")
                print(f"   Полный ответ: {result}")
                return False


# Chat IDs каналов по умолчанию
DEFAULT_CHANNELS = [
    "-1003382613825",  # DIAMOND HEADZH
    "-1003484839912",  # Hypov Hedge Fund (AI Signals)
]

async def send_to_all_channels(channel_ids=None):
    """Отправить сообщение во все указанные каналы"""
    if channel_ids is None:
        channel_ids = DEFAULT_CHANNELS
    
    channel_names = {
        "-1003382613825": "DIAMOND HEADZH",
        "-1003484839912": "Hypov Hedge Fund (AI Signals)"
    }
    
    print(f"📤 Отправка сообщения в {len(channel_ids)} канал(ов)...\n")
    
    results = []
    for chat_id in channel_ids:
        name = channel_names.get(chat_id, "")
        success = await send_message(chat_id)
        results.append((chat_id, success))
    
    print(f"\n📊 Результаты:")
    success_count = sum(1 for _, success in results if success)
    print(f"✅ Успешно: {success_count}/{len(results)}")
    
    return all(success for _, success in results)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Использовать указанные chat_id
        channel_ids = sys.argv[1:]
        try:
            success = asyncio.run(send_to_all_channels(channel_ids))
            sys.exit(0 if success else 1)
        except KeyboardInterrupt:
            print("\n⚠️ Прервано пользователем")
            sys.exit(0)
        except Exception as e:
            print(f"\n❌ Ошибка: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    else:
        # Использовать каналы по умолчанию
        print("💡 Используются каналы по умолчанию:")
        for chat_id in DEFAULT_CHANNELS:
            print(f"   - {chat_id}")
        print()
        try:
            success = asyncio.run(send_to_all_channels())
            sys.exit(0 if success else 1)
        except KeyboardInterrupt:
            print("\n⚠️ Прервано пользователем")
            sys.exit(0)
        except Exception as e:
            print(f"\n❌ Ошибка: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

