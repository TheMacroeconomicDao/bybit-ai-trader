"""
Telegram Formatter
Форматирование результатов анализа для публикации в Telegram
"""

from typing import Dict, List, Any
from datetime import datetime
from loguru import logger


class TelegramFormatter:
    """Форматтер для Telegram публикации"""
    
    @staticmethod
    def format_top_opportunities(analysis_result: Dict[str, Any]) -> str:
        """
        Форматирование топ 3 лонгов и топ 3 шортов для Telegram
        
        Args:
            analysis_result: Результат анализа от AutonomousAnalyzer
            
        Returns:
            Отформатированное сообщение для Telegram
        """
        if not analysis_result.get("success"):
            return "❌ Ошибка анализа рынка. Попробуйте позже."
        
        top_longs = analysis_result.get("top_3_longs", [])
        top_shorts = analysis_result.get("top_3_shorts", [])
        
        if not top_longs and not top_shorts:
            return "⚠️ Качественных возможностей не найдено. Рекомендуется подождать лучших setup."
        
        # Заголовок
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = f"🎯 АНАЛИЗ РЫНКА\n📅 {timestamp}\n\n"
        
        # BTC статус
        btc_status = analysis_result.get("btc_analysis", {}).get("status", "unknown")
        btc_emoji = "🟢" if btc_status == "bullish" else "🔴" if btc_status == "bearish" else "🟡"
        message += f"{btc_emoji} BTC Status: {btc_status.upper()}\n\n"
        
        # ТОП 3 ЛОНГА
        if top_longs:
            message += "🟢 ТОП 3 ЛОНГА\n"
            message += "=" * 50 + "\n\n"
            for idx, opp in enumerate(top_longs, 1):
                message += TelegramFormatter._format_single_opportunity(opp, idx)
                message += "\n" + "─" * 40 + "\n\n"
        
        # ТОП 3 ШОРТА
        if top_shorts:
            message += "🔴 ТОП 3 ШОРТА\n"
            message += "=" * 50 + "\n\n"
            for idx, opp in enumerate(top_shorts, 1):
                message += TelegramFormatter._format_single_opportunity(opp, idx)
                message += "\n" + "─" * 40 + "\n\n"
        
        # Market summary
        market_overview = analysis_result.get("market_overview", {})
        sentiment = market_overview.get("sentiment", "neutral")
        message += f"📊 Market Sentiment: {sentiment.upper()}\n"
        
        # Статистика
        message += f"📈 Проанализировано активов: {analysis_result.get('total_scanned', 0)}\n"
        message += f"✅ Детально проанализировано: {analysis_result.get('total_analyzed', 0)}\n"
        
        return message
    
    @staticmethod
    def _format_single_opportunity(opp: Dict[str, Any], index: int) -> str:
        """Форматирование одной возможности"""
        symbol = opp.get("symbol", "UNKNOWN")
        side = opp.get("side", "long").upper()
        entry = opp.get("entry_price", 0)
        sl = opp.get("stop_loss", 0)
        tp = opp.get("take_profit", 0)
        score = opp.get("confluence_score", 0)
        probability = opp.get("probability", 0)
        rr = opp.get("risk_reward", 0)
        reasoning = opp.get("reasoning", "")
        factors = opp.get("key_factors", [])
        
        # Эмодзи для side
        side_emoji = "🟢" if side == "LONG" else "🔴"
        
        # Эмодзи для score
        if score >= 9.0:
            score_emoji = "🔥"
        elif score >= 8.5:
            score_emoji = "⭐"
        elif score >= 8.0:
            score_emoji = "✅"
        else:
            score_emoji = "⚠️"
        
        message = f"{score_emoji} #{index}. {symbol} {side_emoji} {side}\n\n"
        
        # Цены
        message += f"💰 Entry: ${entry:.4f}\n"
        message += f"🛑 Stop Loss: ${sl:.4f}\n"
        message += f"🎯 Take Profit: ${tp:.4f}\n"
        message += f"📊 R:R = 1:{rr:.2f}\n\n"
        
        # Метрики
        message += f"⭐ Confluence: {score}/10\n"
        message += f"📈 Вероятность: {probability*100:.0f}%\n\n"
        
        # Ключевые факторы
        if factors:
            message += "🔑 Ключевые факторы:\n"
            for factor in factors[:5]:
                message += f"  • {factor}\n"
            message += "\n"
        
        # Обоснование
        if reasoning:
            message += f"💡 Обоснование:\n{reasoning}\n\n"
        
        # Timeframes alignment
        timeframes = opp.get("timeframes_alignment", [])
        if timeframes:
            message += f"⏰ Таймфреймы: {', '.join(timeframes)}\n"
        
        return message
    
    @staticmethod
    def format_market_summary(analysis_result: Dict[str, Any]) -> str:
        """
        Форматирование краткого резюме рынка
        
        Args:
            analysis_result: Результат анализа
            
        Returns:
            Краткое резюме
        """
        market_overview = analysis_result.get("market_overview", {})
        btc_analysis = analysis_result.get("btc_analysis", {})
        
        message = "📊 MARKET SUMMARY\n\n"
        
        # BTC
        btc_price_data = btc_analysis.get("price", {})
        if btc_price_data:
            btc_price = btc_price_data.get("price", 0)
            btc_change = btc_price_data.get("change_24h", 0)
            change_emoji = "🟢" if btc_change > 0 else "🔴" if btc_change < 0 else "🟡"
            message += f"{change_emoji} BTC: ${btc_price:,.2f} ({btc_change:+.2f}%)\n"
        
        # Sentiment
        sentiment = market_overview.get("sentiment", "neutral")
        message += f"📈 Sentiment: {sentiment.upper()}\n"
        
        # Statistics
        stats = market_overview.get("statistics", {})
        if stats:
            message += f"📊 Total Pairs: {stats.get('total_pairs', 0)}\n"
            message += f"🟢 Green: {stats.get('positive_changes', 0)}\n"
            message += f"🔴 Red: {stats.get('negative_changes', 0)}\n"
        
        return message
    
    @staticmethod
    def format_error(error: str) -> str:
        """Форматирование ошибки"""
        return f"❌ Ошибка: {error}\n\nПопробуйте позже или проверьте логи."

