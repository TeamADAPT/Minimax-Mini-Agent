"""
Continuous Hydration System

Background thread that persists session state every 5 seconds or 3 messages,
whichever comes first. Provides real-time data durability and crash recovery.
"""

import asyncio
import threading
import time
from typing import Optional, Dict, Any
from pathlib import Path
from datetime import datetime

from mini_agent.atomic_memory.storage import AtomicMultiTierStorage, AtomicMessage
from mini_agent.atomic_memory.session_manager import AtomicSessionManager


class ContinuousHydrator:
    """
    Background hydration engine that continuously persists session state
    to prevent data loss and enable crash recovery.
    """

    def __init__(
        self,
        storage: Optional[AtomicMultiTierStorage] = None,
        interval_seconds: int = 5,
        message_threshold: int = 3,
        checkpoint_dir: str = "/tmp/nova_checkpoints"
    ):
        """
        Initialize continuous hydrator.

        Args:
            storage: AtomicMultiTierStorage instance (will create if None)
            interval_seconds: How often to hydrate (default: 5 seconds)
            message_threshold: Hydrate after this many messages (default: 3)
            checkpoint_dir: Directory to store checkpoint metadata
        """
        self.storage = storage or AtomicMultiTierStorage()
        self.interval_seconds = interval_seconds
        self.message_threshold = message_threshold
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

        # State tracking
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.loop: Optional[asyncio.AbstractEventLoop] = None

        # Session tracking
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.message_counts: Dict[str, int] = {}
        self.last_hydration: Dict[str, float] = {}

        # Statistics
        self.hydration_count = 0
        self.total_messages_processed = 0
        self.start_time: Optional[float] = None

        print(f"🌊 ContinuousHydrator initialized")
        print(f"   Interval: {interval_seconds}s, Threshold: {message_threshold} messages")
        print(f"   Checkpoint dir: {self.checkpoint_dir}")

    def start(self) -> bool:
        """
        Start the background hydration thread.

        Returns:
            bool: True if started successfully, False if already running
        """
        if self.running:
            print("⚠️  ContinuousHydrator already running")
            return False

        print("🚀 Starting ContinuousHydrator background thread...")
        self.running = True
        self.start_time = time.time()

        # Create new event loop for this thread
        self.loop = asyncio.new_event_loop()

        # Start background thread
        self.thread = threading.Thread(
            target=self._run_event_loop,
            args=(self.loop,),
            daemon=True,
            name="ContinuousHydrator"
        )
        self.thread.start()

        print("✅ ContinuousHydrator started successfully")
        return True

    def stop(self) -> bool:
        """
        Stop the background hydration thread gracefully.

        Returns:
            bool: True if stopped successfully, False if not running
        """
        if not self.running:
            print("⚠️  ContinuousHydrator not running")
            return False

        print("🛑 Stopping ContinuousHydrator...")
        self.running = False

        # Stop the event loop
        if self.loop and self.loop.is_running():
            self.loop.call_soon_threadsafe(self.loop.stop)

        # Wait for thread to finish
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5.0)

        print("✅ ContinuousHydrator stopped")
        self._print_statistics()
        return True

    def _run_event_loop(self, loop: asyncio.AbstractEventLoop):
        """Run the asyncio event loop in the background thread."""
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._hydration_loop())
        except Exception as e:
            print(f"❌ ContinuousHydrator event loop error: {e}")
        finally:
            loop.close()

    async def _hydration_loop(self):
        """Main hydration loop that runs in the background thread."""
        print("🌊 Hydration loop started")

        # Initialize storage connection
        await self.storage.initialize()
        print("✅ Storage initialized in hydration thread")

        # Initial hydration
        await self.hydrate_all()

        # Main loop
        while self.running:
            try:
                # Check if any sessions need hydration
                sessions_to_hydrate = self._get_sessions_needing_hydration()

                if sessions_to_hydrate:
                    await self._hydrate_sessions(sessions_to_hydrate)

                # Sleep for interval (with early wake on message threshold)
                await asyncio.sleep(self.interval_seconds)

            except Exception as e:
                print(f"⚠️  Error in hydration loop: {e}")
                # Continue running despite errors
                await asyncio.sleep(5.0)

        print("🌊 Hydration loop stopped")

    def _get_sessions_needing_hydration(self) -> list:
        """
        Determine which sessions need hydration based on time and message count.

        Returns:
            list: Session IDs that need hydration
        """
        current_time = time.time()
        sessions_needing_hydration = []

        for session_id in self.active_sessions:
            last_hydration = self.last_hydration.get(session_id, 0)
            message_count = self.message_counts.get(session_id, 0)

            # Check time-based hydration
            time_since_hydration = current_time - last_hydration
            time_for_hydration = time_since_hydration >= self.interval_seconds

            # Check message-based hydration
            messages_for_hydration = message_count >= self.message_threshold

            if time_for_hydration or messages_for_hydration:
                sessions_needing_hydration.append(session_id)

        return sessions_needing_hydration

    async def _hydrate_sessions(self, session_ids: list):
        """
        Hydrate all specified sessions.

        Args:
            session_ids: List of session IDs to hydrate
        """
        print(f"💾 Hydrating {len(session_ids)} sessions...")

        for session_id in session_ids:
            try:
                await self._hydrate_session(session_id)
            except Exception as e:
                print(f"⚠️  Error hydrating session {session_id}: {e}")

    async def _hydrate_session(self, session_id: str):
        """
        Hydrate a single session's state to all memory tiers.

        Args:
            session_id: Session ID to hydrate
        """
        if session_id not in self.active_sessions:
            print(f"⚠️  Session {session_id} not found in active sessions")
            return

        session_data = self.active_sessions[session_id]
        messages = session_data.get("messages", [])

        if not messages:
            # Nothing to hydrate
            return

        # Store each message atomically
        stored_count = 0
        for message_data in messages:
            try:
                message = AtomicMessage(**message_data)
                success = await self.storage.store_atomically(message)
                if success:
                    stored_count += 1
            except Exception as e:
                print(f"⚠️  Error storing message for session {session_id}: {e}")

        # Update hydration timestamp and reset message count
        self.last_hydration[session_id] = time.time()
        self.message_counts[session_id] = 0
        self.hydration_count += 1

        print(f"  ✅ Session {session_id[:8]}: {stored_count} messages hydrated")

    def register_session(self, session_id: str, session_data: Dict[str, Any]):
        """
        Register a new session for continuous hydration.

        Args:
            session_id: Unique session identifier
            session_data: Initial session data
        """
        self.active_sessions[session_id] = session_data.copy()
        self.message_counts[session_id] = 0
        self.last_hydration[session_id] = time.time()
        print(f"📋 Registered session {session_id[:8]} for hydration")

    def unregister_session(self, session_id: str):
        """
        Unregister a session from continuous hydration.

        Args:
            session_id: Session ID to unregister
        """
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
        if session_id in self.message_counts:
            del self.message_counts[session_id]
        if session_id in self.last_hydration:
            del self.last_hydration[session_id]
        print(f"📋 Unregistered session {session_id[:8]} from hydration")

    def add_message(self, session_id: str, message: Dict[str, Any]):
        """
        Add a message to a session's message queue.

        Args:
            session_id: Session ID
            message: Message dictionary to add
        """
        if session_id not in self.active_sessions:
            print(f"⚠️  Session {session_id[:8]} not registered for hydration")
            return

        if "messages" not in self.active_sessions[session_id]:
            self.active_sessions[session_id]["messages"] = []

        self.active_sessions[session_id]["messages"].append(message)
        self.message_counts[session_id] = self.message_counts.get(session_id, 0) + 1
        self.total_messages_processed += 1

    async def hydrate_now(self, session_id: Optional[str] = None):
        """
        Force immediate hydration of a session or all sessions.

        Args:
            session_id: Specific session to hydrate, or None for all
        """
        if session_id:
            session_ids = [session_id]
        else:
            session_ids = list(self.active_sessions.keys())

        print(f"🚨 Forced hydration of {len(session_ids)} sessions...")
        await self._hydrate_sessions(session_ids)

    def _print_statistics(self):
        """Print hydration statistics."""
        if not self.start_time:
            return

        runtime = time.time() - self.start_time
        print(f"\n📊 ContinuousHydrator Statistics:")
        print(f"   Runtime: {runtime:.1f} seconds")
        print(f"   Total hydrations: {self.hydration_count}")
        print(f"   Total messages: {self.total_messages_processed}")
        print(f"   Active sessions: {len(self.active_sessions)}")
        if runtime > 0:
            print(f"   Hydration rate: {self.hydration_count / runtime:.2f}/sec")
            print(f"   Message rate: {self.total_messages_processed / runtime:.2f}/sec")

    def get_last_checkpoint(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve the last checkpoint for crash recovery.

        Args:
            session_id: Session ID to retrieve checkpoint for

        Returns:
            dict: Checkpoint data or None if not found
        """
        checkpoint_file = self.checkpoint_dir / f"{session_id}.json"

        if not checkpoint_file.exists():
            return None

        try:
            import json
            with open(checkpoint_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  Error reading checkpoint for {session_id[:8]}: {e}")
            return None

    async def create_checkpoint(self, session_id: str):
        """
        Create a checkpoint file for a session.

        Args:
            session_id: Session ID to checkpoint
        """
        if session_id not in self.active_sessions:
            return

        checkpoint_data = {
            "session_id": session_id,
            "timestamp": time.time(),
            "iso_timestamp": datetime.utcnow().isoformat(),
            "message_count": self.message_counts.get(session_id, 0),
            "session_data": self.active_sessions[session_id]
        }

        try:
            import json
            checkpoint_file = self.checkpoint_dir / f"{session_id}.json"
            with open(checkpoint_file, 'w') as f:
                json.dump(checkpoint_data, f, indent=2)
        except Exception as e:
            print(f"⚠️  Error creating checkpoint for {session_id[:8]}: {e}")


# Global hydrator instance for easy access
_hydrator_instance: Optional[ContinuousHydrator] = None


def get_hydrator() -> ContinuousHydrator:
    """Get the global hydrator instance."""
    global _hydrator_instance
    if _hydrator_instance is None:
        _hydrator_instance = ContinuousHydrator()
    return _hydrator_instance


def start_hydrator() -> bool:
    """Start the global hydrator."""
    return get_hydrator().start()


def stop_hydrator() -> bool:
    """Stop the global hydrator."""
    global _hydrator_instance
    if _hydrator_instance:
        return _hydrator_instance.stop()
    return False


# Example usage
if __name__ == "__main__":
    import asyncio

    async def demo():
        # Create and start hydrator
        hydrator = ContinuousHydrator()
        hydrator.start()

        # Register a session
        session_id = "demo_session_001"
        hydrator.register_session(session_id, {
            "workspace": "/adapt/platform/novaops",
            "agent_version": "ta_00009_bridge"
        })

        # Add some messages
        for i in range(5):
            hydrator.add_message(session_id, {
                "id": f"msg_{i}",
                "role": "assistant" if i % 2 == 0 else "user",
                "content": f"Message {i}",
                "timestamp": time.time()
            })
            await asyncio.sleep(1)

        # Force hydration
        await hydrator.hydrate_now(session_id)

        # Stop hydrator
        hydrator.stop()

    asyncio.run(demo())
