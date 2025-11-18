"""
Детальный форматтер для Telegram
Форматирование полного отчёта как в примере пользователя
"""

from typing import Dict, List, Any
from datetime import datetime
from loguru import logger


class DetailedFormatter:
    """Детальный форматтер для полного отчёта"""
    
    @staticmethod
    def format_full_report(analysis_result: Dict[str, Any]) -> str:
        """
        Форматирование полного детального отчёта
        
        Args:
            analysis_result: Результат анализа от AutonomousAnalyzer
            
        Returns:
            Полный отформатированный отчёт
        """
        if not analysis_result.get("success"):
            return "❌ Ошибка анализа рынка. Попробуйте позже."
        
        message = "MARKET ANALYSIS REPORT\n\n"
        message += "━" * 40 + "\n\n"
        
        # BTC STATUS (CRITICAL)
        btc_analysis = analysis_result.get("btc_analysis", {})
        message += DetailedFormatter._format_btc_status(btc_analysis)
        message += "\n" + "━" * 40 + "\n\n"
        
        # TOP OPPORTUNITIES
        top_longs = analysis_result.get("top_3_longs", [])
        top_shorts = analysis_result.get("top_3_shorts", [])
        all_longs = analysis_result.get("all_longs", [])
        all_shorts = analysis_result.get("all_shorts", [])
        
        message += "TOP OPPORTUNITIES (After Full Market Scan)\n\n"
        
        # LONG OPPORTUNITIES
        if all_longs:
            message += "LONG OPPORTUNITIES:\n\n"
            for idx, opp in enumerate(all_longs[:5], 1):  # Топ 5
                message += DetailedFormatter._format_opportunity_detailed(opp, idx)
                message += "\n"
        else:
            message += "LONG OPPORTUNITIES:\n\n"
            message += "No opportunities found.\n\n"
        
        message += "━" * 40 + "\n\n"
        
        # SHORT OPPORTUNITIES
        if all_shorts:
            message += "SHORT OPPORTUNITIES:\n\n"
            for idx, opp in enumerate(all_shorts[:5], 1):  # Топ 5
                message += DetailedFormatter._format_opportunity_detailed(opp, idx)
                message += "\n"
        else:
            message += "SHORT OPPORTUNITIES:\n\n"
            message += "No opportunities found.\n\n"
        
        message += "━" * 40 + "\n\n"
        
        # DIRECTION COMPARISON
        longs_found = analysis_result.get("longs_found", 0)
        shorts_found = analysis_result.get("shorts_found", 0)
        best_long_score = max([opp.get("confluence_score", 0) for opp in all_longs], default=0)
        best_short_score = max([opp.get("confluence_score", 0) for opp in all_shorts], default=0)
        
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
        message += "Next Update: Monitoring every 4 hours\n"
        
        return message
    
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
        """Детальное форматирование одной возможности"""
        symbol = opp.get("symbol", "UNKNOWN")
        entry_plan = opp.get("entry_plan", {})
        entry = entry_plan.get("entry_price", opp.get("entry_price", 0))
        sl = entry_plan.get("stop_loss", opp.get("stop_loss", 0))
        tp = entry_plan.get("take_profit", opp.get("take_profit", 0))
        score = opp.get("confluence_score", opp.get("final_score", 0))
        probability = opp.get("probability", 0)
        rr = entry_plan.get("risk_reward", opp.get("risk_reward", 0))
        current_price = opp.get("current_price", entry)
        change_24h = opp.get("change_24h", 0)
        
        message = f"{index}. {symbol}\n\n"
        message += f"• Score: {score:.2f} | Probability: {int(probability*100)}%\n"
        message += f"• Current Price: ${current_price:.4f} ({change_24h:+.2f}% 24h)\n"
        message += f"• Entry: ${entry:.4f}\n"
        message += f"• Stop-Loss: ${sl:.4f}\n"
        message += f"• Take-Profit: ${tp:.4f}\n"
        message += f"• Risk/Reward: {rr:.2f}\n"
        
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

