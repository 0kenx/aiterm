import json
import aiohttp
from typing import Dict, Any
from .base import BaseLLMAdapter


class OllamaAdapter(BaseLLMAdapter):
    """Adapter for Ollama API."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Ollama adapter with configuration."""
        super().__init__(config)
        self.base_url = config.get('base_url', 'http://localhost:11434')
        self.model = config.get('model', 'mistral')
        # Ollama-specific options
        self.temperature = config.get('temperature', 0.7)
        self.top_p = config.get('top_p', None)
        self.top_k = config.get('top_k', None)
        self.num_ctx = config.get('num_ctx', None)
        self.seed = config.get('seed', None)
    
    async def needs_context(self, query: str) -> tuple[bool, list[str]]:
        """Determine if we need to gather context for this query."""
        # For local models, we'll do a quick context check
        check_prompt = f"""
Analyze this user request for terminal commands:
"{query}"

Determine if we need extra context to generate accurate commands.
Reply with JSON in this format:
{{
    "needs_context": true/false,
    "commands": ["list", "of", "commands", "to", "run"]
}}

Common context commands include: pwd, ls, uname -a, git status, etc.
Only request context if truly needed for the specific task.
"""
        
        try:
            response = await self._make_request(check_prompt, temperature=0.1)
            data = json.loads(response)
            return data.get('needs_context', False), data.get('commands', [])
        except:
            # If we can't parse, assume no context needed
            return False, []
    
    async def _make_request(self, prompt: str, temperature: float = None) -> str:
        """Make async request to Ollama API."""
        url = f"{self.base_url}/api/generate"
        
        # Build parameters
        params = {
            "model": self.model,
            "prompt": prompt,
            "temperature": temperature or self.temperature,
            "stream": False
        }
        
        # Add optional parameters
        if self.top_p is not None:
            params["options"] = params.get("options", {})
            params["options"]["top_p"] = self.top_p
        if self.top_k is not None:
            params["options"] = params.get("options", {})
            params["options"]["top_k"] = self.top_k
        if self.num_ctx is not None:
            params["options"] = params.get("options", {})
            params["options"]["num_ctx"] = self.num_ctx
        if self.seed is not None:
            params["options"] = params.get("options", {})
            params["options"]["seed"] = self.seed
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, json=params, timeout=30) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get('response', '')
                    else:
                        error_text = await response.text()
                        raise Exception(f"Ollama API error: {response.status} - {error_text}")
            except aiohttp.ClientTimeout:
                raise Exception("Ollama request timed out")
            except aiohttp.ClientError as e:
                raise Exception(f"Ollama connection error: {str(e)}")