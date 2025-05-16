#!/usr/bin/env python3
"""Test the adapters directly."""
import asyncio
import sys
sys.path.insert(0, 'src')

from aiterm.config import Config
from aiterm.llm.test import TestAdapter


async def test_adapter():
    # Create test adapter
    config = {
        'model': 'test-model',
        'instructions': 'You are a helpful test assistant.'
    }
    
    adapter = TestAdapter(config)
    
    # Test needs_context
    needs_context, commands = await adapter.needs_context("list all python files")
    print(f"Needs context: {needs_context}")
    print(f"Commands: {commands}")
    
    # Test generation
    prompt = """
<system_prompt>
You are a helpful assistant that generates terminal commands.
</system_prompt>

<user>
list all python files
</user>

Please respond with JSON containing terminal command suggestions.
"""
    
    response = await adapter.generate(prompt)
    print(f"\nGenerated response:\n{response}")


if __name__ == '__main__':
    asyncio.run(test_adapter())