#!/usr/bin/env python3
"""Test the system using uv."""
import subprocess
import sys

# Run the test command with stdin to select first option
result = subprocess.run([
    'uv', 'run', 'at', '-m', 'test', 'list', 'all', 'python', 'files'
], capture_output=True, text=True, input='1\n')

print("=== Test with UV ===")
print("\nSTDOUT:")
print(result.stdout)
print("\nSTDERR:")
print(result.stderr)
print(f"\nReturn code: {result.returncode}")

# Verify the command ran successfully
if result.returncode == 0:
    print("\n✅ Test passed")
else:
    print("\n❌ Test failed")