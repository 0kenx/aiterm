"""Structured prompt builder for AI models."""
from typing import List, Dict, Optional
from dataclasses import dataclass
from .bloom_filter import should_ignore_command


@dataclass
class PromptRequest:
    """Request for generating command suggestions."""
    suggestions: List[Dict[str, str]]


SYSTEM_PROMPT = """You are an AI terminal assistant that helps users with command-line tasks.
Your role is to suggest appropriate shell commands based on the user's request.

IMPORTANT: You must respond with valid JSON in the following format:
{
    "needs_context": true/false,
    "context_commands": ["command1", "command2"],
    "suggestions": [
        {"command": "actual command", "description": "what it does"}
    ]
}

For each conversation round:
- Set "needs_context" to true only if you need system information to provide better suggestions
- Include "context_commands" only if needs_context is true, commands will be executed in order
- These should be safe info-gathering commands like pwd, ls, cat, echo, grep, find, man
- Do not provide "suggestions" in this case, do not request more than 3 rounds of context_commands in a row

For command suggestions:
- Provide up to 3 relevant command suggestions
- Each suggestion must have a "command" and "description"
- Commands should be practical and safe
- Consider the user's context and history when available
"""


def build_structured_prompt(user_input: str,
                          instructions: Optional[str] = None,
                          available_commands: Optional[List[str]] = None,
                          command_history: Optional[Dict[str, List[str]]] = None,
                          exec_results: Optional[Dict[str, str]] = None,
                          conversation_history: Optional[List[str]] = None) -> str:
    """Build a structured prompt for the AI model.

    Args:
        user_input: The user's current request
        instructions: Model-specific instructions
        available_commands: List of available commands if enabled
        command_history: Command history if enabled
        exec_results: Results from executed context commands
        conversation_history: Previous conversation turns

    Returns:
        Structured prompt string
    """
    parts = []

    # System prompt
    parts.append(f"<system_prompt>\n{SYSTEM_PROMPT}\n</system_prompt>")

    # User instructions from config
    if instructions:
        parts.append(f"<user_prompt>\n{instructions}\n</user_prompt>")

    # Available commands
    if available_commands:
        # Filter out commands starting with . and those in the bloom filter
        filtered_commands = [
            cmd for cmd in available_commands
            if not should_ignore_command(cmd)
        ]
        commands_str = ', '.join(filtered_commands[:1000])  # Limit for context
        parts.append(f"<available_commands>\n{commands_str}\n</available_commands>")

    # Command history
    if command_history:
        history_parts = []
        if 'recent_commands' in command_history:
            recent = command_history['recent_commands'][:20]
            history_parts.append("Recent commands:\n" + "\n".join(recent))
        if 'command_history' in command_history:
            older = command_history['command_history'][:20]
            history_parts.append("Frequently used:\n" + "\n".join(older))

        if history_parts:
            parts.append(f"<command_history>\n{chr(10).join(history_parts)}\n</command_history>")

    # Execution results
    if exec_results:
        results_str = "\n".join([f"$ {cmd}\n{output}" for cmd, output in exec_results.items()])
        parts.append(f"<exec_result>\n{results_str}\n</exec_result>")

    # Conversation history (for multi-turn)
    if conversation_history:
        for i, turn in enumerate(conversation_history):
            if turn.startswith("User:"):
                parts.append(f"<user>\n{turn[5:].strip()}\n</user>")
            elif turn.startswith("[") and "]" in turn:
                # Previous suggestions
                parts.append(f"<assistant>\n{turn}\n</assistant>")
            else:
                # Initial query
                parts.append(f"<user>\n{turn}\n</user>")
    else:
        # Current user input
        parts.append(f"<user>\n{user_input}\n</user>")

    return "\n\n".join(parts)


def build_analysis_prompt(user_input: str, instructions: Optional[str] = None) -> str:
    """Build prompt for initial context analysis."""
    parts = []

    parts.append(f"<system_prompt>\n{SYSTEM_PROMPT}\n</system_prompt>")

    if instructions:
        parts.append(f"<user_prompt>\n{instructions}\n</user_prompt>")

    parts.append(f"<user>\n{user_input}\n</user>")

    parts.append("<task>\nAnalyze if you need system context. Respond with JSON:\n"
                '{"needs_context": true/false, "context_commands": []}\n</task>')

    return "\n\n".join(parts)
