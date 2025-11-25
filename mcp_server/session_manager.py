"""Trading Session Manager"""
from typing import Dict, Any
from datetime import datetime
import pytz
from loguru import logger


class SessionManager:
    """Управление торговыми сессиями (Asian, European, US, Overlap)"""
    
    def __init__(self):
        self.asian_tz = pytz.timezone('Asia/Tokyo')
        self.european_tz = pytz.timezone('Europe/London')
        self.us_tz = pytz.timezone('America/New_York')
        logger.info("Session Manager initialized")
    
    def get_current_session(self) -> str:
        """
        Определяет текущую торговую сессию
        
        Returns:
            "asian", "european", "us", "overlap"
        """
        now = datetime.now(pytz.UTC)
        
        # Конвертируем в локальные времена
        asian_time = now.astimezone(self.asian_tz)
        european_time = now.astimezone(self.european_tz)
        us_time = now.astimezone(self.us_tz)
        
        asian_hour = asian_time.hour
        european_hour = european_time.hour
        us_hour = us_time.hour
        
        # Asian: 00:00 - 09:00 UTC (09:00 - 18:00 Tokyo)
        # European: 07:00 - 16:00 UTC (08:00 - 17:00 London)
        # US: 13:00 - 22:00 UTC (08:00 - 17:00 New York)
        # Overlap EU+US: 13:00 - 16:00 UTC
        
        utc_hour = now.hour
        
        # Overlap (European + US)
        if 13 <= utc_hour < 16:
            return "overlap"
        
        # US session
        elif 13 <= utc_hour < 22:
            return "us"
        
        # European session
        elif 7 <= utc_hour < 16:
            return "european"
        
        # Asian session
        else:
            return "asian"
    
    def get_session_info(self) -> Dict[str, Any]:
        """
        Получить детальную информацию о текущей сессии
        
        Returns:
            Dict с информацией о сессии
        """
        session = self.get_current_session()
        
        session_data = {
            "asian": {
                "name": "Asian Session",
                "hours_utc": "00:00 - 09:00",
                "volatility": "low",
                "best_for": "range trading, accumulation",
                "average_volatility": 0.8
            },
            "european": {
                "name": "European Session",
                "hours_utc": "07:00 - 16:00",
                "volatility": "medium",
                "best_for": "trend continuation",
                "average_volatility": 1.0
            },
            "us": {
                "name": "US Session",
                "hours_utc": "13:00 - 22:00",
                "volatility": "high",
                "best_for": "breakouts, momentum",
                "average_volatility": 1.2
            },
            "overlap": {
                "name": "European + US Overlap",
                "hours_utc": "13:00 - 16:00",
                "volatility": "very_high",
                "best_for": "strong moves, high volume",
                "average_volatility": 1.3
            }
        }
        
        current_info = session_data.get(session, session_data["asian"])
        
        return {
            "current_session": session,
            "name": current_info["name"],
            "hours_utc": current_info["hours_utc"],
            "volatility": current_info["volatility"],
            "best_for": current_info["best_for"],
            "average_volatility": current_info["average_volatility"],
            "timestamp": datetime.now().isoformat()
        }
    
    def get_multiplier(self) -> float:
        """
        Получить множитель размера позиции для текущей сессии
        
        Returns:
            Множитель (0.7 для Asian, 1.0 для European, 1.2 для US, 1.3 для Overlap)
        """
        multipliers = {
            "asian": 0.7,
            "european": 1.0,
            "us": 1.2,
            "overlap": 1.3
        }
        
        session = self.get_current_session()
        return multipliers.get(session, 1.0)


