#!/usr/bin/env python3
"""
Hydrate and aggregate all session history for a workspace.

This script loads all session files for a workspace and aggregates them
into a single chronological conversation history.
"""

from pathlib import Path
from mini_agent.session_manager import SessionManager
from mini_agent.schema import Message


def hydrate_all_sessions(workspace_dir: str | Path) -> list[Message]:
    """Load and aggregate all sessions for a workspace.

    Args:
        workspace_dir: Path to the workspace directory

    Returns:
        List of all messages from all sessions, chronologically ordered
    """
    workspace_path = Path(workspace_dir)
    session_manager = SessionManager(workspace_dir=str(workspace_dir))

    print(f"🔍 Scanning sessions in: {workspace_path}/.agent-sessions")

    # Get all sessions for this workspace
    sessions = session_manager.list_sessions()
    workspace_sessions = [
        s for s in sessions
        if s.get('workspace') and Path(s['workspace']) == workspace_path
    ]

    print(f"📊 Found {len(workspace_sessions)} sessions for workspace")

    if not workspace_sessions:
        print("❌ No sessions found")
        return []

    # Sort by timestamp (oldest first for chronological order)
    workspace_sessions.sort(key=lambda s: s.get('timestamp', ''))

    all_messages = []
    total_loaded = 0

    print(f"\n📖 Loading sessions (oldest → newest):")
    for i, session in enumerate(workspace_sessions, 1):
        filename = session['filename'].replace('.json', '')
        messages = session_manager.load_session(filename)

        if not messages:
            continue

        # Skip the first system message (it's duplicated in each session)
        messages_to_add = messages[1:] if len(messages) > 1 else []

        session_msg_count = len(messages_to_add)
        all_messages.extend(messages_to_add)
        total_loaded += session_msg_count

        print(f"   {i}. {session['filename']}: {session_msg_count} messages")

    print(f"\n✅ Hydrated {total_loaded} messages from {len(workspace_sessions)} sessions")

    return all_messages


def save_hydrated_session(messages: list[Message], output_file: str | Path):
    """Save hydrated session to a JSON file.

    Args:
        messages: List of messages to save
        output_file: Path to output file
    """
    import json
    from datetime import datetime

    session_data = {
        "id": "hydrated_all_sessions",
        "timestamp": datetime.now().isoformat(),
        "workspace": "/adapt/platform/novaops",
        "message_count": len(messages),
        "messages": [msg.model_dump() for msg in messages]
    }

    output_path = Path(output_file)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(session_data, f, indent=2, ensure_ascii=False)

    print(f"💾 Saved hydrated session to: {output_path}")
    print(f"   File size: {output_path.stat().st_size / 1024:.2f} KB")


def print_message_summary(messages: list[Message]):
    """Print a summary of the hydrated messages."""
    if not messages:
        print("\n❌ No messages to display")
        return

    print(f"\n📋 Message Summary:")
    print(f"   Total messages: {len(messages)}")

    # Count by role
    from collections import Counter
    roles = Counter(msg.role for msg in messages)
    for role, count in roles.items():
        print(f"   - {role}: {count}")

    # Show first few messages
    print(f"\n📝 First 5 messages:")
    for i, msg in enumerate(messages[:5], 1):
        preview = msg.content[:100] if isinstance(msg.content, str) else str(msg.content)[:100]
        print(f"   {i}. [{msg.role}] {preview}...")

    # Show last few messages
    print(f"\n📝 Last 5 messages:")
    for i, msg in enumerate(messages[-5:], len(messages)-4):
        preview = msg.content[:100] if isinstance(msg.content, str) else str(msg.content)[:100]
        print(f"   {i}. [{msg.role}] {preview}...")


def main():
    """Main function to hydrate sessions."""
    import argparse

    parser = argparse.ArgumentParser(description="Hydrate all session history")
    parser.add_argument("--workspace", "-w", default="/adapt/platform/novaops",
                       help="Workspace directory")
    parser.add_argument("--output", "-o", default="/adapt/platform/novaops/.agent-sessions/hydrated_all.json",
                       help="Output file path")
    parser.add_argument("--dry-run", action="store_true",
                       help="List sessions without loading")

    args = parser.parse_args()

    if args.dry_run:
        # Just list sessions
        session_manager = SessionManager(workspace_dir=args.workspace)
        sessions = session_manager.list_sessions()
        workspace_sessions = [s for s in sessions if s.get('workspace') and Path(s['workspace']) == Path(args.workspace)]

        print(f"📊 Sessions for {args.workspace}:")
        for s in workspace_sessions:
            print(f"   {s['filename']}: {s['message_count']} messages ({s['timestamp'][:19]})")

        total_messages = sum(s['message_count'] for s in workspace_sessions)
        print(f"\n📈 Total messages across all sessions: {total_messages}")

    else:
        # Hydrate all sessions
        messages = hydrate_all_sessions(args.workspace)

        if messages:
            save_hydrated_session(messages, args.output)
            print_message_summary(messages)
        else:
            print("❌ No messages found to hydrate")


if __name__ == "__main__":
    main()
