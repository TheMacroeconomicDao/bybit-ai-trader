# 🏗️ Архитектура Autonomous Trading Agent

## Обзор системы

Автономный торговый агент состоит из следующих компонентов:

```
┌─────────────────────────────────────────────────────────────┐
│                    Autonomous Trading Agent                  │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐      ┌──────────────┐                    │
│  │ QwenClient   │      │ BybitClient  │                    │
│  │              │      │              │                    │
│  │ • API calls  │      │ • Market data│                    │
│  │ • Analysis   │      │ • OHLCV      │                    │
│  └──────┬───────┘      └──────┬───────┘                    │
│         │                     │                             │
│         └──────────┬──────────┘                             │
│                    │                                         │
│         ┌──────────▼──────────┐                            │
│         │ AutonomousAnalyzer  │                            │
│         │                     │                            │
│         │ • Market scanning   │                            │
│         │ • Deep analysis     │                            │
│         │ • Qwen integration  │                            │
│         │ • Top 3 selection   │                            │
│         └──────────┬──────────┘                            │
│                    │                                         │
│         ┌──────────▼──────────┐                            │
│         │ TelegramFormatter    │                            │
│         │                      │                            │
│         │ • Format messages    │                            │
│         │ • Prepare for TG     │                            │
│         └──────────────────────┘                            │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Компоненты

### 1. QwenClient (`qwen_client.py`)

**Назначение:** Взаимодействие с Alibaba Cloud Qwen API

**Основные методы:**
- `generate()` - Генерация ответа от Qwen
- `analyze_market_opportunities()` - Анализ рыночных возможностей

**Особенности:**
- Асинхронные запросы через aiohttp
- Обработка ошибок и таймаутов
- Поддержка системных промптов
- Парсинг JSON ответов

### 2. AutonomousAnalyzer (`autonomous_analyzer.py`)

**Назначение:** Основной анализатор рынка

**Процесс анализа:**

1. **Market Overview** - Получение общего обзора рынка
2. **BTC Analysis** - Детальный анализ BTC
3. **Market Scanning** - Параллельное сканирование:
   - `scan_market()` с разными критериями
   - `find_oversold_assets()`
   - `find_breakout_opportunities()`
   - `find_trend_reversals()`
4. **Deep Analysis** - Детальный анализ топ кандидатов:
   - Полный технический анализ на всех таймфреймах
   - Валидация точек входа
   - Расчёт финального score
5. **Qwen AI Analysis** - Умный анализ через Qwen
6. **Finalization** - Финализация топ 3 возможностей

**Критерии фильтрации:**
- Confluence score ≥ 8.0/10
- Вероятность ≥ 70%
- R:R ≥ 1:2
- Multi-timeframe alignment

### 3. TelegramFormatter (`telegram_formatter.py`)

**Назначение:** Форматирование результатов для Telegram

**Методы:**
- `format_top_opportunities()` - Форматирование топ 3
- `format_market_summary()` - Краткое резюме рынка
- `format_error()` - Форматирование ошибок

**Формат сообщения:**
- Структурированный текст с эмодзи
- Детальная информация по каждой возможности
- Метрики и обоснование

### 4. Main (`main.py`)

**Назначение:** Точка входа и оркестрация

**Функции:**
- Загрузка конфигурации
- Инициализация компонентов
- Запуск анализа
- Сохранение результатов
- Обработка ошибок

## Поток данных

```
1. main.py запускает AutonomousAnalyzer
   │
   ├─► BybitClient получает рыночные данные
   │   ├─ Market overview
   │   ├─ BTC analysis
   │   └─ Ticker data
   │
   ├─► MarketScanner сканирует рынок
   │   ├─ Parallel scanning
   │   └─ Opportunity filtering
   │
   ├─► TechnicalAnalysis анализирует активы
   │   ├─ Multi-timeframe analysis
   │   ├─ Indicator calculation
   │   └─ Pattern detection
   │
   ├─► QwenClient анализирует через AI
   │   └─ Smart opportunity ranking
   │
   ├─► AutonomousAnalyzer финализирует топ 3
   │   └─ Score calculation & filtering
   │
   └─► TelegramFormatter форматирует результат
       └─ Ready for Telegram publication
```

## Интеграция с существующей системой

Агент использует существующие компоненты:

- ✅ `BybitClient` - для получения рыночных данных
- ✅ `TechnicalAnalysis` - для технического анализа
- ✅ `MarketScanner` - для сканирования рынка
- ✅ База знаний из `knowledge_base/`
- ✅ Промпты из `prompts/`

## Конфигурация

### Переменные окружения

```bash
QWEN_API_KEY          # API ключ Alibaba Cloud (sk-...)
BYBIT_API_KEY         # Bybit API ключ
BYBIT_API_SECRET      # Bybit API секрет
QWEN_MODEL            # Модель Qwen (qwen-max, qwen-plus, qwen-turbo)
BYBIT_TESTNET         # Использовать testnet (true/false)
```

### Файл конфигурации

`config/autonomous_agent.json` - альтернативный способ конфигурации

## Результаты

Агент сохраняет результаты в:

1. **`data/latest_analysis.json`** - Полный JSON результат
2. **`data/latest_telegram_message.txt`** - Готовое сообщение для Telegram

## Логирование

Логи сохраняются в `logs/autonomous_agent_YYYY-MM-DD.log`:
- Ротация: каждый день
- Хранение: 7 дней
- Уровень: INFO и выше

## Масштабирование

### Локальный запуск

```bash
python -m autonomous_agent.main
```

### Kubernetes CronJob

Автоматический запуск по расписанию (например, каждые 30 минут)

### Docker контейнер

Готов к контейнеризации для развёртывания в Kubernetes

## Безопасность

- ✅ Использование read-only API ключей для Bybit
- ✅ Хранение секретов в переменных окружения или Kubernetes Secrets
- ✅ Не коммитятся конфигурационные файлы с секретами
- ✅ Обработка ошибок и таймаутов

## Производительность

- Параллельное сканирование рынка (до 10 одновременных запросов)
- Кеширование данных через BybitClient
- Оптимизированный процесс анализа (фильтрация на ранних этапах)
- Асинхронные операции через asyncio

## Расширяемость

Система легко расширяется:

1. **Новые критерии сканирования** - добавьте в `MarketScanner`
2. **Новые индикаторы** - добавьте в `TechnicalAnalysis`
3. **Новые форматы вывода** - добавьте в `TelegramFormatter`
4. **Интеграция с другими AI** - добавьте новые клиенты

