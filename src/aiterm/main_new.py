#!/usr/bin/env python3
import click
import sys
import os
from typing import Optional, List
from .config_new import Config, ModelConfig
from .tui import TUI
from .executor import CommandExecutor
from .llm import OllamaAdapter, OpenAIAdapter, AnthropicAdapter, TestAdapter, LLMAdapter
from .context_gather import build_extended_context


# Provider to adapter mapping
PROVIDER_ADAPTERS = {
    'ollama': OllamaAdapter,
    'openai': OpenAIAdapter,
    'anthropic': AnthropicAdapter,
    'test': TestAdapter
}


def get_llm_adapter(model_name: str, config: Config) -> Optional[LLMAdapter]:
    """Factory function to get the appropriate LLM adapter."""
    model_config = config.get_model_config(model_name)
    if not model_config:
        return None
    
    # Get the adapter class for this provider
    adapter_class = PROVIDER_ADAPTERS.get(model_config.provider)
    if not adapter_class:
        return None
    
    # Get provider config
    provider_config = config.get_provider_config(model_config.provider)
    
    # Build adapter config
    adapter_config = {}
    
    # Add provider settings
    if provider_config:
        if provider_config.base_url:
            adapter_config['base_url'] = provider_config.base_url
        adapter_config.update(provider_config.custom_options)
    
    # Add model settings
    adapter_config['model'] = model_config.model
    
    # Get API key
    api_key = config.get_api_key(model_name)
    if api_key:
        adapter_config['api_key'] = api_key
    
    # Add custom model options
    adapter_config.update(model_config.custom_options)
    
    try:
        return adapter_class(adapter_config)
    except Exception as e:
        return None


def find_working_model(config: Config, tui: TUI) -> Optional[tuple[str, LLMAdapter]]:
    """Try models in priority order until one works."""
    errors = []
    
    for model_name in config.default_models:
        try:
            adapter = get_llm_adapter(model_name, config)
            if adapter:
                # For Ollama, try a quick test to see if it's running
                if isinstance(adapter, OllamaAdapter):
                    import requests
                    try:
                        resp = requests.get(adapter.base_url + '/api/tags', timeout=0.5)
                        if resp.status_code == 200:
                            return model_name, adapter
                    except:
                        errors.append(f"{model_name}: Ollama not running")
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
    tui.console.print("[yellow]default_models: [gpt4, claude, ollama]")
    tui.console.print("providers:")
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


def build_extended_context_new(config: Config, model_name: str, context: dict = None) -> dict:
    """Build extended context based on model configuration."""
    if context is None:
        context = {}
    
    model_config = config.get_model_config(model_name)
    if not model_config:
        return context
    
    # Use model-specific settings
    include_path = model_config.include_path_commands
    include_history = model_config.include_history_context
    history_size = model_config.history_context_size
    
    extended_context = {}
    
    if include_path:
        try:
            from .context_gather import get_path_commands
            path_commands = get_path_commands()
            if path_commands:
                extended_context['available_commands'] = path_commands[:1000]
        except Exception:
            pass
    
    if include_history:
        try:
            from .context_gather import get_shell_history
            recent, unique_older = get_shell_history(history_size)
            if recent:
                extended_context['recent_commands'] = recent[:100]
            if unique_older:
                extended_context['command_history'] = unique_older[:200]
        except Exception:
            pass
    
    # Merge contexts
    if extended_context:
        context['system_context'] = extended_context
    
    return context


def process_query(config: Config, tui: TUI, llm: LLMAdapter, executor: CommandExecutor, 
                  model_name: str, description_text: str, conversation_history: List[str] = None):
    """Process a single query with the LLM."""
    
    if conversation_history is None:
        conversation_history = []
    
    # Build the full conversation text
    if conversation_history:
        # History already contains everything, current query is the latest user input
        full_text = "\n".join(conversation_history)
    else:
        full_text = description_text
    
    # Check if we need context
    try:
        needs_context, context_commands = llm.needs_context(full_text)
    except Exception as e:
        # If the model fails, go to setup mode
        if "Ollama API error" in str(e):
            tui.error("Ollama is not running")
        else:
            tui.error(str(e))
        setup_mode(config, tui)
    
    context = None
    context_info = {}
    
    if needs_context and context_commands:
        context = executor.gather_context(context_commands)
        context_info['context_commands'] = context_commands

    # Get model config for context settings
    model_config = config.get_model_config(model_name)
    if model_config:
        context_info['has_path_commands'] = model_config.include_path_commands
        context_info['has_history'] = model_config.include_history_context
    else:
        context_info['has_path_commands'] = False
        context_info['has_history'] = False

    # Add extended context if configured
    context = build_extended_context_new(config, model_name, context)

    # Display compact status
    tui.display_status(model_name, context_info)

    # Generate command suggestions
    suggestions = llm.generate_command(full_text, context)
    
    # Display suggestions and let user choose
    selected, continuation = tui.display_suggestions(suggestions)
    
    if continuation:
        # User wants to continue the conversation
        if not conversation_history:  # First time
            conversation_history.append(description_text)
            conversation_history.extend([f"[{i+1}] {s.command}" for i, s in enumerate(suggestions)])
        conversation_history.append(f"User: {continuation}")
        # Pass the continuation as the new query, history contains the context
        return process_query(config, tui, llm, executor, model_name, continuation, conversation_history)
    
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
        llm = get_llm_adapter(model, config)
        if not llm:
            tui.error(f"Failed to initialize model: {model}")
            setup_mode(config, tui)
        model_to_use = model
    else:
        # Try models in priority order
        result = find_working_model(config, tui)
        if not result:
            setup_mode(config, tui)
        model_to_use, llm = result
    
    try:
        # Initialize executor
        executor = CommandExecutor(config)
        
        # Process the query (with potential continuation)
        selected = process_query(config, tui, llm, executor, model_to_use, description_text)
        
        if selected:
            # Check if command is in allow-list or needs confirmation
            if executor.is_command_allowed(selected.command):
                # Execute directly
                success, stdout, stderr = executor.execute_command(selected.command, require_confirmation=False)
                tui.display_result(success, stdout, stderr)
            else:
                # Require confirmation
                if tui.confirm_execution(selected.command):
                    success, stdout, stderr = executor.execute_command(selected.command, require_confirmation=False)
                    tui.display_result(success, stdout, stderr)
                else:
                    tui.info("Command execution cancelled")
    
    except Exception as e:
        tui.error(str(e))
        sys.exit(1)


if __name__ == '__main__':
    main()