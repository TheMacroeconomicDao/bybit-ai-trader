# 🔧 ПОДРОБНЫЙ ПРОМПТ ДЛЯ ИСПРАВЛЕНИЯ AUTONOMOUS AGENT

**Дата создания:** 2025-01-20  
**Связанный документ:** [AGENT_SYSTEM_RESEARCH.md](AGENT_SYSTEM_RESEARCH.md)  
**Цель:** Превратить изолированные компоненты в единую полнофункциональную систему

---

## 📋 КРАТКОЕ РЕЗЮМЕ ПРОБЛЕМ

**Основная проблема:** Autonomous Agent работает ИЗОЛИРОВАННО от остальной системы.

**Критические разрывы:**
1. ❌ Агент НЕ доступен через Cursor MCP
2. ❌ Агент НЕ интегрирован с WebUI
3. ❌ Агент НЕ использует 35 MCP инструментов
4. ❌ Агент НЕ может открывать позиции
5. ❌ Нет автоматического расписания публикаций

---

## 🎯 ЦЕЛЬ ИСПРАВЛЕНИЙ

Создать **Unified Autonomous Trading System**, где:
- ✅ Агент доступен через Cursor как MCP инструмент
- ✅ Агент использует все 35 MCP инструментов
- ✅ Агент интегрирован с WebUI
- ✅ Агент может открывать и управлять позициями
- ✅ Автоматическая публикация по расписанию
- ✅ Единая точка взаимодействия для пользователя

---

## 🔴 ПРИОРИТЕТ 1: UNIFIED AGENT MCP SERVER

### Проблема
Autonomous Agent - это standalone скрипт, недоступный через Cursor MCP.

### Решение
Создать MCP server wrapper для autonomous agent.

### Реализация

#### Шаг 1.1: Создать `mcp_server/autonomous_agent_server.py`

```python
#!/usr/bin/env python3
"""
Autonomous Agent MCP Server
Обертка для autonomous agent с доступом через MCP
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Any, List, Dict
from datetime import datetime

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from loguru import logger

# Импорт autonomous agent компонентов
sys.path.insert(0, str(Path(__file__).parent.parent))
from autonomous_agent.autonomous_analyzer import AutonomousAnalyzer
from autonomous_agent.telegram_formatter import TelegramFormatter
from mcp_server.telegram_bot import TelegramBot

# Настройка логирования
logger.remove()
logger.add(sys.stderr, level="INFO")
logger.add("logs/autonomous_agent_server_{time}.log", rotation="1 day", retention="7 days")

# Инициализация MCP сервера
app = Server("autonomous-trading-agent")

# Глобальные переменные
analyzer: AutonomousAnalyzer = None
formatter = TelegramFormatter()
last_analysis_result: Dict[str, Any] = None


def load_config() -> Dict[str, Any]:
    """Загрузка конфигурации"""
    import os
    
    config = {
        "qwen_api_key": os.getenv("QWEN_API_KEY", ""),
        "bybit_api_key": os.getenv("BYBIT_API_KEY", ""),
        "bybit_api_secret": os.getenv("BYBIT_API_SECRET", ""),
        "qwen_model": os.getenv("QWEN_MODEL", "qwen/qwen-turbo"),
        "testnet": os.getenv("BYBIT_TESTNET", "false").lower() == "true",
        "telegram_bot_token": os.getenv("TELEGRAM_BOT_TOKEN", ""),
        "telegram_chat_ids": os.getenv("TELEGRAM_CHAT_IDS", "")
    }
    
    # Проверка обязательных параметров
    required = ["qwen_api_key", "bybit_api_key", "bybit_api_secret"]
    missing = [k for k in required if not config[k]]
    
    if missing:
        raise ValueError(f"Missing required config: {', '.join(missing)}")
    
    return config


@app.list_tools()
async def list_tools() -> List[Tool]:
    """Список доступных инструментов"""
    return [
        Tool(
            name="analyze_market_comprehensive",
            description=(
                "Запустить ПОЛНЫЙ анализ рынка с помощью autonomous agent. "
                "Находит ТОП-3 LONG и ТОП-3 SHORT возможности с confluence ≥8.0/10, "
                "вероятностью ≥70%, R:R ≥1:2. Использует Qwen AI для интеллектуального анализа."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "save_to_file": {
                        "type": "boolean",
                        "default": True,
                        "description": "Сохранить результаты в data/latest_analysis.json"
                    },
                    "publish_to_telegram": {
                        "type": "boolean",
                        "default": False,
                        "description": "Опубликовать результаты в Telegram"
                    },
                    "track_signals": {
                        "type": "boolean",
                        "default": True,
                        "description": "Записать сигналы в signal tracker для контроля качества"
                    }
                }
            }
        ),
        
        Tool(
            name="get_last_analysis",
            description="Получить результаты последнего анализа рынка (если есть)",
            inputSchema={
                "type": "object",
                "properties": {
                    "format": {
                        "type": "string",
                        "enum": ["json", "telegram", "summary"],
                        "default": "summary",
                        "description": "Формат вывода результатов"
                    }
                }
            }
        ),
        
        Tool(
            name="publish_analysis_to_telegram",
            description="Опубликовать результаты анализа в Telegram каналы",
            inputSchema={
                "type": "object",
                "properties": {
                    "use_last_analysis": {
                        "type": "boolean",
                        "default": True,
                        "description": "Использовать результаты последнего анализа"
                    },
                    "custom_message": {
                        "type": "string",
                        "description": "Кастомное сообщение (опционально)"
                    }
                }
            }
        ),
        
        Tool(
            name="configure_agent",
            description="Настроить параметры autonomous agent",
            inputSchema={
                "type": "object",
                "properties": {
                    "qwen_model": {
                        "type": "string",
                        "description": "Модель Qwen для использования"
                    },
                    "min_confluence": {
                        "type": "number",
                        "default": 8.0,
                        "description": "Минимальный confluence score для сигналов"
                    },
                    "min_probability": {
                        "type": "number",
                        "default": 0.70,
                        "description": "Минимальная вероятность успеха (0-1)"
                    }
                }
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> List[TextContent]:
    """Обработка вызовов инструментов"""
    global analyzer, last_analysis_result
    
    try:
        logger.info(f"Tool called: {name}")
        
        # Инициализация analyzer если нужно
        if analyzer is None:
            config = load_config()
            analyzer = AutonomousAnalyzer(
                qwen_api_key=config["qwen_api_key"],
                bybit_api_key=config["bybit_api_key"],
                bybit_api_secret=config["bybit_api_secret"],
                qwen_model=config["qwen_model"],
                testnet=config["testnet"]
            )
            logger.info("Autonomous Analyzer initialized")
        
        if name == "analyze_market_comprehensive":
            logger.info("Starting comprehensive market analysis...")
            
            # Запуск анализа
            result = await analyzer.analyze_market()
            last_analysis_result = result
            
            # Сохранение в файл
            if arguments.get("save_to_file", True):
                output_file = Path(__file__).parent.parent / "data" / "latest_analysis.json"
                output_file.parent.mkdir(parents=True, exist_ok=True)
                output_file.write_text(
                    json.dumps(result, ensure_ascii=False, indent=2),
                    encoding="utf-8"
                )
                logger.info(f"Results saved to {output_file}")
            
            # Публикация в Telegram
            if arguments.get("publish_to_telegram", False):
                config = load_config()
                if config["telegram_bot_token"] and config["telegram_chat_ids"]:
                    telegram_message = formatter.format_top_opportunities(result)
                    await publish_to_telegram(
                        config["telegram_bot_token"],
                        config["telegram_chat_ids"],
                        telegram_message
                    )
                else:
                    logger.warning("Telegram credentials not configured")
            
            # Форматирование ответа
            if result.get("success"):
                top_longs = result.get("top_3_longs", [])
                top_shorts = result.get("top_3_shorts", [])
                
                summary = {
                    "success": True,
                    "timestamp": result["timestamp"],
                    "market_summary": {
                        "total_scanned": result.get("total_scanned", 0),
                        "total_analyzed": result.get("total_analyzed", 0),
                        "longs_found": len(top_longs),
                        "shorts_found": len(top_shorts)
                    },
                    "top_longs": top_longs,
                    "top_shorts": top_shorts,
                    "telegram_formatted": formatter.format_top_opportunities(result)
                }
                
                return [TextContent(
                    type="text",
                    text=json.dumps(summary, ensure_ascii=False, indent=2)
                )]
            else:
                return [TextContent(
                    type="text",
                    text=json.dumps(result, ensure_ascii=False, indent=2)
                )]
        
        elif name == "get_last_analysis":
            if not last_analysis_result:
                return [TextContent(
                    type="text",
                    text=json.dumps({"success": False, "error": "No analysis available"})
                )]
            
            format_type = arguments.get("format", "summary")
            
            if format_type == "telegram":
                message = formatter.format_top_opportunities(last_analysis_result)
                return [TextContent(type="text", text=message)]
            elif format_type == "json":
                return [TextContent(
                    type="text",
                    text=json.dumps(last_analysis_result, ensure_ascii=False, indent=2)
                )]
            else:  # summary
                summary = {
                    "timestamp": last_analysis_result.get("timestamp"),
                    "longs_found": len(last_analysis_result.get("top_3_longs", [])),
                    "shorts_found": len(last_analysis_result.get("top_3_shorts", [])),
                    "top_longs": last_analysis_result.get("top_3_longs", []),
                    "top_shorts": last_analysis_result.get("top_3_shorts", [])
                }
                return [TextContent(
                    type="text",
                    text=json.dumps(summary, ensure_ascii=False, indent=2)
                )]
        
        elif name == "publish_analysis_to_telegram":
            config = load_config()
            
            if not config["telegram_bot_token"] or not config["telegram_chat_ids"]:
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "success": False,
                        "error": "Telegram credentials not configured"
                    })
                )]
            
            if arguments.get("custom_message"):
                message = arguments["custom_message"]
            elif arguments.get("use_last_analysis", True) and last_analysis_result:
                message = formatter.format_top_opportunities(last_analysis_result)
            else:
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "success": False,
                        "error": "No message to publish"
                    })
                )]
            
            results = await publish_to_telegram(
                config["telegram_bot_token"],
                config["telegram_chat_ids"],
                message
            )
            
            return [TextContent(
                type="text",
                text=json.dumps({"success": True, "results": results}, indent=2)
            )]
        
        elif name == "configure_agent":
            # TODO: Implement configuration updates
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "message": "Configuration updated",
                    "config": arguments
                })
            )]
        
        else:
            raise ValueError(f"Unknown tool: {name}")
    
    except Exception as e:
        logger.error(f"Error in tool {name}: {e}", exc_info=True)
        return [TextContent(
            type="text",
            text=json.dumps({
                "success": False,
                "error": str(e),
                "tool": name
            }, indent=2)
        )]


async def publish_to_telegram(bot_token: str, chat_ids_str: str, message: str):
    """Публикует сообщение в Telegram"""
    chat_ids = [cid.strip() for cid in chat_ids_str.split(",") if cid.strip()]
    
    if not chat_ids:
        logger.warning("No Telegram chat IDs provided")
        return []
    
    bot = TelegramBot(bot_token)
    
    try:
        results = []
        for chat_id in chat_ids:
            try:
                await bot.send_message(chat_id=chat_id, text=message)
                logger.info(f"Message sent to Telegram channel {chat_id}")
                results.append({"chat_id": chat_id, "success": True})
            except Exception as e:
                logger.error(f"Failed to send to {chat_id}: {e}")
                results.append({"chat_id": chat_id, "success": False, "error": str(e)})
        
        return results
    finally:
        await bot.close()


async def main():
    """Запуск Autonomous Agent MCP Server"""
    logger.info("=" * 60)
    logger.info("Starting Autonomous Trading Agent MCP Server")
    logger.info("=" * 60)
    
    # Проверка конфигурации
    try:
        config = load_config()
        logger.info("Configuration loaded successfully")
        logger.info(f"Qwen Model: {config['qwen_model']}")
        logger.info(f"Testnet: {config['testnet']}")
        logger.info(f"Telegram: {'Enabled' if config['telegram_bot_token'] else 'Disabled'}")
    except Exception as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    
    logger.info("=" * 60)
    logger.info("Server ready for connections")
    logger.info("Available tools: 4")
    logger.info("  - analyze_market_comprehensive")
    logger.info("  - get_last_analysis")
    logger.info("  - publish_analysis_to_telegram")
    logger.info("  - configure_agent")
    logger.info("=" * 60)
    
    # Запуск MCP server
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)
```

#### Шаг 1.2: Обновить Cursor MCP конфигурацию

Добавить в `CURSOR_MCP_CONFIG.json` (или Cursor settings):

```json
{
  "mcpServers": {
    "autonomous-agent": {
      "command": "python",
      "args": [
        "/Users/Gyber/GYBERNATY-ECOSYSTEM/TRADER-AGENT/mcp_server/autonomous_agent_server.py"
      ],
      "env": {
        "PYTHONPATH": "/Users/Gyber/GYBERNATY-ECOSYSTEM/TRADER-AGENT",
        "QWEN_API_KEY": "your_key_here",
        "BYBIT_API_KEY": "your_key_here",
        "BYBIT_API_SECRET": "your_secret_here",
        "TELEGRAM_BOT_TOKEN": "your_token_here",
        "TELEGRAM_CHAT_IDS": "your_chat_ids_here"
      }
    }
  }
}
```

#### Шаг 1.3: Тестирование

```bash
# Тест 1: Запуск MCP server вручную
python mcp_server/autonomous_agent_server.py

# Тест 2: Проверка в Cursor
# В Cursor:
1. Restart MCP servers
2. Проверить что "autonomous-agent" доступен
3. Вызвать: analyze_market_comprehensive
```

---

## 🔴 ПРИОРИТЕТ 2: ИНТЕГРАЦИЯ С MCP ИНСТРУМЕНТАМИ

### Проблема
Autonomous Agent дублирует функциональность MCP сервера вместо использования его инструментов.

### Решение
Рефакторинг [`autonomous_analyzer.py`](autonomous_agent/autonomous_analyzer.py:1) для использования MCP инструментов.

### Реализация

#### Шаг 2.1: Добавить MCP Client в AutonomousAnalyzer

Модифицировать `autonomous_agent/autonomous_analyzer.py`:

```python
# В начале файла добавить
from mcp_server.trading_operations import TradingOperations
from mcp_server.signal_tracker import SignalTracker

class AutonomousAnalyzer:
    def __init__(
        self,
        qwen_api_key: str,
        bybit_api_key: str,
        bybit_api_secret: str,
        qwen_model: str = "qwen/qwen-turbo",
        testnet: bool = False,
        signal_tracker: Optional[SignalTracker] = None,
        # ДОБАВИТЬ:
        trading_operations: Optional[TradingOperations] = None
    ):
        # ... существующий код ...
        
        # ДОБАВИТЬ:
        # Инициализация trading operations для полного доступа к MCP
        self.trading_ops = trading_operations or TradingOperations(
            bybit_api_key, bybit_api_secret, testnet
        )
        
        # Signal tracker для автоматической записи сигналов
        self.signal_tracker = signal_tracker or SignalTracker()
```

#### Шаг 2.2: Использовать validate_entry из MCP

Заменить логику валидации:

```python
async def _finalize_top_3_longs_and_shorts(
    self,
    candidates: List[Dict[str, Any]],
    qwen_analysis: Dict[str, Any]
) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Финализация топ 3 лонгов и топ 3 шортов"""
    
    # ... существующий код фильтрации ...
    
    # ДОБАВИТЬ: Валидация через MCP validate_entry
    validated_longs = []
    for opp in top_longs:
        try:
            validation = await self.technical_analysis.validate_entry(
                symbol=opp["symbol"],
                side="long",
                entry_price=opp["entry_price"],
                stop_loss=opp["stop_loss"],
                take_profit=opp["take_profit"]
            )
            
            if validation.get("is_valid"):
                opp["validation"] = validation
                opp["final_score"] = validation.get("score", opp.get("confluence_score", 0))
                validated_longs.append(opp)
        except Exception as e:
            logger.warning(f"Validation failed for {opp['symbol']}: {e}")
            continue
    
    # Аналогично для shorts
    validated_shorts = []
    for opp in top_shorts:
        # ... тот же код ...
    
    return validated_longs[:3], validated_shorts[:3]
```

#### Шаг 2.3: Автоматическая запись сигналов

Уже частично реализовано в [`autonomous_analyzer.py:190-212`](autonomous_agent/autonomous_analyzer.py:190), но нужно гарантировать что это всегда работает:

```python
# В analyze_market() после финализации топ-3
if self.signal_tracker:
    for signal in top_longs + top_shorts:
        try:
            signal_id = await self._record_signal_to_tracker(
                signal,
                signal.get("side", "long")
            )
            logger.info(f"Signal {signal_id} recorded for {signal['symbol']}")
        except Exception as e:
            logger.error(f"Failed to record signal: {e}")
```

---

## 🔴 ПРИОРИТЕТ 3: WEB UI ИНТЕГРАЦИЯ

### Проблема
WebUI не показывает результаты autonomous agent.

### Решение
1. Исправить TypeScript ошибки
2. Добавить endpoint для autonomous agent
3. Создать dashboard для отображения сигналов

### Реализация

#### Шаг 3.1: Добавить API endpoint в HTTP server

Модифицировать `bybit-mcp/build/httpServer.js` (или создать новый):

```javascript
// Добавить новый endpoint
app.get('/api/autonomous-agent/latest', async (req, res) => {
  try {
    const fs = require('fs').promises;
    const path = require('path');
    
    const analysisPath = path.join(
      __dirname,
      '..',
      '..',
      'data',
      'latest_analysis.json'
    );
    
    const data = await fs.readFile(analysisPath, 'utf8');
    const analysis = JSON.parse(data);
    
    res.json({
      success: true,
      data: analysis
    });
  } catch (error) {
    res.status(404).json({
      success: false,
      error: 'No analysis available'
    });
  }
});

app.get('/api/autonomous-agent/signals', async (req, res) => {
  try {
    // TODO: Получить сигналы из signal_tracker
    res.json({
      success: true,
      signals: []
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});
```

#### Шаг 3.2: Создать React компонент для autonomous agent

Создать `bybit-mcp/webui/src/components/AutonomousAgent.tsx`:

```typescript
import React, { useEffect, useState } from 'react';

interface Signal {
  symbol: string;
  side: 'long' | 'short';
  entry_price: number;
  stop_loss: number;
  take_profit: number;
  confluence_score: number;
  probability: number;
  reasoning: string;
}

interface AnalysisResult {
  timestamp: string;
  top_3_longs: Signal[];
  top_3_shorts: Signal[];
  market_overview: any;
}

export function AutonomousAgent() {
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    loadLatestAnalysis();
    const interval = setInterval(loadLatestAnalysis, 60000); // Refresh every minute
    return () => clearInterval(interval);
  }, []);
  
  async function loadLatestAnalysis() {
    try {
      const response = await fetch('/api/autonomous-agent/latest');
      const data = await response.json();
      
      if (data.success) {
        setAnalysis(data.data);
      }
    } catch (error) {
      console.error('Failed to load analysis:', error);
    } finally {
      setLoading(false);
    }
  }
  
  if (loading) return <div>Loading...</div>;
  if (!analysis) return <div>No analysis available</div>;
  
  return (
    <div className="autonomous-agent">
      <h2>🤖 Autonomous Agent Analysis</h2>
      <p className="timestamp">Last updated: {new Date(analysis.timestamp).toLocaleString()}</p>
      
      <div className="signals-grid">
        <div className="signals-section">
          <h3>🟢 TOP 3 LONGS</h3>
          {analysis.top_3_longs.map((signal, i) => (
            <SignalCard key={i} signal={signal} rank={i + 1} />
          ))}
        </div>
        
        <div className="signals-section">
          <h3>🔴 TOP 3 SHORTS</h3>
          {analysis.top_3_shorts.map((signal, i) => (
            <SignalCard key={i} signal={signal} rank={i + 1} />
          ))}
        </div>
      </div>
    </div>
  );
}

function SignalCard({ signal, rank }: { signal: Signal; rank: number }) {
  return (
    <div className="signal-card">
      <div className="signal-header">
        <span className="rank">#{rank}</span>
        <span className="symbol">{signal.symbol}</span>
        <span className={`side ${signal.side}`}>{signal.side.toUpperCase()}</span>
      </div>
      
      <div className="signal-metrics">
        <div className="metric">
          <label>Confluence:</label>
          <span className="value">{signal.confluence_score}/10</span>
        </div>
        <div className="metric">
          <label>Probability:</label>
          <span className="value">{(signal.probability * 100).toFixed(0)}%</span>
        </div>
      </div>
      
      <div className="signal-prices">
        <div className="price">Entry: ${signal.entry_price}</div>
        <div className="price">SL: ${signal.stop_loss}</div>
        <div className="price">TP: ${signal.take_profit}</div>
      </div>
      
      <div className="signal-reasoning">
        <p>{signal.reasoning}</p>
      </div>
    </div>
  );
}
```

#### Шаг 3.3: Добавить в главное приложение

В `bybit-mcp/webui/src/App.tsx`:

```typescript
import { AutonomousAgent } from './components/AutonomousAgent';

function App() {
  return (
    <div className="app">
      <header>
        <h1>Trading Agent Dashboard</h1>
      </header>
      
      <main>
        <AutonomousAgent />
        {/* ... остальные компоненты ... */}
      </main>
    </div>
  );
}
```

---

## 🟡 ПРИОРИТЕТ 4: АВТОМАТИЗАЦИЯ ПУБЛИКАЦИЙ

### Проблема
Нет автоматического расписания для анализа и публикации.

### Решение
Настроить Kubernetes CronJob или системный cron для регулярного запуска.

### Реализация

#### Вариант А: Kubernetes CronJob

Создать `k8s/autonomous-agent-cronjob.yaml`:

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: autonomous-agent-analysis
  namespace: trading-agent
spec:
  # Каждые 30 минут (можно настроить)
  schedule: "*/30 * * * *"
  
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: analyzer
            image: trading-agent:latest
            command:
            - python
            - -m
            - autonomous_agent.main
            
            env:
            - name: QWEN_API_KEY
              valueFrom:
                secretKeyRef:
                  name: trading-secrets
                  key: qwen-api-key
            
            - name: BYBIT_API_KEY
              valueFrom:
                secretKeyRef:
                  name: trading-secrets
                  key: bybit-api-key
            
            - name: BYBIT_API_SECRET
              valueFrom:
                secretKeyRef:
                  name: trading-secrets
                  key: bybit-api-secret
            
            - name: TELEGRAM_BOT_TOKEN
              valueFrom:
                secretKeyRef:
                  name: trading-secrets
                  key: telegram-bot-token
            
            - name: TELEGRAM_CHAT_IDS
              valueFrom:
                secretKeyRef:
                  name: trading-secrets
                  key: telegram-chat-ids
            
            - name: QWEN_MODEL
              value: "qwen/qwen-turbo"
            
            - name: BYBIT_TESTNET
              value: "false"
            
            volumeMounts:
            - name: data
              mountPath: /app/data
            
          volumes:
          - name: data
            persistentVolumeClaim:
              claimName: trading-agent-data
          
          restartPolicy: OnFailure
```

#### Вариант Б: Системный cron

Создать `scripts/run_autonomous_agent.sh`:

```bash
#!/bin/bash

# Load environment variables
source /Users/Gyber/GYBERNATY-ECOSYSTEM/TRADER-AGENT/load_env.sh

# Activate virtual environment
source /Users/Gyber/GYBERNATY-ECOSYSTEM/TRADER-AGENT/venv/bin/activate

# Run autonomous agent
cd /Users/Gyber/GYBERNATY-ECOSYSTEM/TRADER-AGENT
python -m autonomous_agent.main

# Log result
echo "[$(date)] Autonomous agent executed" >> logs/cron.log
```

Добавить в crontab:

```bash
# Edit crontab
crontab -e

# Add line (каждые 30 минут)
*/30 * * * * /Users/Gyber/GYBERNATY-ECOSYSTEM/TRADER-AGENT/scripts/run_autonomous_agent.sh
```

---

## 🟡 ПРИОРИТЕТ 5: УНИФИКАЦИЯ КОНФИГУРАЦИИ

### Проблема
Множественные источники конфигурации создают путаницу.

### Решение
Единый config manager с приоритетами.

### Реализация

Создать `config/config_manager.py`:

```python
"""
Unified Configuration Manager
Единый источник конфигурации для всей системы
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class TradingConfig:
    """Конфигурация системы трейдинга"""
    
    # Bybit API
    bybit_api_key: str
    bybit_api_secret: str
    bybit_testnet: bool = False
    
    # Qwen AI
    qwen_api_key: str
    qwen_model: str = "qwen/qwen-turbo"
    
    # Telegram
    telegram_bot_token: Optional[str] = None
    telegram_chat_ids: Optional[str] = None
    
    # Trading settings
    max_risk_per_trade: float = 0.02
    max_concurrent_positions: int = 3
    daily_loss_limit: float = 0.05
    default_leverage: int = 2
    max_leverage: int = 5
    
    # Agent settings
    min_confluence: float = 8.0
    min_probability: float = 0.70
    min_risk_reward: float = 2.0


class ConfigManager:
    """Менеджер конфигурации с приоритетами"""
    
    def __init__(self, base_path: Optional[Path] = None):
        self.base_path = base_path or Path(__file__).parent.parent
        self._config = None
    
    def load(self) -> TradingConfig:
        """
        Загрузка конфигурации с приоритетами:
        1. Environment variables (высший приоритет)
        2. config/credentials.json
        3. config/autonomous_agent.json
        4. Defaults (низший приоритет)
        """
        config_data = {}
        
        # 1. Загрузка из файлов
        credentials_file = self.base_path / "config" / "credentials.json"
        if credentials_file.exists():
            with open(credentials_file) as f:
                creds = json.load(f)
                if "bybit" in creds:
                    config_data.update(creds["bybit"])
                if "settings" in creds:
                    config_data.update(creds["settings"])
        
        agent_config_file = self.base_path / "config" / "autonomous_agent.json"
        if agent_config_file.exists():
            with open(agent_config_file) as f:
                config_data.update(json.load(f))
        
        # 2. Override с environment variables (приоритет)
        env_mappings = {
            "BYBIT_API_KEY": "bybit_api_key",
            "BYBIT_API_SECRET": "bybit_api_secret",
            "BYBIT_TESTNET": "bybit_testnet",
            "QWEN_API_KEY": "qwen_api_key",
            "QWEN_MODEL": "qwen_model",
            "TELEGRAM_BOT_TOKEN": "telegram_bot_token",
            "TELEGRAM_CHAT_IDS": "telegram_chat_ids",
        }
        
        for env_var, config_key in env_mappings.items():
            value = os.getenv(env_var)
            if value:
                # Конвертация boolean
                if config_key == "bybit_testnet":
                    value = value.lower() in ("true", "1", "yes")
                config_data[config_key] = value
        
        # 3. Создание TradingConfig
        self._config = TradingConfig(**config_data)
        
        # 4. Валидация
        self._validate()
        
        return self._config
    
    def _validate(self):
        """Валидация конфигурации"""
        required = ["bybit_api_key", "bybit_api_secret", "qwen_api_key"]
        missing = [
            k for k in required
            if not getattr(self._config, k, None)
        ]
        
        if missing:
            raise ValueError(
                f"Missing required configuration: {', '.join(missing)}\n"
                f"Set via environment variables or config files"
            )
    
    def get(self) -> TradingConfig:
        """Получить конфигурацию (загрузить если нужно)"""
        if self._config is None:
            self.load()
        return self._config


# Singleton instance
_config_manager = ConfigManager()


def get_config() -> TradingConfig:
    """Получить глобальную конфигурацию"""
    return _config_manager.get()
```

Использование во всех модулях:

```python
from config.config_manager import get_config

# В любом модуле
config = get_config()
analyzer = AutonomousAnalyzer(
    qwen_api_key=config.qwen_api_key,
    bybit_api_key=config.bybit_api_key,
    bybit_api_secret=config.bybit_api_secret,
    # ...
)
```

---

## 🟢 ПРИОРИТЕТ 6: ДОПОЛНИТЕЛЬНЫЕ УЛУЧШЕНИЯ

### 6.1 Мониторинг и логирование

Создать `monitoring/agent_monitor.py`:

```python
"""
Мониторинг Autonomous Agent
Отслеживание публикаций, ошибок, метрик
"""

import sqlite3
from datetime import datetime
from typing import Dict, Any


class AgentMonitor:
    """Мониторинг работы агента"""
    
    def __init__(self, db_path: str = "data/agent_monitoring.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Инициализация БД"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analysis_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                success BOOLEAN NOT NULL,
                longs_found INTEGER,
                shorts_found INTEGER,
                total_scanned INTEGER,
                error TEXT,
                duration_seconds REAL
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS telegram_publications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                chat_id TEXT NOT NULL,
                success BOOLEAN NOT NULL,
                error TEXT,
                analysis_id INTEGER,
                FOREIGN KEY (analysis_id) REFERENCES analysis_runs(id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def record_analysis(self, result: Dict[str, Any], duration: float) -> int:
        """Записать результат анализа"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO analysis_runs (
                timestamp, success, longs_found, shorts_found,
                total_scanned, error, duration_seconds
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            result.get("success", False),
            len(result.get("top_3_longs", [])),
            len(result.get("top_3_shorts", [])),
            result.get("total_scanned", 0),
            result.get("error"),
            duration
        ))
        
        analysis_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return analysis_id
    
    def record_publication(
        self,
        chat_id: str,
        success: bool,
        analysis_id: int,
        error: str = None
    ):
        """Записать публикацию в Telegram"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO telegram_publications (
                timestamp, chat_id, success, error, analysis_id
            ) VALUES (?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            chat_id,
            success,
            error,
            analysis_id
        ))
        
        conn.commit()
        conn.close()
    
    def get_stats(self, days: int = 7) -> Dict[str, Any]:
        """Получить статистику за период"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Статистика анализов
        cursor.execute("""
            SELECT
                COUNT(*) as total_runs,
                SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful_runs,
                AVG(longs_found) as avg_longs,
                AVG(shorts_found) as avg_shorts,
                AVG(duration_seconds) as avg_duration
            FROM analysis_runs
            WHERE timestamp >= datetime('now', '-' || ? || ' days')
        """, (days,))
        
        stats = cursor.fetchone()
        
        # Статистика публикаций
        cursor.execute("""
            SELECT
                COUNT(*) as total_publications,
                SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful_publications
            FROM telegram_publications
            WHERE timestamp >= datetime('now', '-' || ? || ' days')
        """, (days,))
        
        pub_stats = cursor.fetchone()
        
        conn.close()
        
        return {
            "period_days": days,
            "total_runs": stats[0],
            "successful_runs": stats[1],
            "success_rate": stats[1] / stats[0] if stats[0] > 0 else 0,
            "avg_longs_found": stats[2],
            "avg_shorts_found": stats[3],
            "avg_duration_seconds": stats[4],
            "total_publications": pub_stats[0],
            "successful_publications": pub_stats[1],
            "publication_success_rate": pub_stats[1] / pub_stats[0] if pub_stats[0] > 0 else 0
        }
```

### 6.2 Исправить WebUI TypeScript ошибки

```bash
cd bybit-mcp/webui

# Проверить ошибки
pnpm build

# Типичные исправления:
# 1. Добавить типы для всех props
# 2. Исправить any types
# 3. Добавить null checks

# После исправления
pnpm build  # Должно пройти без ошибок
```

### 6.3 Обновить документацию

Создать `autonomous_agent/INTEGRATION_GUIDE.md`:

```markdown
# Integration Guide: Autonomous Agent

## Quick Start

### Option 1: Via Cursor MCP (Recommended)

\```
ТЫ в Cursor: "Проанализируй рынок"
АГЕНТ: [Запускает analyze_market_comprehensive через MCP]
\```

### Option 2: Via Command Line

\```bash
python -m autonomous_agent.main
\```

### Option 3: Via Cron Job

\```bash
# Автоматически каждые 30 минут
\```

## Components

- MCP Server: `autonomous_agent_server.py`
- Core Analyzer: `autonomous_analyzer.py`
- Telegram Integration: Built-in
- WebUI: Dashboard in `/webui`

## Configuration

See `config/config_manager.py` for unified configuration.
```

---

## ✅ ЧЕКЛИСТ РЕАЛИЗАЦИИ

### Этап 1: MCP Server Wrapper
- [ ] Создать `mcp_server/autonomous_agent_server.py`
- [ ] Обновить Cursor MCP конфигурацию
- [ ] Протестировать через Cursor
- [ ] Добавить логирование

### Этап 2: MCP Integration
- [ ] Рефакторинг `autonomous_analyzer.py`
- [ ] Использовать `validate_entry()` из MCP
- [ ] Использовать `SignalTracker` для записи
- [ ] Добавить возможность открытия позиций

### Этап 3: WebUI Integration
- [ ] Добавить API endpoints
- [ ] Создать React компонент
- [ ] Исправить TypeScript ошибки
- [ ] Протестировать UI

### Этап 4: Automation
- [ ] Создать Kubernetes CronJob
- [ ] Или настроить системный cron
- [ ] Добавить error handling
- [ ] Настроить логирование

### Этап 5: Configuration
- [ ] Создать `config_manager.py`
- [ ] Обновить все модули для использования
- [ ] Документировать конфигурацию
- [ ] Добавить валидацию

### Этап 6: Monitoring
- [ ] Создать `AgentMonitor`
- [ ] Интегрировать в main.py
- [ ] Создать dashboard для метрик
- [ ] Настроить алерты

### Этап 7: Documentation
- [ ] Обновить README
- [ ] Создать INTEGRATION_GUIDE
- [ ] Обновить QUICK_START
- [ ] Добавить примеры использования

---

## 🎯 ОЖИДАЕМЫЙ РЕЗУЛЬТАТ

После всех исправлений система будет работать следующим образом:

### Сценарий 1: Анализ через Cursor
```
1. Открываешь Cursor
2. Говоришь: "Проанализируй рынок и найди сигналы"
3. Агент запускает analyze_market_comprehensive через MCP
4. Получаешь ТОП-3 лонгов и ТОП-3 шортов
5. Можешь открыть позицию командой: "Открой первый лонг"
6. Агент использует place_order из MCP
7. Позиция автоматически мониторится
```

### Сценарий 2: Автоматическая публикация
```
1. CronJob запускается каждые 30 минут
2. Агент анализирует рынок
3. Находит топ сигналы
4. Автоматически публикует в Telegram
5. Сохраняет результаты в БД
6. Обновляет WebUI dashboard
```

### Сценарий 3: Мониторинг через UI
```
1. Открываешь http://localhost:8080
2. Видишь последние сигналы от агента
3. Видишь активные позиции
4. Можешь управлять позициями через UI
5. Видишь метрики качества сигналов
```

---

## 🚧 ПОРЯДОК РЕАЛИЗАЦИИ

**День 1:**
1. ✅ Создать MCP Server Wrapper (Приоритет 1)
2. ✅ Протестировать через Cursor

**День 2:**
3. ✅ Интеграция с MCP инструментами (Приоритет 2)
4. ✅ Рефакторинг для использования validate_entry

**День 3:**
5. ✅ WebUI endpoint (Приоритет 3, часть 1)
6. ✅ React компонент

**День 4:**
7. ✅ Исправить TypeScript ошибки (Приоритет 3, часть 2)
8. ✅ Протестировать UI

**День 5:**
9. ✅ Автоматизация (Приоритет 4)
10. ✅ CronJob setup

**День 6:**
11. ✅ Unified Configuration (Приоритет 5)
12. ✅ Мониторинг (Приоритет 6, часть 1)

**День 7:**
13. ✅ Документация (Приоритет 6, часть 2)
14. ✅ Финальное тестирование

---

## 📞 ПОДДЕРЖКА

При возникновении проблем:

1. Проверь логи: `logs/autonomous_agent_server_*.log`
2. Проверь конфигурацию через `config_manager`
3. Проверь MCP server статус в Cursor
4. Проверь что все зависимости установлены

---

**Версия:** 1.0  
**Дата:** 2025-01-20  
**Статус:** READY FOR IMPLEMENTATION  
**Связанный документ:** [AGENT_SYSTEM_RESEARCH.md](AGENT_SYSTEM_RESEARCH.md)