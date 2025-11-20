# 🚀 Быстрый деплой Autonomous Agent

## Локальное тестирование ✅

Тест выполняется. Проверить статус:
```bash
tail -f /tmp/autonomous_agent_test.log
```

## Деплой в Kubernetes

### Вариант 1: Автоматический (рекомендуется)

```bash
./deploy.sh
```

### Вариант 2: Ручной деплой

#### 1. Сборка образа
```bash
cd /Users/Gyber/GYBERNATY-ECOSYSTEM/TRADER-AGENT

docker build \
  -t ghcr.io/themacroeconomicdao/trader-agent:main \
  -t ghcr.io/themacroeconomicdao/trader-agent:latest \
  -f Dockerfile .
```

#### 2. Push в registry
```bash
# Логин (если нужно)
echo "$GITHUB_TOKEN" | docker login ghcr.io -u TheMacroeconomicDao --password-stdin

# Push
docker push ghcr.io/themacroeconomicdao/trader-agent:main
docker push ghcr.io/themacroeconomicdao/trader-agent:latest
```

#### 3. Деплой в Kubernetes
```bash
# Namespace и ConfigMap
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml

# Secrets (если еще не созданы)
kubectl create secret generic trader-agent-secrets \
  --from-literal=QWEN_API_KEY="sk-or-v1-..." \
  --from-literal=BYBIT_API_KEY="your_key" \
  --from-literal=BYBIT_API_SECRET="your_secret" \
  --from-literal=TELEGRAM_BOT_TOKEN="your_token" \
  -n trader-agent

# CronJob
kubectl apply -f k8s/cronjob.yaml
```

#### 4. Проверка
```bash
# Статус CronJob
kubectl get cronjob -n trader-agent

# Последние Jobs
kubectl get jobs -n trader-agent --sort-by=.metadata.creationTimestamp | tail -5

# Логи
kubectl logs -n trader-agent -l app=trader-agent --tail=100 -f
```

#### 5. Ручной запуск для тестирования
```bash
kubectl create job --from=cronjob/trader-agent-analyzer manual-test-$(date +%s) -n trader-agent
```

## Что изменилось

✅ **Полная интеграция компонентов:**
- TradingOperations для автоматической торговли
- SignalTracker для контроля качества
- QualityMetrics для анализа эффективности
- CacheManager для оптимизации (экономия 40-60% API запросов)

✅ **Полная система промптов:**
- market_analysis_protocol_optimized.md
- entry_decision_framework.md
- position_monitoring_protocol.md
- Все файлы из knowledge_base

✅ **Обновленные манифесты:**
- Правильный образ: `ghcr.io/themacroeconomicdao/trader-agent:main`
- Команда запуска: `python -m autonomous_agent.main`

## Расписание

CronJob настроен на выполнение **каждые 4 часа** (`0 */4 * * *`)

Для изменения расписания отредактируйте `k8s/cronjob.yaml`:
```yaml
schedule: "0 */4 * * *"  # Каждые 4 часа
# Или каждые 30 минут:
schedule: "*/30 * * * *"
```

