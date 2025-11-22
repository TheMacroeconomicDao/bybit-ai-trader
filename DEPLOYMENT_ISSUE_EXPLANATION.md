# 🔍 Объяснение проблемы с деплоем

## ❓ В чём была проблема?

### Основная проблема: **Образ не запушен в GitHub Container Registry**

Kubernetes не может скачать образ, потому что:
1. ✅ Образ собран локально
2. ❌ Образ **не запушен** в `ghcr.io/themacroeconomicdao/bybit-ai-trader:main`
3. ❌ Kubernetes получает **403 Forbidden** при попытке скачать несуществующий образ

### Почему в других проектах работает?

В других проектах образ **уже существует в registry** потому что:
- ✅ GitHub Actions workflow автоматически пушит образ при каждом push в `main`
- ✅ Образ был запушен ранее вручную
- ✅ Используется другой registry (например, публичный Docker Hub)

## 🔧 Что было исправлено

### 1. ✅ Добавлен `imagePullSecrets` в CronJob
```yaml
spec:
  imagePullSecrets:
  - name: ghcr-secret
```

**Проблема была**: В `k8s/cronjob.yaml` не было `imagePullSecrets`, поэтому Kubernetes не мог авторизоваться в GitHub Container Registry.

**Решение**: Создан секрет `ghcr-secret` и добавлен в CronJob.

### 2. ✅ Исправлено имя образа
```yaml
image: ghcr.io/themacroeconomicdao/bybit-ai-trader:main
```

**Проблема была**: Использовалось неправильное имя `trader-agent` вместо `bybit-ai-trader` (как в GitHub Actions workflow).

**Решение**: Обновлено на правильное имя из `.github/workflows/deploy.yml`.

### 3. ✅ Создан `ghcr-secret`
```bash
kubectl create secret docker-registry ghcr-secret \
  --docker-server=ghcr.io \
  --docker-username=TheMacroeconomicDao \
  --docker-password="$GHCR_TOKEN" \
  -n trader-agent
```

## 🚀 Как завершить деплой

### Вариант 1: Через GitHub Actions (РЕКОМЕНДУЕТСЯ)

Просто сделайте push в `main`:
```bash
git add k8s/cronjob.yaml
git commit -m "Fix: Add imagePullSecrets and correct image name"
git push origin main
```

GitHub Actions автоматически:
1. Соберёт образ
2. Запушит в `ghcr.io/themacroeconomicdao/bybit-ai-trader:main`
3. Задеплоит в Kubernetes

### Вариант 2: Локальный push (если Docker работает)

```bash
# Используйте GHCR_TOKEN (не GITHUB_TOKEN!)
echo "$GHCR_TOKEN" | docker login ghcr.io -u TheMacroeconomicDao --password-stdin

# Push образа
docker push ghcr.io/themacroeconomicdao/bybit-ai-trader:main
docker push ghcr.io/themacroeconomicdao/bybit-ai-trader:latest
```

## 📊 Текущий статус

✅ **Готово:**
- Образ собран локально
- `imagePullSecrets` настроен
- CronJob обновлён с правильным именем образа
- Секреты созданы

❌ **Осталось:**
- Запушить образ в registry (через GitHub Actions или локально)

## 🎯 Почему токен не подхватывался автоматически?

**Проблема**: В скриптах использовался `$GITHUB_TOKEN`, но в вашем окружении токен называется `$GHCR_TOKEN`.

**Решение**: Используйте правильное имя переменной:
```bash
# ❌ Неправильно
echo "$GITHUB_TOKEN" | docker login ...

# ✅ Правильно
echo "$GHCR_TOKEN" | docker login ...
```

## 💡 Рекомендации

1. **Используйте GitHub Actions** для автоматического push образа
2. **Проверяйте наличие образа** перед деплоем:
   ```bash
   curl -s -H "Authorization: token $GHCR_TOKEN" \
     "https://ghcr.io/v2/themacroeconomicdao/bybit-ai-trader/manifests/main"
   ```
3. **Унифицируйте имена переменных** - используйте `GHCR_TOKEN` везде или `GITHUB_TOKEN`

## ✅ После push образа

Как только образ будет в registry, Kubernetes автоматически:
1. Скачает образ используя `ghcr-secret`
2. Запустит Pod
3. CronJob будет работать по расписанию (каждые 4 часа)

Проверка:
```bash
kubectl get pods -n trader-agent
kubectl logs -n trader-agent -l app=trader-agent
```
