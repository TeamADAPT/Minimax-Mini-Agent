#!/usr/bin/env python3
"""
Bridge Monitoring Service for NovaEventHub

Persistent monitoring service for Bridge ↔ Core communication using mm's NovaEventHub
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from nova_framework.core.event_hub import NovaEventHub, NovaEvent


class BridgeMonitor:
    """Persistent monitoring service for Bridge communication"""

    def __init__(self):
        self.hub = NovaEventHub()
        self.message_count = 0

    async def start(self):
        """Start the monitoring service"""
        print("🌉 Bridge Monitor Starting...")
        print("   Using: NovaEventHub (mm's built-in event system)")

        # Connect to NATS
        connected = await self.hub.connect()
        if not connected:
            print("❌ Failed to connect to NATS")
            return False

        # Subscribe to Bridge channel
        await self.hub.subscribe("novaops.bridge", self.handle_bridge_message)
        print("📡 Subscribed to novaops.bridge channel")

        # Subscribe to all events for monitoring
        await self.hub.subscribe_to_all_events(self.handle_all_events)
        print("📡 Subscribed to all Nova events")

        print("✅ Bridge Monitor running (persistent)")
        return True

    async def handle_bridge_message(self, event: NovaEvent):
        """Handle messages on novaops.bridge channel"""
        self.message_count += 1
        print(f"\n🌉 Bridge Message #{self.message_count}")
        print(f"   From: {event.source_framework} ({event.source_agent_id})")
        print(f"   Type: {event.event_type}")
        print(f"   Data: {event.data}")

    async def handle_all_events(self, event: NovaEvent):
        """Monitor all Nova events"""
        if event.event_type in ["hydration", "session.start", "session.end"]:
            print(f"\n📊 System Event: {event.event_type}")
            print(f"   Framework: {event.source_framework}")
            print(f"   Agent: {event.source_agent_id[:8]}...")

    async def run_forever(self):
        """Run the monitor continuously"""
        try:
            await self.start()
            print("\n" + "="*60)
            print("Bridge Monitor is OPERATIONAL")
            print("Ready for bidirectional communication")
            print("="*60 + "\n")

            # Keep running
            while True:
                await asyncio.sleep(1)

        except KeyboardInterrupt:
            print("\n🌉 Bridge Monitor stopping...")
        finally:
            await self.hub.disconnect()
            print("🌉 Bridge Monitor stopped")


if __name__ == "__main__":
    monitor = BridgeMonitor()
    asyncio.run(monitor.run_forever())
