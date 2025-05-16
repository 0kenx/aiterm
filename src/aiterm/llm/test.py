import json
from typing import Dict, Any
from .base import BaseLLMAdapter


class TestAdapter(BaseLLMAdapter):
    """Test adapter that prints queries and returns mock responses."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize test adapter."""
        super().__init__(config)
        self.model = config.get('model', 'test-model')
    
    async def needs_context(self, query: str) -> tuple[bool, list[str]]:
        """Test implementation - always returns some context commands."""
        print(f"\n[TEST] Checking if context needed for: {query}")
        return True, ["pwd", "ls -la"]
    
    async def _make_request(self, prompt: str, temperature: float = None) -> str:
        """Print the prompt and return mock suggestions in JSON format."""
        print("\n[TEST] Received prompt:")
        print("-" * 40)
        print(prompt)
        print("-" * 40)

        # Parse the prompt to provide appropriate suggestions
        prompt_lower = prompt.lower()

        if "python" in prompt_lower and ("list" in prompt_lower or "find" in prompt_lower):
            mock_response = {
                "suggestions": [
                    {
                        "command": "find . -name '*.py' -type f",
                        "description": "Find all Python files recursively"
                    },
                    {
                        "command": "find . -name '*.py' -type f | head -20",
                        "description": "Find Python files (first 20)"
                    },
                    {
                        "command": "ls -la *.py",
                        "description": "List Python files in current directory"
                    }
                ]
            }
        else:
            # Default test commands
            mock_response = {
                "suggestions": [
                    {
                        "command": "echo 'Test command 1'",
                        "description": "First test command"
                    },
                    {
                        "command": "ls -la",
                        "description": "List all files with details"
                    },
                    {
                        "command": "date",
                        "description": "Show current date and time"
                    }
                ]
            }

        return json.dumps(mock_response)