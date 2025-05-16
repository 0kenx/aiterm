#!/usr/bin/env python3
"""Test without user interaction."""
import subprocess
import sys

# Run the test with echo to provide input
result = subprocess.run(
    "echo '1' | uv run at -m test list all python files",
    shell=True,
    capture_output=True,
    text=True
)

print("STDOUT:")
print(result.stdout)
print("\nSTDERR:")
print(result.stderr)
print(f"\nReturn code: {result.returncode}")