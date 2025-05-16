import subprocess
import shlex
from typing import List, Optional, Tuple, Dict
from .config import Config


class CommandExecutor:
    def __init__(self, config: Config):
        self.config = config
    
    def is_command_allowed(self, command: str) -> bool:
        """Check if command is in the allow-list."""
        # Extract the base command
        try:
            parts = shlex.split(command)
            if not parts:
                return False
            base_command = parts[0]
            return base_command in self.config.allowed_commands
        except ValueError:
            return False
    
    def execute_command(self, command: str, require_confirmation: bool = True) -> Tuple[bool, str, str]:
        """Execute a command safely."""
        if not self.is_command_allowed(command) and require_confirmation:
            return False, "", "Command not in allow-list and confirmation required"
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            return True, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", "Command timed out"
        except Exception as e:
            return False, "", str(e)
    
    def gather_context(self, commands: List[str]) -> Dict[str, str]:
        """Execute context-gathering commands."""
        context = {}
        for cmd in commands:
            if self.is_command_allowed(cmd):
                success, stdout, stderr = self.execute_command(cmd, require_confirmation=False)
                if success:
                    context[cmd] = stdout
        return context
