#!/usr/bin/env python3
"""
MCP Position Monitor - Мониторинг позиций через MCP инструменты
Выводит информацию в чат для принятия решений
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any, Optional

# Импортируем MCP клиент
import sys
from pathlib import Path

# Добавляем путь к mcp_server
sys.path.insert(0, str(Path(__file__).parent / "mcp_server"))

from trading_operations import TradingOperations


class PositionMonitor:
    """Мониторинг позиций через MCP"""
    
    def __init__(self):
        self.api_key = 'V84NJog5v9bM5k6fRn'
        self.api_secret = 'RYZ1JeyGsWhtjigF01rKDYzq3lRbvlxvU89L'
        self.trading = TradingOperations(
            api_key=self.api_key,
            api_secret=self.api_secret,
            testnet=False
        )
        self.last_positions = {}
    
    def get_positions(self) -> Dict[str, Any]:
        """Получить открытые позиции через MCP"""
        try:
            response = self.trading.session.get_positions(category="linear")
            
            if response.get('retCode') == 0:
                positions_list = response.get('result', {}).get('list', [])
                
                positions = {}
                for pos in positions_list:
                    size = float(pos.get('size', 0))
                    if size > 0:
                        symbol = pos.get('symbol', '')
                        positions[symbol] = {
                            'symbol': symbol,
                            'side': pos.get('side', ''),
                            'size': size,
                            'entry_price': float(pos.get('avgPrice', 0)),
                            'mark_price': float(pos.get('markPrice', 0)),
                            'leverage': pos.get('leverage', 'N/A'),
                            'unrealized_pnl': float(pos.get('unrealisedPnl', 0)),
                            'stop_loss': float(pos.get('stopLoss', 0)) if pos.get('stopLoss') else None,
                            'take_profit': float(pos.get('takeProfit', 0)) if pos.get('takeProfit') else None,
                            'liq_price': float(pos.get('liqPrice', 0)) if pos.get('liqPrice') else None,
                        }
                
                return positions
            else:
                return {}
        except Exception as e:
            print(f"❌ Ошибка получения позиций: {e}")
            return {}
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """Получить текущую цену"""
        try:
            ticker = self.trading.session.get_tickers(category="linear", symbol=symbol)
            if ticker.get('retCode') == 0:
                return float(ticker['result']['list'][0]['lastPrice'])
        except:
            pass
        return None
    
    def format_position_info(self, pos: Dict[str, Any], current_price: float) -> str:
        """Форматировать информацию о позиции для вывода"""
        entry = pos['entry_price']
        pnl_pct = ((current_price - entry) / entry) * 100
        leverage_val = float(pos['leverage']) if isinstance(pos['leverage'], (int, float)) else 1
        pnl_with_leverage = pnl_pct * leverage_val
        
        # Статус
        if pos.get('take_profit') and current_price >= pos['take_profit']:
            status = "🎉 TP ДОСТИГНУТ"
        elif pos.get('stop_loss') and current_price <= pos['stop_loss']:
            status = "⚠️ SL СРАБОТАЛ"
        elif pnl_pct > 0:
            status = "🟢 В ПРИБЫЛИ"
        else:
            status = "🔴 В УБЫТКЕ"
        
        info = f"""
📊 ПОЗИЦИЯ: {pos['symbol']} {pos['side']}
   💰 Цена: ${current_price:.2f} | Entry: ${entry:.2f}
   💵 PnL: ${pos['unrealized_pnl']:.4f} ({pnl_pct:.4f}% / {pnl_with_leverage:.2f}% с {leverage_val}x)
   📏 Размер: {pos['size']} контрактов | Leverage: {pos['leverage']}x"""
        
        if pos.get('stop_loss'):
            sl_dist = ((current_price - pos['stop_loss']) / current_price) * 100
            info += f"\n   🛡️ SL: ${pos['stop_loss']:.2f} (расстояние: {sl_dist:.4f}%)"
        
        if pos.get('take_profit'):
            tp_dist = ((pos['take_profit'] - current_price) / current_price) * 100
            info += f"\n   🎯 TP: ${pos['take_profit']:.2f} (расстояние: {tp_dist:.4f}%)"
        
        if pos.get('liq_price'):
            info += f"\n   ⚠️ Liq Price: ${pos['liq_price']:.2f}"
        
        info += f"\n   {status}"
        
        return info
    
    def monitor(self, interval: int = 30):
        """Запустить мониторинг"""
        print("=" * 80)
        print("📊 МОНИТОРИНГ ПОЗИЦИЙ ЧЕРЕЗ MCP")
        print("=" * 80)
        print(f"Обновление каждые {interval} секунд")
        print("WebUI доступен: http://localhost:8081")
        print()
        
        update_count = 0
        
        while True:
            try:
                update_count += 1
                timestamp = datetime.now().strftime('%H:%M:%S')
                
                # Получаем позиции через MCP
                positions = self.get_positions()
                
                print(f"\n[{timestamp}] Обновление #{update_count}")
                print("-" * 80)
                
                if positions:
                    print(f"✅ Найдено позиций: {len(positions)}")
                    print()
                    
                    for symbol, pos in positions.items():
                        current_price = self.get_current_price(symbol)
                        if current_price:
                            info = self.format_position_info(pos, current_price)
                            print(info)
                            print()
                            
                            # Проверка критических событий
                            if pos.get('take_profit') and current_price >= pos['take_profit']:
                                print("🎉 TAKE PROFIT ДОСТИГНУТ!")
                            elif pos.get('stop_loss') and current_price <= pos['stop_loss']:
                                print("⚠️ STOP LOSS СРАБОТАЛ!")
                else:
                    print("⚠️ Открытых позиций нет")
                    print()
                    print("💡 Мониторинг продолжается...")
                    print("   Новые позиции будут отображаться автоматически")
                
                print("-" * 80)
                
                # Сохраняем состояние
                self.last_positions = positions
                
                await asyncio.sleep(interval)
                
            except KeyboardInterrupt:
                print("\n\n⏹️ Мониторинг остановлен")
                break
            except Exception as e:
                print(f"\n⚠️ Ошибка: {e}")
                await asyncio.sleep(interval)


async def main():
    monitor = PositionMonitor()
    await monitor.monitor(interval=30)


if __name__ == "__main__":
    asyncio.run(main())

