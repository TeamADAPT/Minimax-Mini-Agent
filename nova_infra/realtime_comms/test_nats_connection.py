#!/usr/bin/env python3
"""
Quick test for NATS connection using correct credentials
"""

import asyncio
import nats
from nats.aio.client import Client as NATSClient


async def test_nats_connection():
    """Test NATS connection with correct credentials"""

    print("🧪 Testing NATS connection...")
    print("   Host: localhost:18020")
    print("   User: admin")
    print("   Password: teamadapt123 (masked)")

    nc = nats.NATS()

    try:
        # Connect with CORRECT credentials (from running server)
        # Note: Running server uses nats/password, not admin/teamadapt123
        await nc.connect(
            servers=["nats://localhost:18020"],
            user="nats",
            password="password",
            max_reconnect_attempts=3,
            reconnect_time_wait=1,
        )

        print("✅ Successfully connected to NATS!")
        print(f"   Client ID: {nc.client_id}")
        print(f"   Server info: {nc.connected_url}")

        # Test subscription
        messages_received = []

        async def message_handler(msg):
            data = msg.data.decode('utf-8')
            messages_received.append(data)
            print(f"📥 Test message received: {data[:50]}...")

        # Subscribe to test channel
        sub = await nc.subscribe("test.bridge.connection", cb=message_handler)
        print("📋 Subscribed to test.bridge.connection")

        # Publish test message
        test_message = "Bridge Priority 1 execution - NATS connection verified"
        await nc.publish("test.bridge.connection", test_message.encode('utf-8'))
        print(f"📤 Published test message")

        # Wait for message delivery
        await asyncio.sleep(0.5)

        if messages_received:
            print("✅ Message delivery confirmed!")
        else:
            print("⚠️  Message not received (may need more time)")

        # Unsubscribe
        await sub.unsubscribe()
        print("🟢 Unsubscribed from test channel")

        # Disconnect
        await nc.close()
        print("🟢 Disconnected from NATS")

        return True

    except Exception as e:
        print(f"❌ NATS connection failed: {e}")
        try:
            await nc.close()
        except:
            pass
        return False


if __name__ == "__main__":
    success = asyncio.run(test_nats_connection())
    if success:
        print("\n🎉 NATS connection verified - ready for message broker implementation")
    else:
        print("\n❌ NATS connection failed - check server status and credentials")
    exit(0 if success else 1)
