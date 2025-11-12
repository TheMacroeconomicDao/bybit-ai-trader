# Интеграция MCP Server с Cursor

## Архитектура

Система использует готовый `bybit-mcp` (TypeScript/Node.js) для базовых функций:
- Market data (tickers, orderbook, klines)
- Account info (balance, positions, orders)
- ML-RSI и market structure analysis

## Конфигурация для Cursor

### Добавьте в Cursor Settings

Откройте настройки Cursor (Cmd+, на Mac) → найдите "MCP Servers" → добавьте:

```json
{
  "mcpServers": {
    "bybit-trading": {
      "command": "node",
      "args": ["/Users/Gyber/GYBERNATY-ECOSYSTEM/TRADER-AGENT/bybit-mcp/build/index.js"],
      "env": {
        "BYBIT_API_KEY": "V84NJog5v9bM5k6fRn",
        "BYBIT_API_SECRET": "RYZ1JeyGsWhtjigF01rKDYzq3lRbvlxvU89L",
        "BYBIT_TESTNET": "false",
        "BYBIT_TRADING_ENABLED": "false",
        "DEBUG": "false"
      }
    }
  }
}
```

**ВАЖНО:** 
- `BYBIT_TRADING_ENABLED=false` для безопасности (read-only mode)
- Измените на `true` только когда готовы к реальной торговле
- `BYBIT_TESTNET=true` для тестирования на testnet

## Доступные Tools

После настройки у AI агента будут доступны следующие инструменты:

### Рыночные Данные
- `get_ticker` - текущая цена и изменение
- `get_orderbook` - глубина рынка
- `get_kline` - свечи OHLCV
- `get_market_info` - информация о рынке
- `get_trades` - последние сделки
- `get_instrument_info` - детали инструмента

### Анализ
- `get_ml_rsi` - ML-основанный RSI
- `get_market_structure` - структура рынка
- `get_order_blocks` - зоны институциональных ордеров

### Account (требует API ключи)
- `get_wallet_balance` - баланс кошелька
- `get_positions` - открытые позиции
- `get_order_history` - история ордеров

## Проверка Работы

После добавления конфигурации:

1. Перезапустите Cursor
2. Откройте чат с AI
3. Попросите: "Используй get_ticker для проверки цены BTC"
4. AI должен вызвать MCP tool и вернуть данные

## Ограничения Текущего Setup

Bybit-mcp - READ-ONLY сервер. Для торговых операций (place_order, close_position) нужно:

Option A: Расширить bybit-mcp (добавить trading tools)
Option B: Создать отдельный Python MCP server для торговли
Option C: Использовать прямые вызовы Bybit API через Python scripts

**Рекомендация:** Начать с read-only режима для анализа, добавить торговлю после тестирования.
