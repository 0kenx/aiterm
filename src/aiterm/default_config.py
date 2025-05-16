DEFAULT_CONFIG = {
    'default_models': ['ollama', 'gpt-4o', 'claude-3.7', 'gpt-3.5-turbo'],
    'allowed_commands': [
        'pwd', 'ls', 'echo', 'date', 'cat', 'grep', 'find', 'which',
        'whoami', 'hostname', 'uname', 'df', 'du', 'ps', 'top', 'free', 'uptime'
    ],
    'model_configs': {
        'ollama': {
            'base_url': 'http://localhost:11434',
            'model': 'llama3.1'
        }
    },
    'history_file': '~/.local/share/aiterm/history.json',
    'history_context_size': 500,
    'include_path_commands': {
        'ollama': True,
        'default': False
    },
    'include_history_context': {
        'ollama': True,
        'default': False
    }
}