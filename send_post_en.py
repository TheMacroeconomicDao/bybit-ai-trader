#!/usr/bin/env python3
"""
Скрипт для отправки торгового сигнала на английском языке в Telegram каналы
Использование: python send_post_en.py [CHAT_ID1] [CHAT_ID2]
"""
import asyncio
import aiohttp
import sys

BOT_TOKEN = "8003689195:AAGxQsopKvlLS34H2TZ0S1a0K7s4yV4iOBY"

# Chat IDs каналов по умолчанию
DEFAULT_CHANNELS = [
    "-1003382613825",  # DIAMOND HEADZH
    "-1003484839912",  # Hypov Hedge Fund (AI Signals)
]

ENGLISH_MESSAGE = """<b>⚡ DETAILED TRADING PLAN</b>

<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>

<b>📊 TRADE #1: ZEN/USDT</b>

<b>Entry:</b> $15.89
<b>Stop-Loss:</b> $13.58
<b>Take-Profit:</b> $20.52

<b>Risk/Reward:</b> 1:2.0

<b>Position Size:</b> Calculate based on your deposit:

• <b>Risk per trade:</b> 1-2% of deposit (1% recommended)
• <b>Calculation:</b> (Your risk in $) / (Entry - SL = $2.31) = ZEN amount
• <b>Example:</b> With 1% risk and $X deposit → risk = $X × 0.01 → Position size = risk / $2.31

<b>⏰ Safe Time Window:</b> 12-18 hours
<b>⏱️ Maximum:</b> 24 hours

<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>

<b>📊 TRADE #2: XPL/USDT</b>

<b>Entry:</b> $0.240
<b>Stop-Loss:</b> $0.210
<b>Take-Profit:</b> $0.300

<b>Risk/Reward:</b> 1:2.0

<b>Position Size:</b> Calculate based on your deposit:

• <b>Risk per trade:</b> 1-2% of deposit (1% recommended)
• <b>Calculation:</b> (Your risk in $) / (Entry - SL = $0.030) = XPL amount
• <b>Example:</b> With 1% risk and $X deposit → risk = $X × 0.01 → Position size = risk / $0.030

<b>⏰ Safe Time Window:</b> 8-12 hours
<b>⏱️ Maximum:</b> 18 hours

<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>

<b>📊 TRADE #3: MINA/USDT</b>

<b>Entry:</b> $0.143
<b>Stop-Loss:</b> $0.120
<b>Take-Profit:</b> $0.190

<b>Risk/Reward:</b> 1:2.04

<b>Position Size:</b> Calculate based on your deposit:

• <b>Risk per trade:</b> 1-2% of deposit (1% recommended)
• <b>Calculation:</b> (Your risk in $) / (Entry - SL = $0.023) = MINA amount
• <b>Example:</b> With 1% risk and $X deposit → risk = $X × 0.01 → Position size = risk / $0.023

<b>⏰ Safe Time Window:</b> 8-12 hours
<b>⏱️ Maximum:</b> 16 hours

<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>

<b>💰 PORTFOLIO RISK</b>

If opening all 3 positions simultaneously:

• <b>Total risk:</b> 3-6% of deposit (with 1-2% risk per trade)
• <b>Recommendation:</b> Do not exceed 5% total portfolio risk
• <b>Maximum positions:</b> 2-3 simultaneously (depending on deposit size)

<b>Calculation formula:</b>
<code>Total risk = (Risk per trade %) × (Number of positions)
Example: 1% × 3 = 3% total risk</code>

<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>

<b>🎯 ANALYSIS CONFIDENCE: 8.0/10</b>

All 3 assets:

✅ Outperforming BTC by 10-27%
✅ Multi-TF alignment bullish
✅ R:R ≥ 1:2
✅ Probability ≥ 95%
✅ Good liquidity

<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>

<b>🤔 OPEN POSITIONS?</b>

<b>My recommendation:</b> YES, but with caution

<b>Why:</b>

1️⃣ BTC in bearish trend — main risk
2️⃣ All 3 assets outperforming BTC — shows strength
3️⃣ Confluence ≥ 7.0/10 for all
4️⃣ R:R ≥ 1:2 for all
5️⃣ Probability ≥ 95% for all

<b>Entry strategy:</b>

🎯 Start with <b>ZEN/USDT</b> (best confluence 8.0/10)
🎯 Then <b>XPL/USDT</b> (excellent liquidity)
🎯 <b>MINA/USDT</b> — only if first 2 work

<b>⚠️ Important:</b>

• Monitor BTC every 30-60 minutes
• Exit at first signs of BTC weakness
• Do not exceed safe time window
• Use 1-2% risk per trade (no more than 5% total portfolio risk)

<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"""


async def send_message(chat_id: str, channel_name: str = ""):
    """Отправить сообщение в Telegram канал"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    payload = {
        "chat_id": chat_id,
        "text": ENGLISH_MESSAGE,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as response:
            result = await response.json()
            
            if response.status == 200 and result.get("ok"):
                name = channel_name or f"канал {chat_id}"
                print(f"✅ Сообщение успешно отправлено в {name} (CHAT_ID: {chat_id})")
                return True
            else:
                error_msg = result.get("description", "Unknown error")
                print(f"❌ Ошибка отправки: {error_msg}")
                # Пробуем без HTML
                print("Пробую без форматирования...")
                payload["parse_mode"] = None
                async with session.post(url, json=payload) as retry_response:
                    retry_result = await retry_response.json()
                    if retry_response.status == 200 and retry_result.get("ok"):
                        name = channel_name or f"канал {chat_id}"
                        print(f"✅ Сообщение отправлено в {name} (без форматирования)")
                        return True
                    else:
                        print(f"❌ Ошибка: {retry_result.get('description', 'Unknown')}")
                        return False


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
        success = await send_message(chat_id, name)
        results.append((chat_id, success))
    
    print(f"\n📊 Результаты:")
    success_count = sum(1 for _, success in results if success)
    print(f"✅ Успешно: {success_count}/{len(results)}")
    
    return all(success for _, success in results)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Использовать указанные chat_id
        channel_ids = sys.argv[1:]
        asyncio.run(send_to_all_channels(channel_ids))
    else:
        # Использовать каналы по умолчанию
        print("💡 Используются каналы по умолчанию:")
        for chat_id in DEFAULT_CHANNELS:
            print(f"   - {chat_id}")
        print()
        asyncio.run(send_to_all_channels())

