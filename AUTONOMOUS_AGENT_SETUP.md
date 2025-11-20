# 🤖 Autonomous Agent - Настройка и Использование

## 📋 Обзор

Autonomous Agent - это интеллектуальный агент для автоматического анализа криптовалютного рынка и публикации торговых сигналов в Telegram.

## ✅ Что реализовано

### 1. MCP Server Integration
- ✅ MCP server wrapper (`mcp_server/autonomous_agent_server.py`)
- ✅ 4 MCP инструмента для работы через Cursor
- ✅ Интеграция с существующими MCP серверами

### 2. MCP Tools Integration
- ✅ Использование `validate_entry` для валидации сигналов
- ✅ Автоматическая запись сигналов в Signal Tracker
- ✅ Интеграция с Trading Operations

### 3. WebUI Integration
- ✅ API endpoints для получения результатов анализа
- ✅ React компонент для отображения сигналов
- ✅ Автоматическое обновление каждые 60 секунд

### 4. Unified Configuration
- ✅ Единый config manager с приоритетами
- ✅ Поддержка environment variables и config files

### 5. Daily Automation
- ✅ Скрипт для ежедневного запуска
- ✅ Cron job setup script
- ✅ Автоматическая публикация в Telegram

---

## 🚀 Быстрый старт

### Шаг 1: Настройка переменных окружения

```bash
export QWEN_API_KEY="your_qwen_api_key"
export BYBIT_API_KEY="your_bybit_api_key"
export BYBIT_API_SECRET="your_bybit_api_secret"
export QWEN_MODEL="qwen/qwen-turbo"
export BYBIT_TESTNET="false"

# Опционально для Telegram публикации
export TELEGRAM_BOT_TOKEN="your_telegram_bot_token"
export TELEGRAM_CHAT_IDS="chat_id1,chat_id2"
```

Или добавьте в `.env` файл или `load_env.sh`.

### Шаг 2: Тестирование

```bash
# Запуск тестов
python scripts/test_autonomous_agent.py
```

### Шаг 3: Ручной запуск анализа

```bash
# Запуск анализа вручную
python -m autonomous_agent.main
```

### Шаг 4: Настройка автоматической публикации (раз в сутки)

```bash
# Настроить cron job (по умолчанию в 09:00)
./scripts/setup_daily_cron.sh

# Или указать своё время (например, 10:30)
./scripts/setup_daily_cron.sh 10:30
```

---

## 📖 Использование

### Через Cursor MCP

1. Убедитесь что `autonomous-agent` сервер добавлен в `CURSOR_MCP_CONFIG.json`
2. Перезапустите Cursor MCP servers
3. В Cursor вызовите:

```
"Проанализируй рынок через autonomous agent"
```

Или используйте инструменты напрямую:
- `analyze_market_comprehensive` - полный анализ рынка
- `get_last_analysis` - получить последний анализ
- `publish_analysis_to_telegram` - опубликовать в Telegram

### Через WebUI

1. Запустите WebUI: `cd bybit-mcp && pnpm dev:full`
2. Откройте `http://localhost:8081`
3. Перейдите в раздел "Agent Dashboard"
4. Внизу будет секция "Autonomous Agent Analysis"

### Через командную строку

```bash
# Запуск анализа
python -m autonomous_agent.main

# Результаты сохраняются в:
# - data/latest_analysis.json (полные результаты)
# - data/latest_telegram_message.txt (форматированное сообщение)
```

---

## ⚙️ Конфигурация

### Приоритеты конфигурации

1. **Environment Variables** (высший приоритет)
2. `config/credentials.json`
3. `config/autonomous_agent.json`
4. Defaults (низший приоритет)

### Использование Config Manager

```python
from config.config_manager import get_config

config = get_config()
print(config.qwen_model)
print(config.min_confluence)
```

---

## 📅 Автоматическая публикация

### Настройка Cron Job

```bash
# Установить cron job (запуск каждый день в 09:00)
./scripts/setup_daily_cron.sh

# Установить с кастомным временем (например, 10:30)
./scripts/setup_daily_cron.sh 10:30

# Просмотреть текущие cron jobs
crontab -l

# Редактировать cron jobs вручную
crontab -e
```

### Формат Cron

```
MINUTE HOUR * * * /path/to/script.sh
```

Примеры:
- `0 9 * * *` - каждый день в 09:00
- `30 10 * * *` - каждый день в 10:30
- `0 */6 * * *` - каждые 6 часов

### Ручной запуск ежедневного скрипта

```bash
./scripts/run_daily_analysis.sh
```

---

## 📊 Результаты анализа

### Формат результатов

Результаты сохраняются в `data/latest_analysis.json`:

```json
{
  "success": true,
  "timestamp": "2025-01-20T12:00:00",
  "top_3_longs": [
    {
      "symbol": "BTCUSDT",
      "side": "long",
      "entry_price": 50000,
      "stop_loss": 49000,
      "take_profit": 52000,
      "confluence_score": 8.5,
      "probability": 0.75,
      "risk_reward": 2.0,
      "reasoning": "...",
      "validation": {
        "is_valid": true,
        "score": 8.5
      }
    }
  ],
  "top_3_shorts": [],
  "market_summary": {
    "total_scanned": 200,
    "total_analyzed": 50,
    "longs_found": 3,
    "shorts_found": 0
  }
}
```

### Telegram публикация

Если настроены `TELEGRAM_BOT_TOKEN` и `TELEGRAM_CHAT_IDS`, результаты автоматически публикуются в указанные каналы.

---

## 🔍 Мониторинг

### Логи

- `logs/autonomous_agent_server_*.log` - логи MCP server
- `logs/autonomous_agent_*.log` - логи анализа
- `logs/daily_analysis_*.log` - логи ежедневного запуска
- `logs/cron.log` - логи cron job

### Проверка статуса

```bash
# Проверить что cron job установлен
crontab -l | grep run_daily_analysis

# Проверить последний анализ
cat data/latest_analysis.json | jq '.timestamp'

# Проверить логи
tail -f logs/daily_analysis_$(date +%Y%m%d).log
```

---

## 🐛 Troubleshooting

### Проблема: "Missing required config"

**Решение:** Убедитесь что установлены все обязательные переменные окружения:
- `QWEN_API_KEY`
- `BYBIT_API_KEY`
- `BYBIT_API_SECRET`

### Проблема: "Telegram credentials not configured"

**Решение:** Это предупреждение, не ошибка. Анализ будет выполнен, но не опубликован в Telegram. Для публикации установите:
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_IDS`

### Проблема: Cron job не запускается

**Решение:**
1. Проверьте что cron job установлен: `crontab -l`
2. Проверьте права на скрипт: `chmod +x scripts/run_daily_analysis.sh`
3. Проверьте логи: `tail -f logs/cron.log`
4. Убедитесь что пути в cron job абсолютные

### Проблема: MCP server не доступен в Cursor

**Решение:**
1. Проверьте `CURSOR_MCP_CONFIG.json`
2. Перезапустите Cursor MCP servers
3. Проверьте логи: `logs/autonomous_agent_server_*.log`

---

## 📝 Структура файлов

```
TRADER-AGENT/
├── autonomous_agent/
│   ├── autonomous_analyzer.py      # Основной анализатор
│   ├── telegram_formatter.py      # Форматирование для Telegram
│   └── main.py                     # Точка входа
├── mcp_server/
│   └── autonomous_agent_server.py  # MCP server wrapper
├── config/
│   └── config_manager.py          # Unified config manager
├── scripts/
│   ├── run_daily_analysis.sh       # Скрипт ежедневного запуска
│   ├── setup_daily_cron.sh        # Настройка cron job
│   └── test_autonomous_agent.py   # Тесты
└── data/
    ├── latest_analysis.json         # Результаты анализа
    └── latest_telegram_message.txt # Telegram сообщение
```

---

## 🎯 Следующие шаги

1. ✅ Настроить переменные окружения
2. ✅ Запустить тесты
3. ✅ Настроить cron job для ежедневной публикации
4. ✅ Проверить работу через Cursor MCP
5. ✅ Проверить отображение в WebUI

---

**Версия:** 1.0  
**Дата:** 2025-01-20  
**Статус:** ✅ Готово к использованию

