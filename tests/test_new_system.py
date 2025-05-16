#!/usr/bin/env python3
"""Test the new configuration and prompting system."""
import sys
sys.path.insert(0, 'src')

from aiterm.config_new import Config
from aiterm.llm.factory_new import create_adapter
from aiterm.prompt_builder import build_structured_prompt
import asyncio

async def test_system():
    # Create a test config
    config = Config(
        default_models=['test'],
        providers={
            'test': None  # Test provider doesn't need config
        },
        models={
            'test': {
                'provider': 'test',
                'model': 'test-model',
                'instructions': 'You are a helpful terminal assistant. Always reply in JSON format.',
                'include_path_commands': True,
                'include_history_context': True,
                'custom_options': {}
            }
        },
        allowed_commands=['echo', 'ls', 'pwd', 'date']
    )
    
    # Create adapter
    adapter = create_adapter('test', config)
    if not adapter:
        print("Failed to create adapter")
        return
    
    # Test query
    query = "Show me what's in the current directory"
    
    # Check context
    needs_context, context_commands = await adapter.needs_context(query)
    print(f"Needs context: {needs_context}")
    print(f"Context commands: {context_commands}")
    
    # Build prompt
    model_config = config.get_model('test')
    prompt = build_structured_prompt(
        model_config=model_config,
        query=query,
        available_commands=['ls', 'pwd', 'echo', 'date'],
        command_history=['ls -la', 'pwd', 'echo "hello"'],
        extra_context="Current directory is /home/user",
        conversation_history=[],
        exec_results=[]
    )
    
    print("\n--- Generated Prompt ---")
    print(prompt)
    
    # Get response
    print("\n--- Model Response ---")
    response = await adapter.generate(prompt)
    print(response)

if __name__ == '__main__':
    asyncio.run(test_system())