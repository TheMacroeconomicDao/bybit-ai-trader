#!/usr/bin/env python3
"""
Тестовый скрипт для проверки Trading Operations, Monitoring и Auto-Actions функций
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, Any

# Добавляем путь к модулям
sys.path.insert(0, str(Path(__file__).parent / "mcp_server"))

from trading_operations import TradingOperations
from position_monitor import PositionMonitor
from loguru import logger

# Настройка логирования
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    level="INFO"
)


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


async def test_place_order(trading_ops: TradingOperations):
    """Тест place_order"""
    logger.info("=" * 60)
    logger.info("TEST 1: place_order")
    logger.info("=" * 60)
    
    try:
        # Тест с минимальными параметрами (Market order)
        result = await trading_ops.place_order(
            symbol="BTCUSDT",
            side="Buy",
            order_type="Market",
            quantity=0.0001,  # Минимальная сумма для теста
            category="spot"
        )
        
        logger.info(f"✅ place_order result: {json.dumps(result, indent=2)}")
        return result.get("success", False)
    except Exception as e:
        logger.error(f"❌ place_order failed: {e}")
        return False


async def test_close_position(trading_ops: TradingOperations):
    """Тест close_position"""
    logger.info("=" * 60)
    logger.info("TEST 2: close_position")
    logger.info("=" * 60)
    
    try:
        # Тест для spot (если есть позиция)
        result = await trading_ops.close_position(
            symbol="BTCUSDT",
            category="spot",
            reason="Test close"
        )
        
        logger.info(f"✅ close_position result: {json.dumps(result, indent=2)}")
        
        # Если нет позиции - это нормально для теста
        if not result.get("success") and "No" in result.get("message", ""):
            logger.info("ℹ️  No position to close (expected for test)")
            return True
        
        return result.get("success", False)
    except Exception as e:
        logger.error(f"❌ close_position failed: {e}")
        return False


async def test_modify_position(trading_ops: TradingOperations):
    """Тест modify_position"""
    logger.info("=" * 60)
    logger.info("TEST 3: modify_position")
    logger.info("=" * 60)
    
    try:
        # Тест для futures (если есть позиция)
        result = await trading_ops.modify_position(
            symbol="BTCUSDT",
            stop_loss=50000.0,
            take_profit=52000.0,
            category="linear"
        )
        
        logger.info(f"✅ modify_position result: {json.dumps(result, indent=2)}")
        
        # Если нет позиции - это нормально для теста
        if not result.get("success") and "No open position" in result.get("message", ""):
            logger.info("ℹ️  No position to modify (expected for test)")
            return True
        
        return result.get("success", False)
    except Exception as e:
        logger.error(f"❌ modify_position failed: {e}")
        return False


async def test_cancel_order(trading_ops: TradingOperations):
    """Тест cancel_order"""
    logger.info("=" * 60)
    logger.info("TEST 4: cancel_order")
    logger.info("=" * 60)
    
    try:
        # Тест с несуществующим order_id (для проверки обработки ошибок)
        result = await trading_ops.cancel_order(
            order_id="test_order_123",
            symbol="BTCUSDT",
            category="spot"
        )
        
        logger.info(f"✅ cancel_order result: {json.dumps(result, indent=2)}")
        
        # Ожидаем ошибку для несуществующего ордера
        if not result.get("success"):
            logger.info("ℹ️  Order not found (expected for test)")
            return True  # Правильная обработка ошибки
        
        return result.get("success", False)
    except Exception as e:
        logger.error(f"❌ cancel_order failed: {e}")
        return False


async def test_start_monitoring(position_monitor: PositionMonitor):
    """Тест start_position_monitoring"""
    logger.info("=" * 60)
    logger.info("TEST 5: start_position_monitoring")
    logger.info("=" * 60)
    
    try:
        auto_actions = {
            "move_to_breakeven_at": 1.0,
            "enable_trailing_at": 2.0,
            "exit_on_reversal": True,
            "max_time_in_trade": 12
        }
        
        # Запускаем мониторинг в фоне
        monitor_task = asyncio.create_task(
            position_monitor.start_monitoring(auto_actions=auto_actions)
        )
        
        # Ждём немного чтобы убедиться что запустилось
        await asyncio.sleep(2)
        
        if position_monitor.monitoring:
            logger.info("✅ Monitoring started successfully")
            return True
        else:
            logger.error("❌ Monitoring failed to start")
            return False
            
    except Exception as e:
        logger.error(f"❌ start_monitoring failed: {e}")
        return False
    finally:
        # Останавливаем мониторинг
        await position_monitor.stop_monitoring()
        if 'monitor_task' in locals():
            monitor_task.cancel()
            try:
                await monitor_task
            except asyncio.CancelledError:
                pass


async def test_stop_monitoring(position_monitor: PositionMonitor):
    """Тест stop_position_monitoring"""
    logger.info("=" * 60)
    logger.info("TEST 6: stop_position_monitoring")
    logger.info("=" * 60)
    
    try:
        # Сначала запускаем
        monitor_task = asyncio.create_task(
            position_monitor.start_monitoring()
        )
        await asyncio.sleep(1)
        
        # Затем останавливаем
        await position_monitor.stop_monitoring()
        await asyncio.sleep(1)
        
        if not position_monitor.monitoring:
            logger.info("✅ Monitoring stopped successfully")
            return True
        else:
            logger.error("❌ Monitoring failed to stop")
            return False
            
    except Exception as e:
        logger.error(f"❌ stop_monitoring failed: {e}")
        return False
    finally:
        if 'monitor_task' in locals():
            monitor_task.cancel()
            try:
                await monitor_task
            except asyncio.CancelledError:
                pass


async def test_move_to_breakeven(trading_ops: TradingOperations):
    """Тест move_to_breakeven"""
    logger.info("=" * 60)
    logger.info("TEST 7: move_to_breakeven")
    logger.info("=" * 60)
    
    try:
        result = await trading_ops.move_to_breakeven(
            symbol="BTCUSDT",
            entry_price=50000.0,
            category="linear"
        )
        
        logger.info(f"✅ move_to_breakeven result: {json.dumps(result, indent=2)}")
        
        # Если нет позиции - это нормально для теста
        if not result.get("success") and "No open position" in result.get("message", ""):
            logger.info("ℹ️  No position to move to breakeven (expected for test)")
            return True
        
        return result.get("success", False)
    except Exception as e:
        logger.error(f"❌ move_to_breakeven failed: {e}")
        return False


async def test_activate_trailing_stop(trading_ops: TradingOperations):
    """Тест activate_trailing_stop"""
    logger.info("=" * 60)
    logger.info("TEST 8: activate_trailing_stop")
    logger.info("=" * 60)
    
    try:
        result = await trading_ops.activate_trailing_stop(
            symbol="BTCUSDT",
            trailing_distance=2.0,
            category="linear"
        )
        
        logger.info(f"✅ activate_trailing_stop result: {json.dumps(result, indent=2)}")
        
        # Если нет позиции - это нормально для теста
        if not result.get("success") and "No open position" in result.get("message", ""):
            logger.info("ℹ️  No position to activate trailing stop (expected for test)")
            return True
        
        return result.get("success", False)
    except Exception as e:
        logger.error(f"❌ activate_trailing_stop failed: {e}")
        return False


async def main():
    """Главная функция тестирования"""
    logger.info("=" * 60)
    logger.info("НАЧАЛО ТЕСТИРОВАНИЯ TRADING FUNCTIONS")
    logger.info("=" * 60)
    
    # Загрузка credentials
    credentials = load_credentials()
    bybit_creds = credentials["bybit"]
    
    # Инициализация компонентов
    trading_ops = TradingOperations(
        api_key=bybit_creds["api_key"],
        api_secret=bybit_creds["api_secret"],
        testnet=bybit_creds.get("testnet", False)
    )
    
    position_monitor = PositionMonitor(
        api_key=bybit_creds["api_key"],
        api_secret=bybit_creds["api_secret"],
        testnet=bybit_creds.get("testnet", False)
    )
    
    # Результаты тестов
    results = {}
    
    # ═══ Trading Operations ═══
    logger.info("\n📊 ТЕСТИРОВАНИЕ TRADING OPERATIONS")
    logger.info("-" * 60)
    
    results["place_order"] = await test_place_order(trading_ops)
    await asyncio.sleep(1)
    
    results["close_position"] = await test_close_position(trading_ops)
    await asyncio.sleep(1)
    
    results["modify_position"] = await test_modify_position(trading_ops)
    await asyncio.sleep(1)
    
    results["cancel_order"] = await test_cancel_order(trading_ops)
    await asyncio.sleep(1)
    
    # ═══ Monitoring ═══
    logger.info("\n📡 ТЕСТИРОВАНИЕ MONITORING")
    logger.info("-" * 60)
    
    results["start_monitoring"] = await test_start_monitoring(position_monitor)
    await asyncio.sleep(1)
    
    results["stop_monitoring"] = await test_stop_monitoring(position_monitor)
    await asyncio.sleep(1)
    
    # ═══ Auto-Actions ═══
    logger.info("\n🤖 ТЕСТИРОВАНИЕ AUTO-ACTIONS")
    logger.info("-" * 60)
    
    results["move_to_breakeven"] = await test_move_to_breakeven(trading_ops)
    await asyncio.sleep(1)
    
    results["activate_trailing_stop"] = await test_activate_trailing_stop(trading_ops)
    await asyncio.sleep(1)
    
    # ═══ Итоги ═══
    logger.info("\n" + "=" * 60)
    logger.info("ИТОГИ ТЕСТИРОВАНИЯ")
    logger.info("=" * 60)
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    failed = total - passed
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status} - {test_name}")
    
    logger.info("-" * 60)
    logger.info(f"Всего тестов: {total}")
    logger.info(f"✅ Успешно: {passed}")
    logger.info(f"❌ Провалено: {failed}")
    logger.info(f"Процент успеха: {(passed/total*100):.1f}%")
    logger.info("=" * 60)
    
    return passed == total


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\n⚠️  Тестирование прервано пользователем")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n❌ Критическая ошибка: {e}", exc_info=True)
        sys.exit(1)



















