# 🎯 ПРОМПТ: Trading Terminal Only - Полная Очистка и Настройка

## ЦЕЛЬ
Преобразовать проект в единую версию с Trading Terminal как главной страницей, убрать все лишнее, исправить чат, выезжающий с левого края, и убедиться, что все последние доработки подключены.

---

## 📋 ЗАДАЧИ

### 1. АНАЛИЗ ТЕКУЩЕГО СОСТОЯНИЯ

**Проверить:**
- [ ] Какие версии сайта существуют (localhost:3001 vs localhost:8081)
- [ ] Где находится главная точка входа (main.ts, index.html)
- [ ] Какие компоненты используются в Trading Terminal
- [ ] Какие компоненты используются в старом режиме (standard mode)
- [ ] Состояние чата, выезжающего с левого края
- [ ] Какие последние доработки были сделаны (PositionDetailReport, TradingDashboard и т.д.)

**Файлы для анализа:**
- `bybit-mcp/webui/src/main.ts` - точка входа
- `bybit-mcp/webui/index.html` - HTML структура
- `bybit-mcp/webui/src/components/TradingTerminal.ts` - терминал
- `bybit-mcp/webui/src/components/ChatApp.ts` - чат
- `bybit-mcp/webui/src/components/TradingDashboard.ts` - дашборд
- `bybit-mcp/webui/src/components/PositionDetailReport.ts` - отчет по позициям
- `bybit-mcp/src/httpServer.ts` - HTTP сервер на 8081

---

### 2. УДАЛИТЬ СТАРЫЙ РЕЖИМ (STANDARD MODE)

**Убрать из `index.html`:**
- [ ] Весь блок `#main-container` со старым интерфейсом
- [ ] Sidebar с навигацией (chat, tools, dashboard)
- [ ] Старые view'ы (chat-view, tools-view, dashboard-view)
- [ ] Кнопку переключения режимов (`mode-toggle-btn`)
- [ ] Settings modal (или оставить, но упростить)

**Убрать из `main.ts`:**
- [ ] Инициализацию ChatApp для standard mode
- [ ] Метод `switchToMode()` - больше не нужен
- [ ] Метод `toggleMode()` - больше не нужен
- [ ] Метод `switchView()` - больше не нужен
- [ ] Все обработчики для старого режима
- [ ] Инициализацию ToolsManager для старого режима
- [ ] Инициализацию AgentDashboard для старого режима

**Оставить:**
- ✅ Trading Terminal как единственный режим
- ✅ Header с метриками (Balance, P/L, Win Rate, AI Confidence)
- ✅ Кнопки: Settings, Theme Toggle (если нужны)
- ✅ Position Detail Report контейнер

---

### 3. НАСТРОИТЬ ГЛАВНУЮ СТРАНИЦУ КАК TRADING TERMINAL

**В `main.ts`:**
- [ ] Убрать проверку `savedMode` - всегда terminal
- [ ] Сразу инициализировать TradingTerminal
- [ ] Убрать создание `main-container`
- [ ] Создавать `trading-terminal-container` сразу в body

**В `index.html`:**
- [ ] Убрать `#main-container` полностью
- [ ] Оставить только:
  - Header
  - `#trading-terminal-container` (создается динамически)
  - Контейнеры для модалок и панелей
  - `#position-detail-report-container`

**Структура должна быть:**
```html
<body>
  <div id="app">
    <!-- Loading -->
    <div id="loading">...</div>
    
    <!-- Header (упрощенный) -->
    <header class="header">...</header>
    
    <!-- Trading Terminal (создается динамически) -->
    <!-- Контейнеры для панелей -->
    <div id="position-detail-report-container"></div>
  </div>
</body>
```

---

### 4. ИСПРАВИТЬ ЧАТ, ВЫЕЗЖАЮЩИЙ С ЛЕВОГО КРАЯ

**Проблемы, которые нужно исправить:**
- [ ] Чат не выезжает при наведении на левый край
- [ ] Чат не скрывается при уходе мыши
- [ ] Hover zone не работает корректно
- [ ] Z-index конфликты

**В `TradingTerminal.ts`:**
- [ ] Проверить метод `setupChatSlidePanel()`
- [ ] Убедиться, что `chat-hover-zone` создается в HTML
- [ ] Проверить обработчики `mouseenter`/`mouseleave`
- [ ] Убедиться, что панель правильно позиционируется
- [ ] Проверить, что панель на всю высоту экрана

**В `trading-terminal.css`:**
- [ ] Проверить стили `.chat-hover-zone` (width: 20px, z-index высокий)
- [ ] Проверить стили `.chat-slide-panel` (position: fixed, height: 100vh)
- [ ] Убедиться, что transition работает
- [ ] Проверить, что нет конфликтов z-index

**Требования к чату:**
- ✅ Ширина hover zone: 20px от левого края
- ✅ Высота: 100vh (на всю высоту экрана)
- ✅ Панель выезжает при наведении на hover zone
- ✅ Панель скрывается через 500ms после ухода мыши
- ✅ Панель остается открытой, когда мышь внутри панели
- ✅ Плавная анимация (transition)

---

### 5. УБРАТЬ ЛИШНИЕ ЭЛЕМЕНТЫ

**Убрать из Header:**
- [ ] Кнопку "New Trade" (если не функциональна)
- [ ] Кнопку переключения режимов (`mode-toggle-btn`)
- [ ] Лишние иконки, которые не работают

**Оставить в Header:**
- ✅ Logo и название
- ✅ Метрики (Balance, Daily P/L, Win Rate, AI Confidence)
- ✅ Settings (⚙️)
- ✅ Theme Toggle (🌙)

**Убрать компоненты:**
- [ ] `MainLayout.ts` - больше не нужен
- [ ] Старые view'ы из `main.ts`
- [ ] Инициализацию ToolsManager для старого режима
- [ ] Инициализацию AgentDashboard для старого режима

**Оставить компоненты:**
- ✅ TradingTerminal
- ✅ TradingDashboard
- ✅ PositionDetailReport
- ✅ ChatApp (только в терминале, выезжающий)
- ✅ AIReasoningViewer
- ✅ AlertsPanel
- ✅ ActionHistoryTimeline
- ✅ LiveLogViewer
- ✅ SignalMonitoringPanel
- ✅ OrderHistory
- ✅ ChartContainer

---

### 6. ПРОВЕРИТЬ ПОДКЛЮЧЕНИЕ ВСЕХ ДОРАБОТОК

**Проверить, что подключено:**
- [ ] PositionDetailReport - интегрирован в TradingDashboard
- [ ] TradingDashboard - отображает позиции и портфель
- [ ] TradingView графики - работают в терминале
- [ ] Real-time обновления - через tradingDataService
- [ ] WebSocket подключения - работают
- [ ] Все аналитические панели - подключены

**В `TradingTerminal.ts`:**
- [ ] Проверить метод `initializeComponents()`
- [ ] Убедиться, что все компоненты инициализируются
- [ ] Проверить, что PositionDetailReport доступен через TradingDashboard

**В `TradingDashboard.ts`:**
- [ ] Проверить кнопку "View Full Report"
- [ ] Убедиться, что она открывает PositionDetailReport
- [ ] Проверить real-time обновления позиций

---

### 7. УПРОСТИТЬ HTML СТРУКТУРУ

**Финальная структура `index.html`:**
```html
<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Trading Terminal - Bybit MCP</title>
  <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
  <link rel="preload" href="/src/styles/main.css" as="style" />
</head>
<body>
  <div id="app">
    <!-- Loading -->
    <div id="loading" class="loading-container">
      <div class="loading-spinner"></div>
      <p>Loading Trading Terminal...</p>
    </div>

    <!-- Header (упрощенный) -->
    <header class="header">
      <div class="header-content">
        <div class="logo">
          <div class="logo-icon">🤖</div>
          <div class="logo-text">
            <h1 class="logo-title">TRADING TERMINAL</h1>
            <span class="logo-subtitle">Bybit MCP</span>
          </div>
        </div>
        
        <!-- Metrics Bar -->
        <div class="header-metrics">
          <div class="metric-item">
            <span class="metric-label">Balance</span>
            <span class="metric-value" id="header-balance">$0.00</span>
          </div>
          <div class="metric-divider"></div>
          <div class="metric-item">
            <span class="metric-label">Daily P/L</span>
            <span class="metric-value pnl" id="header-daily-pnl">$0.00</span>
          </div>
          <div class="metric-divider"></div>
          <div class="metric-item">
            <span class="metric-label">Win Rate</span>
            <span class="metric-value" id="header-win-rate">0%</span>
          </div>
          <div class="metric-divider"></div>
          <div class="metric-item">
            <span class="metric-label">AI Confidence</span>
            <span class="metric-value confidence" id="header-confidence">--</span>
          </div>
        </div>
        
        <!-- Actions (только нужные) -->
        <div class="header-actions">
          <button id="theme-toggle" class="header-btn" aria-label="Toggle theme">
            <span class="theme-icon">🌙</span>
          </button>
          <button id="settings-btn" class="header-btn" aria-label="Settings">
            <span class="settings-icon">⚙️</span>
          </button>
        </div>
      </div>
    </header>

    <!-- Trading Terminal Container (создается динамически) -->
    <!-- Будет создан через main.ts -->

    <!-- Контейнеры для панелей -->
    <div id="position-detail-report-container" style="display: none;"></div>
    
    <!-- Settings Modal (если нужен) -->
    <div id="settings-modal" class="modal hidden">
      <!-- Упрощенный settings -->
    </div>
  </div>

  <script type="module" src="/src/main.ts"></script>
</body>
</html>
```

---

### 8. ИСПРАВИТЬ MAIN.TS

**Упрощенная структура:**
```typescript
class App {
  private tradingTerminal?: TradingTerminal;
  private isInitialized = false;

  async initialize(): Promise<void> {
    if (this.isInitialized) return;
    
    this.showLoading();
    
    // Initialize services
    try {
      await this.initializeServices();
    } catch (error) {
      console.error('⚠️ Service initialization had errors:', error);
    }
    
    // Initialize UI
    try {
      this.initializeUI();
    } catch (error) {
      console.error('❌ Failed to initialize UI:', error);
      this.showError('Failed to initialize Trading Terminal.');
      return;
    }
    
    // Initialize Trading Terminal immediately
    try {
      this.initializeTradingTerminal();
    } catch (error) {
      console.error('❌ Failed to initialize terminal:', error);
      this.showError('Failed to initialize Trading Terminal.');
      return;
    }
    
    this.hideLoading();
    this.isInitialized = true;
    console.log('✅ Trading Terminal initialized');
  }
  
  private initializeTradingTerminal(): void {
    // Create container
    const container = document.createElement('div');
    container.id = 'trading-terminal-container';
    container.style.display = 'flex';
    container.style.height = 'calc(100vh - var(--header-height, 60px))';
    container.style.width = '100%';
    document.body.appendChild(container);
    
    // Initialize terminal
    this.tradingTerminal = new TradingTerminal('trading-terminal-container');
  }
  
  // ... остальные методы
}
```

---

### 9. ПРОВЕРИТЬ И ИСПРАВИТЬ ЧАТ

**В `TradingTerminal.ts` проверить:**
- [ ] Метод `setupChatSlidePanel()` вызывается
- [ ] Элементы `chat-hover-zone` и `chat-slide-panel` создаются в HTML
- [ ] Обработчики событий правильно настроены
- [ ] Z-index правильные (hover-zone выше панели)

**Исправить логику:**
```typescript
private setupChatSlidePanel(): void {
  const hoverZone = document.getElementById('chat-hover-zone');
  const chatPanel = document.getElementById('chat-slide-panel');
  
  if (!hoverZone || !chatPanel) {
    console.error('❌ Chat elements not found');
    return;
  }
  
  let hideTimeout: number | null = null;
  
  // Show on hover zone enter
  hoverZone.addEventListener('mouseenter', () => {
    if (hideTimeout) {
      clearTimeout(hideTimeout);
      hideTimeout = null;
    }
    this.toggleChatPanel(true);
  });
  
  // Hide when leaving hover zone (if not moving to panel)
  hoverZone.addEventListener('mouseleave', (e) => {
    const relatedTarget = e.relatedTarget as HTMLElement;
    if (relatedTarget && (relatedTarget === chatPanel || chatPanel.contains(relatedTarget))) {
      return; // Moving to panel, keep open
    }
    
    hideTimeout = window.setTimeout(() => {
      if (!chatPanel.matches(':hover')) {
        this.toggleChatPanel(false);
      }
      hideTimeout = null;
    }, 500);
  });
  
  // Keep open when mouse in panel
  chatPanel.addEventListener('mouseenter', () => {
    if (hideTimeout) {
      clearTimeout(hideTimeout);
      hideTimeout = null;
    }
  });
  
  // Hide when leaving panel
  chatPanel.addEventListener('mouseleave', (e) => {
    const relatedTarget = e.relatedTarget as HTMLElement;
    if (relatedTarget && (relatedTarget === hoverZone || hoverZone.contains(relatedTarget))) {
      return; // Moving to hover zone, keep open
    }
    
    hideTimeout = window.setTimeout(() => {
      if (!hoverZone.matches(':hover')) {
        this.toggleChatPanel(false);
      }
      hideTimeout = null;
    }, 500);
  });
}
```

---

### 10. ПРОВЕРИТЬ CSS

**В `trading-terminal.css`:**
- [ ] `.chat-hover-zone` - position: fixed, left: 0, width: 20px, height: 100vh, z-index высокий
- [ ] `.chat-slide-panel` - position: fixed, left: 0, height: 100vh, transform: translateX(-100%), transition
- [ ] `.chat-slide-panel.open` - transform: translateX(0)
- [ ] Нет конфликтов z-index

---

### 11. ПРОВЕРИТЬ HTTP SERVER (8081)

**В `bybit-mcp/src/httpServer.ts`:**
- [ ] Проверить, что статика раздается из `webui/dist`
- [ ] Проверить, что все маршруты работают
- [ ] Убедиться, что главная страница - это index.html

---

### 12. ТЕСТИРОВАНИЕ

**Проверить:**
- [ ] Главная страница открывается как Trading Terminal
- [ ] Чат выезжает при наведении на левый край (20px)
- [ ] Чат скрывается при уходе мыши
- [ ] Все компоненты терминала загружаются
- [ ] TradingDashboard показывает позиции
- [ ] PositionDetailReport открывается из TradingDashboard
- [ ] Real-time обновления работают
- [ ] Header метрики обновляются
- [ ] Нет ошибок в консоли

---

## 🔧 КОМАНДЫ ДЛЯ ПРОВЕРКИ

```bash
# 1. Остановить все процессы
cd bybit-mcp/webui
./scripts/stop-all-dev.sh

# 2. Собрать WebUI
cd bybit-mcp/webui
pnpm build

# 3. Запустить HTTP сервер (в отдельном терминале)
cd bybit-mcp
node build/httpServer.js

# 4. Открыть браузер
open http://localhost:8081
```

---

## ✅ КРИТЕРИИ УСПЕХА

1. ✅ Только одна версия сайта (localhost:8081)
2. ✅ Главная страница - Trading Terminal
3. ✅ Старый режим полностью удален
4. ✅ Чат выезжает с левого края при наведении
5. ✅ Чат скрывается при уходе мыши
6. ✅ Все последние доработки подключены
7. ✅ Лишние элементы убраны
8. ✅ Нет ошибок в консоли
9. ✅ Все компоненты работают

---

## 📝 ПЛАН ДЕЙСТВИЙ

1. **Анализ** - изучить текущую структуру
2. **Очистка** - удалить старый режим
3. **Настройка** - настроить главную страницу как Terminal
4. **Исправление** - исправить чат
5. **Проверка** - проверить все компоненты
6. **Тестирование** - протестировать все функции
7. **Документация** - обновить документацию

---

## 🚨 ВАЖНО

- **НЕ удалять** компоненты, которые используются в Trading Terminal
- **НЕ удалять** PositionDetailReport, TradingDashboard, ChartContainer
- **НЕ удалять** сервисы (tradingDataService, websocketService)
- **Удалять** только старый UI (main-container, sidebar, старые view'ы)
- **Упростить** header, но оставить метрики
- **Исправить** чат, а не переписывать с нуля

---

## 📌 ФАЙЛЫ ДЛЯ ИЗМЕНЕНИЯ

1. `bybit-mcp/webui/index.html` - упростить структуру
2. `bybit-mcp/webui/src/main.ts` - убрать старый режим, оставить только terminal
3. `bybit-mcp/webui/src/components/TradingTerminal.ts` - исправить чат
4. `bybit-mcp/webui/src/styles/trading-terminal.css` - проверить стили чата
5. `bybit-mcp/webui/src/styles/main.css` - убрать стили старого режима (если есть)

---

**НАЧНИ С АНАЛИЗА, ЗАТЕМ ПОСЛЕДОВАТЕЛЬНО ВЫПОЛНИ ВСЕ ЗАДАЧИ!**


