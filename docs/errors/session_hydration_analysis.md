# Session Hydration Analysis & Fix

## Issue Identified

Session resume was not loading the full conversation history because:

1. **Wrong file being loaded**: The `load_workspace_session()` method was using session ID instead of filename, causing it to load `novaops.json` (2 messages) instead of `novaops_10.json` (3 messages) or other numbered sessions with more history.

2. **Session fragmentation**: Each numbered session (`novaops_1.json`, `novaops_2.json`, etc.) represents a separate conversation segment, not a continuous history.

## Sessions Found

```
/adapt/platform/novaops/.agent-sessions/
├── novaops.json       (2 messages) - Base session
├── novaops_1.json     (?? messages)
├── novaops_2.json     (90 messages)
├── novaops_3.json     (90 messages)
├── novaops_4.json     (92 messages)
├── novaops_5.json     (94 messages)
├── novaops_6.json     (91 messages)
├── novaops_7.json     (93 messages)
├── novaops_8.json     (95 messages)
├── novaops_9.json     (97 messages)
└── novaops_10.json    (3 messages) - Latest
```

## Fixes Applied

### Fix 1: cli.py - Removed invalid `messages` parameter
**File**: `/adapt/platform/novaops/frameworks/Minimax-Mini-Agent/mini_agent/cli.py`
```python
# Before (Line 547-565):
if initial_messages:
    agent = Agent(..., messages=initial_messages)  # ❌ Agent doesn't accept this
else:
    agent = Agent(...)

# After (Line 546-558):
agent = Agent(...)  # Create agent first
if initial_messages:
    agent.messages.extend(initial_messages[1:])  # ✅ Add messages after creation
```

### Fix 2: session_manager.py - Use filename instead of ID
**File**: `/adapt/platform/novaops/frameworks/Minimax-Mini-Agent/mini_agent/session_manager.py`
```python
# Before (Line 138):
return self.load_session(latest_session['id'])  # ❌ Loads wrong file

# After (Line 140):
# Use filename stem (without .json) to load correct file
# The ID in session data might not match the filename
return self.load_session(latest_session['filename'].replace('.json', ''))  # ✅
```

## How Session Resume Works Now

1. When you run `mini-agent --resume`, it loads the **most recent** numbered session for the workspace
2. Currently: Loads `novaops_10.json` (the latest)
3. Session files are created automatically based on the workspace name

## Hydrating ALL Sessions (Full History)

To see ALL conversation history across all sessions, you would need to aggregate sessions. Here's how:

```python
from mini_agent.session_manager import SessionManager
from pathlib import Path

workspace_dir = Path('/adapt/platform/novaops')
session_manager = SessionManager(workspace_dir=str(workspace_dir))

# Load all workspace sessions (from newest to oldest)
sessions = session_manager.list_sessions()
workspace_sessions = [
    s for s in sessions
    if s.get('workspace') and Path(s['workspace']) == workspace_dir
]

print(f"Found {len(workspace_sessions)} sessions")

# Aggregate all messages from all sessions
all_messages = []
for session in reversed(workspace_sessions):  # Oldest first for chronological order
    filename = session['filename'].replace('.json', '')
    messages = session_manager.load_session(filename)
    if messages:
        # Skip the first system message (duplicate in each session)
        all_messages.extend(messages[1:])
        print(f"Added {len(messages)-1} messages from {session['filename']}")

print(f"\nTotal aggregated: {len(all_messages)} messages")
```

## Usage

### Resume latest session:
```bash
mini-agent --resume                    # Resume in current directory
mini-agent --resume -w /path/to/dir    # Resume specific workspace
mini-agent -r                          # Short form
```

### View all sessions:
```bash
# In the agent CLI, use:
/sessions
```

### Load specific session:
```bash
# In the agent CLI:
/load novaops_9
```

## Notes

- Each numbered session represents a separate conversation
- Sessions auto-save based on workspace directory
- The `--resume` flag always loads the **most recent** session
- For full history across sessions, you need to manually aggregate
- Session files are in `/adapt/platform/novaops/.agent-sessions/`
