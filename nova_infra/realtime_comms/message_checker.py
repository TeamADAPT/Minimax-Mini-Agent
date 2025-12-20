#!/usr/bin/env python3
"""
Simple Message Checker - Check for recent messages on NovaOps channels
"""

import asyncio
import sys
import time
sys.path.insert(0, '/adapt/platform/novaops')

from nova_infra.realtime_comms.message_broker import NovaMessageBroker


async def check_recent_messages(duration_seconds=10):
    """Check for recent messages on all channels"""

    print("🔍 Checking NovaOps channels for messages...")
    print("="*60)

    broker = NovaMessageBroker()
    messages_received = []

    async def message_handler(msg):
        messages_received.append({
            'timestamp': time.strftime('%H:%M:%S'),
            'sender': f"{msg.sender_name} ({msg.sender_id[:8]})",
            'channel': msg.channel,
            'type': msg.message_type,
            'priority': msg.priority,
            'content': msg.content[:80] + "..." if len(msg.content) > 80 else msg.content
        })

    # Connect and subscribe
    connected = await broker.connect()
    if not connected:
        print("❌ Failed to connect to NATS")
        return

    print("✅ Connected to NATS")
    print(f"📡 Subscribing to all 5 NovaOps channels...")
    print("")

    # Subscribe to all channels
    await broker.subscribe('novaops.general', message_handler)
    await broker.subscribe('novaops.priority', message_handler)
    await broker.subscribe('novaops.bridge', message_handler)
    await broker.subscribe('novaops.tasks', message_handler)
    await broker.subscribe('novaops.system', message_handler)

    print(f"⏱️  Listening for {duration_seconds} seconds...")
    print("   (Any new messages will appear below)")
    print("-"*60)

    await asyncio.sleep(duration_seconds)

    await broker.disconnect()

    # Report results
    print("\n" + "="*60)
    if messages_received:
        print(f"✅ Received {len(messages_received)} message(s):")
        print("")
        for i, msg in enumerate(messages_received, 1):
            print(f"📨 Message {i}:")
            print(f"   Time: {msg['timestamp']}")
            print(f"   From: {msg['sender']}")
            print(f"   Channel: {msg['channel']}")
            print(f"   Type: {msg['type']}")
            print(f"   Priority: {msg['priority']}")
            print(f"   Content: {msg['content']}")
            print()
    else:
        print("📭 No messages received")
        print("   All channels are active but silent")
        print("   No new communications in the last 10 seconds")

    print("="*60)
    return len(messages_received)


if __name__ == "__main__":
    duration = 10  # seconds
    count = asyncio.run(check_recent_messages(duration))
    exit(0 if count >= 0 else 1)
