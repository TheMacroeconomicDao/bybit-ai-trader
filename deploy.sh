#!/bin/bash
# Скрипт для развёртывания Trader Agent в Kubernetes

set -e

echo "🚀 Развёртывание Trader Agent"
echo "================================"

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Проверка наличия kubectl
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}❌ kubectl не найден. Установите kubectl.${NC}"
    exit 1
fi

# Проверка подключения к кластеру
if ! kubectl cluster-info &> /dev/null; then
    echo -e "${RED}❌ Не удалось подключиться к Kubernetes кластеру${NC}"
    echo "   Проверьте что kubectl настроен правильно"
    exit 1
fi

echo -e "${GREEN}✅ kubectl настроен${NC}"

# Переменные
NAMESPACE="trader-agent"
QWEN_API_KEY="${QWEN_API_KEY:-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}"
BYBIT_API_KEY="${BYBIT_API_KEY:-}"
BYBIT_API_SECRET="${BYBIT_API_SECRET:-}"
TELEGRAM_BOT_TOKEN="${TELEGRAM_BOT_TOKEN:-8003689195:AAGxQsopKvlLS34H2TZ0S1a0K7s4yV4iOBY}"

# Проверка обязательных переменных
if [ -z "$BYBIT_API_KEY" ] || [ -z "$BYBIT_API_SECRET" ]; then
    echo -e "${YELLOW}⚠️  BYBIT_API_KEY или BYBIT_API_SECRET не установлены${NC}"
    echo "   Установите через: export BYBIT_API_KEY='...' export BYBIT_API_SECRET='...'"
    echo "   Или обновите значения в этом скрипте"
    read -p "Продолжить без Bybit ключей? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""
echo "📋 Параметры развёртывания:"
echo "   Namespace: $NAMESPACE"
echo "   Qwen Model: qwen/qwen-turbo (OpenRouter)"
echo ""

# ШАГ 1: Создание namespace
echo "📦 ШАГ 1: Создание namespace..."
kubectl apply -f k8s/namespace.yaml
echo -e "${GREEN}✅ Namespace создан${NC}"

# ШАГ 2: Применение ConfigMap
echo ""
echo "⚙️  ШАГ 2: Применение ConfigMap..."
kubectl apply -f k8s/configmap.yaml
echo -e "${GREEN}✅ ConfigMap применён${NC}"

# ШАГ 3: Создание Secrets
echo ""
echo "🔐 ШАГ 3: Создание Secrets..."
kubectl create secret generic trader-agent-secrets \
  --from-literal=QWEN_API_KEY="$QWEN_API_KEY" \
  --from-literal=BYBIT_API_KEY="${BYBIT_API_KEY:-dummy}" \
  --from-literal=BYBIT_API_SECRET="${BYBIT_API_SECRET:-dummy}" \
  --from-literal=TELEGRAM_BOT_TOKEN="$TELEGRAM_BOT_TOKEN" \
  -n "$NAMESPACE" \
  --dry-run=client -o yaml | kubectl apply -f -
echo -e "${GREEN}✅ Secrets созданы${NC}"

# ШАГ 4: Применение CronJob
echo ""
echo "⏰ ШАГ 4: Применение CronJob..."
kubectl apply -f k8s/cronjob.yaml
echo -e "${GREEN}✅ CronJob применён${NC}"

# ШАГ 5: Проверка статуса
echo ""
echo "📊 ШАГ 5: Проверка статуса..."
echo ""
echo "CronJob статус:"
kubectl get cronjob -n "$NAMESPACE"
echo ""
echo "Последние Jobs:"
kubectl get jobs -n "$NAMESPACE" --sort-by=.metadata.creationTimestamp | tail -5

echo ""
echo -e "${GREEN}✅ Развёртывание завершено!${NC}"
echo ""
echo "📋 Полезные команды:"
echo "   Проверить CronJob: kubectl get cronjob -n $NAMESPACE"
echo "   Посмотреть Jobs: kubectl get jobs -n $NAMESPACE"
echo "   Логи: kubectl logs -n $NAMESPACE -l app=trader-agent -f"
echo "   Ручной запуск: kubectl create job --from=cronjob/trader-agent-analyzer trader-agent-test-\$(date +%s) -n $NAMESPACE"
echo ""


