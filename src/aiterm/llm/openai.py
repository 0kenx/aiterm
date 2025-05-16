import json
from openai import AsyncOpenAI
from typing import Dict, Any
from .base import BaseLLMAdapter


class OpenAIAdapter(BaseLLMAdapter):
    """Adapter for OpenAI API with structured outputs."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize OpenAI adapter with configuration."""
        super().__init__(config)
        self.api_key = config.get('api_key')
        self.model = config.get('model', 'gpt-4o')
        self.temperature = config.get('temperature')  # No default - use None if not specified
        self.max_tokens = config.get('max_tokens')
        self.top_p = config.get('top_p')
        self.frequency_penalty = config.get('frequency_penalty')
        self.presence_penalty = config.get('presence_penalty')
        self.seed = config.get('seed')

        # Initialize async client
        self.client = AsyncOpenAI(api_key=self.api_key)
    
    async def needs_context(self, query: str) -> tuple[bool, list[str]]:
        """Determine if we need to gather context for this query."""
        # For cloud models, we usually don't ask for context to save API calls
        # unless it's explicitly needed
        if any(word in query.lower() for word in ['current', 'this', 'here', 'show']):
            return True, ['pwd', 'ls -la']
        return False, []
    
    async def _make_request(self, prompt: str, temperature: float = None) -> str:
        """Make async request to OpenAI API."""
        # Build messages
        messages = [
            {"role": "system", "content": "You are a helpful terminal assistant. Always respond with valid JSON containing command suggestions."},
            {"role": "user", "content": prompt}
        ]
        
        # Build parameters
        params = {
            "model": self.model,
            "messages": messages,
        }

        # Add temperature if specified
        if temperature is not None:
            params["temperature"] = temperature
        elif self.temperature is not None:
            params["temperature"] = self.temperature

        # Add optional parameters only if they're set
        if self.max_tokens is not None:
            params["max_tokens"] = self.max_tokens
        if self.top_p is not None:
            params["top_p"] = self.top_p
        if self.frequency_penalty is not None:
            params["frequency_penalty"] = self.frequency_penalty
        if self.presence_penalty is not None:
            params["presence_penalty"] = self.presence_penalty
        if self.seed is not None:
            params["seed"] = self.seed
        
        # Check if model supports JSON mode
        if self.model in ['gpt-4o', 'gpt-4', 'gpt-3.5-turbo']:
            params["response_format"] = {"type": "json_object"}
        
        try:
            response = await self.client.chat.completions.create(**params)
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")