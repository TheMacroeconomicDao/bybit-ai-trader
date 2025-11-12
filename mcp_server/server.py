#!/usr/bin/env python3
"""
Bybit Trading MCP Server
Основной сервер для взаимодействия с Bybit API через MCP
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from bybit_client import BybitClient
from technical_analysis import TechnicalAnalysis
from market_scanner import MarketScanner

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Инициализация MCP сервера
app = Server("bybit-trading-server")

# Глобальные клиенты
bybit_client: Optional[BybitClient] = None
technical_analysis: Optional[TechnicalAnalysis] = None
market_scanner: Optional[MarketScanner] = None


def load_credentials() -> Dict[str, Any]:
    """Загрузка credentials из config файла"""
    config_path = Path(__file__).parent.parent / "config" / "credentials.json"
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Credentials file not found: {config_path}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in credentials file: {e}")
        raise


@app.list_tools()
async def list_tools() -> List[Tool]:
    """Список всех доступных инструментов MCP сервера"""
    return [
        # 📊 Рыночные данные
        Tool(
            name="get_market_overview",
            description="Получить обзор всего рынка (sentiment, топ движения, условия)",
            inputSchema={
                "type": "object",
                "properties": {
                    "market_type": {
                        "type": "string",
                        "enum": ["spot", "futures", "both"],
                        "description": "Тип рынка для анализа",
                        "default": "both"
                    }
                }
            }
        ),
        Tool(
            name="get_all_tickers",
            description="Получить все торговые пары с базовой информацией",
            inputSchema={
                "type": "object",
                "properties": {
                    "market_type": {
                        "type": "string",
                        "enum": ["spot", "futures"],
                        "description": "Тип рынка"
                    },
                    "sort_by": {
                        "type": "string",
                        "enum": ["volume", "change", "name"],
                        "description": "Сортировка результатов"
                    }
                }
            }
        ),
        Tool(
            name="get_asset_price",
            description="Получить текущую цену актива",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Торговая пара (например BTC/USDT)"
                    }
                },
                "required": ["symbol"]
            }
        ),
        
        # 📈 Технический анализ
        Tool(
            name="analyze_asset",
            description="ПОЛНЫЙ технический анализ актива на всех таймфреймах",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Торговая пара (например ETH/USDT)"
                    },
                    "timeframes": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Таймфреймы для анализа",
                        "default": ["5m", "15m", "1h", "4h", "1d"]
                    },
                    "include_patterns": {
                        "type": "boolean",
                        "description": "Включить распознавание паттернов",
                        "default": True
                    }
                },
                "required": ["symbol"]
            }
        ),
        
        # 🔍 Сканирование рынка
        Tool(
            name="scan_market",
            description="Поиск торговых возможностей по критериям",
            inputSchema={
                "type": "object",
                "properties": {
                    "criteria": {
                        "type": "object",
                        "description": "Критерии фильтрации возможностей"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Максимальное количество результатов",
                        "default": 10
                    }
                },
                "required": ["criteria"]
            }
        ),
        Tool(
            name="find_oversold_assets",
            description="Найти перепроданные активы (RSI < 30)",
            inputSchema={
                "type": "object",
                "properties": {
                    "market_type": {
                        "type": "string",
                        "enum": ["spot", "futures"],
                        "default": "spot"
                    },
                    "min_volume_24h": {
                        "type": "number",
                        "description": "Минимальный объём за 24ч",
                        "default": 1000000
                    }
                }
            }
        ),
        
        # 🎯 Валидация входа
        Tool(
            name="validate_entry",
            description="Валидация точки входа перед открытием позиции",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string"},
                    "side": {
                        "type": "string",
                        "enum": ["long", "short"]
                    },
                    "entry_price": {"type": "number"},
                    "stop_loss": {"type": "number"},
                    "take_profit": {"type": "number"},
                    "risk_pct": {
                        "type": "number",
                        "description": "Риск в % от депозита",
                        "default": 0.01
                    }
                },
                "required": ["symbol", "side", "entry_price", "stop_loss", "take_profit"]
            }
        ),
        
        # 💰 Счёт и позиции
        Tool(
            name="get_account_info",
            description="Получить информацию о счёте и балансе",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="get_open_positions",
            description="Получить все открытые позиции",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        
        # ⚡ Торговые операции
        Tool(
            name="place_order",
            description="Открыть новую позицию",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string"},
                    "side": {
                        "type": "string",
                        "enum": ["buy", "sell"]
                    },
                    "order_type": {
                        "type": "string",
                        "enum": ["market", "limit"],
                        "default": "market"
                    },
                    "quantity": {"type": "number"},
                    "price": {
                        "type": "number",
                        "description": "Цена для limit ордера"
                    },
                    "stop_loss": {"type": "number"},
                    "take_profit": {"type": "number"}
                },
                "required": ["symbol", "side", "quantity"]
            }
        ),
        Tool(
            name="close_position",
            description="Закрыть открытую позицию",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string"},
                    "reason": {
                        "type": "string",
                        "description": "Причина закрытия"
                    }
                },
                "required": ["symbol"]
            }
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> List[TextContent]:
    """Обработка вызовов инструментов"""
    try:
        logger.info(f"Tool called: {name} with args: {arguments}")
        
        # Маршрутизация вызовов
        if name == "get_market_overview":
            result = await bybit_client.get_market_overview(
                arguments.get("market_type", "both")
            )
        elif name == "get_all_tickers":
            result = await bybit_client.get_all_tickers(
                arguments.get("market_type", "spot"),
                arguments.get("sort_by", "volume")
            )
        elif name == "get_asset_price":
            result = await bybit_client.get_asset_price(
                arguments["symbol"]
            )
        elif name == "analyze_asset":
            result = await technical_analysis.analyze_asset(
                symbol=arguments["symbol"],
                timeframes=arguments.get("timeframes", ["5m", "15m", "1h", "4h", "1d"]),
                include_patterns=arguments.get("include_patterns", True)
            )
        elif name == "scan_market":
            result = await market_scanner.scan_market(
                criteria=arguments["criteria"],
                limit=arguments.get("limit", 10)
            )
        elif name == "find_oversold_assets":
            result = await market_scanner.find_oversold_assets(
                market_type=arguments.get("market_type", "spot"),
                min_volume_24h=arguments.get("min_volume_24h", 1000000)
            )
        elif name == "validate_entry":
            result = await technical_analysis.validate_entry(
                symbol=arguments["symbol"],
                side=arguments["side"],
                entry_price=arguments["entry_price"],
                stop_loss=arguments["stop_loss"],
                take_profit=arguments["take_profit"],
                risk_pct=arguments.get("risk_pct", 0.01)
            )
        elif name == "get_account_info":
            result = await bybit_client.get_account_info()
        elif name == "get_open_positions":
            result = await bybit_client.get_open_positions()
        elif name == "place_order":
            result = await bybit_client.place_order(
                symbol=arguments["symbol"],
                side=arguments["side"],
                order_type=arguments.get("order_type", "market"),
                quantity=arguments["quantity"],
                price=arguments.get("price"),
                stop_loss=arguments.get("stop_loss"),
                take_profit=arguments.get("take_profit")
            )
        elif name == "close_position":
            result = await bybit_client.close_position(
                symbol=arguments["symbol"],
                reason=arguments.get("reason", "Manual close")
            )
        else:
            raise ValueError(f"Unknown tool: {name}")
        
        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2, ensure_ascii=False)
        )]
        
    except Exception as e:
        logger.error(f"Error executing tool {name}: {e}", exc_info=True)
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": str(e),
                "tool": name
            }, indent=2)
        )]


async def main():
    """Основная функция запуска сервера"""
    global bybit_client, technical_analysis, market_scanner
    
    logger.info("Starting Bybit Trading MCP Server...")
    
    # Загрузка credentials
    credentials = load_credentials()
    
    # Инициализация клиентов
    bybit_client = BybitClient(
        api_key=credentials["bybit"]["api_key"],
        api_secret=credentials["bybit"]["api_secret"],
        testnet=credentials["bybit"].get("testnet", False)
    )
    
    technical_analysis = TechnicalAnalysis(bybit_client)
    market_scanner = MarketScanner(bybit_client, technical_analysis)
    
    logger.info("✅ Bybit Trading MCP Server started successfully")
    
    # Запуск сервера
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
