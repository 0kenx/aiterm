#!/usr/bin/env python3
"""Test finding Python files."""
import json
from typing import Dict, Any
from aiterm.llm.base import BaseLLMAdapter


class MockLLMAdapter(BaseLLMAdapter):
    """Mock adapter that returns realistic Python file commands."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize mock adapter."""
        super().__init__(config)
        self.model = config.get('model', 'mock-model')
    
    async def needs_context(self, query: str) -> tuple[bool, list[str]]:
        """Mock context check - return pwd."""
        if "list" in query.lower() and "python" in query.lower():
            return True, ["pwd"]
        return False, []
    
    async def _make_request(self, prompt: str, temperature: float = None) -> str:
        """Return realistic commands for finding Python files."""
        # Parse what we're looking for
        if "python" in prompt.lower() and "list" in prompt.lower():
            response = {
                "suggestions": [
                    {
                        "command": "find . -name '*.py' -type f",
                        "description": "Find all Python files recursively from current directory"
                    },
                    {
                        "command": "ls -la *.py",
                        "description": "List Python files in current directory only"
                    },
                    {
                        "command": "find . -name '*.py' -type f | head -20",
                        "description": "Find Python files and show first 20"
                    }
                ]
            }
        else:
            response = {
                "suggestions": [
                    {
                        "command": "ls -la",
                        "description": "List all files"
                    }
                ]
            }
        
        return json.dumps(response)


# Simple test
if __name__ == "__main__":
    import asyncio
    
    async def test():
        adapter = MockLLMAdapter({'model': 'mock'})
        
        # Test context
        needs_ctx, cmds = await adapter.needs_context("list all python files")
        print(f"Needs context: {needs_ctx}, Commands: {cmds}")
        
        # Test generation
        response = await adapter.generate("list all python files")
        print(f"Response: {response}")
    
    asyncio.run(test())