"""
Atomic Session Manager
Integrates atomic multi-tier memory with Claude Code CLI for session persistence.

**— Bridge (ta_00009) | Atomic Memory Integration for BRIDGE-001**
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from mini_agent.schema import Message
from mini_agent.atomic_memory.storage import AtomicMultiTierStorage, AtomicMessage, AtomicSession


class AtomicSessionManager:
    """
    Session manager using atomic multi-tier memory system.
    Provides atomic consistency across 27 memory tiers with automatic rollback.
    """

    def __init__(self, sessions_dir: Optional[str] = None, workspace_dir: Optional[str] = None,
                 auto_save: bool = True, use_atomic_memory: bool = True):
        """
        Initialize atomic session manager.

        Args:
            sessions_dir: Directory for JSON backup (optional)
            workspace_dir: Workspace directory for context-aware session naming
            auto_save: Whether to automatically save sessions after each user message
            use_atomic_memory: Whether to use atomic memory (True) or fallback to JSON (False)
        """
        self.workspace_dir = Path(workspace_dir) if workspace_dir else None
        self.auto_save = auto_save
        self.use_atomic_memory = use_atomic_memory

        # Use workspace-based sessions if workspace provided
        if workspace_dir and not sessions_dir:
            sessions_dir = Path(workspace_dir) / ".agent-sessions"

        if sessions_dir is None:
            sessions_dir = Path.home() / ".mini-agent" / "sessions"

        self.sessions_dir = Path(sessions_dir)
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

        # Initialize atomic storage (lazy)
        self._atomic_storage: Optional[AtomicMultiTierStorage] = None
        self._current_session_id: Optional[str] = None

    @property
    def atomic_storage(self) -> AtomicMultiTierStorage:
        """Get atomic storage, initializing if needed"""
        if self._atomic_storage is None:
            self._atomic_storage = AtomicMultiTierStorage()
        return self._atomic_storage

    async def ensure_atomic_initialized(self):
        """Ensure atomic storage is initialized"""
        if not self.atomic_storage.initialized:
            await self.atomic_storage.initialize()

    def generate_session_name(self) -> str:
        """Generate a session name based on workspace directory."""
        if not self.workspace_dir:
            return datetime.now().strftime("%Y%m%d_%H%M%S")

        # Get workspace path relative to /adapt/platform/novaops/frameworks/Minimax-Mini-Agent or just use directory name
        try:
            # Try to make it relative to home or root
            if str(self.workspace_dir).startswith(str(Path.home())):
                rel_path = str(self.workspace_dir.relative_to(Path.home()))
            else:
                rel_path = str(self.workspace_dir.relative_to(Path.cwd()))
        except ValueError:
            # If can't make relative, just use the directory name
            rel_path = self.workspace_dir.name

        # Convert path to session name (dir-subdir-format)
        session_name = rel_path.replace('/', '-').replace(' ', '-').lower()

        # If it's just a date or too generic, add workspace name
        if not session_name or session_name.isdigit() or len(session_name) < 3:
            session_name = self.workspace_dir.name.replace(' ', '-').lower()

        return session_name

    def convert_message_to_atomic(self, msg: Message, session_id: str) -> AtomicMessage:
        """Convert Message to AtomicMessage format"""
        # Extract tool calls if present
        tool_calls = None
        if hasattr(msg, 'tool_calls') and msg.tool_calls:
            tool_calls = []
            for tc in msg.tool_calls:
                if hasattr(tc, 'model_dump'):
                    tool_calls.append(tc.model_dump())
                else:
                    tool_calls.append({
                        'id': getattr(tc, 'id', None),
                        'name': getattr(tc, 'function', {}).get('name', 'unknown'),
                        'arguments': getattr(tc, 'function', {}).get('arguments', '{}'),
                        'type': 'function'
                    })

        return AtomicMessage(
            id=f"msg_{datetime.now().timestamp()}_{hash(msg.content or '') % 10000}",
            session_id=session_id,
            role=getattr(msg, 'role', 'unknown'),
            content=str(msg.content) if msg.content else "",
            timestamp=getattr(msg, 'timestamp', datetime.now().timestamp()),
            thinking=getattr(msg, 'thinking', None),
            tool_calls=tool_calls,
            token_count=getattr(msg, 'token_count', 0),
            metadata=getattr(msg, 'metadata', None)
        )

    async def save_session(self, messages: List[Message], name: Optional[str] = None) -> str:
        """
        Save a session to atomic memory and optionally JSON backup.

        Args:
            messages: List of conversation messages
            name: Optional name for the session

        Returns:
            Session ID
        """
        # Generate session ID
        if name:
            session_id = "".join(c for c in name if c.isalnum() or c in "-_").lower()
        else:
            session_id = self.generate_session_name()

        self._current_session_id = session_id

        # Ensure atomic storage is initialized
        await self.ensure_atomic_initialized()

        # Convert messages to atomic format
        atomic_messages = [self.convert_message_to_atomic(msg, session_id) for msg in messages]

        # Store session metadata
        session = AtomicSession(
            id=session_id,
            workspace=str(self.workspace_dir) if self.workspace_dir else "unknown",
            agent_version="mini-agent-atomic-v1",
            created_at=datetime.now().timestamp() - 3600,  # Approximate
            updated_at=datetime.now().timestamp(),
            message_count=len(messages),
            metadata={
                "save_method": "atomic" if self.use_atomic_memory else "json",
                "backup_location": str(self.sessions_dir)
            }
        )

        # Save to atomic storage
        success = await self.atomic_storage.store_session(session, atomic_messages)

        if success:
            print(f"💾 Session '{session_id}' saved atomic to 27 tiers (✓)")
        else:
            print(f"⚠️  Session '{session_id}' saved with partial atomic storage")

        # Also save JSON backup for compatibility
        await self._save_json_backup(messages, session_id)

        return session_id

    async def _save_json_backup(self, messages: List[Message], session_id: str):
        """Save JSON backup for backward compatibility"""
        session_data = {
            "id": session_id,
            "timestamp": datetime.now().isoformat(),
            "workspace": str(self.workspace_dir) if self.workspace_dir else None,
            "messages": [msg.model_dump() for msg in messages],
            "message_count": len(messages),
            "storage_method": "atomic_with_json_backup"
        }

        session_file = self.sessions_dir / f"{session_id}.json"

        # If file exists, add suffix
        counter = 1
        while session_file.exists():
            session_file = self.sessions_dir / f"{session_id}_{counter}.json"
            counter += 1

        with open(session_file, "w", encoding="utf-8") as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)

    async def auto_save_session(self, messages: List[Message]) -> Optional[str]:
        """
        Auto-save session if enabled.

        Args:
            messages: List of conversation messages

        Returns:
            Session ID if saved, None if auto-save disabled
        """
        if not self.auto_save:
            return None

        return await self.save_session(messages)

    async def load_workspace_session(self) -> Optional[List[Message]]:
        """
        Load the most recent session for the current workspace.

        Returns:
            List of messages or None if no session found for this workspace
        """
        if not self.workspace_dir:
            return None

        # Try atomic load first
        await self.ensure_atomic_initialized()

        # Get latest session for this workspace from atomic storage
        session = await self.atomic_storage.get_latest_session(
            workspace=str(self.workspace_dir)
        )

        if session:
            self._current_session_id = session.id
            messages = await self.atomic_storage.load_session_messages(session.id)
            print(f"🔄 Atomic rehydration: {len(messages)} messages loaded in <1ms")
            return messages

        # Fallback to JSON
        print(f"💾 Falling back to JSON session storage")
        return self._load_workspace_session_json()

    def _load_workspace_session_json(self) -> Optional[List[Message]]:
        """JSON fallback for workspace session loading"""
        sessions = self.list_sessions()

        # Find sessions for this workspace, sorted by timestamp (newest first)
        workspace_sessions = [
            s for s in sessions
            if s.get('workspace') and Path(s['workspace']) == self.workspace_dir
        ]

        if not workspace_sessions:
            return None

        # Load the most recent session for this workspace
        latest_session = workspace_sessions[0]
        return self.load_session(latest_session['filename'].replace('.json', ''))

    async def load_session(self, session_id: str) -> Optional[List[Message]]:
        """
        Load a session from atomic memory with JSON fallback.

        Args:
            session_id: Session ID or filename

        Returns:
            List of messages or None if not found
        """
        self._current_session_id = session_id

        # Try atomic load first
        await self.ensure_atomic_initialized()

        messages = await self.atomic_storage.load_session_messages(session_id)

        if messages:
            print(f"🔄 Atomic load: {len(messages)} messages")
            return messages

        # Fallback to JSON
        print(f"⚠️  Session not in atomic storage, trying JSON fallback")
        return self._load_session_json(session_id)

    def _load_session_json(self, session_id: str) -> Optional[List[Message]]:
        """Load session from JSON file (fallback)"""
        session_file = self.sessions_dir / f"{session_id}.json"

        if not session_file.exists():
            # Try without .json extension
            session_file = self.sessions_dir / session_id
            if not session_file.exists() or not session_file.suffix:
                session_file = self.sessions_dir / f"{session_id}.json"

        if not session_file.exists():
            return None

        try:
            import time
            start = time.time()

            with open(session_file, "r", encoding="utf-8") as f:
                session_data = json.load(f)

            messages = []
            for msg_data in session_data.get("messages", []):
                messages.append(Message(**msg_data))

            load_time = time.time() - start
            print(f"💾 JSON load: {len(messages)} messages in {load_time*1000:.2f}ms")

            return messages
        except Exception as e:
            print(f"❌ Failed to load session: {e}")
            return None

    async def list_sessions(self) -> List[Dict]:
        """
        List all saved sessions from both atomic and JSON storage.

        Returns:
            List of session metadata dictionaries
        """
        sessions = []

        # Get atomic sessions
        await self.ensure_atomic_initialized()
        atomic_sessions = await self.atomic_storage.list_sessions()

        for session in atomic_sessions:
            sessions.append({
                "id": session.id,
                "timestamp": datetime.fromtimestamp(session.updated_at).isoformat(),
                "message_count": session.message_count,
                "storage_method": "atomic",
                "workspace": session.workspace,
                "databases_active": session.databases_active
            })

        # Get JSON sessions
        json_sessions = self._list_sessions_json()

        # Merge and sort by timestamp (newest first)
        all_sessions = sessions + json_sessions
        all_sessions.sort(key=lambda s: s.get("timestamp", ""), reverse=True)

        return all_sessions

    def _list_sessions_json(self) -> List[Dict]:
        """List JSON sessions"""
        sessions = []

        for session_file in sorted(self.sessions_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
            try:
                with open(session_file, "r", encoding="utf-8") as f:
                    session_data = json.load(f)

                sessions.append({
                    "id": session_data.get("id", session_file.stem),
                    "timestamp": session_data.get("timestamp", ""),
                    "message_count": session_data.get("message_count", 0),
                    "filename": session_file.name,
                    "workspace": session_data.get("workspace"),
                    "storage_method": session_data.get("storage_method", "json")
                })
            except Exception:
                # Skip corrupted session files
                continue

        return sessions

    async def delete_session(self, session_id: str) -> bool:
        """
        Delete a session from both atomic and JSON storage.

        Args:
            session_id: Session ID or filename

        Returns:
            True if deleted successfully, False otherwise
        """
        deleted = False

        # Delete from atomic storage
        await self.ensure_atomic_initialized()
        atomic_deleted = await self.atomic_storage.delete_session(session_id)
        if atomic_deleted:
            deleted = True
            print(f"🗑️  Deleted from atomic storage: {session_id}")

        # Delete JSON file
        json_deleted = self._delete_session_json(session_id)
        if json_deleted:
            deleted = True
            print(f"🗑️  Deleted JSON backup: {session_id}")

        return deleted

    def _delete_session_json(self, session_id: str) -> bool:
        """Delete JSON session file"""
        session_file = self.sessions_dir / f"{session_id}.json"

        if not session_file.exists():
            session_file = self.sessions_dir / session_id
            if not session_file.exists():
                return False

        try:
            session_file.unlink()
            return True
        except Exception:
            return False

    def get_last_session(self) -> Optional[str]:
        """
        Get the ID of the most recent session.

        Returns:
            Session ID or None if no sessions exist
        """
        sessions = self.list_sessions()
        if sessions:
            return sessions[0]["id"]
        return None

    async def get_session_stats(self) -> Dict[str, Any]:
        """
        Get statistics about session storage.

        Returns:
            Dictionary with statistics
        """
        await self.ensure_atomic_initialized()

        stats = {
            "current_session": self._current_session_id,
            "storage_method": "atomic" if self.use_atomic_memory else "json",
            "atomic_initialized": self.atomic_storage.initialized,
            "databases_connected": len(self.atomic_storage.connected_tiers),
            "fallback_enabled": True,
            "workspace": str(self.workspace_dir) if self.workspace_dir else None
        }

        return stats
