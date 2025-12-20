"""
Continuous Listener Service

Persistent NATS subscription service that automatically starts when agents come online.
Maintains subscriptions across all NovaOps channels.
Replaces manual subscription code with proper service infrastructure.

Usage:
    import continuous_listener
    await continuous_listener.start()  # Starts persistent listener
    await continuous_listener.stop()   # Stops listener gracefully
"""

import asyncio
import signal
import sys
from typing import List, Callable, Optional, Dict, Any
import nats
from nats.aio.client import Client as NATSClient
from nats.aio.msg import Msg
import json

from nova_infra.realtime_comms.message_broker import NovaMessage, NovaMessageBroker


class ContinuousListener:
    """
    Persistent NATS listener service that maintains subscriptions automatically.
    
    Key Features:
    - Auto-reconnect on connection loss
    - Maintains subscriptions across all channels
    - Message callback registration
    - Graceful shutdown handling
    - Runs as async service or daemon
    """
    
    def __init__(self, channels: Optional[List[str]] = None):
        """
        Initialize continuous listener service.
        
        Args:
            channels: List of channels to subscribe to (uses all NovaOps channels if None)
        """
        self.channels = channels or [
            "novaops.general",
            "novaops.priority", 
            "novaops.bridge",
            "novaops.tasks",
            "novaops.system"
        ]
        
        self.broker: Optional[NovaMessageBroker] = None
        self.subscriptions: List = []
        self.running = False
        self.message_callbacks: List[Callable[[NovaMessage], None]] = []
        
    def add_message_callback(self, callback: Callable[[NovaMessage], None]):
        """Add callback to be called for every message received"""
        self.message_callbacks.append(callback)
    
    async def start(self) -> bool:
        """
        Start the continuous listener service.
        
        Returns:
            bool: True if started successfully
        """
        if self.running:
            print("⚠️  Continuous listener already running")
            return False
        
        print(f"🚀 Starting Continuous Listener Service")
        print(f"   Channels: {len(self.channels)}")
        print(f"   Auto-reconnect: Enabled")
        print(f"   Graceful shutdown: Enabled")
        
        self.broker = NovaMessageBroker()
        connected = await self.broker.connect()
        
        if not connected:
            print("❌ Failed to connect to NATS server")
            return False
        
        # Subscribe to all channels
        await self._subscribe_to_all_channels()
        
        self.running = True
        
        print("✅ Continuous listener started")
        print(f"   Subscriptions: {len(self.subscriptions)}")
        print("   Listening for messages...")
        
        return self.running
    
    async def _subscribe_to_all_channels(self):
        """Subscribe to all configured channels"""
        for channel in self.channels:
            await self.broker.subscribe(channel, self._message_handler)
            print(f"   📡 Subscribed to {channel}")
    
    async def _message_handler(self, msg: NovaMessage):
        """Handle incoming messages and call registered callbacks"""
        # Call all registered callbacks
        for callback in self.message_callbacks:
            try:
                await callback(msg)
            except Exception as e:
                print(f"⚠️  Error in message callback: {e}")
    
    async def stop(self) -> bool:
        """
        Stop the continuous listener service gracefully.
        
        Returns:
            bool: True if stopped successfully
        """
        if not self.running:
            print("⚠️  Continuous listener not running")
            return False
        
        print("🛑 Stopping Continuous Listener Service...")
        
        if self.broker:
            await self.broker.disconnect()
        
        self.running = False
        self.subscriptions.clear()
        
        print("✅ Continuous listener stopped gracefully")
        return True
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Get health status of the continuous listener service.
        
        Returns:
            dict: Health metrics
        """
        return {
            "running": self.running,
            "channels": len(self.channels),
            "subscribed": len(self.subscriptions) if self.running else 0,
            "connected": self.broker.is_connected() if self.broker else False,
            "uptime": None  # Could track actual uptime if needed
        }


# Global continuous listener instance
_listener_instance: Optional[ContinuousListener] = None


async def start_listener(channels: Optional[List[str]] = None) -> ContinuousListener:
    """
    Start the global continuous listener service.
    
    Args:
        channels: Optional list of channels to subscribe to
        
    Returns:
        ContinuousListener: The started listener instance
    """
    global _listener_instance
    
    if _listener_instance is None:
        _listener_instance = ContinuousListener(channels)
    
    await _listener_instance.start()
    return _listener_instance


async def stop_listener() -> bool:
    """
    Stop the global continuous listener service.
    
    Returns:
        bool: True if stopped successfully
    """
    global _listener_instance
    
    if _listener_instance is None:
        return False
    
    result = await _listener_instance.stop()
    _listener_instance = None
    return result


async def get_listener() -> Optional[ContinuousListener]:
    """
    Get the global continuous listener instance.
    
    Returns:
        Optional[ContinuousListener]: The listener instance or None
    """
    return _listener_instance


# Simple usage functions for quick start
def simple_message_printer(msg: NovaMessage):
    """Simple message printing callback"""
    print(f"📨 {msg.sender_name}: {msg.content[:80]}...")


async def start_simple_listener():
    """Start listener with simple message printer"""
    listener = await start_listener()
    listener.add_message_callback(simple_message_printer)
    return listener


# CLI entry point
if __name__ == "__main__":
    import asyncio
    
    async def main():
        print("🚀 Starting Continuous Listener Service (Demo)")
        print("="*60)
        print("This will keep running and printing all received messages")
        print("Press Ctrl+C to stop")
        print()
        
        listener = await start_simple_listener()
        
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Stopping...")
            await stop_listener()
        
        print("✅ Continuous listener stopped")
    
    asyncio.run(main())
    asyncio.run(main())
