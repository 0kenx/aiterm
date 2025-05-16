#!/usr/bin/env python3
import click
import sys
import json
import re
from typing import Optional, List, Union
from .config import Config, ModelConfig
from .tui import TUI
from .executor import CommandExecutor
from .llm.base import BaseLLMAdapter
from .context_gather import build_extended_context, get_path_commands, get_shell_history
from .prompt_builder import build_structured_prompt
from .llm.factory import create_adapter

def find_working_model(config: Config, tui: TUI) -> Optional[tuple[str, BaseLLMAdapter]]:
    """Try models in priority order until one works."""
    errors = []
    
    for model_name in config.default_models:
        try:
            adapter = create_adapter(model_name, config)
            if adapter:
                # For Ollama, try a quick test to see if it's running
                if hasattr(adapter, 'test_connection'):
                    if adapter.test_connection():
                        return model_name, adapter
                    else:
                        errors.append(f"{model_name}: Connection failed")
                        continue
                else:
                    return model_name, adapter
        except Exception as e:
            errors.append(f"{model_name}: {str(e)}")
    
    # Show all errors before entering setup mode
    if errors:
        tui.console.print("\n[yellow]Tried models:[/yellow]")
        for error in errors:
            tui.console.print(f"  [dim]• {error}[/dim]")
    
    # No models available, enter setup mode
    return None


def setup_mode(config: Config, tui: TUI):
    """Help user configure API keys."""
    tui.console.print("\n[bold cyan]AI Terminal Setup[/bold cyan]\n")
    tui.console.print("No working models found. Let's set up API keys.")
    tui.console.print("\nYou can configure API keys in the following ways:")
    tui.console.print("1. Environment variables: OPENAI_API_KEY, ANTHROPIC_API_KEY")
    tui.console.print("2. Config file: ~/.config/aiterm/config.yaml")
    tui.console.print("\nExample configuration:")
    tui.console.print("[yellow]default_models: \\[gpt4, claude, ollama\\][/yellow]")
    tui.console.print("[yellow]providers:")
    tui.console.print("  openai:")
    tui.console.print("    api_key: sk-...")
    tui.console.print("  anthropic:")
    tui.console.print("    api_key: sk-ant-...")
    tui.console.print("models:")
    tui.console.print("  gpt4:")
    tui.console.print("    provider: openai")
    tui.console.print("    model: gpt-4o[/yellow]")
    tui.console.print("\nFor Ollama, make sure to start the service with: [cyan]ollama serve[/cyan]")
    sys.exit(1)


def parse_json_response(response: str) -> List[dict]:
    """Parse JSON response from the model."""
    try:
        # Try to extract JSON from the response
        json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
        if json_match:
            json_text = json_match.group(1)
        else:
            # Try to find any JSON object in the response
            json_text = response
        
        data = json.loads(json_text)
        
        # Handle different response formats
        if isinstance(data, dict):
            if 'suggestions' in data:
                return data['suggestions']
            elif 'commands' in data:
                return data['commands']
            else:
                # Single command response
                return [data]
        elif isinstance(data, list):
            return data
        else:
            return []
    
    except (json.JSONDecodeError, AttributeError):
        # Fallback to text parsing
        return parse_text_response(response)


def parse_text_response(response: str) -> List[dict]:
    """Fallback parser for non-JSON responses."""
    commands = []
    
    # Look for common patterns
    patterns = [
        r'`([^`]+)`',  # Backticks
        r'```(?:bash|sh)?\n?([^`]+)```',  # Code blocks
        r'^\s*\$?\s*(.+)$',  # Lines starting with $ or just commands
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, response, re.MULTILINE)
        for match in matches:
            cmd = match.strip()
            if cmd and not cmd.startswith('#'):
                commands.append({
                    'command': cmd,
                    'description': 'Command found in response'
                })
    
    # Deduplicate and limit
    seen = set()
    deduped = []
    for cmd in commands:
        if cmd['command'] not in seen:
            seen.add(cmd['command'])
            deduped.append(cmd)
    
    return deduped[:5]


async def process_query(config: Config, tui: TUI, adapter: BaseLLMAdapter, executor: CommandExecutor, 
                       model_name: str, query: str, conversation_history: List[dict] = None):
    """Process a single query with the LLM."""
    
    if conversation_history is None:
        conversation_history = []
    
    # Get model config
    model_config = config.get_model_config(model_name)
    if not model_config:
        tui.error(f"Model {model_name} not found in configuration")
        return None
    
    # Check if we need additional context
    context_info = {}
    
    # Gather available commands if configured
    available_commands = []
    if model_config.include_path_commands:
        try:
            path_commands = get_path_commands()
            available_commands = sorted(path_commands[:1000])  # Limit for context
            context_info['has_path_commands'] = True
        except Exception:
            context_info['has_path_commands'] = False
    else:
        context_info['has_path_commands'] = False
    
    # Gather command history if configured
    command_history = []
    if model_config.include_history_context:
        try:
            recent, unique_older = get_shell_history(model_config.history_context_size)
            # Combine recent and unique older commands
            all_history = recent[:100] + unique_older[:200]
            seen = set()
            for cmd in all_history:
                if cmd not in seen:
                    command_history.append(cmd)
                    seen.add(cmd)
            context_info['has_history'] = True
        except Exception:
            context_info['has_history'] = False
    else:
        context_info['has_history'] = False
    
    # Check if we need dynamic context
    extra_context = None
    exec_results = []
    try:
        needs_context, context_commands = await adapter.needs_context(query)
        if needs_context and context_commands:
            context_parts = []
            for cmd in context_commands:
                success, stdout, stderr = executor.execute_command(cmd, require_confirmation=False)
                if success and stdout:
                    context_parts.append(f"$ {cmd}\n{stdout}")
                    exec_results.append({'command': cmd, 'output': stdout})
            if context_parts:
                extra_context = '\n\n'.join(context_parts)
                context_info['context_commands'] = context_commands
    except Exception as e:
        tui.warning(f"Context gathering failed: {e}")
    
    # Display compact status
    tui.display_status(model_name, context_info)
    
    # Build structured prompt
    # Convert conversation history to the expected format
    conv_history = None
    if conversation_history:
        conv_history = []
        for entry in conversation_history:
            if isinstance(entry, dict):
                conv_history.append(f"{entry['role']}: {entry['content']}")
            else:
                conv_history.append(str(entry))

    prompt = build_structured_prompt(
        user_input=query,
        instructions=model_config.instructions,
        available_commands=available_commands,
        command_history={'command_history': command_history} if command_history else None,
        exec_results={item['command']: item['output'] for item in exec_results} if exec_results else None,
        conversation_history=conv_history
    )
    
    # Generate response
    tui.status(f"Asking {model_name} for suggestions...")
    response = await adapter.generate(prompt)
    
    # Parse response
    suggestions = parse_json_response(response)
    
    # Display suggestions and let user choose
    selected, continuation = tui.display_suggestions(suggestions)
    
    if continuation:
        # User wants to continue the conversation
        # Add current interaction to history
        conversation_history.append({
            'role': 'user',
            'content': query
        })
        conversation_history.append({
            'role': 'assistant', 
            'content': json.dumps({'suggestions': suggestions})
        })
        
        # Process continuation
        return await process_query(config, tui, adapter, executor, model_name, 
                                 continuation, conversation_history)
    
    return selected


@click.command()
@click.option('-m', '--model', default=None, help='Model to use (e.g., gpt4, claude, my_model)')
@click.argument('description', nargs=-1)
def main(model: Optional[str], description):
    """AI Terminal Assistant - Let AI help you with terminal commands."""
    # Load configuration
    config = Config.load()
    
    # Initialize TUI
    tui = TUI()
    
    # Show welcome if no description provided
    if not description:
        tui.display_welcome()
        tui.error("Please provide a description of what you want to do")
        sys.exit(1)
    
    # Join description words
    description_text = ' '.join(description)
    
    # Determine which model to use
    if model:
        # User specified a model
        adapter = create_adapter(model, config)
        if not adapter:
            tui.error(f"Failed to initialize model: {model}")
            tui.error(f"Check if 'test' is configured in your config.yaml")
            import traceback
            traceback.print_exc()
            setup_mode(config, tui)
        model_to_use = model
    else:
        # Try models in priority order
        result = find_working_model(config, tui)
        if not result:
            setup_mode(config, tui)
        model_to_use, adapter = result
    
    try:
        # Initialize executor
        executor = CommandExecutor(config)
        
        # Run the async query processor
        import asyncio
        loop = asyncio.get_event_loop()
        selected = loop.run_until_complete(
            process_query(config, tui, adapter, executor, model_to_use, description_text)
        )
        
        if selected:
            # Extract command from selection
            if isinstance(selected, dict):
                command = selected.get('command', '')
            else:
                command = str(selected)
            
            # Check if command is in allow-list or needs confirmation
            if executor.is_command_allowed(command):
                # Execute directly
                success, stdout, stderr = executor.execute_command(command, require_confirmation=False)
                tui.display_result(success, stdout, stderr)
            else:
                # Require confirmation
                if tui.confirm_execution(command):
                    success, stdout, stderr = executor.execute_command(command, require_confirmation=False)
                    tui.display_result(success, stdout, stderr)
                else:
                    tui.info("Command execution cancelled")
    
    except Exception as e:
        tui.error(str(e))
        sys.exit(1)


if __name__ == '__main__':
    main()