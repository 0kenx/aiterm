"""Base LLM adapter with structured prompting."""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass


@dataclass
class CommandSuggestion:
    command: str
    description: str
    needs_context: bool = False
    context_commands: List[str] = None
    
    def __post_init__(self):
        if self.context_commands is None:
            self.context_commands = []


class BaseLLMAdapter(ABC):
    """Base adapter for LLM services."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize adapter with configuration."""
        self.config = config
        self.instructions = config.get('instructions')
    
    @abstractmethod
    async def _make_request(self, prompt: str, temperature: float = None) -> str:
        """Make async request to the LLM API.
        
        Args:
            prompt: The prompt to send to the model
            temperature: Override temperature if specified
            
        Returns:
            The raw response from the API
        """
        pass
    
    @abstractmethod
    async def needs_context(self, query: str) -> tuple[bool, list[str]]:
        """Determine if additional context is needed for the query.
        
        Args:
            query: The user's query
            
        Returns:
            Tuple of (needs_context, list_of_context_commands)
        """
        pass
    
    async def generate(self, prompt: str) -> str:
        """Generate a response from the model.
        
        This method adds any necessary formatting to ensure JSON response.
        
        Args:
            prompt: The structured prompt
            
        Returns:
            The model's response
        """
        if self.instructions and not prompt.startswith("<system_prompt>"):
            # Add instructions to prompt if not already structured
            final_prompt = f"{self.instructions}\n\n{prompt}"
        else:
            final_prompt = prompt
        
        # Make the request
        response = await self._make_request(final_prompt)
        
        return response