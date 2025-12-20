# Enhanced Mini Agent Setup

This document describes the enhanced setup of Mini Agent with all features enabled and maximum capabilities.

## 🚀 Quick Start

```bash
# Install dependencies (already done)
uv sync

# Configure your API key in mini_agent/config/config.yaml
# Replace "YOUR_API_KEY_HERE" with your actual MiniMax API key

# Run the enhanced agent
python main_enhanced.py

# Or run the enhanced CLI with pause/interject support
mini-agent
```

## ✨ Enhanced Features

### 1. Configuration Enhancements
- **Max Steps**: 2,000,000 (extremely high for long-running tasks)
- **All Tools Enabled**: File tools, bash, session notes, MCP, and Claude Skills
- **MCP Tools Enabled**: Web search and knowledge graph memory
- **Retry Mechanism**: Enabled with exponential backoff

### 2. All Tools Enabled

#### Basic Tools
- ✅ **ReadTool**: Read files from workspace
- ✅ **WriteTool**: Create new files
- ✅ **EditTool**: Edit existing files
- ✅ **BashTool**: Execute shell commands
- ✅ **BashOutputTool**: Get bash command output
- ✅ **BashKillTool**: Kill running processes

#### Session Notes
- ✅ **SessionNoteTool**: Record persistent notes
- ✅ **RecallNoteTool**: Recall stored information

#### MCP Tools
- ✅ **MiniMax Search**: Web search, parallel search, and browsing
- ✅ **Memory**: Knowledge graph memory system

#### Claude Skills
15+ professional skills including:
- Document creation (PDF, DOCX)
- Web application testing
- Algorithmic art generation
- Brand guidelines creation
- Canvas design
- Internal communications
- And more...

### 3. Pause/Interject Functionality

The enhanced CLI supports graceful pausing and interjection:

- **Ctrl+C**: Pause the agent during execution
- **/pause**: Command to pause execution
- **/continue**: Resume paused execution
- **Interject**: While paused, type a new message to change direction
- **Double Ctrl+C**: Force exit if needed

## 📊 Tool Summary

| Category | Tools | Status |
|----------|-------|--------|
| File Operations | 3 | ✅ Enabled |
| Bash Operations | 3 | ✅ Enabled |
| Session Notes | 2 | ✅ Enabled |
| MCP Tools | 2 | ✅ Enabled |
| Claude Skills | 15+ | ✅ Enabled |
| **Total** | **25+** | **✅ Enabled** |

## 🎯 Usage Examples

### Example 1: Create and Test a Python Script
```
You: Create a Python calculator with unit tests, run the tests, and save the results
```

### Example 2: Research and Document
```
You: Search for information about quantum computing, create a summary PDF, and save it
```

### Example 3: Web Application with Memory
```
You: Create a Flask web app for task management. Remember my preference for dark mode in your notes.
```

### Example 4: Complex Multi-step Task
```
You: Build a data processing pipeline that:
1. Downloads data from a URL
2. Processes it with Python
3. Creates visualizations
4. Generates a report PDF
5. Stores the methodology in session memory
```

## ⌨️ Enhanced Commands

### New Commands
- `/pause` - Pause agent execution
- `/continue` - Resume paused execution

### Keyboard Shortcuts
- **Ctrl+C** - Pause/resume agent (press twice to force exit)
- **Ctrl+U** - Clear current input line
- **Ctrl+L** - Clear screen
- **Ctrl+J** - Insert newline
- **Tab** - Auto-complete commands
- **↑/↓** - Browse command history

## 🔧 Configuration

### mini_agent/config/config.yaml
```yaml
max_steps: 2000000  # Very high limit

# All tools enabled
tools:
  enable_file_tools: true
  enable_bash: true
  enable_note: true
  enable_skills: true
  enable_mcp: true
```

### mini_agent/config/mcp.json
```json
{
  "mcpServers": {
    "minimax_search": { "disabled": false },
    "memory": { "disabled": false }
  }
}
```

## 📝 Files Created

1. **mini_agent/config/config.yaml** - Main configuration with max_steps=2000000
2. **mini_agent/config/mcp.json** - MCP tools enabled
3. **main_enhanced.py** - Enhanced runner with all features
4. **mini_agent/cli.py** - Enhanced CLI with pause/interject support

## 🧪 Testing

To verify the enhanced setup:

```bash
# Test configuration
python -c "
from mini_agent.config import Config
config = Config.from_yaml('mini_agent/config/config.yaml')
print(f'Max steps: {config.agent.max_steps}')
print(f'MCP enabled: {config.tools.enable_mcp}')
"

# Test tool loading
python -c "
from mini_agent.tools import BashTool, ReadTool
print('✅ Tools can be imported')
"

# Run a simple test
python main_enhanced.py
```

## 🎮 Interactive Features

### During Execution
When the agent is running a task:
1. Press **Ctrl+C** to pause
2. You'll see options to continue or interject
3. Type a new message to change direction
4. Or type `/continue` to resume

### Example Session
```
You: Create a web scraper that downloads images
Agent: 🤖 Working... (Press Ctrl+C to pause)

# Press Ctrl+C
⏸️  Agent paused.
   Options:
   - Type /continue to resume execution
   - Type a new message to interject
   - Press Ctrl+C again to force exit

You: Actually, focus on downloading PDFs instead of images
Agent: 🤖 Adjusting task... (Press Ctrl+C to pause)
```

## 🔍 Session Memory

The agent maintains session memory using:
- Session notes stored in `workspace/.agent_memory.json`
- Automatic conversation history management
- Token usage tracking and summarization

## 📈 Advantages of Enhanced Setup

1. **Maximum Capability**: All 25+ tools enabled
2. **Long-running Tasks**: 2,000,000 max steps
3. **Flexible Control**: Pause and interject anytime
4. **Persistent Memory**: Session notes across conversations
5. **Professional Skills**: Access to Claude Skills library
6. **External Integration**: MCP tools for web search and knowledge graphs
7. **Production Ready**: Comprehensive error handling and logging

## 🚦 Next Steps

1. **Configure API Keys**: Add your MiniMax API key
2. **Customize MCP**: Add API keys for MCP services if needed
3. **Explore Skills**: Check available skills in `mini_agent/skills/`
4. **Create Projects**: Start building with the enhanced agent
5. **Monitor Usage**: Check token usage and session statistics

## 📚 More Information

- Original README: [README.md](README.md)
- Development Guide: [docs/DEVELOPMENT_GUIDE.md](docs/DEVELOPMENT_GUIDE.md)
- Production Guide: [docs/PRODUCTION_GUIDE.md](docs/PRODUCTION_GUIDE.md)

## 🎉 Summary

Your Mini Agent is now configured with:
- ✅ Maximum execution steps (2,000,000)
- ✅ All tools enabled (25+ tools)
- ✅ Pause/Interject functionality
- ✅ Session memory persistence
- ✅ MCP integration
- ✅ Claude Skills library
- ✅ Enhanced CLI interface

Ready for any task you throw at it! 🚀
