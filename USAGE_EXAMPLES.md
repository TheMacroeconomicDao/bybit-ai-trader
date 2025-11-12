# 💬 Примеры Использования AI Trading Agent

## Базовые Команды

### 1. Быстрая Проверка BTC

```
Вы: "Как BTC?"

AI: 
📊 BTC: $50,250 (+1.2% за 24h)
📈 Trend: Uptrend на 1h, консолидация на 4h
🎯 RSI: 56 (нейтральный, здоровый)
💡 Ближайшая поддержка: $49,800 (EMA50)
   Сопротивление: $51,000

Вывод: Стабилен, небольшой uptrend. Безопасно для alt longs.
```

### 2. Обзор Рынка

```
Вы: "Дай обзор рынка"

AI:
🔍 MARKET OVERVIEW 14:30 UTC

🔸 BTC: $50,250 (+1.2%)
   Trend: Moderate uptrend
   Влияние: Позитивное

📈 SENTIMENT: Умеренно Бычий
   Green: 58% активов
   Red: 42% активов

🔝 TOP GAINERS:
   1. SOL: +8.5% ($145.50) vol $450M
   2. AVAX: +6.2% ($38.20) vol $280M
   3. MATIC: +5.8% ($0.85) vol $320M

💡 Market в good condition для selective longs
```

### 3. Поиск Возможностей

```
Вы: "Найди точки входа на рост"

AI:
[Проводит полный анализ через MCP tools]

🎯 НАЙДЕНО 2 КАЧЕСТВЕННЫХ ВОЗМОЖНОСТИ

━━━━ ВОЗМОЖНОСТЬ #1 ━━━━

💎 ETH/USDT
💵 $3,045 (+1.5%)

💡 ПОЧЕМУ:
Trend Following pullback к EMA50 на 4h в сильном uptrend.
Все таймфреймы aligned bullish. Формируется Hammer у support.
Volume spike на reversal. BTC поддерживает.

🔍 CONFLUENCE: 8.5/10 ✅
   [Детальный breakdown]

📊 ВЕРОЯТНОСТЬ: 73%

⚡ ПЛАН:
Entry: $3,050
SL: $2,970 (риск $80)
TP: $3,210 (reward $160)
R:R: 1:2
Position: 0.0075 ETH (риск $0.60 = 2%)
Safe time: 8 hours

⚠️ РИСКИ:
1. BTC rejection от $51k → exit
2. Volume dries up → exit
3. No progress в 4h → evaluate

✅ РЕКОМЕНДАЦИЯ: ОТКРЫВАТЬ
Отличный setup, высокая вероятность!

━━━━ ВОЗМОЖНОСТЬ #2 ━━━━

[Аналогичный детальный breakdown]

🤔 Готов открывать?
```

---

## Workflow Сценарии

### Сценарий A: Быстрый Скальп

```
10:15 Вы: "Найди quick scalp на 15m"

AI: [Анализирует]
"⚡ SCALP OPPORTUNITY: BTC

Setup: Momentum entry после breakout
TF: 15m
Entry: $50,550
SL: $50,450
TP: $50,750
R:R: 1:2
Safe time: 45 минут MAX

Confluence: 7.5/10 (moderate но fast setup)
Probability: 68%

Note: Quick trade, requires active monitoring!"

Вы: "Открываю на Bybit вручную"
    [открываете]
    
Вы: "Открыл в $50,560"

AI: "✅ Позиция зафиксирована!

Мониторю:
⏱️ 10:20 | +0.15% ($50,635)
⏱️ 10:35 | +0.32% ($50,720) - near TP
⏱️ 10:42 | TP HIT! $50,750 ✅

Рекомендую закрыть. Profit: +0.34% ($0.20)

Хорошая quick trade! 👍"
```

### Сценарий B: Свинг Позиция

```
Monday 09:00 Вы: "Найди хороший swing trade на неделю"

AI: [Полный анализ]
"🎯 SWING OPPORTUNITY: SOL/USDT

Setup: Breakout из 2-недельной consolidation
TF: 4h основной, 1d confirmation
Confluence: 9.0/10 ✅✅
Probability: 76%

Entry: $146.00
SL: $141.50 (риск $4.50)
TP1 (60%): $155.00 (R:R 1:2)
TP2 (40%): $164.00 (R:R 1:4)

Position: 0.2 SOL (risk $0.90 = 3% но для swing OK)
Safe time: 48 hours
Max time: 72 hours

Perfect Storm setup! Очень высокая вероятность!"

Вы: "Открывай"

AI: "⚠️ Режим READ-ONLY. Открой вручную:
- Symbol: SOL/USDT
- Side: Buy
- Qty: 0.2 SOL
- SL: $141.50
- TP1: $155.00 (60%)
- TP2: $164.00 (40%)

Сообщи когда исполнено, начну мониторинг."

Вы: "Исполнено в $146.20"

AI: "✅ Позиция активна! Начинаю мониторинг.

Updates каждые 2-4 часа."

[Через 6 часов]
AI: "⏱️ 15:00 | SOL Update
💰 +2.8% ($150.30) ✅
Progress: 46% к TP1
Indicators: Все bullish
Action: HOLD"

[Через 14 часов]
AI: "⏱️ 23:00 | SOL Update
💰 +5.9% ($154.80) - NEAR TP1! 🎯
SL moved to $147.50 (breakeven) ✅
Action: Готовь partial exit"

[Через 18 часов]
AI: "⏱️ 03:00 | SOL TP1 HIT!
💰 $155.10 ✅

Рекомендую:
- Close 60% СЕЙЧАС
- Trail remaining 40% с 3% trailing

Отличная работа! Secured profit $1.80 на 60%"

[Через 36 часов]
AI: "⏱️ 21:00 | SOL TP2 HIT!
💰 $164.50 ✅

Trailing stop triggered на оставшихся 40%.

FINAL:
- 60% closed @ $155: +6.0%
- 40% closed @ $164.50: +12.5%
- Average: +8.5%
- Total profit: $2.94 на $30 position

EXCELLENT SWING! 🚀"
```

---

## Специальные Команды

### Валидация Вашей Идеи

```
Вы: "Хочу short ETH на $3,100, как думаешь?"

AI: [Анализирует через MCP]

"🔍 ВАЛИДАЦИЯ: ETH Short @ $3,100

[Полный технический анализ]

❌ НЕ РЕКОМЕНДУЮ

Причины:
1. Все таймфреймы показывают uptrend
2. RSI только 58 (не overbought)
3. BTC растёт (+1.5%)
4. Нет reversal patterns
5. Confluence для short: только 3.5/10

Против strong uptrend = low probability (35%)

Alternative: Подожди pullback для LONG
Или дождись clear reversal signals для short.

Сейчас short = counter-trend = risky! ⚠️"
```

### Проверка Открытых Позиций

```
Вы: "Как мои позиции?"

AI: [Использует get_positions()]

"📊 ОТКРЫТЫЕ ПОЗИЦИИ (2)

1. ETH Long:
   Entry: $3,000 | Current: $3,085
   P/L: +2.8% ($0.84) ✅
   Time: 4.5h / 8h safe
   Status: 🟢 Healthy, на пути к TP
   Action: SL moved to BE, continue holding

2. SOL Long:  
   Entry: $146 | Current: $148.50
   P/L: +1.7% ($0.34) ✅
   Time: 2h / 12h safe
   Status: 🟢 Good start
   Action: Monitoring, no actions yet

💰 TOTAL P/L: +3.9% ($1.18)
📊 Portfolio Risk: 0% (both в breakeven)

All positions здоровые, продолжаем hold! ✅"
```

### Ежедневная Утренняя Рутина

```
Вы: "Доброе утро! Что сегодня на рынке?"

AI: [Morning routine из protocol]

"🌅 УТРЕННИЙ АНАЛИЗ РЫНКА

📊 BTC: $50,450 (+0.8% за ночь)
   Trend: Consolidating $49.5k-$51k
   Bias: Neutral, ждём breakout

📈 MARKET REGIME: RANGING → BREAKOUT PENDING
   ADX: 18 (weak trend, consolidation)
   BB Squeeze: Forming ✅
   Volatility: Low → expect spike soon

🎯 СТРАТЕГИЯ НА СЕГОДНЯ:
Breakout Strategy - wait для resolution

📋 WATCHLIST (Top 3):
1. BTC - squeeze, ready для breakout
2. ETH - following BTC
3. SOL - independent strength

⏰ KEY TIMES TODAY:
- 14:00 UTC: Usually breakout time
- 20:00 UTC: US market most active

💡 PLAN:
Wait для BTC breakout direction.
Then trade alts в том же direction.
Estimated: 4-6 hours до clarity.

Буду monitoring и сообщу когда setup formed! 📊"
```

---

## Продвинутое Использование

### Детальный Анализ Конкретного Актива

```
Вы: "Глубокий анализ AVAX на всех таймфреймах"

AI: [Использует множественные MCP calls]

"═══════════════════════════════════════
ГЛУБОКИЙ АНАЛИЗ: AVAX/USDT
═══════════════════════════════════════

📊 MULTI-TIMEFRAME:

1D (Primary):
• Trend: Uptrend (EMA aligned)
• Pattern: Ascending Triangle forming
• Key: Resistance $40, Support $36

4H (Intermediate):
• Trend: Strong uptrend
• ADX: 32 (strong)
• RSI: 62 (momentum good)
• Volume: Rising

1H (Entry):
• Trend: Pullback к EMA20
• Current: $38.15 (at EMA20)
• Hammer forming ✅
• Volume: 1.7x spike

15M (Timing):
• Bullish Engulfing confirmed
• Entry ready

📈 ИНДИКАТОРЫ SUMMARY:
• RSI: Bullish (>50, rising)
• MACD: Bullish crossover 8h ago
• BB: Middle band support
• EMA: Perfect alignment
• Volume: Strong confirmation

🎯 ПАТТЕРНЫ:
• Daily: Ascending Triangle (75% success)
• 1h: Hammer (65% success)
• 15m: Bullish Engulfing (70% success)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CONFLUENCE: 8.5/10 ✅✅
ВЕРОЯТНОСТЬ: 74%
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚡ TRADING PLAN:

Entry: $38.20
SL: $37.50 (ниже EMA20 + buffer)
TP: $39.60 (R:R 1:2)

[Полный план как в примерах выше]

✅ СИЛЬНАЯ ВОЗМОЖНОСТЬ!
═══════════════════════════════════════"
```

### Сравнение Множественных Активов

```
Вы: "Сравни ETH, SOL и AVAX - что лучше?"

AI:
"⚖️ COMPARATIVE ANALYSIS

━━━━ ETH/USDT ━━━━
Confluence: 8.0/10
Probability: 70%
R:R: 1:2
Setup: Trend following
Strength: 💪 Strong

━━━━ SOL/USDT ━━━━
Confluence: 9.0/10
Probability: 75%
R:R: 1:2.5
Setup: Breakout
Strength: 💪💪 Very Strong

━━━━ AVAX/USDT ━━━━
Confluence: 7.5/10
Probability: 67%
R:R: 1:2
Setup: Mean reversion
Strength: 💪 Moderate

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RANKING:
1st: SOL ⭐⭐⭐ (best confluence + probability)
2nd: ETH ⭐⭐ (solid, lower risk)
3rd: AVAX ⭐ (acceptable но lowest)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 РЕКОМЕНДАЦИЯ:
Focus на SOL как primary (если открываешь 1)
Или SOL + ETH если хочешь 2 позиции (diversification)
AVAX skip пока или wait для better setup.

Что выбираешь?"
```

---

## Управление Позициями

### Check Progress

```
[Позиция открыта 2 часа назад]

Вы: "Как ETH?"

AI: [get_ticker("ETHUSDT")]

"⏱️ 16:30 | ETH Long Update

💰 P/L: +1.8% ($0.54)
📊 Current: $3,054 (Entry: $3,000)

Progress: 34% к TP (2h / 8h safe window)

📈 Indicators:
• RSI: 56 → 59 (strengthening) ✅
• MACD: Histogram growing ✅
• Volume: 1.3x avg (good) ✅

🎯 Status: 🟢 Healthy - ahead of schedule

▶️ Action: HOLD
Soon approaching 1:1 R:R ($3,080)
Will move SL to breakeven then.

Next update: 17:30 или когда достигнем BE"
```

### Emergency Situation

```
[BTC резко падает]

AI: [Автоматически проверяет через get_ticker]

"🚨 ALERT: BTC Sharp Drop!

BTC: $50,200 → $49,250 (-1.9% за 15 минут)

Impact на твои позиции:
• ETH: $3,085 → $3,020 (profit +2.8% → +0.7%)
• SOL: $148 → $145 (profit +1.7% → -0.7%)

⚠️ РЕКОМЕНДУЮ:

ETH: 
• Exit 50% СЕЙЧАС (secure $0.40 profit)
• Tighten SL на remaining to $3,010 (near BE)

SOL:
• EXIT полностью (protect capital)
• Small loss лучше чем bigger loss

Reason: BTC leading indicator. 
Когда BTC падает sharp, alts usually follow harder.
Лучше secure что можем и wait для clarity.

Exit сейчас или нет?"
```

---

## Обучающие Диалоги

### Объяснение Индикаторов

```
Вы: "Объясни почему RSI важен"

AI: [Читает technical_indicators_guide.md]

"📚 RSI (Relative Strength Index) - Почему Важен:

RSI измеряет СИЛУ движения цены, не просто direction.

Почему это критично:
• Цена может расти, но momentum слабеет (divergence)
• RSI покажет это РАНЬШЕ чем цена развернётся
• Даёт leading signals

Как использую для trading:
1. Oversold (<30) у поддержки = strong buy signal
   (Probability 70-75% с подтверждением)

2. Divergence - самый сильный signal:
   Price higher high, RSI lower high = reversal coming
   (Probability 75-80%)

3. Crossover 50 level:
   RSI >50 = bullish momentum confirmed
   RSI <50 = bearish momentum

Для крипто:
• Oversold: <25 (не 30!)
• Overbought: >75 (не 70!)
• Reason: Крипто более volatile

Комбинирую с:
• Volume (подтверждение)
• MACD (momentum check)
• BB (price position)
• S/R levels (context)

Never торгую только по RSI!
Minimum 3-4 индикатора должны confirm.

Questions?"
```

### Разбор Ошибки

```
Вы: "Вошёл в ETH long на $3,100, теперь $3,050. Что делать?"

AI: [Анализирует текущую ситуацию]

"Давай разберём situation:

[get_ticker для current price]
[get_kline для context]

📊 ТЕКУЩАЯ СИТУАЦИЯ:

Entry: $3,100
Current: $3,050
Loss: -1.6% (-$0.48 если $30 position)

Был ли SL установлен?

[Если ДА, SL $3,020:]
"✅ Good! SL есть.

Анализ:
• RSI: 45 (neutral, может recover)
• Support: $3,040 (EMA50)
• Volume: declining (worrying)

Recommendation:
1. If SL логично установлен ($3,020) - ДЕРЖИ
   Risk определён, может recover
   
2. Watch closely следующие 2 hours
3. If пробили $3,040 без bounce - SL сработает (правильно)

Don't move SL дальше! Accept loss если hit."

[Если НЕТ SL:]
"❌ ПРОБЛЕМА: Нет Stop-Loss!

Это нарушение rule #1!

IMMEDIATE ACTION:
Set SL СЕЙЧАС на $3,020
(Limit loss на -2.6% = $0.78)

Why важно:
• Без SL risk неограничен
• Может упасть к $2,900 = -6.5% loss
• $30 → $28 → $26 очень быстро
  
Lesson learned:
ВСЕГДА set SL immediately после entry.
No exceptions! 

Set SL сейчас и держи plan!"

[Общий совет:]
"💡 Analysis ошибки:

Возможные причины:
• Вход без полного confluence?
• Против trend на higher TF?
• No volume confirmation?
• Bad timing?

Для future:
• Always use confluence scoring ≥8/10
• Always set SL before entry
• Accept small losses быстро
• Move on к next opportunity

Market даст новые chances! 
Don't revenge trade. 
Learn и improve! 💪"
```

---

## Специальные Запросы

### Education Request

```
Вы: "Научи меня как читать Bollinger Bands"

AI: [Читает indicators guide]

"📚 BOLLINGER BANDS - Полное Руководство:

[Детальное объяснение с примерами]
[Визуализация в текстовом формате]
[Практические примеры торговли]
[Комбинации с другими индикаторами]

Хочешь я найду example на реальном current market?"
```

### Strategy Question

```
Вы: "Когда лучше использовать Trend Following vs Breakout?"

AI: [Читает entry_strategies.md]

"⚖️ TREND FOLLOWING vs BREAKOUT:

Trend Following (75-80% win rate):
Когда использовать:
• ADX > 25 (есть established trend)
• Clear EMA alignment
• Price делает higher highs
• BTC trending же direction

Example текущий: [если есть]

Breakout (70-75% win rate):
Когда использовать:
• ADX < 20 (no trend, consolidation)
• BB Squeeze (low volatility)
• Price в tight range 10+ свечей
• Volume declining (energy accumulating)

Example текущий: [если есть]

Сейчас market:
[Анализирует current regime]
→ Рекомендую: [какую стратегию]

Questions?"
```

---

## Полный Пример Сессии

```
═══════════════════════════════════════
TRADING SESSION: Monday Morning
═══════════════════════════════════════

09:00 Вы: "Проведи утренний анализ"

AI: [Morning routine]
"🌅 УТРЕННИЙ ОБЗОР...
[Детальный анализ]
Watchlist: BTC, ETH, SOL"

09:30 Вы: "Найди лучший setup"

AI: [Глубокий анализ]
"🎯 Best: ETH Trend Following
Confluence: 8.5/10
Probability: 72%
[Полный breakdown]
Готов открывать?"

09:45 Вы: "Открываю ETH long $3,000"

AI: "✅ Отлично! Мониторинг активирован"

11:00 AI: "⏱️ ETH +1.2%, все OK"

12:30 AI: "⏱️ ETH +2.6%, SL → BE ✅"

14:00 AI: "🎯 ETH TP1 hit! Рекомендую 60% close"

14:05 Вы: "Закрыл 60%"

AI: "Perfect! Trail remaining 40%"

16:30 AI: "⏱️ Trail triggered $3,180
Вся позиция закрыта
Profit: +2.8% avg ($0.84)
Excellent execution! 🎉"

17:00 Вы: "Что дальше?"

AI: [Новый scan]
"Ищу next opportunity...
[Analysis]
Сейчас 2 moderate setups (7/10)
Recommend: wait для stronger signal
или можешь review и decide"

═══════════════════════════════════════
SESSION SUMMARY:
1 trade, 1 win, +2.8%
Clean execution, good discipline!
═══════════════════════════════════════
```

---

## Краткая Справка Команд

**Анализ:**
- "Как BTC?" - быстрая проверка
- "Обзор рынка" - market overview
- "Найди точки входа" - полный scan
- "Анализируй [SYMBOL]" - детальный анализ актива
- "Сравни [SYM1] и [SYM2]" - comparison

**Позиции:**
- "Как позиции?" - check all
- "Как [SYMBOL]?" - check конкретную
- "Что с [SYMBOL]?" - update
- "Exit [SYMBOL]?" - должен ли выходить

**Обучение:**
- "Объясни [индикатор/паттерн/стратегию]"
- "Почему [вопрос]?"
- "Как торговать [setup]?"
- "Научи [topic]"

**Валидация:**
- "Хочу [action], как думаешь?" - validate идею
- "Проверь этот setup" - validate
- "Стоит ли [action]?" - opinion

---

*Используйте AI как профессионального ассистента. Задавайте вопросы, учитесь, принимайте informed decisions!*
