#!/bin/bash

# ====================================
# Load Environment Variables Script
# ====================================
# Использование: source load_env.sh
# ====================================

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🔐 Загрузка переменных окружения...${NC}"

# Проверка наличия .env файла
if [ ! -f .env ]; then
    echo -e "${RED}❌ Файл .env не найден!${NC}"
    echo -e "${YELLOW}📋 Создайте его из .env.example:${NC}"
    echo -e "   ${GREEN}cp .env.example .env${NC}"
    echo -e "   ${GREEN}nano .env${NC}  # или используйте ваш редактор"
    return 1
fi

# Загрузка переменных из .env
set -a
source .env
set +a

# Проверка критических переменных
MISSING_VARS=()

if [ -z "$BYBIT_API_KEY" ] || [ "$BYBIT_API_KEY" == "your_bybit_api_key_here" ]; then
    MISSING_VARS+=("BYBIT_API_KEY")
fi

if [ -z "$BYBIT_API_SECRET" ] || [ "$BYBIT_API_SECRET" == "your_bybit_api_secret_here" ]; then
    MISSING_VARS+=("BYBIT_API_SECRET")
fi

if [ -z "$QWEN_API_KEY" ] || [ "$QWEN_API_KEY" == "your_qwen_api_key_here" ]; then
    MISSING_VARS+=("QWEN_API_KEY")
fi

# Вывод результатов
if [ ${#MISSING_VARS[@]} -eq 0 ]; then
    echo -e "${GREEN}✅ Все переменные загружены успешно!${NC}"
    echo ""
    echo -e "${GREEN}📊 Загруженные переменные:${NC}"
    echo -e "   BYBIT_API_KEY: ${BYBIT_API_KEY:0:10}..."
    echo -e "   BYBIT_API_SECRET: ${BYBIT_API_SECRET:0:10}..."
    echo -e "   BYBIT_TESTNET: $BYBIT_TESTNET"
    echo -e "   QWEN_API_KEY: ${QWEN_API_KEY:0:10}..."
    echo -e "   QWEN_MODEL: $QWEN_MODEL"
    echo ""
    echo -e "${GREEN}✅ Готово! Можно запускать приложение.${NC}"
else
    echo -e "${RED}❌ Не заполнены следующие переменные:${NC}"
    for var in "${MISSING_VARS[@]}"; do
        echo -e "   ${YELLOW}- $var${NC}"
    done
    echo ""
    echo -e "${YELLOW}📝 Отредактируйте .env и заполните реальные значения.${NC}"
    return 1
fi