# 🔧 ПРОМПТ: Исправление Trading Terminal UI - Реальные Данные

## ЗАДАЧА

В Trading Terminal UI (WebUI) данные о позициях, портфеле и истории сделок **захардкожены или не получаются из реальных источников**. Нужно исправить код так, чтобы **ВСЕ данные приходили из реальных MCP tools** и отображались корректно.

## ПРОБЛЕМЫ

### 1. Позиции не отображаются
- `tradingDataService.getPositions()` вызывает `get_positions` MCP tool, но ответ может парситься неправильно
- Fallback на MCP в `TradingDashboard.updatePositions()` может не работать
- Нужно использовать правильный MCP tool: `mcp_user-bybit-trading_get_open_positions`

### 2. Портфель показывает захардкоженные значения
- `tradingDataService.getPortfolio()` использует `get_wallet_balance`, но парсинг может быть неправильным
- Нужно использовать: `mcp_user-bybit-trading_get_account_info` для полной информации

### 3. История сделок отсутствует
- Нет компонента для отображения истории ордеров
- Нужно добавить использование: `mcp_user-bybit-trading_get_order_history`

### 4. AI Status захардкожен
- В `TradingDashboard.updateAIStatus()` confidence = 85 (hardcoded)
- Нужно получать реальные данные из analytics или убрать

## ФАЙЛЫ ДЛЯ ИСПРАВЛЕНИЯ

### 1. `bybit-mcp/webui/src/services/tradingDataService.ts`

**Проблема:** Методы `getPositions()` и `getPortfolio()` используют неправильные MCP tool names или неправильно парсят ответы.

**Исправления:**

```typescript
// В методе getPositions() - ИСПРАВИТЬ:
async getPositions(): Promise<Position[]> {
  // Удалить весь старый код парсинга
  
  // ИСПОЛЬЗОВАТЬ ПРАВИЛЬНЫЙ MCP TOOL:
  try {
    const result: any = await mcpClient.callTool('mcp_user-bybit-trading_get_open_positions', {});
    
    // Правильный парсинг ответа
    let positions: any[] = [];
    
    // MCP response format: { content: [{ type: 'text', text: '...' }] }
    if (result?.content?.[0]?.text) {
      try {
        positions = JSON.parse(result.content[0].text);
      } catch (e) {
        // Если уже массив
        positions = Array.isArray(result.content[0].text) 
          ? result.content[0].text 
          : [];
      }
    } else if (Array.isArray(result)) {
      positions = result;
    } else if (result?.positions && Array.isArray(result.positions)) {
      positions = result.positions;
    }
    
    // Преобразовать в формат Position
    if (positions.length > 0) {
      positions.forEach((pos: any) => {
        const position: Position = {
          symbol: this.normalizeSymbol(pos.symbol || ''),
          side: pos.side === 'Sell' ? 'Sell' : 'Buy',
          size: parseFloat(pos.size?.toString() || '0'),
          entry_price: parseFloat(pos.entry_price?.toString() || pos.avgPrice?.toString() || '0'),
          current_price: parseFloat(pos.current_price?.toString() || pos.markPrice?.toString() || '0'),
          unrealized_pnl: parseFloat(pos.unrealized_pnl?.toString() || pos.unrealisedPnl?.toString() || '0'),
          unrealized_pnl_pct: parseFloat(pos.unrealized_pnl_pct?.toString() || 
            (pos.unrealisedPnlPct ? (pos.unrealisedPnlPct * 100).toString() : '0')),
          leverage: pos.leverage ? parseFloat(pos.leverage.toString()) : 1,
          stop_loss: pos.stop_loss || pos.stopLoss ? parseFloat((pos.stop_loss || pos.stopLoss).toString()) : undefined,
          take_profit: pos.take_profit || pos.takeProfit ? parseFloat((pos.take_profit || pos.takeProfit).toString()) : undefined,
          time_in_trade: pos.time_in_trade || this.calculateTimeInTrade(pos.createdTime),
          status: this.calculatePositionStatus(pos),
          updated_at: Date.now()
        };
        
        this.positions.set(position.symbol, position);
        this.notifySubscribers(`position:${position.symbol}`, position);
      });
    }
    
    return Array.from(this.positions.values());
  } catch (error) {
    console.error('Failed to fetch positions:', error);
    return Array.from(this.positions.values()); // Return cached if available
  }
}

// В методе getPortfolio() - ИСПРАВИТЬ:
async getPortfolio(): Promise<PortfolioData> {
  try {
    // ИСПОЛЬЗОВАТЬ ПРАВИЛЬНЫЙ MCP TOOL:
    const result: any = await mcpClient.callTool('mcp_user-bybit-trading_get_account_info', {});
    
    let accountData: any = null;
    
    // Парсинг MCP response
    if (result?.content?.[0]?.text) {
      try {
        accountData = JSON.parse(result.content[0].text);
      } catch (e) {
        accountData = result;
      }
    } else {
      accountData = result;
    }
    
    // Извлечение данных из правильной структуры
    const balance = accountData?.balance?.unified?.total || 
                   accountData?.balance?.total || 
                   accountData?.result?.list?.[0]?.totalEquity || 0;
    
    const available = accountData?.balance?.unified?.available || 
                     accountData?.balance?.available || 
                     accountData?.result?.list?.[0]?.totalAvailableBalance || 0;
    
    const usedMargin = accountData?.balance?.unified?.used_margin || 
                      accountData?.balance?.used_margin || 
                      accountData?.result?.list?.[0]?.totalUsedMargin || 0;
    
    const unrealizedPnl = accountData?.balance?.unified?.unrealized_pnl || 
                          accountData?.balance?.unrealized_pnl || 
                          accountData?.result?.list?.[0]?.totalUnrealisedPnl || 0;
    
    this.portfolioData = {
      balance: parseFloat(balance.toString()),
      available: parseFloat(available.toString()),
      used_margin: parseFloat(usedMargin.toString()),
      unrealized_pnl: parseFloat(unrealizedPnl.toString()),
      daily_pnl: 0, // Можно получить из истории
      total_pnl_pct: parseFloat(balance.toString()) > 0 
        ? (parseFloat(unrealizedPnl.toString()) / parseFloat(balance.toString())) * 100 
        : 0,
      updated_at: Date.now()
    };
    
    this.notifySubscribers('portfolio', this.portfolioData);
    return this.portfolioData;
  } catch (error) {
    console.error('Failed to fetch portfolio:', error);
    // Return cached or default
    return this.portfolioData || {
      balance: 0,
      available: 0,
      used_margin: 0,
      unrealized_pnl: 0,
      daily_pnl: 0,
      total_pnl_pct: 0,
      updated_at: Date.now()
    };
  }
}

// ДОБАВИТЬ НОВЫЙ МЕТОД для истории ордеров:
async getOrderHistory(category: string = 'linear', limit: number = 50): Promise<any[]> {
  try {
    const result: any = await mcpClient.callTool('mcp_user-bybit-trading_get_order_history', {
      category,
      limit: limit.toString()
    });
    
    let orders: any[] = [];
    
    if (result?.content?.[0]?.text) {
      try {
        const parsed = JSON.parse(result.content[0].text);
        orders = parsed?.list || parsed || [];
      } catch (e) {
        orders = Array.isArray(result.content[0].text) ? result.content[0].text : [];
      }
    } else if (Array.isArray(result)) {
      orders = result;
    } else if (result?.list && Array.isArray(result.list)) {
      orders = result.list;
    }
    
    return orders;
  } catch (error) {
    console.error('Failed to fetch order history:', error);
    return [];
  }
}

// ДОБАВИТЬ helper метод:
private calculateTimeInTrade(createdTime?: string | number): string {
  if (!createdTime) return '-';
  
  const created = typeof createdTime === 'string' 
    ? new Date(createdTime).getTime() 
    : typeof createdTime === 'number' 
      ? createdTime 
      : 0;
  
  if (created === 0) return '-';
  
  const now = Date.now();
  const diff = now - created;
  
  if (diff < 0) return '-';
  
  const hours = Math.floor(diff / (1000 * 60 * 60));
  const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
  
  if (hours > 0) {
    return `${hours}h ${minutes}m`;
  }
  return `${minutes}m`;
}
```

### 2. `bybit-mcp/webui/src/components/TradingDashboard.ts`

**Проблема:** 
- `updateAIStatus()` использует захардкоженное значение confidence = 85
- Fallback на MCP может не работать правильно

**Исправления:**

```typescript
// В методе updateAIStatus() - ИСПРАВИТЬ:
private updateAIStatus(): void {
  // УБРАТЬ захардкоженное значение
  // Получать из analytics или убрать вообще
  
  const confidenceBar = this.container.querySelector('#ai-confidence-bar') as HTMLElement;
  const confidenceDisplay = this.container.querySelector('#ai-confidence-display');
  const confidenceValue = this.container.querySelector('#ai-confidence-value');
  const lastAnalysis = this.container.querySelector('#ai-last-analysis');
  
  // Использовать реальные данные из analytics или убрать
  // Если нет реальных данных - скрыть или показать "N/A"
  if (confidenceBar) {
    confidenceBar.style.width = '0%'; // Или скрыть
  }
  
  if (confidenceDisplay) {
    confidenceDisplay.textContent = 'N/A'; // Или убрать секцию
  }
  
  if (confidenceValue) {
    confidenceValue.textContent = '--';
  }
  
  if (lastAnalysis) {
    lastAnalysis.textContent = 'Last analysis: N/A';
  }
}

// В методе updatePositions() - УЛУЧШИТЬ fallback:
private async updatePositions(): Promise<void> {
  try {
    const positions = await tradingDataService.getPositions();
    
    positions.forEach(pos => {
      tradingDataService.subscribeToSymbol(pos.symbol, ['price']);
    });

    this.positions = positions.map(pos => ({
      symbol: pos.symbol,
      side: pos.side,
      size: pos.size,
      entry_price: pos.entry_price,
      current_price: pos.current_price,
      unrealized_pnl: pos.unrealized_pnl,
      unrealized_pnl_pct: pos.unrealized_pnl_pct,
      leverage: pos.leverage || 1,
      stop_loss: pos.stop_loss || 0,
      take_profit: pos.take_profit || 0,
      time_in_trade: pos.time_in_trade,
      status: pos.status || 'healthy'
    }));

    this.renderPositions();
    this.updatePositionsCount();
  } catch (error) {
    console.error('Error updating positions:', error);
    // Fallback уже обработан в tradingDataService
    // Просто обновим UI с пустым списком
    this.positions = [];
    this.renderPositions();
    this.updatePositionsCount();
  }
}
```

### 3. ДОБАВИТЬ компонент для истории ордеров

**Создать:** `bybit-mcp/webui/src/components/OrderHistory.ts`

```typescript
/**
 * Order History Component - Отображение истории ордеров
 */
import { tradingDataService } from '@/services/tradingDataService';
import { mcpClient } from '@/services/mcpClient';

export class OrderHistory {
  private container: HTMLElement;
  private orders: any[] = [];
  private updateInterval: NodeJS.Timeout | null = null;

  constructor(containerId: string) {
    const element = document.getElementById(containerId);
    if (!element) {
      throw new Error(`Order history container #${containerId} not found`);
    }
    this.container = element;
    this.initialize();
  }

  private async initialize(): Promise<void> {
    this.render();
    this.setupEventListeners();
    await this.refresh();
    this.startAutoUpdate();
  }

  private setupEventListeners(): void {
    const refreshBtn = this.container.querySelector('#refresh-orders-btn');
    refreshBtn?.addEventListener('click', () => this.refresh());
  }

  private startAutoUpdate(): void {
    this.updateInterval = setInterval(() => {
      this.refresh();
    }, 10000); // Обновлять каждые 10 секунд
  }

  async refresh(): Promise<void> {
    try {
      const orders = await tradingDataService.getOrderHistory('linear', 50);
      this.orders = orders;
      this.renderOrders();
    } catch (error) {
      console.error('Error refreshing order history:', error);
    }
  }

  private render(): void {
    this.container.innerHTML = `
      <div class="order-history">
        <div class="order-history-header">
          <h3>📜 Order History</h3>
          <button id="refresh-orders-btn" class="refresh-btn">🔄</button>
        </div>
        <div class="order-history-content">
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
                <td colspan="8">Loading...</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    `;
  }

  private renderOrders(): void {
    const tbody = this.container.querySelector('#orders-tbody');
    if (!tbody) return;

    if (this.orders.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="8" class="empty-state">
            <div class="empty-message">
              <span>📭</span>
              <p>No orders found</p>
            </div>
          </td>
        </tr>
      `;
      return;
    }

    tbody.innerHTML = this.orders.map(order => {
      const time = new Date(parseInt(order.createdTime || order.updatedTime || Date.now())).toLocaleString();
      const status = order.orderStatus || order.status || 'Unknown';
      const pnl = parseFloat(order.cumRealisedPnl || order.realisedPnl || '0');
      
      return `
        <tr class="order-row ${status.toLowerCase()}">
          <td>${time}</td>
          <td><strong>${order.symbol}</strong></td>
          <td><span class="side-badge ${order.side?.toLowerCase()}">${order.side}</span></td>
          <td>${order.orderType || '-'}</td>
          <td>$${parseFloat(order.avgPrice || order.price || '0').toFixed(2)}</td>
          <td>${parseFloat(order.cumExecQty || order.qty || '0').toFixed(4)}</td>
          <td><span class="status-badge ${status.toLowerCase()}">${status}</span></td>
          <td class="${pnl >= 0 ? 'positive' : 'negative'}">
            ${pnl >= 0 ? '+' : ''}$${pnl.toFixed(2)}
          </td>
        </tr>
      `;
    }).join('');
  }

  destroy(): void {
    if (this.updateInterval) {
      clearInterval(this.updateInterval);
    }
  }
}
```

### 4. Интегрировать OrderHistory в TradingTerminal

**В файле:** `bybit-mcp/webui/src/components/TradingTerminal.ts`

Добавить в правую колонку:

```typescript
// В методе renderLayout(), в правой колонке добавить:
<!-- Order History Panel -->
<div class="terminal-panel order-history-panel" id="order-history-terminal-container">
  <div class="panel-header">
    <h3 class="panel-title">
      <span class="panel-icon">📜</span>
      <span>Order History</span>
    </h3>
    <button class="panel-action-btn" id="minimize-orders-btn" title="Minimize">−</button>
  </div>
  <div class="panel-content">
    <div id="order-history-container"></div>
  </div>
</div>
```

И в initialize():

```typescript
// Инициализировать OrderHistory
import { OrderHistory } from './OrderHistory';
this.orderHistory = new OrderHistory('order-history-container');
```

## ПРОВЕРКА MCP TOOL NAMES

Убедиться, что используются правильные имена MCP tools:

- ✅ `mcp_user-bybit-trading_get_open_positions` - для позиций
- ✅ `mcp_user-bybit-trading_get_account_info` - для портфеля
- ✅ `mcp_user-bybit-trading_get_order_history` - для истории

**НЕ использовать:**
- ❌ `get_positions` (старое имя)
- ❌ `get_wallet_balance` (неполная информация)

## ТЕСТИРОВАНИЕ

После исправлений проверить:

1. ✅ Позиции отображаются в реальном времени
2. ✅ Портфель показывает реальный баланс
3. ✅ История ордеров загружается
4. ✅ Данные обновляются автоматически
5. ✅ Нет захардкоженных значений
6. ✅ Ошибки обрабатываются gracefully

## ДОПОЛНИТЕЛЬНО

Если данные все еще не приходят:

1. Проверить `mcpClient.callTool()` - правильно ли вызывается
2. Проверить формат ответа MCP - может быть другой
3. Добавить детальное логирование для отладки
4. Проверить WebSocket подключение для real-time обновлений

---

**ВАЖНО:** Все изменения должны быть обратно совместимыми и не ломать существующий функционал. Добавить обработку ошибок везде, где это возможно.



