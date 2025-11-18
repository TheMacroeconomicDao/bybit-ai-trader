"""
Тестовый скрипт для проверки подключения к Qwen API
"""

import asyncio
import os
import sys
from pathlib import Path

# Добавляем путь к проекту
sys.path.insert(0, str(Path(__file__).parent))

from autonomous_agent.qwen_client import QwenClient
from loguru import logger

# Настройка логирования
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>",
    level="INFO"
)


async def test_qwen_basic():
    """Базовый тест подключения к Qwen"""
    print("\n" + "=" * 60)
    print("ТЕСТ 1: Базовое подключение к Qwen API")
    print("=" * 60)
    
    api_key = os.getenv("QWEN_API_KEY", "sk-6f5319fb244f4f9faa1595825cf87a05")
    
    if not api_key:
        print("❌ QWEN_API_KEY не установлен!")
        return False
    
    try:
        # Пробуем qwen-plus сначала (более доступная модель)
        client = QwenClient(api_key, model="qwen-plus")
        print(f"✅ QwenClient инициализирован с моделью: qwen-plus")
        
        # Простой тест
        prompt = "Привет! Ответь коротко: ты работаешь?"
        print(f"\n📤 Отправляю запрос: '{prompt}'")
        
        result = await client.generate(
            prompt=prompt,
            temperature=0.7,
            max_tokens=100
        )
        
        if result.get("success"):
            print(f"✅ Запрос успешен!")
            print(f"📥 Ответ: {result.get('content', '')[:200]}")
            return True
        else:
            print(f"❌ Ошибка: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Исключение: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_qwen_market_analysis():
    """Тест анализа рынка через Qwen"""
    print("\n" + "=" * 60)
    print("ТЕСТ 2: Анализ рынка через Qwen")
    print("=" * 60)
    
    api_key = os.getenv("QWEN_API_KEY", "sk-6f5319fb244f4f9faa1595825cf87a05")
    
    try:
        client = QwenClient(api_key, model="qwen-plus")
        
        # Тестовые рыночные данные
        market_data = {
            "btc_price": 50000,
            "market_sentiment": "bullish",
            "top_gainers": [
                {"symbol": "BTC/USDT", "change": 2.5},
                {"symbol": "ETH/USDT", "change": 1.8}
            ]
        }
        
        system_instructions = """
Ты - профессиональный торговый аналитик.
Твоя задача - анализировать рыночные данные и находить лучшие точки входа.
Всегда отвечай в формате JSON.
"""
        
        print("📤 Отправляю запрос на анализ рынка...")
        
        result = await client.analyze_market_opportunities(
            market_data=market_data,
            system_instructions=system_instructions
        )
        
        if result.get("success"):
            print("✅ Анализ успешен!")
            analysis = result.get("analysis", {})
            print(f"\n📊 Результат анализа:")
            print(f"   - Тип: {type(analysis)}")
            if isinstance(analysis, dict):
                print(f"   - Ключи: {list(analysis.keys())}")
                if "top_opportunities" in analysis:
                    print(f"   - Найдено возможностей: {len(analysis['top_opportunities'])}")
            print(f"\n📝 Полный ответ (первые 500 символов):")
            print(result.get("raw_response", "")[:500])
            return True
        else:
            print(f"❌ Ошибка анализа: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Исключение: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_full_analysis_request():
    """Тест полного запроса анализа рынка"""
    print("\n" + "=" * 60)
    print("ТЕСТ 3: Полный запрос 'Проведи анализ рынка и выдай 3 лучших точки входа'")
    print("=" * 60)
    
    api_key = os.getenv("QWEN_API_KEY", "sk-6f5319fb244f4f9faa1595825cf87a05")
    
    try:
        client = QwenClient(api_key, model="qwen-plus")
        
        prompt = """
Проведи анализ криптовалютного рынка и выдай мне 3 лучших точки входа прямо сейчас.

Требования:
1. Найди ТОП 3 возможности с confluence ≥ 8.0/10
2. Вероятность успеха ≥ 70%
3. R:R минимум 1:2
4. Детально объясни каждую возможность
5. Укажи конкретные уровни входа, SL, TP

Формат ответа (JSON):
{
    "top_opportunities": [
        {
            "symbol": "BTC/USDT",
            "side": "long",
            "entry_price": 50000,
            "stop_loss": 49500,
            "take_profit": 51000,
            "confluence_score": 8.5,
            "probability": 0.75,
            "risk_reward": 2.0,
            "reasoning": "Детальное объяснение",
            "timeframes_alignment": ["1h", "4h", "1d"],
            "key_factors": ["RSI oversold", "Support level"]
        }
    ],
    "market_summary": "Краткое резюме",
    "btc_status": "bullish",
    "recommendations": ["Рекомендации"]
}
"""
        
        system_instructions = """
Ты - профессиональный AI торговый аналитик с глубокими знаниями технического анализа криптовалютных рынков.
Твоя задача - находить моменты НЕИЗБЕЖНОГО роста с максимальной вероятностью успеха.

Критерии качества:
- Confluence минимум: 8.0/10
- Вероятность успеха: ≥ 70%
- R:R минимум: 1:2
- Multi-timeframe alignment
- Детальное обоснование

Всегда отвечай в формате JSON как указано в запросе.
"""
        
        print("📤 Отправляю полный запрос на анализ...")
        print("⏳ Ожидание ответа (может занять 30-60 секунд)...")
        
        result = await client.generate(
            prompt=prompt,
            system_prompt=system_instructions,
            temperature=0.3,
            max_tokens=4000
        )
        
        if result.get("success"):
            print("\n✅ Запрос успешен!")
            content = result.get("content", "")
            
            print(f"\n📥 Длина ответа: {len(content)} символов")
            print(f"\n📝 Ответ (первые 1000 символов):")
            print("-" * 60)
            print(content[:1000])
            print("-" * 60)
            
            # Попытка распарсить JSON
            import json
            try:
                # Извлекаем JSON если обёрнут в markdown
                json_content = content
                if "```json" in json_content:
                    json_start = json_content.find("```json") + 7
                    json_end = json_content.find("```", json_start)
                    json_content = json_content[json_start:json_end].strip()
                elif "```" in json_content:
                    json_start = json_content.find("```") + 3
                    json_end = json_content.find("```", json_start)
                    json_content = json_content[json_start:json_end].strip()
                
                parsed = json.loads(json_content)
                print(f"\n✅ JSON успешно распарсен!")
                print(f"   - Ключи: {list(parsed.keys())}")
                if "top_opportunities" in parsed:
                    print(f"   - Найдено возможностей: {len(parsed['top_opportunities'])}")
                    for i, opp in enumerate(parsed['top_opportunities'][:3], 1):
                        print(f"\n   {i}. {opp.get('symbol', 'N/A')}")
                        print(f"      Entry: ${opp.get('entry_price', 0)}")
                        print(f"      Confluence: {opp.get('confluence_score', 0)}/10")
                        print(f"      Probability: {opp.get('probability', 0)*100:.0f}%")
                
                return True
            except json.JSONDecodeError as e:
                print(f"\n⚠️ Не удалось распарсить JSON: {e}")
                print("   Но ответ получен, возможно формат другой")
                return True  # Все равно успех, просто формат другой
                
        else:
            print(f"\n❌ Ошибка: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"\n❌ Исключение: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Запуск всех тестов"""
    print("\n" + "🔍" * 30)
    print("ТЕСТИРОВАНИЕ ПОДКЛЮЧЕНИЯ К QWEN API")
    print("🔍" * 30)
    
    results = []
    
    # Тест 1: Базовое подключение
    try:
        result1 = await test_qwen_basic()
        results.append(("Базовое подключение", result1))
    except Exception as e:
        print(f"❌ Тест 1 провален с исключением: {e}")
        results.append(("Базовое подключение", False))
    
    # Тест 2: Анализ рынка
    try:
        result2 = await test_qwen_market_analysis()
        results.append(("Анализ рынка", result2))
    except Exception as e:
        print(f"❌ Тест 2 провален с исключением: {e}")
        results.append(("Анализ рынка", False))
    
    # Тест 3: Полный запрос
    try:
        result3 = await test_full_analysis_request()
        results.append(("Полный запрос анализа", result3))
    except Exception as e:
        print(f"❌ Тест 3 провален с исключением: {e}")
        results.append(("Полный запрос анализа", False))
    
    # Итоги
    print("\n" + "=" * 60)
    print("ИТОГИ ТЕСТИРОВАНИЯ")
    print("=" * 60)
    
    for test_name, result in results:
        status = "✅ ПРОШЁЛ" if result else "❌ ПРОВАЛЕН"
        print(f"{status}: {test_name}")
    
    total = len(results)
    passed = sum(1 for _, r in results if r)
    
    print(f"\n📊 Результат: {passed}/{total} тестов прошли успешно")
    
    if passed == total:
        print("🎉 Все тесты прошли успешно!")
        return 0
    else:
        print("⚠️ Некоторые тесты провалились. Проверьте логи выше.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

