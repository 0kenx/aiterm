from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.syntax import Syntax
from rich.table import Table
from rich import box
from typing import List, Optional, Union, Dict
from .llm.base import CommandSuggestion


class TUI:
    def __init__(self):
        self.console = Console()

    def display_welcome(self):
        """Display welcome message."""
        self.console.print(Panel.fit(
            "[bold cyan]AI Terminal Assistant[/bold cyan]\n"
            "Let AI help you with terminal commands",
            border_style="cyan"
        ))

    def display_suggestions(self, suggestions: Union[List[CommandSuggestion], List[Dict]], ) -> tuple[Optional[Union[CommandSuggestion, Dict]], Optional[str]]:
        """Display command suggestions and let user choose.

        Returns:
            tuple: (selected_command, continuation_text)
                   If user selects a command: (command, None)
                   If user types 'q': (None, None)
                   If user types other text: (None, text)
        """
        if not suggestions:
            self.console.print("[red]No suggestions available[/red]")
            return None, None

        # Normalize suggestions to dicts
        normalized_suggestions = []
        for s in suggestions:
            if isinstance(s, dict):
                normalized_suggestions.append(s)
            else:
                # Assume it's a CommandSuggestion object
                normalized_suggestions.append({
                    'command': s.command,
                    'description': s.description
                })

        # Compact display with descriptions
        for i, suggestion in enumerate(normalized_suggestions, 1):
            command_line = f"[{i}] [green]{suggestion['command']}[/green]"
            if 'description' in suggestion and suggestion['description']:
                command_line += f" - [dim]{suggestion['description']}[/dim]"
            self.console.print(command_line)

        choice = Prompt.ask(
            "Select [[cyan]q[/cyan]uit/type text to continue] [[cyan]1[/cyan]]",
            default="1",
            show_default=False
        )

        if choice.lower() == 'q':
            return None, None
        elif choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(normalized_suggestions):
                return normalized_suggestions[idx], None

        # User typed something else - continue conversation
        return None, choice

    def confirm_execution(self, command: str) -> bool:
        """Ask user to confirm command execution."""
        # self.console.print(f"\n[bold]Command to execute:[/bold]")
        self.console.print(Syntax(command, "bash", theme="monokai", line_numbers=False))
        return Confirm.ask("Execute this command?")

    def display_result(self, success: bool, stdout: str, stderr: str):
        """Display command execution result."""
        if success:
            if stdout:
                self.console.print("\n[green]Output:[/green]")
                self.console.print(stdout)
            if stderr:
                self.console.print("\n[yellow]Warnings:[/yellow]")
                self.console.print(stderr)
        else:
            self.console.print("\n[red]Error:[/red]")
            self.console.print(stderr or "Command failed")

    def display_context_gathering(self, commands: List[str]):
        """Display context gathering status."""
        self.console.print("[dim]Gathering context...[/dim]")
        for cmd in commands:
            self.console.print(f"  [dim]• {cmd}[/dim]")
        self.console.print("")

    def display_extended_context_gathering(self, include_path: bool, include_history: bool):
        """Display extended context gathering status."""
        if include_path or include_history:
            self.console.print("[dim]Gathering system context...[/dim]")
            if include_path:
                self.console.print("  [dim]• Available commands from PATH[/dim]")
            if include_history:
                self.console.print("  [dim]• Command history[/dim]")
            self.console.print("")

    def error(self, message: str):
        """Display error message."""
        self.console.print(f"[red]Error:[/red] {message}")

    def info(self, message: str):
        """Display info message."""
        self.console.print(f"[dim]{message}[/dim]")

    def warning(self, message: str):
        """Display warning message."""
        self.console.print(f"[yellow]Warning:[/yellow] {message}")

    def status(self, message: str):
        """Display status message."""
        self.console.print(f"[dim]{message}[/dim]")

    def display_status(self, model: str, context_info: dict):
        """Display compact status line with model and context info."""
        status_parts = [f"Using model: [cyan]{model}[/cyan]"]

        # Add system context info
        system_context = []
        if context_info.get('has_path_commands'):
            system_context.append("PATH")
        if context_info.get('has_history'):
            system_context.append("history")

        if system_context:
            status_parts.append(f"Context included: [yellow]{', '.join(system_context)}[/yellow]")

        # Add extra context from commands
        if context_info.get('context_commands'):
            commands = context_info['context_commands']
            status_parts.append(f"Extra context: [yellow]{', '.join(commands)}[/yellow]")

        self.console.print("   ".join(status_parts))
