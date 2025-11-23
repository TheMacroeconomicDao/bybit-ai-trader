# Развертывание фильтрации стабильных пар

## Изменения

1. **Фильтрация СТЕЙБЛ/СТЕЙБЛ пар** - исключены из финального отчёта:
   - `autonomous_agent/detailed_formatter.py` - добавлена функция `_is_stable_stable_pair()`
   - `publish_market_analysis.py` - добавлена фильтрация перед форматированием

2. **Частота сканирования** - изменена с 4 раз в сутки на 2 раза:
   - `k8s/cronjob.yaml` - schedule: `"0 */12 * * *"` (каждые 12 часов)
   - Обновлен текст в отчётах: "Monitoring every 12 hours (2 times per day)"

## Развертывание

### Шаг 1: Сборка Docker образа

```bash
cd /Users/Gyber/GYBERNATY-ECOSYSTEM/TRADER-AGENT
COMMIT_HASH=$(git rev-parse --short HEAD)

# Сборка образа
docker build -t ghcr.io/themacroeconomicdao/bybit-ai-trader:main \
             -t ghcr.io/themacroeconomicdao/bybit-ai-trader:latest \
             -t ghcr.io/themacroeconomicdao/bybit-ai-trader:$COMMIT_HASH \
             -f Dockerfile .
```

### Шаг 2: Push в registry (если нужно)

```bash
# Если GITHUB_TOKEN установлен
echo "$GITHUB_TOKEN" | docker login ghcr.io -u TheMacroeconomicDao --password-stdin
docker push ghcr.io/themacroeconomicdao/bybit-ai-trader:main
docker push ghcr.io/themacroeconomicdao/bybit-ai-trader:latest
```

### Шаг 3: Обновление CronJob в Kubernetes

```bash
# Применение обновленного CronJob
kubectl apply -f k8s/cronjob.yaml

# Проверка schedule
kubectl get cronjob trader-agent-analyzer -n trader-agent -o jsonpath='{.spec.schedule}'
# Должно быть: 0 */12 * * *
```

### Шаг 4: Тестовый запуск

```bash
# Создание тестового Job
kubectl create job --from=cronjob/trader-agent-analyzer test-stable-filter-$(date +%s) -n trader-agent

# Проверка статуса
kubectl get jobs -n trader-agent --sort-by=.metadata.creationTimestamp | tail -1

# Просмотр логов
POD_NAME=$(kubectl get pods -n trader-agent -l job-name --sort-by=.metadata.creationTimestamp -o jsonpath='{.items[-1].metadata.name}')
kubectl logs -n trader-agent $POD_NAME --tail=50
```

## Проверка результатов

После запуска проверьте:

1. **В отчёте НЕТ пар СТЕЙБЛ/СТЕЙБЛ:**
   - ❌ USDC/USDT
   - ❌ BUSD/USDT
   - ❌ USDT/TRY
   - ❌ USDT/BRL

2. **В отчёте ЕСТЬ пары КРИПТА/СТЕЙБЛ:**
   - ✅ BTC/USDT
   - ✅ ETH/USDT
   - ✅ SOL/USDT

3. **Частота сканирования:**
   - CronJob запускается каждые 12 часов (2 раза в сутки)
   - В отчёте указано: "Monitoring every 12 hours (2 times per day)"

## Откат (если нужно)

```bash
# Откат к предыдущей версии образа
kubectl set image cronjob/trader-agent-analyzer trader-agent=ghcr.io/themacroeconomicdao/bybit-ai-trader:previous-tag -n trader-agent

# Или восстановить schedule
kubectl patch cronjob trader-agent-analyzer -n trader-agent --type='json' -p='[{"op": "replace", "path": "/spec/schedule", "value": "0 */4 * * *"}]'
```
