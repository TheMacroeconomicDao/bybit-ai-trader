# Bybit Trading MCP Server - Документация

## Обзор

Система использует готовый `bybit-mcp` сервер с расширениями для полного функционала трейдинг-агента.

## Компоненты

### 1. bybit-mcp (Base Server)

**Что предоставляет:**
- Real-time market data
- OHLCV данные (klines)
- Orderbook depth
- Account information (balance, positions)
- ML-enhanced RSI
- Market structure analysis  
- Order blocks detection

**Путь:** `/bybit-mcp/`

### 2. Python Расширения

**Дополнительный функционал:**
- Full technical analysis engine
- Market scanning с фильтрами
- Entry validation scoring
- Position management logic

**Файлы:**
- `bybit_client.py` - Обёртка над CCXT для торговых операций
- `technical_analysis.py` - Движок индикаторов
- `market_scanner.py` - Сканер возможностей

## Доступные Tools для AI Агента

### Из bybit-mcp:

```typescript
// Market Data
get_ticker(symbol, category)
get_orderbook(symbol, category, limit)
get_kline(symbol, interval, limit)
get_market_info(category, symbol)
get_trades(symbol, category)
get_instrument_info(symbol, category)

// Advanced Analysis
get_ml_rsi(symbol, interval, knnNeighbors)
get_market_structure(symbol, interval)
get_order_blocks(symbol, interval)

// Account
get_wallet_balance(accountType, coin)
get_positions(category, symbol)
get_order_history(category, symbol)
```

### Планируемые Расширения:

```python
# Technical Analysis
analyze_asset(symbol, timeframes, include_patterns)
validate_entry(symbol, side, entry, sl, tp)
find_support_resistance(symbol, timeframe)

# Market Scanning
scan_market(criteria, limit)
find_oversold_assets(market_type, min_volume)
find_breakout_opportunities(market_type)
find_trend_reversals(market_type)

# Trading (осторожно!)
place_order(symbol, side, type, quantity, sl, tp)
close_position(symbol, reason)
modify_position(symbol, new_sl, new_tp)
```

## Использование

### Пример: Анализ Рынка

```
Пользователь: "Проанализируй текущую ситуацию с BTC"

Агент использует:
1. get_ticker("BTCUSDT", "spot") - текущая цена
2. get_kline("BTCUSDT", "60", 200) - свечи 1h
3. get_ml_rsi("BTCUSDT", "60") - ML-RSI анализ
4. get_market_structure("BTCUSDT", "240") - структура на 4h

Агент анализирует и выдаёт заключение
```

### Пример: Поиск Возможностей

```
Пользователь: "Найди перепроданные активы с хорошим потенциалом роста"

Агент использует:
1. get_market_info("spot") - все активы
2. get_ticker() для каждого - текущие цены
3. get_ml_rsi() для топ кандидатов - проверка oversold
4. get_kline() - подтверждение паттернов

Агент выдаёт 2-3 лучших возможности с обоснованием
```

## Безопасность

**Текущий режим: READ-ONLY** ✅

- API ключи имеют read-only permissions
- `BYBIT_TRADING_ENABLED=false`
- Невозможно открывать/закрывать позиции
- Безопасно для тестирования и анализа

**Для включения торговли:**

1. Создайте NEW API key на Bybit с trading permissions
2. Обновите .env файл
3. Установите `BYBIT_TRADING_ENABLED=true`
4. ТЕСТИРУЙТЕ на testnet СНАЧАЛА

## Тестирование

### Тест 1: Проверка Подключения

```bash
cd /Users/Gyber/GYBERNATY-ECOSYSTEM/TRADER-AGENT/bybit-mcp
node build/index.js
```

Должно запуститься без ошибок.

### Тест 2: Проверка Tools в Cursor

В Cursor попросите AI:
```
"Используй get_ticker чтобы узнать текущую цену Bitcoin"
```

AI должен вызвать tool и вернуть данные.

### Тест 3: Проверка Account

```
"Покажи мой текущий баланс на Bybit"
```

AI использует get_wallet_balance и показывает баланс.

## Troubleshooting

### Проблема: MCP сервер не запускается

**Решение:**
```bash
cd bybit-mcp
npm run build
node build/index.js
```

Проверьте errors в output.

### Проблема: API authentication failed

**Решение:**
- Проверьте API ключи в .env
- Убедитесь что ключи active на Bybit
- Проверьте IP whitelist settings

### Проблема: Tools не видны в Cursor

**Решение:**
- Перезапустите Cursor полностью
- Проверьте конфигурацию MCP в settings
- Проверьте путь к build/index.js корректен

## Следующие Шаги

1. ✅ bybit-mcp установлен и настроен
2. ✅ База знаний создана
3. ⏳ Создать system prompts
4. ⏳ Протестировать в Cursor
5. ⏳ Добавить trading capabilities (опционально)

## Ресурсы

- [bybit-mcp GitHub](https://github.com/sammcj/bybit-mcp)
- [Bybit API Docs](https://bybit-exchange.github.io/docs/)
- [MCP Protocol](https://modelcontextprotocol.io/)
