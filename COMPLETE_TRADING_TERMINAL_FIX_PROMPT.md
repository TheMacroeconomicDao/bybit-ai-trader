# 🔧 ПОЛНОЕ ИСПРАВЛЕНИЕ TRADING TERMINAL - БОЕВАЯ МАШИНА AI ТРЕЙДИНГА

## 🎯 КРИТИЧЕСКАЯ ПРОБЛЕМА

Текущее состояние Trading Terminal **НЕ РАБОТАЕТ**:
- ❌ HTTP 404 ошибки при загрузке данных (позиции, портфель, сигналы)
- ❌ Портфель показывает $0.00 вместо реальных данных
- ❌ Позиции не загружаются (0 активных позиций)
- ❌ Order History компонент удален (откат изменений)
- ❌ Signal Monitoring показывает HTTP 404
- ❌ MCP сервер не получает API ключи из `.env`
- ❌ Прокси Vite не настроен правильно для всех эндпоинтов

**ЦЕЛЬ:** Создать полноценную боевую машину для AI трейдинга с реальными данными в реальном времени.

---

## 📋 АНАЛИЗ ТЕКУЩЕГО СОСТОЯНИЯ

### 1. Проблемы с HTTP 404

**Причина:**
- `mcpClient.ts` использует `baseUrl = '/api/mcp'` для localhost:3000
- Но `vite.config.ts` проксирует только `/api/mcp/*` → `http://localhost:8081/*`
- Проблема: когда порт 3001, логика определения baseUrl не работает правильно
- Прямые запросы к `/tools`, `/call-tool`, `/health` не проксируются

**Файлы:**
- `bybit-mcp/webui/src/services/mcpClient.ts` (строки 26-54)
- `bybit-mcp/webui/vite.config.ts` (строки 25-37)

### 2. Проблемы с загрузкой данных

**Причина:**
- `tradingDataService.ts` вызывает `mcpClient.callTool('get_positions')` → HTTP 404
- `tradingDataService.ts` вызывает `mcpClient.callTool('get_wallet_balance')` → HTTP 404
- `SignalMonitoringPanel.ts` вызывает MCP tool для сигналов → HTTP 404
- Все запросы падают с HTTP 404, потому что прокси не работает

**Файлы:**
- `bybit-mcp/webui/src/services/tradingDataService.ts` (строки 247, 291)
- `bybit-mcp/webui/src/components/SignalMonitoringPanel.ts` (нужно проверить метод загрузки)

### 3. Order History компонент удален

**Причина:**
- Пользователь откатил изменения
- `OrderHistory.ts` удален
- `TradingTerminal.ts` не содержит Order History панель

**Нужно:**
- Восстановить `OrderHistory.ts` компонент
- Интегрировать в `TradingTerminal.ts`
- Использовать `get_order_history` MCP tool

### 4. API ключи не загружаются

**Причина:**
- `env.ts` исправлен, но нужно пересобрать проект
- HTTP сервер не запущен с правильными переменными окружения

**Файлы:**
- `bybit-mcp/src/env.ts` (уже исправлен)
- `bybit-mcp/src/httpServer.ts` (уже исправлен)

---

## ✅ РЕШЕНИЕ - ПОШАГОВЫЙ ПЛАН

### ШАГ 1: Исправить прокси Vite для всех портов

**Файл:** `bybit-mcp/webui/vite.config.ts`

**Исправление:**
```typescript
server: {
  port: 3000,
  host: true,
  proxy: {
    // Proxy MCP server requests - ДОБАВИТЬ прямые пути
    '/api/mcp': {
      target: 'http://localhost:8081',
      changeOrigin: true,
      rewrite: (path) => path.replace(/^\/api\/mcp/, ''),
      configure: (proxy) => {
        proxy.on('error', (err) => {
          console.log('Proxy error:', err);
        });
      }
    },
    // ДОБАВИТЬ: Прямые пути для совместимости
    '/tools': {
      target: 'http://localhost:8081',
      changeOrigin: true,
    },
    '/call-tool': {
      target: 'http://localhost:8081',
      changeOrigin: true,
    },
    '/health': {
      target: 'http://localhost:8081',
      changeOrigin: true,
    },
  },
},
```

### ШАГ 2: Исправить логику baseUrl в mcpClient.ts

**Файл:** `bybit-mcp/webui/src/services/mcpClient.ts`

**Проблема:** Логика определения baseUrl не учитывает порт 3001 и другие случаи.

**Исправление:**
```typescript
constructor(baseUrl: string = '', timeout: number = 30000) {
  // Determine the correct base URL based on environment
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname;
    const port = window.location.port;
    
    // Development mode (localhost:3000 или localhost:3001)
    if (hostname === 'localhost' && (port === '3000' || port === '3001' || port === '')) {
      // Использовать прокси Vite
      this.baseUrl = '/api/mcp';
    } else if (baseUrl && baseUrl !== '' && baseUrl !== 'auto') {
      // Explicit base URL provided
      this.baseUrl = baseUrl.replace(/\/$/, '');
    } else {
      // Production mode - use current origin
      this.baseUrl = window.location.origin;
    }
  } else {
    // Server-side fallback
    this.baseUrl = baseUrl || 'http://localhost:8081';
    this.baseUrl = this.baseUrl.replace(/\/$/, '');
  }
  
  this.timeout = timeout;
  
  console.log('🔧 MCP Client initialized:', {
    hostname: typeof window !== 'undefined' ? window.location.hostname : 'server-side',
    port: typeof window !== 'undefined' ? window.location.port : 'server-side',
    baseUrl: this.baseUrl
  });
}
```

### ШАГ 3: Добавить fallback для прямых запросов

**Файл:** `bybit-mcp/webui/src/services/mcpClient.ts`

**Добавить метод с fallback:**
```typescript
/**
 * Call a specific MCP tool using HTTP with fallback
 */
async callTool<T extends MCPToolName>(
  name: T,
  params: MCPToolParams<T>
): Promise<MCPToolResponse<T>> {
  try {
    console.log(`🔧 Calling tool ${name} with params:`, params);

    const convertedParams = this.validateAndConvertParams(name as string, params as Record<string, any>);
    
    // Попытка 1: Использовать baseUrl (прокси или прямой)
    try {
      const response = await fetch(`${this.baseUrl}/call-tool`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: name as string,
          arguments: convertedParams,
        }),
      });

      if (response.ok) {
        const result = await response.json();
        console.log(`✅ Tool ${name} result:`, result);
        citationStore.processToolResponse(result);
        return result as MCPToolResponse<T>;
      }
    } catch (proxyError) {
      console.warn(`⚠️ Proxy request failed, trying direct connection:`, proxyError);
    }

    // Попытка 2: Прямое подключение к MCP серверу
    const directUrl = 'http://localhost:8081';
    const response = await fetch(`${directUrl}/call-tool`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        name: name as string,
        arguments: convertedParams,
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`HTTP ${response.status}: ${errorText}`);
    }

    const result = await response.json();
    console.log(`✅ Tool ${name} result (direct):`, result);
    citationStore.processToolResponse(result);
    return result as MCPToolResponse<T>;
  } catch (error) {
    console.error(`❌ Failed to call tool ${name}:`, error);
    throw error;
  }
}
```

### ШАГ 4: Восстановить OrderHistory компонент

**Создать файл:** `bybit-mcp/webui/src/components/OrderHistory.ts`

**Полный код компонента:**
```typescript
/**
 * Order History Component - История ордеров
 * Показывает историю всех сделок с фильтрацией и сортировкой
 */

import { mcpClient } from '@/services/mcpClient';
import type { MCPToolResult } from '@/types/mcp';

interface Order {
  orderId: string;
  symbol: string;
  side: 'Buy' | 'Sell';
  orderType: 'Market' | 'Limit';
  price: number;
  qty: number;
  executedQty: number;
  status: 'Filled' | 'PartiallyFilled' | 'New' | 'Cancelled' | 'Rejected';
  realizedPnl?: number;
  realizedPnlPct?: number;
  createdAt: number;
  updatedAt: number;
}

export class OrderHistory {
  private container: HTMLElement;
  private orders: Order[] = [];
  private updateInterval: NodeJS.Timeout | null = null;
  private category: 'spot' | 'linear' = 'linear';
  private filter: 'all' | 'filled' | 'open' | 'cancelled' = 'all';
  private sortBy: 'time' | 'symbol' | 'pnl' = 'time';
  private sortOrder: 'asc' | 'desc' = 'desc';

  constructor(containerId: string) {
    const element = document.getElementById(containerId);
    if (!element) {
      throw new Error(`Order history container #${containerId} not found`);
    }
    this.container = element;
    this.initialize();
  }

  private initialize(): void {
    this.render();
    this.setupEventListeners();
    this.startAutoUpdate();
    this.refresh();
  }

  private render(): void {
    this.container.innerHTML = `
      <div class="order-history-panel">
        <div class="panel-header">
          <h3 class="panel-title">
            📋 Order History
            <span class="order-count" id="order-count">0</span>
          </h3>
          <div class="panel-controls">
            <select class="category-select" id="order-category">
              <option value="linear">Futures</option>
              <option value="spot">Spot</option>
            </select>
            <button class="refresh-btn" id="refresh-orders" title="Refresh">🔄</button>
          </div>
        </div>
        
        <div class="order-filters">
          <button class="filter-btn ${this.filter === 'all' ? 'active' : ''}" data-filter="all">All</button>
          <button class="filter-btn ${this.filter === 'filled' ? 'active' : ''}" data-filter="filled">Filled</button>
          <button class="filter-btn ${this.filter === 'open' ? 'active' : ''}" data-filter="open">Open</button>
          <button class="filter-btn ${this.filter === 'cancelled' ? 'active' : ''}" data-filter="cancelled">Cancelled</button>
        </div>
        
        <div class="order-sort">
          <button class="sort-btn ${this.sortBy === 'time' ? 'active' : ''}" data-sort="time">Time</button>
          <button class="sort-btn ${this.sortBy === 'symbol' ? 'active' : ''}" data-sort="symbol">Symbol</button>
          <button class="sort-btn ${this.sortBy === 'pnl' ? 'active' : ''}" data-sort="pnl">P/L</button>
        </div>
        
        <div class="orders-table-container">
          <table class="orders-table">
            <thead>
              <tr>
                <th>Time</th>
                <th>Symbol</th>
                <th>Side</th>
                <th>Type</th>
                <th>Price</th>
                <th>Qty</th>
                <th>Status</th>
                <th>P/L</th>
              </tr>
            </thead>
            <tbody id="orders-tbody">
              <tr>
                <td colspan="8" class="empty-state">
                  <div class="empty-message">
                    <span class="empty-icon">📭</span>
                    <p>No orders</p>
                    <small>Orders will appear here</small>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    `;
  }

  private setupEventListeners(): void {
    // Category select
    const categorySelect = this.container.querySelector('#order-category') as HTMLSelectElement;
    if (categorySelect) {
      categorySelect.addEventListener('change', (e) => {
        this.category = (e.target as HTMLSelectElement).value as 'spot' | 'linear';
        this.refresh();
      });
    }

    // Refresh button
    const refreshBtn = this.container.querySelector('#refresh-orders');
    if (refreshBtn) {
      refreshBtn.addEventListener('click', () => this.refresh());
    }

    // Filter buttons
    const filterBtns = this.container.querySelectorAll('.filter-btn');
    filterBtns.forEach(btn => {
      btn.addEventListener('click', (e) => {
        const filter = (e.target as HTMLElement).dataset.filter as typeof this.filter;
        if (filter) {
          this.filter = filter;
          filterBtns.forEach(b => b.classList.remove('active'));
          (e.target as HTMLElement).classList.add('active');
          this.renderOrders();
        }
      });
    });

    // Sort buttons
    const sortBtns = this.container.querySelectorAll('.sort-btn');
    sortBtns.forEach(btn => {
      btn.addEventListener('click', (e) => {
        const sortBy = (e.target as HTMLElement).dataset.sort as typeof this.sortBy;
        if (sortBy) {
          if (this.sortBy === sortBy) {
            this.sortOrder = this.sortOrder === 'asc' ? 'desc' : 'asc';
          } else {
            this.sortBy = sortBy;
            this.sortOrder = 'desc';
          }
          sortBtns.forEach(b => b.classList.remove('active'));
          (e.target as HTMLElement).classList.add('active');
          this.updateSortUI();
          this.renderOrders();
        }
      });
    });
  }

  private updateSortUI(): void {
    const sortBtns = this.container.querySelectorAll('.sort-btn');
    sortBtns.forEach(btn => {
      const sortBy = (btn as HTMLElement).dataset.sort;
      if (sortBy === this.sortBy) {
        btn.classList.add('active');
        const arrow = this.sortOrder === 'asc' ? ' ↑' : ' ↓';
        if (!btn.textContent?.includes('↑') && !btn.textContent?.includes('↓')) {
          btn.textContent = btn.textContent + arrow;
        }
      } else {
        btn.classList.remove('active');
        btn.textContent = btn.textContent?.replace(/ [↑↓]/, '') || '';
      }
    });
  }

  private startAutoUpdate(): void {
    this.updateInterval = setInterval(() => {
      this.refresh();
    }, 10000); // Обновление каждые 10 секунд
  }

  private async refresh(): Promise<void> {
    try {
      console.log('🔄 Loading order history...');
      
      const result: any = await mcpClient.callTool('get_order_history', {
        category: this.category,
        limit: '100'
      });

      let orders: any[] = [];
      
      // Парсинг MCP response
      if (result?.content?.[0]?.text) {
        try {
          const parsed = JSON.parse(result.content[0].text);
          orders = parsed?.list || parsed?.result?.list || parsed || [];
        } catch (e) {
          console.error('Failed to parse orders JSON:', e);
          orders = Array.isArray(result.content[0].text) ? result.content[0].text : [];
        }
      } else if (Array.isArray(result)) {
        orders = result;
      } else if (result?.list && Array.isArray(result.list)) {
        orders = result.list;
      }

      // Преобразование в формат Order
      this.orders = orders.map((order: any) => ({
        orderId: order.orderId || order.order_id || order.orderLinkId || '',
        symbol: order.symbol || '',
        side: (order.side || 'Buy') as 'Buy' | 'Sell',
        orderType: (order.orderType || order.order_type || 'Market') as 'Market' | 'Limit',
        price: parseFloat(order.price || order.avgPrice || order.execPrice || '0'),
        qty: parseFloat(order.qty || order.orderQty || '0'),
        executedQty: parseFloat(order.executedQty || order.cumExecQty || '0'),
        status: this.mapOrderStatus(order.orderStatus || order.status || 'New'),
        realizedPnl: parseFloat(order.realizedPnl || order.cumRealisedPnl || '0'),
        realizedPnlPct: order.realizedPnlPct || (order.realizedPnl && order.price ? (order.realizedPnl / order.price) * 100 : 0),
        createdAt: parseInt(order.createdTime || order.created_at || Date.now().toString()),
        updatedAt: parseInt(order.updatedTime || order.updated_at || Date.now().toString())
      }));

      this.renderOrders();
      this.updateOrderCount();
      
      console.log(`✅ Loaded ${this.orders.length} orders`);
    } catch (error) {
      console.error('❌ Error loading order history:', error);
      this.showError(error instanceof Error ? error.message : 'Failed to load orders');
    }
  }

  private mapOrderStatus(status: string): Order['status'] {
    const statusMap: Record<string, Order['status']> = {
      'Filled': 'Filled',
      'PartiallyFilled': 'PartiallyFilled',
      'New': 'New',
      'Cancelled': 'Cancelled',
      'Rejected': 'Rejected'
    };
    return statusMap[status] || 'New';
  }

  private getFilteredOrders(): Order[] {
    let filtered = [...this.orders];

    // Фильтр по статусу
    if (this.filter !== 'all') {
      filtered = filtered.filter(order => {
        if (this.filter === 'filled') return order.status === 'Filled';
        if (this.filter === 'open') return order.status === 'New' || order.status === 'PartiallyFilled';
        if (this.filter === 'cancelled') return order.status === 'Cancelled';
        return true;
      });
    }

    // Сортировка
    filtered.sort((a, b) => {
      let comparison = 0;
      
      if (this.sortBy === 'time') {
        comparison = a.createdAt - b.createdAt;
      } else if (this.sortBy === 'symbol') {
        comparison = a.symbol.localeCompare(b.symbol);
      } else if (this.sortBy === 'pnl') {
        comparison = (a.realizedPnl || 0) - (b.realizedPnl || 0);
      }
      
      return this.sortOrder === 'asc' ? comparison : -comparison;
    });

    return filtered;
  }

  private renderOrders(): void {
    const tbody = this.container.querySelector('#orders-tbody');
    if (!tbody) return;

    const filtered = this.getFilteredOrders();

    if (filtered.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="8" class="empty-state">
            <div class="empty-message">
              <span class="empty-icon">📭</span>
              <p>No orders</p>
              <small>Orders will appear here</small>
            </div>
          </td>
        </tr>
      `;
      return;
    }

    tbody.innerHTML = filtered.map(order => this.renderOrderRow(order)).join('');
  }

  private renderOrderRow(order: Order): string {
    const time = new Date(order.createdAt).toLocaleString();
    const statusClass = this.getStatusClass(order.status);
    const pnlClass = (order.realizedPnl || 0) >= 0 ? 'positive' : 'negative';
    const pnlValue = order.realizedPnl ? (order.realizedPnl >= 0 ? '+' : '') + order.realizedPnl.toFixed(2) : '-';

    return `
      <tr class="order-row">
        <td class="time-cell">${time}</td>
        <td class="symbol-cell"><strong>${order.symbol}</strong></td>
        <td class="side-cell">
          <span class="side-badge ${order.side.toLowerCase()}">${order.side}</span>
        </td>
        <td class="type-cell">${order.orderType}</td>
        <td class="price-cell">$${order.price.toFixed(2)}</td>
        <td class="qty-cell">${order.executedQty.toFixed(4)} / ${order.qty.toFixed(4)}</td>
        <td class="status-cell">
          <span class="status-badge ${statusClass}">${this.formatStatus(order.status)}</span>
        </td>
        <td class="pnl-cell ${pnlClass}">${pnlValue}</td>
      </tr>
    `;
  }

  private getStatusClass(status: Order['status']): string {
    const statusMap: Record<Order['status'], string> = {
      'Filled': 'success',
      'PartiallyFilled': 'warning',
      'New': 'info',
      'Cancelled': 'muted',
      'Rejected': 'error'
    };
    return statusMap[status] || 'info';
  }

  private formatStatus(status: Order['status']): string {
    const statusMap: Record<Order['status'], string> = {
      'Filled': 'Filled',
      'PartiallyFilled': 'Partial',
      'New': 'Open',
      'Cancelled': 'Cancelled',
      'Rejected': 'Rejected'
    };
    return statusMap[status] || status;
  }

  private updateOrderCount(): void {
    const countEl = this.container.querySelector('#order-count');
    if (countEl) {
      countEl.textContent = `(${this.orders.length})`;
    }
  }

  private showError(message: string): void {
    const tbody = this.container.querySelector('#orders-tbody');
    if (tbody) {
      tbody.innerHTML = `
        <tr>
          <td colspan="8" class="error-state">
            <div class="error-message">
              <span class="error-icon">❌</span>
              <p>Ошибка загрузки ордеров: ${message}</p>
              <button class="retry-btn" onclick="location.reload()">Повторить</button>
            </div>
          </td>
        </tr>
      `;
    }
  }

  destroy(): void {
    if (this.updateInterval) {
      clearInterval(this.updateInterval);
      this.updateInterval = null;
    }
  }
}
```

### ШАГ 5: Интегрировать OrderHistory в TradingTerminal

**Файл:** `bybit-mcp/webui/src/components/TradingTerminal.ts`

**Добавить импорт:**
```typescript
import { OrderHistory } from './OrderHistory';
```

**Добавить свойство:**
```typescript
private orderHistory?: OrderHistory;
```

**В методе `renderLayout()` добавить панель Order History в правую колонку:**
```typescript
<!-- Right Column -->
<div class="terminal-column column-right" style="width: ${this.columnWidths[2]}%">
  <div class="column-content">
    <!-- ... существующие панели ... -->
    
    <!-- Order History Panel -->
    <div class="terminal-panel order-history-panel" id="order-history-terminal-container">
      <!-- OrderHistory component will render here -->
    </div>
  </div>
</div>
```

**В методе `initializeComponents()`:**
```typescript
this.orderHistory = new OrderHistory('order-history-terminal-container');
```

**В методе `destroy()`:**
```typescript
this.orderHistory?.destroy();
```

### ШАГ 6: Исправить SignalMonitoringPanel

**Файл:** `bybit-mcp/webui/src/components/SignalMonitoringPanel.ts`

**Найти метод `loadSignals()` и исправить:**
```typescript
private async loadSignals(): Promise<void> {
  try {
    console.log('🔄 Loading signals...');
    
    // Использовать правильный MCP tool
    const result: any = await mcpClient.callTool('get_active_signals', {});
    
    let signals: any[] = [];
    
    // Парсинг MCP response
    if (result?.content?.[0]?.text) {
      try {
        const parsed = JSON.parse(result.content[0].text);
        signals = parsed?.signals || parsed?.list || parsed || [];
      } catch (e) {
        console.error('Failed to parse signals JSON:', e);
        signals = Array.isArray(result.content[0].text) ? result.content[0].text : [];
      }
    } else if (Array.isArray(result)) {
      signals = result;
    } else if (result?.signals && Array.isArray(result.signals)) {
      signals = result.signals;
    } else if (result?.list && Array.isArray(result.list)) {
      signals = result.list;
    }

    // Преобразование в формат Signal
    this.signals = signals.map((signal: any) => ({
      signal_id: signal.signal_id || signal.id || '',
      symbol: signal.symbol || '',
      side: signal.side || 'long',
      entry_price: parseFloat(signal.entry_price || signal.entryPrice || '0'),
      stop_loss: parseFloat(signal.stop_loss || signal.stopLoss || '0'),
      take_profit: parseFloat(signal.take_profit || signal.takeProfit || '0'),
      current_price: signal.current_price ? parseFloat(signal.current_price) : undefined,
      confluence_score: parseFloat(signal.confluence_score || signal.confluenceScore || '0'),
      probability: parseFloat(signal.probability || '0'),
      risk_reward: parseFloat(signal.risk_reward || signal.riskReward || '0'),
      status: (signal.status || 'active') as 'active' | 'completed' | 'cancelled',
      result: signal.result,
      created_at: signal.created_at || signal.createdAt || new Date().toISOString(),
      unrealized_pnl_pct: signal.unrealized_pnl_pct,
      progress_to_tp: signal.progress_to_tp,
      distance_to_sl: signal.distance_to_sl,
      distance_to_tp: signal.distance_to_tp,
      time_in_trade: signal.time_in_trade,
      telegram_updated: signal.telegram_updated
    }));

    this.renderSignals();
    this.updateStats();
    
    console.log(`✅ Loaded ${this.signals.length} signals`);
  } catch (error) {
    console.error('❌ Error loading signals:', error);
    this.showError(error instanceof Error ? error.message : 'Failed to load signals');
  }
}

private showError(message: string): void {
  const signalsList = this.container.querySelector('#signals-list');
  if (signalsList) {
    signalsList.innerHTML = `
      <div class="error-state">
        <span class="error-icon">❌</span>
        <p>Ошибка загрузки сигналов: ${message}</p>
        <button class="retry-btn" id="retry-load-signals">Повторить</button>
      </div>
    `;
    
    const retryBtn = this.container.querySelector('#retry-load-signals');
    if (retryBtn) {
      retryBtn.addEventListener('click', () => this.loadSignals());
    }
  }
}
```

### ШАГ 7: Убедиться, что MCP сервер запущен с API ключами

**Проверить:**
1. `.env` файл существует в корне проекта
2. `BYBIT_API_KEY` и `BYBIT_API_SECRET` установлены
3. HTTP сервер запущен: `cd bybit-mcp && node build/httpServer.js`

**Скрипт запуска:** `bybit-mcp/scripts/start-http-server.sh`
```bash
#!/bin/bash
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/../.." && pwd )"

if [ -f "$PROJECT_ROOT/.env" ]; then
  echo "✅ Loading environment variables from $PROJECT_ROOT/.env"
  export $(cat "$PROJECT_ROOT/.env" | grep -v '^#' | xargs)
fi

cd "$SCRIPT_DIR/.."
echo "🚀 Starting MCP HTTP server..."
node build/httpServer.js
```

---

## 🧪 ТЕСТИРОВАНИЕ

После всех исправлений:

1. **Пересобрать проект:**
```bash
cd bybit-mcp
pnpm run build
```

2. **Запустить HTTP сервер:**
```bash
cd bybit-mcp
chmod +x scripts/start-http-server.sh
./scripts/start-http-server.sh
```

3. **Запустить UI:**
```bash
cd bybit-mcp/webui
pnpm run dev
```

4. **Проверить в браузере `http://localhost:3001/`:**
   - ✅ Портфель показывает реальный баланс (не $0.00)
   - ✅ Позиции загружаются (если есть открытые)
   - ✅ Order History загружается
   - ✅ Signal Monitoring загружается
   - ✅ Нет HTTP 404 ошибок в консоли

---

## 📝 ЧЕКЛИСТ ИСПРАВЛЕНИЙ

- [ ] Исправить `vite.config.ts` - добавить прокси для `/tools`, `/call-tool`, `/health`
- [ ] Исправить `mcpClient.ts` - логика baseUrl для всех портов
- [ ] Добавить fallback в `callTool()` для прямых запросов
- [ ] Создать `OrderHistory.ts` компонент
- [ ] Интегрировать OrderHistory в TradingTerminal
- [ ] Исправить `SignalMonitoringPanel.ts` - метод `loadSignals()`
- [ ] Добавить обработку ошибок в SignalMonitoringPanel
- [ ] Пересобрать проект
- [ ] Протестировать все компоненты

---

## ✅ ОЖИДАЕМЫЙ РЕЗУЛЬТАТ

После применения всех исправлений:
- ✅ Все HTTP 404 ошибки устранены
- ✅ Портфель показывает реальные данные
- ✅ Позиции загружаются в реальном времени
- ✅ Order History работает и показывает историю сделок
- ✅ Signal Monitoring загружает сигналы без ошибок
- ✅ MCP сервер получает API ключи из `.env`
- ✅ Все компоненты обновляются автоматически
- ✅ Полноценная боевая машина для AI трейдинга готова к работе

---

**ВАЖНО:** Читай существующий код перед изменениями. Все исправления должны быть обратно совместимыми. Добавь детальное логирование для отладки.



