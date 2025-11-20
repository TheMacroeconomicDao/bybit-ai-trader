# 🔧 ПРОМПТЫ ДЛЯ ИСПРАВЛЕНИЯ ПРОБЛЕМ
## AI Trading Agent - Action Items

Этот документ содержит готовые к использованию промпты для исправления всех выявленных проблем. Каждый промпт можно скопировать и использовать напрямую в Cursor/CLI для исправления соответствующей проблемы.

---

## 🔴 КРИТИЧЕСКИЕ ПРОБЛЕМЫ (P0)

### ПРОМПТ 1: Удаление Hardcoded API Keys и очистка Git истории

```
КОНТЕКСТ:
В проекте AI Trading Agent обнаружены hardcoded API ключи в следующих файлах и Git истории:

УТЕКШИЕ КЛЮЧИ:
- Bybit API Key #1: V84NJog5v9bM5k6fRn
- Bybit Secret #1: RYZ1JeyGsWhtjigF01rKDYzq3lRbvlxvU89L
- Bybit API Key #2: hdG6Hb7a5OsNzmhLde
- Bybit Secret #2: D5SV0QBeV0v85OxcVoxN82zPrOvRqKqh9b5R
- Qwen API Key: sk-6f5319fb244f4f9faa1595825cf87a05
- Telegram Token: 8003689195:AAGxQsopKvlLS34H2TZ0S1a0K7s4yV4iOBY

ФАЙЛЫ (УЖЕ ОБНОВЛЕНЫ НА PLACEHOLDERS):
✅ README.md, SETUP_GUIDE.md, MASTER_PROMPT.md
✅ TEST_REPORT.md, mcp_integration.md, DUAL_MCP_SETUP.md
✅ config/credentials.json
✅ autonomous_agent/QUICK_START.md, autonomous_agent/README.md

ЗАДАЧА:
Очистить Git историю от всех утекших API ключей и настроить безопасное хранение.

ТРЕБОВАНИЯ:

1. НЕМЕДЛЕННО отозвать все старые ключи:
   - Bybit: https://www.bybit.com/ → Account & Security → API Management → Delete
   - OpenRouter: https://openrouter.ai/ → Settings → Revoke
   - Telegram: @BotFather → /revoke

2. Очистить Git историю используя BFG Repo-Cleaner:
   ```bash
   # Установить BFG
   brew install bfg  # для Mac
   
   # Создать файл со старыми ключами
   cat > passwords.txt << 'EOF'
   V84NJog5v9bM5k6fRn
   RYZ1JeyGsWhtjigF01rKDYzq3lRbvlxvU89L
   hdG6Hb7a5OsNzmhLde
   D5SV0QBeV0v85OxcVoxN82zPrOvRqKqh9b5R
   sk-6f5319fb244f4f9faa1595825cf87a05
   8003689195:AAGxQsopKvlLS34H2TZ0S1a0K7s4yV4iOBY
   EOF
   
   # Запустить BFG
   cd /Users/Gyber/GYBERNATY-ECOSYSTEM/TRADER-AGENT
   bfg --replace-text passwords.txt
   
   # Очистить кеш
   git reflog expire --expire=now --all
   git gc --prune=now --aggressive
   
   # Force push (ОСТОРОЖНО!)
   git push --force --all
   
   # Удалить файл с паролями
   rm passwords.txt
   ```

3. Создать новые API ключи:
   - Bybit: Read + Trade разрешения (БЕЗ Withdraw!)
   - OpenRouter: с лимитами
   - Telegram: новый токен если нужно

4. Настроить GitHub Secrets:
   ```bash
   gh secret set BYBIT_API_KEY
   gh secret set BYBIT_API_SECRET
   gh secret set QWEN_API_KEY
   gh secret set TELEGRAM_BOT_TOKEN
   ```

5. Обновить .env.example:
   ```bash
   cat > .env.example << 'EOF'
   # Bybit API Keys
   BYBIT_API_KEY=your_api_key_here
   BYBIT_API_SECRET=your_api_secret_here
   BYBIT_TESTNET=false
   
   # Qwen/OpenRouter API
   QWEN_API_KEY=your_qwen_key_here
   
   # Telegram
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   TELEGRAM_CHAT_IDS=your_chat_ids_here
   EOF
   ```

6. Установить pre-commit hooks для предотвращения будущих утечек:
   ```bash
   pip install pre-commit
   
   cat > .pre-commit-config.yaml << 'EOF'
   repos:
     - repo: https://github.com/pre-commit/pre-commit-hooks
       rev: v4.4.0
       hooks:
         - id: detect-private-key
         - id: check-added-large-files
     - repo: https://github.com/Yelp/detect-secrets
       rev: v1.4.0
       hooks:
         - id: detect-secrets
           args: ['--baseline', '.secrets.baseline']
   EOF
   
   pre-commit install
   ```

ПРОВЕРКА:
1. Ключи отозваны на всех платформах
2. Git история очищена: `git log -S "V84NJog5v9bM5k6fRn" --all` (должно быть пусто)
3. GitHub Secrets настроены: `gh secret list`
4. Pre-commit hooks установлены: `pre-commit --version`
5. Новые ключи работают: протестировать подключение

КРИТИЧНОСТЬ: P0 - НЕМЕДЛЕННО
ВРЕМЯ: 2-4 часа
РИСК ЕСЛИ НЕ СДЕЛАТЬ: Кража средств, несанкционированные сделки

ССЫЛКИ:
- Детальная инструкция: SECURITY_AUDIT.md
- BFG: https://rtyley.github.io/bfg-repo-cleaner/
```

---

### ПРОМПТ 2: Исправить Hardcoded баланс $30

```
КОНТЕКСТ:
В файле mcp_server/market_scanner.py на строке 443 обнаружено hardcoded значение баланса:
`ACCOUNT_BALANCE = 30.0`

Это недопустимо для production, так как:
- Не масштабируется при изменении депозита
- Риск-расчеты некорректны для других балансов
- Position sizing неправильный

ЗАДАЧА:
Заменить hardcoded значение на динамический запрос баланса из Bybit API.

ТРЕБОВАНИЯ:

1. Открыть файл mcp_server/market_scanner.py

2. Найти строку 443 с `ACCOUNT_BALANCE = 30.0`

3. Заменить на динамический запрос:
   ```python
   # Вместо hardcoded значения
   # ACCOUNT_BALANCE = 30.0  # ❌ УДАЛИТЬ
   
   # Добавить метод для получения баланса
   async def get_account_balance(self):
       """Получить текущий баланс аккаунта"""
       try:
           balance_data = await self.bybit_client.get_wallet_balance()
           
           # Для Unified Trading Account
           if 'result' in balance_data and 'list' in balance_data['result']:
               for account in balance_data['result']['list']:
                   if account.get('accountType') == 'UNIFIED':
                       return float(account.get('totalEquity', 0))
           
           # Fallback для других типов аккаунтов
           return float(balance_data.get('totalEquity', 0))
       except Exception as e:
           logger.error(f"Error getting balance: {e}")
           return 0.0
   
   # Использовать во всех методах где нужен баланс
   account_balance = await self.get_account_balance()
   ```

4. Обновить все места где используется ACCOUNT_BALANCE:
   - В методе calculate_position_size()
   - В методе scan_market()
   - В методе validate_entry()

5. Добавить валидацию баланса:
   ```python
   if account_balance <= 0:
       raise ValueError("Account balance is zero or negative. Cannot calculate position size.")
   ```

6. Добавить кэширование баланса (опционально):
   ```python
   # Добавить в __init__
   self._balance_cache = None
   self._balance_cache_time = None
   self._balance_cache_ttl = 60  # 60 секунд
   
   async def get_account_balance(self, use_cache=True):
       """Получить баланс с кэшированием"""
       now = time.time()
       
       # Проверить кэш
       if use_cache and self._balance_cache is not None:
           if self._balance_cache_time and (now - self._balance_cache_time) < self._balance_cache_ttl:
               return self._balance_cache
       
       # Запросить свежие данные
       balance = await self._fetch_balance_from_api()
       
       # Обновить кэш
       self._balance_cache = balance
       self._balance_cache_time = now
       
       return balance
   ```

ПРИМЕР ЖЕЛАЕМОГО РЕЗУЛЬТАТА:
```python
# До
ACCOUNT_BALANCE = 30.0
position_size = ACCOUNT_BALANCE * risk_percent / 100

# После
account_balance = await self.get_account_balance()
if account_balance <= 0:
    raise ValueError("Invalid account balance")
position_size = account_balance * risk_percent / 100
```

ПРОВЕРКА:
1. Нет hardcoded ACCOUNT_BALANCE в коде: `grep -r "ACCOUNT_BALANCE = " mcp_server/`
2. Баланс запрашивается динамически
3. Все тесты проходят
4. Position sizing корректен для разных балансов

ФАЙЛЫ ДЛЯ ИЗМЕНЕНИЯ:
- mcp_server/market_scanner.py (основной)
- Возможно mcp_server/trading_operations.py

КРИТИЧНОСТЬ: P0 - НЕМЕДЛЕННО
ВРЕМЯ: 2-3 часа
РИСК ЕСЛИ НЕ СДЕЛАТЬ: Неверные расчеты риска, потеря средств
```

---

### ПРОМПТ 3: Исправить Fake R:R Scoring

```
КОНТЕКСТ:
В файле mcp_server/market_scanner.py на строке 337 обнаружено fake scoring:
`rr_score = 1.0`

Это означает что агент всегда даёт максимальную оценку R:R независимо от реального соотношения риск/прибыль.

ЗАДАЧА:
Реализовать настоящий расчёт R:R score на основе фактического соотношения.

ТРЕБОВАНИЯ:

1. Открыть mcp_server/market_scanner.py

2. Найти строку 337 с `rr_score = 1.0`

3. Заменить на реальный расчёт:
   ```python
   def calculate_rr_score(entry_price: float, stop_loss: float, take_profit: float) -> float:
       """
       Рассчитать R:R score на основе соотношения риск/прибыль
       
       Args:
           entry_price: Цена входа
           stop_loss: Уровень стоп-лосса
           take_profit: Уровень тейк-профита
       
       Returns:
           Score от 0 до 10 на основе R:R
       """
       # Рассчитать риск и прибыль
       risk = abs(entry_price - stop_loss)
       reward = abs(take_profit - entry_price)
       
       # Валидация
       if risk <= 0:
           logger.warning("Invalid risk value (<=0)")
           return 0.0
       
       # Рассчитать R:R соотношение
       rr_ratio = reward / risk
       
       # Конвертировать в score 0-10
       # 1:1 R:R = 2.5/10 (минимально приемлемо)
       # 1:2 R:R = 5.0/10 (хорошо)
       # 1:3 R:R = 7.5/10 (отлично)
       # 1:4+ R:R = 10/10 (превосходно)
       
       if rr_ratio < 1.0:
           # R:R меньше 1:1 - очень плохо
           score = max(0, rr_ratio * 2.5)
       elif rr_ratio < 2.0:
           # R:R от 1:1 до 1:2
           score = 2.5 + (rr_ratio - 1.0) * 2.5
       elif rr_ratio < 3.0:
           # R:R от 1:2 до 1:3
           score = 5.0 + (rr_ratio - 2.0) * 2.5
       else:
           # R:R 1:3 и выше
           score = min(10.0, 7.5 + (rr_ratio - 3.0) * 1.25)
       
       return round(score, 2)
   ```

4. Использовать в методе validate_entry():
   ```python
   # Вместо
   # rr_score = 1.0  # ❌ УДАЛИТЬ
   
   # Использовать
   rr_score = calculate_rr_score(entry_price, stop_loss, take_profit)
   
   # Добавить в результат
   result['rr_ratio'] = reward / risk
   result['rr_score'] = rr_score
   
   # Добавить предупреждение если R:R плохой
   if rr_ratio < 1.5:
       warnings.append({
           'type': 'low_rr_ratio',
           'message': f"R:R соотношение низкое: 1:{rr_ratio:.1f}. Рекомендуем минимум 1:2",
           'severity': 'high'
       })
   ```

5. Обновить confluence scoring с учётом R:R:
   ```python
   # В методе scan_market() или validate_entry()
   
   # R:R влияет на итоговый score
   if rr_score >= 7.5:  # R:R >= 1:3
       confluence_adjustment += 0.5
   elif rr_score >= 5.0:  # R:R >= 1:2
       confluence_adjustment += 0.3
   elif rr_score < 2.5:  # R:R < 1:1
       confluence_adjustment -= 1.0
   
   final_confluence = base_confluence + confluence_adjustment
   ```

6. Добавить юнит-тесты:
   ```python
   # tests/test_rr_calculation.py
   
   def test_rr_score_calculation():
       # Test 1:1 R:R
       assert calculate_rr_score(100, 90, 110) == 2.5
       
       # Test 1:2 R:R
       assert calculate_rr_score(100, 90, 120) == 5.0
       
       # Test 1:3 R:R
       assert calculate_rr_score(100, 90, 130) == 7.5
       
       # Test 1:4 R:R
       assert calculate_rr_score(100, 90, 140) >= 8.75
       
       # Test invalid (risk = 0)
       assert calculate_rr_score(100, 100, 110) == 0.0
   ```

ПРИМЕР ЖЕЛАЕМОГО РЕЗУЛЬТАТА:
```python
# Пример анализа
entry = 100
sl = 95
tp = 115

risk = 5
reward = 15
rr_ratio = 3.0

rr_score = calculate_rr_score(entry, sl, tp)
# rr_score = 7.5/10 (отлично!)
```

ПРОВЕРКА:
1. Нет hardcoded `rr_score = 1.0` в коде
2. R:R рассчитывается корректно для разных сценариев
3. Score адекватен (1:1 = 2.5, 1:2 = 5.0, 1:3 = 7.5)
4. Тесты проходят
5. Warnings появляются для плохих R:R

ФАЙЛЫ ДЛЯ ИЗМЕНЕНИЯ:
- mcp_server/market_scanner.py (основной)
- tests/test_rr_calculation.py (новый)

КРИТИЧНОСТЬ: P0 - НЕМЕДЛЕННО
ВРЕМЯ: 2-3 часа
РИСК ЕСЛИ НЕ СДЕЛАТЬ: Ложная уверенность в плохих сделках
```

---

### ПРОМПТ 4: Создать Trading MCP Server

```
КОНТЕКСТ:
Текущий bybit-mcp сервер работает в READ-ONLY режиме и не может:
- Размещать ордера (place_order)
- Закрывать позиции (close_position)
- Изменять SL/TP (modify_position)
- Отменять ордера (cancel_order)

Это ограничивает автоматизацию торговли.

ЗАДАЧА:
Создать отдельный Python MCP сервер для торговых операций с полной автоматизацией.

ТРЕБОВАНИЯ:

1. Создать новый файл mcp_server/trading_server.py:
   ```python
   #!/usr/bin/env python3
   """
   Trading MCP Server - Автоматизация торговых операций
   
   Provides trading operations:
   - place_order: Размещение ордеров
   - close_position: Закрытие позиций
   - modify_position: Изменение SL/TP
   - cancel_order: Отмена ордеров
   - monitor_positions_realtime: WebSocket мониторинг
   """
   
   import asyncio
   import json
   import logging
   from typing import Dict, List, Optional
   from datetime import datetime
   
   from mcp.server import Server
   from mcp.types import Tool, TextContent
   from pybit.unified_trading import HTTP, WebSocket
   
   # Настройка логирования
   logging.basicConfig(level=logging.INFO)
   logger = logging.getLogger(__name__)
   
   # Инициализация MCP сервера
   app = Server("bybit-trading")
   
   # Bybit клиент
   bybit_client = None
   ws_client = None
   
   
   def init_bybit_client():
       """Инициализация Bybit клиента"""
       global bybit_client, ws_client
       
       api_key = os.getenv("BYBIT_API_KEY")
       api_secret = os.getenv("BYBIT_API_SECRET")
       testnet = os.getenv("BYBIT_TESTNET", "false").lower() == "true"
       
       if not api_key or not api_secret:
           raise ValueError("BYBIT_API_KEY and BYBIT_API_SECRET must be set")
       
       bybit_client = HTTP(
           testnet=testnet,
           api_key=api_key,
           api_secret=api_secret
       )
       
       ws_client = WebSocket(
           testnet=testnet,
           api_key=api_key,
           api_secret=api_secret,
           channel_type="private"
       )
   
   
   @app.list_tools()
   async def list_tools() -> List[Tool]:
       """Список доступных инструментов"""
       return [
           Tool(
               name="place_order",
               description="Размещает ордер на Bybit",
               inputSchema={
                   "type": "object",
                   "properties": {
                       "symbol": {"type": "string", "description": "Символ (например, BTCUSDT)"},
                       "side": {"type": "string", "enum": ["Buy", "Sell"]},
                       "order_type": {"type": "string", "enum": ["Market", "Limit"]},
                       "qty": {"type": "number", "description": "Количество"},
                       "price": {"type": "number", "description": "Цена (для Limit)"},
                       "stop_loss": {"type": "number", "description": "Stop Loss"},
                       "take_profit": {"type": "number", "description": "Take Profit"},
                       "reduce_only": {"type": "boolean", "default": False}
                   },
                   "required": ["symbol", "side", "order_type", "qty"]
               }
           ),
           Tool(
               name="close_position",
               description="Закрывает открытую позицию",
               inputSchema={
                   "type": "object",
                   "properties": {
                       "symbol": {"type": "string"},
                       "qty": {"type": "number", "description": "Количество или 'all'"},
                   },
                   "required": ["symbol"]
               }
           ),
           Tool(
               name="modify_position",
               description="Изменяет SL/TP позиции",
               inputSchema={
                   "type": "object",
                   "properties": {
                       "symbol": {"type": "string"},
                       "stop_loss": {"type": "number"},
                       "take_profit": {"type": "number"},
                   },
                   "required": ["symbol"]
               }
           ),
           Tool(
               name="cancel_order",
               description="Отменяет ордер",
               inputSchema={
                   "type": "object",
                   "properties": {
                       "symbol": {"type": "string"},
                       "order_id": {"type": "string"},
                   },
                   "required": ["symbol", "order_id"]
               }
           ),
           Tool(
               name="monitor_positions_realtime",
               description="Запускает WebSocket мониторинг позиций с auto-actions",
               inputSchema={
                   "type": "object",
                   "properties": {
                       "auto_breakeven": {"type": "boolean", "default": True},
                       "auto_trailing": {"type": "boolean", "default": True},
                       "breakeven_rr": {"type": "number", "default": 1.0},
                       "trailing_rr": {"type": "number", "default": 2.0},
                   }
               }
           ),
       ]
   
   
   @app.call_tool()
   async def call_tool(name: str, arguments: Dict) -> List[TextContent]:
       """Вызов инструмента"""
       
       if name == "place_order":
           return await place_order(arguments)
       elif name == "close_position":
           return await close_position(arguments)
       elif name == "modify_position":
           return await modify_position(arguments)
       elif name == "cancel_order":
           return await cancel_order(arguments)
       elif name == "monitor_positions_realtime":
           return await monitor_positions_realtime(arguments)
       else:
           raise ValueError(f"Unknown tool: {name}")
   
   
   async def place_order(args: Dict) -> List[TextContent]:
       """Размещает ордер"""
       try:
           # Валидация параметров
           symbol = args["symbol"]
           side = args["side"]
           order_type = args["order_type"]
           qty = args["qty"]
           
           # Подготовка параметров
           order_params = {
               "category": "linear",  # или "spot"
               "symbol": symbol,
               "side": side,
               "orderType": order_type,
               "qty": str(qty),
           }
           
           if order_type == "Limit":
               order_params["price"] = str(args.get("price"))
           
           if "stop_loss" in args:
               order_params["stopLoss"] = str(args["stop_loss"])
           
           if "take_profit" in args:
               order_params["takeProfit"] = str(args["take_profit"])
           
           if args.get("reduce_only"):
               order_params["reduceOnly"] = True
           
           # Размещение ордера
           result = bybit_client.place_order(**order_params)
           
           # Форматирование ответа
           if result["retCode"] == 0:
               order_id = result["result"]["orderId"]
               
               return [TextContent(
                   type="text",
                   text=json.dumps({
                       "success": True,
                       "order_id": order_id,
                       "symbol": symbol,
                       "side": side,
                       "qty": qty,
                       "message": f"Ордер #{order_id} размещён успешно"
                   }, indent=2)
               )]
           else:
               raise Exception(f"Bybit error: {result['retMsg']}")
       
       except Exception as e:
           logger.error(f"Error placing order: {e}")
           return [TextContent(
               type="text",
               text=json.dumps({
                   "success": False,
                   "error": str(e)
               }, indent=2)
           )]
   
   
   async def close_position(args: Dict) -> List[TextContent]:
       """Закрывает позицию"""
       try:
           symbol = args["symbol"]
           
           # Получить текущую позицию
           positions = bybit_client.get_positions(
               category="linear",
               symbol=symbol
           )
           
           if not positions["result"]["list"]:
               return [TextContent(
                   type="text",
                   text=json.dumps({
                       "success": False,
                       "message": "Нет открытой позиции"
                   }, indent=2)
               )]
           
           position = positions["result"]["list"][0]
           size = float(position["size"])
           side_to_close = "Sell" if position["side"] == "Buy" else "Buy"
           
           # Закрыть позицию
           close_result = bybit_client.place_order(
               category="linear",
               symbol=symbol,
               side=side_to_close,
               orderType="Market",
               qty=str(args.get("qty", size)),
               reduceOnly=True
           )
           
           if close_result["retCode"] == 0:
               return [TextContent(
                   type="text",
                   text=json.dumps({
                       "success": True,
                       "message": f"Позиция {symbol} закрыта",
                       "order_id": close_result["result"]["orderId"]
                   }, indent=2)
               )]
           else:
               raise Exception(f"Error: {close_result['retMsg']}")
       
       except Exception as e:
           logger.error(f"Error closing position: {e}")
           return [TextContent(
               type="text",
               text=json.dumps({
                   "success": False,
                   "error": str(e)
               }, indent=2)
           )]
   
   
   async def modify_position(args: Dict) -> List[TextContent]:
       """Изменяет SL/TP позиции"""
       try:
           symbol = args["symbol"]
           
           # Получить позицию
           positions = bybit_client.get_positions(
               category="linear",
               symbol=symbol
           )
           
           if not positions["result"]["list"]:
               return [TextContent(
                   type="text",
                   text=json.dumps({
                       "success": False,
                       "message": "Нет открытой позиции"
                   })
               )]
           
           position = positions["result"]["list"][0]
           
           # Изменить SL/TP
           params = {
               "category": "linear",
               "symbol": symbol,
               "positionIdx": 0
           }
           
           if "stop_loss" in args:
               params["stopLoss"] = str(args["stop_loss"])
           
           if "take_profit" in args:
               params["takeProfit"] = str(args["take_profit"])
           
           result = bybit_client.set_trading_stop(**params)
           
           if result["retCode"] == 0:
               return [TextContent(
                   type="text",
                   text=json.dumps({
                       "success": True,
                       "message": "SL/TP обновлены",
                       "stop_loss": args.get("stop_loss"),
                       "take_profit": args.get("take_profit")
                   }, indent=2)
               )]
           else:
               raise Exception(f"Error: {result['retMsg']}")
       
       except Exception as e:
           logger.error(f"Error modifying position: {e}")
           return [TextContent(type="text", text=json.dumps({"success": False, "error": str(e)})])
   
   
   async def monitor_positions_realtime(args: Dict) -> List[TextContent]:
       """WebSocket мониторинг с auto-actions"""
       try:
           auto_breakeven = args.get("auto_breakeven", True)
           auto_trailing = args.get("auto_trailing", True)
           breakeven_rr = args.get("breakeven_rr", 1.0)
           trailing_rr = args.get("trailing_rr", 2.0)
           
           # Подписаться на обновления позиций
           def handle_position(message):
               """Обработка обновления позиции"""
               for position in message["data"]:
                   symbol = position["symbol"]
                   side = position["side"]
                   entry_price = float(position["avgPrice"])
                   current_price = float(position["markPrice"])
                   stop_loss = float(position.get("stopLoss", 0))
                   
                   # Рассчитать R:R
                   if side == "Buy":
                       current_rr = (current_price - entry_price) / (entry_price - stop_loss) if stop_loss else 0
                   else:
                       current_rr = (entry_price - current_price) / (stop_loss - entry_price) if stop_loss else 0
                   
                   # Auto-breakeven
                   if auto_breakeven and current_rr >= breakeven_rr and stop_loss != entry_price:
                       logger.info(f"{symbol}: Moving SL to breakeven (R:R={current_rr:.1f})")
                       bybit_client.set_trading_stop(
                           category="linear",
                           symbol=symbol,
                           stopLoss=str(entry_price),
                           positionIdx=0
                       )
                   
                   # Auto-trailing
                   if auto_trailing and current_rr >= trailing_rr:
                       # Implement trailing stop logic
                       pass
           
           ws_client.position_stream(handle_position)
           
           return [TextContent(
               type="text",
               text=json.dumps({
                   "success": True,
                   "message": "WebSocket мониторинг запущен",
                   "auto_breakeven": auto_breakeven,
                   "auto_trailing": auto_trailing
               }, indent=2)
           )]
       
       except Exception as e:
           logger.error(f"Error in monitoring: {e}")
           return [TextContent(type="text", text=json.dumps({"success": False, "error": str(e)})])
   
   
   async def main():
       """Запуск сервера"""
       init_bybit_client()
       
       from mcp.server.stdio import stdio_server
       async with stdio_server() as (read_stream, write_stream):
           await app.run(read_stream, write_stream, app.create_initialization_options())
   
   
   if __name__ == "__main__":
       asyncio.run(main())
   ```

2. Добавить в package.json настройки для нового сервера (если нужно)

3. Обновить Cursor MCP Settings:
   ```json
   {
     "mcpServers": {
       "bybit-analysis": {
         "command": "node",
         "args": ["/path/to/bybit-mcp/build/index.js"],
         "env": { ... }
       },
       "bybit-trading": {
         "command": "python",
         "args": ["/path/to/mcp_server/trading_server.py"],
         "env": {
           "BYBIT_API_KEY": "${BYBIT_API_KEY}",
           "BYBIT_API_SECRET": "${BYBIT_API_SECRET}",
           "BYBIT_TESTNET": "false"
         }
       }
     }
   }
   ```

4. Создать тесты (в testnet режиме):
   ```python
   # tests/test_trading_server.py
   
   async def test_place_order_testnet():
       # Тест размещения ордера в testnet
       pass
   
   async def test_close_position_testnet():
       # Тест закрытия позиции
       pass
   ```

ПРОВЕРКА:
1. Сервер запускается без ошибок
2. MCP tools доступны в Cursor
3. Тесты в testnet проходят
4. Ордера размещаются корректно
5. WebSocket мониторинг работает

ФАЙЛЫ ДЛЯ СОЗДАНИЯ:
- mcp_server/trading_server.py (новый)
- tests/test_trading_server.py (новый)
- docs/TRADING_SERVER_GUIDE.md (новый)

КРИТИЧНОСТЬ: P0 - НЕМЕДЛЕННО
ВРЕМЯ: 6-8 часов
РИСК ЕСЛИ НЕ СДЕЛАТЬ: Нет автоматизации торговли
```

---

### ПРОМПТ 5: Внедрить Order Flow Analysis (CVD)

```
КОНТЕКСТ:
Система использует только запаздывающие индикаторы (RSI, MACD) и игнорирует Order Flow - агрессивные покупки/продажи институционалов.

Cumulative Volume Delta (CVD) показывает:
- Кто контролирует рынок (быки/медведи)
- Дивергенции (Price ↓, CVD ↑ = Absorption)
- Зоны накопления/распределения

ЗАДАЧА:
Реализовать расчёт CVD и интегрировать в анализ.

ТРЕБОВАНИЯ:

1. Создать метод в mcp_server/technical_analysis.py:
   ```python
   def calculate_cvd(trades_data: List[Dict]) -> List[float]:
       """
       Cumulative Volume Delta - агрессивные покупки минус продажи
       
       Args:
           trades_data: Список трейдов с полями:
               - side: 'Buy' или 'Sell'
               - volume: Объём трейда
               - price: Цена
               - timestamp: Время
       
       Returns:
           Список CVD значений
       """
       cvd = 0
       cvd_values = []
       
       for trade in trades_data:
           if trade['side'] == 'Buy':
               # Агрессивная покупка (buyer initiated)
               cvd += trade['volume']
           else:
               # Агрессивная продажа (seller initiated)
               cvd -= trade['volume']
           
           cvd_values.append(cvd)
       
       return cvd_values
   
   
   def detect_cvd_divergence(prices: List[float], cvd: List[float], 
                            lookback: int = 20) -> Dict:
       """
       Поиск дивергенций между ценой и CVD
       
       Bullish Divergence: Price ↓, CVD ↑ = Absorption
       Bearish Divergence: Price ↑, CVD ↓ = Distribution
       
       Args:
           prices: Список цен закрытия
           cvd: Список CVD значений
           lookback: Период для поиска дивергенций
       
       Returns:
           Dict с информацией о дивергенции
       """
       if len(prices) < lookback or len(cvd) < lookback:
           return {'divergence': None}
       
       # Последние значения
       recent_prices = prices[-lookback:]
       recent_cvd = cvd[-lookback:]
       
       # Тренд цены
       price_trend = 'down' if recent_prices[-1] < recent_prices[0] else 'up'
       
       # Тренд CVD
       cvd_trend = 'down' if recent_cvd[-1] < recent_cvd[0] else 'up'
       
       # Проверка дивергенции
       if price_trend == 'down' and cvd_trend == 'up':
           # Bullish divergence - цена падает, но агрессивных покупок больше
           return {
               'divergence': 'bullish',
               'type': 'absorption',
               'confidence': calculate_divergence_strength(recent_prices, recent_cvd),
               'signal': 'potential_reversal_up',
               'explanation': 'Price falling but buying pressure increasing (Absorption)'
           }
       
       elif price_trend == 'up' and cvd_trend == 'down':
           # Bearish divergence - цена растёт, но агрессивных продаж больше
           return {
               'divergence': 'bearish',
               'type': 'distribution',
               'confidence': calculate_divergence_strength(recent_prices, recent_cvd),
               'signal': 'potential_reversal_down',
               'explanation': 'Price rising but selling pressure increasing (Distribution)'
           }
       
       else:
           return {
               'divergence': None,
               'signal': 'aligned',
               'explanation': 'Price and CVD aligned'
           }
   
   
   def calculate_divergence_strength(prices: List[float], cvd: List[float]) -> float:
       """Рассчитать силу дивергенции (0-1)"""
       from scipy.stats import pearsonr
       
       # Корреляция между ценой и CVD
       correlation, _ = pearsonr(prices, cvd)
       
       # Сила дивергенции = 1 - abs(correlation)
       # Если корреляция отрицательная - сильная дивергенция
       strength = 1 - abs(correlation) if correlation < 0 else abs(correlation)
       
       return round(strength, 2)
   ```

2. Интегрировать в mcp_server/bybit_client.py:
   ```python
   async def get_recent_trades(self, symbol: str, limit: int = 1000) -> List[Dict]:
       """Получить последние трейды для CVD анализа"""
       try:
           response = await self.session.get_public_trade_history(
               category="linear",
               symbol=symbol,
               limit=limit
           )
           
           if response["retCode"] == 0:
               trades = []
               for trade in response["result"]["list"]:
                   trades.append({
                       'side': trade['side'],
                       'volume': float(trade['size']),
                       'price': float(trade['price']),
                       'timestamp': int(trade['time'])
                   })
               return trades
           
           return []
       
       except Exception as e:
           logger.error(f"Error getting trades: {e}")
           return []
   ```

3. Добавить в scan_market() и validate_entry():
   ```python
   # В scan_market()
   async def scan_market(criteria: Dict) -> List[Dict]:
       # ... существующий код ...
       
       # Добавить CVD анализ
       trades = await bybit_client.get_recent_trades(symbol)
       cvd = calculate_cvd(trades)
       prices = [t['price'] for t in trades]
       
       cvd_analysis = detect_cvd_divergence(prices, cvd)
       
       # Добавить к confluence score
       if cvd_analysis['divergence'] == 'bullish' and side == 'long':
           confluence_score += 0.5
           probability_boost = 0.05  # +5%
           
           opportunity['cvd_divergence'] = cvd_analysis
           opportunity['key_factors'].append('Bullish CVD Divergence (Absorption)')
       
       elif cvd_analysis['divergence'] == 'bearish' and side == 'short':
           confluence_score += 0.5
           probability_boost = 0.05
           
           opportunity['cvd_divergence'] = cvd_analysis
           opportunity['key_factors'].append('Bearish CVD Divergence (Distribution)')
   ```

4. Визуализация CVD (опционально):
   ```python
   def plot_cvd_divergence(prices, cvd, divergence_info):
       """Создать график CVD с дивергенцией"""
       import matplotlib.pyplot as plt
       
       fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
       
       # График цены
       ax1.plot(prices, label='Price', color='blue')
       ax1.set_title('Price')
       ax1.grid(True, alpha=0.3)
       
       # График CVD
       ax2.plot(cvd, label='CVD', color='green' if cvd[-1] > cvd[0] else 'red')
       ax2.set_title('Cumulative Volume Delta')
       ax2.grid(True, alpha=0.3)
       ax2.axhline(y=0, color='black', linestyle='--', alpha=0.5)
       
       # Отметить дивергенцию
       if divergence_info['divergence']:
           ax1.annotate(
               f"{divergence_info['divergence'].upper()} DIVERGENCE",
               xy=(len(prices)-1, prices[-1]),
               xytext=(len(prices)-20, prices[-1]),
               arrowprops=dict(arrowstyle='->', color='red', lw=2),
               fontsize=12,
               color='red'
           )
       
       plt.tight_layout()
       plt.savefig('cvd_analysis.png')
       plt.close()
   ```

ПРОВЕРКА:
1. CVD рассчитывается корректно
2. Дивергенции детектируются правильно
3. Confluence score увеличивается при подтверждении
4. Тесты проходят
5. Визуализация работает (опционально)

ФАЙЛЫ ДЛЯ ИЗМЕНЕНИЯ:
- mcp_server/technical_analysis.py (добавить CVD методы)
- mcp_server/bybit_client.py (добавить get_recent_trades)
- mcp_server/market_scanner.py (интегрировать CVD)
- tests/test_cvd.py (новый)

КРИТИЧНОСТЬ: P0 - КРИТИЧНО для точности
ВРЕМЯ: 4-6 часов
ЭФФЕКТ: +10-15% точности сигналов
```

---

## 🟡 ВАЖНЫЕ ПРОБЛЕМЫ (P1)

### ПРОМПТ 6: Внедрить кэширование (Redis)

```
КОНТЕКСТ:
Система делает избыточные API запросы без кэширования, что приводит к:
- Медленному повторному анализу (5-8 сек → можно 2-3 сек)
- Избыточной нагрузке на Bybit API
- Плохому UX

ЗАДАЧА:
Внедрить Redis кэширование для всех часто запрашиваемых данных.

ТРЕБОВАНИЯ:

1. Установить Redis:
   ```bash
   # Mac
   brew install redis
   brew services start redis
   
   # Ubuntu
   sudo apt-get install redis-server
   sudo systemctl start redis
   
   # Проверить
   redis-cli ping
   # Должно вернуть: PONG
   ```

2. Установить Python библиотеку:
   ```bash
   pip install redis
   pip install hiredis  # для производительности
   ```

3. Создать mcp_server/cache_manager.py:
   ```python
   import redis
   import json
   import hashlib
   import logging
   from typing import Any, Optional
   from functools import wraps
   
   logger = logging.getLogger(__name__)
   
   
   class CacheManager:
       """Менеджер кэширования для MCP сервера"""
       
       def __init__(self, host='localhost', port=6379, db=0, default_ttl=60):
           """
           Args:
               host: Redis host
               port: Redis port
               db: Database number
               default_ttl: Default TTL в секундах
           """
           try:
               self.redis_client = redis.StrictRedis(
                   host=host,
                   port=port,
                   db=db,
                   decode_responses=True,
                   socket_timeout=5,
                   socket_connect_timeout=5
               )
               
               # Проверить подключение
               self.redis_client.ping()
               self.enabled = True
               logger.info("Redis cache enabled")
           
           except redis.ConnectionError:
               logger.warning("Redis not available, caching disabled")
               self.enabled = False
               self.redis_client = None
           
           self.default_ttl = default_ttl
       
       
       def cache_key(self, prefix: str, **kwargs) -> str:
           """
           Генерация ключа кэша
           
           Args:
               prefix: Префикс ключа (например, "kline", "ticker")
               **kwargs: Параметры для ключа
           
           Returns:
               Уникальный ключ кэша
           """
           # Сортировать параметры для консистентности
           params_str = '_'.join(f"{k}={v}" for k, v in sorted(kwargs.items()))
           
           # Хэшировать если слишком длинный
           if len(params_str) > 100:
               params_hash = hashlib.md5(params_str.encode()).hexdigest()
               return f"mcp:{prefix}:{params_hash}"
           
           return f"mcp:{prefix}:{params_str}"
       
       
       def get(self, key: str) -> Optional[Any]:
           """Получить из кэша"""
           if not self.enabled:
               return None
           
           try:
               data = self.redis_client.get(key)
               if data:
                   return json.loads(data)
               return None
           
           except Exception as e:
               logger.error(f"Cache get error: {e}")
               return None
       
       
       def set(self, key: str, value: Any, ttl: Optional[int] = None):
           """Сохранить в кэш"""
           if not self.enabled:
               return
           
           try:
               ttl = ttl or self.default_ttl
               self.redis_client.setex(
                   key,
                   ttl,
                   json.dumps(value)
               )
           
           except Exception as e:
               logger.error(f"Cache set error: {e}")
       
       
       def delete(self, key: str):
           """Удалить из кэша"""
           if not self.enabled:
               return
           
           try:
               self.redis_client.delete(key)
           except Exception as e:
               logger.error(f"Cache delete error: {e}")
       
       
       def clear_pattern(self, pattern: str):
           """Удалить все ключи по паттерну"""
           if not self.enabled:
               return
           
           try:
               keys = self.redis_client.keys(pattern)
               if keys:
                   self.redis_client.delete(*keys)
           except Exception as e:
               logger.error(f"Cache clear error: {e}")
       
       
       def cached(self, ttl: Optional[int] = None, prefix: str = "func"):
           """
           Декоратор для кэширования результатов функции
           
           Usage:
               @cache_manager.cached(ttl=120, prefix="analyze")
               async def analyze_asset(symbol, timeframe):
                   # ... expensive operation ...
                   return result
           """
           def decorator(func):
               @wraps(func)
               async def wrapper(*args, **kwargs):
                   # Сгенерировать ключ из аргументов
                   cache_key = self.cache_key(
                       prefix=f"{prefix}_{func.__name__}",
                       args=str(args),
                       kwargs=str(kwargs)
                   )
                   
                   # Проверить кэш
                   cached_result = self.get(cache_key)
                   if cached_result is not None:
                       logger.debug(f"Cache HIT: {cache_key}")
                       return cached_result
                   
                   # Выполнить функцию
                   logger.debug(f"Cache MISS: {cache_key}")
                   result = await func(*args, **kwargs)
                   
                   # Сохранить в кэш
                   self.set(cache_key, result, ttl)
                   
                   return result
               
               return wrapper
           return decorator
   
   
   # Глобальный экземпляр
   cache_manager = CacheManager(default_ttl=60)
   ```

4. Интегрировать в существующие функции:
   ```python
   # В mcp_server/market_scanner.py
   
   from cache_manager import cache_manager
   
   @cache_manager.cached(ttl=120, prefix="analyze")
   async def analyze_asset(symbol: str, timeframes: List[str]) -> Dict:
       """Анализ с кэшированием на 2 минуты"""
       # ... существующий код ...
       return result
   
   
   # В mcp_server/bybit_client.py
   
   @cache_manager.cached(ttl=30, prefix="ticker")
   async def get_ticker(self, symbol: str) -> Dict:
       """Тикер с кэшированием на 30 секунд"""
       # ... существующий код ...
       return ticker
   
   
   @cache_manager.cached(ttl=60, prefix="kline")
   async def get_klines(self, symbol: str, interval: str, limit: int) -> List:
       """Свечи с кэшированием на 1 минуту"""
       # ... существующий код ...
       return klines
   
   
   # В mcp_server/technical_analysis.py
   
   @cache_manager.cached(ttl=90, prefix="indicators")
   async def calculate_indicators(self, symbol: str, timeframe: str) -> Dict:
       """Индикаторы с кэшированием на 1.5 минуты"""
       # ... существующий код ...
       return indicators
   ```

5. Добавить статистику кэша:
   ```python
   def get_cache_stats(self) -> Dict:
       """Получить статистику кэша"""
       if not self.enabled:
           return {"enabled": False}
       
       try:
           info = self.redis_client.info('stats')
           
           return {
               "enabled": True,
               "total_commands": info.get('total_commands_processed', 0),
               "keyspace_hits": info.get('keyspace_hits', 0),
               "keyspace_misses": info.get('keyspace_misses', 0),
               "hit_rate": info.get('keyspace_hits', 0) / 
                          max(info.get('keyspace_hits', 0) + info.get('keyspace_misses', 0), 1)
           }
       
       except Exception as e:
           logger.error(f"Error getting cache stats: {e}")
           return {"enabled": True, "error": str(e)}
   ```

6. Создать тесты:
   ```python
   # tests/test_cache.py
   
   import pytest
   from mcp_server.cache_manager import CacheManager
   
   @pytest.fixture
   def cache():
       return CacheManager()
   
   def test_cache_set_get(cache):
       cache.set("test_key", {"value": 123}, ttl=10)
       result = cache.get("test_key")
       assert result == {"value": 123}
   
   def test_cache_ttl(cache):
       import time
       cache.set("test_ttl", "value", ttl=1)
       time.sleep(2)
       assert cache.get("test_ttl") is None
   
   @pytest.mark.asyncio
   async def test_cached_decorator(cache):
       call_count = 0
       
       @cache.cached(ttl=10, prefix="test")
       async def expensive_function(x):
           nonlocal call_count
           call_count += 1
           return x * 2
       
       result1 = await expensive_function(5)
       result2 = await expensive_function(5)
       
       assert result1 == 10
       assert result2 == 10
       assert call_count == 1  # Вызвана только один раз
   ```

ПРОВЕРКА:
1. Redis запущен и доступен
2. Cache manager работает
3. Повторные запросы используют кэш
4. TTL работает корректно
5. Статистика показывает high hit rate (>60%)
6. Время анализа сократилось на 40-60%

ФАЙЛЫ ДЛЯ СОЗДАНИЯ/ИЗМЕНЕНИЯ:
- mcp_server/cache_manager.py (новый)
- mcp_server/market_scanner.py (добавить декораторы)
- mcp_server/bybit_client.py (добавить декораторы)
- mcp_server/technical_analysis.py (добавить декораторы)
- tests/test_cache.py (новый)

КРИТИЧНОСТЬ: P1 - ВАЖНО
ВРЕМЯ: 4-6 часов
ЭФФЕКТ: -40-60% времени анализа
```

---

### ПРОМПТ 7: Историческая статистика паттернов

```
КОНТЕКСТ:
Система находит паттерны (голова-плечи, треугольники, флаги) но не знает их исторический success rate. Это делает probability estimation менее точной.

ЗАДАЧА:
Создать SQLite базу для хранения результатов каждого паттерна и использовать статистику для улучшения оценки вероятности.

ТРЕБОВАНИЯ:

1. Создать mcp_server/pattern_database.py:
   ```python
   import sqlite3
   import logging
   from typing import Dict, List, Optional
   from datetime import datetime
   from pathlib import Path
   
   logger = logging.getLogger(__name__)
   
   
   class PatternDatabase:
       """База данных для хранения статистики паттернов"""
       
       def __init__(self, db_path: str = "data/pattern_stats.db"):
           """
           Args:
               db_path: Путь к SQLite базе
           """
           # Создать директорию если нужно
           Path(db_path).parent.mkdir(parents=True, exist_ok=True)
           
           self.db_path = db_path
           self.conn = sqlite3.connect(db_path)
           self.conn.row_factory = sqlite3.Row
           self._init_db()
         
       
       def _init_db(self):
           """Инициализация таблиц"""
           cursor = self.conn.cursor()
           
           # Таблица обнаруженных паттернов
           cursor.execute("""
               CREATE TABLE IF NOT EXISTS patterns (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   pattern_type TEXT NOT NULL,
                   pattern_name TEXT NOT NULL,
                   symbol TEXT NOT NULL,
                   timeframe TEXT NOT NULL,
                   entry_price REAL,
                   stop_loss REAL,
                   take_profit REAL,
                   exit_price REAL,
                   result TEXT,  -- 'win', 'loss', 'breakeven'
                   profit_pct REAL,
                   date_detected TIMESTAMP,
                   date_closed TIMESTAMP,
                   confluence_score REAL,
                   probability_estimated REAL,
                   metadata TEXT,  -- JSON с доп. данными
                   UNIQUE(pattern_name, symbol, timeframe, date_detected)
               )
           """)
           
           # Таблица агрегированной статистики
           cursor.execute("""
               CREATE TABLE IF NOT EXISTS pattern_stats (
                   pattern_type TEXT,
                   pattern_name TEXT,
                   timeframe TEXT,
                   total_count INTEGER,
                   win_count INTEGER,
                   loss_count INTEGER,
                   breakeven_count INTEGER,
                   avg_profit_pct REAL,
                   avg_loss_pct REAL,
                   win_rate REAL,
                   avg_hold_time_hours REAL,
                   last_updated TIMESTAMP,
                   PRIMARY KEY (pattern_type, pattern_name, timeframe)
               )
           """)
           
           # Индексы для быстрого поиска
           cursor.execute("""
               CREATE INDEX IF NOT EXISTS idx_patterns_symbol_tf 
               ON patterns(symbol, timeframe)
           """)
           
           cursor.execute("""
               CREATE INDEX IF NOT EXISTS idx_patterns_result 
               ON patterns(result)
           """)
           
           self.conn.commit()
       
       
       def record_pattern(
           self,
           pattern_type: str,
           pattern_name: str,
           symbol: str,
           timeframe: str,
           entry_price: float,
           stop_loss: float,
           take_profit: float,
           confluence_score: float,
           probability: float,
           metadata: Optional[Dict] = None
       ) -> int:
           """
           Записать обнаруженный паттерн
           
           Returns:
               ID записи
           """
           cursor = self.conn.cursor()
           
           try:
               cursor.execute("""
                   INSERT INTO patterns 
                   (pattern_type, pattern_name, symbol, timeframe, 
                    entry_price, stop_loss, take_profit,
                    date_detected, confluence_score, probability_estimated, metadata)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
               """, (
                   pattern_type,
                   pattern_name,
                   symbol,
                   timeframe,
                   entry_price,
                   stop_loss,
                   take_profit,
                   datetime.now(),
                   confluence_score,
                   probability,
                   json.dumps(metadata) if metadata else None
               ))
               
               self.conn.commit()
               return cursor.lastrowid
           
           except sqlite3.IntegrityError:
               logger.warning(f"Pattern already recorded: {pattern_name} on {symbol} {timeframe}")
               return -1
       
       
       def update_pattern_result(
           self,
           pattern_id: int,
           exit_price: float,
           result: str,  # 'win', 'loss', 'breakeven'
           profit_pct: float
       ):
           """Обновить результат паттерна после закрытия позиции"""
           cursor = self.conn.cursor()
           
           cursor.execute("""
               UPDATE patterns
               SET exit_price = ?,
                   result = ?,
                   profit_pct = ?,
                   date_closed = ?
               WHERE id = ?
           """, (exit_price, result, profit_pct, datetime.now(), pattern_id))
           
           self.conn.commit()
           
           # Обновить статистику
           self._update_stats()
       
       
       def get_pattern_stats(
           self,
           pattern_name: str,
           timeframe: str
       ) -> Optional[Dict]:
           """Получить статистику паттерна"""
           cursor = self.conn.cursor()
           
           cursor.execute("""
               SELECT *
               FROM pattern_stats
               WHERE pattern_name = ? AND timeframe = ?
           """, (pattern_name, timeframe))
           
           row = cursor.fetchone()
           
           if row:
               return dict(row)
           
           return None
       
       
       def _update_stats(self):
           """Обновить агрегированную статистику"""
           cursor = self.conn.cursor()
           
           cursor.execute("""
               INSERT OR REPLACE INTO pattern_stats
               SELECT 
                   pattern_type,
                   pattern_name,
                   timeframe,
                   COUNT(*) as total_count,
                   SUM(CASE WHEN result = 'win' THEN 1 ELSE 0 END) as win_count,
                   SUM(CASE WHEN result = 'loss' THEN 1 ELSE 0 END) as loss_count,
                   SUM(CASE WHEN result = 'breakeven' THEN 1 ELSE 0 END) as breakeven_count,
                   AVG(CASE WHEN result = 'win' THEN profit_pct END) as avg_profit_pct,
                   AVG(CASE WHEN result = 'loss' THEN profit_pct END) as avg_loss_pct,
                   CAST(SUM(CASE WHEN result = 'win' THEN 1 ELSE 0 END) AS FLOAT) / COUNT(*) as win_rate,
                   AVG(CASE 
                       WHEN date_closed IS NOT NULL 
                       THEN (julianday(date_closed) - julianday(date_detected)) * 24 
                   END) as avg_hold_time_hours,
                   datetime('now') as last_updated
               FROM patterns
               WHERE result IS NOT NULL
               GROUP BY pattern_type, pattern_name, timeframe
           """)
           
           self.conn.commit()
       
       
       def get_top_patterns(self, min_count: int = 10, limit: int = 10) -> List[Dict]:
           """Получить топ паттернов по win rate"""
           cursor = self.conn.cursor()
           
           cursor.execute("""
               SELECT *
               FROM pattern_stats
               WHERE total_count >= ?
               ORDER BY win_rate DESC, total_count DESC
               LIMIT ?
           """, (min_count, limit))
           
           return [dict(row) for row in cursor.fetchall()]
       
       
       def close(self):
           """Закрыть соединение"""
           self.conn.close()
   
   
   # Глобальный экземпляр
   pattern_db = PatternDatabase()
   ```

2. Интегрировать в detect_patterns():
   ```python
   # В mcp_server/technical_analysis.py
   
   from pattern_database import pattern_db
   
   async def detect_patterns(
       symbol: str,
       timeframe: str,
       klines: List,
       pattern_types: List[str] = None
   ) -> List[Dict]:
       """Обнаружение паттернов с исторической статистикой"""
       
       # ... существующий код обнаружения паттернов ...
       
       detected_patterns = []
       
       for pattern in raw_patterns:
           pattern_name = pattern['name']
           
           # Получить историческую статистику
           stats = pattern_db.get_pattern_stats(pattern_name, timeframe)
           
           if stats and stats['total_count'] >= 10:
               # Есть достаточно данных
               historical_win_rate = stats['win_rate']
               historical_avg_profit = stats['avg_profit_pct']
               
               # Boost confidence на основе исторических данных
               if historical_win_rate > 0.75:
                   confidence_boost = 0.15
               elif historical_win_rate > 0.65:
                   confidence_boost = 0.10
               elif historical_win_rate > 0.50:
                   confidence_boost = 0.05
               else:
                   confidence_boost = -0.10  # Penalize плохие паттерны
               
               pattern['confidence'] = min(0.95, pattern.get('confidence', 0.70) + confidence_boost)
               pattern['historical_win_rate'] = historical_win_rate
               pattern['historical_avg_profit'] = historical_avg_profit
               pattern['sample_size'] = stats['total_count']
           
           else:
               # Недостаточно данных - default confidence
               pattern['confidence'] = 0.70
               pattern['historical_win_rate'] = None
               pattern['historical_avg_profit'] = None
               pattern['sample_size'] = stats['total_count'] if stats else 0
           
           detected_patterns.append(pattern)
       
       return detected_patterns
   ```

3. Интегрировать в validate_entry():
   ```python
   # В mcp_server/market_scanner.py
   
   async def validate_entry(...):
       # ... существующая валидация ...
       
       # Записать паттерн в базу
       if pattern_name:
           pattern_id = pattern_db.record_pattern(
               pattern_type=pattern_type,
               pattern_name=pattern_name,
               symbol=symbol,
               timeframe=main_timeframe,
               entry_price=entry_price,
               stop_loss=stop_loss,
               take_profit=take_profit,
               confluence_score=confluence_score,
               probability=base_probability,
               metadata={
                   'indicators': indicators,
                   'market_structure': market_structure,
                   'side': side
               }
           )
           
           # Сохранить ID для последующего обновления
           result['pattern_record_id'] = pattern_id
       
       # Historical pattern boost
       if pattern_stats and pattern_stats['total_count'] >= 10:
           historical_win_rate = pattern_stats['win_rate']
           
           if historical_win_rate > 0.75:
               probability_boost = (historical_win_rate - 0.70) * 0.3
               final_probability += probability_boost
       
       return result
   ```

4. Обновление результата после закрытия:
   ```python
   # Добавить метод для обновления после выхода
   async def update_pattern_result_after_exit(
       pattern_id: int,
       exit_price: float,
       entry_price: float,
       side: str
   ):
       """Обновить результат паттерна после закрытия позиции"""
       
       # Рассчитать profit%
       if side == 'long':
           profit_pct = ((exit_price - entry_price) / entry_price) * 100
       else:
           profit_pct = ((entry_price - exit_price) / entry_price) * 100
       
       # Определить result
       if profit_pct > 0.5:
           result = 'win'
       elif profit_pct < -0.5:
           result = 'loss'
       else:
           result = 'breakeven'
       
       # Обновить в базе
       pattern_db.update_pattern_result(
           pattern_id=pattern_id,
           exit_price=exit_price,
           result=result,
           profit_pct=profit_pct
       )
       
       logger.info(f"Pattern #{pattern_id} result: {result} ({profit_pct:+.2f}%)")
   ```

ПРОВЕРКА:
1. База данных создаётся корректно
2. Паттерны записываются при обнаружении
3. Результаты обновляются после закрытия
4. Статистика агрегируется правильно
5. Confidence boost работает для успешных паттернов
6. Win rate > 65% после накопления данных

ФАЙЛЫ ДЛЯ СОЗДАНИЯ/ИЗМЕНЕНИЯ:
- mcp_server/pattern_database.py (новый)
- mcp_server/technical_analysis.py (интеграция)
- mcp_server/market_scanner.py (интеграция)
- tests/test_pattern_db.py (новый)

КРИТИЧНОСТЬ: P1 - ВАЖНО
ВРЕМЯ: 1-2 дня
ЭФФЕКТ: +15-20% точности probability
```

---

## 📋 ПОРЯДОК ВЫПОЛНЕНИЯ

### Фаза 1: Критические исправления (Week 1)

1. **День 1-2:** ПРОМПТ 1 - Отозвать ключи, очистить Git историю
2. **День 2-3:** ПРОМПТ 2-3 - Исправить hardcoded значения
3. **День 3-5:** ПРОМПТ 4 - Создать Trading MCP Server
4. **День 5-7:** ПРОМПТ 5 - Внедрить Order Flow (CVD)

### Фаза 2: Важные улучшения (Week 2-4)

1. **Неделя 2:** ПРОМПТ 6 - Кэширование
2. **Неделя 3:** ПРОМПТ 7 - Статистика паттернов
3. **Неделя 4:** Остальные P1 промпты

---

## ✅ TRACKING CHECKLIST

### 🔴 Критические (P0)
- [ ] P0-1: Утечка API ключей устранена
- [ ] P0-2: Hardcoded баланс исправлен
- [ ] P0-3: Fake R:R scoring исправлен
- [ ] P0-4: Trading MCP Server создан
- [ ] P0-5: Order Flow (CVD) реализован

### 🟡 Важные (P1)
- [ ] P1-1: Кэширование внедрено
- [ ] P1-2: Статистика паттернов работает
- [ ] P1-3: Batch-операции реализованы (см. SYSTEM_DEEP_REVIEW_REPORT.md)
- [ ] P1-4: Проверка ликвидности автоматическая
- [ ] P1-5: Volatility targeting внедрён
- [ ] P1-6: Parabolic SAR добавлен

### 🟢 Желательные (P2)
- [ ] P2-1: On-chain данные интегрированы
- [ ] P2-2: Sentiment анализ добавлен
- [ ] P2-3: Fibonacci auto-calc
- [ ] P2-4: Адаптивное обучение

---

**Дата создания:** 2025-11-19  
**Версия:** 1.0  
**Статус:** ✅ Готово к использованию

*Каждый промпт можно копировать целиком и использовать для исправления соответствующей проблемы.*