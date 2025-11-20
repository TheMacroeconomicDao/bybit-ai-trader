#!/bin/bash
# Скрипт для деплоя Autonomous Agent в Kubernetes

set -e

echo "🚀 Деплой Autonomous Agent в Kubernetes"
echo "========================================"

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Проверка окружения
echo -e "${YELLOW}📋 Проверка окружения...${NC}"

# Проверка kubectl
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}❌ kubectl не найден. Установите kubectl.${NC}"
    exit 1
fi

# Проверка docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ docker не найден. Установите Docker.${NC}"
    exit 1
fi

# Проверка подключения к кластеру
if ! kubectl cluster-info &> /dev/null; then
    echo -e "${RED}❌ Не удалось подключиться к Kubernetes кластеру.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Окружение готово${NC}"

# Переход в директорию проекта
cd "$(dirname "$0")"

# Проверка ветки
CURRENT_BRANCH=$(git branch --show-current)
echo -e "${YELLOW}📌 Текущая ветка: ${CURRENT_BRANCH}${NC}"

if [ "$CURRENT_BRANCH" != "main" ]; then
    echo -e "${YELLOW}⚠️  Внимание: вы не в ветке main. Продолжить? (y/n)${NC}"
    read -r response
    if [ "$response" != "y" ]; then
        exit 1
    fi
fi

# Шаг 1: Сборка образа
echo -e "\n${YELLOW}📦 Шаг 1: Сборка Docker образа...${NC}"
IMAGE_TAG="ghcr.io/themacroeconomicdao/trader-agent:main"
LATEST_TAG="ghcr.io/themacroeconomicdao/trader-agent:latest"
COMMIT_TAG="ghcr.io/themacroeconomicdao/trader-agent:$(git rev-parse --short HEAD)"

docker build \
  -t "$IMAGE_TAG" \
  -t "$LATEST_TAG" \
  -t "$COMMIT_TAG" \
  -f Dockerfile .

echo -e "${GREEN}✅ Образ собран${NC}"

# Шаг 2: Push в registry
echo -e "\n${YELLOW}📤 Шаг 2: Push образа в registry...${NC}"

# Проверка авторизации в GitHub Container Registry
if ! docker images | grep -q "ghcr.io/themacroeconomicdao/trader-agent"; then
    echo -e "${RED}❌ Образ не найден. Проверьте сборку.${NC}"
    exit 1
fi

# Логин в GHCR (если не залогинен)
if ! docker info | grep -q "ghcr.io"; then
    echo -e "${YELLOW}🔐 Требуется авторизация в GitHub Container Registry${NC}"
    echo "Введите GitHub Personal Access Token:"
    read -rs GITHUB_TOKEN
    echo "$GITHUB_TOKEN" | docker login ghcr.io -u TheMacroeconomicDao --password-stdin
fi

docker push "$IMAGE_TAG"
docker push "$LATEST_TAG"
docker push "$COMMIT_TAG"

echo -e "${GREEN}✅ Образ загружен в registry${NC}"

# Шаг 3: Применение манифестов
echo -e "\n${YELLOW}🚀 Шаг 3: Деплой в Kubernetes...${NC}"

# Namespace
echo "Создание namespace..."
kubectl apply -f k8s/namespace.yaml

# ConfigMap
echo "Применение ConfigMap..."
kubectl apply -f k8s/configmap.yaml

# Secrets (проверка что секреты созданы)
echo "Проверка Secrets..."
if ! kubectl get secret trader-agent-secrets -n trader-agent &> /dev/null; then
    echo -e "${YELLOW}⚠️  Secret trader-agent-secrets не найден.${NC}"
    echo "Создайте секрет вручную:"
    echo "kubectl create secret generic trader-agent-secrets \\"
    echo "  --from-literal=QWEN_API_KEY=\"your_key\" \\"
    echo "  --from-literal=BYBIT_API_KEY=\"your_key\" \\"
    echo "  --from-literal=BYBIT_API_SECRET=\"your_secret\" \\"
    echo "  --from-literal=TELEGRAM_BOT_TOKEN=\"your_token\" \\"
    echo "  -n trader-agent"
    echo ""
    echo "Продолжить без секретов? (y/n)"
    read -r response
    if [ "$response" != "y" ]; then
        exit 1
    fi
fi

# CronJob
echo "Применение CronJob..."
kubectl apply -f k8s/cronjob.yaml

echo -e "${GREEN}✅ Деплой завершен${NC}"

# Шаг 4: Проверка статуса
echo -e "\n${YELLOW}📊 Шаг 4: Проверка статуса...${NC}"

echo "CronJob:"
kubectl get cronjob -n trader-agent

echo ""
echo "Последние Jobs:"
kubectl get jobs -n trader-agent --sort-by=.metadata.creationTimestamp | tail -5

echo ""
echo -e "${GREEN}✅ Деплой успешно завершен!${NC}"
echo ""
echo "Для тестирования запустите Job вручную:"
echo "kubectl create job --from=cronjob/trader-agent-analyzer manual-test-\$(date +%s) -n trader-agent"
echo ""
echo "Для просмотра логов:"
echo "kubectl logs -n trader-agent -l app=trader-agent --tail=100 -f"
