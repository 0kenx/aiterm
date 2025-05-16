DEFAULT_CONFIG = {
    'default_models': ['ollama', 'o4-mini', 'claude-3.7', 'gpt-4.1-mini'],
    'allowed_commands': [
        'pwd', 'ls', 'echo', 'date', 'cat', 'grep', 'find', 'which',
        'whoami', 'hostname', 'uname', 'df', 'du', 'ps', 'top', 'free', 'uptime'
    ],
    'model_configs': {
        'ollama': {
            'base_url': 'http://localhost:11434',
            'model': 'gemma3:12b'
        }
    },
    'history_file': '~/.local/share/aiterm/history.json',
    'history_context_size': 50,
    'available_commands_limit': 2000,
    'include_path_commands': {
        'ollama': True,
        'default': False
    },
    'include_history_context': {
        'ollama': True,
        'default': False
    }
}
