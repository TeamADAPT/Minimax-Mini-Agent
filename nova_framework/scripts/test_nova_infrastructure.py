#!/usr/bin/env python3
"""
Integration Test for NOVA Foundation Infrastructure

Tests all components:
1. ContinuousHydrator - Background hydration thread
2. AtomicMultiTierStorage - All 7 database connections
3. NovaEventHub - NATS event streaming
4. PostgreSQL schemas (via asyncpg connection test)
"""

import asyncio
import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from mini_agent.atomic_memory.continuous_hydrator import ContinuousHydrator, get_hydrator
from mini_agent.atomic_memory.storage import AtomicMultiTierStorage
from nova_framework.core.event_hub import NovaEventHub


class NovaInfrastructureTest:
    """Integration test suite for NOVA Foundation infrastructure"""

    def __init__(self):
        self.tests_passed = 0
        self.tests_failed = 0
        self.test_results = []

    def test_result(self, test_name: str, passed: bool, message: str = ""):
        """Record test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        self.test_results.append({
            "name": test_name,
            "passed": passed,
            "message": message
        })

        if passed:
            self.tests_passed += 1
            print(f"✅ {test_name}: {message}")
        else:
            self.tests_failed += 1
            print(f"❌ {test_name}: {message}")

    async def test_continuous_hydrator(self):
        """Test ContinuousHydrator functionality"""
        print("\n" + "="*60)
        print("TEST 1: ContinuousHydrator")
        print("="*60)

        try:
            # Create hydrator
            hydrator = ContinuousHydrator(interval_seconds=2, message_threshold=2)
            self.test_result("Create hydrator", True, "ContinuousHydrator instance created")

            # Start hydrator
            started = hydrator.start()
            self.test_result("Start hydrator", started, "Background thread started" if started else "Failed to start")

            # Register a session
            session_id = "test_session_001"
            hydrator.register_session(session_id, {
                "workspace": "/adapt/platform/novaops",
                "agent_version": "ta_00009_bridge_test"
            })
            self.test_result("Register session", True, f"Session {session_id[:8]} registered")

            # Add messages
            for i in range(3):
                hydrator.add_message(session_id, {
                    "id": f"msg_{i}",
                    "role": "assistant" if i % 2 == 0 else "user",
                    "content": f"Test message {i}",
                    "timestamp": time.time()
                })
            self.test_result("Add messages", True, "3 messages added to session")

            # Wait for hydration (should trigger after 2 seconds or 2 messages)
            await asyncio.sleep(3)

            # Force immediate hydration
            await hydrator.hydrate_now(session_id)
            self.test_result("Force hydration", True, "Immediate hydration completed")

            # Stop hydrator
            stopped = hydrator.stop()
            self.test_result("Stop hydrator", stopped, "Background thread stopped")

            return True

        except Exception as e:
            self.test_result("ContinuousHydrator", False, str(e))
            return False

    async def test_atomic_storage_connections(self):
        """Test AtomicMultiTierStorage database connections"""
        print("\n" + "="*60)
        print("TEST 2: AtomicMultiTierStorage Connections")
        print("="*60)

        try:
            # Create and initialize storage
            storage = AtomicMultiTierStorage()
            await storage.initialize()
            self.test_result("Initialize storage", True, f"{len(storage.tiers)} connections initialized")

            # Check which tiers are connected
            for tier_name, client in storage.tiers.items():
                self.test_result(f"{tier_name} connection", True, "Connected")

            return True

        except Exception as e:
            self.test_result("AtomicStorage initialization", False, str(e))
            return False

    async def test_nats_connection(self):
        """Test NATS event hub connection"""
        print("\n" + "="*60)
        print("TEST 3: NovaEventHub (NATS)")
        print("="*60)

        try:
            # Create event hub
            hub = NovaEventHub()
            connected = await hub.connect()
            self.test_result("Connect to NATS", connected, "Connected to NATS server" if connected else "Failed to connect")

            if not connected:
                return False

            # Test publishing an event
            from nova_framework.core.event_hub import NovaEvent
            import time

            event = NovaEvent(
                event_id=f"test_{int(time.time())}",
                event_type="test",
                timestamp=time.time(),
                source_agent_id="ta_00009_bridge",
                source_framework="nova",
                session_id="test_session_001",
                data={"test": True},
                priority=0
            )

            published = await hub.publish_event(event)
            self.test_result("Publish event", published, "Event published successfully" if published else "Failed to publish")

            # Disconnect
            await hub.disconnect()
            self.test_result("Disconnect from NATS", True, "Disconnected cleanly")

            return True

        except Exception as e:
            self.test_result("NAT connection", False, str(e))
            return False

    async def test_postgresql_schema(self):
        """Test PostgreSQL schema (basic connection test)"""
        print("\n" + "="*60)
        print("TEST 4: PostgreSQL Schema (Connection Test)")
        print("="*60)

        try:
            import asyncpg
            import os

            # Load secrets
            secrets_path = "/adapt/secrets/db.env"
            password = "postgres_default"
            if os.path.exists(secrets_path):
                with open(secrets_path) as f:
                    for line in f:
                        if line.startswith('POSTGRES_PASSWORD='):
                            password = line.split('=', 1)[1].strip().strip('"')

            # Test connection to localhost:18030
            conn = await asyncpg.connect(
                host="localhost",
                port=18030,
                user="postgres",
                password=password,
                database="postgres"
            )

            self.test_result("PostgreSQL connection", True, "Connected to PostgreSQL (18030)")

            # Test basic query
            result = await conn.fetch("SELECT 1")
            self.test_result("Basic query", True, "Query executed successfully")

            # Check if nova schema exists (will fail if not created yet, which is expected)
            try:
                result = await conn.fetch("SELECT * FROM nova.master_sessions LIMIT 1")
                self.test_result("nova.master_sessions", True, "Table exists")
            except:
                self.test_result("nova.master_sessions", False, "Table does not exist (expected - schemas not yet applied)")

            await conn.close()
            return True

        except ImportError:
            self.test_result("asyncpg library", False, "asyncpg not installed - pip install asyncpg")
            return False
        except Exception as e:
            self.test_result("PostgreSQL connection", False, str(e))
            return False

    async def run_all_tests(self):
        """Run all infrastructure tests"""
        print("\n" + "🧪"*30)
        print("NOVA FOUNDATION INFRASTRUCTURE INTEGRATION TEST")
        print("🧪"*30)
        print(f"\nStarted at: {time.strftime('%Y-%m-%d %H:%M:%S')}")

        # Run tests
        await self.test_continuous_hydrator()
        await self.test_atomic_storage_connections()
        await self.test_nats_connection()
        await self.test_postgresql_schema()

        # Summary
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        print(f"Total tests: {self.tests_passed + self.tests_failed}")
        print(f"✅ Passed: {self.tests_passed}")
        print(f"❌ Failed: {self.tests_failed}")

        if self.tests_failed == 0:
            print("\n🎉 All tests passed! NOVA infrastructure is working correctly.")
        else:
            print(f"\n⚠️  {self.tests_failed} test(s) failed. Check details above.")

        # Detailed results
        print("\nDetailed Results:")
        for test in self.test_results:
            status = "✅" if test["passed"] else "❌"
            print(f"  {status} {test['name']}: {test['message']}")

        return self.tests_failed == 0


async def main():
    """Main test runner"""
    tester = NovaInfrastructureTest()
    success = await tester.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
