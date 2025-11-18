#!/usr/bin/env python3
"""
Тест всех 29 инструментов MCP сервера через реальные вызовы
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

# Добавляем путь для импорта mcp
sys.path.insert(0, str(Path(__file__).parent))

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    from mcp.types import Tool
except ImportError as e:
    print(f"❌ MCP SDK не установлен или неправильный импорт: {e}")
    print("Установите: pip install mcp")
    print("Или проверьте версию: pip install --upgrade mcp")
    sys.exit(1)

try:
    from loguru import logger
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>",
        level="INFO"
    )
except ImportError:
    # Fallback к стандартному logging
    import logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)-8s | %(message)s')
    logger = logging.getLogger(__name__)


# Путь к серверу
SERVER_PATH = Path(__file__).parent / "mcp_server" / "full_server.py"
VENV_PYTHON = Path(__file__).parent / "venv" / "bin" / "python"


class MCPTester:
    """Тестер всех MCP инструментов"""
    
    def __init__(self):
        self.results: Dict[str, Dict[str, Any]] = {}
        self.total_tools = 29
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        
    async def test_tool(
        self,
        session: ClientSession,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Тест одного инструмента"""
        
        logger.info(f"🧪 Тестирую: {tool_name}")
        
        try:
            # Вызываем инструмент
            result = await session.call_tool(tool_name, arguments)
            
            # Парсим результат
            if result and result.content:
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
            
            # Проверяем успешность
            success = True
            error = None
            
            if isinstance(parsed, dict):
                if parsed.get("success") == False:
                    success = False
                    error = parsed.get("error", "Unknown error")
                elif "error" in parsed and parsed["error"]:
                    success = False
                    error = parsed["error"]
            
            return {
                "success": success,
                "result": parsed,
                "error": error,
                "tool_name": tool_name
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка при вызове {tool_name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "tool_name": tool_name,
                "result": None
            }
    
    async def run_all_tests(self):
        """Запуск всех тестов"""
        
        logger.info("=" * 70)
        logger.info("🚀 ТЕСТИРОВАНИЕ ВСЕХ 29 ИНСТРУМЕНТОВ MCP СЕРВЕРА")
        logger.info("=" * 70)
        
        # Проверяем наличие Python
        if not VENV_PYTHON.exists():
            logger.error(f"❌ Python не найден: {VENV_PYTHON}")
            logger.info("Используем системный Python")
            python_cmd = sys.executable
        else:
            python_cmd = str(VENV_PYTHON)
        
        # Параметры сервера
        server_params = StdioServerParameters(
            command=python_cmd,
            args=[str(SERVER_PATH)]
        )
        
        logger.info(f"📡 Подключение к серверу: {python_cmd} {SERVER_PATH}")
        
        try:
            # Подключаемся к серверу
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    # Инициализация
                    await session.initialize()
                    
                    # Получаем список инструментов
                    tools_response = await session.list_tools()
                    tools = tools_response.tools
                    
                    logger.info(f"✅ Подключено! Доступно инструментов: {len(tools)}")
                    
                    # Определяем все 29 инструментов с тестовыми параметрами
                    test_cases = self.get_test_cases()
                    
                    logger.info(f"\n📋 Буду протестировано: {len(test_cases)} инструментов\n")
                    
                    # Тестируем каждый инструмент
                    for i, (tool_name, args) in enumerate(test_cases.items(), 1):
                        logger.info(f"\n[{i}/{len(test_cases)}] {'='*60}")
                        
                        result = await self.test_tool(session, tool_name, args)
                        self.results[tool_name] = result
                        
                        if result["success"]:
                            self.passed += 1
                            logger.success(f"✅ {tool_name}: УСПЕХ")
                        else:
                            self.failed += 1
                            logger.error(f"❌ {tool_name}: ОШИБКА - {result.get('error', 'Unknown')}")
                    
                    # Итоги
                    self.print_summary()
                    
        except Exception as e:
            logger.error(f"❌ Критическая ошибка: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        return self.failed == 0
    
    def get_test_cases(self) -> Dict[str, Dict[str, Any]]:
        """Определение тестовых случаев для всех 29 инструментов"""
        
        return {
            # Market Data (3)
            "get_market_overview": {"market_type": "both"},
            "get_all_tickers": {"market_type": "spot", "sort_by": "volume"},
            "get_asset_price": {"symbol": "BTCUSDT"},
            
            # Technical Analysis (8)
            "analyze_asset": {
                "symbol": "BTCUSDT",
                "timeframes": ["1h", "4h"],
                "include_patterns": True
            },
            "calculate_indicators": {
                "symbol": "BTCUSDT",
                "indicators": ["RSI", "MACD"]
            },
            "detect_patterns": {
                "symbol": "BTCUSDT",
                "timeframe": "1h",
                "pattern_types": ["candlestick"]
            },
            "find_support_resistance": {
                "symbol": "BTCUSDT",
                "timeframe": "1h",
                "lookback_periods": 50
            },
            "get_btc_correlation": {
                "symbol": "ETHUSDT",
                "period": 24,
                "timeframe": "1h"
            },
            "get_funding_rate": {"symbol": "BTCUSDT"},
            "get_open_interest": {
                "symbol": "BTCUSDT",
                "category": "linear"
            },
            "check_tf_alignment": {
                "symbol": "BTCUSDT",
                "timeframes": ["1h", "4h", "1d"]
            },
            
            # Market Scanning (5)
            "scan_market": {
                "criteria": {
                    "market_type": "spot",
                    "min_volume_24h": 1000000
                },
                "limit": 5
            },
            "find_oversold_assets": {
                "market_type": "spot",
                "min_volume_24h": 1000000
            },
            "find_overbought_assets": {
                "market_type": "spot",
                "min_volume_24h": 1000000
            },
            "find_breakout_opportunities": {
                "market_type": "spot",
                "min_volume_24h": 1000000
            },
            "find_trend_reversals": {
                "market_type": "spot",
                "min_volume_24h": 1000000
            },
            
            # Entry Validation (2)
            "check_liquidity": {"symbol": "BTCUSDT"},
            "validate_entry": {
                "symbol": "BTCUSDT",
                "side": "long",
                "entry_price": 50000,
                "stop_loss": 49000,
                "take_profit": 52000,
                "risk_pct": 0.01
            },
            
            # Account (3)
            "get_account_info": {},
            "get_open_positions": {},
            "get_order_history": {"category": "spot", "limit": "10"},
            
            # Trading Operations (4) - только проверка структуры, не реальные ордера!
            "place_order": {
                "symbol": "BTCUSDT",
                "side": "Buy",
                "order_type": "Market",
                "quantity": 0.001,
                "category": "spot"
            },
            "close_position": {
                "symbol": "BTCUSDT",
                "category": "linear"
            },
            "modify_position": {
                "symbol": "BTCUSDT",
                "stop_loss": 49000,
                "take_profit": 52000,
                "category": "linear"
            },
            "cancel_order": {
                "order_id": "test_order_id",
                "symbol": "BTCUSDT",
                "category": "spot"
            },
            
            # Monitoring (2)
            "start_position_monitoring": {
                "auto_actions": {
                    "move_to_breakeven_at": 1.0,
                    "enable_trailing_at": 2.0
                }
            },
            "stop_position_monitoring": {},
            
            # Auto-Actions (2)
            "move_to_breakeven": {
                "symbol": "BTCUSDT",
                "entry_price": 50000,
                "category": "linear"
            },
            "activate_trailing_stop": {
                "symbol": "BTCUSDT",
                "trailing_distance": 1.0,
                "category": "linear"
            }
        }
    
    def print_summary(self):
        """Вывод итогового отчета"""
        
        logger.info("\n" + "=" * 70)
        logger.info("📊 ИТОГОВЫЙ ОТЧЕТ")
        logger.info("=" * 70)
        
        logger.info(f"\n✅ Успешно: {self.passed}/{self.total_tools}")
        logger.info(f"❌ Ошибки: {self.failed}/{self.total_tools}")
        logger.info(f"⏭️  Пропущено: {self.skipped}/{self.total_tools}")
        
        success_rate = (self.passed / self.total_tools * 100) if self.total_tools > 0 else 0
        logger.info(f"\n📈 Успешность: {success_rate:.1f}%")
        
        # Детали по ошибкам
        if self.failed > 0:
            logger.info("\n❌ ИНСТРУМЕНТЫ С ОШИБКАМИ:")
            for tool_name, result in self.results.items():
                if not result.get("success"):
                    error = result.get("error", "Unknown")
                    logger.error(f"  - {tool_name}: {error}")
        
        # Сохраняем отчет в файл
        report_file = Path(__file__).parent / f"mcp_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "total_tools": self.total_tools,
                "passed": self.passed,
                "failed": self.failed,
                "skipped": self.skipped,
                "success_rate": success_rate,
                "results": self.results
            }, f, indent=2, ensure_ascii=False)
        
        logger.info(f"\n💾 Отчет сохранен: {report_file}")
        
        logger.info("\n" + "=" * 70)
        if self.failed == 0:
            logger.success("🎉 ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!")
        else:
            logger.warning(f"⚠️  Есть ошибки в {self.failed} инструментах")
        logger.info("=" * 70)


async def main():
    """Главная функция"""
    
    tester = MCPTester()
    success = await tester.run_all_tests()
    
    return 0 if success else 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("\n⚠️  Тестирование прервано пользователем")
        sys.exit(130)
    except Exception as e:
        logger.error(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

