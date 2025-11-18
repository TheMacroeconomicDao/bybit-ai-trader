"""
Упрощённый тест Qwen API через OpenRouter
"""

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from autonomous_agent.qwen_client import QwenClient
from loguru import logger

logger.add(
    sys.stdout,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>",
    level="INFO"
)


async def test_simple():
    """Простой тест без fallback"""
    print("\n" + "=" * 60)
    print("ПРОСТОЙ ТЕСТ QWEN API")
    print("=" * 60)
    
    api_key = os.getenv("QWEN_API_KEY", "")
    
    if not api_key:
        print("❌ QWEN_API_KEY не установлен!")
        print("   Получите ключ на: https://openrouter.ai/keys")
        print("   Формат ключа: sk-or-v1-...")
        return False
    
    try:
        # Используем OpenRouter формат модели
        print(f"\n📤 Тестирую модель: qwen/qwen-turbo (OpenRouter)")
        client = QwenClient(api_key, model="qwen/qwen-turbo")
        
        prompt = "Привет! Ответь одним словом: работаешь?"
        print(f"📝 Запрос: '{prompt}'")
        
        result = await client.generate(
            prompt=prompt,
            temperature=0.7,
            max_tokens=50
        )
        
        if result.get("success"):
            print(f"\n✅ УСПЕХ!")
            print(f"📥 Ответ: {result.get('content', '')}")
            if result.get("model_used"):
                print(f"🔧 Использована модель: {result.get('model_used')}")
            return True
        else:
            print(f"\n❌ ОШИБКА: {result.get('error', 'Unknown')}")
            return False
            
    except Exception as e:
        print(f"\n❌ ИСКЛЮЧЕНИЕ: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_market_analysis():
    """Тест анализа рынка"""
    print("\n" + "=" * 60)
    print("ТЕСТ АНАЛИЗА РЫНКА")
    print("=" * 60)
    
    api_key = os.getenv("QWEN_API_KEY", "")
    
    if not api_key:
        print("⚠️ QWEN_API_KEY не установлен!")
        return False
    
    try:
        client = QwenClient(api_key, model="qwen/qwen-turbo")
        
        prompt = """
Проведи анализ криптовалютного рынка и выдай мне 3 лучших точки входа прямо сейчас.

Требования:
1. Найди ТОП 3 возможности с confluence ≥ 8.0/10
2. Вероятность успеха ≥ 70%
3. R:R минимум 1:2

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
            "reasoning": "Детальное объяснение"
        }
    ]
}
"""
        
        system_instructions = """
Ты - профессиональный AI торговый аналитик.
Твоя задача - находить моменты НЕИЗБЕЖНОГО роста с максимальной вероятностью успеха.
Всегда отвечай в формате JSON как указано в запросе.
"""
        
        print("📤 Отправляю запрос на анализ рынка...")
        print("⏳ Ожидание ответа...")
        
        result = await client.generate(
            prompt=prompt,
            system_prompt=system_instructions,
            temperature=0.3,
            max_tokens=2000
        )
        
        if result.get("success"):
            print("\n✅ Анализ успешен!")
            content = result.get("content", "")
            print(f"\n📥 Длина ответа: {len(content)} символов")
            print(f"\n📝 Ответ (первые 500 символов):")
            print("-" * 60)
            print(content[:500])
            print("-" * 60)
            
            # Попытка распарсить JSON
            import json
            try:
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
                if "top_opportunities" in parsed:
                    print(f"   Найдено возможностей: {len(parsed['top_opportunities'])}")
                    for i, opp in enumerate(parsed['top_opportunities'][:3], 1):
                        print(f"\n   {i}. {opp.get('symbol', 'N/A')}")
                        print(f"      Entry: ${opp.get('entry_price', 0)}")
                        print(f"      Confluence: {opp.get('confluence_score', 0)}/10")
                
                return True
            except json.JSONDecodeError:
                print("\n⚠️ Не удалось распарсить JSON, но ответ получен")
                return True
        else:
            print(f"\n❌ Ошибка: {result.get('error', 'Unknown')}")
            return False
            
    except Exception as e:
        print(f"\n❌ Исключение: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Запуск тестов"""
    print("\n" + "🔍" * 30)
    print("УПРОЩЁННОЕ ТЕСТИРОВАНИЕ QWEN API")
    print("🔍" * 30)
    
    results = []
    
    # Тест 1: Простой запрос
    try:
        result1 = await test_simple()
        results.append(("Простой запрос", result1))
    except Exception as e:
        print(f"❌ Тест 1 провален: {e}")
        results.append(("Простой запрос", False))
    
    # Тест 2: Анализ рынка (только если первый прошёл)
    if results[0][1]:
        try:
            result2 = await test_market_analysis()
            results.append(("Анализ рынка", result2))
        except Exception as e:
            print(f"❌ Тест 2 провален: {e}")
            results.append(("Анализ рынка", False))
    else:
        print("\n⚠️ Пропускаю тест анализа рынка (первый тест не прошёл)")
        results.append(("Анализ рынка", False))
    
    # Итоги
    print("\n" + "=" * 60)
    print("ИТОГИ")
    print("=" * 60)
    
    for test_name, result in results:
        status = "✅ ПРОШЁЛ" if result else "❌ ПРОВАЛЕН"
        print(f"{status}: {test_name}")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    print(f"\n📊 Результат: {passed}/{total} тестов прошли")
    
    if passed == total:
        print("🎉 Все тесты прошли успешно!")
        return 0
    else:
        print("\n⚠️ Проблемы обнаружены.")
        print("📋 Проверьте:")
        print("   1. API ключ от OpenRouter активен (формат: sk-or-v1-...)")
        print("   2. Баланс на OpenRouter > 0 (https://openrouter.ai/credits)")
        print("   3. Модель qwen/qwen-turbo доступна")
        print("   4. Инструкция: OPENROUTER_SETUP_GUIDE.md")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

