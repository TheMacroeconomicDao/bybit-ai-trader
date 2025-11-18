# 🚀 Быстрый старт - Autonomous Trading Agent

## Шаг 1: Установка зависимостей

```bash
cd /Users/Gyber/GYBERNATY-ECOSYSTEM/TRADER-AGENT
pip install -r requirements.txt
```

## Шаг 2: Настройка API ключей

### Вариант A: Переменные окружения (рекомендуется)

```bash
export QWEN_API_KEY="sk-6f5319fb244f4f9faa1595825cf87a05"
export BYBIT_API_KEY="ваш_bybit_api_key"
export BYBIT_API_SECRET="ваш_bybit_api_secret"
```

### Вариант B: Файл конфигурации

```bash
cp config/autonomous_agent.json.example config/autonomous_agent.json
# Отредактируйте config/autonomous_agent.json и заполните реальными значениями
```

## Шаг 3: Запуск анализа

```bash
python -m autonomous_agent.main
```

## Шаг 4: Проверка результатов

Результаты будут сохранены в:
- `data/latest_analysis.json` - полный JSON результат
- `data/latest_telegram_message.txt` - готовое сообщение для Telegram

## Интеграция с вашим Telegram ботом

После того как вы создали и настроили бота, просто читайте файл `data/latest_telegram_message.txt` и отправляйте его в канал:

```python
from pathlib import Path
import asyncio
from telegram import Bot

async def send_analysis():
    bot = Bot(token="YOUR_BOT_TOKEN")
    message = Path("data/latest_telegram_message.txt").read_text()
    await bot.send_message(chat_id="@your_channel", text=message)

asyncio.run(send_analysis())
```

## Автоматизация через CronJob (Kubernetes)

Создайте CronJob для запуска анализа каждые 30 минут:

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

## Проверка работы

После запуска вы должны увидеть:

1. Логи в консоли с прогрессом анализа
2. Файлы результатов в `data/`
3. Логи в `logs/autonomous_agent_YYYY-MM-DD.log`

## Устранение проблем

### Ошибка "QWEN_API_KEY is required"
- Проверьте, что переменная окружения установлена: `echo $QWEN_API_KEY`
- Или проверьте файл `config/autonomous_agent.json`

### Ошибка подключения к Bybit API
- Проверьте правильность API ключей
- Убедитесь, что ключи имеют необходимые права доступа
- Проверьте доступность интернета

### Ошибка Qwen API
- Проверьте правильность API ключа Alibaba Cloud
- Убедитесь, что у вас есть доступ к Qwen API
- Проверьте баланс на аккаунте Alibaba Cloud

## Следующие шаги

1. ✅ Агент создан и готов к использованию
2. 🔄 Создайте Telegram бота через @BotFather
3. 🔄 Настройте интеграцию бота с агентом
4. 🔄 Разверните в Kubernetes кластере
5. 🔄 Настройте автоматическую публикацию в канал


