# 🤖 Autonomous Trading Agent с Qwen AI

Автономный агент для автоматического анализа криптовалютного рынка и публикации топовых точек входа.

## 🎯 Возможности

- ✅ Автоматический анализ рынка через Bybit API
- ✅ Интеграция с Qwen AI от Alibaba Cloud для умного анализа
- ✅ Поиск ТОП 3 лучших точек входа с confluence ≥ 8.0/10
- ✅ Фильтрация по вероятности ≥ 70% и R:R ≥ 1:2
- ✅ Форматирование результатов для публикации в Telegram
- ✅ Готовность к развёртыванию в Kubernetes

## 📋 Требования

- Python 3.10+
- API ключ Alibaba Cloud Qwen (`sk-...`)
- API ключи Bybit (публичный и секретный)
- Все зависимости из `requirements.txt`

## 🚀 Быстрый старт

### 1. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 2. Настройка переменных окружения

```bash
export QWEN_API_KEY="sk-6f5319fb244f4f9faa1595825cf87a05"
export BYBIT_API_KEY="your_bybit_api_key"
export BYBIT_API_SECRET="your_bybit_api_secret"
export QWEN_MODEL="qwen-max"  # Опционально: qwen-max, qwen-plus, qwen-turbo
export BYBIT_TESTNET="false"  # Опционально: true для testnet
```

### 3. Запуск анализа

```bash
python -m autonomous_agent.main
```

## 📁 Структура

```
autonomous_agent/
├── __init__.py              # Инициализация модуля
├── qwen_client.py           # Клиент для Alibaba Cloud Qwen API
├── autonomous_analyzer.py   # Основной анализатор рынка
├── telegram_formatter.py    # Форматирование для Telegram
├── main.py                  # Точка входа
└── README.md                # Документация
```

## 🔧 Конфигурация

### Через переменные окружения (рекомендуется)

```bash
QWEN_API_KEY=sk-...
BYBIT_API_KEY=...
BYBIT_API_SECRET=...
QWEN_MODEL=qwen-max
BYBIT_TESTNET=false
```

### Через файл конфигурации

Создайте файл `config/autonomous_agent.json`:

```json
{
  "qwen_api_key": "sk-...",
  "bybit_api_key": "...",
  "bybit_api_secret": "...",
  "qwen_model": "qwen-max",
  "testnet": false
}
```

## 📊 Формат вывода

Агент сохраняет результаты в:

1. **`data/latest_analysis.json`** - Полный JSON результат анализа
2. **`data/latest_telegram_message.txt`** - Отформатированное сообщение для Telegram

### Пример Telegram сообщения:

```
🎯 ТОП 3 ТОЧКИ ВХОДА
📅 2025-01-18 12:00:00

🟢 BTC Status: BULLISH

⭐ #1. BTC/USDT 🟢 LONG

💰 Entry: $50000.0000
🛑 Stop Loss: $49500.0000
🎯 Take Profit: $51000.0000
📊 R:R = 1:2.00

⭐ Confluence: 8.5/10
📈 Вероятность: 75%

🔑 Ключевые факторы:
  • Signal: STRONG_BUY
  • 1h RSI oversold (28.5)
  • 4h Support level

💡 Обоснование:
Отличная возможность. Факторы: RSI oversold; Support level; Bullish pattern

⏰ Таймфреймы: 15m, 1h, 4h, 1d
```

## 🔄 Интеграция с Telegram ботом

Агент готов к интеграции с вашим Telegram ботом. Просто читайте файл `data/latest_telegram_message.txt` и отправляйте его в канал:

```python
# Пример интеграции
from pathlib import Path
import telegram

telegram_message = Path("data/latest_telegram_message.txt").read_text()
bot = telegram.Bot(token="YOUR_BOT_TOKEN")
await bot.send_message(chat_id="@your_channel", text=telegram_message)
```

## 🐳 Развёртывание в Kubernetes

### Dockerfile пример:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "-m", "autonomous_agent.main"]
```

### Kubernetes CronJob пример:

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: trading-agent-analysis
spec:
  schedule: "*/30 * * * *"  # Каждые 30 минут
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: analyzer
            image: your-registry/trading-agent:latest
            env:
            - name: QWEN_API_KEY
              valueFrom:
                secretKeyRef:
                  name: trading-secrets
                  key: qwen-api-key
            - name: BYBIT_API_KEY
              valueFrom:
                secretKeyRef:
                  name: trading-secrets
                  key: bybit-api-key
            - name: BYBIT_API_SECRET
              valueFrom:
                secretKeyRef:
                  name: trading-secrets
                  key: bybit-api-secret
          restartPolicy: OnFailure
```

## 📝 Логирование

Логи сохраняются в `logs/autonomous_agent_YYYY-MM-DD.log` с ротацией каждый день и хранением 7 дней.

## 🔍 Процесс анализа

1. **Market Overview** - Получение общего обзора рынка
2. **BTC Analysis** - Детальный анализ BTC (лидер рынка)
3. **Market Scanning** - Параллельное сканирование всех возможностей
4. **Deep Analysis** - Детальный анализ топ кандидатов
5. **Qwen AI Analysis** - Умный анализ через Qwen AI
6. **Finalization** - Финализация топ 3 возможностей

## ⚙️ Параметры анализа

- **Минимальный confluence:** 8.0/10
- **Минимальная вероятность:** 70%
- **Минимальный R:R:** 1:2
- **Таймфреймы:** 15m, 1h, 4h, 1d
- **Минимальный объём:** $1M за 24ч

## 🛡️ Безопасность

- ✅ Используйте read-only API ключи для Bybit
- ✅ Храните секреты в Kubernetes Secrets или переменных окружения
- ✅ Не коммитьте конфигурационные файлы с секретами

## 📞 Поддержка

При возникновении проблем проверьте:
1. Правильность API ключей
2. Доступность Bybit API
3. Доступность Alibaba Cloud Qwen API
4. Логи в `logs/autonomous_agent_*.log`

## 📄 Лицензия

Часть проекта TRADER-AGENT

