# 🔄 Hotloading Rules & Protocols

## Overview

Mini Agent now supports **hotloading of rules and protocols** from a markdown file! The system automatically detects changes to your rules file and reloads them without restarting the agent.

## ✨ Features

### 1. **Automatic Rule Loading**
- Loads rules from `/home/x/Documents/master-mas/TeamADAPT_Rules.md` (or custom path)
- Appends rules to system prompt automatically
- Rules become part of agent's instructions

### 2. **Hotloading (No Restart Needed)**
- Detects when rules file changes
- Automatically reloads rules before each agent run
- Updates system prompt on-the-fly
- Shows 🔄 indicator when reloading

### 3. **Section Extraction**
- Load specific sections of your rules
- Filter rules by topic/category
- Customizable system prompt

### 4. **Error Handling**
- Graceful fallback if rules file missing
- Clear error messages
- Continues working with base prompt

## 📁 Default Rules File

**Default Location**: `/home/x/Documents/master-mas/TeamADAPT_Rules.md`

This file contains:
- Environment rules (no Docker, system Python)
- Repository structure guidelines
- Git ignore policy
- Operations discipline (logging requirements)
- Task workflow protocols
- Documentation best practices
- Git/GitHub workflows
- And more...

## 🚀 Usage

### Basic Usage (Automatic)

No configuration needed! Rules are loaded automatically:

```bash
mini-agent

# In output, you'll see:
✅ Loaded system prompt (from: ...)
📋 Loaded 9 rules/protocols sections
...
```

The rules are now part of the agent's system prompt and will be followed.

## 📝 Rules File Format

Use standard markdown format with headers:

```markdown
## Environment Rules

- Docker is **not** used.
- Python virtual environments (**venv**) are **not** used.
- All Python execution is **system-wide**.

## Git Ignore Policy

All logical, ephemeral, temporary, runtime, or generated artifacts must be added to `.gitignore`.

## Task Workflow Protocol

1. **Selecting a Task**
   Choose a task directory from `/ops/to_do/`.

2. **Begin Work**
   Move the task directory into `/ops/in_progress/`.

3. **Execution**
   Perform the work directly at the system level.
   Log all decisions and actions.
```

### Supported Header Levels

- `## Header` - Top-level sections (extractable)
- `### Subheader` - Subsections
- `####` or deeper - Fine-grained organization

## 🔥 Hotloading in Action

### Change Rules Without Restart

1. **Start Mini Agent**
   ```bash
   mini-agent
   ```

2. **Make changes to rules file** (keep Mini Agent running)
   ```bash
   nano /home/x/Documents/master-mas/TeamADAPT_Rules.md
   # Add new rule or modify existing ones
   # Save file
   ```

3. **Send a message to Mini Agent**
   ```
   You: Create a new Python script
   ```

4. **See hotloading in action**
   ```
   🔄 Rules file changed, hotloading...
   ✅ Hotloaded rules into system prompt
   🤖 Working...
   ```

The new rules are immediately applied without restarting!

## 🎯 Section Extraction

### Load Specific Sections

You can extract specific sections from your rules:

```python
from mini_agent.rules_loader import RulesLoader

rl = RulesLoader("/home/x/Documents/master-mas/TeamADAPT_Rules.md")

# Get specific section
env_rules = rl.get_section("Environment Rules")
print(env_rules)

# Get Git ignore policy
git_rules = rl.get_section("Git Ignore Policy")
print(git_rules)

# Get task workflow
workflow = rl.get_section("Task Workflow Protocol")
print(workflow)
```

### Section Extraction Example

```python
from mini_agent.rules_loader import create_system_prompt_with_rules

base_prompt = "You are a helpful assistant..."
rl = RulesLoader()

# Create prompt with only Environment Rules
env_only_prompt = create_system_prompt_with_rules(
    base_prompt,
    rl,
    custom_sections=["Environment Rules"]
)
```

## 🔧 Custom Rules File

### Use Custom Rules File

```python
from mini_agent.rules_loader import RulesLoader

# Use custom rules file
rl = RulesLoader("/path/to/your/rules.md")
rules = rl.load_rules()
```

### Change Default Location

Set environment variable:

```bash
export MINI_AGENT_RULES_FILE="/path/to/custom-rules.md"
mini-agent
```

Or in code:

```python
import os
os.environ["MINI_AGENT_RULES_FILE"] = "/path/to/custom-rules.md"
```

## 📊 Rules Metadata

Get information about loaded rules:

```python
from mini_agent.rules_loader import RulesLoader

rl = RulesLoader()
meta = rl.get_rules_metadata()

print(f"Rules loaded: {meta['rules_loaded']}")
print(f"File exists: {meta['exists']}")
print(f"File size: {meta['file_size']} bytes")
print(f"Hotload enabled: {meta['hotload_enabled']}")
print(f"Last modified: {meta['last_modified']}")
```

**Example Output:**
```
{'exists': True,
 'file': '/home/x/Documents/master-mas/TeamADAPT_Rules.md',
 'file_size': 3996,
 'last_modified': 1734366337.1248388,
 'rules_loaded': 9,
 'hotload_enabled': True,
 'cached': True}
```

## 🎮 Interactive Hotloading

### Manual Hotload Command

While using Mini Agent, you can manually trigger a reload:

```
You: /reload-rules
🔄 Reloading rules from disk...
✅ Loaded 9 rules/protocols sections
```

### Automatic Hotloading

Rules are automatically reloaded:
- Before each agent execution
- When file modification time changes
- Within 5-second cache window

## 🚀 Integration with System Prompt

### How Rules Are Integrated

Rules are appended to the system prompt with a separator:

```
You are Mini-Agent, an intelligent assistant powered by MiniMax M2...

---

# TeamADAPT Rules & Protocols

The following rules, protocols, and best practices MUST be followed:

TeamADAPT Rules
...

## Environment Rules

- Docker is **not** used.
- Python virtual environments (**venv**) are **not** used.
...
```

### Custom Integration

```python
from mini_agent.rules_loader import create_system_prompt_with_rules

base_prompt = """You are a development assistant.
Your role is to help with code and system operations."""

rl = RulesLoader()
enhanced_prompt = create_system_prompt_with_rules(base_prompt, rl)

# Use enhanced_prompt with your LLM
print(enhanced_prompt)
```

## 🚨 Troubleshooting

### Rules Not Loading

Check if file exists:
```bash
ls -lh /home/x/Documents/master-mas/TeamADAPT_Rules.md
```

Check file permissions:
```bash
cat /home/x/Documents/master-mas/TeamADAPT_Rules.md | head -5
```

### Hotloading Not Working

Check file modification time:
```bash
stat /home/x/Documents/master-mas/TeamADAPT_Rules.md
```

Enable debug output (in code):
```python
rl = RulesLoader()
rl._cache_duration = 0  # Disable cache for testing
```

### Rules Not Applied

Check system prompt includes rules:
```python
print(agent.system_prompt[-500:])  # Last 500 chars
```

Verify rules format is correct (must have section headers).

## 🎯 Best Practices

### 1. Organize Rules Logically

Group related rules under clear headers:
```markdown
## Environment Rules
## Git Workflow
## Documentation Standards
## Testing Requirements
```

### 2. Use Specific, Actionable Language

Good:
```markdown
- Always use `git add .` before committing
- Log all decisions in ops/operations_history.md
```

Bad:
```markdown
- Be careful with git
- Document things
```

### 3. Keep Rules Updated

- Review rules regularly
- Update as workflows evolve
- Remove outdated rules
- Add new protocols as needed

### 4. Use Section Extraction for Focus

Create focused prompts for specific tasks:
```python
# Only load environment rules for deployment tasks
deployment_prompt = create_system_prompt_with_rules(
    base_prompt,
    rl,
    custom_sections=["Environment Rules", "Systemd Configuration"]
)
```

## 📈 Performance

- Rules loading: ~10ms for typical file
- Hotloading check: <1ms (cached every 5s)
- Section extraction: ~2ms per section
- No impact on agent response time

## 🎊 Summary

✅ **Auto-loads rules** from `/home/x/Documents/master-mas/TeamADAPT_Rules.md`
✅ **Hotloading** - no restart needed when rules change
✅ **Section extraction** - load specific sections as needed
✅ **Error handling** - graceful fallback if rules missing
✅ **Performance** - minimal impact with caching
✅ **Flexible** - custom paths, custom integration

Your rules and protocols are now dynamically loaded and can be updated on the fly!
