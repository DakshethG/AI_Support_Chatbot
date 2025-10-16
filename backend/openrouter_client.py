"""
OpenRouter client for AI support bot using nvidia/nemotron-nano-9b-v2:free model
"""

import os
import json
import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

import httpx
import structlog
from pydantic import BaseModel

logger = structlog.get_logger()

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_ID = "nvidia/nemotron-nano-9b-v2:free"


class ChatMessage(BaseModel):
    role: str
    content: str


class OpenRouterUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class OpenRouterResponse(BaseModel):
    answer: str
    confidence: float
    escalate: bool
    suggested_actions: List[str]
    usage: Optional[OpenRouterUsage] = None
    raw_response: Optional[str] = None


@dataclass
class OpenRouterConfig:
    api_key: str
    model: str = MODEL_ID
    base_url: str = OPENROUTER_URL
    timeout: float = 30.0
    max_retries: int = 3
    retry_delay: float = 1.0


class OpenRouterClient:
    def __init__(self, config: OpenRouterConfig):
        self.config = config
        self.session = None
        self.logger = structlog.get_logger().bind(component="openrouter_client")

    async def __aenter__(self):
        self.session = httpx.AsyncClient(timeout=self.config.timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.aclose()
            self.session = None

    def _build_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://ai-support-bot.local",
            "X-Title": "AI Support Bot",
        }

    def _build_payload(
        self,
        messages: List[ChatMessage],
        temperature: float = 0.15,
        max_tokens: int = 512,
    ) -> Dict[str, Any]:
        return {
            "model": self.config.model,
            "messages": [{"role": msg.role, "content": msg.content} for msg in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

    async def _make_request(
        self, payload: Dict[str, Any], attempt: int = 1
    ) -> Dict[str, Any]:
        """Make HTTP request to OpenRouter with retry logic"""
        try:
            headers = self._build_headers()
            
            self.logger.info(
                "Making OpenRouter request",
                model=self.config.model,
                attempt=attempt,
                max_tokens=payload.get("max_tokens"),
                temperature=payload.get("temperature"),
            )

            response = await self.session.post(
                self.config.base_url, 
                json=payload, 
                headers=headers
            )

            if response.status_code == 200:
                return response.json()
            
            # Log the error for debugging
            error_text = response.text
            self.logger.error(
                "OpenRouter API error",
                status_code=response.status_code,
                error_text=error_text,
                attempt=attempt,
            )

            if response.status_code >= 500 and attempt < self.config.max_retries:
                # Retry on server errors
                delay = self.config.retry_delay * (2 ** (attempt - 1))  # exponential backoff
                self.logger.info(f"Retrying in {delay}s...", attempt=attempt)
                await asyncio.sleep(delay)
                return await self._make_request(payload, attempt + 1)

            response.raise_for_status()

        except httpx.TimeoutException as e:
            self.logger.error("OpenRouter request timeout", attempt=attempt, error=str(e))
            if attempt < self.config.max_retries:
                delay = self.config.retry_delay * (2 ** (attempt - 1))
                await asyncio.sleep(delay)
                return await self._make_request(payload, attempt + 1)
            raise

        except Exception as e:
            self.logger.error("OpenRouter request failed", attempt=attempt, error=str(e))
            raise

    def _parse_response(self, data: Dict[str, Any]) -> OpenRouterResponse:
        """Parse OpenRouter response and extract structured output"""
        try:
            # Extract the response content
            choices = data.get("choices", [])
            if not choices:
                raise ValueError("No choices in response")

            content = choices[0]["message"]["content"]
            
            # Extract usage information if available
            usage_data = data.get("usage", {})
            usage = None
            if usage_data:
                usage = OpenRouterUsage(
                    prompt_tokens=usage_data.get("prompt_tokens", 0),
                    completion_tokens=usage_data.get("completion_tokens", 0),
                    total_tokens=usage_data.get("total_tokens", 0),
                )

            # Try to extract JSON from the response
            try:
                # Look for JSON object in the content
                start_idx = content.find('{')
                end_idx = content.rfind('}') + 1
                
                if start_idx != -1 and end_idx > start_idx:
                    json_str = content[start_idx:end_idx]
                    parsed_json = json.loads(json_str)
                    
                    return OpenRouterResponse(
                        answer=parsed_json.get("answer", "").strip(),
                        confidence=float(parsed_json.get("confidence", 0.5)),
                        escalate=bool(parsed_json.get("escalate", False)),
                        suggested_actions=parsed_json.get("suggested_actions", []),
                        usage=usage,
                        raw_response=content,
                    )
                else:
                    # Fallback if no JSON found
                    self.logger.warning("No JSON found in response, using fallback", content=content[:200])
                    return OpenRouterResponse(
                        answer=content.strip(),
                        confidence=0.3,
                        escalate=True,
                        suggested_actions=["human_review"],
                        usage=usage,
                        raw_response=content,
                    )
                    
            except json.JSONDecodeError as e:
                self.logger.warning("Failed to parse JSON from response", error=str(e), content=content[:200])
                return OpenRouterResponse(
                    answer=content.strip(),
                    confidence=0.3,
                    escalate=True,
                    suggested_actions=["human_review"],
                    usage=usage,
                    raw_response=content,
                )

        except Exception as e:
            self.logger.error("Failed to parse OpenRouter response", error=str(e), data=data)
            return OpenRouterResponse(
                answer="I apologize, but I'm having trouble processing your request. Please try again or contact support.",
                confidence=0.0,
                escalate=True,
                suggested_actions=["retry", "human_review"],
                usage=None,
                raw_response=str(data),
            )

    async def chat_completion(
        self,
        messages: List[ChatMessage],
        temperature: float = 0.15,
        max_tokens: int = 512,
    ) -> OpenRouterResponse:
        """Make a chat completion request"""
        payload = self._build_payload(messages, temperature, max_tokens)
        
        try:
            data = await self._make_request(payload)
            response = self._parse_response(data)
            
            self.logger.info(
                "OpenRouter request successful",
                confidence=response.confidence,
                escalate=response.escalate,
                tokens_used=response.usage.total_tokens if response.usage else 0,
            )
            
            return response
            
        except Exception as e:
            self.logger.error("Chat completion failed", error=str(e))
            # Return a fallback response
            return OpenRouterResponse(
                answer="I'm currently experiencing technical difficulties. Please try again later or contact support.",
                confidence=0.0,
                escalate=True,
                suggested_actions=["retry", "technical_support"],
                usage=None,
                raw_response=f"Error: {str(e)}",
            )

    async def health_check(self) -> Dict[str, Any]:
        """Check if the OpenRouter API is accessible"""
        try:
            # Simple test message
            test_messages = [
                ChatMessage(role="system", content="You are a helpful assistant."),
                ChatMessage(role="user", content="Say 'OK' in JSON format: {\"status\": \"OK\"}")
            ]
            
            response = await self.chat_completion(test_messages, max_tokens=50)
            
            return {
                "status": "healthy" if response.confidence > 0 else "degraded",
                "model": self.config.model,
                "response_received": True,
                "confidence": response.confidence,
            }
        except Exception as e:
            self.logger.error("Health check failed", error=str(e))
            return {
                "status": "unhealthy",
                "model": self.config.model,
                "response_received": False,
                "error": str(e),
            }


def create_openrouter_client() -> OpenRouterClient:
    """Factory function to create OpenRouter client from environment"""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY environment variable is required")
    
    model = os.getenv("OPENROUTER_MODEL", MODEL_ID)
    
    config = OpenRouterConfig(
        api_key=api_key,
        model=model,
    )
    
    return OpenRouterClient(config)