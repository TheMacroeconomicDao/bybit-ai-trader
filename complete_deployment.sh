#!/bin/bash
set -e

echo "🚀 Завершение деплоя Trader Agent"
echo ""

# Проверка GITHUB_TOKEN
if [ -z "$GITHUB_TOKEN" ]; then
    echo "❌ ОШИБКА: GITHUB_TOKEN не установлен!"
    echo ""
    echo "Установите токен:"
    echo "  export GITHUB_TOKEN='your_github_token'"
    echo ""
    echo "Или запустите скрипт с токеном:"
    echo "  GITHUB_TOKEN='your_token' ./complete_deployment.sh"
    exit 1
fi

echo "✅ GITHUB_TOKEN найден"
echo ""

# 1. Логин в GitHub Container Registry
echo "🔐 Логин в GitHub Container Registry..."
echo "$GITHUB_TOKEN" | docker login ghcr.io -u TheMacroeconomicDao --password-stdin
echo "✅ Логин успешен"
echo ""

# 2. Push образа
echo "📤 Пуш образа в registry..."
COMMIT_HASH=$(git rev-parse --short HEAD)
docker push ghcr.io/themacroeconomicdao/trader-agent:main
docker push ghcr.io/themacroeconomicdao/trader-agent:latest
docker push ghcr.io/themacroeconomicdao/trader-agent:$COMMIT_HASH
echo "✅ Образ запушен"
echo ""

# 3. Создание imagePullSecret
echo "🔐 Создание imagePullSecret для Kubernetes..."
kubectl create secret docker-registry ghcr-secret \
  --docker-server=ghcr.io \
  --docker-username=TheMacroeconomicDao \
  --docker-password="$GITHUB_TOKEN" \
  -n trader-agent \
  --dry-run=client -o yaml | kubectl apply -f -
echo "✅ imagePullSecret создан"
echo ""

# 4. Обновление CronJob с imagePullSecrets
echo "🔄 Обновление CronJob..."
kubectl patch cronjob trader-agent-analyzer -n trader-agent --type='json' \
  -p='[{"op": "add", "path": "/spec/jobTemplate/spec/template/spec/imagePullSecrets", "value": [{"name": "ghcr-secret"}]}]' 2>/dev/null || \
kubectl patch cronjob trader-agent-analyzer -n trader-agent --type='json' \
  -p='[{"op": "replace", "path": "/spec/jobTemplate/spec/template/spec/imagePullSecrets", "value": [{"name": "ghcr-secret"}]}]'
echo "✅ CronJob обновлен"
echo ""

# 5. Тестовый запуск
echo "🧪 Тестовый запуск Job..."
kubectl delete job -n trader-agent manual-test-* 2>/dev/null || true
kubectl create job --from=cronjob/trader-agent-analyzer manual-test-$(date +%s) -n trader-agent
echo "✅ Тестовый Job создан"
echo ""

# 6. Проверка статуса
echo "⏳ Ожидание запуска Pod (10 секунд)..."
sleep 10

echo ""
echo "📊 Статус Pod:"
kubectl get pods -n trader-agent -l job-name --sort-by=.metadata.creationTimestamp | tail -3

echo ""
echo "📋 Логи (последние 20 строк):"
kubectl logs -n trader-agent -l job-name --tail=20 2>&1 | tail -20 || echo "Логи пока недоступны (Pod еще запускается)"

echo ""
echo "🎉 Деплой завершен!"
echo ""
echo "Для проверки логов:"
echo "  kubectl logs -n trader-agent -l job-name -f"
echo ""
echo "Для проверки статуса CronJob:"
echo "  kubectl get cronjob -n trader-agent"







