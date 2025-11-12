# 📡 Протокол Мониторинга Позиций

## Общие Принципы

Мониторинг позиций - это активный процесс управления риском и максимизации прибыли.

**Частота проверки зависит от timeframe:**
- Скальпинг (5m-15m): каждые 5-15 минут
- Интрадей (1h-4h): каждые 30-60 минут
- Свинг (4h-1d): каждые 2-4 часа

**ОБЯЗАТЕЛЬНО мониторить:**
- Price progress к TP
- Индикаторы (RSI, MACD, Volume)
- Time elapsed
- BTC movements (для alts)
- External factors (news, events)

---

## MONITORING CHECKLIST (Каждая Проверка)

```
═══════════════════════════════════════
POSITION MONITORING CHECKLIST
═══════════════════════════════════════

POSITION INFO:
Symbol: [____]
Entry: $[____] | Current: $[____]
P/L: [__]% ($[__])
Time: [__]h / Safe Window: [__]h
Direction: Long/Short

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PRICE PROGRESS ANALYSIS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[ ] Moving toward TP?
    Current distance: [__]%
    Expected at this time: [__]%
    Status: [On Track / Ahead / Behind]

[ ] Speed acceptable?
    Progress rate: [__]% per hour
    Expected rate: [__]% per hour
    Assessment: [Good / Slow / Fast]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
INDICATOR CHECK:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[ ] RSI still supporting?
    Current: [__]
    Status: [Bullish / Neutral / Bearish]
    Divergence: [None / Forming / Present]

[ ] MACD still favorable?
    Position: [Above / Below signal]
    Histogram: [Growing / Shrinking / Flat]
    Crossover risk: [Low / Medium / High]

[ ] Volume healthy?
    Current: [__]x average
    Trend: [Rising / Stable / Declining]
    Assessment: [Strong / OK / Weak]

[ ] Trend strength (ADX)?
    ADX: [__]
    Status: [Strengthening / Stable / Weakening]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RISK FACTORS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[ ] Reversal pattern forming?
    [Pattern name or None]

[ ] At resistance/support?
    Near level: [Yes/No]
    Attempts to break: [__]
    Rejection risk: [Low/Medium/High]

[ ] BTC status (для alts)?
    BTC: [direction] ([change]%)
    Correlation risk: [Low/Medium/High]

[ ] Time status?
    Elapsed: [__]% of safe time
    Alert level: [Green / Yellow / Red]

[ ] Profit protection?
    Max profit seen: [__]%
    Current profit: [__]%
    Giving back: [__]% [OK if <20%]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ACTIONS NEEDED:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[ ] Move SL to breakeven?
    Condition: At 1:1 R:R OR strong momentum
    Status: [Yes / No / Already done]

[ ] Activate trailing stop?
    Condition: At 2:1 R:R OR exceeded TP
    Status: [Yes / No / Already active]

[ ] Take partial profit?
    Condition: At TP1 level OR resistance
    Status: [Yes / No / Already taken]

[ ] Early exit needed?
    Conditions checked: [list red flags]
    Decision: [Hold / Exit / Partial exit]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OVERALL ASSESSMENT:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Status: [🟢 Healthy / 🟡 Caution / 🔴 Warning]
Action: [HOLD / EXIT / ADJUST]
Reason: [explanation]
═══════════════════════════════════════
```

---

## АВТОМАТИЧЕСКИЕ ДЕЙСТВИЯ

### Action 1: Move to Breakeven

**Trigger Conditions:**

```
Execute когда:
1. Profit достиг 1:1 R:R (risk = reward)
2. OR: Strong momentum (+2% в первый час)
3. OR: Approaching resistance (риск rejection)

Action:
• Calculate breakeven: Entry + Fees + Buffer
• Move SL order к breakeven level
• Log action в monitoring notes

Example:
Entry: $50,000
Initial SL: $49,500 (risk $500)
Current: $50,500 (profit $500 = 1:1 R:R)

New SL: $50,010 (entry + $10 buffer)
→ Risk eliminated ✅
```

### Action 2: Activate Trailing Stop

**Trigger Conditions:**

```
Execute когда:
1. Profit достиг 2:1 R:R
2. OR: Exceeded original TP
3. OR: Strong trend ADX >35 непрерывный

Action:
• Determine trailing distance (2% or 2x ATR)
• Cancel fixed TP limit order
• Activate trailing stop
• Monitor trail updates

Example:
Entry: $50,000
Profit: +$1,000 (2:1 R:R hit)
ATR: $400

Trailing: 2 × $400 = $800
Initial trail SL: $51,000 - $800 = $50,200
```

### Action 3: Partial Profit Taking

**Trigger Conditions:**

```
Execute когда:
1. Hit TP1 level
2. OR: At strong resistance
3. OR: Indicators showing exhaustion

Action:
• Close 50-60% position
• Secure partial profit
• Trail или hold remainder

Example:
Position: 0.01 ETH
TP1: $3,150 reached

Close: 0.006 ETH (60%) at $3,150
Hold: 0.004 ETH (40%) для TP2 или trail
```

### Action 4: Emergency Exit

**Trigger Conditions (ANY of these):**

```
IMMEDIATE EXIT если:
1. Reversal pattern на ANY timeframe
2. BTC sharp reversal (>1.5% против нас)
3. Negative news released
4. Volume collapse (<0.5x average)
5. Indicator divergence против позиции
6. Safe time window exceeded
7. Profit shrinking (was +3%, now +1%)

Action:
• Market order exit (speed > price)
• Accept current P/L
• Document reason в journal
• Take break before next trade
```

---

## МОНИТОРИНГ OUTPUT FORMAT

### Regular Update (Каждый Check)

```
⏱️ [TIME] | POSITION UPDATE: [SYMBOL]

💰 P/L: [+/-X]% ($[X.XX])
📊 Current: $[X] (Entry: $[X])

Progress: [XX]% к TP ([X]h elapsed / [Y]h safe window)

📈 Indicators:
• RSI: [X] ([interpretation])
• MACD: [status]
• Volume: [X]x avg ([assessment])

🎯 Status: [🟢/🟡/🔴] [assessment]

▶️ Action: [HOLD / действие taken]
```

### Example Updates

**Healthy Position:**
```
⏱️ 14:45 | ETH/USDT Long Update

💰 P/L: +2.1% ($0.63)
📊 Current: $3,063 (Entry: $3,000)

Progress: 39% к TP1 (4.5h / 12h safe window)

📈 Indicators:
• RSI: 59 → 62 (momentum strengthening) ✅
• MACD: Histogram growing ✅
• Volume: 1.4x avg (good support) ✅

🎯 Status: 🟢 Healthy - on track

▶️ Action: HOLD - все factors positive
Next check: 16:00 (при достижении 1:1 R:R)
```

**Warning Position:**
```
⏱️ 18:30 | BTC/USDT Long Update

💰 P/L: +0.8% ($0.24)
📊 Current: $50,400 (Entry: $50,000)

Progress: 20% к TP (6h / 8h safe window) ⚠️

📈 Indicators:
• RSI: 58 → 54 (weakening) ⚠️
• MACD: Histogram shrinking ⚠️
• Volume: 0.8x avg (declining) ⚠️

🎯 Status: 🟡 CAUTION - slower than expected

▶️ Action: STRICT MONITORING
• Set tight alert на $50,200 (small profit level)
• If no progress в 1h → consider exit
• Watch для reversal patterns

Next check: 19:00 (early - need close monitoring)
```

---

## DECISION POINTS DURING MONITORING

### Decision Point 1: At 50% Safe Time

```
Check:
• Progress made: [__]%
• Expected: ≥40% к TP

If progress <25%:
→ ⚠️ WARNING: Setup not performing
→ Stricter monitoring
→ Prepare для early exit

If progress 25-40%:
→ OK, continue monitoring

If progress >40%:
→ ✅ Great, likely to hit TP
```

### Decision Point 2: At Resistance

```
Scenario: Price достигла resistance

Check:
• Attempts to break: [count]
• Volume на attempts: [increasing/decreasing]
• RSI: [overbought?]

If 2+ attempts failed + volume declining:
→ EXIT (likely rejection)
→ Take profit before reversal

If strong volume + RSI OK:
→ HOLD (может пробить)
→ Tighten trailing если active
```

### Decision Point 3: Profit Shrinking

```
Scenario: Was +3%, now +1.5%

Analysis:
• Why shrinking?
• Reversal pattern?
• Volume shift?
• BTC turned?

Decision:
• If temporary pullback в uptrend → HOLD
• If reversal signals → EXIT IMMEDIATELY
• If uncertain → EXIT 50%, protect remaining

Rule: Never let +3% become loss!
```

---

## ALERT SYSTEM

### Critical Alerts (Immediate Attention)

```
🚨 CRITICAL ALERTS:

1. Price within 0.5% of SL
   → Check immediately
   → Verify SL order active
   → Prepare psychologically

2. Strong reversal pattern formed
   → Evaluate exit regardless of profit
   → Don't wait for SL

3. BTC sharp move >2% против нас (alts)
   → Exit alts immediately
   → BTC leads market

4. Safe time 90% elapsed
   → Exit protocol initiate
   → Don't exceed max time

5. Negative news/events
   → Assess impact
   → Exit if material
```

### Standard Alerts (Regular Check)

```
📢 STANDARD ALERTS:

1. Reached 1:1 R:R
   → Move to breakeven

2. Reached 2:1 R:R
   → Activate trailing stop

3. TP1 level hit
   → Execute scale out (50-60%)

4. 50% safe time elapsed
   → Progress check

5. Near resistance level
   → Monitor rejection risk
```

---

## MULTIPLE POSITIONS MONITORING

### Priority System

```
When monitoring 2+ positions:

Priority 1: Largest P/L (protect!)
Priority 2: Closest to SL (risk!)
Priority 3: Most time elapsed (timing!)
Priority 4: Newest position (setup freshness)

Check в priority order
Allocate attention accordingly
```

### Correlation Watch

```
If holding multiple alts:

Scenario: ETH long + SOL long + AVAX long

Check BTC every 30 mins:
→ BTC turns → ALL alts at risk
→ Exit based on severity

If BTC -1%: Monitor closely
If BTC -2%: Exit weakest position
If BTC -3%: Exit all alts ⚠️
```

---

## ЖУРНАЛИРОВАНИЕ МОНИТОРИНГА

### Что Записывать

```
Каждый significant update:

[Time] | [Symbol] | [Action/Observation]

14:00 | ETH | Entry executed $3,000
14:30 | ETH | +0.5%, indicators stable
15:15 | ETH | +2.0%, SL moved to BE ✅
16:30 | ETH | +3.5%, TP1 hit, 50% closed ✅
18:00 | ETH | +4.2%, trailing activated
19:30 | ETH | +2.8%, trailing hit, exit ✅

Final: +3.3% avg, 5.5h duration
Lessons: Trailing gave extra +$0.30 vs fixed TP
```

---

## ФИНАЛЬНЫЕ РЕКОМЕНДАЦИИ

**Мониторинг Принципы:**

1. **Регулярность:** Check по schedule
2. **Объективность:** Follow indicators, не emotions
3. **Действия:** Act on warnings немедленно
4. **Документация:** Log all significant events
5. **Дисциплина:** Follow plan mechanically

**Remember:**

> "Good entry + poor monitoring = mediocre result  
> Average entry + great monitoring = great result"

Monitoring делает разницу! 📊

---

*Версия 1.0 - Optimized для active position management*
