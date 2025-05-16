import json
from anthropic import AsyncAnthropic
from typing import Dict, Any
from .base import BaseLLMAdapter


class AnthropicAdapter(BaseLLMAdapter):
    """Adapter for Anthropic API."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Anthropic adapter with configuration."""
        super().__init__(config)
        self.api_key = config.get('api_key')
        self.model = config.get('model', 'claude-3-sonnet-20240229')
        self.temperature = config.get('temperature', 0.7)
        self.max_tokens = config.get('max_tokens', 4096)
        self.top_p = config.get('top_p', None)
        self.top_k = config.get('top_k', None)
        
        # Initialize async client
        self.client = AsyncAnthropic(api_key=self.api_key)
    
    async def needs_context(self, query: str) -> tuple[bool, list[str]]:
        """Determine if we need to gather context for this query."""
        # For cloud models, we usually don't ask for context to save API calls
        # unless it's explicitly needed
        if any(word in query.lower() for word in ['current', 'this', 'here', 'show']):
            return True, ['pwd', 'ls -la']
        return False, []
    
    async def _make_request(self, prompt: str, temperature: float = None) -> str:
        """Make async request to Anthropic API."""
        # Build parameters
        params = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature or self.temperature,
            "max_tokens": self.max_tokens,
        }
        
        # Add optional parameters
        if self.top_p is not None:
            params["top_p"] = self.top_p
        if self.top_k is not None:
            params["top_k"] = self.top_k
        
        # Claude doesn't have built-in JSON mode, so we add instructions
        params["messages"][0]["content"] = f"{prompt}\n\nIMPORTANT: Respond with valid JSON only."
        
        try:
            response = await self.client.messages.create(**params)
            return response.content[0].text
        except Exception as e:
            raise Exception(f"Anthropic API error: {str(e)}")