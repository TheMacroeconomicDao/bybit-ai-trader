#!/bin/bash
# 🚀 V3.0.1 Quick Deployment Script
# Автоматический деплой Trader Agent v3.0.1

set -e

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Trader Agent v3.0.1 - Quick Deployment${NC}"
echo ""

# 1. Проверка окружения
echo -e "${YELLOW}📋 Шаг 1: Проверка окружения...${NC}"

# Проверка Docker
if ! docker info >/dev/null 2>&1; then
    echo -e "${RED}❌ Docker не запущен!${NC}"
    echo "Запустите Docker Desktop:"
    echo "  open -a Docker"
    echo ""
    echo "Подождите ~30 секунд и запустите скрипт снова."
    exit 1
fi
echo -e "${GREEN}✅ Docker запущен${NC}"

# Проверка kubectl
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}❌ kubectl не установлен!${NC}"
    exit 1
fi
echo -e "${GREEN}✅ kubectl доступен${NC}"

# Проверка Git статуса
cd /Users/Gyber/GYBERNATY-ECOSYSTEM/TRADER-AGENT
if [ -n "$(git status --porcelain)" ]; then
    echo -e "${YELLOW}⚠️  Есть незакоммиченные изменения${NC}"
    git status --short
    echo ""
    read -p "Продолжить? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "main" ]; then
    echo -e "${YELLOW}⚠️  Текущая ветка: $CURRENT_BRANCH (ожидается main)${NC}"
    read -p "Переключиться на main? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git checkout main
        git pull origin main
    fi
fi
echo -e "${GREEN}✅ Git статус OK${NC}"

# 2. Сборка образа
echo ""
echo -e "${YELLOW}🔨 Шаг 2: Сборка Docker образа...${NC}"
COMMIT_HASH=$(git rev-parse --short HEAD)
echo "Commit: $COMMIT_HASH"

docker build \
  -t ghcr.io/themacroeconomicdao/bybit-ai-trader:main \
  -t ghcr.io/themacroeconomicdao/bybit-ai-trader:latest \
  -t ghcr.io/themacroeconomicdao/bybit-ai-trader:v3.0.1 \
  -t ghcr.io/themacroeconomicdao/bybit-ai-trader:$COMMIT_HASH \
  -f Dockerfile .

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Ошибка сборки образа!${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Образ собран успешно${NC}"

# 3. Push в registry
echo ""
echo -e "${YELLOW}📤 Шаг 3: Push образа в GHCR...${NC}"

# Проверка авторизации
if ! docker info | grep -q "ghcr.io"; then
    echo -e "${YELLOW}🔐 Требуется авторизация в GitHub Container Registry${NC}"
    if [ -z "$GITHUB_TOKEN" ]; then
        echo "Введите GitHub Personal Access Token (или установите GITHUB_TOKEN env):"
        read -rs GITHUB_TOKEN
    fi
    echo "$GITHUB_TOKEN" | docker login ghcr.io -u TheMacroeconomicDao --password-stdin
fi

docker push ghcr.io/themacroeconomicdao/bybit-ai-trader:main
docker push ghcr.io/themacroeconomicdao/bybit-ai-trader:latest
docker push ghcr.io/themacroeconomicdao/bybit-ai-trader:v3.0.1

echo -e "${GREEN}✅ Образ запушен в registry${NC}"

# 4. Deploy в Kubernetes
echo ""
echo -e "${YELLOW}🚀 Шаг 4: Деплой в Kubernetes...${NC}"

# Namespace
echo "Создание namespace..."
kubectl apply -f k8s/namespace.yaml

# ConfigMap
echo "Применение ConfigMap..."
kubectl apply -f k8s/configmap.yaml

# Secrets (проверка)
echo "Проверка Secrets..."
if ! kubectl get secret trader-agent-secrets -n trader-agent &> /dev/null; then
    echo -e "${YELLOW}⚠️  Secret trader-agent-secrets не найден!${NC}"
    echo ""
    echo "Создайте секрет вручную:"
    echo ""
    echo "kubectl create secret generic trader-agent-secrets \\"
    echo "  --from-literal=QWEN_API_KEY=\"your_key\" \\"
    echo "  --from-literal=BYBIT_API_KEY=\"your_key\" \\"
    echo "  --from-literal=BYBIT_API_SECRET=\"your_secret\" \\"
    echo "  --from-literal=TELEGRAM_BOT_TOKEN=\"your_token\" \\"
    echo "  -n trader-agent"
    echo ""
    read -p "Продолжить без секретов? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo -e "${GREEN}✅ Secrets найдены${NC}"
fi

# CronJob
echo "Применение CronJob..."
kubectl apply -f k8s/cronjob.yaml

# Restart для применения нового образа
echo "Перезапуск CronJob для применения нового образа..."
kubectl rollout restart cronjob/trader-agent-analyzer -n trader-agent

echo -e "${GREEN}✅ Деплой завершен${NC}"

# 5. Проверка статуса
echo ""
echo -e "${YELLOW}📊 Шаг 5: Проверка статуса...${NC}"
echo ""
echo "CronJob статус:"
kubectl get cronjob -n trader-agent
echo ""
echo "Последние Jobs:"
kubectl get jobs -n trader-agent --sort-by=.metadata.creationTimestamp | tail -5

# 6. Тестовый запуск
echo ""
read -p "Запустить тестовый Job? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    TEST_JOB_NAME="manual-test-$(date +%s)"
    echo "Создание тестового Job: $TEST_JOB_NAME"
    kubectl create job --from=cronjob/trader-agent-analyzer $TEST_JOB_NAME -n trader-agent
    
    echo ""
    echo "Ожидание запуска (5 секунд)..."
    sleep 5
    
    echo ""
    echo "Логи тестового Job:"
    kubectl logs -n trader-agent job/$TEST_JOB_NAME --tail=50 -f || true
fi

echo ""
echo -e "${GREEN}🎉 Деплой завершен успешно!${NC}"
echo ""
echo "📋 Следующие шаги:"
echo "1. Проверьте логи: kubectl logs -n trader-agent -l job-name --tail=100"
echo "2. Проверьте Telegram каналы через 12 часов"
echo "3. Мониторинг: kubectl get cronjob,jobs -n trader-agent -w"
echo ""
echo "Версия: v3.0.1-fixed"
echo "Commit: $COMMIT_HASH"
