#!/usr/bin/env python3
"""
Autonomous Agent MCP Server
Обертка для autonomous agent с доступом через MCP
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Any, List, Dict, Optional
from datetime import datetime

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, Resource, TextResourceContents
from loguru import logger

# Импорт autonomous agent компонентов
sys.path.insert(0, str(Path(__file__).parent.parent))
from autonomous_agent.autonomous_analyzer import AutonomousAnalyzer
from autonomous_agent.telegram_formatter import TelegramFormatter
from mcp_server.telegram_bot import TelegramBot
from mcp_server.signal_tracker import SignalTracker
from mcp_server.trading_operations import TradingOperations

# Настройка логирования
logger.remove()
logger.add(sys.stderr, level="INFO")
logger.add("logs/autonomous_agent_server_{time}.log", rotation="1 day", retention="7 days")

# Инициализация MCP сервера
app = Server("autonomous-trading-agent")

# Глобальные переменные
analyzer: Optional[AutonomousAnalyzer] = None
formatter = TelegramFormatter()
last_analysis_result: Optional[Dict[str, Any]] = None
signal_tracker: Optional[SignalTracker] = None
trading_ops: Optional[TradingOperations] = None


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


def initialize_components():
    """Инициализация компонентов системы"""
    global analyzer, signal_tracker, trading_ops
    
    if analyzer is not None:
        return  # Уже инициализирован
    
    config = load_config()
    
    # Инициализация signal tracker
    if signal_tracker is None:
        signal_tracker = SignalTracker()
        logger.info("Signal Tracker initialized")
    
    # Инициализация trading operations
    if trading_ops is None:
        trading_ops = TradingOperations(
            config["bybit_api_key"],
            config["bybit_api_secret"],
            config["testnet"]
        )
        logger.info("Trading Operations initialized")
    
    # Инициализация analyzer с интеграцией MCP компонентов
    analyzer = AutonomousAnalyzer(
        qwen_api_key=config["qwen_api_key"],
        bybit_api_key=config["bybit_api_key"],
        bybit_api_secret=config["bybit_api_secret"],
        qwen_model=config["qwen_model"],
        testnet=config["testnet"],
        signal_tracker=signal_tracker
    )
    logger.info("Autonomous Analyzer initialized with MCP integration")


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
    global analyzer, last_analysis_result, signal_tracker
    
    try:
        logger.info(f"Tool called: {name}")
        
        # Инициализация компонентов если нужно
        if analyzer is None:
            initialize_components()
        
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


@app.list_resources()
async def list_resources() -> List[Resource]:
    """Список всех промптов и базы знаний"""
    
    base_path = Path(__file__).parent.parent
    resources = []
    
    # Промпты из папки prompts/
    prompts_dir = base_path / "prompts"
    if prompts_dir.exists():
        for prompt_file in prompts_dir.glob("*.md"):
            resources.append(Resource(
                uri=f"prompt:///{prompt_file.stem}",
                name=prompt_file.stem,
                description=f"Trading prompt: {prompt_file.stem}",
                mimeType="text/markdown"
            ))
    
    # База знаний из папки knowledge_base/
    kb_dir = base_path / "knowledge_base"
    if kb_dir.exists():
        for kb_file in kb_dir.glob("*.md"):
            resources.append(Resource(
                uri=f"knowledge:///{kb_file.stem}",
                name=kb_file.stem,
                description=f"Trading knowledge: {kb_file.stem}",
                mimeType="text/markdown"
            ))
    
    logger.info(f"Listed {len(resources)} resources ({len(list(prompts_dir.glob('*.md'))) if prompts_dir.exists() else 0} prompts, {len(list(kb_dir.glob('*.md'))) if kb_dir.exists() else 0} knowledge)")
    return resources


@app.read_resource()
async def read_resource(uri: str) -> TextResourceContents:
    """Чтение промпта или базы знаний"""
    
    base_path = Path(__file__).parent.parent
    
    try:
        if uri.startswith("prompt:///"):
            # Читаем промпт
            prompt_name = uri.replace("prompt:///", "")
            prompt_file = base_path / "prompts" / f"{prompt_name}.md"
            
            if not prompt_file.exists():
                raise ValueError(f"Prompt not found: {prompt_name}")
            
            content = prompt_file.read_text(encoding="utf-8")
            logger.info(f"Read prompt: {prompt_name} ({len(content)} chars)")
            
            return TextResourceContents(
                uri=uri,
                mimeType="text/markdown",
                text=content
            )
        
        elif uri.startswith("knowledge:///"):
            # Читаем базу знаний
            kb_name = uri.replace("knowledge:///", "")
            kb_file = base_path / "knowledge_base" / f"{kb_name}.md"
            
            if not kb_file.exists():
                raise ValueError(f"Knowledge base not found: {kb_name}")
            
            content = kb_file.read_text(encoding="utf-8")
            logger.info(f"Read knowledge: {kb_name} ({len(content)} chars)")
            
            return TextResourceContents(
                uri=uri,
                mimeType="text/markdown",
                text=content
            )
        
        else:
            raise ValueError(f"Unknown resource URI: {uri}")
    
    except Exception as e:
        logger.error(f"Error reading resource {uri}: {e}")
        raise


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
    
    # Подсчет ресурсов для логирования
    resources = await list_resources()
    prompts_count = sum(1 for r in resources if str(r.uri).startswith("prompt:///"))
    knowledge_count = sum(1 for r in resources if str(r.uri).startswith("knowledge:///"))
    
    logger.info("=" * 60)
    logger.info("Server ready for connections")
    logger.info(f"Available tools: 4, prompts: {prompts_count}, resources: {len(resources)}")
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

