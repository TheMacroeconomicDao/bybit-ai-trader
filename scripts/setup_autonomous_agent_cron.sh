#!/bin/bash

# Setup Autonomous Agent Cron Job
# Устанавливает автоматический запуск агента каждые 4 часа

# Определяем путь к проекту автоматически
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
SCRIPT_PATH="$PROJECT_DIR/scripts/run_daily_analysis.sh"

# Цвета
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}🔧 Setting up Autonomous Agent cron job...${NC}"

# Проверка существования скрипта
if [ ! -f "$SCRIPT_PATH" ]; then
    echo -e "${RED}❌ Script not found: $SCRIPT_PATH${NC}"
    exit 1
fi

# Делаем исполняемым
chmod +x "$SCRIPT_PATH"
echo -e "${GREEN}✅ Script permissions set${NC}"

# Расписание (по умолчанию каждые 4 часа)
# Можно изменить: "0 */4 * * *" = каждые 4 часа
# "0 */2 * * *" = каждые 2 часа
# "0 9,13,17,21 * * *" = в 9:00, 13:00, 17:00, 21:00
SCHEDULE="${1:-0 */4 * * *}"

# Создаём временный файл
CRON_TEMP=$(mktemp)

# Получаем текущие cron jobs
crontab -l > "$CRON_TEMP" 2>/dev/null || true

# Удаляем старые задачи для run_daily_analysis.sh
grep -v "run_daily_analysis.sh" "$CRON_TEMP" > "${CRON_TEMP}.new" || true
mv "${CRON_TEMP}.new" "$CRON_TEMP"

# Добавляем новую задачу
echo "# Autonomous Trading Agent - Market Analysis" >> "$CRON_TEMP"
echo "$SCHEDULE $SCRIPT_PATH >> $PROJECT_DIR/logs/cron.log 2>&1" >> "$CRON_TEMP"
echo "" >> "$CRON_TEMP"

# Устанавливаем новый crontab
crontab "$CRON_TEMP"
rm "$CRON_TEMP"

echo -e "${GREEN}✅ Cron job установлен!${NC}"
echo -e "${GREEN}📅 Расписание: $SCHEDULE${NC}"
echo ""
echo "Текущие cron jobs для агента:"
crontab -l | grep -A 1 "Autonomous Trading" || echo "  (не найдено)"
echo ""
echo -e "${YELLOW}📝 Проверить логи: tail -f $PROJECT_DIR/logs/cron.log${NC}"
echo -e "${YELLOW}🔄 Изменить расписание: $0 \"0 */2 * * *\"${NC}"





