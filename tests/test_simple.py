#!/usr/bin/env python3
"""Simple test without dependencies."""
import sys
import os
# Add parent directory to path to find src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

# Test imports
try:
    from aiterm.config import Config, ModelConfig, ProviderConfig
    print("✅ Config imports successful")
except ImportError as e:
    print(f"❌ Config import failed: {e}")

try:
    from aiterm.prompt_builder import build_structured_prompt
    print("✅ Prompt builder import successful")
except ImportError as e:
    print(f"❌ Prompt builder import failed: {e}")

try:
    from aiterm.llm.base import BaseLLMAdapter
    print("✅ Base adapter import successful")
except ImportError as e:
    print(f"❌ Base adapter import failed: {e}")

# Test basic functionality
try:
    # Create a minimal model config
    model_config = ModelConfig(
        provider='test',
        model='test-model',
        instructions='Test instructions',
        include_path_commands=True,
        include_history_context=True
    )
    print("✅ ModelConfig creation successful")

    # Test prompt building (without actual execution)
    print("\n--- Testing Prompt Builder ---")

    # Test the public function
    prompt = build_structured_prompt(
        user_input="test query",
        instructions="Test instructions",
        available_commands=['ls', 'cd', 'pwd'],
        command_history={'command_history': ['ls -la', 'cd ..']}
    )
    print("✅ Structured prompt created successfully")
    print("Prompt preview:", prompt[:100] + "...")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n✨ Test complete!")