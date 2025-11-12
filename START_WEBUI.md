# 🚀 Как Запустить WebUI

## ✅ ПРАВИЛЬНЫЙ СПОСОБ

HTTP сервер **УЖЕ настроен** для раздачи WebUI! Есть два варианта:

---

## ВАРИАНТ 1: Production (WebUI встроен в HTTP сервер) ⭐ РЕКОМЕНДУЕТСЯ

### Шаг 1: Собрать WebUI
```bash
cd /Users/Gyber/GYBERNATY-ECOSYSTEM/TRADER-AGENT/bybit-mcp/webui
pnpm install
pnpm build
```

### Шаг 2: Запустить HTTP сервер
```bash
cd /Users/Gyber/GYBERNATY-ECOSYSTEM/TRADER-AGENT/bybit-mcp
pnpm start:http
```

### Шаг 3: Открыть в браузере
```
http://localhost:8080
```

**WebUI будет доступен на том же порту что и MCP сервер!** 🎉

---

## ВАРИАНТ 2: Development (отдельный dev сервер)

### Терминал 1: Запустить MCP HTTP сервер
```bash
cd /Users/Gyber/GYBERNATY-ECOSYSTEM/TRADER-AGENT/bybit-mcp
pnpm start:http
```

### Терминал 2: Запустить WebUI dev сервер
```bash
cd /Users/Gyber/GYBERNATY-ECOSYSTEM/TRADER-AGENT/bybit-mcp/webui
pnpm dev
```

### Открыть в браузере
```
http://localhost:3000
```

**WebUI будет проксировать запросы к MCP серверу на порту 8080.**

---

## ВАРИАНТ 3: Одной командой (concurrently)

```bash
cd /Users/Gyber/GYBERNATY-ECOSYSTEM/TRADER-AGENT/bybit-mcp/webui
pnpm dev:full
```

Это запустит и MCP сервер и WebUI одновременно.

---

## 🔍 Как Это Работает

HTTP сервер (`bybit-mcp/build/httpServer.js`) автоматически проверяет наличие `webui/dist`:

```javascript
const webuiPath = path.join(__dirname, "..", "webui", "dist");

if (existsSync(webuiPath)) {
  app.use(express.static(webuiPath));
  // WebUI будет доступен на http://localhost:8080
}
```

Если WebUI собран → он раздаётся автоматически!  
Если WebUI не собран → работает только MCP API на `/mcp`, `/tools`, `/health`

---

## ⚠️ Текущая Проблема

WebUI имеет TypeScript ошибки, поэтому сборка не проходит. 

**Решение:**
1. Исправить ошибки TypeScript
2. Или использовать dev режим (Вариант 2)

---

## 🎯 Рекомендация

**Используй Вариант 2 (Development)** - он работает сразу без исправления ошибок!

```bash
# Терминал 1
cd /Users/Gyber/GYBERNATY-ECOSYSTEM/TRADER-AGENT/bybit-mcp
pnpm start:http

# Терминал 2  
cd /Users/Gyber/GYBERNATY-ECOSYSTEM/TRADER-AGENT/bybit-mcp/webui
pnpm dev
```

Затем открой: **http://localhost:3000** 🚀










