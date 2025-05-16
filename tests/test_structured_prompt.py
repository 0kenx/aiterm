#!/usr/bin/env python3
"""Test the structured prompting system."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from aiterm.prompt_builder import build_structured_prompt, build_analysis_prompt


def test_structured_prompts():
    """Test the structured prompt builder."""
    print("=== Testing Structured Prompts ===\n")
    
    # Test 1: Basic prompt
    print("1. Basic prompt:")
    basic_prompt = build_structured_prompt(
        user_input="list all python files"
    )
    print(basic_prompt)
    print("\n" + "="*50 + "\n")
    
    # Test 2: With instructions
    print("2. With model instructions:")
    instructions_prompt = build_structured_prompt(
        user_input="list all python files",
        instructions="Focus on files in the src directory. Prefer find over ls."
    )
    print(instructions_prompt)
    print("\n" + "="*50 + "\n")
    
    # Test 3: With context
    print("3. With full context:")
    context_prompt = build_structured_prompt(
        user_input="list all python files",
        instructions="Be concise and efficient.",
        available_commands=["find", "ls", "grep", "cat", "echo"],
        command_history={
            'recent_commands': ["cd src", "ls -la", "git status"],
            'command_history': ["find . -name '*.py'", "grep -r TODO"]
        },
        exec_results={
            "pwd": "/home/user/project",
            "ls -la": "total 16\ndrwxr-xr-x  4 user user  128 Dec  1 10:00 .\ndrwxr-xr-x 10 user user  320 Dec  1 09:00 ..\ndrwxr-xr-x  3 user user   96 Dec  1 10:00 src\n-rw-r--r--  1 user user  100 Dec  1 10:00 README.md"
        }
    )
    print(context_prompt)
    print("\n" + "="*50 + "\n")
    
    # Test 4: Multi-turn conversation
    print("4. Multi-turn conversation:")
    conversation_prompt = build_structured_prompt(
        user_input="just in the tests directory",
        conversation_history=[
            "list all python files",
            "[1] find . -name '*.py' -type f",
            "[2] ls *.py", 
            "User: just in the tests directory"
        ]
    )
    print(conversation_prompt)
    print("\n" + "="*50 + "\n")
    
    # Test 5: Analysis prompt
    print("5. Analysis prompt:")
    analysis_prompt = build_analysis_prompt(
        user_input="show me the largest files",
        instructions="Consider whether file sizes are needed for accurate suggestions."
    )
    print(analysis_prompt)


if __name__ == '__main__':
    test_structured_prompts()