# ⚡ БЫСТРОЕ ИСПРАВЛЕНИЕ AUTONOMOUS AGENT

**Время выполнения:** ~15-20 минут  
**Приоритет:** 🔴 КРИТИЧЕСКИЙ

Это краткая инструкция для быстрого исправления критических проблем безопасности.  
**Полный отчет:** [`AUTONOMOUS_AGENT_FULL_AUDIT_REPORT.md`](./AUTONOMOUS_AGENT_FULL_AUDIT_REPORT.md)

---

## 🚨 ШАГ 1: SECURITY - Деактивировать Скомпрометированные Ключи

### 1.1 Qwen API ключ (НЕМЕДЛЕННО!)

**Проблема:** Реальный API ключ в `config/autonomous_agent.json.example` строка 2

```bash
# Откройте OpenRouter
open https://openrouter.ai/keys

# Деактивируйте ключ: sk-6f5319fb244f4f9faa1595825cf87a05
# Создайте новый ключ
```

### 1.2 Обновите .env с новым ключом

```bash
# Откройте .env
nano .env

# Обновите строку (ИСПОЛЬЗУЙТЕ НОВЫЙ КЛЮЧ!):
QWEN_API_KEY=sk-or-v1-ВАШИ_НОВЫЙ_КЛЮЧ_ЗДЕСЬ
```

---

## 🔒 ШАГ 2: Исправить publish_market_analysis.py

### 2.1 Создать бэкап

```bash
cp publish_market_analysis.py publish_market_analysis.py.backup
```

### 2.2 Применить исправления

Откройте [`publish_market_analysis.py`](./publish_market_analysis.py) и примените следующие изменения:

**В НАЧАЛЕ ФАЙЛА (после импортов):**

```python
import os
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()
```

**ЗАМЕНИТЬ строки 23-27:**

```python
# СТАРЫЙ КОД (УДАЛИТЬ):
# scan_files = [
#     '/Users/Gyber/.cursor/projects/...',
#     ...
# ]

# НОВЫЙ КОД:
from pathlib import Path

# Используем относительный путь от проекта
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"

# Читаем последние 3 файла результатов сканирования
scan_files = sorted(
    DATA_DIR.glob("scan_results_*.json"),
    key=lambda p: p.stat().st_mtime,
    reverse=True
)[:3]  # Последние 3 файла
```

**ЗАМЕНИТЬ строки 177-181:**

```python
# СТАРЫЙ КОД (УДАЛИТЬ - НЕБЕЗОПАСНО!):
# BOT_TOKEN = "8003689195:AAGxQsopKvlLS34H2TZ0S1a0K7s4yV4iOBY"
# DEFAULT_CHANNELS = [
#     "-1003382613825",
#     "-1003484839912",
# ]

# НОВЫЙ КОД:
# Telegram bot configuration from environment
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
DEFAULT_CHANNELS_STR = os.getenv("TELEGRAM_CHAT_IDS", "")

if not BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")

if not DEFAULT_CHANNELS_STR:
    raise ValueError("TELEGRAM_CHAT_IDS environment variable is required")

# Parse chat IDs from comma-separated string
DEFAULT_CHANNELS = [
    cid.strip() for cid in DEFAULT_CHANNELS_STR.split(",") 
    if cid.strip()
]

if not DEFAULT_CHANNELS:
    raise ValueError("No valid chat IDs found in TELEGRAM_CHAT_IDS")
```

### 2.3 Проверить изменения

```bash
# Проверить что credentials удалены
grep -n "8003689195" publish_market_analysis.py
# Должен вернуть: (empty)

grep -n "1003382613825" publish_market_analysis.py
# Должен вернуть: (empty)
```

---

## 📝 ШАГ 3: Обновить .env

```bash
# Откройте .env
nano .env

# Убедитесь что есть эти строки:
TELEGRAM_BOT_TOKEN=8003689195:AAGxQsopKvlLS34H2TZ0S1a0K7s4yV4iOBY
TELEGRAM_CHAT_IDS=-1003382613825,-1003484839912

# Сохраните и закройте (Ctrl+O, Enter, Ctrl+X)
```

---

## 🔧 ШАГ 4: Исправить Example Файлы

### 4.1 Исправить config/autonomous_agent.json.example

```bash
nano config/autonomous_agent.json.example
```

Замените содержимое на:

```json
{
  "qwen_api_key": "your_qwen_openrouter_api_key_here",
  "bybit_api_key": "your_bybit_api_key_here",
  "bybit_api_secret": "your_bybit_api_secret_here",
  "qwen_model": "qwen/qwen-turbo",
  "testnet": false,
  "comment": "⚠️ НИКОГДА НЕ КОММИТЬТЕ РЕАЛЬНЫЕ КЛЮЧИ! Скопируйте в autonomous_agent.json и заполните реальными значениями"
}
```

### 4.2 Обновить .env.example

```bash
nano .env.example
```

Замените строку 27:

```bash
# СТАРОЕ:
# TELEGRAM_CHAT_ID=your_chat_id_here

# НОВОЕ:
# ⚠️ Несколько каналов через запятую: -1001234567890,-1009876543210
TELEGRAM_CHAT_IDS=your_chat_id_1,your_chat_id_2
```

---

## ✅ ШАГ 5: Тестирование

### 5.1 Проверить что .env загружается

```bash
source load_env.sh
```

**Ожидаемый результат:**
```
✅ Все переменные загружены успешно!
```

### 5.2 Создать тестовые данные

```bash
mkdir -p data

# Создать тестовый файл результатов
cat > data/scan_results_test.json << 'EOF'
[{
  "symbol": "BTC/USDT",
  "score": 8.5,
  "probability": 0.75,
  "current_price": 50000,
  "change_24h": 2.5,
  "entry_plan": {
    "side": "long",
    "entry_price": 50000,
    "stop_loss": 49500,
    "take_profit": 51000,
    "risk_reward": 2.0
  }
}]
EOF
```

### 5.3 Тестовый запуск публикации (DRY RUN)

```bash
source venv/bin/activate
python -c "
import os
from dotenv import load_dotenv
load_dotenv()

print('Testing environment variables...')
print(f'TELEGRAM_BOT_TOKEN: {\"✅ SET\" if os.getenv(\"TELEGRAM_BOT_TOKEN\") else \"❌ NOT SET\"}')
print(f'TELEGRAM_CHAT_IDS: {os.getenv(\"TELEGRAM_CHAT_IDS\", \"❌ NOT SET\")}')
print(f'QWEN_API_KEY: {\"✅ SET\" if os.getenv(\"QWEN_API_KEY\") else \"❌ NOT SET\"}')
"
```

**Ожидаемый результат:**
```
Testing environment variables...
TELEGRAM_BOT_TOKEN: ✅ SET
TELEGRAM_CHAT_IDS: -1003382613825,-1003484839912
QWEN_API_KEY: ✅ SET
```

### 5.4 Запуск агента

```bash
source venv/bin/activate
source load_env.sh
python -m autonomous_agent.main
```

**Ожидаемый результат:**
```
Starting Autonomous Trading Agent
Configuration loaded: Qwen model=qwen/qwen-turbo
...
Analysis completed successfully
```

---

## 🔍 ШАГ 6: Проверка Безопасности

```bash
# 1. Проверить что .env НЕ в Git
cat .gitignore | grep "^\.env$"
# Должно вернуть: .env

# 2. Проверить что credentials удалены из кода
grep -r "8003689195" --exclude-dir=.git --exclude="*.backup" .
# Должно вернуть: (empty) или только в .env

grep -r "sk-6f5319fb244f4f9faa1595825cf87a05" --exclude-dir=.git .
# Должно вернуть: (empty)

# 3. Проверить Git status
git status
# .env НЕ должен быть в списке изменений
```

---

## 📋 ЧЕКЛИСТ БЫСТРОГО ИСПРАВЛЕНИЯ

- [ ] ✅ Деактивирован старый Qwen API ключ в OpenRouter
- [ ] ✅ Создан новый Qwen API ключ
- [ ] ✅ Обновлен `.env` с новым ключом
- [ ] ✅ Удалены Telegram credentials из `publish_market_analysis.py`
- [ ] ✅ Добавлена загрузка credentials из `.env`
- [ ] ✅ Исправлены хардкод пути в `publish_market_analysis.py`
- [ ] ✅ Исправлен `config/autonomous_agent.json.example`
- [ ] ✅ Обновлен `.env.example` (TELEGRAM_CHAT_IDS)
- [ ] ✅ Протестирована загрузка `.env`
- [ ] ✅ Протестирован запуск агента
- [ ] ✅ Проверено что credentials не в Git

---

## 🚀 СЛЕДУЮЩИЕ ШАГИ

После выполнения критических исправлений:

### 1. Установить автоматизацию (опционально)

```bash
# Создать скрипт установки cron
cat > scripts/setup_autonomous_agent_cron.sh << 'EOF'
#!/bin/bash
PROJECT_DIR="/Users/Gyber/GYBERNATY-ECOSYSTEM/TRADER-AGENT"
SCRIPT_PATH="$PROJECT_DIR/scripts/run_daily_analysis.sh"

chmod +x "$SCRIPT_PATH"
SCHEDULE="${1:-0 */4 * * *}"

CRON_TEMP=$(mktemp)
crontab -l > "$CRON_TEMP" 2>/dev/null || true
grep -v "run_daily_analysis.sh" "$CRON_TEMP" > "${CRON_TEMP}.new" || true
mv "${CRON_TEMP}.new" "$CRON_TEMP"

echo "# Autonomous Trading Agent - Market Analysis" >> "$CRON_TEMP"
echo "$SCHEDULE $SCRIPT_PATH >> $PROJECT_DIR/logs/cron.log 2>&1" >> "$CRON_TEMP"

crontab "$CRON_TEMP"
rm "$CRON_TEMP"

echo "✅ Cron job установлен! Расписание: $SCHEDULE"
EOF

chmod +x scripts/setup_autonomous_agent_cron.sh
./scripts/setup_autonomous_agent_cron.sh
```

### 2. Создать скрипт проверки статуса

```bash
# Быстрая проверка работы системы
./scripts/check_agent_status.sh  # Если создан из полного отчёта
```

### 3. Коммит изменений (ПОСЛЕ проверки безопасности!)

```bash
# Убедитесь что .env НЕ в коммите!
git status

# Должны быть только:
git add publish_market_analysis.py
git add config/autonomous_agent.json.example
git add .env.example
git add scripts/setup_autonomous_agent_cron.sh

git commit -m "🔒 Security: Remove hardcoded credentials, fix paths, add env loading"
git push
```

---

## ⚠️ ВАЖНЫЕ НАПОМИНАНИЯ

1. **НИКОГДА** не коммитьте `.env` в Git
2. **ВСЕГДА** используйте placeholders в example файлах
3. **ПРОВЕРЯЙТЕ** `git status` перед коммитом
4. **РОТИРУЙТЕ** API ключи, если они были скомпрометированы
5. **ЛОГИРУЙТЕ** все операции для отладки

---

## 🆘 Если что-то пошло не так

### Откатить изменения

```bash
# Если есть backup
cp publish_market_analysis.py.backup publish_market_analysis.py

# Проверить логи
tail -f logs/*.log
```

### Проверить переменные окружения

```bash
source load_env.sh
env | grep -E "QWEN|BYBIT|TELEGRAM"
```

### Связаться с поддержкой

См. полный отчёт: [`AUTONOMOUS_AGENT_FULL_AUDIT_REPORT.md`](./AUTONOMOUS_AGENT_FULL_AUDIT_REPORT.md)

---

**Время создания:** 2025-11-20  
**Статус:** READY TO FIX  
**Приоритет:** 🔴 МАКСИМАЛЬНЫЙ