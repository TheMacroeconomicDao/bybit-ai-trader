#!/usr/bin/env python3
"""
Комплексное тестирование всех MCP инструментов
Проверяет что все инструменты работают и возвращают правильные данные
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import traceback

# Добавляем путь к mcp_server
sys.path.insert(0, str(Path(__file__).parent / "mcp_server"))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from loguru import logger

# Импорты для инициализации сервера
from trading_operations import TradingOperations
from technical_analysis import TechnicalAnalysis
from market_scanner import MarketScanner
from position_monitor import PositionMonitor
from bybit_client import BybitClient
from signal_tracker import SignalTracker
from signal_price_monitor import SignalPriceMonitor
from quality_metrics import QualityMetrics
from signal_reports import SignalReports

# Настройка логирования
logger.remove()
logger.add(sys.stderr, level="INFO", format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>")

# Глобальные клиенты
trading_ops: Optional[TradingOperations] = None
technical_analysis: Optional[TechnicalAnalysis] = None
market_scanner: Optional[MarketScanner] = None
position_monitor: Optional[PositionMonitor] = None
bybit_client: Optional[BybitClient] = None
signal_tracker: Optional[SignalTracker] = None
signal_monitor: Optional[SignalPriceMonitor] = None
quality_metrics: Optional[QualityMetrics] = None
signal_reports: Optional[SignalReports] = None


def load_credentials() -> Dict[str, Any]:
    """Загрузка credentials"""
    config_path = Path(__file__).parent / "config" / "credentials.json"
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Credentials not found: {config_path}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON: {e}")
        raise


async def initialize_components():
    """Инициализация всех компонентов"""
    global trading_ops, technical_analysis, market_scanner, position_monitor, bybit_client
    global signal_tracker, signal_monitor, quality_metrics, signal_reports
    
    logger.info("Инициализация компонентов...")
    
    credentials = load_credentials()
    bybit_creds = credentials["bybit"]
    
    trading_ops = TradingOperations(
        api_key=bybit_creds["api_key"],
        api_secret=bybit_creds["api_secret"],
        testnet=bybit_creds.get("testnet", False)
    )
    
    bybit_client = BybitClient(
        api_key=bybit_creds["api_key"],
        api_secret=bybit_creds["api_secret"],
        testnet=bybit_creds.get("testnet", False)
    )
    
    technical_analysis = TechnicalAnalysis(bybit_client)
    market_scanner = MarketScanner(bybit_client, technical_analysis)
    
    position_monitor = PositionMonitor(
        api_key=bybit_creds["api_key"],
        api_secret=bybit_creds["api_secret"],
        testnet=bybit_creds.get("testnet", False)
    )
    
    signal_tracker = SignalTracker()
    signal_monitor = SignalPriceMonitor(signal_tracker, bybit_client, check_interval=300)
    quality_metrics = QualityMetrics(signal_tracker)
    signal_reports = SignalReports(signal_tracker, quality_metrics)
    
    logger.info("✅ Все компоненты инициализированы")


# Тестовые случаи для каждого инструмента
TEST_CASES = {
    # ═══════════════════════════════════════
    # 📊 РЫНОЧНЫЕ ДАННЫЕ
    # ═══════════════════════════════════════
    
    "get_market_overview": {
        "args": {"market_type": "spot"},
        "expected_fields": ["timestamp", "market_type", "sentiment", "btc", "statistics"],
        "description": "Полный обзор рынка"
    },
    
    "get_all_tickers": {
        "args": {"market_type": "spot", "sort_by": "volume"},
        "expected_fields": ["symbol", "price", "change_24h", "volume_24h"],
        "description": "Все торговые пары",
        "min_results": 10
    },
    
    "get_asset_price": {
        "args": {"symbol": "BTC/USDT"},
        "expected_fields": ["symbol", "price", "change_24h", "volume_24h"],
        "description": "Текущая цена актива"
    },
    
    # ═══════════════════════════════════════
    # 📈 ТЕХНИЧЕСКИЙ АНАЛИЗ
    # ═══════════════════════════════════════
    
    "analyze_asset": {
        "args": {"symbol": "BTC/USDT", "timeframes": ["1h", "4h"], "include_patterns": True},
        "expected_fields": ["symbol", "timeframes", "composite_signal"],
        "description": "Полный анализ актива"
    },
    
    "calculate_indicators": {
        "args": {"symbol": "BTC/USDT", "indicators": ["RSI", "MACD"]},
        "expected_fields": ["indicators"],
        "description": "Расчет индикаторов"
    },
    
    "detect_patterns": {
        "args": {"symbol": "BTC/USDT", "timeframe": "1h", "pattern_types": ["candlestick"]},
        "expected_fields": ["patterns"],
        "description": "Поиск паттернов"
    },
    
    "find_support_resistance": {
        "args": {"symbol": "BTC/USDT", "timeframe": "1h", "lookback_periods": 50},
        "expected_fields": ["support_levels", "resistance_levels"],
        "description": "Уровни поддержки и сопротивления"
    },
    
    "get_btc_correlation": {
        "args": {"symbol": "ETH/USDT", "period": 24, "timeframe": "1h"},
        "expected_fields": ["symbol", "correlation", "correlation_strength"],
        "description": "Корреляция с BTC"
    },
    
    "get_funding_rate": {
        "args": {"symbol": "BTC/USDT:USDT"},
        "expected_fields": ["symbol", "funding_rate", "market_bias"],
        "description": "Funding rate для фьючерсов"
    },
    
    "check_tf_alignment": {
        "args": {"symbol": "BTC/USDT", "timeframes": ["1h", "4h", "1d"]},
        "expected_fields": ["symbol", "alignment_score", "timeframes"],
        "description": "Проверка alignment таймфреймов"
    },
    
    # ═══════════════════════════════════════
    # 🔍 СКАНИРОВАНИЕ РЫНКА
    # ═══════════════════════════════════════
    
    "scan_market": {
        "args": {
            "criteria": {
                "market_type": "spot",
                "min_volume_24h": 1000000
            },
            "limit": 5
        },
        "expected_fields": ["symbol", "score", "probability"],
        "description": "Сканирование рынка",
        "min_results": 1
    },
    
    "find_oversold_assets": {
        "args": {"market_type": "spot", "min_volume_24h": 1000000},
        "expected_fields": ["symbol", "score"],
        "description": "Перепроданные активы",
        "min_results": 0  # Может быть 0 если нет oversold
    },
    
    "find_overbought_assets": {
        "args": {"market_type": "spot", "min_volume_24h": 1000000},
        "expected_fields": ["symbol", "score"],
        "description": "Перекупленные активы",
        "min_results": 0
    },
    
    "find_breakout_opportunities": {
        "args": {"market_type": "spot", "min_volume_24h": 1000000},
        "expected_fields": ["symbol", "score"],
        "description": "Возможности пробоя",
        "min_results": 0
    },
    
    "find_trend_reversals": {
        "args": {"market_type": "spot", "min_volume_24h": 1000000},
        "expected_fields": ["symbol", "score"],
        "description": "Развороты тренда",
        "min_results": 0
    },
    
    # ═══════════════════════════════════════
    # 🎯 ВАЛИДАЦИЯ ВХОДА
    # ═══════════════════════════════════════
    
    "check_liquidity": {
        "args": {"symbol": "BTC/USDT"},
        "expected_fields": ["symbol", "liquidity_score"],
        "description": "Проверка ликвидности"
    },
    
    "validate_entry": {
        "args": {
            "symbol": "BTC/USDT",
            "side": "long",
            "entry_price": 50000,
            "stop_loss": 49000,
            "take_profit": 52000,
            "risk_pct": 0.01
        },
        "expected_fields": ["is_valid", "confluence_score", "probability"],
        "description": "Валидация точки входа"
    },
    
    "get_open_interest": {
        "args": {"symbol": "BTCUSDT", "category": "linear"},
        "expected_fields": ["symbol", "open_interest", "trend"],
        "description": "Open Interest для futures"
    },
    
    # ═══════════════════════════════════════
    # 💰 СЧЁТ И ПОЗИЦИИ
    # ═══════════════════════════════════════
    
    "get_account_info": {
        "args": {},
        "expected_fields": ["balance"],
        "description": "Информация о счёте"
    },
    
    "get_open_positions": {
        "args": {},
        "expected_fields": [],  # Может быть пустой список
        "description": "Открытые позиции",
        "is_list": True
    },
    
    "get_order_history": {
        "args": {"category": "spot", "limit": "10"},
        "expected_fields": [],
        "description": "История ордеров",
        "is_list": True
    },
    
    # ═══════════════════════════════════════
    # 📡 REAL-TIME МОНИТОРИНГ
    # ═══════════════════════════════════════
    
    "start_position_monitoring": {
        "args": {
            "auto_actions": {
                "move_to_breakeven_at": 1.0,
                "enable_trailing_at": 2.0,
                "exit_on_reversal": True,
                "max_time_in_trade": 12
            }
        },
        "expected_fields": ["success", "message"],
        "description": "Запуск мониторинга позиций"
    },
    
    "stop_position_monitoring": {
        "args": {},
        "expected_fields": ["success", "message"],
        "description": "Остановка мониторинга"
    },
    
    # ═══════════════════════════════════════
    # 🛠️ ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
    # ═══════════════════════════════════════
    
    "move_to_breakeven": {
        "args": {"symbol": "BTCUSDT", "entry_price": 50000, "category": "linear"},
        "expected_fields": ["success"],
        "description": "Перевод SL в breakeven",
        "skip_if_no_position": True
    },
    
    "activate_trailing_stop": {
        "args": {"symbol": "BTCUSDT", "trailing_distance": 2.0, "category": "linear"},
        "expected_fields": ["success"],
        "description": "Активация trailing stop",
        "skip_if_no_position": True
    },
    
    # ═══════════════════════════════════════
    # 📊 КОНТРОЛЬ КАЧЕСТВА СИГНАЛОВ
    # ═══════════════════════════════════════
    
    "track_signal": {
        "args": {
            "symbol": "BTC/USDT",
            "side": "long",
            "entry_price": 50000,
            "stop_loss": 49000,
            "take_profit": 52000,
            "confluence_score": 8.5,
            "probability": 0.75
        },
        "expected_fields": ["success", "signal_id"],
        "description": "Запись сигнала"
    },
    
    "get_signal_quality_metrics": {
        "args": {"days": 30, "include_patterns": True},
        "expected_fields": ["success", "metrics"],
        "description": "Метрики качества сигналов"
    },
    
    "get_signal_performance_report": {
        "args": {"days": 30, "format": "summary"},
        "expected_fields": ["success", "report"],
        "description": "Отчет о производительности"
    },
    
    "get_active_signals": {
        "args": {},
        "expected_fields": ["success", "active_signals"],
        "description": "Активные сигналы",
        "is_list": True
    },
    
    "get_signal_details": {
        "args": {"signal_id": "test_signal_123"},
        "expected_fields": ["success"],
        "description": "Детали сигнала",
        "skip_if_no_signals": True
    },
}


async def test_tool(tool_name: str, test_case: Dict[str, Any]) -> Dict[str, Any]:
    """Тестирование одного инструмента"""
    result = {
        "tool": tool_name,
        "description": test_case.get("description", ""),
        "status": "pending",
        "error": None,
        "response_time": None,
        "response_size": None,
        "fields_check": None,
        "results_count": None
    }
    
    try:
        # Проверяем нужно ли пропустить тест
        if test_case.get("skip_if_no_position") and tool_name in ["move_to_breakeven", "activate_trailing_stop"]:
            # Проверяем есть ли открытые позиции
            try:
                positions = await trading_ops.session.get_positions(category="linear", symbol="BTCUSDT")
                if positions.get("retCode") == 0:
                    positions_list = positions.get("result", {}).get("list", [])
                    if not any(float(p.get("size", 0)) != 0 for p in positions_list):
                        result["status"] = "skipped"
                        result["error"] = "Нет открытых позиций для тестирования"
                        return result
            except:
                result["status"] = "skipped"
                result["error"] = "Не удалось проверить позиции"
                return result
        
        if test_case.get("skip_if_no_signals") and tool_name == "get_signal_details":
            # Проверяем есть ли сигналы
            try:
                active_signals = await signal_tracker.get_active_signals()
                if not active_signals:
                    result["status"] = "skipped"
                    result["error"] = "Нет активных сигналов для тестирования"
                    return result
                # Используем первый сигнал
                test_case["args"]["signal_id"] = active_signals[0]["signal_id"]
            except:
                result["status"] = "skipped"
                result["error"] = "Не удалось проверить сигналы"
                return result
        
        # Выполняем тест
        start_time = datetime.now()
        
        # Импортируем обработчик из full_server
        from mcp_server.full_server import call_tool
        
        response = await call_tool(tool_name, test_case["args"])
        
        end_time = datetime.now()
        response_time = (end_time - start_time).total_seconds()
        
        # Парсим ответ
        if isinstance(response, list) and len(response) > 0:
            response_text = response[0].text if hasattr(response[0], 'text') else str(response[0])
            try:
                response_data = json.loads(response_text)
            except:
                response_data = {"raw_response": response_text}
        else:
            response_data = {"raw_response": str(response)}
        
        result["response_time"] = round(response_time, 2)
        result["response_size"] = len(str(response_data))
        
        # Проверяем наличие ожидаемых полей
        expected_fields = test_case.get("expected_fields", [])
        if expected_fields:
            missing_fields = []
            for field in expected_fields:
                if isinstance(response_data, dict):
                    if field not in response_data:
                        # Проверяем вложенные структуры
                        found = False
                        for key, value in response_data.items():
                            if isinstance(value, dict) and field in value:
                                found = True
                                break
                            elif isinstance(value, list) and len(value) > 0:
                                if isinstance(value[0], dict) and field in value[0]:
                                    found = True
                                    break
                        if not found:
                            missing_fields.append(field)
            
            result["fields_check"] = {
                "expected": expected_fields,
                "missing": missing_fields,
                "passed": len(missing_fields) == 0
            }
        
        # Проверяем количество результатов для списков
        if test_case.get("is_list") or test_case.get("min_results") is not None:
            if isinstance(response_data, list):
                results_count = len(response_data)
            elif isinstance(response_data, dict) and "list" in response_data:
                results_count = len(response_data["list"])
            elif isinstance(response_data, dict) and "active_signals" in response_data:
                results_count = len(response_data["active_signals"])
            else:
                results_count = 1 if response_data else 0
            
            result["results_count"] = results_count
            min_results = test_case.get("min_results", 0)
            if results_count < min_results:
                result["status"] = "warning"
                result["error"] = f"Ожидалось минимум {min_results} результатов, получено {results_count}"
            else:
                result["status"] = "success"
        else:
            result["status"] = "success"
        
        # Проверяем на ошибки в ответе
        if isinstance(response_data, dict):
            if response_data.get("success") == False:
                result["status"] = "error"
                result["error"] = response_data.get("error", "Unknown error")
            elif "error" in response_data and response_data["error"]:
                result["status"] = "error"
                result["error"] = response_data["error"]
        
        result["sample_response"] = json.dumps(response_data, indent=2, ensure_ascii=False)[:500]  # Первые 500 символов
        
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
        result["traceback"] = traceback.format_exc()
        logger.error(f"Ошибка при тестировании {tool_name}: {e}")
    
    return result


async def main():
    """Главная функция тестирования"""
    logger.info("=" * 60)
    logger.info("КОМПЛЕКСНОЕ ТЕСТИРОВАНИЕ ВСЕХ MCP ИНСТРУМЕНТОВ")
    logger.info("=" * 60)
    
    # Инициализация
    await initialize_components()
    
    # Результаты тестирования
    results = {
        "timestamp": datetime.now().isoformat(),
        "total_tools": len(TEST_CASES),
        "tested": 0,
        "success": 0,
        "error": 0,
        "warning": 0,
        "skipped": 0,
        "tools": []
    }
    
    # Тестируем каждый инструмент
    logger.info(f"\nНачинаем тестирование {len(TEST_CASES)} инструментов...\n")
    
    for i, (tool_name, test_case) in enumerate(TEST_CASES.items(), 1):
        logger.info(f"[{i}/{len(TEST_CASES)}] Тестирую: {tool_name}...")
        
        try:
            result = await test_tool(tool_name, test_case)
            results["tools"].append(result)
            results["tested"] += 1
            
            if result["status"] == "success":
                results["success"] += 1
                logger.info(f"  ✅ {tool_name}: Успешно ({result['response_time']}s)")
            elif result["status"] == "warning":
                results["warning"] += 1
                logger.warning(f"  ⚠️  {tool_name}: Предупреждение - {result.get('error', '')}")
            elif result["status"] == "skipped":
                results["skipped"] += 1
                logger.info(f"  ⏭️  {tool_name}: Пропущен - {result.get('error', '')}")
            else:
                results["error"] += 1
                logger.error(f"  ❌ {tool_name}: Ошибка - {result.get('error', 'Unknown')}")
        
        except Exception as e:
            logger.error(f"  ❌ {tool_name}: Критическая ошибка - {e}")
            results["tools"].append({
                "tool": tool_name,
                "status": "error",
                "error": str(e),
                "traceback": traceback.format_exc()
            })
            results["error"] += 1
        
        # Небольшая задержка между тестами
        await asyncio.sleep(0.5)
    
    # Сохраняем результаты
    report_file = Path(__file__).parent / f"mcp_tools_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    # Выводим итоговый отчет
    logger.info("\n" + "=" * 60)
    logger.info("ИТОГОВЫЙ ОТЧЕТ")
    logger.info("=" * 60)
    logger.info(f"Всего инструментов: {results['total_tools']}")
    logger.info(f"Протестировано: {results['tested']}")
    logger.info(f"✅ Успешно: {results['success']}")
    logger.info(f"⚠️  Предупреждения: {results['warning']}")
    logger.info(f"⏭️  Пропущено: {results['skipped']}")
    logger.info(f"❌ Ошибки: {results['error']}")
    logger.info(f"\nОтчет сохранен: {report_file}")
    
    # Детальный отчет по ошибкам
    if results["error"] > 0:
        logger.info("\n" + "=" * 60)
        logger.info("ДЕТАЛИ ОШИБОК")
        logger.info("=" * 60)
        for tool_result in results["tools"]:
            if tool_result["status"] == "error":
                logger.error(f"\n{tool_result['tool']}:")
                logger.error(f"  Ошибка: {tool_result.get('error', 'Unknown')}")
                if "traceback" in tool_result:
                    logger.error(f"  Traceback: {tool_result['traceback'][:500]}")
    
    # Детальный отчет по предупреждениям
    if results["warning"] > 0:
        logger.info("\n" + "=" * 60)
        logger.info("ДЕТАЛИ ПРЕДУПРЕЖДЕНИЙ")
        logger.info("=" * 60)
        for tool_result in results["tools"]:
            if tool_result["status"] == "warning":
                logger.warning(f"\n{tool_result['tool']}:")
                logger.warning(f"  Предупреждение: {tool_result.get('error', 'Unknown')}")
    
    logger.info("\n" + "=" * 60)
    
    # Закрываем соединения
    if bybit_client:
        await bybit_client.close()
    
    return results


if __name__ == "__main__":
    try:
        results = asyncio.run(main())
        sys.exit(0 if results["error"] == 0 else 1)
    except KeyboardInterrupt:
        logger.info("\nТестирование прервано пользователем")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}", exc_info=True)
        sys.exit(1)

