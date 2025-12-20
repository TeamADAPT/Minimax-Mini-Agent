# Session Management Documentation

## Overview

The enhanced Mini Agent now supports complete session management, allowing you to save conversation history, resume previous sessions, and manage multiple conversation threads. Sessions are persisted to disk and survive application restarts.

## Features

- ✅ **Save Sessions**: Save current conversation at any time
- ✅ **Load Sessions**: Resume any previous conversation
- ✅ **Auto-resume**: Resume the last session on startup
- ✅ **Session List**: View all saved sessions with timestamps
- ✅ **Persistent Storage**: Sessions saved to `~/.mini-agent/sessions/`

## Commands

### /save [name]
Save the current conversation session.

**Usage:**
- `/save` - Save with auto-generated name (timestamp)
- `/save project-x` - Save with custom name

**Example:**
```
You: /save python-calculator-project
✅ Saved session 'python-calculator-project' as python-calculator-project
```

### /load [id]
Load a previous session.

**Usage:**
- `/load` - Load the most recent session
- `/load python-calculator-project` - Load specific session by ID

**Example:**
```
You: /load python-calculator-project
✅ Loaded session python-calculator-project with 15 messages
```

### /sessions
List all saved sessions in reverse chronological order.

**Output:**
```
Saved Sessions:
────────────────────────────────────────────────────────────
  1. python-calculator-project
     Messages: 15
     Saved: 2025-12-16 10:30:22

  2. web-scraping-task
     Messages: 8
     Saved: 2025-12-16 09:15:10

  3. 20251215_feature_analysis
     Messages: 23
     Saved: 2025-12-15 18:45:33
```

## Command-line Options

### --resume, -r
Automatically resume the last saved session on startup.

**Usage:**
```bash
# Resume last session
mini-agent --resume

# Or with short flag
mini-agent -r

# Resume with specific workspace
mini-agent --resume --workspace ./my-project
```

## Session Storage

Sessions are stored in your home directory:
- **Location:** `~/.mini-agent/sessions/`
- **Format:** JSON files with timestamp or custom names
- **Contents:** Complete conversation history including system prompt

**Example session file:**
```json
{
  "id": "python-calculator-project",
  "timestamp": "2025-12-16T10:30:22.123456",
  "message_count": 15,
  "messages": [
    {
      "role": "system",
      "content": "You are Mini-Agent..."
    },
    {
      "role": "user",
      "content": "Create a calculator app"
    },
    ...
  ]
}
```

## Integration with Other Features

### Session Management + Pause/Interject
You can pause a long-running task, save the session, and resume later:

```
You: Create a comprehensive web application
Agent: 🤖 Working... (Press Ctrl+C to pause)

# Press Ctrl+C to pause
⏸️  Agent paused.
You: /save webapp-partial
✅ Saved session 'webapp-partial' as webapp-partial

# Later, resume the session
$ mini-agent --resume
🔄 Resuming last session: webapp-partial
✅ Loaded 12 messages from last session
```

### Session Management + Workspace
Combine with workspace for project-specific sessions:

```bash
# Work on project A
mini-agent --workspace ./project-a
/save project-a-setup

# Work on project B
mini-agent --workspace ./project-b
/save project-b-setup

# Resume project A later
mini-agent --workspace ./project-a --resume
```

## Best Practices

1. **Save After Milestones**: Save sessions after completing significant parts of a task
2. **Use Descriptive Names**: Name sessions clearly (e.g., "flask-api-v1" not "session1")
3. **Regular Cleanup**: Delete old sessions to free up disk space
4. **Project Organization**: Use workspace directories with matching session names

## Troubleshooting

### Session Not Found
```
❌ Session not found: my-session
```
**Solution**: Check available sessions with `/sessions` command

### Cannot Load Session
```
❌ Error loading session
```
**Possible causes**:
- Session file is corrupted
- Mini Agent version mismatch
- Session uses tools not available in current setup

**Solution**: Try loading a different session or check the session file in `~/.mini-agent/sessions/`

### Sessions Directory Not Found
Sessions are automatically created on first save. If you see an error:
```bash
mkdir -p ~/.mini-agent/sessions/
```

## Advanced Usage

### Session Archiving
Manually backup important sessions:
```bash
# Copy session to backup location
cp ~/.mini-agent/sessions/critical-project.json ~/backups/

# Restore from backup
cp ~/backups/critical-project.json ~/.mini-agent/sessions/
```

### Session Sharing
Share sessions with team members:
```bash
# Export session
cp ~/.mini-agent/sessions/shared-analysis.json ./

# Team member imports session
mkdir -p ~/.mini-agent/sessions/
cp shared-analysis.json ~/.mini-agent/sessions/
```

### Automated Session Saving
Future enhancement: Sessions can be auto-saved based on:
- Time intervals
- Message count
- Specific keywords in conversation
- Successful task completion

## API Reference

### SessionManager Class

```python
from mini_agent.session_manager import SessionManager

# Initialize
session_manager = SessionManager()

# Save session
session_id = session_manager.save_session(messages, name="my-session")

# Load session
messages = session_manager.load_session("my-session")

# List sessions
sessions = session_manager.list_sessions()

# Get last session
last_id = session_manager.get_last_session()

# Delete session
success = session_manager.delete_session("old-session")
```

## Summary

With session management, you can:
- ✅ Never lose important conversations
- ✅ Switch between multiple projects seamlessly
- ✅ Resume work exactly where you left off
- ✅ Maintain a history of all your work
- ✅ Organize sessions by project or task
- ✅ Combine with pause/interject for maximum flexibility

Sessions are the foundation for long-term productivity with Mini Agent!
