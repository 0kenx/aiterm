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
        self.temperature = config.get('temperature')  # No default - use None if not specified
        self.top_p = config.get('top_p')
        self.top_k = config.get('top_k')
        self.num_ctx = config.get('num_ctx')
        self.seed = config.get('seed')

        # Debug log
        print(f"[DEBUG] Ollama adapter initialized with base_url={self.base_url}, model={self.model}")
    
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
        except Exception as e:
            # If we can't parse, assume no context needed
            print(f"[DEBUG] Ollama needs_context error: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            return False, []
    
    async def _make_request(self, prompt: str, temperature: float = None) -> str:
        """Make async request to Ollama API."""
        url = f"{self.base_url}/api/generate"
        
        # Build parameters
        params = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }

        # Build options dictionary from configured parameters
        options = {}

        # Add all configured options
        if self.temperature is not None:
            options["temperature"] = self.temperature
        if self.top_p is not None:
            options["top_p"] = self.top_p
        if self.top_k is not None:
            options["top_k"] = self.top_k
        if self.num_ctx is not None:
            options["num_ctx"] = self.num_ctx
        if self.seed is not None:
            options["seed"] = self.seed

        # Add temperature override if provided
        if temperature is not None:
            options["temperature"] = temperature

        # Add options to params if any exist
        if options:
            params["options"] = options
        
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