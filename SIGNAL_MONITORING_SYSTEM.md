# 📡 Система Мониторинга Сигналов

## Обзор

Реализована комплексная система мониторинга торговых сигналов в реальном времени с интеграцией в UI и автоматическим обновлением Telegram постов.

---

## 🎯 Возможности

### 1. UI Компонент `SignalMonitoringPanel`
- ✅ Real-time мониторинг активных сигналов
- ✅ Визуальные индикаторы состояния (🟢/🟡/🟠/🔴)
- ✅ Прогресс-бары к TP/SL
- ✅ Метрики P/L, Confluence, Probability
- ✅ Автообновление каждые 30 секунд
- ✅ Фильтрация и сортировка сигналов

### 2. Telegram Интеграция
- ✅ Автоматическое обновление постов в реальном времени
- ✅ Индикаторы состояния сигналов
- ✅ Прогресс-бары в текстовом формате
- ✅ Информация о P/L, времени в сделке
- ✅ Цветовое кодирование статусов

### 3. Backend Система
- ✅ Хранение `message_id` для каждого сигнала
- ✅ Автоматическое обновление при изменении цены
- ✅ Интеграция с `SignalPriceMonitor`

---

## 📁 Структура Файлов

### Backend (Python)

1. **`mcp_server/telegram_bot.py`** (расширен)
   - Добавлен метод `edit_message()` для редактирования постов

2. **`mcp_server/signal_tracker.py`** (расширен)
   - Добавлена колонка `telegram_message_ids` в БД
   - Методы `set_telegram_message_ids()` и `get_telegram_message_ids()`

3. **`mcp_server/telegram_signal_updater.py`** (новый)
   - Класс `TelegramSignalUpdater`
   - Генерация индикаторов состояния
   - Обновление Telegram постов

4. **`mcp_server/signal_price_monitor.py`** (расширен)
   - Интеграция обновления Telegram постов при изменении цены

### Frontend (TypeScript)

1. **`bybit-mcp/webui/src/components/SignalMonitoringPanel.ts`** (новый)
   - Компонент мониторинга сигналов
   - Real-time обновления через MCP

2. **`bybit-mcp/webui/src/styles/signal-monitoring.css`** (новый)
   - Стили для компонента мониторинга

---

## 🚀 Использование

### 1. Сохранение message_id при публикации сигнала

```python
from mcp_server.telegram_bot import TelegramBot
from mcp_server.signal_tracker import SignalTracker

# При публикации сигнала в Telegram
bot = TelegramBot("YOUR_BOT_TOKEN")
tracker = SignalTracker()

# Отправляем сообщение
result = await bot.send_message(chat_id="-1003382613825", text=message, parse_mode="HTML")
message_id = result["result"]["message_id"]

# Сохраняем message_id для сигнала
signal_id = "your-signal-id"
await tracker.set_telegram_message_ids(signal_id, {
    "-1003382613825": message_id,
    "-1003484839912": another_message_id  # если несколько каналов
})
```

### 2. Автоматическое обновление постов

Обновление происходит автоматически при изменении цены через `SignalPriceMonitor`. 

Для ручного обновления:

```python
from mcp_server.telegram_signal_updater import TelegramSignalUpdater
from mcp_server.telegram_bot import TelegramBot

bot = TelegramBot("YOUR_BOT_TOKEN")
tracker = SignalTracker()
updater = TelegramSignalUpdater(tracker, bot, "YOUR_BOT_TOKEN")

# Обновить один сигнал
await updater.update_signal_post(signal_id="signal-id", current_price=50000.0)

# Обновить все активные сигналы
await updater.update_all_active_signals()
```

### 3. Использование UI компонента

```typescript
import { SignalMonitoringPanel } from '@/components/SignalMonitoringPanel';

// В вашем layout или главном компоненте
const signalPanel = new SignalMonitoringPanel('signal-monitoring-container');

// Компонент автоматически:
// - Загружает сигналы через MCP
// - Обновляет каждые 30 секунд
// - Показывает индикаторы состояния
```

### 4. Добавление в MainLayout

```typescript
// В MainLayout.ts или где используете панели
<div id="signal-monitoring-container"></div>

// Инициализация
import { SignalMonitoringPanel } from '@/components/SignalMonitoringPanel';
const signalPanel = new SignalMonitoringPanel('signal-monitoring-container');
```

---

## 📊 Формат Индикаторов в Telegram

Индикатор состояния добавляется в Telegram пост в следующем формате:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 СТАТУС СИГНАЛА: BTCUSDT

🟢 NEAR TP 🟢

Прогресс к TP:
████████████████████░░ 85.3%

Текущая цена: $51,200.00
Entry: $50,000.00
Stop-Loss: $48,000.00
Take-Profit: $52,000.00

P/L: 🟢 📈 +2.40%

⏱️ Время в сделке: 2h 15m

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Статусы Индикаторов

- 🟢 **NEAR TP** - Прогресс ≥ 75%
- 🟡 **IN PROGRESS** - Прогресс 50-75%
- 🟠 **EARLY STAGE** - Прогресс 25-50%
- 🔴 **NEAR SL** - Прогресс < 25%
- ✅ **TP HIT** - Take-Profit достигнут
- ❌ **SL HIT** - Stop-Loss достигнут

---

## ⚙️ Конфигурация

### Переменные окружения

```bash
# Telegram Bot Token для обновления постов
export TELEGRAM_BOT_TOKEN="your-bot-token"
```

### Настройка интервала обновления

В `SignalPriceMonitor`:
```python
signal_monitor = SignalPriceMonitor(
    signal_tracker,
    bybit_client,
    check_interval=300  # 5 минут (по умолчанию)
)
```

В UI компоненте:
```typescript
// Автообновление каждые 30 секунд (по умолчанию)
// Можно изменить в SignalMonitoringPanel.ts:
this.updateInterval = setInterval(() => {
    this.loadSignals();
}, 30000);  // изменить на нужный интервал
```

---

## 🎨 UI Компонент - Детали

### Структура компонента

```
SignalMonitoringPanel
├── Header (заголовок + статус LIVE)
├── Stats Grid (4 карточки метрик)
├── Filters (статус, сортировка)
└── Signals List (карточки сигналов)
```

### Карточка сигнала включает:

- **Header**: Символ, сторона (LONG/SHORT), статус индикатор
- **Price Section**: Entry и Current цена
- **P/L Section**: Процент прибыли/убытка
- **Progress Section**: Прогресс-бар к TP
- **Levels Section**: Расстояние до SL/TP
- **Metrics Section**: Confluence, Probability, R:R, время в сделке
- **Footer**: Кнопки действий (Детали, Обновить Telegram)

### Фильтры

- **Все** - показать все сигналы
- **Активные** - только активные
- **Завершенные** - только завершенные

### Сортировка

- Новые первыми
- Прогресс ↓/↑
- Confluence ↓
- Символ A-Z

---

## 🔧 MCP Tools

Для работы UI компонента нужны следующие MCP tools:

1. **`get_active_signals`** - получение активных сигналов
   ```python
   @app.call_tool()
   async def get_active_signals() -> List[TextContent]:
       signals = await signal_tracker.get_active_signals()
       return [TextContent(type="text", text=json.dumps(signals))]
   ```

2. **`get_price_snapshots`** - получение snapshots цены
   ```python
   @app.call_tool()
   async def get_price_snapshots(signal_id: str, limit: int = 100) -> List[TextContent]:
       snapshots = await signal_tracker.get_price_snapshots(signal_id, limit)
       return [TextContent(type="text", text=json.dumps(snapshots))]
   ```

---

## 📝 Примеры

### Пример 1: Публикация сигнала с сохранением message_id

```python
async def publish_signal_with_tracking(signal_data: dict):
    bot = TelegramBot("YOUR_BOT_TOKEN")
    tracker = SignalTracker()
    
    # Записываем сигнал
    signal_id = await tracker.record_signal(
        symbol=signal_data["symbol"],
        side=signal_data["side"],
        entry_price=signal_data["entry_price"],
        stop_loss=signal_data["stop_loss"],
        take_profit=signal_data["take_profit"],
        confluence_score=signal_data["confluence_score"],
        probability=signal_data["probability"]
    )
    
    # Формируем сообщение
    message = format_trading_signal(signal_data)
    
    # Отправляем в каналы
    message_ids = {}
    for chat_id in ["-1003382613825", "-1003484839912"]:
        result = await bot.send_message(chat_id, message, parse_mode="HTML")
        message_ids[chat_id] = result["result"]["message_id"]
    
    # Сохраняем message_ids
    await tracker.set_telegram_message_ids(signal_id, message_ids)
    
    await bot.close()
```

### Пример 2: Ручное обновление поста

```python
async def manually_update_signal_post(signal_id: str):
    bot = TelegramBot("YOUR_BOT_TOKEN")
    tracker = SignalTracker()
    updater = TelegramSignalUpdater(tracker, bot, "YOUR_BOT_TOKEN")
    
    # Получаем текущую цену
    signal = await tracker.get_signal(signal_id)
    # ... получаем цену через API ...
    
    # Обновляем пост
    await updater.update_signal_post(signal_id, current_price=50000.0)
    
    await bot.close()
```

---

## 🐛 Troubleshooting

### Telegram посты не обновляются

1. Проверьте что `TELEGRAM_BOT_TOKEN` установлен
2. Убедитесь что `message_id` сохранены в БД
3. Проверьте логи на ошибки обновления

### UI компонент не загружает сигналы

1. Проверьте что MCP tools `get_active_signals` и `get_price_snapshots` доступны
2. Проверьте консоль браузера на ошибки
3. Убедитесь что компонент инициализирован после загрузки MCP client

### Индикаторы не отображаются корректно

1. Проверьте что `current_price` обновляется в snapshots
2. Убедитесь что `progress_to_tp` рассчитывается правильно
3. Проверьте логику определения статуса в `generate_status_indicator()`

---

## 🔮 Будущие Улучшения

- [ ] WebSocket обновления для real-time UI
- [ ] Графики прогресса сигналов
- [ ] Уведомления при достижении TP/SL
- [ ] Экспорт статистики сигналов
- [ ] Интеграция с TradingView для визуализации
- [ ] Мобильная версия компонента

---

## 📚 Связанные Документы

- `TELEGRAM_BOT_INTEGRATION.md` - Интеграция Telegram Bot
- `TRADE_COPILOT_UX_UI_DESIGN.md` - UI дизайн система
- `mcp_server/signal_tracker.py` - Документация SignalTracker

---

**Версия:** 1.0  
**Дата:** 2024  
**Статус:** ✅ Реализовано


