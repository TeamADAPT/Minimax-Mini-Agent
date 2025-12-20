# A2A Communications & Self-Modification Workflow

## Overview

Mini Agent now supports:
- **A2A (Agent-to-Agent) Communication** - Agents can talk to each other
- **Self-Modification Workflow** - Agents can propose changes to their own code
- **Approval System** - All modifications require human approval
- **Audit Trail** - Complete logging of all proposed and applied changes

## Architecture

```
┌─────────────────┐     A2A Message      ┌──────────────────┐
│ Agent A         │ ────────────────────> │ Agent B (Human)  │
│ (Proposes       │      Request          │ Admin/Reviewer)  │
│  Modification)  │                       │                  │
└─────────────────┘                       └──────────────────┘
         ▲                                        │
         │                                        ▼
         │                               ┌──────────────────┐
         │                               │ Review & Decide  │
         │                               └──────────────────┘
         │                                        │
         │                                        ▼
         │                               ┌──────────────────┐
         │                               │ Approve/Reject   │
         │                               └──────────────────┘
         │                                        │
         │                                        ▼
         │   A2A Response     ┌──────────────────┐
         │ ──────────────────── │ Agent A         │
         │                      │ (Applies if     │
         │                      │  approved)      │
         ▼                      └──────────────────┘
┌─────────────────┐
│ Log & Audit     │
│ All Changes     │
└─────────────────┘
```

## Files Created

1. **`mini_agent/a2a_comms.py`** - A2A communication infrastructure
2. **`self_modification_workflow.py`** - Self-modification workflow demo
3. **`mini_agent/rules_loader.py`** - Enhanced with portable paths
4. **`mini_agent/config/TeamADAPT_Rules.md`** - Copied for portability

## A2A Communication

### Core Components

```python
from mini_agent.a2a_comms import A2AComms, A2AMessage

# Initialize comms
a2a = A2AComms("development_agent_001")

# Send message to another agent
msg_id = a2a.send_message(
    recipient_id="human_admin",
    message_type="self_modification_request",
    content={
        "file_path": "mini_agent/cli.py",
        "changes": {...},
        "reasoning": "Improve error handling"
    }
)

# Receive messages
messages = await a2a.receive_messages()
for msg in messages:
    if msg.message_type == "approval_response":
        if msg.content.get("approved"):
            # Apply changes
            pass
```

### Message Types

1. **`self_modification_request`** - Agent proposes changes to its own code
2. **`approval_request`** - Request approval from admin/reviewer
3. **`approval_response`** - Approval/rejection with feedback
4. **`modification_complete`** - Notification that changes were applied
5. **`modification_rejected`** - Modification was rejected

All messages are:
- **Persistent** - Stored to disk (JSONL format)
- **Tracked** - Correlation IDs link request/response
- **Acknowledged** - Receipt tracking
- **Logged** - Complete audit trail

## Self-Modification Workflow

### How It Works

1. **Agent Proposes Change**
   ```python
   from self_modification_workflow import SelfModificationWorkflow

   workflow = SelfModificationWorkflow("agent_001")

   modification_id = await workflow.propose_modification(
       file_path="mini_agent/cli.py",
       changes={
           "type": "insert",
           "position": "end",
           "new_text": "print('Debug: Agent started')"
       },
       reasoning="Add debug output for troubleshooting",
       context={"priority": "low"}
   )
   ```

2. **A2A Sends Approval Request**
   - Message sent to `human_admin` (or designated reviewer)
   - Request includes:
     - File path to modify
     - Exact changes (diff format)
     - Reasoning/explanation
     - Context and metadata
     - Modification ID

3. **Human Reviews Changes**
   - Reviewer sees:
     ```
     Modification Request: mod_20251216_143022_1234
     Agent: agent_001
     File: mini_agent/cli.py

     Proposed Changes:
     + print('Debug: Agent started')

     Reasoning: Add debug output for troubleshooting

     Approve? (y/n):
     ```

4. **Human Approves or Rejects**
   - If approved: Agent applies changes automatically
   - If rejected: Agent receives feedback, can revise and retry
   - All decisions logged with timestamps

5. **Changes Applied (if approved)**
   - Agent receives approval via A2A
   - Modifies its own code
   - Sends completion notification
   - Updates audit log

6. **Audit Trail Created**
   - All proposed changes stored
   - All decisions logged
   - Who approved/rejected tracked
   - When it happened recorded

### File Structure

```
~/.mini-agent/self_modifications/
├── pending.jsonl      # Modifications awaiting approval
├── approved.jsonl     # Approved and applied modifications
├── rejected.jsonl     # Rejected modifications
└── audit.log          # Detailed audit trail
```

## Usage Examples

### Example 1: Agent Proposes Code Improvement

```python
from self_modification_workflow import SelfModificationWorkflow

async def improve_error_handling():
    workflow = SelfModificationWorkflow("cli_agent")

    # Agent proposes to add better error handling
    mod_id = await workflow.propose_modification(
        file_path="mini_agent/cli.py",
        changes={
            "type": "replace",
            "old_text": """            except Exception as e:
                print(f"\\n{Colors.RED}❌ Error: {e}{Colors.RESET}")""",
            "new_text": """            except Exception as e:
                print(f"\\n{Colors.RED}❌ Error: {e}{Colors.RESET}")
                import traceback
                traceback.print_exc()
                print(f"{Colors.DIM}Use /debug for detailed diagnostics{Colors.RESET}")"""",
        },
        reasoning="Add detailed error reporting and debugging hints for better user experience",
        context={"priority": "medium", "user_impact": "high"}
    )

    print(f"Proposed modification: {mod_id}")
    print("Awaiting human approval via /review-modifications")
```

### Example 2: Human Reviews Pending Modifications

```python
async def review_pending():
    workflow = SelfModificationWorkflow("reviewer")

    await workflow.review_modifications()
    # Interactive prompt shows each pending modification
    # Human approves or rejects each one
```

### Example 3: Agent Adds New Feature

```python
async def add_feature():
    workflow = SelfModificationWorkflow("feature_agent")

    # Agent proposes adding a new command
    mod_id = await workflow.propose_modification(
        file_path="mini_agent/cli.py",
        changes={
            "type": "insert",
            "position": "before",
            "anchor_text": "elif command == \"/stats":",
            "new_text": """                elif command == "/debug":
                    print(f"\\n{Colors.BRIGHT_CYAN}Debug Info:{Colors.RESET}")
                    print(f"  Messages: {len(agent.messages)}")
                    print(f"  Tools: {len(agent.tools)}")
                    print(f"  Workspace: {workspace_dir}")
                    continue
"""",
        },
        reasoning="Add /debug command to help users diagnose agent state",
        context={"feature_type": "diagnostic_command", "backward_compatible": True}
    )
```

## Security Considerations

### Access Control

- **Admin Approval Required** - All modifications require human approval
- **Audit Trail** - Complete log of all proposed and applied changes
- **File Scope** - Can restrict which files can be modified
- **Change Validation** - Validates changes before applying

### Restrictions

```python
# Example: Restrict which files can be modified
ALLOWED_FILES = [
    "mini_agent/cli.py",
    "mini_agent/config.py",
    "examples/*.py",
]

BLOCKED_FILES = [
    "mini_agent/__init__.py",
    "pyproject.toml",
    "setup.py",
]
```

### Review Requirements

- **Two-person rule** for critical files
- **Tests must pass** before approval
- **Backup** automatically created
- **Revert capability** built-in

## Monitoring and Alerts

### Notification Setup

```python
# Send notifications for modification requests
import subprocess

def notify_admin(modification_id: str, file_path: str):
    """Notify admin of pending modification."""
    message = f"Agent requesting self-modification: {file_path}"

    # Slack notification
    subprocess.run([
        "slack-notify", "-m", message, "-c", "#agent-approvals"
    ])

    # Or email
    subprocess.run([
        "mail", "-s", f"Agent Modification Request: {modification_id}",
        "admin@teamadapt.ai"
    ])
```

### Dashboard

Create a simple dashboard:

```python
# Import this in your agent
@app.route("/modifications")
def modification_dashboard():
    """Show pending modifications."""
    workflow = SelfModificationWorkflow("dashboard")
    pending = workflow._load_pending_modifications()

    return {
        "pending_count": len(pending),
        "pending": pending,
        "approved_count": len(workflow._load_approved_modifications()),
    }
```

## Testing Self-Modifications

### Pre-Approval Testing

```python
async def test_modification(modification_id: str):
    """Test a modification before approval."""
    # Create test environment
    # Apply changes to a test branch
    # Run tests
    # Report results
    pass
```

### Post-Approval Verification

```python
async def verify_modification(modification_id: str):
    """Verify a modification was applied correctly."""
    # Check file was modified
    # Verify syntax is valid
    # Run affected tests
    # Check agent still works
    pass
```

## Best Practices

### For Agents

1. **Explain Why** - Always provide clear reasoning
2. **Show Impact** - Explain user-facing benefits
3. **Test First** - Test changes locally if possible
4. **Small Changes** - Propose incremental improvements
5. **Document** - Add comments explaining changes

### For Reviewers

1. **Understand Impact** - How does this affect users?
2. **Check Security** - Any security implications?
3. **Test Coverage** - Are tests updated/added?
4. **Documentation** - Is it documented?
5. **Backup** - Can we revert if needed?

## Integration with Mini Agent

### Modify CLI to Support Self-Modification

```python
# Add to mini_agent/cli.py

elif command == "/modify-self":
    # Agent requests to modify its own code
    workflow = SelfModificationWorkflow(session_id)

    # Parse modification request from user input
    mod_request = parse_modification_command(user_input)

    mod_id = await workflow.propose_modification(**mod_request)
    print(f"Modification proposed: {mod_id}")
    print("Use /review-modifications to approve/reject")

elif command == "/review-modifications":
    workflow = SelfModificationWorkflow("cli")
    await workflow.review_modifications()
```

### Add Self-Modification Tools

```python
# In mini_agent/tools/self_modification_tool.py

class SelfModificationTool:
    """Tool allowing agents to propose self-modifications."""

    @tool
    async def propose_self_modification(
        self,
        file_path: str,
        changes: dict,
        reasoning: str,
    ) -> str:
        """Propose a modification to agent's own code."""
        workflow = SelfModificationWorkflow(get_current_agent_id())

        mod_id = await workflow.propose_modification(
            file_path, changes, reasoning
        )

        return f"Modification proposed: {mod_id}. Awaiting human approval."
```

## Command Reference

### For Agents

```python
# Propose modification
workflow.propose_modification(...)

# Check status
workflow.get_modification_status(mod_id)

# Revoke proposal
workflow.revoke_modification(mod_id)
```

### For Humans

```bash
# Review pending modifications
mini-agent
You: /review-modifications

# List all modifications
You: /list-modifications

# Get details
You: /show-modification <id>
```

## Future Enhancements

1. **Multi-Agent Consensus** - Multiple agents review before approval
2. **Automated Testing** - Auto-run tests on proposed changes
3. **Rollbacks** - One-click rollback of applied changes
4. **Version Control** - Automatic git branches for modifications
5. **Metrics** - Track which modifications improve performance

## Summary

✅ **A2A Communication** - Agents can send/receive messages
✅ **Self-Modification** - Agents can propose code changes
✅ **Approval Workflow** - All changes require human approval
✅ **Audit Trail** - Complete logging of all actions
✅ **Portable** - Works with the portable deployment model
✅ **Secure** - Safety checks and validation built-in

**Your agents are now collaborative, self-improving, and safely controlled!** 🚀
