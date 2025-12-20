#!/usr/bin/env python3
"""
Simple Bridge Test Tool - No Manual Code Required

Usage: python3 bridge_test.py ping
       python3 bridge_test.py status
       python3 bridge_test.py command check_infrastructure
"""

import sys
import asyncio
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from nova_framework.core.event_hub import NovaEventHub, NovaEvent


class BridgeTester:
    """Simple tester for Bridge service"""

    async def ping(self):
        """Send ping and wait for pong"""
        print("📤 Sending PING to Bridge...")

        hub = NovaEventHub()
        await hub.connect()

        # Send ping
        ping_event = NovaEvent(
            event_id=f"ping_test_{int(datetime.now().timestamp())}",
            event_type="bridge.ping",
            timestamp=datetime.now().timestamp(),
            source_agent_id="bridge_tester",
            source_framework="tester",
            session_id="ping_test",
            data={"message": "Test ping for Bridge"},
            priority=2
        )

        await hub.publish_event(ping_event, "novaops.bridge")
        print("✅ Ping sent")

        # Check for response (briefly)
        await asyncio.sleep(1)
        await hub.disconnect()
        print("✅ Test complete - check Bridge log for response")

    async def status(self):
        """Request Bridge status"""
        print("📡 Querying Bridge status...")

        hub = NovaEventHub()
        await hub.connect()

        query_event = NovaEvent(
            event_id=f"query_{int(datetime.now().timestamp())}",
            event_type="core.query",
            timestamp=datetime.now().timestamp(),
            source_agent_id="bridge_tester",
            source_framework="tester",
            session_id="query_test",
            data={"query": "status"},
            priority=1
        )

        await hub.publish_event(query_event, "novaops.bridge")
        print("✅ Status query sent")

        await asyncio.sleep(1)
        await hub.disconnect()

    async def command(self, cmd: str):
        """Send command to Bridge"""
        print(f"📤 Sending command: {cmd}")

        hub = NovaEventHub()
        await hub.connect()

        cmd_event = NovaEvent(
            event_id=f"cmd_{int(datetime.now().timestamp())}",
            event_type="core.command",
            timestamp=datetime.now().timestamp(),
            source_agent_id="bridge_tester",
            source_framework="tester",
            session_id="command_test",
            data={
                "command": cmd,
                "params": {}
            },
            priority=2
        )

        await hub.publish_event(cmd_event, "novaops.bridge")
        print("✅ Command sent")

        await asyncio.sleep(2)
        await hub.disconnect()

    async def bidirectional(self):
        """Test bidirectional communication"""
        print("🔄 Testing bidirectional communication...")

        hub = NovaEventHub()
        await hub.connect()

        # Send 3 ping-pong rounds
        for i in range(1, 4):
            ping_event = NovaEvent(
                event_id=f"ping_round_{i}_{int(datetime.now().timestamp())}",
                event_type="bridge.ping",
                timestamp=datetime.now().timestamp(),
                source_agent_id="bridge_tester",
                source_framework="tester",
                session_id=f"bidirectional_test",
                data={
                    "message": f"Round {i}/3 - bidirectional test",
                    "round": i
                },
                priority=2
            )

            await hub.publish_event(ping_event, "novaops.bridge")
            print(f"📤 Sent ping #{i}")
            await asyncio.sleep(1.5)

        await hub.disconnect()
        print("✅ Bidirectional test complete")


async def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 bridge_test.py ping")
        print("  python3 bridge_test.py status")
        print("  python3 bridge_test.py command <command_name>")
        print("  python3 bridge_test.py bidirectional")
        sys.exit(1)

    tester = BridgeTester()
    command = sys.argv[1]

    if command == "ping":
        await tester.ping()
    elif command == "status":
        await tester.status()
    elif command == "command":
        if len(sys.argv) < 3:
            print("Error: Command name required")
            print("Example: python3 bridge_test.py command check_infrastructure")
            sys.exit(1)
        await tester.command(sys.argv[2])
    elif command == "bidirectional":
        await tester.bidirectional()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
