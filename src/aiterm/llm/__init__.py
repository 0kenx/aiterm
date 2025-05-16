"""LLM adapters for AI Terminal."""
from .base import BaseLLMAdapter, CommandSuggestion
from .ollama import OllamaAdapter
from .openai import OpenAIAdapter
from .anthropic import AnthropicAdapter
from .test import TestAdapter
from .factory import create_adapter

# For backwards compatibility, export the base class as LLMAdapter too
LLMAdapter = BaseLLMAdapter

__all__ = [
    'BaseLLMAdapter',
    'LLMAdapter',
    'CommandSuggestion',
    'OllamaAdapter',
    'OpenAIAdapter',
    'AnthropicAdapter',
    'TestAdapter',
    'create_adapter'
]
