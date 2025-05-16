#!/usr/bin/env python3
import click
import sys
import json
import re
import os
from typing import Optional, List, Union, Tuple
from .config import Config, ModelConfig
from .tui import TUI
from .executor import CommandExecutor
from .llm.base import BaseLLMAdapter
from .context_gather import build_extended_context, get_path_commands, get_shell_history
from .prompt_builder import build_structured_prompt
from .llm.factory import create_adapter

def is_valid_api_key(api_key: Optional[str]) -> bool:
    """Check if an API key appears to be valid (not a placeholder)."""
    if not api_key:
        return False

    # Remove whitespace
    api_key = api_key.strip()

    # Check for placeholder patterns
    placeholders = [
        'your_api_key_here',
        'your-api-key',
        'YOUR_API_KEY',
        '<your-api-key>',
        'sk-...',
        'sk-ant-...',
        '...',
        'xxx',
        'TODO',
        '<YOUR_API_KEY>',
        '{YOUR_API_KEY}',
        '${YOUR_API_KEY}',
        'your_key_here',
        'placeholder',
        'test',
        'demo'
    ]

    # Check if it's a placeholder
    if api_key.lower() in [p.lower() for p in placeholders]:
        return False

    # Check for very short keys
    if len(api_key) < 20:
        return False

    # Check for basic patterns (very lenient)
    # OpenAI keys usually start with sk- followed by alphanumeric
    # Anthropic keys usually start with sk-ant- followed by alphanumeric
    # But we'll be lenient and just check for reasonable length and characters
    if not re.match(r'^[a-zA-Z0-9_\-]{20,}$', api_key):
        return False

    return True


def build_model_list(config: Config, user_model: Optional[str] = None) -> List[Tuple[str, str]]:
    """Build a prioritized list of models with valid API keys.

    Returns list of (model_name, api_key) tuples.
    Priority order:
    1. User-specified model (if any)
    2. Models from default_models list in config

    API key priority for each model:
    1. Model-specific api_key from config
    2. Provider-specific api_key from config
    3. Environment variable
    """
    models_to_try = []
    seen_models = set()

    # Helper function to get API key for a model
    def get_api_key_for_model(model_name: str) -> Optional[str]:
        model_config = config.get_model_config(model_name)
        if not model_config:
            return None

        # 1. Check model-specific API key
        if model_config.api_key and is_valid_api_key(model_config.api_key):
            return model_config.api_key

        # 2. Check provider API key
        provider_config = config.get_provider_config(model_config.provider)
        if provider_config and provider_config.api_key and is_valid_api_key(provider_config.api_key):
            return provider_config.api_key

        # 3. Check environment variables
        env_var_map = {
            'openai': 'OPENAI_API_KEY',
            'anthropic': 'ANTHROPIC_API_KEY'
        }

        env_var = env_var_map.get(model_config.provider)
        if env_var:
            env_key = os.environ.get(env_var)
            if is_valid_api_key(env_key):
                return env_key

        # Special case: Ollama doesn't need an API key
        if model_config.provider == 'ollama':
            return 'ollama-local'

        return None

    # Add user-specified model first if provided
    if user_model:
        api_key = get_api_key_for_model(user_model)
        if api_key:
            models_to_try.append((user_model, api_key))
            seen_models.add(user_model)

    # Add models from default list
    for model_name in config.default_models:
        if model_name not in seen_models:
            api_key = get_api_key_for_model(model_name)
            if api_key:
                models_to_try.append((model_name, api_key))
                seen_models.add(model_name)

    return models_to_try


def setup_mode(config: Config, tui: TUI):
    """Help user configure API keys."""
    tui.console.print("\n[bold cyan]AI Terminal Setup[/bold cyan]\n")
    tui.console.print("No working models found. Let's set up API keys.")
    tui.console.print("\nYou can configure API keys in the following ways:")
    tui.console.print("1. Environment variables: OPENAI_API_KEY, ANTHROPIC_API_KEY")
    tui.console.print("2. Config file: ~/.config/aiterm/config.yaml")
    tui.console.print("\nExample configuration:")
    tui.console.print("[yellow]default_models: \\[gpt4, claude, ollama\\][/yellow]")
    tui.console.print("[yellow]providers:[/yellow]")
    tui.console.print("[yellow]  openai:[/yellow]")
    tui.console.print("[yellow]    api_key: sk-...[/yellow]")
    tui.console.print("[yellow]  anthropic:[/yellow]")
    tui.console.print("[yellow]    api_key: sk-ant-...[/yellow]")
    tui.console.print("[yellow]models:[/yellow]")
    tui.console.print("[yellow]  gpt4:[/yellow]")
    tui.console.print("[yellow]    provider: openai[/yellow]")
    tui.console.print("[yellow]    model: gpt-4o[/yellow]")
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
    # tui.status(f"Asking {model_name} for suggestions...")
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

    # If user quit (selected is None and continuation is None), return special value
    if selected is None and continuation is None:
        return 'QUIT'

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

    # Build the list of models to try
    models_to_try = build_model_list(config, model)

    if not models_to_try:
        tui.error("No models with valid API keys found")
        setup_mode(config, tui)
        return

    # Try each model until one succeeds
    successful_model = None
    successful_adapter = None
    errors = []

    for model_name, api_key in models_to_try:
        try:
            # Create adapter
            adapter = create_adapter(model_name, config)
            if adapter:
                # Try to get a response to verify it's working
                executor = CommandExecutor(config)
                import asyncio
                loop = asyncio.get_event_loop()

                # Quick test query
                selected = loop.run_until_complete(
                    process_query(config, tui, adapter, executor, model_name, description_text)
                )

                if selected == 'QUIT':
                    # User explicitly quit, exit cleanly
                    sys.exit(0)
                elif selected:
                    # Model worked, use it for execution
                    successful_model = model_name
                    successful_adapter = adapter
                    break
                else:
                    errors.append(f"{model_name}: No response generated")
        except Exception as e:
            errors.append(f"{model_name}: {str(e)}")
            continue

    # If no model worked, show errors and enter setup mode
    if not successful_model:
        tui.console.print("\n[yellow]Tried models:[/yellow]")
        for error in errors:
            tui.console.print(f"  [dim]• {error}[/dim]")
        setup_mode(config, tui)
        return

    # Use the successful model
    model_to_use = successful_model
    adapter = successful_adapter

    # Process the selection from the successful model
    try:
        if selected == 'QUIT':
            # User quit, exit cleanly
            sys.exit(0)
        elif selected:
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
