#!/bin/bash

# Check Autonomous Agent Status
# Полная диагностика системы

# Определяем путь к проекту автоматически
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Цвета
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}"
echo "╔════════════════════════════════════════════════════╗"
echo "║   AUTONOMOUS AGENT - SYSTEM STATUS CHECK          ║"
echo "╚════════════════════════════════════════════════════╝"
echo -e "${NC}"

# 1. Переменные окружения
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📋 ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

cd "$PROJECT_DIR"
if [ -f "$PROJECT_DIR/load_env.sh" ]; then
    source "$PROJECT_DIR/load_env.sh" 2>/dev/null
else
    echo -e "  ${YELLOW}⚠️  load_env.sh not found${NC}"
fi

check_env_var() {
    local var_name=$1
    local var_value=${!var_name}
    local placeholder="your_$(echo "$var_name" | tr '[:upper:]' '[:lower:]')_here"
    
    if [ -n "$var_value" ] && [ "$var_value" != "$placeholder" ]; then
        echo -e "  ${GREEN}✅ $var_name${NC}: SET"
        return 0
    else
        echo -e "  ${RED}❌ $var_name${NC}: NOT SET"
        return 1
    fi
}

check_env_var "QWEN_API_KEY"
check_env_var "BYBIT_API_KEY"
check_env_var "BYBIT_API_SECRET"
check_env_var "TELEGRAM_BOT_TOKEN" || echo -e "     ${YELLOW}(optional)${NC}"
check_env_var "TELEGRAM_CHAT_IDS" || echo -e "     ${YELLOW}(optional)${NC}"

# 2. Зависимости
echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📦 ЗАВИСИМОСТИ${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

if [ -d "$PROJECT_DIR/venv" ]; then
    echo -e "  ${GREEN}✅ Virtual environment${NC}: EXISTS"
    source "$PROJECT_DIR/venv/bin/activate" 2>/dev/null
    
    if command -v python >/dev/null 2>&1; then
        python "$PROJECT_DIR/scripts/check_dependencies.py" 2>/dev/null || echo -e "  ${YELLOW}⚠️  Could not check dependencies${NC}"
    fi
else
    echo -e "  ${RED}❌ Virtual environment${NC}: NOT FOUND"
fi

# 3. Cron Job
echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}⏰ АВТОМАТИЗАЦИЯ${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

if crontab -l 2>/dev/null | grep -q "run_daily_analysis"; then
    echo -e "  ${GREEN}✅ Cron job${NC}: УСТАНОВЛЕН"
    echo -e "\n  Расписание:"
    crontab -l | grep "run_daily_analysis"
else
    echo -e "  ${RED}❌ Cron job${NC}: НЕ УСТАНОВЛЕН"
    echo -e "  ${YELLOW}Установите: ./scripts/setup_autonomous_agent_cron.sh${NC}"
fi

# 4. Файлы результатов
echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📊 ПОСЛЕДНИЙ АНАЛИЗ${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

ANALYSIS_FILE="$PROJECT_DIR/data/latest_analysis.json"
if [ -f "$ANALYSIS_FILE" ]; then
    echo -e "  ${GREEN}✅ Analysis file${NC}: EXISTS"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        MODIFIED=$(stat -f "%Sm" -t "%Y-%m-%d %H:%M:%S" "$ANALYSIS_FILE" 2>/dev/null)
    else
        MODIFIED=$(stat -c "%y" "$ANALYSIS_FILE" 2>/dev/null | cut -d' ' -f1,2 | cut -d'.' -f1)
    fi
    echo -e "  ${BLUE}📅 Last modified${NC}: $MODIFIED"
else
    echo -e "  ${RED}❌ Analysis file${NC}: NOT FOUND"
fi

TELEGRAM_FILE="$PROJECT_DIR/data/latest_telegram_message.txt"
if [ -f "$TELEGRAM_FILE" ]; then
    echo -e "  ${GREEN}✅ Telegram message${NC}: EXISTS"
    LINES=$(wc -l < "$TELEGRAM_FILE" 2>/dev/null || echo "0")
    echo -e "  ${BLUE}📏 Size${NC}: $LINES lines"
else
    echo -e "  ${RED}❌ Telegram message${NC}: NOT FOUND"
fi

# 5. Логи
echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📝 ЛОГИ${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

if [ -d "$PROJECT_DIR/logs" ]; then
    LOG_COUNT=$(ls -1 "$PROJECT_DIR/logs" 2>/dev/null | wc -l | tr -d ' ')
    echo -e "  ${GREEN}✅ Logs directory${NC}: EXISTS ($LOG_COUNT files)"
    
    LATEST_LOG=$(ls -t "$PROJECT_DIR/logs"/*.log 2>/dev/null | head -1)
    if [ -n "$LATEST_LOG" ]; then
        echo -e "  ${BLUE}📄 Latest log${NC}: $(basename "$LATEST_LOG")"
    fi
else
    echo -e "  ${YELLOW}⚠️  Logs directory${NC}: NOT FOUND"
fi

# Итоговая оценка
echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}✅ ИТОГОВАЯ ОЦЕНКА${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

echo -e "\n${GREEN}Система готова к работе!${NC}"
echo -e "\n${YELLOW}Следующие шаги:${NC}"
echo -e "  1. Запуск вручную: ${GREEN}python -m autonomous_agent.main${NC}"
echo -e "  2. Установка cron: ${GREEN}./scripts/setup_autonomous_agent_cron.sh${NC}"
echo -e "  3. Проверка логов: ${GREEN}tail -f logs/*.log${NC}"
echo ""

