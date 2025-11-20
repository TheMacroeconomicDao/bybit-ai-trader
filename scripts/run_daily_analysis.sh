#!/bin/bash

# Daily Autonomous Agent Analysis Script
# Запускает анализ рынка и публикует результаты в Telegram раз в сутки

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Путь к проекту
PROJECT_DIR="/Users/Gyber/GYBERNATY-ECOSYSTEM/TRADER-AGENT"
LOG_DIR="$PROJECT_DIR/logs"
LOG_FILE="$LOG_DIR/daily_analysis_$(date +%Y%m%d).log"

# Создаём директорию для логов если не существует
mkdir -p "$LOG_DIR"

# Функция логирования
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}" | tee -a "$LOG_FILE"
}

# Начало выполнения
log "=========================================="
log "Starting Daily Autonomous Agent Analysis"
log "=========================================="

# Переход в директорию проекта
cd "$PROJECT_DIR" || {
    log_error "Failed to change directory to $PROJECT_DIR"
    exit 1
}

# Загрузка переменных окружения
if [ -f "$PROJECT_DIR/load_env.sh" ]; then
    source "$PROJECT_DIR/load_env.sh"
    log "Environment variables loaded"
else
    log_warning "load_env.sh not found, using system environment variables"
fi

# Проверка обязательных переменных окружения
if [ -z "$QWEN_API_KEY" ]; then
    log_error "QWEN_API_KEY is not set"
    exit 1
fi

if [ -z "$BYBIT_API_KEY" ]; then
    log_error "BYBIT_API_KEY is not set"
    exit 1
fi

if [ -z "$BYBIT_API_SECRET" ]; then
    log_error "BYBIT_API_SECRET is not set"
    exit 1
fi

# Проверка Telegram credentials (опционально, но предупреждаем если нет)
if [ -z "$TELEGRAM_BOT_TOKEN" ] || [ -z "$TELEGRAM_CHAT_IDS" ]; then
    log_warning "TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_IDS not set - analysis will run but won't be published to Telegram"
fi

# Активация виртуального окружения
if [ -d "$PROJECT_DIR/venv" ]; then
    source "$PROJECT_DIR/venv/bin/activate"
    log "Virtual environment activated"
else
    log_error "Virtual environment not found at $PROJECT_DIR/venv"
    exit 1
fi

# Запуск анализа с автоматической публикацией в Telegram
log "Starting market analysis..."
python -m autonomous_agent.main

# Проверка результата
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    log_success "Analysis completed successfully"
    
    # Проверяем что файл с результатами создан
    ANALYSIS_FILE="$PROJECT_DIR/data/latest_analysis.json"
    if [ -f "$ANALYSIS_FILE" ]; then
        log_success "Analysis results saved to $ANALYSIS_FILE"
    else
        log_warning "Analysis results file not found at $ANALYSIS_FILE"
    fi
    
    # Проверяем что Telegram сообщение создано
    TELEGRAM_FILE="$PROJECT_DIR/data/latest_telegram_message.txt"
    if [ -f "$TELEGRAM_FILE" ]; then
        log_success "Telegram message saved to $TELEGRAM_FILE"
    fi
else
    log_error "Analysis failed with exit code $EXIT_CODE"
    exit $EXIT_CODE
fi

log "=========================================="
log "Daily Analysis Script Completed"
log "=========================================="

exit 0

