#!/usr/bin/env python3
"""Мониторинг позиции BTCUSDT в реальном времени"""

import sys
sys.path.insert(0, 'mcp_server')
from trading_operations import TradingOperations
import asyncio
import time
from datetime import datetime

async def monitor_position():
    api_key = 'V84NJog5v9bM5k6fRn'
    api_secret = 'RYZ1JeyGsWhtjigF01rKDYzq3lRbvlxvU89L'
    
    trading = TradingOperations(api_key=api_key, api_secret=api_secret, testnet=False)
    
    print("=" * 80)
    print("📊 МОНИТОРИНГ ПОЗИЦИИ BTCUSDT")
    print("=" * 80)
    print()
    
    # Параметры ордера (из предыдущего размещения)
    entry_price = 91469.0
    stop_loss = 91400.0
    take_profit = 91650.0
    leverage = 20
    quantity = 0.009
    
    print(f"🔹 ПАРАМЕТРЫ ПОЗИЦИИ:")
    print(f"   Symbol: BTCUSDT")
    print(f"   Side: LONG")
    print(f"   Entry Price: ${entry_price:.2f}")
    print(f"   Stop Loss: ${stop_loss:.2f}")
    print(f"   Take Profit: ${take_profit:.2f}")
    print(f"   Leverage: {leverage}x")
    print(f"   Quantity: {quantity} контрактов")
    print()
    
    # Расчеты
    sl_distance = ((entry_price - stop_loss) / entry_price) * 100
    tp_distance = ((take_profit - entry_price) / entry_price) * 100
    rr = tp_distance / sl_distance if sl_distance > 0 else 0
    
    print(f"   📈 РАСЧЕТЫ:")
    print(f"      Расстояние до SL: {sl_distance:.4f}%")
    print(f"      Расстояние до TP: {tp_distance:.4f}%")
    print(f"      R:R: {rr:.2f}")
    print()
    
    print("=" * 80)
    print("🔄 ЗАПУСК МОНИТОРИНГА (обновление каждые 10 секунд)")
    print("=" * 80)
    print("Нажмите Ctrl+C для остановки")
    print()
    
    update_count = 0
    last_price = None
    
    try:
        while True:
            try:
                # Получаем текущую цену через ticker
                ticker = trading.session.get_tickers(category="linear", symbol="BTCUSDT")
                
                if ticker.get('retCode') == 0:
                    current_price = float(ticker['result']['list'][0]['lastPrice'])
                    last_price = current_price
                    
                    # Получаем позиции
                    try:
                        positions_response = trading.session.get_positions(
                            category="linear", 
                            symbol="BTCUSDT"
                        )
                        
                        if positions_response.get('retCode') == 0:
                            positions_list = positions_response.get('result', {}).get('list', [])
                            
                            if positions_list and float(positions_list[0].get('size', 0)) > 0:
                                pos = positions_list[0]
                                unrealized_pnl = float(pos.get('unrealisedPnl', 0))
                                mark_price = float(pos.get('markPrice', 0))
                                actual_entry = float(pos.get('avgPrice', 0))
                                
                                # Используем актуальный entry price если есть
                                if actual_entry > 0:
                                    entry_price = actual_entry
                            else:
                                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] ⚠️ Позиция закрыта")
                                break
                    except Exception as e:
                        # Если не удалось получить позиции, используем последнюю известную цену
                        pass
                    
                    # Расчеты PnL
                    pnl_pct = ((current_price - entry_price) / entry_price) * 100
                    pnl_with_leverage = pnl_pct * leverage
                    
                    # Расчет расстояний
                    sl_distance_pct = ((current_price - stop_loss) / current_price) * 100
                    tp_distance_pct = ((take_profit - current_price) / current_price) * 100
                    
                    update_count += 1
                    timestamp = datetime.now().strftime('%H:%M:%S')
                    
                    # Статус
                    if current_price >= take_profit:
                        status = "✅ TP ДОСТИГНУТ"
                        color = "\033[92m"  # Зеленый
                        reset = "\033[0m"
                    elif current_price <= stop_loss:
                        status = "❌ SL СРАБОТАЛ"
                        color = "\033[91m"  # Красный
                        reset = "\033[0m"
                    elif pnl_pct > 0:
                        status = "🟢 В ПРИБЫЛИ"
                        color = "\033[92m"
                        reset = "\033[0m"
                    else:
                        status = "🔴 В УБЫТКЕ"
                        color = "\033[91m"
                        reset = "\033[0m"
                    
                    # Вывод информации
                    print(f"{color}[{timestamp}] #{update_count} | "
                          f"Price: ${current_price:.2f} | "
                          f"PnL: {pnl_pct:.4f}% ({pnl_with_leverage:.2f}% с {leverage}x) | "
                          f"SL: {sl_distance_pct:.4f}% | TP: {tp_distance_pct:.4f}% | "
                          f"{status}{reset}")
                    
                    # Проверка достижения TP/SL
                    if current_price >= take_profit:
                        print(f"\n{color}🎉 TAKE PROFIT ДОСТИГНУТ! Цена: ${current_price:.2f}{reset}")
                        print(f"   Прибыль: {pnl_with_leverage:.2f}% с {leverage}x leverage")
                        break
                    elif current_price <= stop_loss:
                        print(f"\n{color}⚠️ STOP LOSS СРАБОТАЛ! Цена: ${current_price:.2f}{reset}")
                        print(f"   Убыток: {pnl_with_leverage:.2f}% с {leverage}x leverage")
                        break
                
                await asyncio.sleep(10)
                
            except KeyboardInterrupt:
                print(f"\n\n⏹️ Мониторинг остановлен пользователем")
                if last_price:
                    pnl_pct = ((last_price - entry_price) / entry_price) * 100
                    pnl_with_leverage = pnl_pct * leverage
                    print(f"   Последняя цена: ${last_price:.2f}")
                    print(f"   Текущий PnL: {pnl_pct:.4f}% ({pnl_with_leverage:.2f}% с {leverage}x)")
                break
            except Exception as e:
                print(f"\n⚠️ Ошибка при обновлении: {e}")
                await asyncio.sleep(10)
    
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(monitor_position())

