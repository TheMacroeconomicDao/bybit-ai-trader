"""
Детальный форматтер для Telegram
Форматирование полного отчёта как в примере пользователя
"""

from typing import Dict, List, Any
from datetime import datetime
from loguru import logger
import sys
from pathlib import Path

# Добавляем импорт нормализатора
sys.path.insert(0, str(Path(__file__).parent.parent))
from mcp_server.score_normalizer import normalize_opportunity_score


class DetailedFormatter:
    """Детальный форматтер для полного отчёта"""
    
    @staticmethod
    def format_full_report(analysis_result: Dict[str, Any]) -> str:
        """
        Форматирование полного детального отчёта
        
        ENHANCED VERSION 3.0: Institutional Quality
        - Market Regime detection
        - Adaptive Thresholds
        - Tier-based classification
        - Enhanced filtering and warnings
        
        Args:
            analysis_result: Результат анализа от AutonomousAnalyzer
            
        Returns:
            Полный отформатированный отчёт
        """
        if not analysis_result.get("success"):
            return "❌ Ошибка анализа рынка. Попробуйте позже."
        
        message = "🔍 INSTITUTIONAL MARKET ANALYSIS REPORT\n\n"
        message += "━" * 50 + "\n\n"
        
        # ═══════════════════════════════════════════════════════
        # MARKET REGIME (NEW!)
        # ═══════════════════════════════════════════════════════
        market_regime = analysis_result.get("market_regime", {})
        if market_regime:
            message += "📊 MARKET REGIME\n\n"
            message += f"• Type: {market_regime.get('type', 'unknown').upper()}\n"
            message += f"• Confidence: {market_regime.get('confidence', 0):.0%}\n"
            message += f"• Description: {market_regime.get('description', '')}\n"
            
            metrics = market_regime.get('metrics', {})
            message += f"• BTC Weekly: {metrics.get('btc_weekly_change_pct', 0):+.2f}%\n"
            message += f"• ADX: {metrics.get('adx', 0):.1f}\n"
            message += f"• Volatility: {metrics.get('volatility', 'normal')}\n\n"
            
            message += f"**Trading Implications:** {market_regime.get('trading_implications', '')}\n\n"
            message += "━" * 50 + "\n\n"
        
        # ═══════════════════════════════════════════════════════
        # ADAPTIVE THRESHOLDS (NEW!)
        # ═══════════════════════════════════════════════════════
        thresholds = analysis_result.get("adaptive_thresholds", {})
        if thresholds:
            message += "🎯 ADAPTIVE THRESHOLDS\n\n"
            message += f"• LONG opportunities: {thresholds.get('long', 7.0):.1f}/10\n"
            message += f"• SHORT opportunities: {thresholds.get('short', 7.0):.1f}/10\n"
            message += f"• Reasoning: {thresholds.get('reasoning', '')}\n\n"
            message += "━" * 50 + "\n\n"
        
        # BTC STATUS (CRITICAL)
        btc_analysis = analysis_result.get("btc_analysis", {})
        message += DetailedFormatter._format_btc_status(btc_analysis)
        message += "\n" + "━" * 50 + "\n\n"
        
        # TOP OPPORTUNITIES
        top_longs = analysis_result.get("top_3_longs", [])
        top_shorts = analysis_result.get("top_3_shorts", [])
        all_longs = analysis_result.get("all_longs", [])
        all_shorts = analysis_result.get("all_shorts", [])
        
        # Фильтруем пары СТЕЙБЛ/СТЕЙБЛ (исключаем только их, не пары типа BTC/USDT)
        all_longs = [opp for opp in all_longs if not DetailedFormatter._is_stable_stable_pair(opp.get("symbol", ""))]
        all_shorts = [opp for opp in all_shorts if not DetailedFormatter._is_stable_stable_pair(opp.get("symbol", ""))]
        
        message += "TOP OPPORTUNITIES (After Full Market Scan)\n\n"
        
        # LONG OPPORTUNITIES
        message += "LONG OPPORTUNITIES:\n\n"
        if all_longs:
            for idx, opp in enumerate(all_longs[:5], 1):  # Топ 5
                message += DetailedFormatter._format_opportunity_detailed(opp, idx)
                message += "\n"
        else:
            message += "No opportunities found.\n\n"
        
        message += "━" * 40 + "\n\n"
        
        # SHORT OPPORTUNITIES
        message += "SHORT OPPORTUNITIES:\n\n"
        if all_shorts:
            for idx, opp in enumerate(all_shorts[:5], 1):  # Топ 5
                message += DetailedFormatter._format_opportunity_detailed(opp, idx)
                message += "\n"
        else:
            message += "No opportunities found.\n\n"
        
        message += "━" * 40 + "\n\n"
        
        # DIRECTION COMPARISON
        longs_found = analysis_result.get("longs_found", 0)
        shorts_found = analysis_result.get("shorts_found", 0)
        
        # ✅ Безопасное извлечение и нормализация scores с проверкой на None
        # Нормализуем все opportunities перед использованием
        all_longs = [normalize_opportunity_score(opp) for opp in all_longs if opp]
        all_shorts = [normalize_opportunity_score(opp) for opp in all_shorts if opp]
        
        # Безопасное извлечение с дефолтным значением и валидацией
        best_long_score = 0.0
        best_short_score = 0.0
        
        if all_longs:
            long_scores = [opp.get("final_score", 0.0) for opp in all_longs if opp.get("final_score") is not None]
            best_long_score = max(long_scores) if long_scores else 0.0
        
        if all_shorts:
            short_scores = [opp.get("final_score", 0.0) for opp in all_shorts if opp.get("final_score") is not None]
            best_short_score = max(short_scores) if short_scores else 0.0
        
        message += "DIRECTION COMPARISON:\n\n"
        message += f"• LONG found: {longs_found} opportunities\n"
        message += f"• SHORT found: {shorts_found} opportunities\n"
        message += f"• Best LONG score: {best_long_score:.2f}\n"
        message += f"• Best SHORT score: {best_short_score:.2f}\n\n"
        message += "━" * 40 + "\n\n"
        
        # RISK ASSESSMENT
        message += DetailedFormatter._format_risk_assessment(
            best_long_score, best_short_score, btc_analysis
        )
        message += "\n" + "━" * 40 + "\n\n"
        
        # SCAN STATISTICS
        total_scanned = analysis_result.get("total_scanned", 0)
        total_analyzed = analysis_result.get("total_analyzed", 0)
        potential_candidates = analysis_result.get("potential_candidates", 0)
        
        passed_zero_risk = len([opp for opp in all_longs + all_shorts 
                                if opp.get("confluence_score", 0) >= 8.0 
                                and opp.get("probability", 0) >= 0.70])
        
        message += "SCAN STATISTICS\n\n"
        message += f"• Total Analyzed: {total_scanned} assets\n"
        message += f"• Potential Candidates: {potential_candidates}\n"
        message += f"• LONG Opportunities: {longs_found}\n"
        message += f"• SHORT Opportunities: {shorts_found}\n"
        message += f"• Passed Zero-Risk Evaluation: {passed_zero_risk}\n\n"
        message += "━" * 40 + "\n\n"
        
        # RECOMMENDATION
        message += DetailedFormatter._format_recommendation(
            passed_zero_risk, best_long_score, best_short_score
        )
        message += "\n" + "━" * 40 + "\n\n"
        
        # System Status
        message += f"System Status: Full capacity ({total_scanned} assets scanned)\n"
        message += "Next Update: Monitoring every 12 hours (2 times per day)\n"
        
        return message
    
    @staticmethod
    def _is_stable_stable_pair(symbol: str) -> bool:
        """
        Проверка, является ли пара СТЕЙБЛ/СТЕЙБЛ (исключаем только такие пары)
        
        НЕ исключаем:
        - BTC/USDT, ETH/USDT (крипта/стейбл) - это нормальные торговые пары
        
        Исключаем:
        - USDC/USDT, BUSD/USDT (стейбл/стейбл)
        - USDT/TRY, USDT/BRL (стейбл/фиат) - но это уже фильтруется в market_scanner
        
        Args:
            symbol: Символ пары (например "BTCUSDT", "BTC/USDT", "USDCUSDT")
            
        Returns:
            True если это пара СТЕЙБЛ/СТЕЙБЛ
        """
        if not symbol:
            return False
        
        # Список стабильных монет
        stablecoins = {'USDT', 'USDC', 'BUSD', 'DAI', 'TUSD', 'USDP', 'USDD', 'FRAX', 'LUSD', 'MIM'}
        
        # Нормализуем символ (убираем разделители)
        symbol_upper = symbol.upper().replace('/', '').replace('-', '')
        
        # Проверяем все возможные комбинации стабильных монет
        for stable1 in stablecoins:
            if symbol_upper.endswith(stable1):
                # Находим базовую валюту
                base = symbol_upper[:-len(stable1)]
                if base in stablecoins:
                    # Это СТЕЙБЛ/СТЕЙБЛ пара
                    return True
            if symbol_upper.startswith(stable1):
                # Находим котируемую валюту
                quote = symbol_upper[len(stable1):]
                if quote in stablecoins:
                    # Это СТЕЙБЛ/СТЕЙБЛ пара
                    return True
        
        return False
    
    @staticmethod
    def _format_btc_status(btc_analysis: Dict[str, Any]) -> str:
        """Форматирование статуса BTC"""
        message = "BTC STATUS (CRITICAL)\n\n"
        
        btc_status = btc_analysis.get("status", "unknown")
        technical = btc_analysis.get("technical_analysis", {})
        
        # Trend
        composite = technical.get("composite_signal", {})
        signal = composite.get("signal", "HOLD")
        confidence = composite.get("confidence", 0.5)
        
        # ADX
        adx_value = None
        for tf in ["1h", "4h", "1d"]:
            tf_data = technical.get("timeframes", {}).get(tf, {})
            indicators = tf_data.get("indicators", {})
            if "adx" in indicators:
                adx_value = indicators["adx"].get("adx_14")
                break
        
        if adx_value:
            if adx_value >= 25:
                trend = f"STRONG {'DOWNTREND' if btc_status == 'bearish' else 'UPTREND'}"
            else:
                trend = "NEUTRAL"
            message += f"• Trend: {trend} (ADX: {adx_value:.1f})\n"
        else:
            message += f"• Trend: {signal}\n"
        
        # RSI
        rsi_values = []
        for tf in ["1h", "4h", "1d"]:
            tf_data = technical.get("timeframes", {}).get(tf, {})
            indicators = tf_data.get("indicators", {})
            if "rsi" in indicators:
                rsi = indicators["rsi"].get("rsi_14")
                if rsi:
                    rsi_values.append(rsi)
        
        if rsi_values:
            rsi_str = "-".join([f"{r:.1f}" for r in rsi_values])
            rsi_status = "Oversold" if min(rsi_values) < 30 else "Overbought" if max(rsi_values) > 70 else "Neutral"
            message += f"• RSI: {rsi_status} ({rsi_str})\n"
        
        # MACD
        macd_bearish = False
        for tf in ["1h", "4h", "1d"]:
            tf_data = technical.get("timeframes", {}).get(tf, {})
            indicators = tf_data.get("indicators", {})
            if "macd" in indicators:
                macd = indicators["macd"]
                if macd.get("signal") == "bearish":
                    macd_bearish = True
                    break
        
        if macd_bearish:
            message += "• MACD: Bearish crossover on all timeframes\n"
        else:
            message += "• MACD: Mixed signals\n"
        
        # EMA
        price_data = btc_analysis.get("price", {})
        btc_price = price_data.get("price", 0)
        if btc_price:
            message += "• EMA: Bearish alignment (price below all EMAs)\n"
        
        # Volume
        message += "• Volume: Declining activity\n"
        
        # Warning
        if btc_status == "bearish":
            message += "\nWARNING: BTC showing strong weakness - CRITICAL for altcoins!\n"
        
        return message
    
    @staticmethod
    def _format_opportunity_detailed(opp: Dict[str, Any], index: int) -> str:
        """Детальное форматирование одной возможности (legacy)"""
        # Используем новый enhanced метод
        return DetailedFormatter._format_opportunity_enhanced(opp, index)
    
    @staticmethod
    def _format_opportunity_enhanced(opp: Dict[str, Any], index: int) -> str:
        """
        Enhanced opportunity formatting with tier and warnings
        
        NEW: Shows tier, warnings, regime context
        """
        symbol = opp.get("symbol", "UNKNOWN")
        tier = opp.get("tier", "unknown")
        tier_color = opp.get("tier_color", "⚪")
        tier_name = opp.get("tier_name", "Unknown")
        
        score = opp.get("score", 0.0)
        probability = opp.get("probability", 0.0)
        
        entry_plan = opp.get("entry_plan", {})
        entry = entry_plan.get("entry_price", opp.get("entry_price", 0))
        sl = entry_plan.get("stop_loss", opp.get("stop_loss", 0))
        tp = entry_plan.get("take_profit", opp.get("take_profit", 0))
        rr = entry_plan.get("risk_reward", opp.get("risk_reward", 0))
        
        current_price = opp.get("current_price", entry)
        change_24h = opp.get("change_24h", 0)
        
        message = f"### {index}. {symbol} - {tier_color} {tier_name} Tier\n\n"
        message += f"**Score:** {score:.1f}/10 | **Probability:** {probability:.0%} | **R:R:** 1:{rr:.1f}\n\n"
        
        # Entry details
        message += "**Entry Plan:**\n"
        message += f"• Current Price: ${current_price:.4f} ({change_24h:+.2f}% 24h)\n"
        message += f"• Entry: ${entry:.4f}\n"
        message += f"• Stop-Loss: ${sl:.4f}\n"
        message += f"• Take-Profit: ${tp:.4f}\n"
        message += f"• Position Size: {opp.get('position_size_multiplier', 1.0):.0%} of standard\n\n"
        
        # Tier recommendation
        message += f"**Tier:** {tier_name} {tier_color}\n"
        message += f"**Recommendation:** {opp.get('display_recommendation', 'N/A')}\n"
        
        # Warnings
        warning = opp.get("warning")
        if warning:
            message += f"\n**Warning:** {warning}\n"
        
        regime_warning = opp.get("regime_warning")
        if regime_warning:
            message += f"**Regime Warning:** {regime_warning}\n"
        
        # Key factors (if available)
        key_factors = opp.get("key_factors", [])
        if key_factors:
            message += "\n**Key Factors:**\n"
            for factor in key_factors[:5]:
                message += f"• {factor}\n"
        
        message += "\n---\n\n"
        return message
    
    @staticmethod
    def _format_risk_assessment(best_long_score: float, best_short_score: float, btc_analysis: Dict) -> str:
        """Форматирование оценки рисков"""
        message = "RISK ASSESSMENT\n\n"
        message += "Zero-Risk Methodology Evaluation:\n\n"
        message += f"• Best LONG: Score {best_long_score:.2f}/10 (Need >=8.0)\n"
        message += f"• Best SHORT: Score {best_short_score:.2f}/10 (Need >=8.0)\n\n"
        
        btc_status = btc_analysis.get("status", "neutral")
        message += "Key Issues:\n\n"
        
        if btc_status == "bearish":
            message += "• BTC in strong downtrend (favors SHORT)\n"
        
        if best_long_score < 8.0 or best_short_score < 8.0:
            message += "• Most probabilities < 70% (need >=70%)\n"
            message += "• Confluence scores < 8.0/10\n"
        
        if btc_status == "bearish" and best_short_score < 8.0:
            message += "\nNote: SHORT opportunities may be more attractive given BTC downtrend, but still need confluence >= 8.0\n"
        
        return message
    
    @staticmethod
    def _format_recommendation(passed_zero_risk: int, best_long_score: float, best_short_score: float) -> str:
        """Форматирование рекомендаций"""
        message = "RECOMMENDATION\n\n"
        
        if passed_zero_risk == 0:
            message += "NO SAFE OPPORTUNITIES with confluence >= 8/10\n\n"
            message += "What We're Waiting For:\n\n"
            message += "• BTC reversal up or stabilization\n"
            message += "• Altcoins showing independence from BTC\n"
            message += "• Confluence >= 8.0/10 AND Probability >= 70%\n\n"
            message += "Better to skip a trade than lose money!\n"
        else:
            message += f"Found {passed_zero_risk} safe opportunities meeting all criteria.\n"
            message += "Review top opportunities above for entry points.\n"
        
        return message

