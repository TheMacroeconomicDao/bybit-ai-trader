# ULTIMATE UI/UX DESIGN PROMPT
## Comprehensive Trading System Interface Design

**Дата:** 2025-11-24  
**Версия:** 1.0 COMPREHENSIVE  
**Цель:** Спроектировать максимально функциональный и удобный интерфейс для AI-powered торговой системы

---

## 🎯 ЗАДАЧА

Спроектировать современный, интуитивный и мощный интерфейс для **AI Trading Copilot**, который объединяет:
- 🤖 **AI-ассистента** (автономный анализ, рекомендации, обучение)
- 📊 **Традиционные трейдерские инструменты** (графики, индикаторы, терминал)
- ⚡ **Автоматизацию** (мониторинг 24/7, авто-действия, риск-менеджмент)

---

## 📚 КОНТЕКСТ ПРОЕКТА

### Текущая Архитектура:

```
┌─────────────────────────────────────────┐
│         TRADER (Пользователь)          │
└──────────────┬──────────────────────────┘
               │
     ┌─────────┴──────────┐
     ↓                    ↓
┌────────────┐      ┌────────────┐
│  WebUI     │      │  Cursor    │
│ (Frontend) │      │   (IDE)    │
└─────┬──────┘      └─────┬──────┘
      │                   │
      ↓                   ↓
┌────────────────────────────────┐
│      AI Agent (Qwen/Claude)    │
│  - Natural language interface  │
│  - Multi-step reasoning        │
│  - Tool calling                │
└──────────┬─────────────────────┘
           │
     ┌─────┴─────┐
     ↓           ↓
┌──────────┐ ┌──────────────┐
│Knowledge │ │  MCP Servers │
│   Base   │ │  (31 tools)  │
└──────────┘ └──────┬───────┘
                    │
              ┌─────┴─────┐
              ↓           ↓
         ┌────────┐  ┌─────────┐
         │ Bybit  │  │ Signal  │
         │  API   │  │Tracker  │
         └────────┘  └─────────┘
```

### Доступные Возможности (31 MCP Tool):

**📊 Market Data (6 tools):**
1. get_ticker - текущие цены
2. get_kline - OHLCV свечи
3. get_orderbook - глубина рынка
4. get_market_info - обзор рынка
5. get_trades - последние сделки
6. get_instrument_info - детали инструмента

**🧠 Advanced Analysis (3 tools):**
7. get_ml_rsi - ML-enhanced RSI
8. get_market_structure - структура рынка (Order Blocks, FVG, BOS)
9. get_order_blocks - институциональные зоны

**💼 Account Data (3 tools):**
10. get_wallet_balance - баланс кошелька
11. get_positions - открытые позиции
12. get_order_history - история ордеров

**⚡ Trading Operations (6 tools):**
13. place_order - открыть позицию
14. close_position - закрыть позицию
15. modify_position - изменить SL/TP
16. cancel_order - отменить ордер
17. move_to_breakeven - перевести в breakeven
18. activate_trailing_stop - активировать trailing stop

**🔍 Market Scanning (4 tools):**
19. scan_market - умный сканер
20. find_oversold_assets - перепроданные активы (RSI <30)
21. find_overbought_assets - перекупленные активы (RSI >70)
22. find_breakout_opportunities - BB squeeze breakouts

**✅ Entry Validation (1 tool):**
23. validate_entry - валидация точки входа (score 0-10)

**📡 Position Monitoring (2 tools):**
24. start_position_monitoring - real-time мониторинг
25. stop_position_monitoring - остановить мониторинг

**💸 Fund Management (1 tool):**
26. transfer_funds - перевод между счетами

**📈 Analysis (5 tools):**
27. analyze_asset - полный TA на всех TF
28. calculate_indicators - расчёт индикаторов
29. detect_patterns - поиск паттернов
30. find_support_resistance - уровни S/R
31. get_btc_correlation - корреляция с BTC

---

## 👤 ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ

### Кто наш трейдер?

**Уровень опыта:**
- 🟢 Начинающий: Нужны подсказки, обучение, простота
- 🟡 Средний: Знает основы, хочет автоматизировать рутину
- 🔴 Профессионал: Нужна скорость, детализация, кастомизация

**Стиль торговли:**
- ⚡ Scalping (секунды-минуты)
- 📊 Day Trading (минуты-часы)
- 📈 Swing Trading (дни-недели)
- 🎯 Position Trading (недели-месяцы)

**Предпочтения:**
- 🤖 AI-первый: Доверяет AI, хочет минимум ручной работы
- ⚖️ Гибридный: AI + Manual control
- 🎮 Manual-первый: AI только как помощник

---

## 📊 НЕОБХОДИМЫЕ ДАННЫЕ ДЛЯ ТРЕЙДЕРА

### 1. **REAL-TIME MARKET DATA**

**Основное:**
- ✅ Текущая цена актива
- ✅ 24h изменение (%, $)
- ✅ 24h объём торговли
- ✅ Bid/Ask спред
- ✅ Last trade price & time

**Глубина рынка:**
- ✅ Orderbook (топ 20-50 уровней)
- ✅ Визуализация ликвидности
- ✅ Whale orders (крупные заявки)
- ✅ Order flow (покупки vs продажи)

**Агрегированные данные:**
- ✅ Market sentiment (Fear & Greed)
- ✅ BTC dominance
- ✅ Топ gainers/losers
- ✅ Volatility index

---

### 2. **TECHNICAL ANALYSIS**

**Индикаторы (multi-timeframe):**
- ✅ RSI (14, 21) + ML-RSI
- ✅ MACD (12, 26, 9)
- ✅ Bollinger Bands (20, 2)
- ✅ EMA (9, 21, 50, 200)
- ✅ ATR (14)
- ✅ ADX (14) - trend strength
- ✅ Stochastic (14, 3, 3)
- ✅ Volume indicators

**Levels & Zones:**
- ✅ Support/Resistance levels
- ✅ Order Blocks (bullish/bearish)
- ✅ Fair Value Gaps (FVG)
- ✅ Break of Structure (BOS)
- ✅ Change of Character (ChoCh)
- ✅ Liquidity zones
- ✅ Volume Profile (POC, Value Area)

**Patterns:**
- ✅ Candlestick patterns (27 типов)
- ✅ Chart patterns (H&S, Double Top/Bottom, etc.)
- ✅ Divergences (RSI, MACD)
- ✅ Elliott Waves (опционально)

---

### 3. **AI INSIGHTS & RECOMMENDATIONS**

**Анализ:**
- ✅ Confluence Score (0-10)
- ✅ Probability of success (%)
- ✅ Entry recommendation (LONG/SHORT/WAIT)
- ✅ Confluence breakdown (что даёт points)
- ✅ Key factors (почему этот сигнал)
- ✅ Timeframe alignment
- ✅ Pattern reliability

**Entry Plan:**
- ✅ Recommended Entry Price
- ✅ Stop-Loss (ATR-based или level-based)
- ✅ Take-Profit (R:R минимум 1:2)
- ✅ Position size (based on % risk)
- ✅ Risk/Reward ratio
- ✅ Expected Value (EV)

**Warnings & Notes:**
- ⚠️ BTC correlation warning
- ⚠️ High volatility warning
- ⚠️ Low liquidity warning
- ⚠️ News events nearby
- 💡 Alternative entries
- 💡 Invalidation levels

---

### 4. **PORTFOLIO & RISK MANAGEMENT**

**Account Overview:**
- ✅ Total Balance (USDT)
- ✅ Available Balance
- ✅ Margin Used / Free Margin
- ✅ Unrealized P&L
- ✅ Realized P&L (daily, weekly, monthly)
- ✅ Win Rate %
- ✅ Average R:R
- ✅ Sharpe Ratio

**Active Positions:**
- ✅ Symbol
- ✅ Side (LONG/SHORT)
- ✅ Entry Price
- ✅ Current Price
- ✅ Size (quantity & $value)
- ✅ Leverage
- ✅ Unrealized P&L ($, %, R)
- ✅ Stop-Loss
- ✅ Take-Profit
- ✅ Distance to SL/TP
- ✅ Time in trade
- ✅ Status (monitoring, auto-actions enabled)

**Risk Metrics:**
- ✅ Current exposure ($)
- ✅ Max risk per trade (2%)
- ✅ Total portfolio risk
- ✅ Drawdown (current, max)
- ✅ Risk-adjusted returns

---

### 5. **HISTORICAL & TRACKING**

**Trade History:**
- ✅ Past trades (последние 100)
- ✅ Entry/Exit prices
- ✅ P&L per trade
- ✅ Duration
- ✅ R:R actual
- ✅ Tags (scalp, swing, AI-signal, manual)
- ✅ Notes

**Signal Quality Tracking:**
- ✅ AI signals published
- ✅ Success rate per pattern
- ✅ Success rate per timeframe
- ✅ Success rate per asset
- ✅ Average holding time
- ✅ Best/Worst performers

**Performance Analytics:**
- 📊 Equity curve
- 📊 Daily/Weekly/Monthly P&L
- 📊 Win/Loss distribution
- 📊 R-multiple distribution
- 📊 Trade frequency
- 📊 Best hours for trading

---

## 🎨 UI/UX DESIGN REQUIREMENTS

### 1. **LAYOUT ARCHITECTURE**

```
┌───────────────────────────────────────────────────────────┐
│  HEADER (Top Bar)                                         │
│  [Logo] [Market Status] [Balance] [P&L] [Profile] [⚙️]   │
└───────────────────────────────────────────────────────────┘
│
┌───────────┬──────────────────────────────┬────────────────┐
│           │                              │                │
│  SIDEBAR  │       MAIN WORKSPACE         │   AI PANEL     │
│           │                              │                │
│  - Watch  │  ┌────────────────────────┐  │ 🤖 AI Chat     │
│    list   │  │   CHART (TradingView)  │  │                │
│  - Scans  │  │   + Indicators         │  │ Top Signals:   │
│  - Alerts │  │   + Levels            │  │ 1. ETH LONG    │
│  - Tools  │  │   + AI Annotations    │  │ 2. BTC SHORT   │
│           │  └────────────────────────┘  │                │
│           │                              │ Quick Actions: │
│           │  ┌────────────────────────┐  │ [Scan Market]  │
│           │  │  POSITIONS & ORDERS    │  │ [Validate]     │
│           │  │  Active | Closed       │  │ [Monitor]      │
│           │  └────────────────────────┘  │                │
│           │                              │                │
└───────────┴──────────────────────────────┴────────────────┘
│
┌───────────────────────────────────────────────────────────┐
│  FOOTER (Status Bar)                                      │
│  [Connection] [MCP Status] [Last Update] [Notifications]  │
└───────────────────────────────────────────────────────────┘
```

---

### 2. **KEY UI COMPONENTS**

#### A. **AI CHAT INTERFACE** (Right Panel, Always Visible)

**Features:**
- 💬 Natural language queries
- 🎯 Context-aware suggestions
- 📊 Rich message formatting (charts, tables, code blocks)
- 🔗 Interactive elements (click to apply action)
- 📎 File attachments (import strategies, share signals)
- 🎨 Syntax highlighting для кода
- ⚡ Quick Actions buttons

**Example Interaction:**
```
USER: "Найди oversold активы с хорошим R:R"

AI: 🔍 Сканирую рынок...
    
    Найдено 3 возможности:
    
    1. ⭐ ETH/USDT - Confluence 8.2/10
       Entry: $3,250 | SL: $3,200 | TP: $3,400
       R:R = 1:3 | Probability: 73%
       
       [View Details] [Validate] [Open Position]
    
    2. ⚡ SOL/USDT - Confluence 7.8/10
       ...
```

#### B. **MARKET SCANNER** (Sidebar Tab)

**Filters:**
- 🎯 Strategy type (Oversold, Breakout, Reversal, Momentum)
- 📊 Timeframe (5m, 15m, 1h, 4h, 1d)
- 💰 Min volume
- 📈 Min confluence score
- 🎲 Min probability
- 💱 Market type (Spot, Futures)

**Results Display:**
```
┌─────────────────────────────────────┐
│ ETH/USDT               [⭐ 8.2/10] │
│ 💰 $3,250  ↗ +2.3%     Long Setup  │
│ 🎯 Entry: $3,250  SL: $3,200       │
│ 📊 Vol: High  P: 73%   R:R: 1:3    │
│ [Chart] [Details] [Trade]          │
├─────────────────────────────────────┤
│ SOL/USDT               [⚡ 7.8/10] │
│ ...                                 │
└─────────────────────────────────────┘
```

#### C. **CHART WORKSPACE** (Main Area)

**Integration:**
- 📊 TradingView embedded chart (или custom WebGL chart)
- 🎨 AI-generated annotations:
  - Entry zones (green box)
  - Stop-loss zones (red line)
  - Take-profit zones (blue line)
  - Support/Resistance levels (dashed)
  - Order Blocks (highlighted boxes)
  - FVG (gap markers)
- 🔔 Real-time price alerts
- 📍 Position entry markers
- 🎯 Target achievement indicators

**Timeframe Sync:**
- Multi-timeframe view (split screen 2/4/6 charts)
- Single click to switch TF
- TF alignment indicator (все TF согласованы = зелёный)

#### D. **POSITIONS PANEL** (Bottom of Main Area)

**Columns:**
| Symbol | Side | Entry | Current | P&L | SL | TP | Time | Status | Actions |
|--------|------|-------|---------|-----|----|----|------|--------|---------|
| ETHUSDT | LONG | 3250 | 3280 | +30 (+0.92%) | 3200 | 3400 | 1h 23m | 📡 Monitoring | [Close] [Modify] |

**Quick Stats Row:**
```
Total P&L: +$125 (+2.3%)  |  Win Rate: 68%  |  Active: 2  |  Daily P&L: +$87
```

#### E. **ORDER ENTRY FORM** (Modal/Slide-out Panel)

**Fields:**
- 🎯 Symbol (autocomplete)
- ↕️ Side (LONG/SHORT toggle)
- 💰 Order type (Market/Limit)
- 📊 Quantity (auto-calculated from risk %)
- 💵 Entry Price (if Limit)
- 🛑 Stop-Loss (price or %)
- 🎯 Take-Profit (price or %)
- ⚖️ Risk (% of balance, default 2%)
- 🔢 Leverage (1x-125x slider)

**AI Assist Features:**
- ✅ Auto-fill from AI signal
- ✅ Validate entry before submit
- ✅ Show R:R calculation live
- ✅ Show position size in USDT
- ⚠️ Warnings (high risk, low R:R, etc.)

---

### 3. **ADVANCED FEATURES**

#### A. **SMART DASHBOARDS**

**Dashboard Types:**
1. **Overview** - Balance, P&L, Active positions, Top signals
2. **Analysis** - Market heatmap, Correlation matrix, Sentiment gauges
3. **Performance** - Equity curve, Trade stats, Win rate by strategy
4. **Risk** - Exposure breakdown, Drawdown chart, VAR analysis

**Customization:**
- Drag & drop widgets
- Save dashboard layouts
- Share dashboards (export JSON)

#### B. **MONITORING & ALERTS**

**Real-time Monitoring Panel:**
```
┌────────────────────────────────────┐
│ 📡 ACTIVE MONITORING (2 positions) │
├────────────────────────────────────┤
│ ETHUSDT LONG                       │
│ Entry: $3,250 → Current: $3,280    │
│ P&L: +$30 (+0.65R)                 │
│ ✅ Breakeven activated             │
│ ⏱️ 1h 23m in trade                 │
│ 🎯 Next: Move SL to +1R at $3,300  │
├────────────────────────────────────┤
│ BTCUSDT SHORT                      │
│ Entry: $103,000 → Current: $102,800│
│ P&L: +$200 (+0.43R)                │
│ ⚠️ Approaching reversal zone       │
│ 💡 Consider partial profit         │
└────────────────────────────────────┘
```

**Alert Types:**
- 📈 Price alerts
- 🎯 Target hit alerts
- 🛑 Stop-loss hit alerts
- ⚡ New signal alerts
- 📊 Confluence score > 8 alerts
- 🤖 AI recommendation alerts

#### C. **BACKTESTING & SIMULATION**

**Paper Trading Mode:**
- Toggle между real/paper
- Separate balance tracking
- Same UI/UX
- Performance comparison

**Strategy Backtester:**
- Import custom strategies
- Historical data replay
- Performance metrics
- Optimization suggestions

#### D. **EDUCATIONAL FEATURES**

**For Beginners:**
- 📚 Interactive tutorials
- 💡 Tooltips on hover
- 📖 Knowledge base integration
- 🎓 Trading academy (video courses)
- ❓ AI explains every decision

**Learning Mode:**
- AI предлагает, но не исполняет
- User must confirm understanding
- Quiz после каждой сделки
- Progress tracking

---

## 🎯 USER FLOW EXAMPLES

### Flow 1: AUTONOMOUS TRADING (AI-First)

```
1. User opens app
   ↓
2. AI automatically:
   - Scans market
   - Finds top 3 opportunities
   - Shows в sidebar: "3 новых сигнала"
   ↓
3. User clicks "View Signals"
   ↓
4. AI Panel shows:
   - Detailed analysis
   - Entry plan
   - Risk assessment
   ↓
5. User clicks [Open Position]
   ↓
6. Order form pre-filled
   ↓
7. User reviews & confirms
   ↓
8. Position opened
   ↓
9. AI starts monitoring 24/7
   ↓
10. AI automatically:
    - Moves to breakeven at +1R
    - Activates trailing stop at +2R
    - Closes at TP or reversal signal
    ↓
11. User receives notification with P&L
```

---

### Flow 2: MANUAL TRADING (AI-Assisted)

```
1. User selects asset from watchlist
   ↓
2. Chart opens with auto-loaded indicators
   ↓
3. User spots potential setup
   ↓
4. User asks AI: "Validate this LONG"
   ↓
5. AI analyzes:
   - Multi-timeframe
   - Confluence score
   - Pattern reliability
   ↓
6. AI responds:
   "⚠️ Score 6.5/10 - Not recommended
   Issues:
   - BTC correlation high (0.87)
   - H4 RSI overbought (72)
   - Low volume
   
   Suggest: Wait for RSI <60 or BTC stabilization"
   ↓
7. User decides:
   a) Follow AI → Wait
   b) Override → Open anyway (with warning logged)
   ↓
8. If opened:
   - AI monitors
   - AI suggests adjustments
   - User can manual override anytime
```

---

### Flow 3: RESEARCH & LEARNING

```
1. User asks: "Explain Order Blocks"
   ↓
2. AI provides:
   - Text explanation
   - Visual diagram
   - Real chart examples
   - Video link (if available)
   ↓
3. User asks: "Show me OB on ETHUSDT"
   ↓
4. AI:
   - Opens ETHUSDT chart
   - Highlights Order Blocks
   - Explains each one
   - Shows how to trade them
   ↓
5. User asks: "Find assets with OB near price"
   ↓
6. AI scans and shows results
   ↓
7. User selects one
   ↓
8. AI provides full analysis
```

---

## 🎨 DESIGN PRINCIPLES

### 1. **CLARITY FIRST**
- Информация должна быть немедленно понятной
- Используйте цвета осознанно (зелёный=прибыль, красный=убыток)
- Критическая информация = крупный шрифт
- Secondary information = smaller, greyed out

### 2. **SPEED MATTERS**
- Hotkeys для всех основных действий
- Quick actions всегда доступны
- Minimize clicks to execute
- Instant feedback на все действия

### 3. **PROGRESSIVE DISCLOSURE**
- Показывать minimal info по умолчанию
- Детали = click to expand
- Advanced features = hidden до активации
- Beginners = guided mode ON по умолчанию

### 4. **TRUST & TRANSPARENCY**
- AI должен объяснять каждое решение
- Show "why" не только "what"
- Вероятности и confidence всегда видимы
- Можно всегда проверить источник данных

### 5. **CONSISTENCY**
- Одинаковые паттерны во всём UI
- Одинаковые цвета для одинаковых концептов
- Предсказуемое поведение
- Standard iconography

---

## 🛠️ TECHNOLOGY STACK RECOMMENDATIONS

### Frontend:
- **Framework:** React + TypeScript (или Next.js for SSR)
- **UI Library:** shadcn/ui (Tailwind-based, highly customizable)
- **Charting:** TradingView Lightweight Charts или Recharts
- **State Management:** Zustand (или Redux Toolkit)
- **Real-time:** WebSocket (Socket.io)
- **Forms:** React Hook Form + Zod validation
- **Styling:** Tailwind CSS + CSS Modules
- **Icons:** Lucide React (или Heroicons)

### Backend:
- **API:** FastAPI (Python) - уже используется в MCP server
- **WebSocket:** FastAPI WebSocket support
- **Database:** PostgreSQL (trades, signals) + Redis (cache, sessions)
- **AI Integration:** OpenRouter API или Ollama (local)

### Infrastructure:
- **Hosting:** Vercel (frontend) + Railway (backend)
- **Monitoring:** Sentry (errors) + LogRocket (sessions)
- **Analytics:** Mixpanel (user behavior)

---

## 📋 PRIORITY ROADMAP

### Phase 1: MVP (Weeks 1-4)
- [ ] Basic layout (header, sidebar, main, footer)
- [ ] AI Chat interface
- [ ] Market scanner с фильтрами
- [ ] Chart integration (TradingView Lightweight)
- [ ] Positions panel
- [ ] Order entry form
- [ ] Real-time price updates

### Phase 2: Core Features (Weeks 5-8)
- [ ] Advanced TA indicators on chart
- [ ] AI annotations (OB, FVG, S/R levels)
- [ ] Position monitoring panel
- [ ] Alert system
- [ ] Performance dashboard
- [ ] Trade history

### Phase 3: Advanced (Weeks 9-12)
- [ ] Multi-chart view
- [ ] Custom dashboards
- [ ] Backtesting interface
- [ ] Paper trading mode
- [ ] Signal quality tracking
- [ ] Educational features

### Phase 4: Polish & Optimize (Weeks 13-16)
- [ ] Performance optimization
- [ ] Mobile responsive
- [ ] Dark/Light themes
- [ ] Customizable hotkeys
- [ ] Export/Import settings
- [ ] Social features (share signals)

---

## 🎓 MOCKUP EXAMPLES

### Example 1: Main Trading View

```
┌─────────────────────────────────────────────────────────────────────────┐
│ 🤖 TraderAI  |  ⚡ BTCUSDT $103,250 (+2.3%)  |  💰 $5,420  |  📊 +$125 │
└─────────────────────────────────────────────────────────────────────────┘
│
┌──────────┬──────────────────────────────────────────────┬───────────────┐
│ Watchlist│              BTCUSDT - 1H Chart              │  🤖 AI Panel  │
│──────────│──────────────────────────────────────────────│───────────────│
│✨ Scans  │  ┌────────────────────────────────────────┐ │💬 Ask me      │
│  • Over  │  │ 📊 Price: $103,250                    │ │   anything... │
│    sold  │  │ [Chart with candlesticks, indicators] │ │               │
│  • Break │  │ SL: $102,800 | TP: $104,500          │ │📊 Top Signals:│
│    out   │  └────────────────────────────────────────┘ │               │
│──────────│                                              │1.⭐ETH 8.2/10 │
│📋 Lists  │  ┌────────────────────────────────────────┐ │  LONG $3,250  │
│  • My    │  │ Active Positions (2)                   │ │  [Details]    │
│    Favs  │  ├──────┬────┬──────┬────┬─────┬────────┤ │               │
│  • Top5  │  │ ETH  │LONG│ 3250 │3280│ +30 │📡 Mon  │ │2.⚡SOL 7.8/10 │
│  • Crypto│  │ BTC  │SHORT│103k │102.8│+200│📡 Mon  │ │  SHORT $142   │
│──────────│  └──────┴────┴──────┴────┴─────┴────────┘ │  [Details]    │
│🔔 Alerts │                                              │               │
│  • Price │  Stats: Total P&L: +$230 | Win Rate: 68%   │🎯 Actions:    │
│  • Signal│                                              │[Scan Market]  │
│──────────│──────────────────────────────────────────────│[Validate]     │
└──────────┴──────────────────────────────────────────────┴───────────────┘
│ 🟢 Connected | MCP: ✅ | Last: 2s ago | 3 new alerts                   │
└─────────────────────────────────────────────────────────────────────────┘
```

### Example 2: AI Signal Detail View

```
┌────────────────────────────────────────────────┐
│ 🤖 AI Analysis: ETHUSDT                       │
├────────────────────────────────────────────────┤
│                                                │
│ ⭐ Confluence Score: 8.2/10                    │
│ 🎯 Recommended: LONG                           │
│ 📊 Probability: 73%                            │
│ ⚖️ Risk/Reward: 1:3                           │
│                                                │
│ 💰 Entry Plan:                                 │
│   Entry: $3,250                                │
│   Stop-Loss: $3,200 (-1.54%)                  │
│   Take-Profit: $3,400 (+4.62%)                │
│   Position Size: 15.38 ETH ($50 risk = 2%)    │
│                                                │
│ 📈 Why this setup?                             │
│   ✅ RSI oversold on 1H (28.4)                │
│   ✅ Bullish OB at $3,240-$3,260              │
│   ✅ FVG fill complete                        │
│   ✅ BTC correlation low (0.32)               │
│   ✅ Volume spike +180%                       │
│   ✅ 4H trend still bullish                   │
│                                                │
│ ⚠️ Considerations:                            │
│   • News event in 4h (FOMC)                   │
│   • Consider reducing size by 50%             │
│                                                │
│ ⏰ Timeframe Alignment:                        │
│   5m: ⚪ Neutral                              │
│   15m: 🟢 Bullish                            │
│   1H: 🟢 Bullish                             │
│   4H: 🟢 Bullish                             │
│   1D: 🟡 Sideways                            │
│                                                │
│ [View Chart] [Validate] [Open Position]       │
└────────────────────────────────────────────────┘
```

---

## ✅ SUCCESS METRICS

Интерфейс считается успешным если:

1. **Speed to Trade:** < 30 секунд от идеи до исполнения
2. **Learning Curve:** Новичок может торговать < 1 часа
3. **AI Trust:** Users follow AI recommendations >60% времени
4. **Monitoring:** 95% позиций открываются с мониторингом
5. **Win Rate:** >55% profitable trades для следующих AI
6. **User Retention:** >70% active after 30 days
7. **Task Completion:** >90% users complete intended actions
8. **Error Rate:** <5% ошибочных inputs требуют correction

---

## 🎯 FINAL DELIVERABLES

После проектирования UI/UX необходимо создать:

1. **Wireframes** (low-fidelity) - основная структура
2. **Mockups** (high-fidelity) - детальный дизайн с цветами
3. **Prototype** (interactive) - кликабельный прототип в Figma
4. **Component Library** - React components
5. **Style Guide** - цвета, типография, spacing
6. **User Flows** - диаграммы для каждого сценария
7. **Technical Specs** - детальное описание для разработки

---

## 📚 RESOURCES & REFERENCES

**Inspiration:**
- TradingView (chart interaction)
- 3Commas (bot management)
- Binance (order entry)
- Bloomberg Terminal (data density)
- Notion (AI chat interface)

**Design Systems:**
- shadcn/ui - https://ui.shadcn.com/
- Radix UI - https://www.radix-ui.com/
- Tailwind UI - https://tailwindui.com/

**Trading UI Examples:**
- https://www.tradingview.com/
- https://www.binance.com/en/trade/
- https://www.coinbase.com/advanced-trade

---

**КОНЕЦ ПРОМПТА**

Этот промпт служит comprehensive guide для проектирования UI/UX. Используйте его в новом чате с AI дизайнером или фронтенд-разработчиком для создания детальных mockups и prototype.