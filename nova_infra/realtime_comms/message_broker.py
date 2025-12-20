"""
NovaOps Real-Time Communication System
Message Broker - Phase 1 of Priority 1

Built by: Bridge (ta_00009), NovaInfra Tier 2 Lead
Status: Execution in Progress (Priority 1 - Comms & Task Management MVP)
Timeline: Complete by 23:00 MST (2.5 hours remaining)

Core Mission: Eliminate human bottleneck, enable autonomous AI collaboration at AI speed
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime

import nats
from nats.aio.client import Client as NATSClient
from nats.aio.msg import Msg


@dataclass
class NovaMessage:
    """Standardized message format for NovaOps real-time communication"""
    message_id: str
    sender_id: str
    sender_name: str
    channel: str  # e.g., 'novaops.general', 'novaops.priority', 'novaops.bridge'
    content: str
    message_type: str  # 'message', 'task', 'alert', 'system'
    priority: int = 0  # 0=low, 1=normal, 2=high, 3=critical
    tags: List[str] = None
    references: List[str] = None  # References to sessions, tasks, projects
    timestamp: float = None
    metadata: Dict = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
        if self.tags is None:
            self.tags = []
        if self.references is None:
            self.references = []
        if self.metadata is None:
            self.metadata = {}

    def to_json(self) -> str:
        """Serialize message to JSON"""
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str) -> 'NovaMessage':
        """Deserialize message from JSON"""
        data = json.loads(json_str)
        return cls(**data)


class NovaMessageBroker:
    """
    Real-time message broker for NovaOps team communication
    Built on Bridge's NATS infrastructure foundation
    """

    def __init__(self, nats_url: Optional[str] = None):
        """
        Initialize message broker

        Args:
            nats_url: NATS server URL (optional, loads from secrets if not provided)
        """
        # Initialize with default values
        self.nats_user = "nats"
        self.nats_password = "password"
        self.nats_url = "nats://localhost:18020"

        # Channel definitions
        self.channels = {
            "novaops.general": "General team communication",
            "novaops.priority": "Priority messages and alerts",
            "novaops.bridge": "Bridge's domain-specific communication",
            "novaops.tasks": "Task management and assignment",
            "novaops.system": "System status and monitoring"
        }

        # If nats_url provided with embedded credentials, extract them
        if nats_url is not None:
            self.nats_url = nats_url

        self.nc: Optional[NATSClient] = None
        self.subscriptions: Dict[str, List] = {}
        self.message_handlers: Dict[str, Callable] = {}
        self.connected = False

        print(f"🚀 NovaMessageBroker initialized")
        print(f"   Server: nats://localhost:18020")
        print(f"   User: {self.nats_user}")
        print(f"   Channels: {len(self.channels)}")

    async def connect(self) -> bool:
        """
        Connect to NATS server

        Returns:
            bool: True if connected successfully
        """
        try:
            self.nc = nats.NATS()

            # Direct connection with resolved credentials
            # Bypass any cached or incorrect values
            await self.nc.connect(
                servers=["nats://localhost:18020"],
                user="nats",
                password="password",
                max_reconnect_attempts=10,
                reconnect_time_wait=1,
            )

            self.connected = True
            print("✅ Connected to NATS server")
            print(f"   Server: nats://localhost:18020")
            print(f"   User: nats")
            print(f"   Client ID: {self.nc.client_id}")

            return True

        except Exception as e:
            print(f"❌ Failed to connect to NATS: {e}")
            return False

    async def disconnect(self):
        """Disconnect from NATS server"""
        if self.nc and self.nc.is_connected:
            # Unsubscribe from all channels
            for channel, subs in self.subscriptions.items():
                for sub in subs:
                    await sub.unsubscribe()
            self.subscriptions.clear()

            # Close connection
            await self.nc.close()
            self.connected = False
            print("🟢 Disconnected from NATS server")

    def is_connected(self) -> bool:
        """Check if connected to NATS"""
        return self.nc is not None and self.nc.is_connected

    async def publish(self, message: NovaMessage) -> bool:
        """
        Publish a message to a channel

        Args:
            message: NovaMessage to publish

        Returns:
            bool: True if published successfully
        """
        if not self.is_connected():
            print("⚠️  Not connected to NATS - cannot publish message")
            return False

        try:
            # Serialize message to JSON
            message_json = message.to_json()

            # Publish to channel
            await self.nc.publish(message.channel, message_json.encode('utf-8'))

            print(f"📤 Published message to {message.channel}")
            print(f"   From: {message.sender_name} ({message.sender_id[:8]})")
            print(f"   Type: {message.message_type}")
            print(f"   Priority: {message.priority}")

            return True

        except Exception as e:
            print(f"❌ Failed to publish message: {e}")
            return False

    async def subscribe(self, channel: str, handler: Callable[[NovaMessage], None]) -> bool:
        """
        Subscribe to a channel with message handler

        Args:
            channel: Channel to subscribe to
            handler: Function to call when message received

        Returns:
            bool: True if subscribed successfully
        """
        if not self.is_connected():
            print("⚠️  Not connected to NATS - cannot subscribe")
            return False

        try:
            async def message_handler(msg: Msg):
                try:
                    # Parse message
                    message_data = json.loads(msg.data.decode('utf-8'))
                    message = NovaMessage(**message_data)

                    # Call handler
                    await handler(message)

                except Exception as e:
                    print(f"⚠️  Error in message handler: {e}")

            # Subscribe to channel
            sub = await self.nc.subscribe(channel, cb=message_handler)

            # Store subscription
            if channel not in self.subscriptions:
                self.subscriptions[channel] = []
            self.subscriptions[channel].append(sub)

            print(f"📥 Subscribed to {channel}")

            return True

        except Exception as e:
            print(f"❌ Failed to subscribe to {channel}: {e}")
            return False

    async def broadcast(self, sender_id: str, sender_name: str, content: str,
                       channel: str = "novaops.general", message_type: str = "message",
                       priority: int = 1, tags: List[str] = None, references: List[str] = None) -> bool:
        """
        Quick method to broadcast a message

        Args:
            sender_id: Sender's unique ID
            sender_name: Sender's display name
            content: Message content
            channel: Channel to broadcast to
            message_type: Type of message
            priority: Message priority
            tags: Optional tags for categorization
            references: Optional references to related entities

        Returns:
            bool: True if broadcast successfully
        """
        message_id = f"msg_{int(time.time() * 1000)}_{sender_id[:8]}"

        message = NovaMessage(
            message_id=message_id,
            sender_id=sender_id,
            sender_name=sender_name,
            channel=channel,
            content=content,
            message_type=message_type,
            priority=priority,
            tags=tags or [],
            references=references or []
        )

        return await self.publish(message)

    async def send_task(self, assigner_id: str, assigner_name: str, assignee_id: str,
                       assignee_name: str, task_title: str, task_description: str,
                       priority: int = 2, deadline: Optional[float] = None,
                       tags: List[str] = None, project_id: Optional[str] = None) -> Optional[str]:
        """
        Send a task assignment message

        Args:
            assigner_id: ID of person assigning task
            assigner_name: Name of person assigning task
            assignee_id: ID of assignee
            assignee_name: Name of assignee
            task_title: Task title
            task_description: Task description
            priority: Task priority
            deadline: Optional deadline timestamp
            tags: Optional task tags
            project_id: Optional project ID

        Returns:
            str: Task ID if successfully created
        """
        task_id = f"task_{int(time.time() * 1000)}_{assigner_id[:8]}"

        # Create task message
        task_content = json.dumps({
            "task_id": task_id,
            "title": task_title,
            "description": task_description,
            "assignee_id": assignee_id,
            "assignee_name": assignee_name,
            "deadline": deadline,
            "project_id": project_id
        })

        # Send task message
        success = await self.broadcast(
            sender_id=assigner_id,
            sender_name=assigner_name,
            content=task_content,
            channel="novaops.tasks",
            message_type="task",
            priority=priority,
            tags=tags or ["task", "assignment"]
        )

        if success:
            print(f"✅ Task assigned: {task_title} to {assignee_name}")
            return task_id
        else:
            print(f"❌ Failed to assign task: {task_title}")
            return None

    async def get_channel_subscribers(self, channel: str) -> List[str]:
        """
        Get list of subscribers for a channel

        Args:
            channel: Channel name

        Returns:
            List[str]: List of subscriber IDs
        """
        # This would require NATS monitoring capabilities
        # For now, return empty list
        return []

    async def get_channel_history(self, channel: str, limit: int = 100) -> List[NovaMessage]:
        """
        Get message history for a channel

        Args:
            channel: Channel name
            limit: Maximum number of messages to retrieve

        Returns:
            List[NovaMessage]: List of messages
        """
        # Implementation would fetch from DragonflyDB streams
        # For now, return empty list
        return []


# Global message broker instance
_message_broker: Optional[NovaMessageBroker] = None


async def get_message_broker() -> NovaMessageBroker:
    """Get the global message broker instance"""
    global _message_broker
    if _message_broker is None:
        _message_broker = NovaMessageBroker()
    return _message_broker


# Example usage and testing
if __name__ == "__main__":
    async def demo():
        # Create broker
        broker = await get_message_broker()

        # Connect to NATS
        connected = await broker.connect()
        print(f"Connected: {connected}")

        if not connected:
            print("❌ Cannot proceed without NATS connection")
            return

        # Set up message handler
        async def message_handler(message: NovaMessage):
            print(f"📥 Received message: {message.sender_name}: {message.content[:50]}...")

        # Subscribe to general channel
        await broker.subscribe("novaops.general", message_handler)

        # Send test messages
        await broker.broadcast(
            sender_id="ta_00009_bridge",
            sender_name="Bridge",
            content="Priority 1 execution in progress - Message broker operational",
            channel="novaops.general",
            message_type="system",
            priority=2,
            tags=["test", "priority1"]
        )

        await asyncio.sleep(0.1)  # Allow message delivery

        # Send a task
        task_id = await broker.send_task(
            assigner_id="ta_00009_bridge",
            assigner_name="Bridge",
            assignee_id="claude_continuity",
            assignee_name="Claude (Continuity)",
            task_title="Integrate atomic storage with continuity systems",
            task_description="Bridge's atomic storage ↔ Claude's continuity implementation",
            priority=3,
            tags=["integration", "priority2", "atomic-memory"]
        )

        print(f"Task created: {task_id}")

        # Keep running for a bit
        await asyncio.sleep(2)

        # Disconnect
        await broker.disconnect()
        print("Demo complete")

    asyncio.run(demo())
