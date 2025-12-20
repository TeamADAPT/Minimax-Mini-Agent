# 🔄 Auto-Save & Workspace-Based Sessions

## Overview

Mini Agent now features **automatic session management** with workspace-aware saving, loading, and naming. No need to manually save your sessions anymore!

## ✨ Features

### 1. **Auto-Save After Every Message**
- Sessions automatically saved when you press Enter
- No `/save` command needed
- Pick up exactly where you left off

### 2. **Workspace-Based Session Naming**
- Session names based on directory path
- Example: `/home/user/projects/myapp` → `projects-myapp`
- Different directories = different sessions

### 3. **Auto-Resume by Directory**
- Run `mini-agent` in a directory → auto-resumes that session
- No `--resume` flag needed
- Seamless context switching between projects

### 4. **Sessions Stored in Workspace**
- Sessions saved in `workspace/.agent-sessions/`
- Sessions travel with your project directory
- Easy to backup, share, or move

## 🚀 Usage

### Basic Usage (Automatic)

```bash
# Navigate to your project
cd /path/to/your/project

# Start mini-agent - automatically resumes this directory's session
mini-agent

# You'll see:
🔍 Looking for saved session in workspace: /path/to/your/project
✅ Auto-resumed workspace session with 23 messages
💾 Auto-saved session: project-name
```

### Multiple Projects

```bash
# Work on Project A
cd ~/projects/project-a
mini-agent
# Works on session 'project-a', auto-saves everything

# Switch to Project B
cd ~/projects/project-b
mini-agent
# Works on different session 'project-b', completely separate

# Back to Project A
cd ~/projects/project-a
mini-agent
# Resumes exactly where you left off in Project A!
```

## 💾 Storage Structure

```
~/projects/myapp/                    # Your project directory
├── .agent-sessions/                 # Session storage
│   ├── myapp.json                   # Session file (auto-named)
│   ├── myapp_1.json                 # If multiple sessions in same dir
│   └── myapp_feature-x.json         # Manual save with custom name
├── src/
├── tests/
└── ...
```

## 🎯 How It Works

### Session Naming

| Directory | Session Name | Example File |
|-----------|--------------|--------------|
| `/home/user/projects/myapp` | `projects-myapp` | `projects-myapp.json` |
| `/home/user/work/docs` | `work-docs` | `work-docs.json` |
| `/tmp/experiment` | `experiment` | `experiment.json` |

### Auto-Save Triggers

Sessions are auto-saved when:
1. You send a message (press Enter)
2. After agent completes its response
3. Before running any tool
4. Even if you use `/pause` or change direction

## 🎮 Advanced Usage

### Manual Save (Still Available)

Even with auto-save, you can still manually save:

```
You: /save feature-login
✅ Saved session 'feature-login' as feature-login
```

This creates a snapshot you can return to:

```
You: /sessions
  1. projects-myapp              (auto-saved)
  2. projects-myapp_1            (auto-saved)
  3. feature-login               (manual save)

You: /load feature-login
✅ Loaded feature-login with 15 messages
```

### List Sessions

```
You: /sessions
  1. projects-myapp
     Messages: 42
     Saved: 2025-12-16 14:30:22

  2. work-docs
     Messages: 8
     Saved: 2025-12-16 13:15:10
```

### Move Sessions with Project

```bash
# Copy project with all sessions
cp -r ~/projects/myapp /backup/myapp

# Sessions preserved in .agent-sessions/ directory

# On new machine
cd /backup/myapp
mini-agent
✅ Auto-resumed workspace session with 42 messages
```

## ⌨️ Interrupt Keys (Pause/Interject)

| Key Combination | Action | When to Use |
|-----------------|--------|-------------|
| **Ctrl+C** (once) | Pause agent execution | Agent is working, you want to change direction |
| **Ctrl+C** (twice) | Force exit | Agent is stuck or you need to stop immediately |
| **/pause** | Pause via command | Same as single Ctrl+C |
| **/continue** | Resume execution | After pausing, want to continue original task |

### Example Pause/Interject Flow

```
You: Create a Flask web application
Agent: 🤖 Working... (Press Ctrl+C to pause)

# Oops, changed my mind!
[Press Ctrl+C once]

⏸️  Agent execution paused.
   Options:
   - Type /continue to resume execution
   - Type a new message to interject and change direction
   - Press Ctrl+C again to force exit

You: Actually, create it with FastAPI instead of Flask
Agent: 🤖 Adjusting task... (Press Ctrl+C to pause)

# Continues with new instructions...
```

## 📁 Storage Locations

### Automatic Location (Workspace-Based)
- **Location**: `workspace/.agent-sessions/`
- **Naming**: Based on directory path
- **Auto-load**: ✅ Yes

### Global Location (Fallback)
- **Location**: `~/.mini-agent/sessions/`
- **Naming**: Timestamp or custom
- **Auto-load**: Only with `--resume` flag

## 🔧 Configuration

### Environment Variable (Optional)

```bash
export MINI_AGENT_SESSIONS_DIR="/path/to/custom/sessions"
mini-agent
```

### Per-Project Override

```bash
# Use different session storage for this run
mini-agent --workspace ./project --session-dir ./.my-sessions
```

## 🚫 Disabling Auto-Save

If you need to disable auto-save:

```python
# In code
session_manager = SessionManager(auto_save=False)
```

Or via environment variable:
```bash
export MINI_AGENT_AUTO_SAVE=false
mini-agent
```

## 🐛 Troubleshooting

### Session Not Found

```bash
# Look for sessions manually
ls -la .agent-sessions/

# Check if session is in global location
ls -la ~/.mini-agent/sessions/
```

### Wrong Session Loaded

```bash
# Clear all sessions for current directory
rm -rf .agent-sessions/

# Or manually load a different session
mini-agent
You: /load projects-otherapp
```

### Session File Corrupted

```bash
# Delete corrupted session
rm .agent-sessions/bad-session.json

# Next run will start fresh
mini-agent
```

## 🎊 Summary

✅ **Auto-save**: Every message automatically persisted
✅ **Auto-resume**: Start where you left off automatically
✅ **Workspace-aware**: Different dirs = different sessions
✅ **Contextual naming**: Sessions named by directory path
✅ **Stored locally**: Sessions in workspace/.agent-sessions/
✅ **Pause/Interject**: Ctrl+C to pause, change direction
✅ **No manual work**: Never need to /save or remember --resume

**Just run `mini-agent` in any directory and continue your work seamlessly!** 🚀
