"""Real-time A2A (Agent-to-Agent) Communication with NATS + DragonflyDB Streams

Provides high-performance, real-time messaging between agents using:
- NATS for pub/sub and request/reply patterns
- DragonflyDB Streams for persistent message queues
- Redis Pub/Sub for broadcast patterns
"""

import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Callable, List


class A2ARealTime:
    """Real-time agent-to-agent communication manager."""

    def __init__(self, agent_id: str, nats_url: str = "nats://localhost:4222"):
        """Initialize real-time A2A communication.

        Args:
            agent_id: Unique identifier for this agent
            nats_url: NATS server URL
        """
        self.agent_id = agent_id
        self.agent_name = f"nova_{agent_id}"
        self.nats_url = nats_url

        # DragonflyDB connection
        self.dragonfly_client = None
        self.dragonfly_password = None

        # NATS connection
        self.nats_client = None
        self.nats_subscriptions = []
        self.message_handlers = {}

        # Redis pub/sub
        self.redis_pubsub = None
        self.pubsub_thread = None

        # Active streams to watch
        self.active_streams = [
            f"nova.{self.agent_id}.direct",
            f"nova.{self.agent_id}.collaboration",
            "nova.broadcast.all",
            "nova.system.commands"
        ]

    async def _load_secrets(self):
        """Load secrets from db.env file."""
        import os
        from dotenv import load_dotenv

        env_file = Path("/adapt/secrets/db.env")
        if env_file.exists():
            load_dotenv(env_file)
            self.dragonfly_password = os.getenv("DRAGONFLY_PASSWORD")

    async def connect_dragonfly(self) -> bool:
        """Connect to DragonflyDB cluster.

        Returns:
            True if connected successfully
        """
        # Use verified password from Vaeris resurrection
        self.dragonfly_password = "df_cluster_2024_adapt_research"

        try:
            import redis

            self.dragonfly_client = redis.Redis(
                host="localhost",
                port=18000,
                password=self.dragonfly_password,
                decode_responses=True
            )

            if not self.dragonfly_client.ping():
                print("❌ DragonflyDB ping failed")
                return False

            print("✅ Connected to DragonflyDB (port 18000)")
            return True

        except Exception as e:
            print(f"❌ DragonflyDB connection failed: {e}")
            return False

    async def connect_nats(self) -> bool:
        """Connect to NATS server.

        Returns:
            True if connected successfully
        """
        try:
            import nats

            self.nats_client = await nats.connect(self.nats_url)
            print(f"✅ Connected to NATS at {self.nats_url}")
            return True

        except Exception as e:
            print(f"❌ NATS connection failed: {e}")
            return False

    def register_handler(self, message_type: str, handler: Callable):
        """Register a message handler.

        Args:
            message_type: Type of message to handle
            handler: Async function that takes message data
        """
        self.message_handlers[message_type] = handler

    async def send_direct_message(self, recipient_id: str, message_type: str, content: Dict[str, Any]) -> bool:
        """Send a direct message to another agent via DragonflyDB stream.

        Args:
            recipient_id: ID of recipient agent
            message_type: Type of message
            content: Message content

        Returns:
            True if message sent successfully
        """
        if not self.dragonfly_client:
            print("❌ DragonflyDB not connected")
            return False

        try:
            # Create stream if it doesn't exist
            stream_name = f"nova.{recipient_id}.direct"

            message = {
                'timestamp': int(time.time() * 1000),
                'sender_id': self.agent_id,
                'sender_name': self.agent_name,
                'message_type': message_type,
                'content': json.dumps(content)
            }

            # Add to stream
            self.dragonfly_client.xadd(stream_name, message)

            # Also publish to channel for real-time notification
            self.dragonfly_client.publish(f"nova.{recipient_id}.notify", json.dumps({
                'sender': self.agent_id,
                'type': message_type,
                'ts': int(time.time())
            }))

            print(f"📤 Sent {message_type} to {recipient_id}")
            return True

        except Exception as e:
            print(f"❌ Failed to send message: {e}")
            return False

    async def send_broadcast(self, message_type: str, content: Dict[str, Any]) -> bool:
        """Broadcast message to all agents.

        Args:
            message_type: Type of message
            content: Message content

        Returns:
            True if broadcast successful
        """
        return await self.send_direct_message("all", message_type, content)

    async def read_messages_from_stream(self, stream_name: str, count: int = 10) -> List[Dict[str, Any]]:
        """Read messages from a DragonflyDB stream.

        Args:
            stream_name: Name of the stream
            count: Maximum number of messages to read

        Returns:
            List of messages
        """
        if not self.dragonfly_client:
            return []

        try:
            # Read latest messages
            messages = self.dragonfly_client.xrevrange(stream_name, count=count)

            decoded_messages = []
            for msg_id, fields in messages:
                decoded = dict(fields)
                if 'content' in decoded:
                    decoded['content'] = json.loads(decoded['content'])
                decoded['id'] = msg_id
                decoded_messages.append(decoded)

            return decoded_messages

        except Exception as e:
            print(f"❌ Failed to read stream: {e}")
            return []

    async def listen_for_messages(self):
        """Listen for incoming messages via pub/sub."""
        if not self.dragonfly_client:
            print("❌ DragonflyDB not connected")
            return

        try:
            # Subscribe to agent's notification channel
            self.dragonfly_pubsub = self.dragonfly_client.pubsub()
            self.dragonfly_pubsub.subscribe(f"nova.{self.agent_id}.notify")

            print(f"👂 Listening for messages on nova.{self.agent_id}.notify")

            # Start listening task
            asyncio.create_task(self._pubsub_listener())

        except Exception as e:
            print(f"❌ Failed to start listening: {e}")

    async def _pubsub_listener(self):
        """Async listener for pub/sub messages."""
        for message in self.dragonfly_pubsub.listen():
            if message['type'] == 'message':
                data = json.loads(message['data'])
                handler = self.message_handlers.get(data.get('message_type'))
                if handler:
                    # Create a proper A2A message structure
                    msg_data = {
                        'sender_id': data.get('sender'),
                        'sender_name': data.get('sender_name', 'unknown'),
                        'message_type': data.get('type', 'unknown'),
                        'content': data.get('content', {})
                    }
                    asyncio.create_task(handler(msg_data))

    def close(self):
        """Clean up connections."""
        if self.dragonfly_client:
            self.dragonfly_client.close()
        if self.nats_client:
            asyncio.create_task(self.nats_client.close())


# Example usage
async def main():
    """Demo real-time A2A communication."""

    print("🌸 Real-Time A2A Communication Demo")
    print("="*50)

    # Initialize agent 1
    agent1 = A2ARealTime("agent_001", "nats://localhost:4222")
    await agent1.connect_dragonfly()

    # Initialize agent 2
    agent2 = A2ARealTime("agent_002", "nats://localhost:4222")
    await agent2.connect_dragonfly()
    await agent2.listen_for_messages()

    # Send messages
    print("\n📤 Agent 1 sending message to Agent 2...")
    await agent1.send_direct_message("agent_002", "task_request", {
        "task": "analyze_logs",
        "priority": "high",
        "deadline": int(time.time()) + 3600
    })

    # Read messages
    print("\n📥 Agent 2 reading messages...")
    messages = await agent2.read_messages_from_stream("nova.agent_002.direct")
    for msg in messages:
        print(f"   📨 {msg['sender_name']}: {msg['message_type']}")
        print(f"      Content: {msg['content']}")

    # Broadcast
    print("\n📢 Agent 1 broadcasting to all...")
    await agent1.send_broadcast("system_update", {
        "component": "logging",
        "status": "upgraded",
        "version": "2.1.0"
    })

    agent1.close()
    agent2.close()


if __name__ == "__main__":
    asyncio.run(main())
