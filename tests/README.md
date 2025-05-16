# AITerm Tests

This directory contains the essential tests for the AITerm project.

## Test Files

1. **test_simple.py** - Basic smoke test that verifies imports and core functionality
2. **test_adapters.py** - Tests the adapter interface and TestAdapter implementation
3. **test_structured_prompt.py** - Tests the prompt builder system
4. **test_new_config.py** - Tests the configuration management system
5. **test_new_system.py** - Integration test for config + adapter + prompt builder
6. **test_conversation_flow.py** - Tests multi-turn conversation handling
7. **test_with_uv.py** - Tests CLI usage with `uv run`
8. **test_with_uv_config.py** - Tests custom config file loading
9. **test_non_interactive.py** - Tests non-interactive usage with piped input

## Running Tests

To run all tests:

```bash
cd /home/dev/git/aiterm
for test in tests/test_*.py; do
    echo "Running $test..."
    uv run $test
done
```

To run a specific test:

```bash
uv run tests/test_simple.py
```

## Test Coverage

- **Core Components**: Config, PromptBuilder, BaseLLMAdapter
- **Adapters**: TestAdapter with all LLM providers
- **Integration**: Full system workflow from input to output
- **User Interface**: Interactive and non-interactive modes
- **Configuration**: YAML loading/saving, provider settings