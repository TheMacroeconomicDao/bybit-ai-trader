# Kubernetes Manifests для Trader Agent

## Структура

- `namespace.yaml` - Namespace для приложения
- `configmap.yaml` - Конфигурация приложения
- `secrets.yaml` - Шаблон для секретов (заполняется через GitHub Actions)
- `cronjob.yaml` - CronJob для автоматического анализа каждые 30 минут

## Использование

### Ручной деплой:

```bash
# 1. Создать namespace
kubectl apply -f namespace.yaml

# 2. Создать ConfigMap
kubectl apply -f configmap.yaml

# 3. Создать Secrets вручную
kubectl create secret generic trader-agent-secrets \
  --from-literal=QWEN_API_KEY="sk-6f5319fb244f4f9faa1595825cf87a05" \
  --from-literal=BYBIT_API_KEY="your_bybit_api_key" \
  --from-literal=BYBIT_API_SECRET="your_bybit_api_secret" \
  --from-literal=TELEGRAM_BOT_TOKEN="8003689195:AAGxQsopKvlLS34H2TZ0S1a0K7s4yV4iOBY" \
  -n trader-agent

# 4. Создать CronJob
kubectl apply -f cronjob.yaml
```

### Автоматический деплой через GitHub Actions:

GitHub Actions workflow автоматически:
1. Собирает Docker образ
2. Пушит в GHCR
3. Обновляет секреты из GitHub Secrets
4. Деплоит CronJob

## Проверка

```bash
# Проверить CronJob
kubectl get cronjob -n trader-agent

# Проверить последние Job
kubectl get jobs -n trader-agent

# Проверить логи
kubectl logs -n trader-agent -l app=trader-agent --tail=100

# Ручной запуск для тестирования
kubectl create job --from=cronjob/trader-agent-analyzer manual-test-$(date +%s) -n trader-agent
```

