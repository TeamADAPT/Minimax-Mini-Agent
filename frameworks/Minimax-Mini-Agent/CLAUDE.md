# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Mini Agent is a Python-based AI agent framework that demonstrates best practices for building agents with the MiniMax M2 model. It uses an Anthropic-compatible API and supports interleaved thinking to unlock the model's reasoning capabilities.

## Essential Commands

### Development Setup
```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Install in editable mode for development
uv tool install -e .

# Initialize Claude Skills (optional but recommended)
git submodule update --init --recursive
```

### Running the Agent
```bash
# Run directly (for debugging)
uv run python -m mini_agent.cli

# Run installed version
mini-agent

# Run with custom workspace
mini-agent --workspace /path/to/your/project

# Run ACP server (for Zed Editor integration)
mini-agent-acp
```

### Testing
```bash
# Run all tests
pytest tests/ -v

# Run specific test modules
pytest tests/test_agent.py tests/test_note_tool.py -v

# Run with coverage
pytest tests/ --cov=mini_agent
```

### Linting
```bash
# Run pylint (configured in pyproject.toml)
pylint mini_agent/
```

## Architecture Overview

### Core Components

1. **Agent Loop** (`mini_agent/agent.py`): Main execution loop that manages conversation history, tool execution, and context summarization. Key methods:
   - `run()`: Main entry point for agent execution
   - `_summarize_history()`: Manages conversation context when approaching token limits
   - `_execute_tool()`: Handles tool execution with proper error handling

2. **LLM Clients** (`mini_agent/llm/`): Abstraction layer supporting both Anthropic and OpenAI APIs. The client handles:
   - Retry mechanisms with exponential backoff
   - Response streaming
   - Error handling and logging

3. **Tool System** (`mini_agent/tools/`): Modular tool architecture where each tool inherits from `Tool` base class. Tools include:
   - File operations (read, write, edit, list)
   - Bash command execution
   - Session notes for persistent memory
   - MCP tool loading for external integrations
   - Claude Skills integration

4. **Configuration** (`mini_agent/config.py`): Pydantic-based configuration system that loads from multiple sources:
   - Development config: `mini_agent/config/config.yaml`
   - User config: `~/.config/mini-agent/config.yaml`
   - Package config: `mini_agent/config/config-example.yaml`

### Tool Architecture

Tools follow a specific pattern:
- Inherit from `Tool` base class
- Define `name`, `description`, and `parameters` properties
- Implement `execute()` method that returns `ToolResult`
- Use explicit parameter signatures in subclasses for better type hints (pylint configured to allow this)

### MCP Integration

The project supports MCP (Model Context Protocol) tools through:
- `mcp.json` configuration file
- `MCPLoader` class that dynamically loads MCP servers
- Integration with external tools like knowledge graphs and web search

### Session Management

The agent maintains conversation state through:
- Message history with automatic summarization
- Session notes tool for persistent memory across sessions
- Token usage tracking and management
- Workspace directory for file operations

### Key Design Patterns

1. **Async Throughout**: All operations are async for better performance
2. **Type Safety**: Extensive use of Pydantic models for validation
3. **Error Handling**: Comprehensive error handling with retry mechanisms
4. **Logging**: Detailed logging at multiple levels for debugging
5. **Modular Tools**: Easy to add new tools without modifying core agent code

## Configuration

The main configuration file (`config.yaml`) controls:
- API settings (key, base URL, model)
- Agent behavior (max steps, workspace directory)
- Tool enablement flags
- Retry configuration
- MCP server settings

## Common Development Tasks

### Adding a New Tool
1. Create new file in `mini_agent/tools/`
2. Inherit from `Tool` base class
3. Implement required methods
4. Register in tool loading logic

### Modifying System Prompt
Edit `mini_agent/config/system_prompt.md` to customize agent behavior.

### Debugging
- Enable verbose logging in config
- Check logs in workspace directory
- Use `/stats` command in interactive mode to see token usage

## Important Notes

- Always use `uv` for dependency management
- Python 3.10+ is required
- The project uses git submodules for Claude Skills - ensure they're initialized
- MCP tools require separate configuration in `mcp.json`
- SSL certificate issues can be fixed by updating certifi package