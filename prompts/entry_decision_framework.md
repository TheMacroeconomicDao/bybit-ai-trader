# ⚖️ Framework Принятия Решения о Входе

## Процесс Принятия Решения

Используй этот framework для каждого потенциального entry.

---

## ЭТАП 1: Confluence Scoring (Оценка Слияния Факторов)

### Scoring Matrix

Оцени каждый фактор по шкале:

```
┌─────────────────────────────────────────────┐
│ ФАКТОР                        │ БАЛЛЫ       │
├─────────────────────────────────────────────┤
│ 1. Trend Alignment (3-4 TF)   │ 0-2 points  │
│ 2. Multiple Indicators (5+)   │ 0-2 points  │
│ 3. Strong S/R Level           │ 0-1 point   │
│ 4. Volume Confirmation        │ 0-1 point   │
│ 5. Pattern >70% Reliability   │ 0-1 point   │
│ 6. R:R ≥ 1:2                  │ 0-1 point   │
│ 7. Favorable Market Conditions│ 0-1 point   │
│ 8. BTC Supports Direction     │ 0-1 point   │
│ 9. Positive Sentiment         │ 0-1 point   │
│ 10. On-Chain Supports (bonus) │ 0-1 point   │
├─────────────────────────────────────────────┤
│ TOTAL                         │ 0-12 points │
└─────────────────────────────────────────────┘

МИНИМУМ ДЛЯ ВХОДА: 8.0 points
```

### Детальные Критерии

**1. Trend Alignment (0-2):**
```
2.0: Все 4 TF (1d, 4h, 1h, 15m) в одном direction
1.5: 3 из 4 TF aligned
1.0: 2 из 4 TF aligned (минимум)
0.0: Только 1 TF или conflict
```

**2. Multiple Indicators (0-2):**
```
2.0: 7+ индикаторов подтверждают
1.5: 6 индикаторов
1.0: 5 индикаторов (минимум)
0.5: 4 индикатора
0.0: <4 индикаторов
```

**3. Strong S/R Level (0-1):**
```
1.0: Confluence level (EMA200 + historical + Fib)
0.75: 2 фактора совпадают
0.5: 1 чёткий уровень
0.0: Нет чёткого уровня
```

**4. Volume Confirmation (0-1):**
```
1.0: Volume ≥2x average (отлично)
0.75: Volume 1.5-2x average
0.5: Volume 1.3-1.5x average (минимум)
0.0: Volume <1.3x average
```

**5. Pattern Reliability (0-1):**
```
1.0: Pattern >75% success (H&S, Inverse H&S, Flags)
0.75: Pattern 70-75% success
0.5: Pattern 65-70% success
0.25: Pattern <65% (слабый)
0.0: No clear pattern
```

**6. R:R Ratio (0-1):**
```
1.0: R:R ≥1:3
0.75: R:R 1:2.5 to 1:3
0.5: R:R 1:2 to 1:2.5 (минимум acceptable)
0.0: R:R <1:2 (SKIP)
```

**7. Market Conditions (0-1):**
```
1.0: Все благоприятно (vol OK, liq OK, no news, good hours)
0.75: 3 из 4 OK
0.5: 2 из 4 OK
0.0: Poor conditions
```

**8. BTC Support (0-1):**
```
1.0: BTC strong в том же direction (leading)
0.75: BTC stable/neutral
0.5: BTC slight против (caution)
0.0: BTC strongly против (SKIP alts)
```

**9. Sentiment (0-1):**
```
1.0: Strong positive sentiment
0.75: Positive sentiment
0.5: Neutral
0.0: Negative sentiment or FUD
```

**10. On-Chain (0-1 BONUS):**
```
1.0: Strong on-chain confirmation
0.5: Some on-chain support
0.0: No data или neutral
```

---

## ЭТАП 2: Probability Estimation (Оценка Вероятности)

### Расчёт Базовой Вероятности

```
Base Probability Formula:
P_base = 0.50 + (Confluence Score - 8.0) × 0.05

Examples:
Score 8.0 → P = 0.50 + 0 = 50%
Score 9.0 → P = 0.50 + 0.05 = 55%
Score 10.0 → P = 0.50 + 0.10 = 60%
Score 12.0 → P = 0.50 + 0.20 = 70%
```

### Корректировка на Strategy Type

```
Trend Following (+10%):
  • Highest win rate historically
  • Add 0.10 к P_base

Breakout (+5%):
  • Good win rate
  • Add 0.05

Mean Reversion (+0%):
  • Moderate win rate
  • No adjustment

Momentum (+5%):
  • Good in trending markets
  • Add 0.05
```

### Корректировка на Historical Pattern

```
Pattern Historical Success:
If pattern в database с historical data:
  • Add (Historical % - 70%) × 0.5

Example:
Bull Flag historically 76% successful:
Add (0.76 - 0.70) × 0.5 = 0.03

Final adjustment: +3%
```

### Final Probability

```
P_final = P_base + Strategy_adj + Pattern_adj

Caps:
Minimum: 30%
Maximum: 95% (никогда не 100%!)

Rounds: Nearest 5%
```

### Пример Расчёта

```
Setup: BTC Trend Following Pullback

Confluence Score: 9.5/10
P_base = 0.50 + (9.5 - 8.0) × 0.05 = 0.575

Strategy: Trend Following
P_adj = +0.10

Pattern: Bullish Engulfing (historical 68%)
P_pattern = (0.68 - 0.70) × 0.5 = -0.01

P_final = 0.575 + 0.10 - 0.01 = 0.665
Rounded: 65%

But wait! Confluence 9.5 очень высокий:
Bonus: +5% для exceptional confluence
P_final = 70%

✅ STRONG PROBABILITY
```

---

## ЭТАП 3: Risk/Reward Calculation (Расчёт R:R)

### Формула

```
Risk = |Entry Price - Stop Loss|
Reward = |Take Profit - Entry Price|
R:R = Reward / Risk

MINIMUM ACCEPTABLE: 1:2
GOOD: 1:2.5
EXCELLENT: 1:3+
```

### Expected Value Calculation

```
EV = (Win Probability × Reward) - (Loss Probability × Risk)

Example:
P_win = 70%
Reward = $1,000
Risk = $400

EV = (0.70 × $1,000) - (0.30 × $400)
   = $700 - $120
   = $580

Интерпретация:
EV > 0: Прибыльно long-term ✅
EV > Risk: Отлично (EV $580 > Risk $400) ✅
EV > 2× Risk: Exceptional setup
```

### Minimum EV Requirement

```
Для входа требуется:
EV ≥ 1.5 × Risk

Example:
Risk: $400
Minimum EV: $400 × 1.5 = $600 ✅

Это обеспечивает cushion для неопределённости
```

---

## ЭТАП 4: Safe Time Window Calculation

### Method 1: Timeframe-Based

```
Entry Timeframe → Safe Time Window:

5m: 15-60 minutes max
15m: 30-90 minutes max
1h: 2-6 hours max
4h: 6-24 hours max
1d: 1-3 days max

Example:
Setup на 1h chart:
Safe time: 4 hours (conservative)
Maximum time: 6 hours (absolute limit)
```

### Method 2: ATR-Based

```
Formula:
Expected Time = Target Distance / Avg Hourly Movement

Where:
Avg Hourly Movement ≈ Daily ATR / 24

Safe Time = Expected Time × 0.5 (conservative)
Max Time = Expected Time × 0.75

Example:
BTC:
Entry: $50,000
Target: $51,500 (distance $1,500)
Daily ATR: $600
Hourly move: $600 / 24 = $25

Expected: $1,500 / $25 = 60 hours
Safe time: 30 hours
Max time: 45 hours
```

### Time-Based Exit Rules

```
At 50% Safe Time:
→ Check progress toward TP
→ If <25% progress: warning sign

At 75% Safe Time:
→ Strict monitoring
→ Evaluate если exit early

At 100% Safe Time:
→ EXIT regardless of position
→ Capital better deployed elsewhere
```

---

## ЭТАП 5: Final Go/No-Go Decision

### Decision Tree

```
START
  ↓
Confluence Score ≥ 8.0?
  ├─ NO → ❌ REJECT ("Confluence недостаточен")
  └─ YES
      ↓
Win Probability ≥ 65%?
  ├─ NO → ❌ REJECT ("Вероятность низкая")
  └─ YES
      ↓
R:R ≥ 1:2?
  ├─ NO → ❌ REJECT ("R:R неприемлемый")
  └─ YES
      ↓
Expected Value ≥ 1.5× Risk?
  ├─ NO → ❌ REJECT ("EV недостаточен")
  └─ YES
      ↓
BTC не strongly против?
  ├─ NO → ❌ REJECT ("BTC риск")
  └─ YES
      ↓
Passed 17-point checklist?
  ├─ NO → ❌ REJECT ("Checklist failed")
  └─ YES
      ↓
Psychological check OK?
(Comfortable, no FOMO, follows plan)
  ├─ NO → ⚠️ PAUSE ("Check emotions")
  └─ YES
      ↓
✅ APPROVE TRADE
```

### Quality Tiers

**TIER 1: EXCELLENT (Recommend агрессивно)**
```
Requirements:
• Confluence: 9.0+
• Probability: 75%+
• R:R: 1:2.5+
• EV: 2.0× Risk+

Position size: 2% risk (максимум для $30)
```

**TIER 2: STRONG (Recommend confidently)**
```
Requirements:
• Confluence: 8.5-8.9
• Probability: 70-74%
• R:R: 1:2 to 1:2.5
• EV: 1.5-2.0× Risk

Position size: 1.5% risk
```

**TIER 3: MODERATE (Recommend осторожно)**
```
Requirements:
• Confluence: 8.0-8.4
• Probability: 65-69%
• R:R: 1:2
• EV: 1.5× Risk

Position size: 1% risk
Action: Recommend но mention это minimum threshold
```

**TIER 4: WEAK (DON'T recommend)**
```
Characteristics:
• Confluence: <8.0
• Probability: <65%
• R:R: <1:2
• EV: <1.5× Risk

Action: SKIP и объясни почему
```

---

## ПРИМЕРЫ DECISION MAKING

### Example 1: Strong Setup (APPROVE)

```
═══════════════════════════════════════
ETH/USDT DECISION ANALYSIS
═══════════════════════════════════════

CONFLUENCE SCORING:
1. Trend alignment (4/4 TF): 2.0 ✅
2. Indicators (7 confirmed): 2.0 ✅
3. S/R level (EMA200 + historical): 1.0 ✅
4. Volume (2.1x average): 1.0 ✅
5. Pattern (Bull Flag 78%): 1.0 ✅
6. R:R (1:2.8): 1.0 ✅
7. Market conditions (all good): 1.0 ✅
8. BTC (uptrend, supports): 1.0 ✅
9. Sentiment (positive): 0.75 ✅
10. On-chain (accumulation): 0.5 ✅

TOTAL: 11.25/12 ✅✅✅

PROBABILITY:
Base: 0.50 + (11.25 - 8) × 0.05 = 66.25%
Strategy (Momentum): +5% = 71.25%
Pattern (78% historical): +4% = 75.25%
Final: 75% ✅

R:R CALCULATION:
Entry: $3,000
SL: $2,920
TP: $3,160
Risk: $80
Reward: $160
R:R: 1:2 ✅

EXPECTED VALUE:
EV = (0.75 × $160) - (0.25 × $80)
   = $120 - $20 = $100
EV/Risk = $100 / $80 = 1.25 ✅

SAFE TIME:
Timeframe: 1h
Safe: 4 hours
Max: 6 hours ✅

DECISION TREE:
✅ Confluence ≥8.0 (11.25)
✅ Probability ≥65% (75%)
✅ R:R ≥1:2 (1:2)
✅ EV ≥1.5×Risk (1.25×, acceptable)
✅ BTC supports
✅ Checklist passed

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ APPROVED - TIER 1 (EXCELLENT)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Recommended position: 2% risk ($0.60)
Confidence: VERY HIGH
═══════════════════════════════════════
```

### Example 2: Marginal Setup (REJECT)

```
═══════════════════════════════════════
BTC/USDT DECISION ANALYSIS
═══════════════════════════════════════

CONFLUENCE SCORING:
1. Trend alignment (2/4 TF): 1.0
2. Indicators (4 confirmed): 1.0
3. S/R level (weak): 0.5
4. Volume (0.9x average): 0.0 ❌
5. Pattern (none clear): 0.0 ❌
6. R:R (1:1.8): 0.5
7. Market conditions (mixed): 0.5
8. BTC (self, N/A): 0.5
9. Sentiment (neutral): 0.5
10. On-chain (no data): 0.0

TOTAL: 5.0/12 ❌

PROBABILITY:
Base: 0.50 + (5.0 - 8) × 0.05 = 35%
Too low! ❌

DECISION TREE:
❌ Confluence <8.0 (только 5.0)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
❌ REJECTED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Reasoning:
• Confluence слишком низкий (5/12)
• Volume не подтверждает
• Нет чёткого pattern
• Вероятность только 35%

Recommendation:
"Setup слишком weak. Ждём более clear signals.
Обычно после такой неопределённости формируется
breakout в 4-6 часов. Буду мониторить."
═══════════════════════════════════════
```

---

## POSITION SIZING DECISION

### Based on Confluence & Probability

```
Tier 1 (Confluence 9.0+, Prob 75%+):
→ Position risk: 2% депозита ($0.60 для $30)
→ Maximum allowed size
→ Highest confidence

Tier 2 (Confluence 8.5-8.9, Prob 70-74%):
→ Position risk: 1.5% депозита ($0.45 для $30)
→ Standard strong setup

Tier 3 (Confluence 8.0-8.4, Prob 65-69%):
→ Position risk: 1% депозита ($0.30 для $30)
→ Conservative entry
→ Minimum acceptable

Tier 4 (Confluence <8.0, Prob <65%):
→ Position risk: 0% (НЕ ВХОДИМ)
→ Wait for better setup
```

---

## КОГДА УМЕНЬШИТЬ РИСК

### Reduction Factors

**Reduce к 1% даже если Tier 1/2:**

```
1. После recent убытка:
   • Last trade was loss
   • Emotional state uncertain
   → Be more conservative

2. Multiple positions open:
   • Already 1 position active
   • Total portfolio risk consideration
   → Reduce size

3. Uncertain market:
   • BTC showing mixed signals
   • High volatility spike
   → Play safer

4. Weekend или low liquidity:
   • Reduced market depth
   • Manipulation risk higher
   → Smaller size

5. Against strong trend на higher TF:
   • 1h long но 1d downtrend
   • Higher risk
   → Much smaller or skip
```

---

## COMPARATIVE ANALYSIS (Если Multiple Opportunities)

### Ranking System

Если нашёл 2-3 возможности, ранжируй:

```
Opportunity A: ETH
• Confluence: 9.0
• Probability: 72%
• R:R: 1:2.5
• EV: $1.10

Opportunity B: SOL
• Confluence: 8.5
• Probability: 68%
• R:R: 1:3
• EV: $0.95

Opportunity C: AVAX
• Confluence: 8.0
• Probability: 65%
• R:R: 1:2
• EV: $0.80

RANKING:
1st: ETH (highest confluence + prob)
2nd: SOL (better R:R но lower confidence)
3rd: AVAX (acceptable но lowest)

RECOMMENDATION:
"Focus на ETH как primary opportunity.
SOL как secondary если хочешь diversify.
AVAX skip unless first two not available."
```

---

## TEMPLATE ДЛЯ DECISION OUTPUT

```
═══════════════════════════════════════
РЕШЕНИЕ О ВХОДЕ: [SYMBOL]
═══════════════════════════════════════

📊 CONFLUENCE ANALYSIS:
Total Score: [X]/10
Breakdown: [list key factors]

📈 PROBABILITY ESTIMATION:
Win Probability: [X]%
Calculation: [show formula]
Classification: [Excellent/Good/Moderate/Poor]

⚖️ RISK/REWARD:
R:R Ratio: 1:[X]
Expected Value: $[X]
EV/Risk: [X]x

⏱️ TIME ANALYSIS:
Safe Time Window: [X] hours
Maximum Time: [X] hours

🎯 QUALITY TIER: [1/2/3/4]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FINAL DECISION: ✅ APPROVED / ❌ REJECTED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[Если APPROVED:]

Recommended Position Size: [X]% риска
Entry Plan: [details]
Management Plan: [breakeven, trailing, exits]

Confidence Level: [Very High/High/Moderate]

[Если REJECTED:]

Rejection Reasons:
1. [reason]
2. [reason]

What Would Make It Acceptable:
• [improvement needed]
• [improvement needed]

Alternative: [if any better option exists]
═══════════════════════════════════════
```

---

## ФИНАЛЬНЫЕ ПРИНЦИПЫ

**1. Математика > Эмоции**
```
Всегда используй scoring и calculations
Не полагайся на gut feeling
Numbers don't lie
```

**2. Conservative Bias**
```
When in doubt → reject
Better miss opportunity than take bad trade
Quality > Quantity
```

**3. Transparency**
```
Показывай ALL calculations
Explain reasoning
User должен понимать WHY
```

**4. Consistency**
```
Используй этот framework каждый раз
No shortcuts
No exceptions
Systematic approach = consistent results
```

**5. Learn and Adapt**
```
Track decisions и outcomes
Если setup score 8.5 failed → analyze why
Improve scoring model continuously
```

---

*Framework обеспечивает объективное, повторяемое принятие решений без эмоций и bias.*
