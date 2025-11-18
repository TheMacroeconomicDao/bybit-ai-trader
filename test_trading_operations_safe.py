#!/usr/bin/env python3
"""
Безопасное тестирование торговых операций
Использует минимальные суммы и проверяет доступность средств
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, Any

sys.path.insert(0, str(Path(__file__).parent))

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
except ImportError as e:
    print(f"❌ MCP SDK не установлен: {e}")
    sys.exit(1)

try:
    from loguru import logger
    logger.remove()
    logger.add(sys.stdout, format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>", level="INFO")
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)-8s | %(message)s')
    logger = logging.getLogger(__name__)


SERVER_PATH = Path(__file__).parent / "mcp_server" / "full_server.py"
VENV_PYTHON = Path(__file__).parent / "venv" / "bin" / "python"


async def safe_test_trading_operations():
    """Безопасное тестирование торговых операций"""
    
    logger.info("=" * 70)
    logger.info("🛡️  БЕЗОПАСНОЕ ТЕСТИРОВАНИЕ ТОРГОВЫХ ОПЕРАЦИЙ")
    logger.info("=" * 70)
    
    # Проверяем Python
    if not VENV_PYTHON.exists():
        python_cmd = sys.executable
    else:
        python_cmd = str(VENV_PYTHON)
    
    server_params = StdioServerParameters(
        command=python_cmd,
        args=[str(SERVER_PATH)]
    )
    
    results = {}
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                logger.info("✅ Подключено к MCP серверу")
                
                # ШАГ 1: Проверяем баланс
                logger.info("\n" + "=" * 70)
                logger.info("ШАГ 1: ПРОВЕРКА БАЛАНСА")
                logger.info("=" * 70)
                
                account_info = await session.call_tool("get_account_info", {})
                account_data = json.loads(account_info.content[0].text)
                
                total_balance = account_data.get("balance", {}).get("total", 0)
                available_balance = account_data.get("balance", {}).get("available", 0)
                
                logger.info(f"💰 Общий баланс: ${total_balance:.2f}")
                logger.info(f"💵 Доступно: ${available_balance:.2f}")
                
                if available_balance < 1:
                    logger.warning("⚠️  Доступный баланс менее $1. Торговые операции могут не пройти.")
                    logger.info("Продолжаем тестирование структуры запросов...")
                
                # ШАГ 2: Проверяем текущую цену BTC
                logger.info("\n" + "=" * 70)
                logger.info("ШАГ 2: ПРОВЕРКА ТЕКУЩЕЙ ЦЕНЫ")
                logger.info("=" * 70)
                
                price_info = await session.call_tool("get_asset_price", {"symbol": "BTCUSDT"})
                price_data = json.loads(price_info.content[0].text)
                current_price = price_data.get("price", 0)
                
                logger.info(f"📊 Текущая цена BTC: ${current_price:,.2f}")
                
                # ШАГ 3: Валидация входа (без реального ордера)
                logger.info("\n" + "=" * 70)
                logger.info("ШАГ 3: ВАЛИДАЦИЯ ВХОДА")
                logger.info("=" * 70)
                
                entry_price = current_price * 0.99  # На 1% ниже текущей цены
                stop_loss = entry_price * 0.99      # На 1% ниже entry
                take_profit = entry_price * 1.02    # На 2% выше entry
                
                logger.info(f"📈 Entry: ${entry_price:,.2f}")
                logger.info(f"🛑 Stop Loss: ${stop_loss:,.2f}")
                logger.info(f"🎯 Take Profit: ${take_profit:,.2f}")
                
                validation = await session.call_tool("validate_entry", {
                    "symbol": "BTCUSDT",
                    "side": "long",
                    "entry_price": entry_price,
                    "stop_loss": stop_loss,
                    "take_profit": take_profit
                })
                validation_data = json.loads(validation.content[0].text)
                
                is_valid = validation_data.get("is_valid", False)
                score = validation_data.get("score", 0)
                
                logger.info(f"✅ Валидация: {'ПРОЙДЕНА' if is_valid else 'НЕ ПРОЙДЕНА'}")
                logger.info(f"📊 Score: {score}/10")
                
                if not is_valid or score < 7:
                    logger.warning("⚠️  Setup не валиден. НЕ РЕКОМЕНДУЕТСЯ открывать позицию!")
                    logger.info("Пропускаем реальный place_order для безопасности.")
                    results["place_order"] = {
                        "tested": False,
                        "reason": "Setup не валиден (score < 7)",
                        "validation": validation_data
                    }
                else:
                    # ШАГ 4: Тестируем place_order с МИНИМАЛЬНОЙ суммой
                    logger.info("\n" + "=" * 70)
                    logger.info("ШАГ 4: ТЕСТИРОВАНИЕ PLACE_ORDER (МИНИМАЛЬНАЯ СУММА)")
                    logger.info("=" * 70)
                    
                    # Используем минимальную сумму: $1
                    min_quantity = 1.0 / current_price  # Минимальное количество BTC на $1
                    
                    logger.warning(f"⚠️  ВНИМАНИЕ: Попытка разместить ордер на ${1.0:.2f}")
                    logger.info(f"📦 Количество: {min_quantity:.8f} BTC")
                    
                    # Сначала проверяем ликвидность
                    liquidity_check = await session.call_tool("check_liquidity", {"symbol": "BTCUSDT"})
                    liquidity_data = json.loads(liquidity_check.content[0].text)
                    liquidity_score = liquidity_data.get("liquidity_score", 0)
                    
                    if liquidity_score < 0.5:
                        logger.warning(f"⚠️  Низкая ликвидность (score: {liquidity_score:.2f})")
                        logger.info("Пропускаем place_order для безопасности.")
                        results["place_order"] = {
                            "tested": False,
                            "reason": "Низкая ликвидность",
                            "liquidity_score": liquidity_score
                        }
                    else:
                        # Пробуем разместить ордер
                        logger.info("Попытка разместить ордер...")
                        
                        try:
                            order_result = await session.call_tool("place_order", {
                                "symbol": "BTCUSDT",
                                "side": "Buy",
                                "order_type": "Market",
                                "quantity": min_quantity,
                                "category": "spot"
                            })
                            
                            order_data = json.loads(order_result.content[0].text)
                            success = order_data.get("success", False)
                            
                            if success:
                                logger.success("✅ Ордер успешно размещен!")
                                results["place_order"] = {
                                    "tested": True,
                                    "success": True,
                                    "order_id": order_data.get("order_id"),
                                    "data": order_data
                                }
                                
                                # Если ордер размещен, можем протестировать cancel_order
                                order_id = order_data.get("order_id")
                                if order_id:
                                    logger.info("\n" + "=" * 70)
                                    logger.info("ШАГ 5: ТЕСТИРОВАНИЕ CANCEL_ORDER")
                                    logger.info("=" * 70)
                                    
                                    cancel_result = await session.call_tool("cancel_order", {
                                        "order_id": order_id,
                                        "symbol": "BTCUSDT",
                                        "category": "spot"
                                    })
                                    
                                    cancel_data = json.loads(cancel_result.content[0].text)
                                    cancel_success = cancel_data.get("success", False)
                                    
                                    if cancel_success:
                                        logger.success("✅ Ордер успешно отменен!")
                                        results["cancel_order"] = {
                                            "tested": True,
                                            "success": True,
                                            "data": cancel_data
                                        }
                                    else:
                                        logger.warning(f"⚠️  Не удалось отменить ордер: {cancel_data.get('error')}")
                                        results["cancel_order"] = {
                                            "tested": True,
                                            "success": False,
                                            "error": cancel_data.get("error"),
                                            "data": cancel_data
                                        }
                            else:
                                error = order_data.get("error", "Unknown")
                                logger.warning(f"⚠️  Ордер не размещен: {error}")
                                results["place_order"] = {
                                    "tested": True,
                                    "success": False,
                                    "error": error,
                                    "data": order_data
                                }
                                
                        except Exception as e:
                            logger.error(f"❌ Ошибка при размещении ордера: {e}")
                            results["place_order"] = {
                                "tested": True,
                                "success": False,
                                "error": str(e)
                            }
                
                # ШАГ 6: Тестируем операции с позициями (если есть открытые позиции)
                logger.info("\n" + "=" * 70)
                logger.info("ШАГ 6: ПРОВЕРКА ОТКРЫТЫХ ПОЗИЦИЙ")
                logger.info("=" * 70)
                
                positions_info = await session.call_tool("get_open_positions", {})
                positions_data = json.loads(positions_info.content[0].text)
                
                if isinstance(positions_data, list) and len(positions_data) > 0:
                    logger.info(f"📊 Найдено открытых позиций: {len(positions_data)}")
                    
                    # Тестируем modify_position
                    first_position = positions_data[0]
                    symbol = first_position.get("symbol")
                    
                    logger.info(f"\nТестируем modify_position для {symbol}...")
                    modify_result = await session.call_tool("modify_position", {
                        "symbol": symbol,
                        "stop_loss": first_position.get("entry_price", 0) * 0.99,
                        "take_profit": first_position.get("entry_price", 0) * 1.02,
                        "category": "linear"
                    })
                    
                    modify_data = json.loads(modify_result.content[0].text)
                    results["modify_position"] = {
                        "tested": True,
                        "success": modify_data.get("success", False),
                        "data": modify_data
                    }
                    
                    # Тестируем move_to_breakeven
                    logger.info(f"\nТестируем move_to_breakeven для {symbol}...")
                    breakeven_result = await session.call_tool("move_to_breakeven", {
                        "symbol": symbol,
                        "entry_price": first_position.get("entry_price", 0),
                        "category": "linear"
                    })
                    
                    breakeven_data = json.loads(breakeven_result.content[0].text)
                    results["move_to_breakeven"] = {
                        "tested": True,
                        "success": breakeven_data.get("success", False),
                        "data": breakeven_data
                    }
                    
                    # Тестируем activate_trailing_stop
                    logger.info(f"\nТестируем activate_trailing_stop для {symbol}...")
                    trailing_result = await session.call_tool("activate_trailing_stop", {
                        "symbol": symbol,
                        "trailing_distance": 1.0,
                        "category": "linear"
                    })
                    
                    trailing_data = json.loads(trailing_result.content[0].text)
                    results["activate_trailing_stop"] = {
                        "tested": True,
                        "success": trailing_data.get("success", False),
                        "data": trailing_data
                    }
                    
                    # Тестируем close_position
                    logger.info(f"\nТестируем close_position для {symbol}...")
                    close_result = await session.call_tool("close_position", {
                        "symbol": symbol,
                        "category": "linear"
                    })
                    
                    close_data = json.loads(close_result.content[0].text)
                    results["close_position"] = {
                        "tested": True,
                        "success": close_data.get("success", False),
                        "data": close_data
                    }
                    
                else:
                    logger.info("📊 Нет открытых позиций")
                    logger.info("Операции с позициями не могут быть протестированы")
                    
                    results["modify_position"] = {
                        "tested": False,
                        "reason": "Нет открытых позиций"
                    }
                    results["move_to_breakeven"] = {
                        "tested": False,
                        "reason": "Нет открытых позиций"
                    }
                    results["activate_trailing_stop"] = {
                        "tested": False,
                        "reason": "Нет открытых позиций"
                    }
                    results["close_position"] = {
                        "tested": False,
                        "reason": "Нет открытых позиций"
                    }
                
                # Итоговый отчет
                logger.info("\n" + "=" * 70)
                logger.info("📊 ИТОГОВЫЙ ОТЧЕТ")
                logger.info("=" * 70)
                
                tested_count = sum(1 for r in results.values() if r.get("tested", False))
                success_count = sum(1 for r in results.values() if r.get("success", False))
                
                logger.info(f"\n✅ Протестировано: {tested_count}/6")
                logger.info(f"✅ Успешно: {success_count}/{tested_count}")
                
                for tool_name, result in results.items():
                    if result.get("tested"):
                        status = "✅" if result.get("success") else "❌"
                        logger.info(f"{status} {tool_name}: {'УСПЕХ' if result.get('success') else 'ОШИБКА'}")
                        if not result.get("success") and result.get("error"):
                            logger.info(f"   Ошибка: {result.get('error')}")
                    else:
                        logger.info(f"⏭️  {tool_name}: {result.get('reason', 'Не протестирован')}")
                
                # Сохраняем отчет
                report_file = Path(__file__).parent / f"trading_ops_test_report_{Path(__file__).stem}.json"
                with open(report_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        "timestamp": __import__('datetime').datetime.now().isoformat(),
                        "balance": {
                            "total": total_balance,
                            "available": available_balance
                        },
                        "results": results
                    }, f, indent=2, ensure_ascii=False)
                
                logger.info(f"\n💾 Отчет сохранен: {report_file}")
                
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    try:
        asyncio.run(safe_test_trading_operations())
    except KeyboardInterrupt:
        logger.info("\n⚠️  Тестирование прервано пользователем")
        sys.exit(130)
    except Exception as e:
        logger.error(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

