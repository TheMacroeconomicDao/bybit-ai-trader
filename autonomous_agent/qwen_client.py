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
        if not api_key:
            raise ValueError("API key is required for Qwen client")
        
        # НОВАЯ ПРОВЕРКА формата ключа
        if not api_key.startswith("sk-or-"):
            logger.warning(
                f"OpenRouter API key should start with 'sk-or-'. "
                f"Your key starts with: {api_key[:10]}... "
                f"Please verify your OPENROUTER_API_KEY"
            )
        
        self.api_key = api_key
        self.model = model
        self.base_url = self.BASE_URL
        self.available_models = [
            "qwen/qwen-turbo",
            "qwen/qwen-plus", 
            "qwen/qwen-max"
        ]
        
        logger.info(f"Qwen client initialized with OpenRouter, model: {model}")
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        top_p: float = 0.8,
        retries: int = 5,
        initial_backoff: float = 1.0
    ) -> Dict[str, Any]:
        """
        Генерация ответа от Qwen с обработкой ошибок и повторными попытками.
        
        Args:
            prompt: Пользовательский промпт
            system_prompt: Системный промпт (опционально)
            temperature: Температура генерации (0-1)
            max_tokens: Максимальное количество токенов
            top_p: Top-p sampling
            retries: Количество повторных попыток при ошибках 429
            initial_backoff: Начальное время ожидания в секундах
            
        Returns:
            Ответ от модели с метаданными
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/your-repo",
            "X-Title": "Trader Agent"
        }
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p
        }

        backoff_time = initial_backoff
        
        for attempt in range(retries):
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
                            if "choices" in data and len(data["choices"]) > 0:
                                choice = data["choices"][0]
                                content = choice.get("message", {}).get("content", "")
                                return {
                                    "success": True, "content": content,
                                    "usage": data.get("usage", {}), "model": data.get("model", self.model),
                                    "id": data.get("id", "")
                                }
                            logger.warning(f"Unexpected response format: {data}")
                            return {
                                "success": True, "content": json.dumps(data, ensure_ascii=False),
                                "usage": data.get("usage", {}), "model": data.get("model", self.model)
                            }
                        
                        elif response.status == 429:
                            logger.warning(f"Rate limit exceeded (429). Retrying in {backoff_time:.2f} seconds... (Attempt {attempt + 1}/{retries})")
                            await asyncio.sleep(backoff_time)
                            backoff_time *= 2  # Exponential backoff
                            continue

                        elif response.status == 401:
                            response_text = await response.text()
                            error_msg = (
                                f"❌ OpenRouter API Authentication Failed (401)\nResponse: {response_text}\n\n"
                                f"SOLUTIONS:\n1. Check OPENROUTER_API_KEY in .env file\n"
                                f"2. Verify key format: should start with 'sk-or-v1-'\n"
                                f"3. Get new key at: https://openrouter.ai/keys\n"
                                f"4. Check account balance at: https://openrouter.ai/credits\n"
                            )
                            logger.error(error_msg)
                            return {
                                "success": False, "error": "authentication_failed", "content": "",
                                "details": response_text, "action_required": "Check OPENROUTER_API_KEY in .env",
                                "graceful_fallback": True, "message": "Qwen AI analysis skipped due to API authentication error"
                            }
                        
                        else:
                            response_text = await response.text()
                            logger.error(f"OpenRouter API error {response.status}: {response_text}")
                            return {
                                "success": False, "error": f"API error {response.status}", "content": "",
                                "graceful_fallback": True, "message": f"Qwen AI analysis skipped (API error {response.status})"
                            }
            
            except asyncio.TimeoutError:
                logger.error("Qwen API request timeout")
                return {
                    "success": False, "error": "Request timeout", "content": "",
                    "graceful_fallback": True, "message": "Qwen AI analysis skipped (timeout)"
                }
            except Exception as e:
                logger.error(f"Qwen API error: {e}", exc_info=True)
                return {
                    "success": False, "error": str(e), "content": "",
                    "graceful_fallback": True, "message": f"Qwen AI analysis skipped ({str(e)})"
                }

        logger.error(f"Failed to generate response after {retries} retries.")
        return {
            "success": False, "error": "rate_limit_exceeded", "content": "",
            "graceful_fallback": True, "message": f"Qwen AI analysis skipped after {retries} failed attempts due to rate limiting."
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
Analyze the following market data and find TOP 3 best LONG and TOP 3 best SHORT opportunities for trading.

Market Data:
{json.dumps(market_data, ensure_ascii=False, indent=2)}

Requirements:
1. Find TOP 3 LONG with confluence ≥ 8.0/10
2. Find TOP 3 SHORT with confluence ≥ 8.0/10
3. Success probability ≥ 70% for each opportunity
4. R:R minimum 1:2 for each opportunity
5. Explain each opportunity in detail
6. Specify exact entry, SL, TP levels

Response Format (JSON):
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
            "reasoning": "Detailed explanation why this is a good long entry",
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
            "reasoning": "Detailed explanation why this is a good short entry",
            "timeframes_alignment": ["1h", "4h", "1d"],
            "key_factors": ["RSI overbought", "Resistance level", "Bearish pattern"]
        }}
    ],
    "market_summary": "Brief summary of market conditions",
    "btc_status": "bullish/neutral/bearish",
    "recommendations": ["General recommendations"]
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

