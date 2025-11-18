# Исправление: Поиск в обе стороны (LONG и SHORT)

## Проблема

Анализатор искал **только LONG позиции**, даже когда рынок был медвежий. Это происходило потому что:

1. ❌ Не было функции `find_overbought_assets()` для поиска SHORT возможностей
2. ❌ `_generate_entry_plan()` всегда генерировал план для LONG (SL ниже, TP выше)
3. ❌ `_calculate_opportunity_score()` давал отрицательный score для SELL сигналов (неправильно для шортов)
4. ❌ Протокол анализа не учитывал market regime при выборе направления поиска

## Исправления

### 1. Добавлена функция `find_overbought_assets()`

**Файл:** `mcp_server/market_scanner.py`

```python
async def find_overbought_assets(
    self,
    market_type: str = "spot",
    min_volume_24h: float = 1000000
) -> List[Dict[str, Any]]:
    """
    Найти перекупленные активы (RSI > 70) для SHORT позиций
    """
```

- Ищет активы с RSI > 70 (строгие критерии)
- Fallback на RSI > 65 если мало результатов
- Возвращает список активов готовых для SHORT

### 2. Исправлен `_generate_entry_plan()`

**Было:**
```python
# Всегда LONG
stop_loss = current_price - (atr * 2)
take_profit = current_price + (atr * 4)
```

**Стало:**
```python
# Определяет направление по сигналу
if is_short:
    # SHORT: SL выше цены, TP ниже цены
    stop_loss = current_price + (atr * 2)
    take_profit = current_price - (atr * 4)
    side = "short"
else:
    # LONG: SL ниже цены, TP выше цены
    stop_loss = current_price - (atr * 2)
    take_profit = current_price + (atr * 4)
    side = "long"
```

Теперь возвращает поле `"side"` указывающее направление позиции.

### 3. Исправлен `_calculate_opportunity_score()`

**Было:**
```python
elif composite.get('signal') == 'STRONG_SELL':
    score -= 2.5  # ❌ Неправильно для шортов!
elif composite.get('signal') == 'SELL':
    score -= 1.5  # ❌ Неправильно для шортов!
```

**Стало:**
```python
elif signal == 'STRONG_SELL':
    score += 2.5  # ✅ Для шортов STRONG_SELL это хорошо!
elif signal == 'SELL':
    score += 1.5  # ✅ Для шортов SELL это хорошо!
```

Теперь SELL сигналы дают положительный score для SHORT позиций.

### 4. Добавлен Tool в MCP сервер

**Файл:** `mcp_server/full_server.py`

Добавлен новый Tool:
```python
Tool(
    name="find_overbought_assets",
    description="Найти перекупленные активы (RSI >70) для SHORT позиций",
    ...
)
```

### 5. Обновлен протокол анализа

**Файлы:**
- `prompts/market_analysis_protocol.md`
- `prompts/agent_core_instructions.md`

**Добавлено:**
- Инструкция всегда искать в ОБЕ СТОРОНЫ
- Приоритет SHORT в медвежьем рынке
- Приоритет LONG в бычьем рынке
- Но не игнорировать противоположное направление

## Как использовать

### Пример анализа с учетом market regime:

```python
# 1. Определить market regime
btc_structure = await get_market_structure("BTCUSDT", "240")
market_regime = btc_structure["marketRegime"]  # trending_down/trending_up/ranging

# 2. Параллельно искать в обе стороны
tasks = [
    find_oversold_assets(market_type="spot"),      # LONG
    find_overbought_assets(market_type="spot"),    # SHORT
    scan_market({"max_rsi": 35}, limit=50),        # LONG
    scan_market({"min_rsi": 65}, limit=50),        # SHORT
]

results = await asyncio.gather(*tasks)

# 3. Приоритизировать по market regime
if market_regime == "trending_down":
    # Приоритет SHORT, но не игнорируй LONG
    short_opportunities = results[1] + results[3]
    long_opportunities = results[0] + results[2]
elif market_regime == "trending_up":
    # Приоритет LONG, но не игнорируй SHORT
    long_opportunities = results[0] + results[2]
    short_opportunities = results[1] + results[3]
else:
    # Ranging - равномерно
    all_opportunities = results[0] + results[1] + results[2] + results[3]
```

## Результат

Теперь анализатор:
- ✅ Ищет LONG и SHORT позиции
- ✅ Учитывает market regime при приоритизации
- ✅ Правильно генерирует entry plans для обоих направлений
- ✅ Правильно считает score для обоих направлений
- ✅ Возвращает поле `"side"` в entry_plan

## Тестирование

После этих изменений анализатор должен:
1. Находить SHORT возможности в медвежьем рынке
2. Находить LONG возможности в бычьем рынке
3. Находить возможности в обе стороны в ranging рынке
4. Правильно генерировать SL/TP для обоих направлений

---

**Дата исправления:** 2025-11-17  
**Версия:** 1.1

