"""
event_hub.py

NOVA Framework Event Hub - NATS-based event streaming for cross-framework communication

Provides real-time event publishing and subscription for:
- Hydration events
- Session lifecycle events
- Cross-framework context transfer
- Agent coordination
"""

import asyncio
import json
from typing import Optional, Callable, Dict, Any, List
from dataclasses import dataclass, asdict
from datetime import datetime

import nats
from nats.aio.client import Client as NATSClient
from nats.aio.msg import Msg


@dataclass
class NovaEvent:
    """Standardized event structure for NOVA Framework"""
    event_id: str
    event_type: str  # 'hydration', 'session.start', 'session.end', 'context.bridge', 'agent.register'
    timestamp: float
    source_agent_id: str
    source_framework: str
    session_id: Optional[str]
    data: Dict[str, Any]
    priority: int = 0  # 0=low, 1=normal, 2=high, 3=critical

    def to_json(self) -> str:
        """Serialize event to JSON"""
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str) -> 'NovaEvent':
        """Deserialize event from JSON"""
        data = json.loads(json_str)
        return cls(**data)


class NovaEventHub:
    """
    NATS-based event hub for NOVA Framework cross-framework communication
    """

    def __init__(
        self,
        nats_url: str = "nats://localhost:18020",
        nats_user: str = "nats",
        nats_password: str = None
    ):
        """
        Initialize NOVA Event Hub

        Args:
            nats_url: NATS server URL
            nats_user: NATS username
            nats_password: NATS password (will load from secrets if None)
        """
        self.nats_url = nats_url
        self.nats_user = nats_user
        self.nats_password = nats_password
        self.nc: Optional[NATSClient] = None
        self.subscriptions: List = []

        # Load password from secrets if not provided
        if self.nats_password is None:
            self.nats_password = self._load_nats_password()

        print(f"🌐 NovaEventHub initialized")
        print(f"   NATS URL: {nats_url}")

    def _load_nats_password(self) -> str:
        """Load NATS password from secrets file"""
        try:
            import os
            secrets_path = "/adapt/secrets/db.env"
            if os.path.exists(secrets_path):
                with open(secrets_path, 'r') as f:
                    for line in f:
                        if line.startswith('NATS_PASSWORD='):
                            return line.split('=', 1)[1].strip().strip('"')
        except Exception as e:
            print(f"⚠️  Could not load NATS password: {e}")

        # Default password for development
        return "nats_password_2024"

    async def connect(self) -> bool:
        """
        Connect to NATS server

        Returns:
            bool: True if connected successfully
        """
        try:
            self.nc = nats.NATS()

            # Set up connection options
            options = {
                "servers": [self.nats_url],
                "user": self.nats_user,
                "password": self.nats_password,
                "max_reconnect_attempts": 10,
                "reconnect_time_wait": 1,
            }

            # Connect to NATS
            await self.nc.connect(**options)

            print("✅ Connected to NATS server")
            return True

        except Exception as e:
            print(f"❌ Failed to connect to NATS: {e}")
            return False

    async def disconnect(self):
        """Disconnect from NATS server"""
        if self.nc and self.nc.is_connected:
            # Unsubscribe from all subscriptions
            for sub in self.subscriptions:
                await sub.unsubscribe()
            self.subscriptions.clear()

            # Close connection
            await self.nc.close()
            print("🌐 Disconnected from NATS server")

    def is_connected(self) -> bool:
        """Check if connected to NATS"""
        return self.nc is not None and self.nc.is_connected

    async def publish_event(self, event: NovaEvent, subject: Optional[str] = None) -> bool:
        """
        Publish an event to NATS

        Args:
            event: NovaEvent to publish
            subject: Custom subject (will auto-generate if None)

        Returns:
            bool: True if published successfully
        """
        if not self.is_connected():
            print("⚠️  Not connected to NATS - cannot publish event")
            return False

        try:
            # Auto-generate subject if not provided
            if subject is None:
                subject = self._generate_subject(event)

            # Serialize event to JSON
            event_json = event.to_json()

            # Publish to NATS
            await self.nc.publish(subject, event_json.encode('utf-8'))

            print(f"📤 Published {event.event_type} to {subject}")
            return True

        except Exception as e:
            print(f"❌ Failed to publish event: {e}")
            return False

    def _generate_subject(self, event: NovaEvent) -> str:
        """Generate NATS subject from event"""
        # Subject format: nova.{framework}.{event_type}.{session_id}
        session_part = event.session_id[:8] if event.session_id else "none"
        return f"nova.{event.source_framework}.{event.event_type}.{session_part}"

    async def subscribe(self, subject: str, callback: Callable[[NovaEvent], None]) -> bool:
        """
        Subscribe to events matching a subject pattern

        Args:
            subject: Subject pattern (can include wildcards)
            callback: Callback function to execute when event received

        Returns:
            bool: True if subscribed successfully
        """
        if not self.is_connected():
            print("⚠️  Not connected to NATS - cannot subscribe")
            return False

        try:
            async def message_handler(msg: Msg):
                try:
                    # Parse event from message
                    event_data = json.loads(msg.data.decode('utf-8'))
                    event = NovaEvent(**event_data)

                    # Call user callback
                    await callback(event)

                except Exception as e:
                    print(f"⚠️  Error in subscription callback: {e}")

            # Subscribe to subject
            sub = await self.nc.subscribe(subject, cb=message_handler)
            self.subscriptions.append(sub)

            print(f"📥 Subscribed to {subject}")
            return True

        except Exception as e:
            print(f"❌ Failed to subscribe to {subject}: {e}")
            return False

    # Convenience methods for common event types

    async def publish_hydration_event(
        self,
        session_id: str,
        agent_id: str,
        framework: str,
        message_count: int,
        token_count: int,
        storage_tiers: int,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> bool:
        """Publish a hydration event"""
        event = NovaEvent(
            event_id=f"hydrate_{int(datetime.now().timestamp())}_{session_id[:8]}",
            event_type="hydration",
            timestamp=datetime.now().timestamp(),
            source_agent_id=agent_id,
            source_framework=framework,
            session_id=session_id,
            data={
                "message_count": message_count,
                "token_count": token_count,
                "storage_tiers": storage_tiers,
                "success": success,
                "error_message": error_message
            },
            priority=1
        )
        return await self.publish_event(event)

    async def publish_session_event(
        self,
        session_id: str,
        agent_id: str,
        framework: str,
        event_type: str  # 'session.start', 'session.end', 'session.pause', 'session.resume'
    ) -> bool:
        """Publish a session lifecycle event"""
        event = NovaEvent(
            event_id=f"session_{int(datetime.now().timestamp())}_{session_id[:8]}",
            event_type=event_type,
            timestamp=datetime.now().timestamp(),
            source_agent_id=agent_id,
            source_framework=framework,
            session_id=session_id,
            data={},
            priority=2  # Session events are higher priority
        )
        return await self.publish_event(event)

    async def publish_context_bridge_event(
        self,
        source_session_id: str,
        target_session_id: str,
        source_framework: str,
        target_framework: str,
        agent_id: str,
        relationship_type: str,
        relevance_score: float
    ) -> bool:
        """Publish a context bridge creation event"""
        event = NovaEvent(
            event_id=f"bridge_{int(datetime.now().timestamp())}_{source_session_id[:8]}_{target_session_id[:8]}",
            event_type="context.bridge",
            timestamp=datetime.now().timestamp(),
            source_agent_id=agent_id,
            source_framework=source_framework,
            session_id=source_session_id,
            data={
                "target_session_id": target_session_id,
                "target_framework": target_framework,
                "relationship_type": relationship_type,
                "relevance_score": relevance_score
            },
            priority=1
        )
        return await self.publish_event(event)

    # Subscription helpers

    async def subscribe_to_hydration_events(
        self,
        framework: Optional[str] = None,
        callback: Callable[[NovaEvent], None] = None
    ) -> bool:
        """
        Subscribe to hydration events

        Args:
            framework: Filter by framework (None for all frameworks)
            callback: Event callback function
        """
        if framework:
            subject = f"nova.{framework}.hydration.*"
        else:
            subject = "nova.*.hydration.*"

        return await self.subscribe(subject, callback or self._default_hydration_handler)

    async def subscribe_to_session_events(
        self,
        framework: Optional[str] = None,
        callback: Callable[[NovaEvent], None] = None
    ) -> bool:
        """Subscribe to session lifecycle events"""
        if framework:
            subject = f"nova.{framework}.session.*"
        else:
            subject = "nova.*.session.*"

        return await self.subscribe(subject, callback or self._default_session_handler)

    async def subscribe_to_all_events(self, callback: Callable[[NovaEvent], None]) -> bool:
        """Subscribe to all NOVA events"""
        return await self.subscribe("nova.>", callback)

    # Default handlers

    async def _default_hydration_handler(self, event: NovaEvent):
        """Default handler for hydration events"""
        data = event.data
        success = "✅" if data.get("success") else "❌"
        print(f"{success} Hydration: {event.source_framework} | "
              f"Messages: {data.get('message_count')} | "
              f"Tiers: {data.get('storage_tiers')}")

    async def _default_session_handler(self, event: NovaEvent):
        """Default handler for session events"""
        session_part = event.session_id[:8] if event.session_id else "none"
        print(f"📋 Session: {event.event_type} | {event.source_framework} | {session_part}")


# Global event hub instance
_event_hub_instance: Optional[NovaEventHub] = None


async def get_event_hub() -> NovaEventHub:
    """Get the global event hub instance"""
    global _event_hub_instance
    if _event_hub_instance is None:
        _event_hub_instance = NovaEventHub()
        await _event_hub_instance.connect()
    return _event_hub_instance


# Example usage
if __name__ == "__main__":
    import asyncio

    async def demo():
        # Create and connect event hub
        hub = NovaEventHub()
        await hub.connect()

        # Subscribe to events with default handlers
        await hub.subscribe_to_hydration_events()
        await hub.subscribe_to_session_events()

        # Publish some test events
        await hub.publish_hydration_event(
            session_id="test_session_001",
            agent_id="ta_00009_bridge",
            framework="nova",
            message_count=5,
            token_count=1500,
            storage_tiers=7
        )

        await hub.publish_session_event(
            session_id="test_session_001",
            agent_id="ta_00009_bridge",
            framework="nova",
            event_type="session.start"
        )

        # Keep running for a bit
        await asyncio.sleep(2)

        # Disconnect
        await hub.disconnect()

    asyncio.run(demo())
