"""
OpenRouter Qwen API Client
Клиент для взаимодействия с Qwen через OpenRouter API
OpenRouter предоставляет доступ к моделям Qwen через OpenAI-совместимый API
"""

import json
import asyncio
import aiohttp
from typing import Dict, List, Any, Optional
from loguru import logger


class QwenClient:
    """Клиент для OpenRouter Qwen API (OpenAI-совместимый)"""
    
    # OpenRouter API endpoint (OpenAI-совместимый)
    BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
    
    def __init__(self, api_key: str, model: str = "qwen/qwen-turbo"):
        """
        Инициализация клиента Qwen через OpenRouter
        
        Args:
            api_key: API ключ от OpenRouter (sk-or-v1-...)
            model: Модель Qwen для использования 
                   Доступные:
                   - qwen/qwen-turbo (быстрая, дешёвая)
                   - qwen/qwen-plus (сбалансированная)
                   - qwen/qwen-max (самая мощная)
                   По умолчанию: qwen/qwen-turbo
        """
        self.api_key = api_key
        self.model = model
        self.base_url = self.BASE_URL
        self.available_models = [
            "qwen/qwen-turbo",
            "qwen/qwen-plus", 
            "qwen/qwen-max"
        ]
        
        if not api_key:
            raise ValueError("API key is required for Qwen client")
        
        logger.info(f"Qwen client initialized with OpenRouter, model: {model}")
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        top_p: float = 0.8
    ) -> Dict[str, Any]:
        """
        Генерация ответа от Qwen
        
        Args:
            prompt: Пользовательский промпт
            system_prompt: Системный промпт (опционально)
            temperature: Температура генерации (0-1)
            max_tokens: Максимальное количество токенов
            top_p: Top-p sampling
            
        Returns:
            Ответ от модели с метаданными
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/your-repo",  # Опционально, для отслеживания
            "X-Title": "Trader Agent"  # Опционально, название приложения
        }
        
        # Формируем сообщения в формате OpenAI
        messages = []
        
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        # OpenRouter использует стандартный OpenAI формат
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.base_url,
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Обработка ответа OpenRouter (OpenAI-совместимый формат)
                        if "choices" in data and len(data["choices"]) > 0:
                            choice = data["choices"][0]
                            content = choice.get("message", {}).get("content", "")
                            
                            return {
                                "success": True,
                                "content": content,
                                "usage": data.get("usage", {}),
                                "model": data.get("model", self.model),
                                "id": data.get("id", "")
                            }
                        
                        # Fallback для других форматов ответа
                        logger.warning(f"Unexpected response format: {data}")
                        return {
                            "success": True,
                            "content": json.dumps(data, ensure_ascii=False),
                            "usage": data.get("usage", {}),
                            "model": data.get("model", self.model)
                        }
                    else:
                        error_text = await response.text()
                        logger.error(f"OpenRouter API error {response.status}: {error_text}")
                        
                        # Если модель недоступна, пробуем fallback модели
                        if response.status == 404 or (response.status == 400 and "model" in error_text.lower()):
                            if not hasattr(self, '_fallback_attempted'):
                                logger.warning(f"Model {self.model} is not available, trying fallback models...")
                                self._fallback_attempted = True
                                
                                # Пробуем другие модели по порядку
                                for fallback_model in self.available_models:
                                    if fallback_model != self.model:
                                        logger.info(f"Trying fallback model: {fallback_model}")
                                        fallback_payload = {
                                            "model": fallback_model,
                                            "messages": messages,
                                            "temperature": temperature,
                                            "max_tokens": max_tokens,
                                            "top_p": top_p
                                        }
                                        
                                        try:
                                            async with session.post(
                                                self.base_url,
                                                headers=headers,
                                                json=fallback_payload,
                                                timeout=aiohttp.ClientTimeout(total=60)
                                            ) as fallback_response:
                                                if fallback_response.status == 200:
                                                    fallback_data = await fallback_response.json()
                                                    if "choices" in fallback_data and len(fallback_data["choices"]) > 0:
                                                        content = fallback_data["choices"][0].get("message", {}).get("content", "")
                                                        logger.info(f"Successfully used fallback model: {fallback_model}")
                                                        if hasattr(self, '_fallback_attempted'):
                                                            delattr(self, '_fallback_attempted')
                                                        return {
                                                            "success": True,
                                                            "content": content,
                                                            "usage": fallback_data.get("usage", {}),
                                                            "model_used": fallback_model
                                                        }
                                        except Exception as e:
                                            logger.warning(f"Fallback model {fallback_model} failed: {e}")
                                            continue
                                
                                if hasattr(self, '_fallback_attempted'):
                                    delattr(self, '_fallback_attempted')
                        
                        return {
                            "success": False,
                            "error": f"API error {response.status}: {error_text}",
                            "content": ""
                        }
        
        except asyncio.TimeoutError:
            logger.error("Qwen API request timeout")
            return {
                "success": False,
                "error": "Request timeout",
                "content": ""
            }
        except Exception as e:
            logger.error(f"Qwen API error: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "content": ""
            }
    
    async def analyze_market_opportunities(
        self,
        market_data: Dict[str, Any],
        system_instructions: str
    ) -> Dict[str, Any]:
        """
        Анализ рыночных возможностей через Qwen
        
        Args:
            market_data: Структурированные данные рынка
            system_instructions: Инструкции для модели
            
        Returns:
            Анализ от Qwen с топовыми точками входа
        """
        prompt = f"""
Проанализируй следующие рыночные данные и найди ТОП 3 лучших ЛОНГА и ТОП 3 лучших ШОРТА для торговли.

Рыночные данные:
{json.dumps(market_data, ensure_ascii=False, indent=2)}

Требования:
1. Найди ТОП 3 ЛОНГА с confluence ≥ 8.0/10
2. Найди ТОП 3 ШОРТА с confluence ≥ 8.0/10
3. Вероятность успеха ≥ 70% для каждой возможности
4. R:R минимум 1:2 для каждой возможности
5. Детально объясни каждую возможность
6. Укажи конкретные уровни входа, SL, TP

Формат ответа (JSON):
{{
    "top_longs": [
        {{
            "symbol": "BTC/USDT",
            "side": "long",
            "entry_price": 50000,
            "stop_loss": 49500,
            "take_profit": 51000,
            "confluence_score": 8.5,
            "probability": 0.75,
            "risk_reward": 2.0,
            "reasoning": "Детальное объяснение почему это хороший лонг",
            "timeframes_alignment": ["1h", "4h", "1d"],
            "key_factors": ["RSI oversold", "Support level", "Bullish pattern"]
        }}
    ],
    "top_shorts": [
        {{
            "symbol": "ETH/USDT",
            "side": "short",
            "entry_price": 3000,
            "stop_loss": 3050,
            "take_profit": 2900,
            "confluence_score": 8.3,
            "probability": 0.72,
            "risk_reward": 2.0,
            "reasoning": "Детальное объяснение почему это хороший шорт",
            "timeframes_alignment": ["1h", "4h", "1d"],
            "key_factors": ["RSI overbought", "Resistance level", "Bearish pattern"]
        }}
    ],
    "market_summary": "Краткое резюме рыночной ситуации",
    "btc_status": "bullish/neutral/bearish",
    "recommendations": ["Общие рекомендации"]
}}
"""
        
        result = await self.generate(
            prompt=prompt,
            system_prompt=system_instructions,
            temperature=0.3,  # Низкая температура для более детерминированного анализа
            max_tokens=4000
        )
        
        if result["success"]:
            try:
                # Пытаемся распарсить JSON из ответа
                content = result["content"]
                
                # Извлекаем JSON если он обёрнут в markdown code blocks
                if "```json" in content:
                    json_start = content.find("```json") + 7
                    json_end = content.find("```", json_start)
                    content = content[json_start:json_end].strip()
                elif "```" in content:
                    json_start = content.find("```") + 3
                    json_end = content.find("```", json_start)
                    content = content[json_start:json_end].strip()
                
                parsed = json.loads(content)
                return {
                    "success": True,
                    "analysis": parsed,
                    "raw_response": result["content"]
                }
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON from Qwen response: {e}")
                # Возвращаем raw response если не удалось распарсить
                return {
                    "success": True,
                    "analysis": {"raw_text": result["content"]},
                    "raw_response": result["content"]
                }
        else:
            return {
                "success": False,
                "error": result.get("error", "Unknown error"),
                "analysis": None
            }

