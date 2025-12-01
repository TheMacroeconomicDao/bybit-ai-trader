"""
Validation Engine для проверки торговых возможностей
Основан на 7_zero_risk_methodology.md и entry_decision_framework.md
"""

from typing import Dict, Any, List
from loguru import logger


class ValidationEngine:
    """
    Движок валидации торговых возможностей
    
    Проверяет:
    1. Критерии безопасного входа (8/10 минимум)
    2. Confluence scoring matrix
    3. Probability estimation
    4. Risk/Reward calculation
    """
    
    def __init__(self):
        """Инициализация validation engine"""
        pass
    
    def validate_opportunity(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """
        Полная валидация возможности
        
        Returns:
            {
                "is_valid": bool,
                "score": float,  # 0-10
                "passed_checks": int,
                "total_checks": int,
                "checklist": {...},
                "warnings": [...],
                "recommendations": [...]
            }
        """
        
        checklist = self._run_checklist(opportunity)
        passed_checks = sum(1 for v in checklist.values() if v)
        total_checks = len(checklist)
        
        # Минимум 8/10 критериев должно быть выполнено
        is_valid = passed_checks >= 8
        
        # Расчёт score на основе checklist
        score = (passed_checks / total_checks) * 10
        
        # Сбор предупреждений
        warnings = self._collect_warnings(opportunity, checklist)
        
        # Рекомендации
        recommendations = self._generate_recommendations(opportunity, checklist)
        
        return {
            "is_valid": is_valid,
            "score": round(score, 1),
            "passed_checks": passed_checks,
            "total_checks": total_checks,
            "checklist": checklist,
            "warnings": warnings,
            "recommendations": recommendations
        }
    
    def _run_checklist(self, opp: Dict[str, Any]) -> Dict[str, bool]:
        """
        Чеклист из 7_zero_risk_methodology.md
        
        10 критериев безопасного входа:
        1. ✅ Trend alignment (все таймфреймы согласны)
        2. ✅ Множественные индикаторы (минимум 5)
        3. ✅ Сильный уровень S/R
        4. ✅ Volume confirmation
        5. ✅ Паттерн с высокой вероятностью (>70%)
        6. ✅ Хороший R:R (минимум 1:2)
        7. ✅ Благоприятные рыночные условия
        8. ✅ BTC поддерживает движение
        9. ✅ Нет негативного sentiment
        10.✅ On-chain данные поддерживают
        """
        
        checklist = {}
        
        # 1. Trend Alignment
        analysis = opp.get("full_analysis", {})
        timeframes = analysis.get("timeframes", {})
        
        # Подсчитываем aligned таймфреймы
        aligned_count = 0
        side = opp.get("side", "long").lower()
        
        for tf_data in timeframes.values():
            trend = tf_data.get("trend", {})
            direction = trend.get("direction", "").lower()
            
            if side == "long":
                if direction in ["uptrend", "bullish", "rising"]:
                    aligned_count += 1
            else:  # short
                if direction in ["downtrend", "bearish", "falling"]:
                    aligned_count += 1
        
        checklist["trend_alignment"] = aligned_count >= 3  # Минимум 3/4 TF
        
        # 2. Multiple Indicators
        confirmed_indicators = 0
        
        # Проверяем индикаторы на всех таймфреймах
        for tf_data in timeframes.values():
            indicators = tf_data.get("indicators", {})
            
            # RSI
            rsi = indicators.get("rsi", {})
            rsi_value = rsi.get("rsi_14", 50)
            if side == "long" and rsi_value < 35:
                confirmed_indicators += 1
            elif side == "short" and rsi_value > 65:
                confirmed_indicators += 1
            
            # MACD
            macd = indicators.get("macd", {})
            histogram = macd.get("histogram", 0)
            if side == "long" and histogram > 0:
                confirmed_indicators += 1
            elif side == "short" and histogram < 0:
                confirmed_indicators += 1
            
            # Bollinger Bands
            bb = indicators.get("bollinger_bands", {})
            bb_position = bb.get("position", "middle")
            if side == "long" and bb_position == "lower":
                confirmed_indicators += 1
            elif side == "short" and bb_position == "upper":
                confirmed_indicators += 1
            
            # EMA
            ema = indicators.get("ema", {})
            if ema:
                price_above_ema = ema.get("price_above_ema_50", False)
                if side == "long" and price_above_ema:
                    confirmed_indicators += 1
                elif side == "short" and not price_above_ema:
                    confirmed_indicators += 1
        
        # Также проверяем общий счетчик если есть
        confirmed_indicators = max(
            confirmed_indicators,
            opp.get("confirmed_indicators_count", 0)
        )
        
        checklist["multiple_indicators"] = confirmed_indicators >= 5
        
        # 3. Strong S/R Level
        # Проверяем наличие уровней поддержки/сопротивления
        sr_levels = opp.get("support_resistance", {})
        has_strong_level = False
        
        if side == "long":
            support = sr_levels.get("support", [])
            entry_price = opp.get("entry_price", 0)
            # Проверяем что цена близко к поддержке
            for level in support:
                if abs(entry_price - level) / entry_price < 0.02:  # В пределах 2%
                    has_strong_level = True
                    break
        else:  # short
            resistance = sr_levels.get("resistance", [])
            entry_price = opp.get("entry_price", 0)
            for level in resistance:
                if abs(entry_price - level) / entry_price < 0.02:
                    has_strong_level = True
                    break
        
        checklist["strong_sr_level"] = has_strong_level or opp.get("near_support", False) or opp.get("near_resistance", False)
        
        # 4. Volume Confirmation
        volume_ratio = opp.get("volume_ratio", 1.0)
        checklist["volume_confirmation"] = volume_ratio >= 1.5
        
        # 5. Pattern Reliability
        pattern_success = opp.get("pattern_success_rate", 0)
        if pattern_success == 0:
            # Пробуем получить из analysis
            patterns = analysis.get("patterns", [])
            if patterns:
                # Берем максимальный success rate из паттернов
                pattern_success = max(
                    p.get("reliability", 0) / 100.0 if isinstance(p.get("reliability"), (int, float)) else 0
                    for p in patterns
                    if isinstance(p, dict)
                )
        
        checklist["pattern_reliability"] = pattern_success >= 0.70
        
        # 6. Good R:R
        rr_ratio = opp.get("risk_reward", 0)
        if rr_ratio == 0:
            # Рассчитываем из entry, stop_loss, take_profit
            entry = opp.get("entry_price", 0)
            stop_loss = opp.get("stop_loss", 0)
            take_profit = opp.get("take_profit", 0)
            
            if entry > 0 and stop_loss > 0 and take_profit > 0:
                if side == "long":
                    risk = abs(entry - stop_loss)
                    reward = abs(take_profit - entry)
                else:  # short
                    risk = abs(stop_loss - entry)
                    reward = abs(entry - take_profit)
                
                if risk > 0:
                    rr_ratio = reward / risk
        
        checklist["good_rr"] = rr_ratio >= 2.0
        
        # 7. Favorable Market Conditions
        market_conditions = opp.get("market_conditions", {})
        volatility = market_conditions.get("volatility", "normal")
        trend_strength = market_conditions.get("trend_strength", "medium")
        
        checklist["favorable_conditions"] = (
            volatility in ["normal", "low"] and
            trend_strength in ["strong", "medium"]
        )
        
        # 8. BTC Support
        btc_status = opp.get("btc_status", "neutral").lower()
        btc_trend = opp.get("btc_trend", "neutral").lower()
        
        if side == "long":
            checklist["btc_support"] = btc_status in ["bullish", "neutral"] or btc_trend in ["bullish", "neutral"]
        else:  # short
            checklist["btc_support"] = btc_status in ["bearish", "neutral"] or btc_trend in ["bearish", "neutral"]
        
        # 9. Positive Sentiment
        sentiment = opp.get("sentiment", "neutral").lower()
        checklist["positive_sentiment"] = sentiment in ["positive", "neutral"]
        
        # 10. On-Chain Support (опционально, но бонус)
        onchain = opp.get("onchain_support", False)
        checklist["onchain_support"] = onchain
        
        return checklist
    
    def _collect_warnings(
        self,
        opp: Dict[str, Any],
        checklist: Dict[str, bool]
    ) -> List[str]:
        """Сбор предупреждений на основе failed checks"""
        
        warnings = []
        
        if not checklist.get("trend_alignment"):
            warnings.append("⚠️ Недостаточное выравнивание таймфреймов (нужно минимум 3/4)")
        
        if not checklist.get("multiple_indicators"):
            warnings.append("⚠️ Мало подтверждающих индикаторов (нужно минимум 5)")
        
        if not checklist.get("strong_sr_level"):
            warnings.append("⚠️ Слабый уровень поддержки/сопротивления")
        
        if not checklist.get("volume_confirmation"):
            warnings.append("⚠️ Слабое подтверждение объемом (volume_ratio < 1.5)")
        
        if not checklist.get("pattern_reliability"):
            warnings.append("⚠️ Паттерн с низкой надежностью (<70%)")
        
        if not checklist.get("good_rr"):
            warnings.append("⚠️ R:R ниже минимума 1:2")
        
        if not checklist.get("favorable_conditions"):
            warnings.append("⚠️ Неблагоприятные рыночные условия")
        
        if not checklist.get("btc_support"):
            warnings.append("⚠️ BTC не поддерживает движение")
        
        if not checklist.get("positive_sentiment"):
            warnings.append("⚠️ Негативный sentiment")
        
        return warnings
    
    def _generate_recommendations(
        self,
        opp: Dict[str, Any],
        checklist: Dict[str, bool]
    ) -> List[str]:
        """Генерация рекомендаций для улучшения setup"""
        
        recommendations = []
        
        passed = sum(1 for v in checklist.values() if v)
        total = len(checklist)
        score = (passed / total) * 10
        
        if score >= 8.0:
            recommendations.append("✅ ОТКРЫВАТЬ - качественный setup")
            recommendations.append(f"Confluence score: {score:.1f}/10")
        elif score >= 7.0:
            recommendations.append("⚠️ ОСТОРОЖНО - допустимый setup, но не идеальный")
            recommendations.append("Рекомендуется уменьшить размер позиции")
            recommendations.append(f"Confluence score: {score:.1f}/10 (минимум 8.0)")
        else:
            recommendations.append("❌ ПОДОЖДАТЬ - setup слишком слабый")
            recommendations.append("Ждать улучшения confluence")
            recommendations.append(f"Confluence score: {score:.1f}/10 (нужно минимум 8.0)")
        
        # Специфичные рекомендации
        if not checklist.get("trend_alignment"):
            recommendations.append("→ Дождаться выравнивания большего количества таймфреймов")
        
        if not checklist.get("volume_confirmation"):
            recommendations.append("→ Дождаться увеличения объема")
        
        if not checklist.get("btc_support"):
            recommendations.append("→ Дождаться поддержки от BTC")
        
        return recommendations









