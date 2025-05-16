"""Context gathering utilities for aiterm."""
import os
import subprocess
from pathlib import Path
from typing import List, Set, Tuple
from collections import OrderedDict


def get_path_commands() -> List[str]:
    """Get all executable commands available in PATH using shell."""
    try:
        # Use shell to find all executables in PATH
        # This command lists all executable files in PATH directories
        result = subprocess.run(
            ['sh', '-c', 'export LC_ALL=C; for dir in ${PATH//:/ }; do ls -1 "$dir" 2>/dev/null || true; done | sort -u'],
            capture_output=True,
            text=True,
            timeout=3
        )

        if result.returncode == 0 and result.stdout:
            commands = [cmd.strip() for cmd in result.stdout.splitlines() if cmd.strip()]
            return commands
    except Exception:
        pass

    # Fallback to empty list if command fails
    return []


def get_shell_history(history_size: int = 500) -> Tuple[List[str], List[str]]:
    """Get shell history using the history command from the current shell.

    Returns:
        tuple: (recent_commands, unique_older_commands)
    """
    all_commands = []

    # Get current shell
    shell = os.environ.get('SHELL', '/bin/sh')

    try:
        # Use history command from the current shell with interactive flag
        result = subprocess.run(
            [shell, '-i', '-c', 'history'],
            capture_output=True,
            text=True,
            timeout=3,
            env=os.environ
        )

        if result.returncode == 0 and result.stdout:
            # Parse history output - most shells have format like "  123  command"
            for line in result.stdout.splitlines():
                line = line.strip()
                if line:
                    # Remove line numbers if present
                    parts = line.split(None, 1)
                    if len(parts) > 1 and parts[0].isdigit():
                        all_commands.append(parts[1])
                    else:
                        # Some shells don't have line numbers
                        all_commands.append(line)
    except Exception:
        pass

    # Reverse to get most recent first
    all_commands.reverse()

    # Split into recent and older unique commands
    recent_commands = all_commands[:history_size]

    # Get unique commands from older history
    recent_set = set(recent_commands)
    older_unique = []
    seen = set()

    for cmd in all_commands[history_size:]:
        if cmd not in recent_set and cmd not in seen:
            older_unique.append(cmd)
            seen.add(cmd)

    return recent_commands, older_unique


def build_extended_context(config, model_name: str, context: dict = None) -> dict:
    """Build extended context with PATH commands and history if configured."""
    if context is None:
        context = {}
    
    # Determine if we should include extended context
    include_path = config.include_path_commands.get(
        model_name, 
        config.include_path_commands.get('default', False)
    )
    include_history = config.include_history_context.get(
        model_name,
        config.include_history_context.get('default', False)
    )
    
    extended_context = {}
    
    if include_path:
        try:
            path_commands = get_path_commands()
            if path_commands:
                # Limit to reasonable size
                extended_context['available_commands'] = path_commands[:1000]
        except Exception:
            pass
    
    if include_history:
        try:
            recent, unique_older = get_shell_history(config.history_context_size)
            if recent:
                extended_context['recent_commands'] = recent[:100]  # Limit size
            if unique_older:
                extended_context['command_history'] = unique_older[:200]  # Limit size
        except Exception:
            pass
    
    # Merge contexts
    if extended_context:
        context['system_context'] = extended_context
    
    return context