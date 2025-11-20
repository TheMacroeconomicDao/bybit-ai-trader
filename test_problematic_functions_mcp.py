#!/usr/bin/env python3
"""
Тестирование проблемных MCP функций через прямой вызов
"""
import asyncio
import json
import sys
from pathlib import Path

# Добавляем путь к mcp_server
sys.path.insert(0, str(Path(__file__).parent / "mcp_server"))

from mcp.server.stdio import stdio_server
from mcp.client.stdio import stdio_client
from mcp import ClientSession, StdioServerParameters
from mcp.types import Tool

async def test_mcp_tools():
    """Тестирование проблемных MCP инструментов"""
    
    print("=" * 70)
    print("🧪 ТЕСТИРОВАНИЕ ПРОБЛЕМНЫХ MCP ФУНКЦИЙ")
    print("=" * 70)
    print()
    
    # Параметры сервера
    server_params = StdioServerParameters(
        command="python3",
        args=["mcp_server/full_server.py"],
        env=None
    )
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Инициализация
                await session.initialize()
                
                # Получаем список инструментов
                tools = await session.list_tools()
                print(f"✅ Подключено к MCP серверу")
                print(f"   Доступно инструментов: {len(tools.tools)}")
                print()
                
                # Проблемные функции для тестирования
                problematic_tools = [
                    ("get_asset_price", {"symbol": "BTC/USDT"}),
                    ("analyze_asset", {"symbol": "BTC/USDT", "timeframes": ["1h"], "include_patterns": False}),
                    ("get_btc_correlation", {"symbol": "ETH/USDT", "period": 24, "timeframe": "1h"}),
                ]
                
                results = {}
                
                for tool_name, args in problematic_tools:
                    print(f"🧪 Тест: {tool_name}")
                    print("-" * 70)
                    try:
                        result = await session.call_tool(tool_name, args)
                        
                        # Парсим результат
                        if result.content:
                            content = result.content[0] if isinstance(result.content, list) else result.content
                            if hasattr(content, 'text'):
                                try:
                                    parsed = json.loads(content.text)
                                except:
                                    parsed = {"raw": content.text}
                            else:
                                parsed = {"raw": str(content)}
                        else:
                            parsed = {"raw": "No content"}
                        
                        # Проверяем на ошибки
                        if isinstance(parsed, dict):
                            if parsed.get("success") == False:
                                error = parsed.get("error", "Unknown error")
                                if "retCode" in error or "KeyError" in error:
                                    print(f"   ❌ ОШИБКА (KeyError/retCode): {error[:150]}")
                                    results[tool_name] = "FAILED"
                                else:
                                    print(f"   ⚠️ Ошибка: {error[:150]}")
                                    results[tool_name] = "ERROR"
                            elif "error" in parsed and parsed["error"]:
                                error = parsed["error"]
                                if "retCode" in error or "KeyError" in error:
                                    print(f"   ❌ ОШИБКА (KeyError/retCode): {error[:150]}")
                                    results[tool_name] = "FAILED"
                                else:
                                    print(f"   ⚠️ Ошибка: {error[:150]}")
                                    results[tool_name] = "ERROR"
                            else:
                                print(f"   ✅ УСПЕХ: функция выполнилась без KeyError")
                                results[tool_name] = "SUCCESS"
                        else:
                            print(f"   ✅ УСПЕХ: получен результат")
                            results[tool_name] = "SUCCESS"
                            
                    except Exception as e:
                        error_str = str(e)
                        if "retCode" in error_str or "KeyError" in error_str:
                            print(f"   ❌ ОШИБКА (KeyError/retCode): {error_str[:150]}")
                            results[tool_name] = "FAILED"
                        else:
                            print(f"   ❌ ОШИБКА: {error_str[:150]}")
                            results[tool_name] = "ERROR"
                    
                    print()
                
                # Итоги
                print("=" * 70)
                print("📊 ИТОГИ ТЕСТИРОВАНИЯ")
                print("=" * 70)
                for tool_name, status in results.items():
                    if status == "SUCCESS":
                        print(f"   ✅ {tool_name}: РАБОТАЕТ")
                    elif status == "FAILED":
                        print(f"   ❌ {tool_name}: KeyError/retCode ОШИБКА")
                    else:
                        print(f"   ⚠️ {tool_name}: ДРУГАЯ ОШИБКА")
                print()
                
                success_count = sum(1 for s in results.values() if s == "SUCCESS")
                total_count = len(results)
                print(f"✅ Успешно: {success_count}/{total_count}")
                
    except Exception as e:
        print(f"❌ Ошибка подключения к MCP серверу: {e}")
        print("   Убедитесь, что сервер запущен")

if __name__ == "__main__":
    asyncio.run(test_mcp_tools())

