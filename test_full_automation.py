"""
Тест полной автоматизации автономного агента
"""

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from autonomous_agent.autonomous_analyzer import AutonomousAnalyzer
from autonomous_agent.telegram_formatter import TelegramFormatter
from loguru import logger

logger.add(
    sys.stdout,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>",
    level="INFO"
)


async def test_full_automation():
    """Тест полной автоматизации"""
    print("\n" + "=" * 60)
    print("ТЕСТ ПОЛНОЙ АВТОМАТИЗАЦИИ")
    print("=" * 60)
    
    # Загрузка конфигурации
    qwen_api_key = os.getenv("QWEN_API_KEY", "")
    bybit_api_key = os.getenv("BYBIT_API_KEY", "")
    bybit_api_secret = os.getenv("BYBIT_API_SECRET", "")
    testnet = os.getenv("BYBIT_TESTNET", "false").lower() == "true"
    
    if not qwen_api_key:
        print("❌ QWEN_API_KEY не установлен!")
        return False
    
    if not bybit_api_key or not bybit_api_secret:
        print("⚠️ BYBIT_API_KEY или BYBIT_API_SECRET не установлены")
        print("   Тестирую только Qwen без реальных данных Bybit...")
        # Можно протестировать только Qwen часть
        return await test_qwen_only()
    
    try:
        print("\n📊 Инициализация анализатора...")
        analyzer = AutonomousAnalyzer(
            qwen_api_key=qwen_api_key,
            bybit_api_key=bybit_api_key,
            bybit_api_secret=bybit_api_secret,
            qwen_model="qwen/qwen-turbo",
            testnet=testnet
        )
        
        print("✅ Анализатор инициализирован")
        print("\n🚀 Запуск полного анализа рынка...")
        print("⏳ Это может занять 2-5 минут...")
        
        result = await analyzer.analyze_market()
        
        if result.get("success"):
            print("\n✅ Анализ завершён успешно!")
            
            # Форматирование
            formatter = TelegramFormatter()
            telegram_message = formatter.format_top_opportunities(result)
            
            # Вывод результата
            print("\n" + "=" * 60)
            print("РЕЗУЛЬТАТ АНАЛИЗА")
            print("=" * 60)
            print(telegram_message[:1000])  # Первые 1000 символов
            if len(telegram_message) > 1000:
                print("\n... (сообщение обрезано, полный текст в файле)")
            print("=" * 60)
            
            # Сохранение
            data_dir = Path(__file__).parent / "data"
            data_dir.mkdir(parents=True, exist_ok=True)
            
            analysis_file = data_dir / "latest_analysis.json"
            analysis_file.write_text(
                json.dumps(result, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
            print(f"\n💾 Результат сохранён: {analysis_file}")
            
            telegram_file = data_dir / "latest_telegram_message.txt"
            telegram_file.write_text(telegram_message, encoding="utf-8")
            print(f"💾 Telegram сообщение сохранено: {telegram_file}")
            
            # Проверка результатов
            opportunities = result.get("opportunities", [])
            print(f"\n🎯 Найдено возможностей: {len(opportunities)}")
            
            if opportunities:
                for i, opp in enumerate(opportunities[:3], 1):
                    print(f"\n   {i}. {opp.get('symbol', 'N/A')} ({opp.get('side', 'N/A').upper()})")
                    print(f"      Confluence: {opp.get('confluence_score', 0)}/10")
                    print(f"      Probability: {opp.get('probability', 0)*100:.0f}%")
            
            await analyzer.close()
            return True
        else:
            error = result.get("error", "Unknown error")
            print(f"\n❌ Ошибка анализа: {error}")
            await analyzer.close()
            return False
            
    except Exception as e:
        print(f"\n❌ Исключение: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_qwen_only():
    """Тест только Qwen без Bybit данных"""
    print("\n📝 Тестирую только Qwen AI анализ...")
    
    from autonomous_agent.qwen_client import QwenClient
    
    qwen_api_key = os.getenv("QWEN_API_KEY", "")
    client = QwenClient(qwen_api_key, model="qwen/qwen-turbo")
    
    # Тестовые данные
    market_data = {
        "market_overview": {
            "btc_price": 50000,
            "market_sentiment": "bullish"
        },
        "scanned_opportunities": [
            {
                "symbol": "BTC/USDT",
                "score": 8.5,
                "indicators": {"rsi": 28, "macd": "bullish"}
            }
        ]
    }
    
    system_instructions = "Ты профессиональный торговый аналитик."
    
    result = await client.analyze_market_opportunities(
        market_data=market_data,
        system_instructions=system_instructions
    )
    
    if result.get("success"):
        print("✅ Qwen анализ работает!")
        return True
    else:
        print(f"❌ Ошибка: {result.get('error')}")
        return False


async def main():
    """Запуск теста"""
    print("\n" + "🚀" * 30)
    print("ТЕСТ ПОЛНОЙ АВТОМАТИЗАЦИИ")
    print("🚀" * 30)
    
    result = await test_full_automation()
    
    print("\n" + "=" * 60)
    if result:
        print("✅ ТЕСТ ПРОШЁЛ УСПЕШНО!")
        print("🎉 Система готова к развёртыванию!")
    else:
        print("❌ ТЕСТ ПРОВАЛЕН")
        print("Проверьте логи выше для деталей")
    print("=" * 60)
    
    return 0 if result else 1


if __name__ == "__main__":
    import json
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

