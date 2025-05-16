"""Context gathering utilities for aiterm."""
import os
import subprocess
from pathlib import Path
from typing import List, Set, Tuple
from collections import OrderedDict


def get_path_commands() -> List[str]:
    """Get all executable commands available in PATH."""
    commands = set()
    
    # Get all directories in PATH
    path_dirs = os.environ.get('PATH', '').split(':')
    
    for directory in path_dirs:
        if not directory or not os.path.isdir(directory):
            continue
            
        try:
            # List all files in the directory
            for filename in os.listdir(directory):
                filepath = os.path.join(directory, filename)
                # Check if it's an executable file
                if os.path.isfile(filepath) and os.access(filepath, os.X_OK):
                    commands.add(filename)
        except (OSError, PermissionError):
            # Skip directories we can't read
            continue
    
    return sorted(list(commands))


def get_shell_history(history_size: int = 500) -> Tuple[List[str], List[str]]:
    """Get shell history from various sources.
    
    Returns:
        tuple: (recent_commands, unique_older_commands)
    """
    all_commands = []
    
    # Try different history sources
    history_files = [
        Path("~/.bash_history").expanduser(),
        Path("~/.zsh_history").expanduser(),
        Path("~/.history").expanduser(),
    ]
    
    for history_file in history_files:
        if history_file.exists():
            try:
                with open(history_file, 'r', errors='ignore') as f:
                    # Read lines and handle different formats
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                            
                        # Handle zsh format (: timestamp:0;command)
                        if line.startswith(': ') and ';' in line:
                            parts = line.split(';', 1)
                            if len(parts) > 1:
                                line = parts[1].strip()
                        
                        # Skip common non-commands
                        if line and not line.startswith('#'):
                            all_commands.append(line)
                            
            except Exception:
                continue
    
    # Also try to get current shell's history if available
    try:
        # Try bash history command
        result = subprocess.run(['bash', '-c', 'history'], 
                              capture_output=True, text=True, timeout=1)
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                # History format: "  123  command"
                parts = line.strip().split(None, 1)
                if len(parts) > 1 and parts[0].isdigit():
                    all_commands.append(parts[1])
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