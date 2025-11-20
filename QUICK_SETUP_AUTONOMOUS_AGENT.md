# 🚀 Быстрая настройка Autonomous Agent

## 1️⃣ Настройка переменных окружения

```bash
# Добавьте в load_env.sh или экспортируйте:
export QWEN_API_KEY="your_key"
export BYBIT_API_KEY="your_key"
export BYBIT_API_SECRET="your_secret"
export TELEGRAM_BOT_TOKEN="your_token"  # Опционально
export TELEGRAM_CHAT_IDS="chat_id1,chat_id2"  # Опционально
```

## 2️⃣ Тестирование

```bash
# Активируйте venv
source venv/bin/activate

# Запустите тесты
python scripts/test_autonomous_agent.py
```

## 3️⃣ Ручной запуск анализа

```bash
# Активируйте venv
source venv/bin/activate

# Запустите анализ
python -m autonomous_agent.main
```

## 4️⃣ Настройка ежедневной публикации (раз в сутки)

```bash
# Настроить cron job (по умолчанию в 09:00)
./scripts/setup_daily_cron.sh

# Или указать своё время (например, 10:30)
./scripts/setup_daily_cron.sh 10:30

# Проверить что cron job установлен
crontab -l | grep run_daily_analysis
```

## 5️⃣ Проверка работы

```bash
# Проверить последний анализ
cat data/latest_analysis.json | jq '.timestamp'

# Проверить логи
tail -f logs/daily_analysis_$(date +%Y%m%d).log
```

## ✅ Готово!

Теперь анализ будет запускаться автоматически каждый день в указанное время и публиковаться в Telegram.

---

**Подробная документация:** [AUTONOMOUS_AGENT_SETUP.md](AUTONOMOUS_AGENT_SETUP.md)

