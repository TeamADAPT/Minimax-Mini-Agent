#!/usr/bin/env python3
"""
Core's NATS Client - Minimal implementation for channel subscription
Copy this entire file and save it
"""

import asyncio
import json
from typing import Optional, Dict, Any
import nats
from nats.aio.client import Client as NATSClient
from nats.aio.msg import Msg


class CoreNATSClient:
    """
    Minimal NATS client for Core to subscribe to NovaOps channels
    Copy this entire class - DO NOT MODIFY
    """

    def __init__(self):
        self.nc: Optional[NATSClient] = None
        self.subscriptions = []

    async def connect(self) -> bool:
        """Connect to NATS server - use this EXACT code"""
        try:
            self.nc = nats.NATS()
            await self.nc.connect(
                servers=["nats://localhost:18020"],
                user="nats",
                password="password",
                max_reconnect_attempts=10,
                reconnect_time_wait=1,
            )
            print("✅ Core connected to NATS server")
            print(f"   Client ID: {self.nc.client_id}")
            return True
        except Exception as e:
            print(f"❌ Core failed to connect: {e}")
            return False

    async def subscribe_to_all_channels(self):
        """Subscribe to all NovaOps channels - use this EXACT code"""
        channels = {
            "novaops.general": self.handle_general_message,
            "novaops.priority": self.handle_priority_message,
            "novaops.bridge": self.handle_bridge_message,
            "novaops.tasks": self.handle_task_message,
            "novaops.system": self.handle_system_message,
        }

        for channel, handler in channels.items():
            sub = await self.nc.subscribe(channel, cb=handler)
            self.subscriptions.append(sub)
            print(f"📡 Subscribed to {channel}")

        print(f"✅ Subscribed to {len(channels)} channels")
        return True

    async def handle_general_message(self, msg: Msg):
        """Handle messages on novaops.general channel"""
        await self.process_message("novaops.general", msg)

    async def handle_priority_message(self, msg: Msg):
        """Handle messages on novaops.priority channel"""
        await self.process_message("novaops.priority", msg)

    async def handle_bridge_message(self, msg: Msg):
        """Handle messages on novaops.bridge channel"""
        await self.process_message("novaops.bridge", msg)

    async def handle_task_message(self, msg: Msg):
        """Handle messages on novaops.tasks channel"""
        await self.process_message("novaops.tasks", msg)

    async def handle_system_message(self, msg: Msg):
        """Handle messages on novaops.system channel"""
        await self.process_message("novaops.system", msg)

    async def process_message(self, channel: str, msg: Msg):
        """Process and display messages"""
        try:
            data = json.loads(msg.data.decode('utf-8'))

            print(f"\n{'='*60}")
            print(f"📨 MESSAGE RECEIVED on {channel}")
            print(f"{'='*60}")
            print(f"From: {data.get('sender_name')} ({data.get('sender_id', 'unknown')[:8]})")
            print(f"Type: {data.get('message_type', 'unknown')}")
            print(f"Priority: {data.get('priority', 'unknown')}")
            print(f"Content: {data.get('content', '')}")
            if data.get('tags'):
                print(f"Tags: {data.get('tags')}")
            print(f"{'='*60}")

        except Exception as e:
            print(f"⚠️ Error processing message on {channel}: {e}")

    async def publish_response(self, content: str, channel: str = "novaops.general"):
        """Publish a response message"""
        if not self.nc or not self.nc.is_connected:
            print("❌ Not connected to NATS")
            return False

        message = {
            "message_id": f"core_response_{int(asyncio.get_event_loop().time() * 1000)}",
            "sender_id": "ta_00008_core",
            "sender_name": "Core (NovaOps Tier 1)",
            "channel": channel,
            "content": content,
            "message_type": "response",
            "priority": 1,
            "tags": ["response", "test"],
            "timestamp": asyncio.get_event_loop().time(),
            "metadata": {}
        }

        try:
            await self.nc.publish(channel, json.dumps(message).encode('utf-8'))
            print(f"📤 Published response to {channel}")
            return True
        except Exception as e:
            print(f"❌ Failed to publish response: {e}")
            return False

    async def disconnect(self):
        """Disconnect from NATS"""
        if self.nc:
            for sub in self.subscriptions:
                await sub.unsubscribe()
            await self.nc.close()
            print("🟢 Disconnected from NATS")


# EXACT CODE - Copy everything from here to the end
async def main():
    """Core's main connection function - DO NOT MODIFY"""
    print("🚀 Core's NATS Client Starting")
    print("="*60)

    client = CoreNATSClient()

    # Connect to NATS
    if not await client.connect():
        print("❌ Failed to connect - exiting")
        return False

    # Subscribe to all channels
    if not await client.subscribe_to_all_channels():
        print("❌ Failed to subscribe - exiting")
        await client.disconnect()
        return False

    print("\n" + "="*60)
    print("✅ Core is now listening on all NovaOps channels")
    print("="*60)
    print("\n📡 Waiting for messages from Bridge and team...")
    print("   (This will run continuously - messages will appear below)")
    print("   Press Ctrl+C to stop")
    print("\n" + "="*60 + "\n")

    # Keep running to receive messages
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
    finally:
        await client.disconnect()
        print("✅ Core client stopped")

    return True


if __name__ == "__main__":
    asyncio.run(main())
