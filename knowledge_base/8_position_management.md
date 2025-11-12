# ⚡ Управление Позициями: От Входа До Выхода

## Введение

Открытие позиции - это только 20% работы. Остальные 80% - это управление ей. Правильное управление позицией может превратить посредственный setup в прибыльный, а плохое управление может уничтожить отличный setup.

**Цель:** Максимизировать прибыль и минимизировать риск через активное управление после входа.

---

## LIFECYCLE ПОЗИЦИИ (Жизненный Цикл)

### ФАЗА 0: Pre-Entry (Подготовка)

#### Checklist Перед Входом

```
═══════════════════════════════════════
PRE-ENTRY CHECKLIST
═══════════════════════════════════════

ТЕХНИЧЕСКИЙ АНАЛИЗ:
[ ] Multi-timeframe alignment проверен
[ ] Confluence score ≥ 8/10
[ ] Pattern identified и confirmed
[ ] S/R levels определены
[ ] Индикаторы подтверждают

РИСК-МЕНЕДЖМЕНТ:
[ ] Entry price определён
[ ] Stop-loss рассчитан логично
[ ] Take-profit targets установлены
[ ] R:R ≥ 1:2
[ ] Position size рассчитан (risk 1-2%)

РЫНОЧНЫЕ УСЛОВИЯ:
[ ] Market regime поддерживает стратегию
[ ] BTC direction благоприятный
[ ] Volume pattern правильный
[ ] No negative news expected

ПСИХОЛОГИЯ:
[ ] Нет эмоционального давления
[ ] Следую торговому плану
[ ] Готов принять убыток если SL
[ ] Comfortable с размером позиции

ПЛАН УПРАВЛЕНИЯ:
[ ] Знаю когда move to breakeven
[ ] Знаю когда activate trailing
[ ] Знаю условия досрочного exit
[ ] Safe time window определён

ЕСЛИ ВСЕ ГАЛОЧКИ ✅ → ГОТОВ ВХОДИТЬ
ЕСЛИ ХОТЬ ОДНА ❌ → ПОДОЖДИ
═══════════════════════════════════════
```

---

### ФАЗА 1: Entry Execution (Исполнение Входа)

#### Типы Входа

**Market Order:**
```
Когда использовать:
• Strong momentum breakout
• Need immediate execution
• High liquidity asset

Risks:
• Slippage (может быть $10-50)
• Worse price than expected

Example:
Planned entry: $50,000
Market order executed: $50,035 (slippage $35)
```

**Limit Order:**
```
Когда использовать:
• Планируемый pullback entry
• Want better price
• No rush

Risks:
• May not fill
• Price may run without you

Example:
Current: $50,100
Limit order: $50,000 (ждём pullback)
If price goes to $51,000 без pullback → missed
```

**Рекомендация:**
- **Breakouts:** Market order (speed важнее цены)
- **Pullbacks:** Limit order (better price)

#### Immediate Actions После Entry

```
СРАЗУ после исполнения:

1. SET STOP-LOSS (30 секунд):
   • Если exchange поддерживает: OCO order
   • Если нет: Manual stop-loss order
   • НЕ ОТКЛАДЫВАЙТЕ! Сразу!

2. SET TAKE-PROFIT (1 минута):
   • Limit orders на TP levels
   • Или plan trailing activation point

3. RECORD в Journal (2 минуты):
   • Entry details
   • Reasoning
   • Plan

4. SET ALERTS (2 минуты):
   • Alert на 50% к TP (check breakeven)
   • Alert на 75% к TP (consider partial exit)
   • Alert на near SL (monitor closely)

TOTAL TIME: 5 минут
Эти 5 минут КРИТИЧНЫ!
```

---

### ФАЗА 2: Initial Stop Placement (Первоначальный Стоп)

#### Где Разместить Initial SL

**Принцип:** SL должен быть там, где setup invalidated.

**Для Trend Following:**
```
SL = Ниже EMA(50) + buffer (0.5-1x ATR)

Example:
Entry: $50,200 (pullback от EMA20)
EMA(50): $49,800
ATR: $400
Buffer: $200

SL = $49,800 - $200 = $49,600
```

**Для Breakout:**
```
SL = Внутри пробитого range

Example:
Range: $49,000-$51,000
Breakout: $51,100
Entry: $51,150

SL = $50,500 (middle of range)
Или $49,900 (ниже range для wider stop)
```

**Для Mean Reversion:**
```
SL = Ниже support level + buffer

Example:
Support: $2,900
Entry: $2,935
Buffer: $50 (ATR-based)

SL = $2,900 - $50 = $2,850
```

#### Stop-Loss НИКОГДА НЕ:

```
❌ НЕ двигайте ДАЛЬШЕ (accept loss!)
❌ НЕ remove "на минутку"
❌ НЕ ставьте на "круглых" числах
❌ НЕ ставьте слишком близко (volatility выбьет)
❌ НЕ ставьте слишком далеко (bad R:R)
```

---

### ФАЗА 3: Мониторинг в Процессе

#### Частота Проверки

```
По типу торговли:

Скальпинг (5m-15m):
• Check каждые 5-15 минут
• Alerts critical
• Quick reactions needed

Интрадей (1h-4h):
• Check каждые 30-60 минут
• Alerts на key levels
• Moderate monitoring

Свинг (4h-1d):
• Check каждые 2-4 часа
• Alerts на significant moves
• Relaxed monitoring
```

#### Что Проверять

**1. Price Progress (Прогресс Цены):**
```
Questions:
• Движется к TP?
• Как быстро?
• Соответствует ожиданиям?

Benchmarks:
• Should reach 25% к TP в первые 25% safe time
• If не movement в 50% safe time → warning

Example:
Safe time: 8 hours, TP distance: $1,000

After 2h (25%): expect +$250 progress
After 4h (50%): expect +$500 progress

If actual: только +$100 after 4h:
→ Slower than expected
→ Evaluate exit
```

**2. Индикаторы Status:**
```
Monitor:
• RSI: still supporting?
• MACD: still bullish?
• Volume: still strong?
• ADX: trend strengthening or weakening?

Warning signs:
• RSI divergence forming
• MACD turning
• Volume declining
• ADX falling
```

**3. Volume Dynamics:**
```
Healthy (продолжаем hold):
• Volume steady или increasing
• Up-moves on higher volume
• Down-moves on lower volume

Unhealthy (consider exit):
• Volume declining significantly
• Up-moves on lower volume
• Down-moves on higher volume
```

**4. Time Elapsed:**
```
Track:
• Hours/days in trade
• % of safe time used
• Progress vs time (efficiency)

Alert levels:
• 50% safe time → check progress
• 75% safe time → strict monitoring
• 100% safe time → EXIT regardless
```

**5. External Factors:**
```
Monitor:
• BTC movements (для altcoins)
• News/announcements
• Market sentiment shifts
• Competitor movements
```

---

### ФАЗА 4: Breakeven Translation (Перевод в Безубыток)

#### Когда Переводить в Breakeven

**Условие 1: Достигли 1:1 R:R**
```
Entry: $50,000
SL: $49,500 (risk $500)
Current price: $50,500 (+$500 = 1:1)

Action:
• Move SL to $50,010 (breakeven + комиссии)
• Теперь риск ZERO
• Можем hold без stress
```

**Условие 2: Сильный Импульс**
```
Scenario:
• Entry: $3,000
• За первый час: +2.5% → $3,075
• Strong momentum, likely continues

Action:
• Move SL к breakeven раньше (до 1:1)
• Lock in no-loss scenario early
• Ride momentum с comfort
```

**Условие 3: Приближается Сопротивление**
```
Scenario:
• Entry: $50,000
• Current: $50,800 (+1.6%)
• Resistance: $51,000 (близко)
• Может rejection

Action:
• Move SL к $50,050 (breakeven)
• Если rejection → exit с tiny profit
• Если breakout → continue holding
```

#### Как Переводить

```
Conservative:
SL = Entry + Комиссии + $5-10 buffer

Example:
Entry: $50,000
Fees: ~0.1% = $50
Buffer: $10
Breakeven SL: $50,060

Moderate:
SL = Entry + Комиссии
Breakeven SL: $50,050

Aggressive (если сильный momentum):
SL = Entry (даже если small loss от fees)
Breakeven SL: $50,000
```

---

### ФАЗА 5: Trailing Stop Activation

#### Когда Активировать Trailing

**Timing 1: Достигли 2:1 R:R**
```
Entry: $50,000
Initial SL: $49,500 (risk $500)
TP planned: $51,000 (reward $1,000)

Price reaches $51,000:
• Achieved 2:1 ✅
• Significant profit locked
• Time для trail remaining

Action:
Activate trailing stop: 2% или 2x ATR
```

**Timing 2: Сильный Непрерывный Тренд**
```
Indicators:
• ADX > 35 (very strong trend)
• Price не pullback > 30 минут
• Volume sustained high
• All EMA aligned perfectly

Action:
• Activate trailing earlier (even at 1.5:1)
• Maximize trend capture
```

**Timing 3: Exceeded Original TP**
```
Scenario:
• TP was $51,000
• Price reached $51,200 и продолжает
• Strong momentum continues

Action:
• Cancel limit TP order
• Activate trailing immediately
• Let profits run!
```

#### Trailing Distance Calculation

**Method 1: Fixed Percentage**
```
Trailing Distance = Entry × Percentage

Для криптовалют:
• Conservative: 2-3%
• Moderate: 1.5-2%
• Aggressive: 1-1.5%

Example:
Entry: $50,000
Trailing: 2% = $1,000

Price $53,000:
Trailing SL: $53,000 - $1,000 = $52,000 (locked +$2,000)
```

**Method 2: ATR-Based** (РЕКОМЕНДУЕТСЯ)
```
Trailing Distance = ATR × Multiplier

Multiplier:
• Volatile market: 2.5-3x ATR
• Normal market: 2x ATR
• Calm market: 1.5x ATR

Example:
ATR: $500
Multiplier: 2x
Trailing: $1,000

Adapts к волатильности автоматически!
```

**Method 3: Parabolic SAR**
```
• Используйте SAR indicator
• SAR dots trail под ценой
• Exit когда price crosses SAR
• Автоматический, adaptive
```

#### Trailing Management

**НЕ trail слишком tight:**
```
Problem:
• 0.5% trailing в volatile market
• Normal fluctuation выбивает
• Miss большую часть move

Solution:
• Минимум 1.5% для BTC
• Минимум 2% для altcoins
• Больше в high volatility
```

**НЕ trail too loose:**
```
Problem:
• 5% trailing
• Отдаём слишком много back
• Profit сокращается значительно

Solution:
• Maximum 3% для BTC
• Maximum 3.5% для alts
• Tighten по мере profit роста
```

**Progressive Tightening:**
```
Strategy:
Initial trailing: 2.5% ATR
After +5% profit: 2.0x ATR
After +10% profit: 1.5x ATR

= Secure больше profit по мере роста
= Natural profit taking
```

---

### ФАЗА 6: Exit Execution (Исполнение Выхода)

#### Типы Exit

**1. TP Hit (Target Profit Достигнут)**
```
Лучший сценарий:
• Limit order automatically fills
• Planned profit secured
• Emotionless execution ✅

Action:
• Record в journal
• Analyze execution
• Look для next opportunity
```

**2. Trailing Stop Hit**
```
Сценарий:
• Rode trend хорошо
• Максимизировали profit
• Clean exit ✅

Action:
• Calculate profit secured
• Happy с результатом
• Journal entry
```

**3. Manual Exit (Досрочный)**
```
Reasons:
• Reversal pattern seen
• Volume dried up
• Time limit exceeded
• Better opportunity found
• Risk changed

Action:
• Market order exit (быстро)
• Accept current profit/loss
• Move on
```

**4. Stop-Loss Hit**
```
Сценарий:
• Setup не worked
• Loss controlled ✅

Action:
• Accept loss emotionless
• НЕ revenge trade
• Journal и analyze
• Break before next trade
```

---

## ADVANCED POSITION MANAGEMENT

### Scale Out (Частичное Закрытие)

#### Standard Scaling Plan

```
Распределение:
50% at TP1 (Conservative target)
30% at TP2 (Moderate target)
20% at TP3 or Trail (Aggressive)

Example:
Position: 0.01 ETH
Entry: $3,000
TP1: $3,150 → Close 0.005 ETH (50%)
TP2: $3,250 → Close 0.003 ETH (30%)
TP3: Trail remaining 0.002 ETH (20%)
```

#### Преимущества Scale Out

**Psychological:**
- Secured profit reduces stress
- Comfortable holding remainder
- Less emotional

**Financial:**
- Optimizes average exit price
- Участвуете в bigger moves
- Reduces regret (some profit always taken)

**Risk:**
- Partial profit locked early
- Remaining позиция "free" (playing with profit)

### Position Addition (Добавление к Позиции)

#### Когда Можно Добавлять

**ТОЛЬКО когда:**
```
1. First position в PROFIT
2. Original thesis stronger (more confluence)
3. New entry має better R:R than first
4. Total risk still ≤ 2-3% портфеля
5. Strong trend continues (ADX rising)
```

**Pyramiding Example:**
```
Position 1:
Entry: $50,000, Size: 0.0005 BTC, Risk: $0.25
Current: $50,800 (+$400 profit)

Position 2 (add):
Entry: $50,800 (pullback)
Size: 0.0003 BTC (smaller!), Risk: $0.15
Total risk: $0.40 (still < 2%)

Combined SL: Move to breakeven first position

= Dollar-cost averaging UP (правильно)
≠ Averaging DOWN (неправильно!)
```

**НИКОГДА не averaging down:**
```
❌ WRONG:
Position 1: Long $50,000 (now at $49,500, -$500 loss)
Position 2: Add long $49,500 to "average down"

= Увеличиваете risk на losing trade
= Emotional decision
= Path to ruin

✅ RIGHT:
If losing → Accept loss, exit, move on
```

---

## УПРАВЛЕНИЕ НЕСКОЛЬКИМИ ПОЗИЦИЯМИ

### Maximum Concurrent Positions

```
Депозит-based limits:
$30: Maximum 2 positions
$100: Maximum 2-3 positions
$500: Maximum 3-4 positions
$1,000+: Maximum 4-5 positions

Почему limited:
• Easier мониторинг
• Less correlation risk
• More capital per trade (better execution)
• Mental capacity limit
```

### Correlation Management

#### Проблема

```
Scenario (BAD):
Position 1: ETH Long (+2%)
Position 2: ADA Long (+1.5%)
Position 3: SOL Long (+1%)

BTC suddenly drops -3%:
→ ETH drops -4% (SL hit: -$0.30)
→ ADA drops -3.5% (SL hit: -$0.30)
→ SOL drops -3% (SL hit: -$0.30)

Total loss: -$0.90 in minutes! (3% портфеля)

Problem: All positions correlated, all failed together
```

#### Solution: Diversification

```
Better Portfolio:
Position 1: BTC Long (leader)
Position 2: ETH Short (hedge)
Position 3: Wait for uncorrelated

Or:
Position 1: Trend Following BTC Long
Position 2: Mean Reversion ALT Long (different setup)

= Lower correlation
= Independent failures
= Smoother equity curve
```

### Priority Monitoring

**Когда multiple positions:**

```
Priority Order:
1. Largest position size
2. Highest % риска
3. Closest to SL
4. Most profitable (protect gains)
5. Most time-sensitive

Example:
Pos A: BTC 1% риска, +2% profit, 2h old
Pos B: ETH 1.5% риска, -0.5% loss, near SL, 5h old
Pos C: SOL 0.5% риска, +0.2% profit, 1h old

Monitoring priority: B > A > C
```

### Portfolio Risk

**Aggregate Risk Calculation:**

```
Position 1: 1.5% риска
Position 2: 1.0% риска
Position 3: 1.0% риска

Total Portfolio Risk: 3.5%

Rule: Total risk ≤ 5% портфеля

If opening Position 4:
Max risk = 5% - 3.5% = 1.5%
```

---

## SITUATIONAL MANAGEMENT

### Scenario 1: Быстрый Profit (+3% за час)

```
Situation:
• Entry: $50,000
• Current: $51,500 (+3%) in 1 hour!
• Way faster than expected

Analysis:
• Probably unsustainable
• May pullback
• Secure some profit

Action:
• Close 50% сразу (take profit)
• Move SL to breakeven на remainder
• Or activate tight trailing (1%)
• Secure gains before reversal
```

### Scenario 2: Медленный Grind

```
Situation:
• Entry: $50,000
• 6 hours passed
• Only at $50,250 (+0.5%)
• Expected: +2% by now

Analysis:
• Setup слабее than expected
• Momentum lacking
• Opportunity cost

Action:
• If indicators still good: hold но monitor strict
• If indicators weakening: exit с small profit
• If time > 75% safe window: exit
```

### Scenario 3: Pullback к Breakeven

```
Situation:
• Entry: $50,000
• Reached $51,200 (+2.4%)
• Pulled back к $50,100 (+0.2%)

Analysis:
• Lost большую часть profit
• Momentum questioned

Action:
• If indicators still bullish: hold (может resume)
• If reversal forming: exit сразу
• If volume dried up: exit
• НЕ wait для full loss!
```

### Scenario 4: Stuck Sideways

```
Situation:
• Entry: $50,000
• Sideways $50,000-$50,300 для 4 hours
• No direction

Analysis:
• Setup stalled
• Capital unproductive

Action:
• Exit если > 50% safe time
• Free capital для better opportunity
• "No decision is a decision"
```

### Scenario 5: News Released

```
Positive News:
• Supports position direction
• May cause spike
• Action: Consider letting winners run или
  partial profit take на spike

Negative News:
• Against position
• Uncertainty increased
• Action: EXIT IMMEDIATELY
• Don't wait to see impact
```

---

## ПСИХОЛОГИЯ УПРАВЛЕНИЯ ПОЗИЦИЕЙ

### Dealing with Winning Positions

**Problem: Greed**
```
Thought: "It может go higher!"
Result: Hold слишком долго, profit evaporates

Solution:
• Follow TP plan strictly
• Scale out systematically
• Remember: Planned profit > hoped-for profit
• "Pigs get slaughtered"
```

**Problem: Exit Too Early**
```
Thought: "Better take profit now before it reverses"
Result: Miss большую часть move

Solution:
• Let trailing stop work
• Trust в plan
• If strong trend → stay in
• Small profit multiple times < big profit once
```

### Dealing with Losing Positions

**Problem: Hope**
```
Thought: "It will come back"
Result: Hold losing position, bigger loss

Solution:
• Respect stop-loss
• Cut losses быстро
• Accept small loss
• Move on
```

**Problem: Moving SL**
```
Thought: "Just a little more room"
Result: Even bigger loss

Solution:
• NEVER move SL away
• SL = invalidation point
• If hit → setup wrong → accept it
```

---

## POSITION MANAGEMENT CHECKLIST

### Hourly Check (For Active Positions)

```
═══════════════════════════════════════
POSITION MONITORING CHECKLIST
═══════════════════════════════════════

POSITION INFO:
Symbol: ______  Entry: $______
Current: $______  P/L: ____%
Time elapsed: __ hours / Safe time: __ hours

PRICE PROGRESS:
[ ] Moving toward TP?
[ ] Speed acceptable?
[ ] Expected progress: __%
[ ] Actual progress: __% [OK/SLOW/FAST]

INDICATORS:
[ ] RSI still supporting? [YES/NO]
[ ] MACD still bullish? [YES/NO]
[ ] Volume healthy? [YES/NO]
[ ] No divergence forming? [YES/NO]

ACTIONS NEEDED:
[ ] Move to breakeven? (at 1:1 R:R)
[ ] Activate trailing? (at 2:1 R:R)
[ ] Take partial profit? (at resistance)
[ ] Exit early? (warnings present)

RED FLAGS:
[ ] Reversal pattern forming?
[ ] Volume dried up?
[ ] Time > 75% safe window?
[ ] BTC turned against us?
[ ] Profit shrinking?

IF ANY RED FLAG → CONSIDER EXIT!
═══════════════════════════════════════
```

---

## BEST PRACTICES

### DO's ✅

```
✅ Set SL сразу after entry
✅ Move к breakeven at 1:1 R:R
✅ Use trailing после 2:1 R:R
✅ Take partial profits at resistances
✅ Exit at FIRST reversal sign
✅ Monitor positions регулярно
✅ Journal все управленческие решения
✅ Follow safe time windows
✅ Scale out systematically
✅ Accept small losses quickly
```

### DON'Ts ❌

```
❌ Remove SL "на минутку"
❌ Move SL further from entry
❌ Average down losing positions
❌ Hold past safe time из надежды
❌ Ignore warning signs
❌ Let small profit become loss
❌ Fight trend
❌ Over-monitor (causes emotional trades)
❌ Forget about positions
❌ Hope вместо plan
```

---

## ФИНАЛЬНЫЕ РЕКОМЕНДАЦИИ

### Position Management Principles

**1. Plan Before Execute**
```
Before entry KNOW:
• Where breakeven move
• When activate trailing
• What conditions trigger early exit
• Maximum time willing to hold
```

**2. Execute Plan Mechanically**
```
• No emotions
• Follow rules
• Trust система
• Review after, не during
```

**3. Protect Profits Aggressively**
```
• Once в profit, protect it
• Move к breakeven быстро
• Scale out systematically
• Trailing in trends
```

**4. Cut Losses Quickly**
```
• SL hits → exit (no questions)
• Warning signs → exit (no hope)
• Better safe than sorry
• Capital preservation > ego
```

**5. Learn and Adapt**
```
• Journal every management decision
• What worked / didn't work
• Improve system continuously
• Find your optimal style
```

---

## EXAMPLE: COMPLETE POSITION LIFECYCLE

```
═══════════════════════════════════════
COMPLETE TRADE: ETH/USDT Long
═══════════════════════════════════════

PRE-ENTRY (Day 1, 10:00):
• Analysis done, confluence 8.5/10 ✅
• Entry: $3,000, SL: $2,920, TP: $3,160
• R:R: 1:2, Risk: 2% ($0.60)
• Position: 0.02 ETH ($60)
• Safe time: 12 hours

ENTRY (Day 1, 10:15):
• Limit order filled: $3,000
• Stop-loss set immediately: $2,920
• TP limit order set: $3,160
• Alerts set: $3,040 (breakeven check), $3,140 (near TP)

HOUR 2 (12:15) - Initial Monitoring:
• Price: $3,055 (+1.8%)
• Progress: Good (25% к TP)
• Indicators: Still bullish
• Action: HOLD

HOUR 4 (14:15) - Breakeven Check:
• Price: $3,085 (+2.8%, reached 1:1 R:R)
• Alert triggered
• Action: MOVE SL to $3,005 (breakeven) ✅
• Risk eliminated!

HOUR 6 (16:15) - Partial Profit:
• Price: $3,145 (+4.8%, near TP)
• Resistance appearing
• Action: Close 50% at $3,145 (+$2.90 profit locked)
• Move SL to $3,080 на remainder

HOUR 8 (18:15) - Trailing Activation:
• Price: $3,180 (+6%, exceeded TP!)
• Strong momentum continues
• Action: Cancel TP order, activate trailing 2% ($64)
• Trailing SL: $3,116

HOUR 11 (21:15) - Peak:
• Price: $3,225 (+7.5%)
• Trailing SL: $3,161
• Locked profit on remaining 50%: +$161 × 0.01 = $1.61

HOUR 12 (22:15) - Exit:
• Price pulled back to $3,160
• Trailing stop triggered
• Final exit: $3,160 на remaining 50%

RESULTS:
Position 1 (50%): Entry $3,000 → Exit $3,145 = +4.8%
Position 2 (50%): Entry $3,000 → Exit $3,160 = +5.3%
Average: +5.05% on $60 = $3.03 profit

Time in trade: 12 hours (exactly safe time)
Execution: PERFECT ✅

JOURNAL NOTES:
• Plan followed strictly
• Breakeven move protected capital
• Scale out secured profit
• Trailing captured extra move
• Clean exit without stress

LESSONS:
• Trailing gave extra +$0.60 vs fixed TP
• Breakeven move removed stress
• Scale out psychologically easier
• Plan works when followed
═══════════════════════════════════════
```

---

## ЗАКЛЮЧЕНИЕ

**Hierarchy Position Management:**

```
1. PRESERVATION (Priority #1)
   • Move to breakeven early
   • Protect capital
   • Accept small losses

2. OPTIMIZATION
   • Scale out for best average
   • Trail in trends
   • Maximize wins

3. DISCIPLINE
   • Follow plan не emotions
   • Mechanical execution
   • Trust system

4. LEARNING
   • Journal everything
   • Analyze patterns
   • Improve continuously
```

### Final Wisdom

> **"Amateur трейдеры focus на entry.  
> Professional трейдеры focus на management."**

**Ключевые Принципы:**

- Set SL немедленно после entry (no excuses!)
- Move к breakeven at 1:1 R:R (eliminate risk!)
- Trail в сильных трендах (maximize profit!)
- Exit at FIRST warning (better safe!)
- Scale out for optimization (best average!)
- Monitor регулярно (be aware!)
- Journal все decisions (learn continuously!)

**Помните:**

```
Good Entry + Bad Management = Loss
Average Entry + Good Management = Profit

Management ≥ Entry
```

---

*Управление позицией - это где зарабатываются настоящие деньги. Master это skill.*

