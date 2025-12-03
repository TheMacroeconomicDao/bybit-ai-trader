# Объединение двух MCP серверов Bybit в единый моносервер

## 🎯 ЦЕЛЬ

Объединить два существующих MCP сервера Bybit в один унифицированный моносервер, который будет предоставлять все инструменты через единый интерфейс.

## 📊 ТЕКУЩАЯ АРХИТЕКТУРА

### Сервер 1: Python MCP Server (`mcp_server/full_server.py`)

**Расположение:** `mcp_server/full_server.py`  
**Транспорт:** stdio (MCP SDK для Python)  
**Порт HTTP:** Нет (только stdio)  
**Всего инструментов:** ~35

**Категории инструментов:**

#### 📊 Рыночные данные (3):
- `get_market_overview` - Полный обзор рынка
- `get_all_tickers` - Все торговые пары
- `get_asset_price` - Текущая цена актива

#### 📈 Технический анализ (8):
- `analyze_asset` - Полный анализ актива на всех таймфреймах
- `calculate_indicators` - Расчет индикаторов
- `detect_patterns` - Поиск паттернов
- `find_support_resistance` - Уровни S/R
- `get_btc_correlation` - Корреляция с BTC
- `get_funding_rate` - Funding rate для фьючерсов
- `check_tf_alignment` - Проверка alignment таймфреймов

#### 🔍 Сканирование рынка (5):
- `scan_market` - Поиск торговых возможностей
- `find_oversold_assets` - Перепроданные активы (RSI <30)
- `find_overbought_assets` - Перекупленные активы (RSI >70)
- `find_breakout_opportunities` - Возможности пробоя
- `find_trend_reversals` - Развороты тренда

#### 🎯 Валидация входа (2):
- `check_liquidity` - Проверка ликвидности
- `validate_entry` - Валидация точки входа

#### 💰 Счёт и позиции (3):
- `get_account_info` - Информация о счёте
- `get_open_positions` - Открытые позиции
- `get_order_history` - История ордеров

#### ⚡ Торговые операции (5):
- `place_order` - Открыть позицию
- `close_position` - Закрыть позицию
- `modify_position` - Изменить SL/TP
- `cancel_order` - Отменить ордер

#### 📡 Мониторинг (2):
- `start_position_monitoring` - Запуск мониторинга позиций
- `stop_position_monitoring` - Остановка мониторинга

#### 🤖 Автоматические действия (2):
- `move_to_breakeven` - Перевести SL в breakeven
- `activate_trailing_stop` - Активировать trailing stop

#### 📊 Система качества сигналов (5):
- `track_signal` - Записать сигнал для отслеживания
- `get_signal_quality_metrics` - Метрики качества сигналов
- `get_signal_performance_report` - Отчет о производительности
- `get_active_signals` - Активные сигналы
- `get_signal_details` - Детали сигнала

#### 🔬 Продвинутый анализ (2):
- `detect_whale_activity` - Анализ активности китов
- `get_volume_profile` - Volume Profile с POC и Value Area

#### 📈 Дополнительные (2):
- `get_open_interest` - Open Interest для futures
- `get_session_info` - Информация о торговой сессии

**Особенности:**
- Использует Python MCP SDK (`mcp.server`)
- Работает через stdio
- Имеет богатую бизнес-логику (technical_analysis, market_scanner, trading_operations, signal_tracker и т.д.)
- Интегрирован с базой данных для отслеживания сигналов
- Имеет автоматический мониторинг позиций и сигналов

---

### Сервер 2: Node.js MCP Server (`bybit-mcp/`)

**Расположение:** `bybit-mcp/src/index.ts` (stdio) + `bybit-mcp/src/httpServer.ts` (HTTP)  
**Транспорт:** stdio + HTTP/SSE  
**Порт HTTP:** 8081  
**Всего инструментов:** 13

**Инструменты:**

1. `get_ticker` - Информация о тикере (с reference ID для верификации)
2. `get_kline` - Данные свечей OHLCV (с reference ID)
3. `get_orderbook` - Глубина рынка
4. `get_trades` - Последние сделки
5. `get_market_info` - Обзор рынка
6. `get_instrument_info` - Детали инструмента
7. `get_ml_rsi` - ML-enhanced RSI с KNN алгоритмом
8. `get_market_structure` - Структура рынка (ML-RSI + Order Blocks + Liquidity)
9. `get_order_blocks` - Институциональные зоны накопления
10. `get_positions` - Открытые позиции (через Bybit API)
11. `get_wallet_balance` - Баланс кошелька
12. `get_order_history` - История ордеров
13. `open_webui` - Открыть WebUI в браузере

**Особенности:**
- Использует Node.js MCP SDK (`@modelcontextprotocol/sdk`)
- Поддерживает HTTP/SSE транспорт (порт 8081)
- Имеет WebUI интеграцию
- Использует `bybit-api` npm пакет
- Имеет продвинутые ML алгоритмы (KNN для RSI)
- Поддерживает reference ID для верификации данных

---

## 🔄 ПРОБЛЕМЫ ТЕКУЩЕЙ АРХИТЕКТУРЫ

1. **Дублирование функциональности:**
   - `get_positions` (Node.js) vs `get_open_positions` (Python)
   - `get_order_history` есть в обоих серверах
   - `get_wallet_balance` (Node.js) vs `get_account_info` (Python)

2. **Разные интерфейсы:**
   - Python сервер работает только через stdio
   - Node.js сервер имеет HTTP endpoint на порту 8081
   - Frontend вынужден обращаться к разным серверам

3. **Несогласованность данных:**
   - Разные форматы ответов
   - Разные названия параметров
   - Разные структуры данных

4. **Сложность поддержки:**
   - Два кодовых базы
   - Два процесса для запуска
   - Дублирование логики

---

## ✅ ЦЕЛЕВАЯ АРХИТЕКТУРА

### Единый Python MCP Server с HTTP endpoint

**Требования:**

1. **Единый сервер:**
   - Python-based (основная бизнес-логика уже там)
   - Поддержка stdio (для MCP клиентов)
   - Поддержка HTTP/SSE (для WebUI и прямых вызовов)
   - Порт: 8081 (как у Node.js сервера)

2. **Объединение инструментов:**
   - Все инструменты из Python сервера (35)
   - Все уникальные инструменты из Node.js сервера (13)
   - Удаление дубликатов с унификацией интерфейсов
   - Итого: ~45-48 уникальных инструментов

3. **Миграция Node.js инструментов:**
   - `get_ticker` → Python реализация
   - `get_kline` → Python реализация
   - `get_orderbook` → Python реализация
   - `get_trades` → Python реализация
   - `get_market_info` → Python реализация (уже есть `get_market_overview`)
   - `get_instrument_info` → Python реализация
   - `get_ml_rsi` → Python реализация (критично - ML алгоритмы)
   - `get_market_structure` → Python реализация
   - `get_order_blocks` → Python реализация
   - `get_positions` → Объединить с `get_open_positions`
   - `get_wallet_balance` → Объединить с `get_account_info`
   - `get_order_history` → Унифицировать
   - `open_webui` → Python реализация (опционально)

4. **HTTP Server:**
   - FastAPI или Flask для HTTP endpoint
   - Endpoints:
     - `GET /health` - Health check
     - `GET /tools` - Список всех инструментов
     - `POST /call-tool` - Вызов инструмента
     - `GET /api/mcp/...` - MCP совместимые endpoints
   - Поддержка CORS для WebUI
   - WebSocket для real-time обновлений (опционально)

5. **Унификация интерфейсов:**
   - Единый формат ответов
   - Единые названия параметров
   - Единая структура данных
   - Обратная совместимость где возможно

---

## 📋 ПЛАН ВЫПОЛНЕНИЯ

### Этап 1: Анализ и подготовка
- [ ] Составить полный список всех инструментов из обоих серверов
- [ ] Выявить дубликаты и определить стратегию объединения
- [ ] Определить приоритеты миграции (критичные инструменты первыми)
- [ ] Изучить ML алгоритмы из Node.js (`get_ml_rsi`, KNN)

### Этап 2: Создание HTTP сервера для Python MCP
- [ ] Добавить FastAPI/Flask в `mcp_server/full_server.py`
- [ ] Реализовать HTTP endpoints (`/health`, `/tools`, `/call-tool`)
- [ ] Добавить поддержку CORS
- [ ] Протестировать HTTP endpoint отдельно

### Этап 3: Миграция Node.js инструментов
- [ ] `get_ticker` - простая миграция (Bybit API)
- [ ] `get_kline` - простая миграция (Bybit API)
- [ ] `get_orderbook` - простая миграция (Bybit API)
- [ ] `get_trades` - простая миграция (Bybit API)
- [ ] `get_instrument_info` - простая миграция (Bybit API)
- [ ] `get_ml_rsi` - **КРИТИЧНО** - портировать ML алгоритмы (KNN, smoothing)
- [ ] `get_market_structure` - объединить с существующими анализами
- [ ] `get_order_blocks` - портировать логику определения блоков

### Этап 4: Унификация дубликатов
- [ ] Объединить `get_positions` + `get_open_positions` → единый `get_open_positions`
- [ ] Объединить `get_wallet_balance` + `get_account_info` → расширенный `get_account_info`
- [ ] Унифицировать `get_order_history` (один инструмент с опциями)

### Этап 5: Обновление frontend
- [ ] Обновить `bybit-mcp/webui/src/services/mcpClient.ts` для работы с единым сервером
- [ ] Обновить все вызовы инструментов в UI
- [ ] Удалить зависимости от Node.js MCP сервера
- [ ] Обновить конфигурацию (vite.config.ts, proxy settings)

### Этап 6: Тестирование и документация
- [ ] Протестировать все инструменты через HTTP
- [ ] Протестировать через stdio (MCP клиенты)
- [ ] Обновить документацию
- [ ] Создать migration guide

---

## 🔧 ТЕХНИЧЕСКИЕ ДЕТАЛИ

### Структура файлов

```
mcp_server/
├── full_server.py          # Основной MCP сервер (stdio + HTTP)
├── http_server.py          # HTTP endpoints (FastAPI/Flask)
├── bybit_client.py         # Клиент Bybit API
├── technical_analysis.py   # Технический анализ
├── market_scanner.py       # Сканирование рынка
├── trading_operations.py   # Торговые операции
├── signal_tracker.py       # Отслеживание сигналов
├── ml_rsi.py              # НОВЫЙ: ML-RSI с KNN (из Node.js)
├── order_blocks.py        # НОВЫЙ: Order Blocks (из Node.js)
├── market_structure.py    # НОВЫЙ: Market Structure (из Node.js)
└── ... (остальные модули)
```

### HTTP Server структура

```python
# mcp_server/http_server.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from mcp_server.full_server import app as mcp_app

app = FastAPI(title="Bybit MCP Server HTTP API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "healthy", "name": "bybit-trading-complete"}

@app.get("/tools")
async def list_tools():
    tools = await mcp_app.list_tools()
    return [tool.dict() for tool in tools]

@app.post("/call-tool")
async def call_tool(request: dict):
    name = request.get("name")
    arguments = request.get("arguments", {})
    
    result = await mcp_app.call_tool(name, arguments)
    return {"content": [{"type": "text", "text": json.dumps(result)}]}
```

### ML-RSI миграция (критично)

Node.js версия использует:
- KNN алгоритм для pattern recognition
- Smoothing методы (Kalman, ALMA, Double EMA)
- Feature extraction (RSI, momentum, volatility, slope, price_momentum)

Нужно портировать:
- `bybit-mcp/src/utils/knnAlgorithm.ts` → Python
- `bybit-mcp/src/utils/mathUtils.ts` → Python
- `bybit-mcp/src/tools/GetMLRSI.ts` → Python

---

## 📝 ПРИМЕРЫ КОДА

### Пример 1: Добавление HTTP endpoint в Python сервер

```python
# mcp_server/full_server.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# ... существующий код MCP сервера ...

# Создаем HTTP сервер
http_app = FastAPI(title="Bybit MCP HTTP Server")

http_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@http_app.get("/health")
async def health():
    return {
        "status": "healthy",
        "name": "bybit-trading-complete",
        "version": "1.0.0"
    }

@http_app.get("/tools")
async def list_tools_http():
    tools = await list_tools()
    return [tool.dict() for tool in tools]

@http_app.post("/call-tool")
async def call_tool_http(request: dict):
    name = request.get("name")
    arguments = request.get("arguments", {})
    
    if not name:
        raise HTTPException(status_code=400, detail="Tool name required")
    
    result = await app.call_tool(name, arguments)
    return {"content": result}

# Запуск HTTP сервера
if __name__ == "__main__":
    # Запускаем HTTP сервер в отдельном процессе/потоке
    uvicorn.run(http_app, host="0.0.0.0", port=8081)
```

### Пример 2: Миграция get_ticker

```python
# mcp_server/full_server.py

@app.call_tool()
async def call_tool(name: str, arguments: Any) -> List[TextContent]:
    # ... существующие инструменты ...
    
    elif name == "get_ticker":
        symbol = arguments.get("symbol")
        category = arguments.get("category", "spot")
        include_reference_id = arguments.get("includeReferenceId", False)
        
        # Используем существующий bybit_client
        ticker_data = await bybit_client.get_ticker(symbol, category)
        
        result = {
            "symbol": symbol,
            "category": category,
            "lastPrice": ticker_data["lastPrice"],
            "price24hPcnt": ticker_data["price24hPcnt"],
            # ... остальные поля
        }
        
        if include_reference_id:
            result["meta"] = {
                "requestId": str(uuid.uuid4()),
                "timestamp": datetime.now().isoformat()
            }
        
        return [TextContent(type="text", text=json.dumps(result))]
```

---

## ⚠️ КРИТИЧЕСКИЕ МОМЕНТЫ

1. **ML-RSI алгоритмы:**
   - Критично портировать KNN алгоритм точно
   - Сохранить все smoothing методы
   - Протестировать на тех же данных что Node.js версия

2. **Обратная совместимость:**
   - Frontend должен продолжать работать
   - Старые вызовы должны работать
   - Постепенная миграция

3. **Производительность:**
   - HTTP endpoint не должен замедлять stdio
   - Кэширование где возможно
   - Асинхронная обработка

4. **Тестирование:**
   - Все инструменты должны быть протестированы
   - Сравнение результатов с Node.js версией
   - Интеграционные тесты

---

## 🎯 РЕЗУЛЬТАТ

После выполнения:

1. ✅ Один MCP сервер вместо двух
2. ✅ Все инструменты доступны через stdio и HTTP
3. ✅ Единый интерфейс и формат данных
4. ✅ Упрощенная поддержка и разработка
5. ✅ WebUI работает с единым сервером
6. ✅ Все ML алгоритмы портированы в Python

---

## 📚 РЕСУРСЫ

- Python MCP SDK: https://github.com/modelcontextprotocol/python-sdk
- FastAPI: https://fastapi.tiangolo.com/
- Bybit API: https://bybit-exchange.github.io/docs/v5/
- Существующий код:
  - `mcp_server/full_server.py` - Python сервер
  - `bybit-mcp/src/index.ts` - Node.js stdio сервер
  - `bybit-mcp/src/httpServer.ts` - Node.js HTTP сервер
  - `bybit-mcp/src/tools/` - Node.js инструменты

---

**Начни с анализа дубликатов и создания HTTP сервера для Python MCP. Затем постепенно мигрируй инструменты из Node.js.**
