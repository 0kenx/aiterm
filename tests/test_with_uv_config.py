#!/usr/bin/env python3
"""Test with a config file that includes test model."""
import subprocess
import os
import tempfile
import yaml

# Create a test config
config = {
    'default_models': ['test', 'gpt4'],
    'allowed_commands': ['echo', 'ls', 'pwd', 'date'],
    'providers': {
        'test': {}
    },
    'models': {
        'test': {
            'provider': 'test',
            'model': 'test-model',
            'instructions': 'You are a test model. Always reply with JSON.'
        }
    }
}

# Write config to temp file
with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
    yaml.dump(config, f)
    config_path = f.name

# Set config path
os.environ['AITERM_CONFIG'] = config_path

try:
    # Run the test command
    result = subprocess.run([
        'uv', 'run', 'at', '-m', 'test', 'list', 'all', 'python', 'files'
    ], capture_output=True, text=True)

    print("STDOUT:")
    print(result.stdout)
    print("\nSTDERR:")
    print(result.stderr)
    print(f"\nReturn code: {result.returncode}")
finally:
    # Clean up
    os.unlink(config_path)