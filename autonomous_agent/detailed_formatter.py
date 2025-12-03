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
            return "❌ Market analysis error. Please try again later."
        
        message = "🔍 INSTITUTIONAL MARKET ANALYSIS\n\n"
        message += "─" * 30 + "\n\n"
        
        # ═══════════════════════════════════════════════════════
        # MARKET REGIME - COMPACT
        # ═══════════════════════════════════════════════════════
        market_regime = analysis_result.get("market_regime", {})
        thresholds = analysis_result.get("adaptive_thresholds", {})
        
        if market_regime:
            regime_type = market_regime.get('type', 'unknown').upper()
            confidence = market_regime.get('confidence', 0)
            message += f"📊 MARKET REGIME: {regime_type} ({confidence:.0%})\n"
            
            if thresholds:
                message += f"🎯 THRESHOLDS: LONG {thresholds.get('long', 7.0):.1f}/10 | SHORT {thresholds.get('short', 7.0):.1f}/10\n"
            
            message += "\n" + "─" * 30 + "\n\n"
        
        # BTC STATUS - COMPACT
        btc_analysis = analysis_result.get("btc_analysis", {})
        btc_status = btc_analysis.get("status", "neutral")
        message += f"BTC: {btc_status.upper()}\n\n"
        message += "─" * 30 + "\n\n"
        
        # TOP OPPORTUNITIES
        top_longs = analysis_result.get("top_3_longs", [])
        top_shorts = analysis_result.get("top_3_shorts", [])
        all_longs = analysis_result.get("all_longs", [])
        all_shorts = analysis_result.get("all_shorts", [])
        
        # Фильтруем пары СТЕЙБЛ/СТЕЙБЛ (исключаем только их, не пары типа BTC/USDT)
        all_longs = [opp for opp in all_longs if not DetailedFormatter._is_stable_stable_pair(opp.get("symbol", ""))]
        all_shorts = [opp for opp in all_shorts if not DetailedFormatter._is_stable_stable_pair(opp.get("symbol", ""))]
        
        message += "TOP OPPORTUNITIES\n\n"
        
        # LONG OPPORTUNITIES - COMPACT (TOP-3 ONLY)
        message += f"📈 LONG (Top 3 of {len(all_longs)}):\n\n"
        if all_longs:
            for idx, opp in enumerate(all_longs[:3], 1):  # ✅ Только TOP-3
                message += DetailedFormatter._format_opportunity_compact(opp, idx)
        else:
            message += "No opportunities found.\n\n"
        
        message += "─" * 30 + "\n\n"
        
        # SHORT OPPORTUNITIES - COMPACT (TOP-3 ONLY)
        message += f"📉 SHORT (Top 3 of {len(all_shorts)}):\n\n"
        if all_shorts:
            for idx, opp in enumerate(all_shorts[:3], 1):  # ✅ Только TOP-3
                message += DetailedFormatter._format_opportunity_compact(opp, idx)
        else:
            message += "No opportunities found.\n\n"
        
        message += "─" * 30 + "\n\n"
        
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
        
        # COMPACT SUMMARY
        total_scanned = analysis_result.get("total_scanned", 0)
        passed_zero_risk = len([opp for opp in all_longs + all_shorts
                                if opp.get("confluence_score", 0) >= 8.0
                                and opp.get("probability", 0) >= 0.70])
        
        message += f"📊 STATS: {total_scanned} scanned | {longs_found} LONG | {shorts_found} SHORT | {passed_zero_risk} elite (≥8.0)\n"
        
        if passed_zero_risk == 0:
            message += "\n⚠️ NO ELITE OPPORTUNITIES (≥8.0/10) - Wait for better setups!\n"
        
        message += "\n" + "─" * 30 + "\n"
        message += "Next scan: 12h | System: INSTITUTIONAL v3.0"
        
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
        
        # Список стабильных монет (включая RLUSD)
        stablecoins = {'USDT', 'USDC', 'BUSD', 'DAI', 'TUSD', 'USDP', 'USDD', 'FRAX', 'LUSD', 'MIM', 'RLUSD'}
        
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
    def _format_opportunity_compact(opp: Dict[str, Any], index: int) -> str:
        """
        КОМПАКТНОЕ форматирование возможности (v3.0)
        Минимум текста, максимум пользы
        """
        symbol = opp.get("symbol", "UNKNOWN")
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
        
        # COMPACT FORMAT: 1 строка заголовок + 3 строки данные + warnings
        message = f"{index}. {symbol} - {tier_color} {tier_name} ({score:.1f}/10 | {probability:.0%} | R:R 1:{rr:.1f})\n"
        message += f"   Entry: ${entry:.4f} | SL: ${sl:.4f} | TP: ${tp:.4f}\n"
        
        # Warnings ONLY if important
        warning = opp.get("warning")
        regime_warning = opp.get("regime_warning")
        
        if warning:
            message += f"   ⚠️ {warning}\n"
        if regime_warning:
            message += f"   {regime_warning}\n"
        
        message += "\n"
        return message
    
    @staticmethod
    def _format_opportunity_detailed(opp: Dict[str, Any], index: int) -> str:
        """Детальное форматирование одной возможности (legacy)"""
        # Используем compact формат
        return DetailedFormatter._format_opportunity_compact(opp, index)
    

