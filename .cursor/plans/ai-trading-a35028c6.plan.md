<!-- a35028c6-677f-4d7e-8a8c-dea4d3dad5a7 18f76061-0896-4ae0-8bbd-848d8d7d688e -->
# Enhanced WebUI для Real-Time Мониторинга

## Анализ Текущего WebUI

Существующие компоненты в bybit-mcp/webui:

- AgentDashboard.ts - базовый dashboard
- ChatApp.ts - chat интерфейс
- DataVerificationPanel.ts - data verification
- DebugConsole.ts - debug логи
- ToolsManager.ts - управление tools
- Charts - TradingView Lightweight Charts
- Services - AI client, MCP client, config

## План Доработки

### Phase 1: Анализ и Подготовка

**1.1 Изучить существующую кодовую базу WebUI**

- Прочитать все компоненты в `/webui/src/components/`
- Понять архитектуру services (`mcpClient.ts`, `aiClient.ts`)
- Изучить существующие types (`mcp.ts`, `ai.ts`, `workflow.ts`)
- Определить что можно переиспользовать vs что создавать с нуля

**1.2 Спроектировать UI Layout**

- Main layout: Split view или Tab-based
- Рекомендация: Split 3-column layout для максимальной информативности:
  - Left: Chat + AI Reasoning (40% width)
  - Center: Trading Dashboard + Charts (35% width)  
  - Right: Alerts + Logs + Actions History (25% width)
- Responsive: адаптация при изменении размера

**1.3 Определить Data Flow**

- WebSocket connection к оба MCP servers
- Real-time updates от position_monitor
- Event streaming от AI reasoning
- Log aggregation из всех источников

### Phase 2: Новые Компоненты

**2.1 TradingDashboard.ts (НОВЫЙ!)**

Компонент для отображения trading state:

Секции:

- Portfolio Overview (balance, total P/L, daily P/L)
- Active Positions Table (symbol, entry, current, P/L%, SL, TP, time, status)
- Position Detail Card (при клике - детали позиции)
- Quick Actions (close position, modify SL/TP buttons)

Функции:

- `renderPortfolioOverview()` - общий обзор
- `renderPositionsTable()` - таблица позиций
- `renderPositionDetail(symbol)` - детали позиции
- `updatePositionRealtime(data)` - WebSocket updates
- `handleQuickAction(action, symbol)` - быстрые действия

Data sources:

- get_wallet_balance для balance
- get_positions для позиций
- WebSocket от position_monitor для updates

**2.2 AIReasoningViewer.ts (НОВЫЙ!)**

Компонент для визуализации AI thinking process:

Отображает:

- Current analysis step (Шаг 3/10: Multi-timeframe analysis...)
- Confluence scoring breakdown (visual bars для каждого фактора)
- Probability calculation (формулы и промежуточные результаты)
- Decision tree visualization (путь через decision tree)
- Self-check checklist (17 пунктов с галочками)

Функции:

- `renderAnalysisStep(step, data)` - текущий шаг
- `renderConfluenceScore(breakdown)` - визуальный scoring
- `renderProbabilityCalc(formula, result)` - calculation display
- `renderDecisionTree(path)` - decision path
- `renderSelfCheck(checklist)` - checklist с status

Data source:

- Parse AI responses для extraction reasoning
- Structure data в JSON format
- Real-time update по мере analysis

**2.3 AlertsPanel.ts (НОВЫЙ!)**

Панель для всех alerts и warnings:

Типы alerts:

- 🚨 CRITICAL (красные): SL близко, reversal pattern, BTC sharp move
- ⚠️ WARNING (жёлтые): approaching resistance, volume declining, time 75%
- ℹ️ INFO (синие): breakeven achieved, trailing activated, TP approaching
- ✅ SUCCESS (зелёные): position opened, TP hit, profit secured

Функции:

- `addAlert(type, message, symbol)` - добавить alert
- `renderAlerts()` - display all
- `clearAlert(id)` - dismiss alert
- `filterByType(type)` - фильтр по типу
- `playSound(type)` - звуковые уведомления (опционально)

Features:

- Auto-dismiss после X секунд для INFO
- Persistent для CRITICAL до user acknowledge
- Counter для unread alerts
- Filter и search

**2.4 ActionHistoryTimeline.ts (НОВЫЙ!)**

Timeline всех действий агента:

Отображает хронологию:

```
15:30 🔍 Market scan initiated
15:31 📊 Analyzed 47 assets  
15:32 🎯 Found 2 opportunities
15:33 ✅ ETH validated: 8.5/10 confluence
15:34 ⚡ Order placed: ETH Long $3,000
15:35 📡 Monitoring started
17:45 ⚡ ETH: SL moved to breakeven
19:20 ⚡ ETH: Trailing activated
21:30 ✅ ETH closed: +4.8% profit
```

Функции:

- `addAction(timestamp, type, message, details)` - log action
- `renderTimeline()` - chronological display
- `filterBySymbol(symbol)` - filter для specific asset
- `filterByType(type)` - filter по type (analysis, trading, monitoring)
- `exportHistory()` - export для journal

Features:

- Color coding по type action
- Expandable details (клик для full data)
- Auto-scroll to latest
- Search и filter
- Max 500 items (старые auto-archive)

**2.5 LiveLogViewer.ts (НОВЫЙ!)**

Real-time log viewer (tail -f style):

Показывает:

- MCP server logs (обоих серверов)
- AI decision logs
- Trading execution logs
- Error logs

Функции:

- `connectToLogStream()` - WebSocket к log sources
- `renderLog(entry)` - display log entry
- `filterByLevel(level)` - DEBUG/INFO/WARNING/ERROR
- `filterBySource(source)` - bybit-analysis/bybit-trading/AI
- `searchLogs(query)` - text search
- `clearLogs()` - clear display

Features:

- Color coding (ERROR red, WARNING yellow, INFO white, DEBUG gray)
- Auto-scroll toggle
- Level filtering
- Copy log entries
- Download logs

**2.6 EnhancedChartsPanel.ts (Улучшение существующего)**

Расширение существующего chart component:

Добавить:

- Indicator overlays (RSI, MACD, BB прямо на графике)
- Multi-timeframe tabs (5m, 15m, 1h, 4h, 1d)
- Entry/SL/TP markers на графике (visual lines)
- Pattern annotations (показывать detected patterns)
- Confluence score display на графике

Функции (добавить к существующим):

- `addIndicatorOverlay(indicator, data)` - индикаторы
- `markEntryLevels(entry, sl, tp)` - визуальные линии
- `annotatePattern(pattern, location)` - pattern markers
- `displayConfluence(score)` - score overlay

### Phase 3: UI Layout Organization

**3.1 Main Layout Component (MainLayout.ts)**

Создать responsive 3-column layout:

```typescript
// Структура:
<div class="main-layout">
  <div class="column-left">   // 40% width
    <ChatApp />              // Top half
    <AIReasoningViewer />    // Bottom half
  </div>
  
  <div class="column-center"> // 35% width
    <TradingDashboard />     // Top third
    <EnhancedCharts />       // Middle third
    <PositionDetails />      // Bottom third
  </div>
  
  <div class="column-right">  // 25% width
    <AlertsPanel />          // Top quarter
    <ActionHistory />        // Middle half
    <LiveLogViewer />        // Bottom quarter
  </div>
</div>
```

Features:

- Resizable columns (drag dividers)
- Collapsible panels
- Full-screen mode для любой секции
- Save layout preferences в localStorage

**3.2 Navigation Tabs (опциональный режим)**

Для тех кто предпочитает tabs вместо split:

Tabs:

1. 📊 Overview (Dashboard + Charts)
2. 💬 AI Chat (Chat + Reasoning)
3. 📡 Monitoring (Positions + Alerts)
4. 📜 History (Actions + Logs)
5. ⚙️ Settings

Toggle между Split View и Tab View в settings.

**3.3 Styling Enhancement**

Улучшить существующие стили:

- Consistent color scheme (trading red/green)
- Professional typography
- Smooth animations
- Status indicators (🟢🟡🔴)
- Progress bars для targets
- Sparklines для mini charts

CSS файлы обновить:

- `trading-dashboard.css` (новый)
- `ai-reasoning.css` (новый)
- `alerts-panel.css` (новый)
- `action-history.css` (новый)
- `live-logs.css` (новый)
- `main-layout.css` (новый)
- Обновить `variables.css` с trading colors

### Phase 4: Data Integration

**4.1 WebSocket Integration для Real-time Updates**

Создать `tradingDataService.ts`:

Connections:

- WebSocket к bybit-mcp HTTP server (SSE)
- WebSocket к position_monitor (Python)
- Polling fallback если WS fails

Функции:

- `connectToPositionMonitor()` - position updates
- `connectToMCPServer()` - tool responses
- `subscribeToSymbol(symbol)` - price updates для symbol
- `handlePositionUpdate(data)` - обработка updates
- `handleAlert(alert)` - новые alerts
- `handleAction(action)` - logged actions

Emit events для components:

- `onPositionUpdate` → TradingDashboard
- `onAlert` → AlertsPanel
- `onAction` → ActionHistory
- `onLog` → LiveLogViewer

**4.2 AI Reasoning Parser (aiReasoningParser.ts)**

Парсинг AI responses для extraction structured data:

Functions:

- `parseAnalysisSteps(response)` - extract шаги анализа
- `parseConfluenceScore(response)` - extract scoring breakdown
- `parseProbability(response)` - extract probability calc
- `parseDecisionPath(response)` - extract decision tree path
- `parseSelfCheck(response)` - extract checklist results

Regex patterns для extraction:

- Confluence: `Confluence: (\d+\.?\d*)/10`
- Probability: `Вероятность: (\d+)%`
- Steps: `Шаг \d+:` patterns
- Checklist: `\[✅\|❌\]` patterns

Return structured JSON для visualization.

**4.3 Position Data Aggregator (positionAggregator.ts)**

Агрегация данных о позициях из multiple sources:

Sources:

- get_positions (snapshot)
- WebSocket updates (real-time)
- AI analysis (reasoning для position)
- Historical data (entry reasoning, changes)

Aggregated model:

```typescript
{
  symbol: "ETHUSDT",
  entry: 3000,
  current: 3085,
  pnl: 2.8,
  pnl_usd: 0.84,
  sl: 2920,
  tp: 3160,
  time_in_trade: "4h 25m",
  safe_time_window: "8h",
  status: "healthy", // healthy, warning, critical
  ai_confidence: 8.5,
  entry_reasoning: "Trend following pullback...",
  last_action: "SL moved to breakeven",
  alerts: [...],
  history: [...]
}
```

Functions:

- `aggregatePositionData(symbol)` - combine all sources
- `updateRealtime(symbol, newData)` - merge updates
- `calculateMetrics(position)` - P/L, time, progress
- `determineStatus(position)` - health status

### Phase 5: Advanced Features

**5.1 Confluence Visualizer (confluenceViz.ts)**

Visual representation confluence scoring:

Display как horizontal bar chart:

```
Trend Alignment:     ████████░░ 1.8/2.0
Indicators:          ██████████ 2.0/2.0
S/R Level:           ███████░░░ 0.7/1.0
Volume:              ██████████ 1.0/1.0
Pattern:             ██████████ 1.0/1.0
R:R:                 ███████░░░ 0.7/1.0
Conditions:          ████████░░ 0.8/1.0
BTC Support:         ██████████ 1.0/1.0
Sentiment:           ████████░░ 0.75/1.0
On-Chain:            █████░░░░░ 0.5/1.0
─────────────────────────────────────
TOTAL:               ████████░░ 9.25/12
```

Color coding:

- Green: ≥0.75 of max
- Yellow: 0.5-0.75
- Red: <0.5

**5.2 Decision Tree Visualizer (decisionTreeViz.ts)**

Интерактивная визуализация decision path:

```
START
  ↓
[✅] Confluence ≥8.0? (9.25)
  ↓
[✅] Probability ≥65%? (73%)
  ↓
[✅] R:R ≥1:2? (1:2)
  ↓
[✅] EV ≥1.5×Risk? (2.1×)
  ↓
[✅] BTC OK? (Yes)
  ↓
[✅] Checklist passed? (16/17)
  ↓
✅ APPROVED - STRONG SETUP
```

Interactive: hover для details на каждом шаге.

**5.3 Performance Analytics (performanceAnalytics.ts)**

Отображение trading statistics:

Metrics:

- Total trades (today, week, month, all-time)
- Win rate % (visual progress circle)
- Average R:R achieved
- Best/Worst trades
- Profit curve chart
- Drawdown chart
- Win/Loss streak current

Auto-calculate из Action History.

**5.4 Market Heatmap (marketHeatmap.ts)**

Visual heatmap всего рынка:

Display:

- Grid с top 50 assets по volume
- Color по change % (green/red gradient)
- Size по volume
- Click для quick analysis

Updates real-time через WebSocket.

### Phase 6: Integration и Wiring

**6.1 Update Main.ts**

Инициализация всех новых компонентов:

- Import all new components
- Setup WebSocket connections
- Initialize data services
- Render main layout
- Setup event listeners

**6.2 Create tradingDataService.ts**

Центральный service для trading data:

- WebSocket manager
- Data caching
- Event emitter
- Error handling
- Reconnection logic

**6.3 Update MCP Client**

Расширить `mcpClient.ts`:

- Support для dual MCP servers (оба!)
- Tool calls к bybit-analysis
- Tool calls к bybit-trading
- Response aggregation

**6.4 Logging Service Enhancement**

Улучшить `logService.ts`:

- Structured logging
- Log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Log sources (MCP, AI, Trading, Monitor)
- Log persistence (localStorage)
- Export функция

### Phase 7: UI Polish

**7.1 Status Indicators**

Visual indicators везде:

- 🟢 Healthy (green)
- 🟡 Warning (yellow)
- 🔴 Critical (red)
- ⚪ Neutral (gray)

Apply к:

- Positions status
- Market conditions
- Server connection
- AI confidence

**7.2 Notifications System**

Browser notifications для critical events:

- Position opened
- TP/SL hit
- Emergency exit triggered
- BTC sharp move
- Critical errors

Требует user permission (request при first load).

**7.3 Keyboard Shortcuts**

Добавить shortcuts для power users:

- `Ctrl+1-5` - switch tabs/panels
- `Ctrl+R` - refresh data
- `Ctrl+C` - close selected position (с confirmation!)
- `Ctrl+L` - focus logs
- `Ctrl+A` - focus alerts
- `Esc` - close modals/panels
- `/` - search/filter

**7.4 Dark/Light Theme Enhancement**

Улучшить themes специально для trading:

- Dark: reduce eye strain, highlight P/L colors
- Light: clear для daylight
- Trading colors consistent (green profit, red loss)

### Phase 8: Testing и Optimization

**8.1 Component Testing**

Протестировать каждый компонент:

- TradingDashboard с mock data
- AIReasoningViewer с sample analysis
- AlertsPanel с different alert types
- Charts с real market data
- WebSocket connections

**8.2 Performance Optimization**

- Lazy loading компонентов
- Virtual scrolling для long lists
- Debounce updates (не каждый tick)
- Memo heavy computations
- Optimize re-renders

**8.3 Browser Testing**

Test на:

- Chrome (primary)
- Firefox
- Safari
- Different screen sizes

**8.4 WebSocket Reliability**

- Reconnection logic
- Heartbeat checks
- Fallback к polling
- Error recovery

### Phase 9: Documentation

**9.1 WebUI User Guide**

Создать `WEBUI_GUIDE.md`:

- Layout explanation
- Features overview
- How to read каждую панель
- Keyboard shortcuts
- Troubleshooting

**9.2 Component Documentation**

JSDoc comments для всех компонентов:

- Purpose
- Props/Parameters
- Data flow
- Events emitted

**9.3 Development Guide**

Для future improvements:

- Architecture overview
- How to add new component
- How to add new data source
- Styling guidelines

### Phase 10: Deployment

**10.1 Build Configuration**

Setup production build:

- Минификация
- Tree shaking
- Asset optimization
- Environment variables

**10.2 Startup Scripts**

Создать `start_webui.sh`:

```bash
#!/bin/bash
# Start both MCP servers + WebUI

# Terminal 1: bybit-analysis
node bybit-mcp/build/httpServer.js &

# Terminal 2: bybit-trading  
python mcp_server/full_server.py &

# Terminal 3: WebUI
cd bybit-mcp/webui && pnpm dev

echo "✅ All services started!"
echo "WebUI: http://localhost:3000"
```

**10.3 Docker Support (опционально)**

Docker compose для одной командой запуска:

- bybit-mcp service
- trading-mcp service
- webui service
- All connected

## UI Mockup (Text Representation)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 🤖 AI TRADING AGENT - LIVE MONITOR          BTC: $50,250 (+1.2%)    🔌 Connected │
├────────────────────────┬──────────────────────────────┬─────────────────────────┤
│ 💬 AI CHAT            │ 📊 TRADING DASHBOARD         │ 🚨 ALERTS (2)          │
│                        │                              │                         │
│ You: Найди точки входа│ Portfolio: $30.84 (+2.8%)    │ [⚠️] ETH near TP        │
│                        │ Daily P/L: +$0.84            │      15:45              │
│ AI: 🔍 Analyzing...   │                              │                         │
│     Checked 47 assets  │ 🔹 Active Positions (2)      │ [✅] SOL BE activated   │
│     Found 2 setups     │                              │      14:30              │
│                        │ ETH  $3,085  +2.8%  ✅       │                         │
│ 🎯 OPPORTUNITIES:      │ Entry: $3,000  SL: BE       │─────────────────────────│
│                        │ TP: $3,160     4h 25m       │ 📜 ACTION HISTORY      │
│ 1. ETH 8.5/10         │                              │                         │
│ [Details...]           │ SOL  $148.50  +1.7%  🔄     │ 15:45 🔍 Market scan   │
│                        │ Entry: $146    SL: $141.5   │ 15:46 📊 47 assets     │
├────────────────────────┤ TP: $155       2h 10m       │ 15:47 🎯 2 found       │
│ 🧠 AI REASONING       │                              │ 14:30 ⚡ SOL opened    │
│                        │─────────────────────────────│ 14:31 📡 Monitor ON    │
│ Step 4/10: Multi-TF   │ 📈 CHART: ETH/USDT 1h       │ 14:35 ⚡ SOL SL→BE     │
│                        │                              │                         │
│ Confluence Scoring:    │ [Candlestick chart]         │─────────────────────────│
│ Trend:     ████████ 2.0│ RSI: 59 ↑                   │ 🔍 LIVE LOGS           │
│ Indicators:██████ 1.8  │ MACD: Bullish ✅            │                         │
│ Volume:    ██████ 1.0  │                              │ [INFO] Position update │
│ Pattern:   ██████ 1.0  │ Entry: $3,000 ←─────        │ [DEBUG] WS heartbeat   │
│ R:R:       ███░░░ 0.7  │ Current: $3,085             │ [INFO] ETH +2.8%       │
│ TOTAL: 8.5/10 ✅      │ TP: $3,160 ─────→           │ [WARN] Near TP         │
│                        │                              │                         │
│ Decision: STRONG SETUP │                              │ [Filter: All ▼]        │
└────────────────────────┴──────────────────────────────┴─────────────────────────┘
```

## Implementation Files

New files to create:

1. `src/components/TradingDashboard.ts`
2. `src/components/AIReasoningViewer.ts`
3. `src/components/AlertsPanel.ts`
4. `src/components/ActionHistoryTimeline.ts`
5. `src/components/LiveLogViewer.ts`
6. `src/components/EnhancedChartsPanel.ts`
7. `src/components/MainLayout.ts`
8. `src/services/tradingDataService.ts`
9. `src/services/aiReasoningParser.ts`
10. `src/services/positionAggregator.ts`
11. `src/styles/trading-dashboard.css`
12. `src/styles/ai-reasoning.css`
13. `src/styles/alerts-panel.css`
14. `src/styles/action-history.css`
15. `src/styles/live-logs.css`
16. `src/styles/main-layout.css`
17. `WEBUI_GUIDE.md`

Files to update:

1. `src/main.ts` - initialize new layout
2. `src/services/mcpClient.ts` - dual MCP support
3. `src/services/logService.ts` - enhanced logging
4. `src/styles/variables.css` - trading colors
5. `webui/README.md` - updated features

Estimated total: ~2,000-2,500 строк нового кода

## Expected Results

После реализации пользователь сможет:

1. **Видеть всё в одном месте:**

   - Chat с AI слева
   - Trading dashboard центр
   - Alerts и logs справа

2. **Понимать AI reasoning:**

   - Каждый шаг analysis
   - Confluence breakdown визуально
   - Decision path clearly

3. **Мониторить позиции real-time:**

   - P/L обновляется каждую секунду
   - Status indicators
   - Progress к TP visual

4. **Получать alerts:**

   - Critical events immediately
   - Visual + sound notifications
   - Prioritized display

5. **Анализировать history:**

   - Timeline всех actions
   - Searchable logs
   - Export для review

6. **Контролировать систему:**

   - See exactly что агент делает
   - Intervene если нужно
   - Learn от observing

## Timing

Phase 1: 1 hour (analysis)

Phase 2: 6-8 hours (new components)

Phase 3: 2-3 hours (layout)

Phase 4: 3-4 hours (integration)

Phase 5: 3-4 hours (advanced features)

Phase 6: 1-2 hours (wiring)

Phase 7: 2 hours (polish)

Phase 8: 2 hours (testing)

Phase 9: 1 hour (docs)

Phase 10: 1 hour (deployment)

**Total: 22-30 hours work**

Можно разбить на части и делать iteratively.

### To-dos

- [x] Провести глубокое веб-исследование: технические индикаторы, паттерны, стратегии входа, риск-менеджмент, методология нулевого риска
- [x] Создать knowledge_base/1_trading_fundamentals.md на основе исследования
- [x] Создать knowledge_base/2_technical_indicators_guide.md с детальным описанием всех 13 индикаторов
- [x] Создать knowledge_base/3_patterns_recognition.md с candlestick и chart patterns
- [x] Создать knowledge_base/4_entry_strategies.md с 4 стратегиями высокой вероятности
- [x] Создать knowledge_base/5_risk_management.md с position sizing, stops, TP стратегиями
- [x] Создать knowledge_base/6_market_analysis_framework.md с multi-timeframe и regime detection
- [x] Создать knowledge_base/7_zero_risk_methodology.md с критериями безопасного входа
- [x] Создать knowledge_base/8_position_management.md с lifecycle позиции
- [x] Установить и настроить готовый bybit-mcp сервер с API ключами
- [x] Расширить MCP Server недостающими функциями: technical analysis, market scanner, entry validation
- [x] Протестировать все MCP tools на testnet
- [x] Создать prompts/agent_core_instructions.md с ролью, принципами и протоколом самопроверки
- [x] Создать prompts/market_analysis_protocol.md с пошаговым протоколом анализа
- [x] Создать prompts/entry_decision_framework.md с framework принятия решений
- [x] Создать prompts/position_monitoring_protocol.md с протоколом мониторинга
- [x] Настроить MCP Server в Cursor IDE и создать .cursorrules
- [x] Протестировать полный workflow: исследование рынка -> анализ -> размещение ордера -> мониторинг -> закрытие
- [x] Commit и push всех изменений в GitHub (без credentials!)