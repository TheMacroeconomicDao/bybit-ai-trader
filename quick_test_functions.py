#!/usr/bin/env python3
"""
Быстрый тест проблемных функций
Проверяет что исправления работают
"""
import asyncio
import sys
from pathlib import Path

# Загружаем .env
from dotenv import load_dotenv
load_dotenv()

sys.path.insert(0, str(Path(__file__).parent / "mcp_server"))

print("=" * 70)
print("🧪 БЫСТРЫЙ ТЕСТ ПРОБЛЕМНЫХ ФУНКЦИЙ")
print("=" * 70)
print()

# Проверяем что переменные загружены
import os
api_key = os.getenv('BYBIT_API_KEY')
api_secret = os.getenv('BYBIT_API_SECRET')

if not api_key or not api_secret:
    print("❌ API ключи не найдены в .env")
    print("   Проверьте что .env файл существует и содержит BYBIT_API_KEY и BYBIT_API_SECRET")
    sys.exit(1)

print(f"✅ API ключи загружены из .env")
print(f"   API Key: {api_key[:10]}...{api_key[-4:]}")
print(f"   API Secret: {'*' * 10}...{api_secret[-4:]}")
print()

# Импортируем функции для тестирования парсинга ошибок
print("🔍 Тест 1: Проверка функции parse_ccxt_error")
print("-" * 70)
try:
    from bybit_client import parse_ccxt_error
    
    # Тестируем парсинг ошибки CCXT
    test_error = Exception('bybit {"retCode":10003,"retMsg":"API key is invalid.","result":{},"retExtInfo":{},"time":1763660636556}')
    parsed = parse_ccxt_error(test_error)
    
    if parsed["parsed"] and parsed["retCode"] == 10003:
        print(f"   ✅ УСПЕХ: parse_ccxt_error правильно парсит ошибки CCXT")
        print(f"   ✅ retCode: {parsed['retCode']}")
        print(f"   ✅ retMsg: {parsed['retMsg']}")
    else:
        print(f"   ❌ ОШИБКА: parse_ccxt_error не работает правильно")
        print(f"   Результат: {parsed}")
except Exception as e:
    print(f"   ❌ ОШИБКА при импорте/тестировании: {e}")

print()
print("=" * 70)
print("✅ ТЕСТ ЗАВЕРШЕН")
print("=" * 70)
print()
print("📋 Следующие шаги:")
print("   1. Перезапустите MCP сервер для применения изменений")
print("   2. Проверьте логи сервера - должны быть:")
print("      ✅ Loaded .env file from ...")
print("      ✅ Found credentials in ENVIRONMENT VARIABLES")
print("   3. Вызовите проблемные функции через MCP клиент")

