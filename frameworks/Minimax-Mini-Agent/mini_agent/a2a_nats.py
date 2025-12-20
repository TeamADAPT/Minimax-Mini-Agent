"""A2A (Agent-to-Agent) Communication via NATS

Lightweight, high-performance messaging for agent collaboration.
Requirements: NATS server (install: apt install nats-server)
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Any, Dict, Optional, Callable, List
from dataclasses import dataclass, asdict


@dataclass
class A2AMessage:
    """Represents a message between agents via NATS."""

    sender_id: str
    recipient_id: str
    message_type: str
    content: Dict[str, Any]
    correlation_id: Optional[str] = None
    timestamp: Optional[str] = None
    id: Optional[str] = None

    def __post_init__(self):
        if self.id is None:
            self.id = str(uuid.uuid4())
        if self.correlation_id is None:
            self.correlation_id = self.id
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "A2AMessage":
        return cls(**data)


class A2ANATSClient:
    """NATS-based A2A communication client."""

    def __init__(
        self,
        agent_id: str,
        nats_url: str = "nats://localhost:4222",
        auto_reconnect: bool = True,
    ):
        """Initialize NATS A2A client.

        Args:
            agent_id: Unique identifier for this agent
            nats_url: NATS server URL (default: localhost:4222)
            auto_reconnect: Auto-reconnect on connection loss
        """
        self.agent_id = agent_id
        self.nats_url = nats_url
        self.auto_reconnect = auto_reconnect

        self._nc = None
        self._subscriptions = []
        self._message_handlers: Dict[str, Callable] = {}

        # Register default handlers
        self.register_handler("self_modification_request", self._default_handler)
        self.register_handler("approval_request", self._default_handler)
        self.register_handler("modification_complete", self._default_handler)
        self.register_handler("modification_rejected", self._default_handler)

    async def connect(self) -> bool:
        """Connect to NATS server.

        Returns:
            True if connected, False otherwise
        """
        try:
            import nats
        except ImportError:
            print("❌ NATS Python client not installed. Install with: pip install nats-py")
            return False

        try:
            self._nc = await nats.connect(self.nats_url)
            print(f"✅ Connected to NATS at {self.nats_url} (Agent: {self.agent_id})")

            # Subscribe to agent's inbox
            inbox_subject = f"a2a.{self.agent_id}.inbox"
            sub = await self._nc.subscribe(inbox_subject, cb=self._message_handler)
            self._subscriptions.append(sub)

            # Subscribe to broadcast channel
            broadcast_subject = "a2a.broadcast.>"
            sub = await self._nc.subscribe(broadcast_subject, cb=self._message_handler)
            self._subscriptions.append(sub)

            return True
        except Exception as e:
            print(f"❌ Failed to connect to NATS: {e}")
            return False

    async def disconnect(self):
        """Disconnect from NATS server."""
        if self._nc:
            # Unsubscribe all
            for sub in self._subscriptions:
                await sub.unsubscribe()
            self._subscriptions.clear()

            # Close connection
            await self._nc.close()
            self._nc = None

            print(f"✅ Disconnected from NATS (Agent: {self.agent_id})")

    def register_handler(self, message_type: str, handler: Callable):
        """Register a message handler.

        Args:
            message_type: Type of message to handle
            handler: Async function that takes A2AMessage and returns optional response
        """
        self._message_handlers[message_type] = handler

    async def send_message(
        self, recipient_id: str, message_type: str, content: Dict[str, Any]
    ) -> Optional[str]:
        """Send a message to a specific agent.

        Args:
            recipient_id: ID of the recipient agent
            message_type: Type of message
            content: Message content

        Returns:
            Message ID if successful, None otherwise
        """
        if not self._nc:
            print("❌ Not connected to NATS")
            return None

        try:
            msg = A2AMessage(
                sender_id=self.agent_id,
                recipient_id=recipient_id,
                message_type=message_type,
                content=content,
            )

            subject = f"a2a.{recipient_id}.inbox"
            payload = json.dumps(msg.to_dict()).encode()

            await self._nc.publish(subject, payload)
            # print(f"📤 Sent {message_type} to {recipient_id} (ID: {msg.id[:8]}...)")

            return msg.id

        except Exception as e:
            print(f"❌ Failed to send message: {e}")
            return None

    async def broadcast_message(self, message_type: str, content: Dict[str, Any]):
        """Broadcast message to all agents.

        Args:
            message_type: Type of message
            content: Message content
        """
        if not self._nc:
            print("❌ Not connected to NATS")
            return

        try:
            msg = A2AMessage(
                sender_id=self.agent_id, recipient_id="*", message_type=message_type, content=content
            )

            subject = "a2a.broadcast"
            payload = json.dumps(msg.to_dict()).encode()

            await self._nc.publish(subject, payload)
            # print(f"📢 Broadcast {message_type} to all agents")

        except Exception as e:
            print(f"❌ Failed to broadcast message: {e}")

    async def _message_handler(self, msg):
        """Internal message handler for NATS subscriptions."""
        try:
            data = json.loads(msg.data.decode())
            a2a_msg = A2AMessage.from_dict(data)

            # Check if message is for this agent or broadcast
            if a2a_msg.recipient_id in (self.agent_id, "*"):
                await self._process_message(a2a_msg)

        except Exception as e:
            print(f"❌ Error processing NATS message: {e}")

    async def _process_message(self, a2a_msg: A2AMessage):
        """Process received A2A message."""
        handler = self._message_handlers.get(a2a_msg.message_type)

        if handler:
            try:
                response = await handler(a2a_msg)
                if response and a2a_msg.sender_id != "*":
                    # Send response back to sender
                    await self.send_message(
                        a2a_msg.sender_id,
                        f"{a2a_msg.message_type}_response",
                        {"response": response, "acknowledged": True},
                    )
            except Exception as e:
                print(f"❌ Error in message handler: {e}")
        else:
            print(f"⚠️  No handler for message type: {a2a_msg.message_type}")

    async def _default_handler(self, msg: A2AMessage) -> Optional[str]:
        """Default handler for unhandled messages."""
        # print(f"ℹ️  Received {msg.message_type} from {msg.sender_id}")
        return f"Received {msg.message_type}"

    async def request_reply(
        self, recipient_id: str, message_type: str, content: Dict[str, Any], timeout: float = 5.0
    ) -> Optional[A2AMessage]:
        """Send request and wait for reply.

        Args:
            recipient_id: Recipient agent ID
            message_type: Message type
            content: Request content
            timeout: Timeout in seconds

        Returns:
            Response message or None on timeout
        """
        if not self._nc:
            print("❌ Not connected to NATS")
            return None

        try:
            request_msg = A2AMessage(
                sender_id=self.agent_id,
                recipient_id=recipient_id,
                message_type=message_type,
                content=content,
            )

            # Create inbox for reply
            inbox = f"_INBOX.{uuid.uuid4().hex}"

            # Subscribe to reply inbox
            future = asyncio.Future()

            async def reply_handler(msg):
                try:
                    data = json.loads(msg.data.decode())
                    if not future.done():
                        future.set_result(A2AMessage.from_dict(data))
                except Exception as e:
                    if not future.done():
                        future.set_exception(e)

            sub = await self._nc.subscribe(inbox, cb=reply_handler)

            # Send request with reply subject
            subject = f"a2a.{recipient_id}.inbox"
            payload = json.dumps(request_msg.to_dict()).encode()
            await self._nc.publish(subject, payload, reply=inbox)

            # Wait for reply
            try:
                response = await asyncio.wait_for(future, timeout)
                return response
            except asyncio.TimeoutError:
                print(f"⏰ Timeout waiting for reply from {recipient_id}")
                return None
            finally:
                await sub.unsubscribe()

        except Exception as e:
            print(f"❌ Request failed: {e}")
            return None

    def is_connected(self) -> bool:
        """Check if connected to NATS."""
        return self._nc is not None and self._nc.is_connected


# Global A2A client instance for convenience
_global_a2a_client: Optional[A2ANATSClient] = None


def get_a2a_client(agent_id: Optional[str] = None) -> A2ANATSClient:
    """Get or create global A2A client.

    Args:
        agent_id: Agent ID (uses default if not provided)

    Returns:
        A2ANATSClient instance
    """
    global _global_a2a_client

    if _global_a2a_client is None:
        if agent_id is None:
            import uuid

            agent_id = f"mini_agent_{uuid.uuid4().hex[:8]}"
        _global_a2a_client = A2ANATSClient(agent_id)

    return _global_a2a_client


def set_a2a_client(client: A2ANATSClient):
    """Set the global A2A client instance.

    Args:
        client: A2ANATSClient instance
    """
    global _global_a2a_client
    _global_a2a_client = client


# NATS installation helper
async def check_nats_server():
    """Check if NATS server is running and provide installation instructions."""
    import socket

    try:
        # Try to connect to NATS
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(("localhost", 4222))
        sock.close()

        if result == 0:
            print("✅ NATS server is running on localhost:4222")
            return True
        else:
            print("❌ NATS server not running on localhost:4222")
            print("")
            print("To install NATS server:")
            print("  On Ubuntu/Debian: sudo apt install nats-server")
            print("  On CentOS/RHEL: sudo yum install nats-server")
            print("  On macOS: brew install nats-server")
            print("")
            print("To start NATS server:")
            print("  sudo systemctl start nats-server")
            print("  # or")
            print("  nats-server &")
            return False

    except Exception as e:
        print(f"❌ Error checking NATS server: {e}")
        return False
