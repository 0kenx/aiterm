"""Factory for creating LLM adapters based on configuration."""
from typing import Optional
from ..config import Config
from .base import BaseLLMAdapter
from .ollama import OllamaAdapter
from .openai import OpenAIAdapter
from .anthropic import AnthropicAdapter


# Map provider names to adapter classes
PROVIDER_ADAPTERS = {
    'ollama': OllamaAdapter,
    'openai': OpenAIAdapter,
    'anthropic': AnthropicAdapter,
}


def create_adapter(model_name: str, config: Config) -> Optional[BaseLLMAdapter]:
    """Create an LLM adapter for the specified model."""

    model_config = config.get_model_config(model_name)
    if not model_config:
        print(f"Error: Model '{model_name}' is not configured.")
        available = list(config.models.keys())
        if available:
            print(f"Available models: {', '.join(available)}")
        else:
            print("No models configured. Please check your config.yaml")
        return None
    
    # Get the adapter class for this provider
    adapter_class = PROVIDER_ADAPTERS.get(model_config.provider)
    if not adapter_class:
        print(f"Error: Unknown provider '{model_config.provider}' for model '{model_name}'")
        print(f"Available providers: {', '.join(PROVIDER_ADAPTERS.keys())}")
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
        print(f"Adapter class: {adapter_class}")
        print(f"Adapter config: {adapter_config}")
        import traceback
        traceback.print_exc()
        raise  # Re-raise to capture in main