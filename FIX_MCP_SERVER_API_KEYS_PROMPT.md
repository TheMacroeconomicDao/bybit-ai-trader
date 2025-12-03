# 🔧 ИСПРАВЛЕНИЕ MCP СЕРВЕРА - API КЛЮЧИ И ОСТАВШИЕСЯ БАГИ

## 🎯 ПРОБЛЕМА

MCP HTTP сервер (`bybit-mcp/build/httpServer.js`) не получает API ключи из переменных окружения, хотя они есть в системе и используются трейдер-агентом.

### Симптомы:
- Ошибки: `"Private endpoints require api and private keys set"`
- Ошибки: `"Cannot get wallet balance in development mode - API credentials required"`
- UI показывает пустые данные вместо реальных

### Причина:
1. **Путь к `.env` файлу неправильный**: `env.ts` ищет `.env` в `process.cwd()`, но при запуске `node build/httpServer.js` из директории `bybit-mcp`, `process.cwd()` = `bybit-mcp`, а `.env` находится в корне проекта (`/Users/Gyber/GYBERNATY-ECOSYSTEM/TRADER-AGENT/.env`)
2. **Переменные окружения не передаются**: При прямом запуске `node build/httpServer.js` переменные из `CURSOR_MCP_CONFIG.json` не доступны
3. **Нет fallback на корневой `.env`**: `env.ts` не проверяет родительские директории

---

## ✅ РЕШЕНИЕ

### 1. Исправить загрузку `.env` в `bybit-mcp/src/env.ts`

**Проблема:** `env.ts` ищет `.env` только в `process.cwd()`, но файл находится в корне проекта.

**Исправление:**
```typescript
// bybit-mcp/src/env.ts
import { config } from 'dotenv'
import { join, dirname } from 'path'
import { existsSync } from 'fs'
import { fileURLToPath } from 'url'

// Определяем корень проекта (2 уровня выше от bybit-mcp/src)
const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)
const projectRoot = join(__dirname, '..', '..') // Переход из bybit-mcp/src в корень проекта

// Пробуем загрузить .env из разных мест (приоритет):
// 1. Корень проекта (где находится .env)
const projectEnvPath = join(projectRoot, '.env')
// 2. Текущая директория (bybit-mcp)
const currentEnvPath = join(process.cwd(), '.env')
// 3. Директория bybit-mcp
const bybitMcpEnvPath = join(__dirname, '..', '.env')

let envLoaded = false

// Пробуем загрузить в порядке приоритета
if (existsSync(projectEnvPath)) {
  config({ path: projectEnvPath })
  envLoaded = true
  console.log(`✅ Loaded .env from project root: ${projectEnvPath}`)
} else if (existsSync(currentEnvPath)) {
  config({ path: currentEnvPath })
  envLoaded = true
  console.log(`✅ Loaded .env from current directory: ${currentEnvPath}`)
} else if (existsSync(bybitMcpEnvPath)) {
  config({ path: bybitMcpEnvPath })
  envLoaded = true
  console.log(`✅ Loaded .env from bybit-mcp: ${bybitMcpEnvPath}`)
}

if (!envLoaded) {
  console.warn('⚠️ No .env file found. Trying default dotenv behavior...')
  config() // Попытка загрузить из текущей директории
}

export interface EnvConfig {
  apiKey: string | undefined
  apiSecret: string | undefined
  useTestnet: boolean
  debug: boolean
}

export function getEnvConfig(): EnvConfig {
  const config = {
    apiKey: process.env.BYBIT_API_KEY,
    apiSecret: process.env.BYBIT_API_SECRET,
    useTestnet: process.env.BYBIT_USE_TESTNET === 'true',
    debug: process.env.DEBUG === 'true',
  }
  
  // Логирование для отладки (без показа секретов)
  if (config.apiKey) {
    console.log(`✅ BYBIT_API_KEY loaded (length: ${config.apiKey.length}, preview: ${config.apiKey.substring(0, 4)}...${config.apiKey.substring(config.apiKey.length - 4)})`)
  } else {
    console.warn('⚠️ BYBIT_API_KEY not found in environment')
  }
  
  if (config.apiSecret) {
    console.log(`✅ BYBIT_API_SECRET loaded (length: ${config.apiSecret.length})`)
  } else {
    console.warn('⚠️ BYBIT_API_SECRET not found in environment')
  }
  
  return config
}

// Validate environment variables
export function validateEnv(): void {
  const config = getEnvConfig()

  // In development mode, API keys are optional
  if (!config.apiKey || !config.apiSecret) {
    console.warn('⚠️ Running in development mode: API keys not provided')
    console.warn('   Set BYBIT_API_KEY and BYBIT_API_SECRET environment variables or add them to .env file')
  } else {
    console.log('✅ API credentials configured - production mode enabled')
  }

  // Additional validations can be added here
}
```

### 2. Создать скрипт запуска с правильными переменными окружения

**Создать файл:** `bybit-mcp/scripts/start-http-server.sh`

```bash
#!/bin/bash
# Скрипт запуска HTTP MCP сервера с правильными переменными окружения

# Определяем корень проекта (2 уровня выше)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/../.." && pwd )"

# Загружаем переменные из .env файла в корне проекта
if [ -f "$PROJECT_ROOT/.env" ]; then
  echo "✅ Loading environment variables from $PROJECT_ROOT/.env"
  export $(cat "$PROJECT_ROOT/.env" | grep -v '^#' | xargs)
else
  echo "⚠️ Warning: .env file not found at $PROJECT_ROOT/.env"
fi

# Переходим в директорию bybit-mcp
cd "$SCRIPT_DIR/.."

# Запускаем HTTP сервер
echo "🚀 Starting MCP HTTP server..."
node build/httpServer.js
```

**Сделать исполняемым:**
```bash
chmod +x bybit-mcp/scripts/start-http-server.sh
```

**Обновить `package.json`:**
```json
{
  "scripts": {
    "serve:http": "node build/httpServer.js",
    "serve:http:env": "./scripts/start-http-server.sh",
    "start:http": "pnpm run build && pnpm run serve:http:env"
  }
}
```

### 3. Исправить проверку API ключей в `BaseTool.ts`

**Проблема:** `isDevMode` определяется как `!config.apiKey || !config.apiSecret`, но нужно также проверять, что ключи не пустые строки.

**Исправление:**
```typescript
// bybit-mcp/src/tools/BaseTool.ts (строка ~81)
constructor(mockClient?: RestClientV5) {
  if (mockClient) {
    // Use provided mock client for testing
    this.client = mockClient
    this.isDevMode = true
    this.isTestMode = true
  } else {
    // Normal production/development initialization
    const config = getEnvConfig()
    // Проверяем, что ключи не только существуют, но и не пустые
    this.isDevMode = !config.apiKey || !config.apiSecret || 
                     config.apiKey.trim() === '' || 
                     config.apiSecret.trim() === ''

    if (this.isDevMode) {
      console.warn('⚠️ Running in development mode - API keys missing or empty')
      this.client = new RestClientV5({
        testnet: true,
      })
    } else {
      console.log('✅ Running in production mode with API credentials')
      this.client = new RestClientV5({
        key: config.apiKey,
        secret: config.apiSecret,
        testnet: config.useTestnet,
        recv_window: 5000, // 5 second receive window
      })
    }
  }
}
```

### 4. Добавить проверку API ключей при старте HTTP сервера

**Исправление в `bybit-mcp/src/httpServer.ts`:**
```typescript
// Добавить после импортов (строка ~22)
import { validateEnv, getEnvConfig } from "./env.js"

// Добавить после создания app (строка ~38)
// Validate environment on startup
validateEnv()
const envConfig = getEnvConfig()
if (!envConfig.apiKey || !envConfig.apiSecret) {
  console.warn('⚠️ WARNING: BYBIT_API_KEY and/or BYBIT_API_SECRET not set!')
  console.warn('   Private endpoints (positions, wallet balance, orders) will not work.')
  console.warn('   Set them in .env file or as environment variables.')
} else {
  console.log('✅ API credentials loaded successfully')
}
```

### 5. Улучшить обработку ошибок в UI

**Проблема:** UI не показывает понятные сообщения об ошибках API ключей.

**Уже исправлено в предыдущих изменениях:**
- `tradingDataService.ts` теперь хранит `lastError`
- `TradingDashboard.ts` показывает сообщения об ошибках

**Проверить, что изменения применены правильно.**

### 6. Исправить имя инструмента в `getPortfolio()`

**Проблема:** В `TradingDashboard.ts` используется неправильное имя инструмента.

**Исправление:**
```typescript
// bybit-mcp/webui/src/components/TradingDashboard.ts (строка ~471)
// Fallback to MCP if tradingDataService fails
try {
  const balanceResult = await mcpClient.callTool('get_wallet_balance', {
    accountType: 'UNIFIED'
  });
  // ... остальной код
}
```

---

## 📋 ЧЕКЛИСТ ИСПРАВЛЕНИЙ

- [ ] Исправить `bybit-mcp/src/env.ts` - добавить поиск `.env` в корне проекта
- [ ] Создать скрипт `bybit-mcp/scripts/start-http-server.sh` для запуска с правильными переменными
- [ ] Обновить `package.json` - добавить скрипт `serve:http:env`
- [ ] Исправить проверку пустых строк в `BaseTool.ts`
- [ ] Добавить валидацию при старте в `httpServer.ts`
- [ ] Проверить, что UI правильно показывает ошибки API ключей
- [ ] Пересобрать проект: `cd bybit-mcp && pnpm run build`
- [ ] Протестировать запуск: `cd bybit-mcp && pnpm run serve:http:env`

---

## 🧪 ТЕСТИРОВАНИЕ

После исправлений:

1. **Проверить загрузку переменных:**
```bash
cd bybit-mcp
node -e "import('./src/env.js').then(m => { const c = m.getEnvConfig(); console.log('API Key:', c.apiKey ? c.apiKey.substring(0, 4) + '...' : 'NOT FOUND'); console.log('API Secret:', c.apiSecret ? 'FOUND (' + c.apiSecret.length + ' chars)' : 'NOT FOUND'); })"
```

2. **Запустить HTTP сервер:**
```bash
cd bybit-mcp
pnpm run serve:http:env
```

3. **Проверить логи:** Должны увидеть:
   - `✅ Loaded .env from project root: ...`
   - `✅ BYBIT_API_KEY loaded (length: X, preview: ...)`
   - `✅ BYBIT_API_SECRET loaded (length: X)`
   - `✅ API credentials configured - production mode enabled`
   - `✅ Running in production mode with API credentials`

4. **Проверить в браузере:** `http://localhost:3001/`
   - Позиции должны загружаться (если есть открытые позиции)
   - Портфель должен показывать реальный баланс
   - История ордеров должна загружаться

---

## 🔍 ДОПОЛНИТЕЛЬНАЯ ДИАГНОСТИКА

Если проблемы остаются:

1. **Проверить, что `.env` файл существует:**
```bash
ls -la /Users/Gyber/GYBERNATY-ECOSYSTEM/TRADER-AGENT/.env
```

2. **Проверить содержимое `.env`:**
```bash
grep BYBIT_API /Users/Gyber/GYBERNATY-ECOSYSTEM/TRADER-AGENT/.env
```

3. **Проверить переменные окружения в процессе:**
```bash
cd bybit-mcp
node -e "console.log('BYBIT_API_KEY:', process.env.BYBIT_API_KEY ? 'SET (' + process.env.BYBIT_API_KEY.length + ' chars)' : 'NOT SET')"
```

4. **Проверить логи HTTP сервера:** Должны видеть сообщения о загрузке переменных

---

## 📝 ПРИМЕЧАНИЯ

- **Безопасность:** Никогда не коммитьте `.env` файл в git
- **Приоритет:** Переменные окружения имеют приоритет над `.env` файлом
- **Тестнет:** Если `BYBIT_TESTNET=true`, будет использоваться тестовая сеть Bybit
- **Отладка:** Установите `DEBUG=true` для подробных логов

---

## ✅ ОЖИДАЕМЫЙ РЕЗУЛЬТАТ

После применения всех исправлений:
- ✅ MCP HTTP сервер загружает API ключи из `.env` файла в корне проекта
- ✅ Приватные эндпоинты (позиции, баланс, ордера) работают корректно
- ✅ UI показывает реальные данные вместо ошибок
- ✅ Сообщения об ошибках понятные и информативные
- ✅ Логи показывают успешную загрузку API ключей


