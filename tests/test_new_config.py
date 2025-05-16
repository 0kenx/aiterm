#!/usr/bin/env python3
"""Test the new config system."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from aiterm.config import Config, ModelConfig, ProviderConfig


def test_new_config():
    """Test the new configuration system."""
    print("=== Testing New Config System ===\n")
    
    # Create a test config
    config = Config()
    
    # Add providers
    config.providers['openai'] = ProviderConfig(api_key='test-key')
    config.providers['ollama'] = ProviderConfig(base_url='http://localhost:11434')
    
    # Add models
    config.models['gpt4'] = ModelConfig(
        provider='openai',
        model='gpt-4o',
        include_path_commands=False,
        include_history_context=True,
        history_context_size=300,
        custom_options={'temperature': 0.7, 'max_tokens': 1024}
    )
    
    config.models['my_model'] = ModelConfig(
        provider='ollama',
        model='llama3.1',
        include_path_commands=True,
        include_history_context=True,
        api_key='override-key'  # Model-specific key
    )
    
    # Test model config retrieval
    gpt4_config = config.get_model_config('gpt4')
    print(f"GPT-4 config: {gpt4_config}")
    
    # Test API key retrieval
    gpt4_key = config.get_api_key('gpt4')
    print(f"GPT-4 API key: {gpt4_key}")
    
    my_model_key = config.get_api_key('my_model')
    print(f"My model API key: {my_model_key}")
    
    # Test with environment variable
    os.environ['OPENAI_API_KEY'] = 'env-key'
    config.providers['openai'].api_key = None  # Remove provider key
    gpt4_key_env = config.get_api_key('gpt4')
    print(f"GPT-4 API key (from env): {gpt4_key_env}")
    
    # Test saving and loading
    print("\nTesting save/load...")
    temp_path = "/tmp/test_config.yaml"
    
    # Save to temp file
    import yaml
    from pathlib import Path
    
    config_dict = {
        'default_models': config.default_models,
        'allowed_commands': config.allowed_commands,
        'providers': {
            'openai': {},
            'ollama': {'base_url': 'http://localhost:11434'}
        },
        'models': {
            'gpt4': {
                'provider': 'openai',
                'model': 'gpt-4o',
                'include_path_commands': False,
                'include_history_context': True,
                'history_context_size': 300,
                'temperature': 0.7,
                'max_tokens': 1024
            }
        },
        'history_file': config.history_file
    }
    
    with open(temp_path, 'w') as f:
        yaml.dump(config_dict, f)
    
    print(f"Saved config to {temp_path}")
    
    # Test custom options passthrough
    print("\nTesting custom options...")
    print(f"GPT-4 temperature: {gpt4_config.custom_options.get('temperature')}")
    print(f"GPT-4 max_tokens: {gpt4_config.custom_options.get('max_tokens')}")


if __name__ == '__main__':
    test_new_config()