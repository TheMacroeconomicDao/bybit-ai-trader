#!/usr/bin/env python3
"""
Test script for Autonomous Agent MCP Server
Тестирование всех компонентов autonomous agent
"""

import asyncio
import sys
import os
from pathlib import Path

# Добавляем путь к проекту
sys.path.insert(0, str(Path(__file__).parent.parent))

from autonomous_agent.autonomous_analyzer import AutonomousAnalyzer
from autonomous_agent.telegram_formatter import TelegramFormatter
from mcp_server.signal_tracker import SignalTracker


async def test_autonomous_analyzer():
    """Тест AutonomousAnalyzer"""
    print("=" * 60)
    print("TEST 1: Autonomous Analyzer Initialization")
    print("=" * 60)
    
    # Проверка переменных окружения
    qwen_key = os.getenv("QWEN_API_KEY")
    bybit_key = os.getenv("BYBIT_API_KEY")
    bybit_secret = os.getenv("BYBIT_API_SECRET")
    
    if not all([qwen_key, bybit_key, bybit_secret]):
        print("❌ Missing required environment variables:")
        print(f"   QWEN_API_KEY: {'✅' if qwen_key else '❌'}")
        print(f"   BYBIT_API_KEY: {'✅' if bybit_key else '❌'}")
        print(f"   BYBIT_API_SECRET: {'✅' if bybit_secret else '❌'}")
        return False
    
    print("✅ Environment variables check passed")
    
    try:
        # Инициализация signal tracker
        signal_tracker = SignalTracker()
        print("✅ Signal Tracker initialized")
        
        # Инициализация analyzer
        analyzer = AutonomousAnalyzer(
            qwen_api_key=qwen_key,
            bybit_api_key=bybit_key,
            bybit_api_secret=bybit_secret,
            qwen_model=os.getenv("QWEN_MODEL", "qwen/qwen-turbo"),
            testnet=os.getenv("BYBIT_TESTNET", "false").lower() == "true",
            signal_tracker=signal_tracker
        )
        print("✅ Autonomous Analyzer initialized")
        
        # Закрытие соединений
        await analyzer.close()
        print("✅ Analyzer closed successfully")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_telegram_formatter():
    """Тест TelegramFormatter"""
    print("\n" + "=" * 60)
    print("TEST 2: Telegram Formatter")
    print("=" * 60)
    
    try:
        formatter = TelegramFormatter()
        print("✅ TelegramFormatter initialized")
        
        # Тестовые данные
        test_result = {
            "success": True,
            "timestamp": "2025-01-20T12:00:00",
            "top_3_longs": [
                {
                    "symbol": "BTCUSDT",
                    "side": "long",
                    "entry_price": 50000,
                    "stop_loss": 49000,
                    "take_profit": 52000,
                    "confluence_score": 8.5,
                    "probability": 0.75,
                    "risk_reward": 2.0,
                    "reasoning": "Test reasoning"
                }
            ],
            "top_3_shorts": []
        }
        
        formatted = formatter.format_top_opportunities(test_result)
        print("✅ Formatting successful")
        print(f"   Formatted message length: {len(formatted)} characters")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config_manager():
    """Тест ConfigManager"""
    print("\n" + "=" * 60)
    print("TEST 3: Config Manager")
    print("=" * 60)
    
    try:
        from config.config_manager import get_config, ConfigManager
        
        # Тест загрузки конфигурации
        config = get_config()
        print("✅ Config loaded successfully")
        print(f"   Qwen Model: {config.qwen_model}")
        print(f"   Testnet: {config.bybit_testnet}")
        print(f"   Min Confluence: {config.min_confluence}")
        print(f"   Min Probability: {config.min_probability}")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_file_structure():
    """Тест структуры файлов"""
    print("\n" + "=" * 60)
    print("TEST 4: File Structure")
    print("=" * 60)
    
    base_path = Path(__file__).parent.parent
    required_files = [
        "mcp_server/autonomous_agent_server.py",
        "autonomous_agent/autonomous_analyzer.py",
        "autonomous_agent/telegram_formatter.py",
        "config/config_manager.py",
        "scripts/run_daily_analysis.sh",
        "scripts/setup_daily_cron.sh"
    ]
    
    all_exist = True
    for file_path in required_files:
        full_path = base_path / file_path
        exists = full_path.exists()
        status = "✅" if exists else "❌"
        print(f"   {status} {file_path}")
        if not exists:
            all_exist = False
    
    return all_exist


async def main():
    """Запуск всех тестов"""
    print("\n" + "=" * 60)
    print("AUTONOMOUS AGENT TEST SUITE")
    print("=" * 60)
    print()
    
    results = []
    
    # Тест 1: Autonomous Analyzer
    result1 = await test_autonomous_analyzer()
    results.append(("Autonomous Analyzer", result1))
    
    # Тест 2: Telegram Formatter
    result2 = test_telegram_formatter()
    results.append(("Telegram Formatter", result2))
    
    # Тест 3: Config Manager
    result3 = test_config_manager()
    results.append(("Config Manager", result3))
    
    # Тест 4: File Structure
    result4 = test_file_structure()
    results.append(("File Structure", result4))
    
    # Итоги
    print("\n" + "=" * 60)
    print("TEST RESULTS")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status}: {name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Total: {len(results)} tests")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print("=" * 60)
    
    if failed == 0:
        print("\n✅ All tests passed!")
        return 0
    else:
        print(f"\n❌ {failed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

