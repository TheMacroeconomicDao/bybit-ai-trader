# 📊 Framework Анализа Рынка

## Введение

Системный подход к анализу крипторынка требует структурированного framework, который учитывает multiple таймфреймы, рыночные режимы, объём и корреляции. Этот документ описывает полный процесс анализа от macro до micro уровня.

---

## MULTI-TIMEFRAME ANALYSIS (Мультитаймфреймовый Анализ)

### Философия

**"Top-Down Approach"** - анализируем от старших таймфреймов к младшим:
1. **Старшие ТФ** определяют НАПРАВЛЕНИЕ (trend)
2. **Младшие ТФ** определяют TIMING (entry точки)

**Правило:** Никогда не торгуйте против тренда старшего ТФ!

---

### Иерархия Таймфреймов

```
┌─────────────────────────────────────┐
│ 1 WEEK (1w)                         │
│ • Overall market structure          │
│ • Major S/R levels                  │
│ • Long-term trend                   │
└────────────┬────────────────────────┘
             ↓
┌─────────────────────────────────────┐
│ 1 DAY (1d)                          │
│ • Primary trend direction           │
│ • Key levels and zones              │
│ • Trend strength                    │
└────────────┬────────────────────────┘
             ↓
┌─────────────────────────────────────┐
│ 4 HOUR (4h)                         │  
│ • Intermediate trend                │ ← ОСНОВНОЙ для trend
│ • Entry зоны                        │
│ • Pattern formation                 │
└────────────┬────────────────────────┘
             ↓
┌─────────────────────────────────────┐
│ 1 HOUR (1h)                         │
│ • Short-term trend                  │ ← ОСНОВНОЙ для entry
│ • Precise entry timing              │
│ • Pattern confirmation              │
└────────────┬────────────────────────┘
             ↓
┌─────────────────────────────────────┐
│ 15 MIN (15m)                        │
│ • Fine-tune entry                   │ ← Timing точности
│ • Immediate price action            │
└────────────┬────────────────────────┘
             ↓
┌─────────────────────────────────────┐
│ 5 MIN (5m)                          │
│ • Execution timing                  │ ← Только для execution
│ • Stop-loss placement               │
└─────────────────────────────────────┘
```

---

### Процесс Top-Down Analysis

### ШАГ 1: Weekly (1w) - Macro Context

**Что смотреть:**
- Major trend direction (up/down/sideways)
- Key support/resistance zones
- Market structure (higher highs, lower lows)
- Major patterns forming

**Пример:**
```
BTC 1w chart:
• Trend: Uptrend (higher highs, higher lows)
• Current: $50,000
• Major resistance: $60,000 (previous ATH)
• Major support: $42,000 (EMA200)
• Structure: Healthy uptrend ✅

Decision: BIAS = BULLISH
Торгуем только long позиции
```

### ШАГ 2: Daily (1d) - Primary Trend

**Что смотреть:**
- Current trend direction
- EMA alignment (9, 20, 50, 200)
- Recent price action
- Volume trends

**Пример:**
```
BTC 1d chart:
• EMA alignment: Bullish (9>20>50>200) ✅
• Recent action: Consolidation $48k-$52k
• Volume: Declining (consolidation confirm)
• ADX: 22 (moderate trend)

Decision: Primary trend = UP
Ищем long opportunities на pullbacks
```

### ШАГ 3: 4-Hour (4h) - Intermediate Trend

**Что смотреть:**
- Intermediate swing high/lows
- Pattern formation
- Confluence zones
- Entry opportunities

**Пример:**
```
BTC 4h chart:
• Pattern: Ascending triangle forming
• Resistance: $51,000 (3 touches)
• Support: Rising from $49,500
• MACD: Bullish crossover
• RSI: 55 (neutral, ready for move)

Decision: Wait for breakout above $51,000
Setup ready ✅
```

### ШАГ 4: 1-Hour (1h) - Entry Timing

**Что смотреть:**
- Precise entry zones
- Short-term patterns
- Indicator convergence
- Entry triggers

**Пример:**
```
BTC 1h chart:
• Breakout произошёл: $51,050
• Volume spike: 2.1x average ✅
• Pullback к $50,950 (retest)
• Hammer forming at retest level

Decision: ENTRY готов
Entry: $50,980 (above Hammer)
```

### ШАГ 5: 15-Minute (15m) - Fine Tuning

**Что смотреть:**
- Exact entry candle
- Immediate price action
- Entry confirmation

**Пример:**
```
BTC 15m chart:
• Bullish Engulfing at retest level
• Volume increasing
• RSI turning up

Decision: EXECUTE NOW
Entry: Market order $50,985
```

---

### Alignment Rules (Правила Выравнивания)

### Полное Совпадение (Ideal)

```
1w: Uptrend ✅
1d: Uptrend ✅
4h: Uptrend ✅
1h: Pullback to support → reversal up ✅

= МАКСИМАЛЬНАЯ confidence
= Enter with larger position (2% risk vs 1%)
= Highest probability
```

### Частичное Совпадение (Good)

```
1w: Sideways (neutral)
1d: Uptrend ✅
4h: Uptrend ✅
1h: Pullback → reversal ✅

= GOOD confidence
= Enter with standard position (1.5% risk)
= Good probability
```

### Конфликт (Avoid)

```
1w: Downtrend ❌
1d: Downtrend ❌
4h: Uptrend ✅
1h: Buy signal

= LOW confidence
= DON'T TRADE
= Против macro trend
```

**ПРАВИЛО:** Minimum 3 из 4 таймфреймов должны совпадать для входа!

---

### Приоритет Таймфреймов

```
Priority Order:
1. 1d (PRIMARY) - определяет main bias
2. 4h (SECONDARY) - подтверждает setup
3. 1h (ENTRY) - timing входа
4. 15m (EXECUTION) - fine-tuning

Конфликты:
• 1d vs 1h → Follow 1d ✅
• 4h vs 15m → Follow 4h ✅
• Старший ВСЕГДА главнее младшего
```

---

## MARKET REGIME DETECTION (Определение Режима Рынка)

### Зачем Определять Режим

Разные стратегии работают в разных рыночных режимах:
- Trend Following → trending markets
- Mean Reversion → ranging markets  
- Breakout → low volatility → high volatility transition

**Торговля неправильной стратегией в неправильном режиме = убытки**

---

### РЕЖИМ 1: Trending vs Ranging

#### Trending Market

**Характеристики:**
- Чёткие higher highs и higher lows (uptrend)
- Или lower highs и lower lows (downtrend)
- ADX > 25 (лучше > 30)
- Цена не возвращается к старым levels

**Индикаторы:**
```
ADX > 25: Trending
ADX > 30: Strong trend
ADX > 40: Very strong trend

Bollinger Bands: Wide (high volatility)
ATR: High or rising
```

**Стратегии использовать:**
- ✅ Trend Following
- ✅ Momentum (в направлении тренда)
- ✅ Pullback entries
- ❌ Mean Reversion (против тренда)
- ❌ Range trading

#### Ranging Market

**Характеристики:**
- Цена между чёткой support и resistance
- Horizontal movement
- ADX < 20 (слабый или нет тренда)
- Multiple rejections от boundaries

**Индикаторы:**
```
ADX < 20: Ranging
ADX < 15: Strong range

Bollinger Bands: Narrow (low volatility)
ATR: Low or declining
Price: Between parallel levels
```

**Стратегии использовать:**
- ✅ Range trading (buy support, sell resistance)
- ✅ Mean Reversion
- ✅ BB bounce plays
- ❌ Trend Following
- ❌ Breakout (wait for squeeze)

**Transition Watch:**
- Range → Trend обычно через Breakout
- Ждите BB squeeze → expansion

---

### РЕЖИМ 2: Bullish vs Bearish

#### Bullish Market

**Характеристики:**
- BTC растёт или stable
- Majority альткоинов в green
- Fear & Greed > 50
- Higher lows на major timeframes
- Volume на up-moves > down-moves

**Индикаторы:**
```
• 50%+ активов в green за 24h
• BTC dominance stable or declining (good для alts)
• Market cap растёт
• Sentiment: Greed zone
```

**Стратегии:**
- Focus на LONG позиции
- Избегайте shorts (против тренда)
- Buy dips агрессивно
- Hold winners дольше

#### Bearish Market

**Характеристики:**
- BTC падает
- Majority активов в red
- Fear & Greed < 40
- Lower highs формируются
- Volume на down-moves > up-moves

**Индикаторы:**
```
• 60%+ активов в red
• BTC dominance растёт (capital flows to BTC)
• Market cap падает
• Sentiment: Fear zone
```

**Стратегии:**
- Focus на SHORT позиции or SIDELINES
- Избегайте longs (catching knives)
- Sell rallies
- Cash is a position

#### Neutral Market

**Характеристики:**
- Mixed signals
- BTC sideways
- 50/50 green/red
- Fear & Greed 40-60

**Стратегии:**
- Wait для clarity
- Range trading only
- Reduce position sizes
- High selectivity

---

### РЕЖИМ 3: Volatility Level

#### High Volatility

**Определение:**
```
ATR > 150% of 20-period average
Daily moves > 5%
Bollinger Bands очень wide
Множественные gap moves
```

**Характеристики:**
- Резкие движения
- Wide intraday ranges
- Высокий risk и reward
- Эмоционально сложно

**Адаптации:**
- Reduce position size (50-75% normal)
- Wider stop-losses (2.5-3x ATR)
- Take profits быстрее
- Avoid leverage >2x
- More selective entries

**Стратегии:**
- ✅ Momentum (в направлении spike)
- ✅ Quick scalps
- ❌ Tight stops (будут выбиты)
- ❌ High leverage

#### Low Volatility

**Определение:**
```
ATR < 75% of 20-period average
Daily moves < 2%
Bollinger Bands очень narrow (squeeze)
Price в tight range
```

**Характеристики:**
- Малые движения
- Consolidation/accumulation
- Boring, но безопасно
- Preparing для breakout

**Адаптации:**
- Ждите breakout (не торгуйте range)
- Or range trade boundaries
- Tighter stops (1-1.5x ATR)
- Normal position sizing

**Стратегии:**
- ✅ Wait для BB squeeze breakout
- ✅ Range trading (если чёткие границы)
- ❌ Trend following (нет тренда)
- ❌ Momentum (нет momentum)

#### Medium Volatility

**Определение:**
```
ATR near 20-period average
Daily moves 2-5%
Normal market conditions
```

**Адаптации:**
- Standard position sizing
- Standard stops (2x ATR)
- All strategies работают

---

## VOLUME ANALYSIS (Анализ Объёма)

### Почему Volume Критичен

**"Volume precedes price"** - объём часто показывает намерения до движения цены.

- High volume = Strong conviction
- Low volume = Weak conviction
- Volume confirmation = higher probability

---

### Volume Confirmation

### Для Движений Вверх

**Здоровое движение:**
```
• Up-move на HIGH volume ✅
• Down-move на LOW volume ✅
• Volume растёт с ростом цены
```

**Слабое движение (warning):**
```
• Up-move на LOW volume ❌
• Down-move на HIGH volume ❌
• Volume падает при росте цены
```

### Для Пробоев

**Настоящий breakout:**
```
• Breakout volume > 1.5-2x average ✅
• Sustained high volume после пробоя ✅
```

**Ложный breakout:**
```
• Breakout на low/average volume ❌
• Volume падает сразу после пробоя ❌
```

### Пример

```
BTC пробой $51,000:

Scenario A (TRUE):
• Breakout свеча: volume 1,250 BTC (2.1x avg)
• Next 3 свечи: volume 800-1,000 BTC (sustained)
• Result: Price продолжает к $52,500 ✅

Scenario B (FALSE):
• Breakout свеча: volume 650 BTC (1.1x avg)
• Next 3 свечи: volume 400-500 BTC (declining)
• Result: Price возвращается в range ❌
```

---

### Volume Divergence

### Bullish Divergence (Бычья)

```
Цена: делает lower lows
Volume: делает higher lows (растёт при падениях)

Интерпретация:
• Selling pressure уменьшается
• Buyers начинают накапливать
• Вероятный разворот вверх
```

**Торговля:**
```
Ждите:
1. Price reversal pattern (Hammer, Engulfing)
2. RSI divergence тоже
3. Support level hold

Entry: После confirmation
High probability reversal ✅
```

### Bearish Divergence (Медвежья)

```
Цена: делает higher highs
Volume: делает lower highs (падает при росте)

Интерпретация:
• Buying pressure уменьшается
• Sellers accumulating
• Вероятный разворот вниз
```

**Торговля:**
```
Ждите:
1. Shooting Star или Bearish Engulfing
2. RSI divergence
3. Resistance rejection

Entry: Short после confirmation
High probability reversal ✅
```

---

### Volume Patterns

#### Climax Volume

**Определение:** Экстремально высокий volume spike (3-5x average)

**Типы:**

**Buying Climax:**
- Huge volume на top
- После длительного rally
- Usually marks short-term top
- Take profits!

**Selling Climax:**
- Huge volume на bottom
- После длительного падения
- Usually marks short-term bottom
- Entry opportunity!

**Пример:**
```
ETH падает неделю: $3,200 → $2,850

Day 8:
• Massive red candle: $2,950 → $2,820
• Volume: 4.5x average (CLIMAX)
• Panic selling

Next day:
• Price recovers to $2,920
• Volume normalizes

= Selling exhaustion
= Entry opportunity после confirmation ✅
```

#### Volume Spike

**Определение:** Внезапный volume рост (1.5-2.5x average)

**Интерпретация зависит от context:**

**В тренде:**
- Volume spike в направлении тренда = continuation
- Volume spike против тренда = возможный reversal

**На уровнях:**
- Volume spike на breakout = true breakout
- Volume spike на rejection = strong level

---

## Volume Indicators

### OBV (On-Balance Volume)

**Формула:**
```
Если Close > Close_prev: OBV = OBV_prev + Volume
Если Close < Close_prev: OBV = OBV_prev - Volume
Если Close = Close_prev: OBV = OBV_prev
```

**Использование:**
- OBV растёт = accumulation (покупатели сильнее)
- OBV падает = distribution (продавцы сильнее)
- OBV divergence = сильный reversal signal

**Пример:**
```
Price: $50,000 → $51,500 → $51,000 (higher low)
OBV: растёт постоянно

= Buying pressure сохраняется
= Despite pullback, accumulation continues
= Bullish signal ✅
```

### VWAP (Volume Weighted Average Price)

**Что показывает:**
- Средняя цена с учётом объёма
- Fair value для сегодня
- Institutional trading level

**Использование:**
```
Price > VWAP: Bullish, buyers в control
Price < VWAP: Bearish, sellers в control
Price at VWAP: Balance, potential bounce
```

**Стратегии:**
```
Long: Купить когда price pullback к VWAP в uptrend
Short: Продать когда price rally к VWAP в downtrend

VWAP как dynamic S/R level
```

---

### Volume Profile

**Определение:** Показывает сколько volume traded на каждом price level за период.

#### Ключевые Зоны

**POC (Point of Control):**
- Price level с максимальным volume
- Магнит для цены
- Strong support/resistance

**Value Area:**
- 70% total volume
- "Fair value" zone
- Price tends to return здесь

**High Volume Nodes (HVN):**
- Zones с много volume
- Strong support/resistance
- Price может consolidate здесь

**Low Volume Nodes (LVN):**
- Zones с мало volume
- Price moves through быстро
- No support/resistance

#### Торговля с Volume Profile

```
Strategy 1: Reversion to POC
• Price far от POC
• Tendency to return
• Entry: в направлении к POC

Strategy 2: LVN Breakout
• Price near LVN
• Breakout через LVN = fast move
• Entry: при breakout

Strategy 3: HVN Support/Resistance
• Price approaching HVN
• Expect bounce or rejection
• Entry: на reaction
```

**Пример:**
```
BTC Volume Profile (last 7 days):
• POC: $50,200
• Value Area: $49,800-$50,600
• HVN: $50,000-$50,400
• LVN: $50,700-$51,200

Current Price: $51,500 (above value area)

Analysis:
• Price extended от POC
• LVN выше = path of least resistance
• HVN ниже = support on pullback

Strategy:
• Expect pullback к $50,200 (POC)
• Or breakout through LVN к next HVN
```

---

## CORRELATION ANALYSIS (Анализ Корреляций)

### BTC Dominance и Влияние

**BTC Dominance:**
```
BTC Dominance = Market Cap BTC / Total Crypto Market Cap

Typical range: 40-60%
```

#### Сценарии

**Rising BTC Dominance:**
```
• Capital flows ИЗ alts В BTC
• Alts underperform или падают
• Risk-off sentiment
• Uncertainty в market

Action:
• Focus на BTC торговлю
• Избегайте alt longs
• Or trade alts short
```

**Falling BTC Dominance:**
```
• Capital flows из BTC в alts
• Alt season potential
• Risk-on sentiment
• Confidence в market

Action:
• Focus на alt торговлю
• Alts outperform BTC
• Hunt для best alt setups
```

**Stable BTC Dominance:**
```
• Balanced market
• BTC и alts движутся together
• Normal conditions

Action:
• Trade оба (BTC и alts)
• Follow individual setups
```

---

### BTC Correlation Patterns

#### High Correlation (>0.8)

**Большинство альткоинов:**
- ETH, BNB, SOL, ADA, etc.
- Следуют за BTC movements
- BTC вверх → alts вверх
- BTC вниз → alts вниз (сильнее)

**Правила торговли:**
```
1. ALWAYS check BTC перед alt trade
2. Если BTC падает → избегайте alt longs
3. Если BTC растёт → alt longs safer
4. Если BTC sideways → alts могут outperform
```

#### Medium Correlation (0.5-0.8)

**Некоторые альты:**
- Могут двигаться независимо short-term
- Но follow BTC long-term

**Правила:**
- Можно торговать independent
- Но monitor BTC trend

#### Divergence Trading

**Бычья Divergence:**
```
BTC: Sideways or slight down
ALT: Strong up move

Интерпретация:
• Alt показывает strength
• Potential leader
• High conviction buying

Action:
• Strong long candidate
• Может продолжить outperform
• Watch для continuation
```

**Медвежья Divergence:**
```
BTC: Растёт
ALT: Falling or weak

Интерпретация:
• Alt показывает weakness
• Distribution happening
• Low conviction

Action:
• Avoid longs
• Consider short
• Wait для BTC correlation return
```

---

## PRACTICAL ANALYSIS WORKFLOW

### Daily Market Analysis Routine

```
═══════════════════════════════════════
MORNING ROUTINE (9:00 AM)
═══════════════════════════════════════

1. BTC ANALYSIS (10 min):
   • 1d chart: trend direction
   • Key levels: S/R
   • Sentiment: bullish/bearish/neutral
   • События: news, макро

2. MARKET OVERVIEW (5 min):
   • Top gainers/losers
   • BTC dominance
   • Total market cap trend
   • Volume trends

3. REGIME DETECTION (5 min):
   • Trending or ranging? (ADX)
   • Bullish or bearish? (sentiment)
   • High or low volatility? (ATR, BB width)
   • Определить regime → select стратегии

4. WATCHLIST CREATION (10 min):
   • Scan для opportunities
   • Multi-timeframe check each
   • Rate confluence (1-10)
   • Top 3-5 candidates

═══════════════════════════════════════
DURING TRADING HOURS
═══════════════════════════════════════

5. OPPORTUNITY MONITORING (continuous):
   • Watch watchlist активы
   • Wait для entry triggers
   • Execute на confluence ≥7

6. POSITION MONITORING (every 15-30 min):
   • Check open positions
   • Evaluate indicators
   • Adjust stops if needed
   • Take profits per plan

═══════════════════════════════════════
EVENING ROUTINE (9:00 PM)
═══════════════════════════════════════

7. REVIEW (15 min):
   • Journal все сделки
   • Analyze execution
   • Определить lessons
   • Plan для tomorrow

8. MACRO CHECK (5 min):
   • News review
   • Upcoming events tomorrow
   • Set alerts
```

---

## DECISION TREE EXAMPLES

### Example 1: Should I Take This Trade?

```
START
  ↓
Multi-TF aligned (3/4)? 
  ├─ NO → ❌ SKIP
  └─ YES → Continue
      ↓
Confluence ≥ 6?
  ├─ NO → ❌ SKIP  
  └─ YES → Continue
      ↓
R:R ≥ 1:2?
  ├─ NO → ❌ SKIP
  └─ YES → Continue
      ↓
Market regime supports strategy?
  ├─ NO → ❌ SKIP
  └─ YES → Continue
      ↓
BTC поддерживает направление?
  ├─ NO → ❌ SKIP or reduce size
  └─ YES → Continue
      ↓
Volume confirms?
  ├─ NO → ❌ WAIT для confirmation
  └─ YES → ✅ TAKE TRADE
```

### Example 2: Which Strategy To Use?

```
START: Определён хороший setup
  ↓
What's Market Regime?
  │
  ├─ TRENDING (ADX > 25)
  │   └─ Use: Trend Following или Momentum
  │
  ├─ RANGING (ADX < 20)
  │   └─ Use: Mean Reversion или Range Trading
  │
  └─ TRANSITION (BB Squeeze)
      └─ Use: Breakout Strategy
```

---

## ЗАКЛЮЧЕНИЕ

**Ключевые Принципы Market Analysis:**

1. **Top-Down Always**
   - Start с macro (1w, 1d)
   - End с micro (1h, 15m)
   - Старший ТФ определяет bias

2. **Identify Regime First**
   - Trending → Trend Following
   - Ranging → Mean Reversion
   - Don't fight режим

3. **Volume is King**
   - Price без volume = suspicious
   - Volume confirmation обязательна
   - Volume divergence = powerful signal

4. **Respect BTC**
   - BTC leads рынок
   - Alt correlation с BTC high
   - BTC против вас = reduce confidence

5. **Confluence Determines Entry**
   - 3-4 factors: weak
   - 5-6 factors: moderate
   - 7-8 factors: strong ✅
   - 9-10 factors: excellent ✅✅

6. **Adapt to Conditions**
   - High vol → smaller size, wider stops
   - Low vol → wait для breakout
   - Bearish market → reduce longs
   - Bullish market → maximize longs

**Final Wisdom:**

> "Лучший трейдер не тот, кто всегда прав.  
> Это тот, кто адаптируется к рынку."

Используйте этот framework для системного, повторяемого анализа рынка каждый день.

---

*Структурированный анализ убирает эмоции и гадания. Следуйте framework механически для последовательных результатов.*

