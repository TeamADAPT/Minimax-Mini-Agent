"""A2A (Agent-to-Agent) Communication Module

Enables agents to communicate with each other through:
- Message passing
- Event broadcasting
- Shared state management
- Self-modification coordination
"""

import asyncio
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable


class A2AMessage:
    """Represents a message between agents."""

    def __init__(
        self,
        sender_id: str,
        recipient_id: str,
        message_type: str,
        content: Dict[str, Any],
        correlation_id: Optional[str] = None,
    ):
        self.id = str(uuid.uuid4())
        self.sender_id = sender_id
        self.recipient_id = recipient_id
        self.message_type = message_type  # e.g., "self_modification_request", "approval_request", etc.
        self.content = content
        self.correlation_id = correlation_id or self.id
        self.timestamp = datetime.now().isoformat()
        self.acknowledged = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary."""
        return {
            "id": self.id,
            "sender_id": self.sender_id,
            "recipient_id": self.recipient_id,
            "message_type": self.message_type,
            "content": self.content,
            "correlation_id": self.correlation_id,
            "timestamp": self.timestamp,
            "acknowledged": self.acknowledged,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "A2AMessage":
        """Create message from dictionary."""
        msg = cls(
            sender_id=data["sender_id"],
            recipient_id=data["recipient_id"],
            message_type=data["message_type"],
            content=data["content"],
            correlation_id=data.get("correlation_id"),
        )
        msg.id = data.get("id", msg.id)
        msg.timestamp = data.get("timestamp", msg.timestamp)
        msg.acknowledged = data.get("acknowledged", False)
        return msg


class A2AComms:
    """A2A Communication manager."""

    def __init__(self, agent_id: str, storage_dir: Optional[Path] = None):
        """Initialize A2A communications.

        Args:
            agent_id: Unique identifier for this agent
            storage_dir: Directory for persistent message storage
        """
        self.agent_id = agent_id
        self.storage_dir = storage_dir or Path.home() / ".mini-agent" / "a2a"
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # In-memory message queues
        self.inbox: List[A2AMessage] = []
        self.outbox: List[A2AMessage] = []
        self.message_handlers: Dict[str, Callable] = {}

        # Persistent storage files
        self.inbox_file = self.storage_dir / f"{agent_id}_inbox.jsonl"
        self.outbox_file = self.storage_dir / f"{agent_id}_outbox.jsonl"
        self.state_file = self.storage_dir / f"{agent_id}_state.json"

        # Register default handlers
        self.register_handler("self_modification_request", self._handle_self_modification)
        self.register_handler("approval_request", self._handle_approval)
        self.register_handler("modification_complete", self._handle_completion)

    def register_handler(self, message_type: str, handler: Callable):
        """Register a handler for a message type.

        Args:
            message_type: Type of message to handle
            handler: Function that takes A2AMessage and returns response
        """
        self.message_handlers[message_type] = handler

    def send_message(self, recipient_id: str, message_type: str, content: Dict[str, Any]) -> str:
        """Send a message to another agent.

        Args:
            recipient_id: ID of recipient agent
            message_type: Type of message
            content: Message content dictionary

        Returns:
            Message ID
        """
        msg = A2AMessage(
            sender_id=self.agent_id,
            recipient_id=recipient_id,
            message_type=message_type,
            content=content,
        )

        # Add to outbox
        self.outbox.append(msg)

        # Persist to disk
        self._persist_message(msg, self.outbox_file)

        return msg.id

    def broadcast_message(self, message_type: str, content: Dict[str, Any], exclude_self: bool = True):
        """Broadcast message to all agents.

        Args:
            message_type: Type of message
            content: Message content
            exclude_self: Whether to exclude sender
        """
        # This would typically query a registry of all agents
        # For now, we use a simple broadcast file

        broadcast_msg = A2AMessage(
            sender_id=self.agent_id,
            recipient_id="*",  # Broadcast indicator
            message_type=message_type,
            content=content,
        )

        broadcast_file = self.storage_dir / "broadcast.jsonl"
        self._persist_message(broadcast_msg, broadcast_file)

    async def receive_messages(self) -> List[A2AMessage]:
        """Receive all pending messages for this agent.

        Returns:
            List of messages
        """
        # Load from disk
        messages = self._load_messages(self.inbox_file)

        # Add to inbox
        self.inbox.extend(messages)

        # Process messages
        responses = []
        for msg in self.inbox[:]:
            if msg.recipient_id == self.agent_id or msg.recipient_id == "*":
                handler = self.message_handlers.get(msg.message_type)
                if handler:
                    try:
                        response = await handler(msg)
                        if response:
                            responses.append(response)
                        msg.acknowledged = True
                    except Exception as e:
                        print(f"Error handling message {msg.id}: {e}")

        # Save state
        self._save_state()

        return self.inbox

    def _persist_message(self, msg: A2AMessage, file: Path):
        """Persist message to JSONL file."""
        try:
            with open(file, "a", encoding="utf-8") as f:
                f.write(json.dumps(msg.to_dict(), ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"Warning: Could not persist message: {e}")

    def _load_messages(self, file: Path) -> List[A2AMessage]:
        """Load messages from JSONL file."""
        messages = []
        if not file.exists():
            return messages

        try:
            with open(file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        msg_data = json.loads(line)
                        messages.append(A2AMessage.from_dict(msg_data))
        except Exception as e:
            print(f"Warning: Could not load messages: {e}")

        return messages

    def _save_state(self):
        """Save agent state."""
        try:
            state = {
                "agent_id": self.agent_id,
                "last_updated": datetime.now().isoformat(),
                "inbox_count": len(self.inbox),
                "outbox_count": len(self.outbox),
            }
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save state: {e}")

    # Default message handlers
    async def _handle_self_modification(self, msg: A2AMessage) -> Optional[A2AMessage]:
        """Handle self-modification request."""
        content = msg.content
        modification = content.get("modification", {})

        # Validate modification request
        required_fields = ["file_path", "changes", "reasoning"]
        if not all(field in modification for field in required_fields):
            return A2AMessage(
                sender_id=self.agent_id,
                recipient_id=msg.sender_id,
                message_type="modification_rejected",
                content={"reason": "Invalid modification format", "original_request": content},
                correlation_id=msg.correlation_id,
            )

        # Create approval request
        approval_request = {
            "modification_id": str(uuid.uuid4()),
            "agent_id": self.agent_id,
            "file_path": modification["file_path"],
            "changes": modification["changes"],
            "reasoning": modification["reasoning"],
            "timestamp": datetime.now().isoformat(),
        }

        # Send approval request to human/admin
        self.send_message("human_admin", "approval_request", approval_request)

        # Acknowledge receipt
        return A2AMessage(
            sender_id=self.agent_id,
            recipient_id=msg.sender_id,
            message_type="modification_pending_approval",
            content={"approval_id": approval_request["modification_id"]},
            correlation_id=msg.correlation_id,
        )

    async def _handle_approval(self, msg: A2AMessage) -> Optional[A2AMessage]:
        """Handle approval response."""
        content = msg.content
        approved = content.get("approved", False)
        modification_id = content.get("modification_id")

        if approved:
            # Execute modification
            success = await self._execute_modification(content.get("modification", {}))

            if success:
                return A2AMessage(
                    sender_id=self.agent_id,
                    recipient_id=msg.sender_id,
                    message_type="modification_complete",
                    content={
                        "modification_id": modification_id,
                        "status": "success",
                        "message": "Modification applied successfully",
                    },
                    correlation_id=msg.correlation_id,
                )
            else:
                return A2AMessage(
                    sender_id=self.agent_id,
                    recipient_id=msg.sender_id,
                    message_type="modification_failed",
                    content={
                        "modification_id": modification_id,
                        "status": "failed",
                        "error": "Failed to apply modification",
                    },
                    correlation_id=msg.correlation_id,
                )
        else:
            # Modification rejected
            return A2AMessage(
                sender_id=self.agent_id,
                recipient_id=msg.sender_id,
                message_type="modification_rejected",
                content={"modification_id": modification_id, "reason": content.get("reason", "No reason provided")},
                correlation_id=msg.correlation_id,
            )

    async def _handle_completion(self, msg: A2AMessage) -> Optional[A2AMessage]:
        """Handle modification completion notification."""
        # Log the completion
        print(f"Modification {msg.content.get('modification_id')} completed: {msg.content.get('status')}")
        return None

    async def _execute_modification(self, modification: Dict[str, Any]) -> bool:
        """Execute a self-modification."""
        try:
            import os
            from pathlib import Path

            file_path = Path(modification.get("file_path"))

            if not file_path.exists():
                print(f"File not found: {file_path}")
                return False

            changes = modification.get("changes", {})
            change_type = changes.get("type")

            if change_type == "replace":
                old_text = changes.get("old_text")
                new_text = changes.get("new_text")

                if old_text and new_text is not None:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()

                    if old_text in content:
                        content = content.replace(old_text, new_text)

                        with open(file_path, "w", encoding="utf-8") as f:
                            f.write(content)

                        print(f"✅ Modified {file_path}")
                        return True
                    else:
                        print(f"Text not found in {file_path}: {old_text[:50]}...")
                        return False

            elif change_type == "insert":
                position = changes.get("position", "end")
                new_text = changes.get("new_text", "")

                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                if position == "end":
                    content += "\n" + new_text
                elif position == "begin":
                    content = new_text + "\n" + content

                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)

                print(f"✅ Inserted content into {file_path}")
                return True

            return False

        except Exception as e:
            print(f"Error executing modification: {e}")
            return False


# Global A2A instance
_a2a_instance: Optional[A2AComms] = None


def get_a2a_comms(agent_id: Optional[str] = None) -> A2AComms:
    """Get or create global A2AComms instance.

    Args:
        agent_id: Agent ID (uses default if not provided)

    Returns:
        A2AComms instance
    """
    global _a2a_instance

    if _a2a_instance is None:
        if agent_id is None:
            agent_id = f"mini_agent_{uuid.uuid4().hex[:8]}"
        _a2a_instance = A2AComms(agent_id)

    return _a2a_instance
