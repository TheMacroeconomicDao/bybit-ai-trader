# ═══════════════════════════════════════════════════════════
# FILE: mcp_server/ml_probability_predictor.py
# PURPOSE: ML Probability Predictor - Learn from historical signal outcomes
# VERSION: 3.0 INSTITUTIONAL (OPTIONAL)
# ═══════════════════════════════════════════════════════════

"""
ML Probability Predictor - Learn from historical signal outcomes
Uses RandomForest to predict win probability based on setup characteristics

FEATURES:
- confluence_score (0-10)
- volume_ratio (vs average)
- btc_aligned (boolean)
- rsi_14 (RSI value)
- risk_reward (R:R ratio)
- pattern_type (encoded)
- session (encoded)

TARGET:
- win/loss from SignalTracker

MODEL:
- RandomForestClassifier (100 trees, max_depth=10)
- Simple, interpretable, fast
"""

from typing import Dict, Any, Optional, List
import numpy as np
from loguru import logger
from datetime import datetime
from pathlib import Path

# Optional ML dependencies
try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import StandardScaler
    import joblib
    SKLEARN_AVAILABLE = True
except ImportError:
    logger.warning("scikit-learn not available, ML predictions disabled")
    SKLEARN_AVAILABLE = False
    RandomForestClassifier = None
    StandardScaler = None
    joblib = None


class MLProbabilityPredictor:
    """
    ML-enhanced probability prediction
    
    Learns from historical signal outcomes to improve probability estimates
    Falls back to static formula if ML unavailable or insufficient data
    """
    
    def __init__(self, model_path: str = "data/ml_models/probability_model.pkl"):
        """Initialize ML predictor"""
        self.model_path = Path(model_path)
        self.model: Optional[Any] = None
        self.scaler: Optional[Any] = None
        self.enabled = SKLEARN_AVAILABLE
        
        self.feature_names = [
            "confluence_score",
            "volume_ratio",
            "btc_aligned",
            "rsi_14",
            "risk_reward",
            "pattern_encoded",
            "session_encoded"
        ]
        
        if self.enabled:
            self._load_model()
        else:
            logger.warning("ML predictor disabled (sklearn not available)")
    
    def model_available(self) -> bool:
        """Check if ML model is loaded and ready"""
        return self.enabled and self.model is not None and self.scaler is not None
    
    def _load_model(self):
        """Load trained model from disk"""
        if not self.model_path.exists():
            logger.info(f"No ML model found at {self.model_path}")
            return
        
        try:
            data = joblib.load(self.model_path)
            self.model = data["model"]
            self.scaler = data["scaler"]
            trained_on = data.get("trained_on", "unknown")
            timestamp = data.get("timestamp", "unknown")
            
            logger.info(
                f"ML probability model loaded: "
                f"trained on {trained_on} signals ({timestamp})"
            )
        except Exception as e:
            logger.error(f"Failed to load ML model: {e}")
            self.model = None
            self.scaler = None
    
    def predict_probability(
        self,
        confluence_score: float,
        volume_ratio: float,
        btc_aligned: bool,
        rsi_14: float,
        risk_reward: float,
        pattern_type: str = "unknown",
        session: str = "neutral"
    ) -> float:
        """
        Predict win probability using ML model
        
        Args:
            confluence_score: Normalized score (0-10)
            volume_ratio: Volume vs avg
            btc_aligned: Whether BTC supports direction
            rsi_14: RSI value
            risk_reward: R:R ratio
            pattern_type: Pattern name
            session: Trading session
            
        Returns:
            Predicted probability (0-1)
            Falls back to static calc if ML unavailable
        """
        if not self.model_available():
            # Fallback to static
            return self._static_probability(confluence_score, risk_reward)
        
        try:
            # Encode features
            features = self._encode_features(
                confluence_score,
                volume_ratio,
                btc_aligned,
                rsi_14,
                risk_reward,
                pattern_type,
                session
            )
            
            # Scale
            features_scaled = self.scaler.transform([features])
            
            # Predict
            prob = self.model.predict_proba(features_scaled)[0][1]
            
            # Clip to reasonable range (never 100% or 0%)
            prob = np.clip(prob, 0.35, 0.95)
            
            logger.debug(f"ML prediction: {prob:.2f} for score={confluence_score:.1f}")
            return float(prob)
            
        except Exception as e:
            logger.error(f"ML prediction failed: {e}")
            return self._static_probability(confluence_score, risk_reward)
    
    def _encode_features(
        self,
        confluence_score: float,
        volume_ratio: float,
        btc_aligned: bool,
        rsi_14: float,
        risk_reward: float,
        pattern_type: str,
        session: str
    ) -> List[float]:
        """Encode features for ML model"""
        
        # Pattern encoding
        pattern_map = {
            "unknown": 0,
            "oversold_bounce": 1,
            "breakout": 2,
            "trend_following": 3,
            "reversal": 4,
            "engulfing": 5,
            "hammer": 6,
            "flag": 7
        }
        pattern_encoded = pattern_map.get(pattern_type.lower(), 0)
        
        # Session encoding
        session_map = {
            "neutral": 0,
            "asian": 1,
            "european": 2,
            "us": 3,
            "overlap": 4
        }
        session_encoded = session_map.get(session.lower(), 0)
        
        return [
            float(confluence_score),
            float(volume_ratio),
            1.0 if btc_aligned else 0.0,
            float(rsi_14),
            float(risk_reward),
            float(pattern_encoded),
            float(session_encoded)
        ]
    
    def _static_probability(self, confluence_score: float, risk_reward: float) -> float:
        """
        Fallback static probability calculation
        
        Formula:
        base = 0.50 + (score - 7.0) × 0.03
        rr_bonus = min(0.10, (rr - 2.0) × 0.03)
        final = base + rr_bonus
        """
        base_prob = 0.50 + (confluence_score - 7.0) * 0.03
        rr_bonus = min(0.10, (risk_reward - 2.0) * 0.03)
        prob = base_prob + rr_bonus
        
        return round(np.clip(prob, 0.35, 0.85), 2)
    
    async def train_from_tracker(self, signal_tracker) -> bool:
        """
        Train model from SignalTracker historical data
        
        This should be run periodically (e.g., weekly) to update model
        
        Args:
            signal_tracker: SignalTracker instance with historical data
            
        Returns:
            True if training successful
        """
        if not self.enabled:
            logger.warning("ML training disabled (sklearn not available)")
            return False
        
        logger.info("Training ML probability model from historical signals...")
        
        try:
            # Get completed signals
            completed_signals = await self._get_completed_signals(signal_tracker)
            
            if len(completed_signals) < 30:
                logger.warning(
                    f"Insufficient data for training: {len(completed_signals)} signals "
                    f"(need minimum 30)"
                )
                return False
            
            # Prepare training data
            X, y = self._prepare_training_data(completed_signals)
            
            if len(X) == 0:
                logger.error("No valid training data after preparation")
                return False
            
            # Initialize model and scaler
            self.model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42,
                n_jobs=-1
            )
            self.scaler = StandardScaler()
            
            # Fit
            X_scaled = self.scaler.fit_transform(X)
            self.model.fit(X_scaled, y)
            
            # Calculate accuracy
            train_accuracy = self.model.score(X_scaled, y)
            
            # Save model
            self.model_path.parent.mkdir(parents=True, exist_ok=True)
            joblib.dump({
                "model": self.model,
                "scaler": self.scaler,
                "feature_names": self.feature_names,
                "trained_on": len(completed_signals),
                "train_accuracy": train_accuracy,
                "timestamp": datetime.now().isoformat()
            }, self.model_path)
            
            logger.info(
                f"✅ ML model trained on {len(completed_signals)} signals "
                f"(accuracy: {train_accuracy:.2%}) and saved"
            )
            return True
            
        except Exception as e:
            logger.error(f"Model training failed: {e}", exc_info=True)
            return False
    
    async def _get_completed_signals(self, signal_tracker) -> List[Dict]:
        """Get completed signals from tracker"""
        # Get signals from last 90 days with results
        cursor = signal_tracker.conn.cursor()
        cursor.execute("""
            SELECT * FROM signals
            WHERE status = 'completed'
            AND result IN ('tp_hit', 'sl_hit')
            AND created_at >= date('now', '-90 days')
            ORDER BY created_at DESC
        """)
        
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    def _prepare_training_data(self, signals: List[Dict]) -> tuple:
        """
        Prepare X (features) and y (labels) for training
        
        Returns:
            (X, y) as numpy arrays
        """
        X = []
        y = []
        
        for signal in signals:
            try:
                # Parse analysis_data if JSON
                analysis_data = signal.get("analysis_data")
                if isinstance(analysis_data, str):
                    import json
                    analysis_data = json.loads(analysis_data)
                
                # Extract features
                confluence_score = signal.get("confluence_score", 7.0)
                risk_reward = signal.get("risk_reward", 2.0)
                pattern_type = signal.get("pattern_type", "unknown")
                
                # Extract from analysis_data
                volume_ratio = 1.0
                btc_aligned = False
                rsi_14 = 50.0
                session = "neutral"
                
                if analysis_data:
                    # Try to extract volume_ratio
                    for tf_data in analysis_data.get("timeframes", {}).values():
                        vol = tf_data.get("indicators", {}).get("volume", {})
                        if vol.get("volume_ratio"):
                            volume_ratio = vol["volume_ratio"]
                            break
                    
                    # Try to extract RSI
                    for tf_data in analysis_data.get("timeframes", {}).values():
                        rsi = tf_data.get("indicators", {}).get("rsi", {})
                        if rsi.get("rsi_14"):
                            rsi_14 = rsi["rsi_14"]
                            break
                
                # Encode features
                features = self._encode_features(
                    confluence_score,
                    volume_ratio,
                    btc_aligned,
                    rsi_14,
                    risk_reward,
                    pattern_type,
                    session
                )
                X.append(features)
                
                # Label: 1 for win, 0 for loss
                result = signal.get("result", "")
                label = 1 if result == "tp_hit" else 0
                y.append(label)
                
            except Exception as e:
                logger.warning(f"Failed to process signal {signal.get('signal_id')}: {e}")
                continue
        
        return np.array(X), np.array(y)