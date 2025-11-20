#!/bin/bash

# Setup Daily Cron Job для Autonomous Agent
# Настраивает автоматический запуск анализа раз в сутки

PROJECT_DIR="/Users/Gyber/GYBERNATY-ECOSYSTEM/TRADER-AGENT"
SCRIPT_PATH="$PROJECT_DIR/scripts/run_daily_analysis.sh"

# Проверяем что скрипт существует
if [ ! -f "$SCRIPT_PATH" ]; then
    echo "Error: Script not found at $SCRIPT_PATH"
    exit 1
fi

# Делаем скрипт исполняемым
chmod +x "$SCRIPT_PATH"

# Время запуска (по умолчанию 09:00 каждый день)
# Можно изменить через аргумент: ./setup_daily_cron.sh 10:00
RUN_TIME="${1:-09:00}"

echo "Setting up daily cron job for Autonomous Agent"
echo "Script: $SCRIPT_PATH"
echo "Run time: $RUN_TIME (daily)"
echo ""

# Создаём временный файл с cron задачей
CRON_TEMP=$(mktemp)
crontab -l > "$CRON_TEMP" 2>/dev/null || true

# Удаляем старую задачу если есть
grep -v "run_daily_analysis.sh" "$CRON_TEMP" > "${CRON_TEMP}.new" || true
mv "${CRON_TEMP}.new" "$CRON_TEMP"

# Добавляем новую задачу
# Формат: minute hour * * * command
# Пример: 0 9 * * * = каждый день в 09:00
HOUR=$(echo "$RUN_TIME" | cut -d: -f1)
MINUTE=$(echo "$RUN_TIME" | cut -d: -f2)

echo "$MINUTE $HOUR * * * $SCRIPT_PATH >> $PROJECT_DIR/logs/cron.log 2>&1" >> "$CRON_TEMP"

# Устанавливаем новый crontab
crontab "$CRON_TEMP"
rm "$CRON_TEMP"

echo "✅ Cron job installed successfully!"
echo ""
echo "Current crontab:"
crontab -l | grep "run_daily_analysis.sh"
echo ""
echo "To view all cron jobs: crontab -l"
echo "To remove this cron job: crontab -e (then delete the line)"

