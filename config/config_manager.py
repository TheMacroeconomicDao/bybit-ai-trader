"""
Unified Configuration Manager
Единый источник конфигурации для всей системы
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class TradingConfig:
    """Конфигурация системы трейдинга"""
    
    # Bybit API
    bybit_api_key: str
    bybit_api_secret: str
    bybit_testnet: bool = False
    
    # Qwen AI
    qwen_api_key: str
    qwen_model: str = "qwen/qwen-turbo"
    
    # Telegram
    telegram_bot_token: Optional[str] = None
    telegram_chat_ids: Optional[str] = None
    
    # Trading settings
    max_risk_per_trade: float = 0.02
    max_concurrent_positions: int = 3
    daily_loss_limit: float = 0.05
    default_leverage: int = 2
    max_leverage: int = 5
    
    # Agent settings
    min_confluence: float = 8.0
    min_probability: float = 0.70
    min_risk_reward: float = 2.0


class ConfigManager:
    """Менеджер конфигурации с приоритетами"""
    
    def __init__(self, base_path: Optional[Path] = None):
        self.base_path = base_path or Path(__file__).parent.parent
        self._config = None
    
    def load(self) -> TradingConfig:
        """
        Загрузка конфигурации с приоритетами:
        1. Environment variables (высший приоритет)
        2. config/credentials.json
        3. config/autonomous_agent.json
        4. Defaults (низший приоритет)
        """
        config_data = {}
        
        # 1. Загрузка из файлов
        credentials_file = self.base_path / "config" / "credentials.json"
        if credentials_file.exists():
            try:
                with open(credentials_file) as f:
                    creds = json.load(f)
                    if "bybit" in creds:
                        config_data.update(creds["bybit"])
                    if "settings" in creds:
                        config_data.update(creds["settings"])
            except Exception as e:
                print(f"Warning: Failed to load credentials.json: {e}")
        
        agent_config_file = self.base_path / "config" / "autonomous_agent.json"
        if agent_config_file.exists():
            try:
                with open(agent_config_file) as f:
                    config_data.update(json.load(f))
            except Exception as e:
                print(f"Warning: Failed to load autonomous_agent.json: {e}")
        
        # 2. Override с environment variables (приоритет)
        env_mappings = {
            "BYBIT_API_KEY": "bybit_api_key",
            "BYBIT_API_SECRET": "bybit_api_secret",
            "BYBIT_TESTNET": "bybit_testnet",
            "QWEN_API_KEY": "qwen_api_key",
            "QWEN_MODEL": "qwen_model",
            "TELEGRAM_BOT_TOKEN": "telegram_bot_token",
            "TELEGRAM_CHAT_IDS": "telegram_chat_ids",
        }
        
        for env_var, config_key in env_mappings.items():
            value = os.getenv(env_var)
            if value:
                # Конвертация boolean
                if config_key == "bybit_testnet":
                    value = value.lower() in ("true", "1", "yes")
                config_data[config_key] = value
        
        # 3. Создание TradingConfig
        self._config = TradingConfig(**config_data)
        
        # 4. Валидация
        self._validate()
        
        return self._config
    
    def _validate(self):
        """Валидация конфигурации"""
        required = ["bybit_api_key", "bybit_api_secret", "qwen_api_key"]
        missing = [
            k for k in required
            if not getattr(self._config, k, None)
        ]
        
        if missing:
            raise ValueError(
                f"Missing required configuration: {', '.join(missing)}\n"
                f"Set via environment variables or config files"
            )
    
    def get(self) -> TradingConfig:
        """Получить конфигурацию (загрузить если нужно)"""
        if self._config is None:
            self.load()
        return self._config


# Singleton instance
_config_manager = ConfigManager()


def get_config() -> TradingConfig:
    """Получить глобальную конфигурацию"""
    return _config_manager.get()

