"""
ML Pattern Success Predictor
Lightweight implementation для quick deployment
"""
from typing import Dict, List, Any, Optional
from loguru import logger


class MLPredictor:
    """
    Простой ML predictor на основе исторических данных
    Fallback на heuristic если модель не обучена
    """
    
    def __init__(self):
        self.pattern_success_db = self._init_pattern_database()
        self.trained = False
        logger.info("ML Predictor initialized (heuristic mode)")
    
    def predict_success_probability(
        self,
        confluence_score: float,
        pattern_type: str = "unknown",
        volume_ratio: float = 1.0,
        btc_aligned: bool = False,
        session: str = "neutral",
        rsi: float = 50.0,
        risk_reward: float = 2.0,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Predict success probability на основе confluence и контекста
        
        Args:
            confluence_score: Confluence score (0-20)
            pattern_type: Тип паттерна (bull_flag, bear_flag, etc.)
            volume_ratio: Отношение объема к среднему
            btc_aligned: Совпадает ли направление с BTC
            session: Торговая сессия (asian, european, us, overlap)
            rsi: Текущий RSI
            risk_reward: Risk:Reward ratio
            **kwargs: Дополнительные параметры
        
        Returns:
            {
                "predicted_probability": float,
                "confidence": float,
                "adjustment": float,
                "method": str
            }
        """
        
        # Base probability от confluence (0-20 scale)
        base_prob = min(0.95, max(0.30, (confluence_score / 20.0) * 1.4))
        
        # Pattern historical adjustment
        pattern_key = pattern_type.lower() if pattern_type else "unknown"
        pattern_data = self.pattern_success_db.get(pattern_key, {})
        historical_wr = pattern_data.get('win_rate', 0.70)
        
        # Pattern bonus/penalty (отклонение от среднего 70%)
        pattern_adj = (historical_wr - 0.70) * 0.5
        
        # Session bonus
        session_bonus = 0.0
        if session == "overlap":
            session_bonus = 0.05
        elif session in ["european", "us"]:
            session_bonus = 0.02
        
        # BTC alignment bonus
        btc_bonus = 0.03 if btc_aligned else -0.02
        
        # Volume bonus (только если volume выше среднего)
        vol_bonus = 0.0
        if volume_ratio > 1.0:
            vol_bonus = min(0.05, (volume_ratio - 1.0) * 0.05)
        
        # RSI adjustment (экстремальные значения увеличивают вероятность)
        rsi_adj = 0.0
        if rsi < 30:  # Oversold
            rsi_adj = 0.02
        elif rsi > 70:  # Overbought
            rsi_adj = 0.02
        
        # R:R bonus
        rr_bonus = 0.0
        if risk_reward >= 3.0:
            rr_bonus = 0.03
        elif risk_reward >= 2.5:
            rr_bonus = 0.02
        elif risk_reward >= 2.0:
            rr_bonus = 0.01
        
        # Final calculation
        final_prob = base_prob + pattern_adj + session_bonus + btc_bonus + vol_bonus + rsi_adj + rr_bonus
        final_prob = min(0.95, max(0.30, final_prob))
        
        # Confidence зависит от количества факторов
        factors_count = sum([
            1 if pattern_adj != 0 else 0,
            1 if session_bonus > 0 else 0,
            1 if btc_bonus > 0 else 0,
            1 if vol_bonus > 0 else 0,
            1 if rsi_adj > 0 else 0,
            1 if rr_bonus > 0 else 0
        ])
        
        confidence = min(0.90, 0.60 + (factors_count * 0.05))
        
        return {
            "predicted_probability": round(final_prob, 3),
            "confidence": round(confidence, 2),
            "adjustment": round(final_prob - base_prob, 3),
            "base_probability": round(base_prob, 2),
            "pattern_adjustment": round(pattern_adj, 3),
            "session_bonus": round(session_bonus, 3),
            "btc_bonus": round(btc_bonus, 3),
            "volume_bonus": round(vol_bonus, 3),
            "rsi_adjustment": round(rsi_adj, 3),
            "rr_bonus": round(rr_bonus, 3),
            "method": "heuristic_enhanced"
        }
    
    def _init_pattern_database(self) -> Dict[str, Dict]:
        """
        Historical pattern win rates (simplified)
        На основе статистики реальных паттернов
        """
        return {
            "bull_flag": {"win_rate": 0.78, "avg_rr": 2.3},
            "bear_flag": {"win_rate": 0.75, "avg_rr": 2.2},
            "hammer": {"win_rate": 0.65, "avg_rr": 1.8},
            "engulfing": {"win_rate": 0.70, "avg_rr": 2.0},
            "triangle": {"win_rate": 0.68, "avg_rr": 2.5},
            "head_shoulders": {"win_rate": 0.76, "avg_rr": 2.8},
            "double_bottom": {"win_rate": 0.72, "avg_rr": 2.2},
            "double_top": {"win_rate": 0.74, "avg_rr": 2.3},
            "pullback": {"win_rate": 0.75, "avg_rr": 2.0},
            "breakout": {"win_rate": 0.65, "avg_rr": 2.5},
            "reversal": {"win_rate": 0.68, "avg_rr": 2.0},
            "unknown": {"win_rate": 0.70, "avg_rr": 2.0}
        }









