"""Session management for conversation history persistence and resuming."""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from .schema import Message


class SessionManager:
    """Manages session persistence, loading, and resuming."""

    def __init__(self, sessions_dir: Optional[str] = None, workspace_dir: Optional[str] = None, auto_save: bool = True):
        """Initialize session manager.

        Args:
            sessions_dir: Directory to store session files. If None, uses workspace-based storage
            workspace_dir: Workspace directory for context-aware session naming
            auto_save: Whether to automatically save sessions after each user message
        """
        self.workspace_dir = Path(workspace_dir) if workspace_dir else None
        self.auto_save = auto_save

        # Use workspace-based sessions if workspace provided
        if workspace_dir and not sessions_dir:
            sessions_dir = Path(workspace_dir) / ".agent-sessions"

        if sessions_dir is None:
            sessions_dir = Path.home() / ".mini-agent" / "sessions"

        self.sessions_dir = Path(sessions_dir)
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

    def generate_session_name(self) -> str:
        """Generate a session name based on workspace directory.

        Returns:
            Session ID in format: dir-subdir (relative to /adapt/platform/novaops/frameworks/Minimax-Mini-Agent)
        """
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

    def save_session(self, messages: List[Message], name: Optional[str] = None) -> str:
        """Save a session to disk.

        Args:
            messages: List of conversation messages
            name: Optional name for the session. If not provided, uses workspace-based naming.

        Returns:
            Session ID (filename without extension)
        """
        # Generate session ID
        if name:
            # Sanitize name for filesystem
            session_id = "".join(c for c in name if c.isalnum() or c in "-_").lower()
        else:
            session_id = self.generate_session_name()

        session_data = {
            "id": session_id,
            "timestamp": datetime.now().isoformat(),
            "workspace": str(self.workspace_dir) if self.workspace_dir else None,
            "messages": [msg.model_dump() for msg in messages],
            "message_count": len(messages),
        }

        session_file = self.sessions_dir / f"{session_id}.json"

        # If file exists, add suffix
        counter = 1
        while session_file.exists():
            session_file = self.sessions_dir / f"{session_id}_{counter}.json"
            counter += 1

        with open(session_file, "w", encoding="utf-8") as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)

        return session_file.stem

    def auto_save_session(self, messages: List[Message]) -> Optional[str]:
        """Auto-save session if enabled.

        Args:
            messages: List of conversation messages

        Returns:
            Session ID if saved, None if auto-save disabled
        """
        if not self.auto_save:
            return None

        return self.save_session(messages)

    def load_workspace_session(self) -> Optional[List[Message]]:
        """Load the most recent session for the current workspace.

        Returns:
            List of messages or None if no session found for this workspace
        """
        if not self.workspace_dir:
            return None

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
        # Use filename stem (without .json) to load the correct file
        # The ID in session data might not match the filename (e.g., novaops_10.json has ID "novaops")
        return self.load_session(latest_session['filename'].replace('.json', ''))

    def load_session(self, session_id: str) -> Optional[List[Message]]:
        """Load a session from disk.

        Args:
            session_id: Session ID or filename

        Returns:
            List of messages or None if not found
        """
        session_file = self.sessions_dir / f"{session_id}.json"

        if not session_file.exists():
            # Try without .json extension
            session_file = self.sessions_dir / session_id
            if not session_file.exists() or not session_file.suffix:
                session_file = self.sessions_dir / f"{session_id}.json"

        if not session_file.exists():
            return None

        try:
            with open(session_file, "r", encoding="utf-8") as f:
                session_data = json.load(f)

            messages = []
            for msg_data in session_data.get("messages", []):
                messages.append(Message(**msg_data))

            return messages
        except Exception:
            return None

    def list_sessions(self) -> List[Dict]:
        """List all saved sessions.

        Returns:
            List of session metadata dictionaries
        """
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
                })
            except Exception:
                # Skip corrupted session files
                continue

        return sessions

    def delete_session(self, session_id: str) -> bool:
        """Delete a session file.

        Args:
            session_id: Session ID or filename

        Returns:
            True if deleted successfully, False otherwise
        """
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
        """Get the ID of the most recent session.

        Returns:
            Session ID or None if no sessions exist
        """
        sessions = self.list_sessions()
        if sessions:
            return sessions[0]["id"]
        return None
