#!/usr/bin/env python3
"""Test the conversation flow manually."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from aiterm.main import process_query
from aiterm.config import Config
from aiterm.tui import TUI
from aiterm.executor import CommandExecutor
from aiterm.llm.test import TestAdapter

# Mock TUI to simulate user input
class MockTUI(TUI):
    def __init__(self, responses):
        super().__init__()
        self.responses = responses
        self.response_index = 0
        
    def display_suggestions(self, suggestions):
        # Show what would be displayed
        print("\nSuggestions:")
        for i, s in enumerate(suggestions, 1):
            print(f"[{i}] {s.command}")
        
        # Get next response
        if self.response_index < len(self.responses):
            response = self.responses[self.response_index]
            self.response_index += 1
            print(f"\nUser types: '{response}'")
            
            if response.isdigit():
                idx = int(response) - 1
                if 0 <= idx < len(suggestions):
                    return suggestions[idx], None
            elif response.lower() == 'q':
                return None, None
            else:
                return None, response
        return None, None

# Test the flow
config = Config.load()
executor = CommandExecutor(config)
llm = TestAdapter({})

# Simulate: initial query -> "some more" -> select 1
tui = MockTUI(["some more", "1"])

print("=== Testing Conversation Flow ===")
print("\nInitial query: 'list all python files'")

selected = process_query(config, tui, llm, executor, 'test', 'list all python files')

if selected:
    print(f"\nFinal selection: {selected.command}")
else:
    print("\nNo selection made")