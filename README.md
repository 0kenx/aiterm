# AITerm - AI Terminal Assistant

AITerm is an AI-powered terminal command assistant that converts natural language descriptions into shell commands. It features an intelligent two-step process: first determining if context is needed, then generating appropriate command suggestions.

## Features

- Natural language to shell command translation
- Multi-model support (OpenAI, Anthropic, Ollama)
- Intelligent context gathering before command generation
- Structured XML-based prompting system
- JSON-formatted responses for consistency
- Model-specific configuration and instructions
- Interactive command selection with rich TUI
- Non-interactive mode for automation
- Test mode for development

## Installation

### NixOS

#### Using Flakes

Add to your `flake.nix`:

```nix
{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    aiterm.url = "github:0kenx/aiterm";
  };

  outputs = { self, nixpkgs, aiterm, ... }: {
    nixosConfigurations.myhost = nixpkgs.lib.nixosSystem {
      modules = [
        ({ pkgs, ... }: {
          environment.systemPackages = [
            aiterm.packages.${pkgs.system}.default
          ];
        })
      ];
    };
  };
}
```

Or use the provided NixOS module:

```nix
{
  modules = [
    aiterm.nixosModules.default
    {
      programs.aiterm = {
        enable = true;
        defaultConfig = {
          default_model = "gpt-4o";
          enforce_json_output = true;
        };
      };
    }
  ];
}
```

#### Direct Installation

```bash
# Run without installing
nix run github:0kenx/aiterm -- list python files

# Install to user profile
nix profile install github:0kenx/aiterm
```

### Home Manager

Add to your Home Manager configuration:

```nix
{ config, pkgs, ... }:

{
  home.packages = [
    (pkgs.callPackage (builtins.fetchTarball {
      url = "https://github.com/0kenx/aiterm/archive/main.tar.gz";
    }) {})
  ];

  # Optional: manage aiterm config with Home Manager
  xdg.configFile."aiterm/config.yaml".text = ''
    enforce_json_output: true
    default_model: gpt-4o

    providers:
      openai:
        api_key: ''${OPENAI_API_KEY}
      anthropic:
        api_key: ''${ANTHROPIC_API_KEY}

    models:
      gpt-4o:
        provider: openai
        model: gpt-4o
        include_path_commands: true
  '';
}
```

Or using flakes in Home Manager:

```nix
{
  inputs = {
    home-manager.url = "github:nix-community/home-manager";
    aiterm.url = "github:0kenx/aiterm";
  };

  outputs = { self, home-manager, aiterm, ... }: {
    homeConfigurations.myuser = home-manager.lib.homeManagerConfiguration {
      modules = [
        ({ pkgs, ... }: {
          home.packages = [
            aiterm.packages.${pkgs.system}.default
          ];
        })
      ];
    };
  };
}
```

### Using uv (Recommended for Development)

```bash
# Clone the repository
git clone https://github.com/0kenx/aiterm
cd aiterm

# Run directly with uv
uv run ait list all python files
```

### Using pip

```bash
pip install .
ait list all python files
```

## Usage

### Interactive Mode

```bash
# Use default model
ait find large files over 100MB

# Specify a model
ait -m gpt-4o list docker containers
ait -m claude-3.7 show system resources
ait -m ollama compress this directory

# Use test mode (no API required)
ait -m test show network connections
```

### Non-Interactive Mode

```bash
# Pipe input
echo "list all python files" | ait

# Use in scripts
ait --no-interactive find files modified today
```

## Configuration

AITerm uses a YAML configuration file located at `~/.config/aiterm/config.yaml` (or `config.yaml` in the local directory).

```yaml
# Enable strict JSON responses
enforce_json_output: true

# Default model to use
default_model: gpt-4o

# Provider configurations
providers:
  openai:
    api_key: ${OPENAI_API_KEY}  # Environment variable
    
  anthropic:
    api_key: ${ANTHROPIC_API_KEY}
    
  ollama:
    base_url: http://localhost:11434

# Model configurations
models:
  gpt-4o:
    provider: openai
    model: gpt-4o
    instructions: |
      You are a terminal command expert. Focus on practical solutions.
    include_path_commands: true
    include_history_context: true
    
  claude-3.7:
    provider: anthropic
    model: claude-3-7-sonnet-20250122
    instructions: |
      Provide clear and efficient command suggestions.
    
  ollama:
    provider: ollama
    model: llama3.1
    
  test:
    provider: test
    model: test
```

### Model-Specific Instructions

Each model can have custom instructions that guide its behavior:

```yaml
models:
  gpt-4o:
    provider: openai
    model: gpt-4o
    instructions: |
      Focus on modern best practices.
      Prefer using newer command options when available.
      Always consider cross-platform compatibility.
```

## Architecture

### Core Components

1. **Config System** (`config.py`)
   - Manages providers and models
   - Handles environment variable substitution
   - Supports layered configuration

2. **Prompt Builder** (`prompt_builder.py`)
   - Creates structured XML prompts
   - Enforces JSON response format
   - Handles context injection

3. **LLM Adapters** (`llm/`)
   - Base adapter with async support
   - Provider-specific implementations
   - Test adapter for development

4. **Context Gathering** (`context_gather.py`)
   - PATH command collection
   - Shell history analysis
   - Smart context filtering

5. **Command Executor** (`executor.py`)
   - Safe command execution
   - Timeout handling
   - Result formatting

## Development

### Running Tests

```bash
# Run all tests
uv run python tests/test_simple.py

# Run specific test
uv run tests/test_adapters.py
```

### Test Mode

The test mode provides mock responses for development:

```bash
ait -m test list all python files
```

### Project Structure

```
aiterm/
├── src/
│   └── aiterm/
│       ├── config.py           # Configuration management
│       ├── context_gather.py   # Context collection
│       ├── executor.py         # Command execution
│       ├── llm/               # LLM adapters
│       │   ├── base.py
│       │   ├── openai.py
│       │   ├── anthropic.py
│       │   ├── ollama.py
│       │   └── test.py
│       ├── main.py             # Main entry point
│       ├── prompt_builder.py   # Prompt construction
│       └── tui.py              # Terminal UI
├── tests/                     # Test suite
├── README.md
└── pyproject.toml
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

MIT