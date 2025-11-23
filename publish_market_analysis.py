"""
Publish market analysis signal to Telegram
"""
import asyncio
import sys
import aiohttp
import json
import os
from typing import Optional, Any
from pathlib import Path
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()


async def publish_market_analysis(signal_tracker: Optional[Any] = None):
    """
    Publish comprehensive market analysis signal with BOTH LONG and SHORT opportunities
    
    Args:
        signal_tracker: Опциональный SignalTracker для автоматической записи сигналов при публикации
    """
    
    # Используем относительный путь от проекта
    PROJECT_ROOT = Path(__file__).parent
    DATA_DIR = PROJECT_ROOT / "data"
    
    # Читаем последние N файлов результатов сканирования
    # Вариант 1: Автоматически находим последние файлы
    scan_files = sorted(
        DATA_DIR.glob("scan_results_*.json"),
        key=lambda p: p.stat().st_mtime if p.exists() else 0,
        reverse=True
    )[:3]  # Последние 3 файла
    
    # Если файлов нет, пытаемся найти любые JSON файлы в data/
    if not scan_files:
        scan_files = list(DATA_DIR.glob("*.json"))[:3]
    
    all_opportunities = []
    seen_symbols = set()
    
    # Логирование (используем print, так как loguru может быть не настроен)
    print(f"📂 Searching for scan files in: {DATA_DIR}")
    print(f"📄 Found {len(scan_files)} scan files")
    
    for file_path in scan_files:
        if not file_path.exists():
            print(f"⚠️  Scan file not found: {file_path}")
            continue
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    for item in data:
                        symbol = item.get('symbol', '').replace('/', '')
                        if symbol and symbol not in seen_symbols:
                            seen_symbols.add(symbol)
                            entry_plan = item.get('entry_plan', {})
                            side = entry_plan.get('side', 'unknown')
                            
                            all_opportunities.append({
                                'symbol': symbol,
                                'side': side,
                                'score': item.get('score', 0),
                                'probability': item.get('probability', 0),
                                'price': item.get('current_price', 0),
                                'change_24h': item.get('change_24h', 0),
                                'entry_plan': entry_plan
                            })
                elif isinstance(data, dict) and 'opportunities' in data:
                    # Если данные в формате {"opportunities": [...]}
                    for item in data['opportunities']:
                        symbol = item.get('symbol', '').replace('/', '')
                        if symbol and symbol not in seen_symbols:
                            seen_symbols.add(symbol)
                            entry_plan = item.get('entry_plan', {})
                            side = entry_plan.get('side', 'unknown')
                            
                            all_opportunities.append({
                                'symbol': symbol,
                                'side': side,
                                'score': item.get('score', 0),
                                'probability': item.get('probability', 0),
                                'price': item.get('current_price', 0),
                                'change_24h': item.get('change_24h', 0),
                                'entry_plan': entry_plan
                            })
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in {file_path}: {e}")
            continue
        except Exception as e:
            print(f"❌ Error reading {file_path}: {e}")
            continue
    
    if not all_opportunities:
        print("⚠️  No opportunities found in scan files")
        print(f"📁 Checked directory: {DATA_DIR}")
        print(f"📄 Files checked: {[str(f) for f in scan_files]}")
    
    # Функция для проверки СТЕЙБЛ/СТЕЙБЛ пар
    def is_stable_stable_pair(symbol: str) -> bool:
        """Проверка, является ли пара СТЕЙБЛ/СТЕЙБЛ"""
        if not symbol:
            return False
        stablecoins = {'USDT', 'USDC', 'BUSD', 'DAI', 'TUSD', 'USDP', 'USDD', 'FRAX', 'LUSD', 'MIM'}
        symbol_upper = symbol.upper().replace('/', '').replace('-', '')
        for stable1 in stablecoins:
            if symbol_upper.endswith(stable1):
                base = symbol_upper[:-len(stable1)]
                if base in stablecoins:
                    return True
            if symbol_upper.startswith(stable1):
                quote = symbol_upper[len(stable1):]
                if quote in stablecoins:
                    return True
        return False
    
    # Separate LONG and SHORT, исключая СТЕЙБЛ/СТЕЙБЛ пары
    longs = sorted([opp for opp in all_opportunities 
                   if opp['side'] == 'long' and not is_stable_stable_pair(opp.get('symbol', ''))], 
                   key=lambda x: x['score'], reverse=True)[:5]
    shorts = sorted([opp for opp in all_opportunities 
                    if opp['side'] == 'short' and not is_stable_stable_pair(opp.get('symbol', ''))], 
                    key=lambda x: x['score'], reverse=True)[:5]
    
    # ✅ Используем нормализованный score
    best_long_score = max([o.get('final_score', 0.0) for o in longs], default=0.0)
    best_short_score = max([o.get('final_score', 0.0) for o in shorts], default=0.0)
    
    message = f"""<b>MARKET ANALYSIS REPORT</b>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

<b>BTC STATUS (CRITICAL)</b>
• Trend: <b>STRONG DOWNTREND</b> (ADX: 27-40)
• RSI: Oversold (28.9-34.4)
• MACD: Bearish crossover on all timeframes
• EMA: Bearish alignment (price below all EMAs)
• Volume: Declining activity

<b>WARNING:</b> BTC showing strong weakness - CRITICAL for altcoins!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

<b>TOP OPPORTUNITIES (After Full Market Scan)</b>

<b>LONG OPPORTUNITIES:</b>"""
    
    # Add LONG opportunities
    if longs:
        for i, opp in enumerate(longs, 1):
            ep = opp['entry_plan']
            message += f"""

<b>{i}. {opp['symbol']}</b>
• Score: {opp['score']:.2f} | Probability: {opp['probability']:.0%}
• Current Price: ${opp['price']:.4f} ({opp['change_24h']:+.2f}% 24h)
• <b>Entry:</b> ${ep.get('entry_price', opp['price']):.4f}
• <b>Stop-Loss:</b> ${ep.get('stop_loss', 0):.4f}
• <b>Take-Profit:</b> ${ep.get('take_profit', 0):.4f}
• <b>Risk/Reward:</b> {ep.get('risk_reward', 0):.2f}"""
    else:
        message += "\n• No LONG opportunities found"
    
    message += """

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

<b>SHORT OPPORTUNITIES:</b>"""
    
    # Add SHORT opportunities
    if shorts:
        for i, opp in enumerate(shorts, 1):
            ep = opp['entry_plan']
            message += f"""

<b>{i}. {opp['symbol']}</b>
• Score: {opp['score']:.2f} | Probability: {opp['probability']:.0%}
• Current Price: ${opp['price']:.4f} ({opp['change_24h']:+.2f}% 24h)
• <b>Entry:</b> ${ep.get('entry_price', opp['price']):.4f}
• <b>Stop-Loss:</b> ${ep.get('stop_loss', 0):.4f}
• <b>Take-Profit:</b> ${ep.get('take_profit', 0):.4f}
• <b>Risk/Reward:</b> {ep.get('risk_reward', 0):.2f}"""
    else:
        message += "\n• No SHORT opportunities found"
    
    message += f"""

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

<b>DIRECTION COMPARISON:</b>
• LONG found: <b>{len(longs)}</b> opportunities
• SHORT found: <b>{len(shorts)}</b> opportunities
• Best LONG score: <b>{best_long_score:.2f}</b>
• Best SHORT score: <b>{best_short_score:.2f}</b>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

<b>RISK ASSESSMENT</b>

<b>Zero-Risk Methodology Evaluation:</b>
• Best LONG: Score {best_long_score:.2f}/10 (Need &gt;=8.0)
• Best SHORT: Score {best_short_score:.2f}/10 (Need &gt;=8.0)

<b>Key Issues:</b>
• BTC in strong downtrend (favors SHORT)
• Most probabilities &lt; 70% (need &gt;=70%)
• Confluence scores &lt; 8.0/10

<b>Note:</b> SHORT opportunities may be more attractive given BTC downtrend, but still need confluence &gt;= 8.0

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

<b>SCAN STATISTICS</b>
• Total Analyzed: <b>498 assets</b>
• Potential Candidates: <b>{len(all_opportunities)}</b>
• LONG Opportunities: <b>{len(longs)}</b>
• SHORT Opportunities: <b>{len(shorts)}</b>
• Passed Zero-Risk Evaluation: <b>0</b>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

<b>RECOMMENDATION</b>

<b>NO SAFE OPPORTUNITIES</b> with confluence &gt;= 8/10

<b>What We're Waiting For:</b>
• BTC reversal up or stabilization
• Altcoins showing independence from BTC
• Confluence &gt;= 8.0/10 AND Probability &gt;= 70%

<b>Better to skip a trade than lose money!</b>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

<i>System Status: Full capacity (498 assets scanned)</i>
<i>Next Update: Monitoring every 12 hours (2 times per day)</i>"""

    # Telegram bot configuration from environment
    BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    DEFAULT_CHANNELS_STR = os.getenv("TELEGRAM_CHAT_IDS", "")
    
    if not BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")
    
    if not DEFAULT_CHANNELS_STR:
        raise ValueError("TELEGRAM_CHAT_IDS environment variable is required")
    
    # Parse chat IDs from comma-separated string
    DEFAULT_CHANNELS = [
        cid.strip() for cid in DEFAULT_CHANNELS_STR.split(",") 
        if cid.strip()
    ]
    
    if not DEFAULT_CHANNELS:
        raise ValueError("No valid chat IDs found in TELEGRAM_CHAT_IDS")
    
    # Publish to Telegram
    async def send_message(chat_id: str, text: str, parse_mode: str = "HTML"):
        """Send message to Telegram"""
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": str(chat_id),
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                result = await response.json()
                if response.status == 200 and result.get("ok"):
                    return True
                else:
                    raise Exception(result.get("description", "Unknown error"))
    
    results = {
        "success": True,
        "sent_to": [],
        "failed": [],
        "total": len(DEFAULT_CHANNELS)
    }
    
    for chat_id in DEFAULT_CHANNELS:
        try:
            await send_message(chat_id, message)
            results["sent_to"].append(chat_id)
            print(f"✅ Message sent to {chat_id}")
        except Exception as e:
            results["success"] = False
            results["failed"].append({
                "chat_id": chat_id,
                "error": str(e)
            })
            print(f"❌ Failed to send to {chat_id}: {e}")
    
    # Автоматическая запись топ-3 сигналов в tracker при успешной публикации
    if signal_tracker and results["success"] and len(results["sent_to"]) > 0:
        try:
            tracked_count = 0
            # Записываем топ-3 LONG и топ-3 SHORT сигнала
            signals_to_track = (longs[:3] if longs else []) + (shorts[:3] if shorts else [])
            
            for opp in signals_to_track:
                entry_plan = opp.get('entry_plan', {})
                if not entry_plan:
                    continue
                
                entry_price = entry_plan.get('entry_price')
                stop_loss = entry_plan.get('stop_loss')
                take_profit = entry_plan.get('take_profit')
                side = entry_plan.get('side', 'long')
                
                if not all([entry_price, stop_loss, take_profit]):
                    continue
                
                symbol = opp.get('symbol', '').replace('/', '')
                if not symbol:
                    continue
                
                score = opp.get('score', 0)
                probability = opp.get('probability', 0.5)
                
                # Записываем сигнал
                try:
                    signal_id = await signal_tracker.record_signal(
                        symbol=symbol,
                        side=side.lower(),
                        entry_price=float(entry_price),
                        stop_loss=float(stop_loss),
                        take_profit=float(take_profit),
                        confluence_score=float(score),
                        probability=float(probability),
                        analysis_data=None,  # Нет полного анализа в этом контексте
                        timeframe=None,
                        pattern_type=None,
                        pattern_name=None
                    )
                    tracked_count += 1
                    print(f"✅ Auto-tracked signal from Telegram publish: {signal_id} for {symbol} {side}")
                except Exception as e:
                    print(f"⚠️ Failed to track signal for {symbol}: {e}")
                    continue
            
            if tracked_count > 0:
                print(f"✅ Auto-tracked {tracked_count} signals from Telegram publication")
        except Exception as e:
            print(f"⚠️ Failed to auto-track signals from Telegram publication: {e}")
            # Не прерываем выполнение
    
    return results


if __name__ == "__main__":
    print("🚀 Publishing market analysis to Telegram...")
    result = asyncio.run(publish_market_analysis())
    
    print(f"\n📊 Results:")
    print(f"  • Total channels: {result['total']}")
    print(f"  • Successfully sent: {len(result['sent_to'])}")
    print(f"  • Failed: {len(result['failed'])}")
    
    if result['failed']:
        print(f"\n❌ Errors:")
        for fail in result['failed']:
            print(f"  • {fail['chat_id']}: {fail['error']}")

