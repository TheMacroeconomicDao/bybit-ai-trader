# 🔍 DEEP SYSTEM AUDIT & FIX PROMPT

**Objective:** Найти и устранить ВСЕ оставшиеся проблемы в системе для максимальной эффективности

---

## 🎯 ТЕКУЩИЕ ПРОБЛЕМЫ

### 1. ❌ USDE/USDT проходит через фильтр
**Факт:** USDE/USDT (стейбл пара) отображается в отчете со score 7.0  
**Ожидание:** Должна быть отфильтрована  
**Reason:** USDE не в списке стейблкоинов

### 2. ⚪ "Unknown" tier для USDE/USDT
**Факт:** USDE/USDT показывает "Unknown" tier вместо классификации  
**Ожидание:** Должна быть корректная tier классификация ИЛИ фильтрация  
**Impact:** Confusion для пользователя

---

## 📋 ЗАДАЧИ ДЛЯ АУДИТА

### TASK 1: Trace фильтрации стейбл пар

**Действия:**
1. Прочитать [`autonomous_agent/autonomous_analyzer.py`](autonomous_agent/autonomous_analyzer.py) метод `_scan_all_opportunities`
2. Проверить где ИМЕННО применяется `_is_stable_stable_pair()`
3. Проверить [`mcp_server/market_scanner.py`](mcp_server/market_scanner.py) - применяется ли там фильтр?
4. Проверить [`autonomous_agent/detailed_formatter.py`](autonomous_agent/detailed_formatter.py) - применяется ли там фильтр?

**Найти:**
- В каких местах фильтр НЕ применяется но должен?
- Почему USDE проходит через фильтр?
- Какой полный список стейблкоинов нужен?
- если наш способ убрать из анализа пары стейбл/стейбл прох то  нужно разработаь качесвтенное решение этой звадачи


### TASK 2: Trace tier classification

**Действия:**
1. Прочитать [`mcp_server/tier_classifier.py`](mcp_server/tier_classifier.py) метод `classify()`
2. Прочитать [`mcp_server/market_scanner.py`](mcp_server/market_scanner.py) где вызывается tier classification
3. Проверить почему USDE/USDT получает tier="unknown"

**Найти:**
- При каких условиях tier становится "unknown"?
- Какие данные отсутствуют для USDE/USDT?
- Как это исправить?

### TASK 3: Полная проверка data flow

**Trace весь путь opportunity от начала до конца:**

```
1. market_scanner.scan_market()
   ↓
2. Фильтрация по volume/price
   ↓
3. analyze_ticker() для каждого
   ↓
4. Tier classification ← ГДЕ ЭТО?
   ↓
5. SmartDisplay.select_top_3_with_warnings()
   ↓
6. autonomous_analyzer._scan_all_opportunities()
   ↓ ФИЛЬТР _is_stable_stable_pair() ← ГДЕ ЭТО ПРИМЕНЯЕТСЯ?
   ↓
7. autonomous_analyzer.analyze_market()
   ↓ 
8. detailed_formatter.format_full_report()
   ↓ ФИЛЬТР _is_stable_stable_pair() ← ГДЕ ЭТО ПРИМЕНЯЕТСЯ?
   ↓
9. Telegram message
```

**Проверить на КАЖДОМ этапе:**
- Применяется ли фильтр стейбл пар?
- Есть ли tier classification?
- Корректны ли данные?

### TASK 4: Найти ВСЕ стейблкоины

**Действия:**
1. Прочитать реальный список всех тикеров от Bybit
2. Идентифицировать ВСЕ стейблкоины
3. Обновить списки в ОБОИХ файлах

**Известные стейблкоины:**
- USDT, USDC, BUSD, DAI, TUSD, USDP, USDD, FRAX, LUSD, MIM, RLUSD
- **USDE** (USDe from Ethena) ← MISSING!
- GUSD, USDJ, UST, USTC?
- Другие?

### TASK 5: Проверка всех фильтров

**Места где ДОЛЖЕН применяться фильтр:**
1. `market_scanner.py` - при scan_market() (ПЕРЕД tier classification)
2. `autonomous_analyzer.py` - в _scan_all_opportunities() (ПРИ объединении результатов)
3. `detailed_formatter.py` - в format_full_report() (ФИНАЛЬНАЯ проверка перед display)

**Проверить:**
- Применяется ли фильтр во ВСЕХ 3 местах?
- Если нет - ПОЧЕМУ?
- Если да - ПОЧЕМУ USDE проходит?

---

## 🔧 ИНСТРУКЦИИ ДЛЯ ИСПРАВЛЕНИЯ

### Step 1: READ ALL CRITICAL FILES

Прочитать ВСЕ файлы одновременно (эффективнее для LLM):

```xml
<read_file>
<args>
  <file><path>autonomous_agent/autonomous_analyzer.py</path></file>
  <file><path>mcp_server/market_scanner.py</path></file>
  <file><path>autonomous_agent/detailed_formatter.py</path></file>
  <file><path>mcp_server/tier_classifier.py</path></file>
  <file><path>mcp_server/smart_display.py</path></file>
</args>
</read_file>
```

### Step 2: ANALYZE DATA FLOW

Trace КАЖДЫЙ шаг от scan до display:
1. Где создается opportunity?
2. Где добавляется tier?
3. Где применяется фильтр стейбл пар?
4. Где формируется финальный список?

### Step 3: IDENTIFY ROOT CAUSES

Для КАЖДОЙ проблемы найти:
- **Root Cause:** Почему это произошло?
- **Impact:** Какие последствия?
- **Fix:** Конкретное решение с кодом

### Step 4: FIX ALL ISSUES

Применить исправления в правильном порядке:
1. Обновить список стейблкоинов (добавить USDE + все остальные)
2. Применить фильтр в нужных местах
3. Исправить tier classification если нужно
4. Проверить все edge cases

### Step 5: VERIFY FIXES

```bash
# 1. Unit tests
venv/bin/pytest tests/ -v

# 2. Integration test
venv/bin/python test_institutional_modules.py

# 3. Real scan test (локально)
venv/bin/python -c "
import asyncio
from autonomous_agent.autonomous_analyzer import AutonomousAnalyzer
import os

async def test():
    analyzer = AutonomousAnalyzer(
        qwen_api_key=os.getenv('QWEN_API_KEY'),
        bybit_api_key=os.getenv('BYBIT_API_KEY'),
        bybit_api_secret=os.getenv('BYBIT_API_SECRET')
    )
    result = await analyzer.analyze_market()
    print('LONGS:', len(result.get('all_longs', [])))
    print('SHORTS:', len(result.get('all_shorts', [])))
    for opp in result.get('all_longs', [])[:5]:
        symbol = opp.get('symbol', 'UNKNOWN')
        tier = opp.get('tier', 'unknown')
        print(f'  {symbol}: tier={tier}')
    await analyzer.close()

asyncio.run(test())
"
```

---

## 🎯 EXPECTED RESULTS

### После всех исправлений:

**1. Фильтрация стейбл пар:**
```
✅ USDE/USDT - EXCLUDED
✅ RLUSD/USDT - EXCLUDED
✅ USDC/USDT - EXCLUDED
✅ USDT/TRY - EXCLUDED
✅ BTC/USDT - INCLUDED
✅ ETH/USDT - INCLUDED
```

**2. Tier classification:**
```
✅ Все opportunities имеют tier: elite, professional, speculative, high_risk, или not_recommended
✅ НЕТ "unknown" tier
✅ Tier соответствует score и probability
```

**3. Финальный отчет:**
```
✅ Market Regime отображается
✅ Adaptive Thresholds отображаются
✅ НЕТ стейбл пар
✅ ВСЕ opportunities с правильным tier
✅ Компактный формат
✅ БЕЗ лишних символов ━
```

---

## 📊 ПОЛНЫЙ СПИСОК СТЕЙБЛКОИНОВ (для обновления)

```python
STABLECOINS = {
    # Major stablecoins
    'USDT', 'USDC', 'BUSD', 'DAI',
    
    # Centralized stablecoins
    'TUSD', 'USDP', 'USDD', 'GUSD', 'USDJ',
    
    # Algorithmic/Synthetic
    'FRAX', 'LUSD', 'MIM', 'USDE',  # ← USDE MISSING!
    
    # Ripple stablecoins
    'RLUSD',
    
    # Deprecated (но могут быть на Bybit)
    'UST', 'USTC',
    
    # Others
    'USDN', 'USDX', 'SUSD', 'CUSD'
}

FIAT_CURRENCIES = {
    'TRY', 'BRL', 'EUR', 'GBP', 'AUD', 'RUB', 
    'UAH', 'KZT', 'NGN', 'PLN', 'ARS'
}
```

---

## 🔬 DEEP DIVE QUESTIONS

### Question 1: Data Flow
**Q:** В каком ТОЧНО месте создается opportunity с tier="unknown"?  
**Method:** Trace через логи, найти строку где tier устанавливается

### Question 2: Filter Application
**Q:** Применяется ли `_is_stable_stable_pair()` в `market_scanner.py`?  
**Expected:** ДА, должен применяться ДО tier classification  
**Reality:** Проверить код

### Question 3: Tier Classification Logic
**Q:** При каких ТОЧНО условиях tier становится "unknown"?  
**Check:** Прочитать [`tier_classifier.py`](mcp_server/tier_classifier.py) line by line

### Question 4: Multiple Filters
**Q:** Сколько раз применяется фильтр стейбл пар в полном цикле?  
**Expected:** Минимум 1 раз, максимум 3 раза (market_scanner, analyzer, formatter)  
**Reality:** Проверить код

---

## ✅ COMPLETION CRITERIA

**Система считается полностью исправленной когда:**

1. ✅ **30/30 unit tests pass**
2. ✅ **Integration test pass**
3. ✅ **Real scan НЕ показывает стейбл пары**
4. ✅ **ВСЕ opportunities имеют valid tier (не "unknown")**
5. ✅ **Market Regime отображается**
6. ✅ **Adaptive Thresholds отображаются**
7. ✅ **Компактный формат без лишних символов**
8. ✅ **Production deployment successful**

---

## 🚀 EXECUTION PLAN

```bash
# 1. Прочитать все критичные файлы
<read_file> для 5 файлов одновременно

# 2. Найти root causes
Trace data flow step-by-step

# 3. Список всех проблем
- USDE/USDT issue
- Unknown tier issue
- Любые другие найденные проблемы

# 4. Исправить ВСЕ проблемы в правильном порядке
- Обновить список стейблкоинов
- Применить фильтр в нужных местах
- Исправить tier classification
- Любые другие фиксы

# 5. Проверить
- Unit tests
- Integration test
- Real scan тест
- Production deployment

# 6. Commit и deploy
- Descriptive commit message
- Update version tag
- Push to main
- Rebuild Docker
- Update Kubernetes
```

---

## 🎓 HIGH-LEVEL ANALYSIS FRAMEWORK

### Pattern Analysis:
1. **Читай КОД, НЕ документацию** - код = источник правды
2. **Trace execution path** - следуй за данными шаг за шагом
3. **Validate assumptions** - проверяй каждое предположение кодом
4. **Test each fix** - не переходи к следующему пока не проверил текущий
5. **Document findings** - записывай ВСЕ найденное

### Root Cause Analysis:
```
Symptom (что видим)
  ↓
Immediate Cause (что непосредственно вызвало)
  ↓
Root Cause (фундаментальная причина)
  ↓
Systemic Issue (почему это не было поймано раньше)
  ↓
Prevention (как предотвратить в будущем)
```

### Fix Validation:
```
1. Read code ← Понимание текущего состояния
2. Identify issue ← Точная диагностика
3. Plan fix ← Стратегия исправления
4. Apply fix ← Реализация
5. Test fix ← Локальная проверка
6. Commit ← Сохранение
7. Deploy ← Production проверка
8. Verify ← Финальная валидация
```

---

## 🔍 КОНКРЕТНЫЕ ВОПРОСЫ ДЛЯ ОТВЕТА

### О фильтрации:

1. **Где ТОЧНО вызывается `_is_stable_stable_pair()`?**
   - Найти ВСЕ вызовы в кодебазе
   - Проверить что он вызывается в нужных местах

2. **Почему USDE проходит через фильтр?**
   - USDE в списке? (должен быть)
   - Фильтр применяется ДО или ПОСЛЕ tier classification?
   - Есть ли race condition?

3. **Какой ПОЛНЫЙ список стейблкоинов на Bybit?**
   - Получить реальный список от API
   - Сравнить с нашим списком
   - Обновить если нужно

### О tier classification:

4. **Почему tier="unknown" для USDE?**
   - Какие данные отсутствуют?
   - Какая логика в tier_classifier.classify()?
   - Является ли это bug или feature?

5. **Должны ли стейбл пары иметь tier?**
   - Логический ответ: НЕТ, они должны быть отфильтрованы ДО classification
   - Текущая реальность: Проверить код

### О системной архитектуре:

6. **Правильный ли order операций?**
   ```
   Current:
   1. scan_market
   2. tier_classify
   3. filter_stable_pairs?
   
   Should be:
   1. scan_market
   2. filter_stable_pairs  ← FIRST!
   3. tier_classify
   ```

7. **Какие еще пары нужно исключить?**
   - Стейбл/Фиат (USDT/TRY)
   - Wrapped tokens (WBTC/BTC)?
   - Low volume (<1M)?

---

## 💡 СИСТЕМНОЕ МЫШЛЕНИЕ

### Принципы:

1. **Defense in Depth:**
   - Фильтр должен применяться на НЕСКОЛЬКИХ уровнях
   - Один fail - другие catch

2. **Fail Fast:**
   - Фильтрация стейбл пар должна быть ПЕРВОЙ
   - НЕ тратить время на их анализ

3. **Clear Separation:**
   - market_scanner = data acquisition
   - tier_classifier = quality assessment
   - smart_display = presentation logic
   - Каждый слой имеет свою ответственность

4. **Explicit > Implicit:**
   - Лучше 3 раза проверить чем 1 раз пропустить
   - Better redundant filter than missing filter

---

## 🎯 DELIVERABLES

После аудита создай:

1. **AUDIT_REPORT.md**
   - Все найденные проблемы
   - Root causes
   - Systemic issues

2. **FIXES_APPLIED.md**
   - Все примененные исправления
   - Код changes
   - Тесты results

3. **FINAL_VERIFICATION.md**
   - Production test results
   - Telegram output samples
   - Confirmation что ВСЕ исправлено

---

## 🚀 START COMMAND

```bash
# Начни с глубокого чтения кодебазы
# Прочитай 5 критичных файлов ОДНОВРЕМЕННО

read_file:
- autonomous_agent/autonomous_analyzer.py
- mcp_server/market_scanner.py  
- autonomous_agent/detailed_formatter.py
- mcp_server/tier_classifier.py
- mcp_server/smart_display.py

# Потом проанализируй data flow
# Найди ВСЕ проблемы
# Исправь ВСЕ проблемы
# Verify исправления
```

---

**КРИТИЧЕСКИ ВАЖНО:**

- НЕ предполагай - ПРОВЕРЯЙ код
- НЕ пропускай шаги - СЛЕДУЙ процессу
- НЕ делай частичные фиксы - ИСПРАВЛЯЙ полностью
- НЕ гадай - READ the actual code

**The fate of the system depends on your thoroughness!** 🔥