#!/usr/bin/env python3
"""
Прямое тестирование всех MCP инструментов
Вызывает методы напрямую без MCP протокола для быстрой проверки
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import traceback
import pandas as pd

# Добавляем путь к mcp_server
sys.path.insert(0, str(Path(__file__).parent / "mcp_server"))

from loguru import logger
from trading_operations import TradingOperations, get_all_account_balances
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
logger.add(
    sys.stderr,
    level="INFO",
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>"
)

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


async def test_tool_direct(tool_name: str, test_func, *args, **kwargs) -> Dict[str, Any]:
    """Прямое тестирование инструмента"""
    result = {
        "tool": tool_name,
        "status": "pending",
        "error": None,
        "response_time": None,
        "has_data": False,
        "sample_response": None
    }
    
    try:
        start_time = datetime.now()
        
        # Вызываем функцию
        response = await test_func(*args, **kwargs)
        
        end_time = datetime.now()
        response_time = (end_time - start_time).total_seconds()
        
        result["response_time"] = round(response_time, 2)
        result["has_data"] = response is not None
        
        # Проверяем тип ответа
        if isinstance(response, dict):
            result["sample_response"] = json.dumps(response, indent=2, ensure_ascii=False)[:500]
            # Проверяем на ошибки
            if response.get("success") == False:
                result["status"] = "error"
                result["error"] = response.get("error", "Unknown error")
            elif "error" in response and response["error"]:
                result["status"] = "error"
                result["error"] = response["error"]
            else:
                result["status"] = "success"
        elif isinstance(response, list):
            result["sample_response"] = f"List with {len(response)} items"
            result["status"] = "success" if len(response) > 0 else "warning"
            if len(response) == 0:
                result["error"] = "Empty list returned"
        else:
            result["sample_response"] = str(response)[:500]
            result["status"] = "success"
        
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
        result["traceback"] = traceback.format_exc()
        logger.error(f"Ошибка при тестировании {tool_name}: {e}")
    
    return result


# Тестовые функции для каждого инструмента
TEST_FUNCTIONS = {
    # ═══════════════════════════════════════
    # 📊 РЫНОЧНЫЕ ДАННЫЕ
    # ═══════════════════════════════════════
    
    "get_market_overview": {
        "func": lambda: trading_ops.get_market_overview("spot"),
        "description": "Полный обзор рынка"
    },
    
    "get_all_tickers": {
        "func": lambda: bybit_client.get_all_tickers("spot", "volume"),
        "description": "Все торговые пары"
    },
    
    "get_asset_price": {
        "func": lambda: bybit_client.get_asset_price("BTC/USDT"),
        "description": "Текущая цена актива"
    },
    
    # ═══════════════════════════════════════
    # 📈 ТЕХНИЧЕСКИЙ АНАЛИЗ
    # ═══════════════════════════════════════
    
    "analyze_asset": {
        "func": lambda: technical_analysis.analyze_asset("BTC/USDT", ["1h", "4h"], True),
        "description": "Полный анализ актива"
    },
    
    "calculate_indicators": {
        "func": lambda: technical_analysis._analyze_timeframe("BTC/USDT", "1h", False),
        "description": "Расчет индикаторов"
    },
    
    "detect_patterns": {
        "async_func": lambda: _test_detect_patterns(),
        "description": "Поиск паттернов"
    },
    
    "find_support_resistance": {
        "async_func": lambda: _test_find_support_resistance(),
        "description": "Уровни поддержки и сопротивления"
    },
    
    "get_btc_correlation": {
        "func": lambda: technical_analysis.get_btc_correlation("ETH/USDT", 24, "1h"),
        "description": "Корреляция с BTC"
    },
    
    "get_funding_rate": {
        "func": lambda: bybit_client.get_funding_rate("BTC/USDT:USDT"),
        "description": "Funding rate для фьючерсов"
    },
    
    "check_tf_alignment": {
        "func": lambda: technical_analysis.check_tf_alignment("BTC/USDT", ["1h", "4h", "1d"]),
        "description": "Проверка alignment таймфреймов"
    },
    
    # ═══════════════════════════════════════
    # 🔍 СКАНИРОВАНИЕ РЫНКА
    # ═══════════════════════════════════════
    
    "scan_market": {
        "func": lambda: market_scanner.scan_market(
            {"market_type": "spot", "min_volume_24h": 1000000},
            limit=5
        ),
        "description": "Сканирование рынка"
    },
    
    "find_oversold_assets": {
        "func": lambda: market_scanner.find_oversold_assets("spot", 1000000),
        "description": "Перепроданные активы"
    },
    
    "find_overbought_assets": {
        "func": lambda: market_scanner.find_overbought_assets("spot", 1000000),
        "description": "Перекупленные активы"
    },
    
    "find_breakout_opportunities": {
        "func": lambda: market_scanner.find_breakout_opportunities("spot", 1000000),
        "description": "Возможности пробоя"
    },
    
    "find_trend_reversals": {
        "func": lambda: market_scanner.find_trend_reversals("spot", 1000000),
        "description": "Развороты тренда"
    },
    
    # ═══════════════════════════════════════
    # 🎯 ВАЛИДАЦИЯ ВХОДА
    # ═══════════════════════════════════════
    
    "check_liquidity": {
        "func": lambda: technical_analysis.check_liquidity("BTC/USDT"),
        "description": "Проверка ликвидности"
    },
    
    "validate_entry": {
        "func": lambda: technical_analysis.validate_entry(
            "BTC/USDT", "long", 50000, 49000, 52000, 0.01, signal_tracker
        ),
        "description": "Валидация точки входа"
    },
    
    "get_open_interest": {
        "func": lambda: bybit_client.get_open_interest("BTCUSDT", "linear"),
        "description": "Open Interest для futures"
    },
    
    # ═══════════════════════════════════════
    # 💰 СЧЁТ И ПОЗИЦИИ
    # ═══════════════════════════════════════
    
    "get_account_info": {
        "async_func": lambda: _test_get_account_info(),
        "description": "Информация о счёте"
    },
    
    "get_open_positions": {
        "async_func": lambda: _test_get_open_positions(),
        "description": "Открытые позиции"
    },
    
    "get_order_history": {
        "async_func": lambda: _test_get_order_history(),
        "description": "История ордеров"
    },
    
    # ═══════════════════════════════════════
    # 📡 REAL-TIME МОНИТОРИНГ
    # ═══════════════════════════════════════
    
    "start_position_monitoring": {
        "async_func": lambda: _test_start_monitoring(),
        "description": "Запуск мониторинга позиций"
    },
    
    "stop_position_monitoring": {
        "func": lambda: position_monitor.stop_monitoring(),
        "description": "Остановка мониторинга"
    },
    
    # ═══════════════════════════════════════
    # 🛠️ ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
    # ═══════════════════════════════════════
    
    "move_to_breakeven": {
        "func": lambda: trading_ops.move_to_breakeven("BTCUSDT", 50000, "linear"),
        "description": "Перевод SL в breakeven",
        "skip_if_no_position": True
    },
    
    "activate_trailing_stop": {
        "func": lambda: trading_ops.activate_trailing_stop("BTCUSDT", 2.0, "linear"),
        "description": "Активация trailing stop",
        "skip_if_no_position": True
    },
    
    # ═══════════════════════════════════════
    # 📊 КОНТРОЛЬ КАЧЕСТВА СИГНАЛОВ
    # ═══════════════════════════════════════
    
    "track_signal": {
        "func": lambda: signal_tracker.record_signal(
            "BTC/USDT", "long", 50000, 49000, 52000, 8.5, 0.75
        ),
        "description": "Запись сигнала"
    },
    
    "get_signal_quality_metrics": {
        "func": lambda: quality_metrics.calculate_overall_metrics(days=30),
        "description": "Метрики качества сигналов"
    },
    
    "get_signal_performance_report": {
        "func": lambda: signal_reports.generate_summary_report(days=30, format="summary"),
        "description": "Отчет о производительности"
    },
    
    "get_active_signals": {
        "func": lambda: signal_tracker.get_active_signals(),
        "description": "Активные сигналы"
    },
    
    "get_signal_details": {
        "async_func": lambda: _test_get_signal_details(),
        "description": "Детали сигнала",
        "skip_if_no_signals": True
    },
}


async def _test_detect_patterns():
    """Вспомогательная функция для detect_patterns"""
    ohlcv = await bybit_client.get_ohlcv("BTC/USDT", "1h")
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    return technical_analysis._detect_patterns(df)


async def _test_find_support_resistance():
    """Вспомогательная функция для find_support_resistance"""
    ohlcv = await bybit_client.get_ohlcv("BTC/USDT", "1h", limit=50)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    return technical_analysis._find_support_resistance(df)


async def _test_get_account_info():
    """Вспомогательная функция для get_account_info"""
    all_balances = get_all_account_balances(trading_ops.session, coin="USDT")
    positions = []
    test_symbols = ["BTCUSDT", "ETHUSDT"]
    
    for test_symbol in test_symbols:
        try:
            test_response = trading_ops.session.get_positions(category="linear", symbol=test_symbol)
            if test_response.get("retCode") == 0:
                positions_list = test_response.get("result", {}).get("list", [])
                positions.extend([p for p in positions_list if float(p.get("size", 0)) != 0])
        except:
            continue
    
    positions = [p for p in positions if float(p.get("size", 0)) != 0]
    total_equity = all_balances.get("total", 0.0)
    available = all_balances.get("available", 0.0)
    used_margin = sum(float(p.get("positionIM", 0) or 0) for p in positions)
    unrealized_pnl = sum(float(p.get("unrealisedPnl", 0) or 0) for p in positions)
    
    return {
        "balance": {
            "spot": all_balances.get("spot", {"total": 0.0, "available": 0.0, "success": False}),
            "contract": all_balances.get("contract", {"total": 0.0, "available": 0.0, "success": False}),
            "unified": all_balances.get("unified", {"total": 0.0, "available": 0.0, "success": False}),
            "total": total_equity,
            "available": available,
            "used_margin": used_margin,
            "unrealized_pnl": unrealized_pnl
        },
        "positions": positions,
        "risk_metrics": {
            "total_risk_pct": (used_margin / total_equity * 100) if total_equity > 0 else 0,
            "positions_count": len(positions),
            "max_drawdown": "N/A"
        }
    }


async def _test_get_open_positions():
    """Вспомогательная функция для get_open_positions"""
    all_positions = []
    test_symbols = ["BTCUSDT", "ETHUSDT"]
    
    for test_symbol in test_symbols:
        try:
            test_response = trading_ops.session.get_positions(category="linear", symbol=test_symbol)
            if test_response.get("retCode") == 0:
                positions_list = test_response.get("result", {}).get("list", [])
                all_positions.extend([p for p in positions_list if float(p.get("size", 0)) != 0])
        except:
            continue
    
    if all_positions:
        open_positions = [
            {
                "symbol": p.get("symbol"),
                "side": p.get("side"),
                "size": float(p.get("size", 0)),
                "entry_price": float(p.get("avgPrice", 0)),
                "current_price": float(p.get("markPrice", 0)),
                "unrealized_pnl": float(p.get("unrealisedPnl", 0)),
                "unrealized_pnl_pct": float(p.get("unrealisedPnl", 0)) / float(p.get("positionValue", 1)) * 100 if float(p.get("positionValue", 0)) != 0 else 0,
                "leverage": p.get("leverage"),
                "margin": float(p.get("positionIM", 0)),
                "liquidation_price": float(p.get("liqPrice", 0))
            }
            for p in all_positions if float(p.get("size", 0)) != 0
        ]
        return open_positions
    else:
        return []


async def _test_get_order_history():
    """Вспомогательная функция для get_order_history"""
    response = trading_ops.session.get_order_history(category="spot", limit="10")
    if response.get("retCode") == 0:
        return response.get("result", {})
    else:
        return {"success": False, "error": response.get("retMsg", "Unknown error")}


async def _test_start_monitoring():
    """Вспомогательная функция для start_position_monitoring"""
    await position_monitor.start_monitoring({
        "move_to_breakeven_at": 1.0,
        "enable_trailing_at": 2.0,
        "exit_on_reversal": True,
        "max_time_in_trade": 12
    })
    return {"success": True, "message": "Position monitoring started"}


async def _test_get_signal_details():
    """Вспомогательная функция для get_signal_details"""
    active_signals = await signal_tracker.get_active_signals()
    if not active_signals:
        return {"success": False, "error": "No active signals"}
    signal_id = active_signals[0]["signal_id"]
    signal = await signal_tracker.get_signal(signal_id)
    if signal:
        snapshots = await signal_tracker.get_price_snapshots(signal_id, limit=100)
        return {
            "success": True,
            "signal": signal,
            "price_snapshots": snapshots,
            "snapshots_count": len(snapshots)
        }
    else:
        return {"success": False, "error": f"Signal {signal_id} not found"}


async def main():
    """Главная функция тестирования"""
    logger.info("=" * 70)
    logger.info("🔍 КОМПЛЕКСНОЕ ТЕСТИРОВАНИЕ ВСЕХ MCP ИНСТРУМЕНТОВ")
    logger.info("=" * 70)
    
    # Инициализация
    await initialize_components()
    
    # Результаты тестирования
    results = {
        "timestamp": datetime.now().isoformat(),
        "total_tools": len(TEST_FUNCTIONS),
        "tested": 0,
        "success": 0,
        "error": 0,
        "warning": 0,
        "skipped": 0,
        "tools": []
    }
    
    logger.info(f"\nНачинаем тестирование {len(TEST_FUNCTIONS)} инструментов...\n")
    
    # Тестируем каждый инструмент
    for i, (tool_name, test_config) in enumerate(TEST_FUNCTIONS.items(), 1):
        logger.info(f"[{i}/{len(TEST_FUNCTIONS)}] Тестирую: {tool_name}...")
        
        try:
            # Проверяем нужно ли пропустить
            if test_config.get("skip_if_no_position"):
                try:
                    positions = await _test_get_open_positions()
                    if not positions:
                        result = {
                            "tool": tool_name,
                            "status": "skipped",
                            "error": "Нет открытых позиций для тестирования",
                            "description": test_config.get("description", "")
                        }
                        results["tools"].append(result)
                        results["skipped"] += 1
                        results["tested"] += 1
                        logger.info(f"  ⏭️  {tool_name}: Пропущен (нет позиций)")
                        continue
                except:
                    pass
            
            if test_config.get("skip_if_no_signals") and tool_name == "get_signal_details":
                try:
                    active_signals = await signal_tracker.get_active_signals()
                    if not active_signals:
                        result = {
                            "tool": tool_name,
                            "status": "skipped",
                            "error": "Нет активных сигналов для тестирования",
                            "description": test_config.get("description", "")
                        }
                        results["tools"].append(result)
                        results["skipped"] += 1
                        results["tested"] += 1
                        logger.info(f"  ⏭️  {tool_name}: Пропущен (нет сигналов)")
                        continue
                except:
                    pass
            
            # Вызываем функцию
            if "async_func" in test_config:
                result = await test_tool_direct(tool_name, test_config["async_func"])
            else:
                result = await test_tool_direct(tool_name, test_config["func"])
            
            result["description"] = test_config.get("description", "")
            results["tools"].append(result)
            results["tested"] += 1
            
            if result["status"] == "success":
                results["success"] += 1
                logger.info(f"  ✅ {tool_name}: Успешно ({result['response_time']}s)")
            elif result["status"] == "warning":
                results["warning"] += 1
                logger.warning(f"  ⚠️  {tool_name}: Предупреждение - {result.get('error', '')}")
            else:
                results["error"] += 1
                logger.error(f"  ❌ {tool_name}: Ошибка - {result.get('error', 'Unknown')}")
        
        except Exception as e:
            logger.error(f"  ❌ {tool_name}: Критическая ошибка - {e}")
            results["tools"].append({
                "tool": tool_name,
                "status": "error",
                "error": str(e),
                "traceback": traceback.format_exc(),
                "description": test_config.get("description", "")
            })
            results["error"] += 1
            results["tested"] += 1
        
        # Небольшая задержка между тестами
        await asyncio.sleep(0.5)
    
    # Сохраняем результаты
    report_file = Path(__file__).parent / f"mcp_tools_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    # Выводим итоговый отчет
    logger.info("\n" + "=" * 70)
    logger.info("📊 ИТОГОВЫЙ ОТЧЕТ")
    logger.info("=" * 70)
    logger.info(f"Всего инструментов: {results['total_tools']}")
    logger.info(f"Протестировано: {results['tested']}")
    logger.info(f"✅ Успешно: {results['success']}")
    logger.info(f"⚠️  Предупреждения: {results['warning']}")
    logger.info(f"⏭️  Пропущено: {results['skipped']}")
    logger.info(f"❌ Ошибки: {results['error']}")
    
    success_rate = (results['success'] / results['tested'] * 100) if results['tested'] > 0 else 0
    logger.info(f"\n📈 Успешность: {success_rate:.1f}%")
    logger.info(f"\n💾 Отчет сохранен: {report_file}")
    
    # Детальный отчет по ошибкам
    if results["error"] > 0:
        logger.info("\n" + "=" * 70)
        logger.info("❌ ДЕТАЛИ ОШИБОК")
        logger.info("=" * 70)
        for tool_result in results["tools"]:
            if tool_result["status"] == "error":
                logger.error(f"\n🔴 {tool_result['tool']}:")
                logger.error(f"   Описание: {tool_result.get('description', 'N/A')}")
                logger.error(f"   Ошибка: {tool_result.get('error', 'Unknown')}")
    
    # Детальный отчет по предупреждениям
    if results["warning"] > 0:
        logger.info("\n" + "=" * 70)
        logger.info("⚠️  ДЕТАЛИ ПРЕДУПРЕЖДЕНИЙ")
        logger.info("=" * 70)
        for tool_result in results["tools"]:
            if tool_result["status"] == "warning":
                logger.warning(f"\n🟡 {tool_result['tool']}:")
                logger.warning(f"   Описание: {tool_result.get('description', 'N/A')}")
                logger.warning(f"   Предупреждение: {tool_result.get('error', 'Unknown')}")
    
    logger.info("\n" + "=" * 70)
    
    # Закрываем соединения
    if bybit_client:
        await bybit_client.close()
    
    return results


if __name__ == "__main__":
    try:
        results = asyncio.run(main())
        sys.exit(0 if results["error"] == 0 else 1)
    except KeyboardInterrupt:
        logger.info("\n⚠️  Тестирование прервано пользователем")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}", exc_info=True)
        sys.exit(1)

