"""Factory for creating LLM adapters based on configuration."""
from typing import Optional
from ..config import Config
from .base import BaseLLMAdapter
from .ollama import OllamaAdapter
from .openai import OpenAIAdapter
from .anthropic import AnthropicAdapter
from .test import TestAdapter


# Map provider names to adapter classes
PROVIDER_ADAPTERS = {
    'ollama': OllamaAdapter,
    'openai': OpenAIAdapter,
    'anthropic': AnthropicAdapter,
    'test': TestAdapter
}


def create_adapter(model_name: str, config: Config) -> Optional[BaseLLMAdapter]:
    """Create an LLM adapter for the specified model."""
    model_config = config.get_model_config(model_name)
    if not model_config:
        print(f"No config found for model: {model_name}")
        print(f"Available models: {list(config.models.keys())}")
        return None
    
    # Get the adapter class for this provider
    adapter_class = PROVIDER_ADAPTERS.get(model_config.provider)
    if not adapter_class:
        return None
    
    # Get provider config
    provider_config = config.get_provider_config(model_config.provider)
    
    # Build adapter configuration
    adapter_config = {}
    
    # Add provider settings
    if provider_config:
        if provider_config.base_url:
            adapter_config['base_url'] = provider_config.base_url
        adapter_config.update(provider_config.custom_options)
    
    # Add model settings
    adapter_config['model'] = model_config.model
    
    # Get API key
    api_key = config.get_api_key(model_name)
    if api_key:
        adapter_config['api_key'] = api_key
    
    # Add custom model options (these override provider options)
    adapter_config.update(model_config.custom_options)
    
    try:
        return adapter_class(adapter_config)
    except Exception as e:
        print(f"Failed to create adapter for {model_name}: {e}")
        import traceback
        traceback.print_exc()
        return None