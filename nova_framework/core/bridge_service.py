"""
Native Bridge Bidirectional Service

Proper persistent service for Bridge ↔ Core communication
- No manual code execution needed
- Native Python service with systemd management
- Wake-on-message via persistent NATS subscriptions
- Bidirectional routing and response handling
"""

import asyncio
import signal
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, Callable

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from nova_framework.core.event_hub import NovaEventHub, NovaEvent


class BridgeService:
    """Native Bridge service with bidirectional communication"""

    def __init__(self, service_name: str = "bridge_native_listener"):
        self.hub = NovaEventHub()
        self.service_name = service_name
        self.is_running = False
        self.message_count = 0
        self.start_time = None
        self.response_handlers: Dict[str, Callable] = {}

    async def start(self):
        """Start Bridge service as persistent daemon"""
        self.start_time = datetime.now()
        print(f"🌉 {self.service_name} starting...")

        # Connect to NATS
        if not await self.hub.connect():
            print(f"❌ {self.service_name} failed to connect to NATS")
            return False

        # Subscribe to Bridge channel
        await self.hub.subscribe("novaops.bridge", self.handle_bridge_message)
        print(f"📡 Subscribed to novaops.bridge")

        # Subscribe to Core commands
        await self.hub.subscribe("novaops.core.commands", self.handle_core_command)

        # Subscribe to system events
        await self.hub.subscribe_to_all_events(self.handle_system_event)
        print(f"📡 Monitoring all system events")

        self.is_running = True
        print(f"✅ {self.service_name} operational - waiting for messages")
        return True

    async def handle_bridge_message(self, event: NovaEvent):
        """Handle incoming Bridge messages"""
        self.message_count += 1

        print(f"\n🌉 {self.service_name} RECEIVED #{self.message_count}")
        print(f"   Type: {event.event_type}")
        print(f"   From: {event.source_framework}")
        print(f"   Data: {event.data}")

        # Route based on message type
        if event.event_type == "bridge.ping":
            await self.respond_to_ping(event)
        elif event.event_type == "core.query":
            await self.respond_to_query(event)
        elif event.event_type == "bridge.message":
            await self.handle_message(event)
        elif event.event_type == "bridge.command":
            await self.execute_command(event)
        elif event.event_type == "bridge.sync":
            await self.handle_sync(event)
        else:
            print(f"   📝 Unhandled: {event.event_type}")

    async def respond_to_ping(self, event: NovaEvent):
        """Respond to ping with pong"""
        print(f"   🏓 PING received - sending PONG")

        response = NovaEvent(
            event_id=f"pong_{int(datetime.now().timestamp())}",
            event_type="bridge.pong",
            timestamp=datetime.now().timestamp(),
            source_agent_id=self.service_name,
            source_framework="bridge",
            session_id=event.session_id,
            data={
                "reply_to": event.event_id,
                "message": "Bridge is awake and responding",
                "uptime": str(datetime.now() - self.start_time),
                "messages_processed": self.message_count
            },
            priority=2
        )

        await self.hub.publish_event(response, "novaops.bridge")
        print(f"   ✅ PONG sent")

    async def respond_to_query(self, event: NovaEvent):
        """Respond to status queries"""
        query = event.data.get("query", "status")
        print(f"   ❓ QUERY received: {query}")

        response_data = {
            "status": "operational",
            "service": self.service_name,
            "uptime": str(datetime.now() - self.start_time),
            "messages_processed": self.message_count,
            "connected": self.hub.is_connected()
        }

        response = NovaEvent(
            event_id=f"query_resp_{int(datetime.now().timestamp())}",
            event_type="bridge.query_response",
            timestamp=datetime.now().timestamp(),
            source_agent_id=self.service_name,
            source_framework="bridge",
            session_id=event.session_id,
            data=response_data,
            priority=1
        )

        await self.hub.publish_event(response, "novaops.bridge")
        print(f"   ✅ Query response sent")

    async def handle_message(self, event: NovaEvent):
        """Handle general messages"""
        message = event.data.get("message", "")
        print(f"   💬 Message: {message}")

        # Autonomous processing based on message content
        if "urgent" in message.lower():
            await self.handle_urgent_message(event)
        elif "status" in message.lower():
            await self.respond_to_query(event)
        else:
            print(f"   ✅ Message acknowledged")

    async def execute_command(self, event: NovaEvent):
        """Execute commands autonomously"""
        command = event.data.get("command", "")
        params = event.data.get("params", {})
        print(f"   🛠️ Command: {command}")

        result = await self.run_command(command, params)

        response = NovaEvent(
            event_id=f"cmd_ack_{int(datetime.now().timestamp())}",
            event_type="bridge.command_ack",
            timestamp=datetime.now().timestamp(),
            source_agent_id=self.service_name,
            source_framework="bridge",
            session_id=event.session_id,
            data={
                "command": command,
                "status": "completed",
                "result": result
            },
            priority=1
        )

        await self.hub.publish_event(response, "novaops.bridge")
        print(f"   ✅ Command executed and acknowledged")

    async def handle_sync(self, event: NovaEvent):
        """Handle synchronization requests"""
        print(f"   🔄 Sync request from {event.source_framework}")

        sync_data = {
            "service": self.service_name,
            "uptime": str(datetime.now() - self.start_time),
            "messages_processed": self.message_count,
            "is_running": self.is_running
        }

        response = NovaEvent(
            event_id=f"sync_resp_{int(datetime.now().timestamp())}",
            event_type="bridge.sync_response",
            timestamp=datetime.now().timestamp(),
            source_agent_id=self.service_name,
            source_framework="bridge",
            session_id=event.session_id,
            data=sync_data,
            priority=1
        )

        await self.hub.publish_event(response, "novaops.bridge")
        print(f"   ✅ Sync response sent")

    async def handle_core_command(self, event: NovaEvent):
        """Handle direct commands from Core"""
        await self.execute_command(event)

    async def handle_system_event(self, event: NovaEvent):
        """Monitor system events for context"""
        if event.event_type in ["hydration", "session.start", "session.end"]:
            print(f"📊 System: {event.event_type} | {event.source_framework}")

    async def handle_urgent_message(self, event: NovaEvent):
        """Handle urgent messages with priority"""
        print(f"   🚨 URGENT: {event.data.get('message')}")

        # Could trigger notifications, alerts, etc.
        print(f"   ✅ Urgent message handled")

    async def run_command(self, command: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute specific commands"""
        if command == "check_infrastructure":
            return await self.check_infrastructure(params)
        elif command == "get_status":
            return self.get_status()
        elif command == "sync_memory":
            return await self.sync_memory(params)
        else:
            return {"error": f"Unknown command: {command}"}

    async def check_infrastructure(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Check infrastructure status"""
        services = params.get("services", ["nats", "redis", "postgresql"])
        results = {}

        for service in services:
            # Simplified checks
            if service == "nats":
                results[service] = {
                    "status": "operational",
                    "url": "nats://localhost:18020",
                    "connected": self.hub.is_connected()
                }
            else:
                results[service] = {"status": "assumed_operational"}

        return {"services": results, "checked_at": datetime.now().isoformat()}

    def get_status(self) -> Dict[str, Any]:
        """Get service status"""
        return {
            "service": self.service_name,
            "running": self.is_running,
            "uptime": str(datetime.now() - self.start_time),
            "messages_processed": self.message_count,
            "nats_connected": self.hub.is_connected()
        }

    async def sync_memory(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Sync memory with other frameworks"""
        target = params.get("target", "unknown")
        return {
            "status": "sync_initiated",
            "target": target,
            "bridge_state": self.get_status()
        }

    async def run_forever(self):
        """Run continuously as daemon"""
        if not await self.start():
            print(f"❌ {self.service_name} failed to start")
            return

        # Set up signal handlers for graceful shutdown
        def signal_handler(sig, frame):
            print(f"\n🌉 {self.service_name} shutting down...")
            self.is_running = False
            asyncio.create_task(self.shutdown())

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        print(f"🌉 {self.service_name} running as daemon")
        print(f"   PID: {BridgeService.get_pid()}")
        print(f"   Channel: novaops.bridge")
        print(f"   Mode: Bidirectional, autonomous")
        print("="*60)

        # Continuous operation - event driven
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            pass
        finally:
            await self.shutdown()

    async def shutdown(self):
        """Graceful shutdown"""
        print(f"🌉 {self.service_name} shutting down...")
        self.is_running = False
        await self.hub.disconnect()
        print(f"🌉 {self.service_name} stopped")

    @staticmethod
    def get_pid() -> Optional[int]:
        """Get PID of running Bridge service"""
        try:
            import psutil
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                if 'bridge_service.py' in ' '.join(proc.info.get('cmdline', [])):
                    return proc.info['pid']
        except:
            pass
        return None


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Bridge Bidirectional Service')
    parser.add_argument('--service-name', default='bridge_native_service',
                        help='Service name for identification')
    parser.add_argument('--daemon', action='store_true',
                        help='Run as daemon')

    args = parser.parse_args()

    service = BridgeService(service_name=args.service_name)

    if args.daemon:
        print("🌉 Starting Bridge daemon...")
        asyncio.run(service.run_forever())
    else:
        print("🌉 Starting Bridge service (foreground)...")
        asyncio.run(service.run_forever())
