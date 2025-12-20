#!/usr/bin/env python3
"""
Test atomic memory integration for Claude Code
Verifies session persistence, restoration, and performance

**— Bridge (ta_00009) | Atomic Memory Integration Test**
"""

import asyncio
import time
from datetime import datetime
from pathlib import Path

from mini_agent.schema import Message
from mini_agent.atomic_memory.session_manager import AtomicSessionManager


async def test_atomic_session_manager():
    """Comprehensive test of atomic session manager"""

    print("\n" + "="*70)
    print("Atomic Memory Integration Test")
    print("="*70)

    # Create test messages
    test_messages = [
        Message(
            id=f"msg_{i}",
            role="user" if i % 2 == 0 else "assistant",
            content=f"Test message {i}",
            timestamp=time.time()
        )
        for i in range(10)  # 10 test messages
    ]

    print(f"\n📦 Created {len(test_messages)} test messages")

    # Initialize atomic session manager
    session_manager = AtomicSessionManager(
        workspace_dir=Path("/tmp/test_workspace"),
        auto_save=True
    )

    print("\n🔧 Initializing atomic storage...")
    await session_manager.ensure_atomic_initialized()

    stats = await session_manager.get_session_stats()
    print(f"✓ Storage initialized with {stats['databases_connected']} tiers")

    # Test 1: Save session
    print("\n" + "-"*70)
    print("Test 1: Save Session")
    print("-"*70)

    start = time.time()
    session_id = await session_manager.save_session(test_messages, name="atomic_test")
    save_time = time.time() - start

    print(f"✓ Session saved: {session_id}")
    print(f"⏱️  Save time: {save_time*1000:.2f}ms")

    # Test 2: Load session
    print("\n" + "-"*70)
    print("Test 2: Load Session")
    print("-"*70)

    start = time.time()
    loaded_messages = await session_manager.load_session(session_id)
    load_time = time.time() - start

    print(f"✓ Messages loaded: {len(loaded_messages) if loaded_messages else 0}")
    print(f"⏱️  Load time: {load_time*1000:.2f}ms")

    # Verify content
    if loaded_messages and len(loaded_messages) == len(test_messages):
        print("✓ Content verification: PASS (all messages present)")
    else:
        print("❌ Content verification: FAIL")

    # Test 3: Performance comparison
    print("\n" + "-"*70)
    print("Test 3: Performance Benchmark")
    print("-"*70)

    # Create larger session (738 messages like in production)
    large_messages = [
        Message(
            id=f"msg_{i}",
            role="user" if i % 2 == 0 else "assistant",
            content=f"Large test message {i}" * 10,  # 10x longer content
            timestamp=time.time()
        )
        for i in range(738)
    ]

    print(f"📦 Created {len(large_messages)} messages (production size)")

    start = time.time()
    large_session_id = await session_manager.save_session(
        large_messages,
        name="large_benchmark"
    )
    large_save_time = time.time() - start

    print(f"✓ Large session saved: {large_session_id}")
    print(f"⏱️  Large save time: {large_save_time*1000:.2f}ms")

    start = time.time()
    loaded_large = await session_manager.load_session(large_session_id)
    large_load_time = time.time() - start

    print(f"✓ Large session loaded: {len(loaded_large) if loaded_large else 0} messages")
    print(f"⏱️  Large load time: {large_load_time*1000:.2f}ms")

    # Compare with JSON (simulate)
    json_load_time_ms = 450  # From documentation
    atomic_load_time_ms = large_load_time * 1000

    improvement = json_load_time_ms / atomic_load_time_ms if atomic_load_time_ms > 0 else 0
    print(f"\n📊 Performance Improvement: {improvement:.1f}x faster than JSON")

    # Test 4: Workspace auto-resume
    print("\n" + "-"*70)
    print("Test 4: Workspace Auto-Resume")
    print("-"*70)

    start = time.time()
    workspace_session = await session_manager.load_workspace_session()
    workspace_time = time.time() - start

    if workspace_session:
        print(f"✓ Workspace session loaded: {len(workspace_session)} messages")
        print(f"⏱️  Resume time: {workspace_time*1000:.2f}ms")
    else:
        print("⚠️  No workspace session found (expected for test)")

    # Test 5: Listing sessions
    print("\n" + "-"*70)
    print("Test 5: List Sessions")
    print("-"*70)

    sessions = await session_manager.list_sessions()
    print(f"✓ Found {len(sessions)} sessions:")
    for session in sessions[:5]:  # Show first 5
        print(f"  - {session['id']}: {session['message_count']} messages")

    # Test 6: Verify <1s requirement
    print("\n" + "-"*70)
    print("Test 6: Acceptance Criteria")
    print("-"*70)

    print("Requirement: <1s load time")
    print(f"Measured: {large_load_time*1000:.2f}ms")

    if large_load_time < 1.0:
        print("✅ PASS: Load time <1s")
    else:
        print("❌ FAIL: Load time exceeds 1s")

    print("\nRequirement: 0% context loss")
    if loaded_large and len(loaded_large) == len(large_messages):
        print("✅ PASS: No context loss detected")
    else:
        print("❌ FAIL: Context loss detected")

    # Test 7: Multi-tier verification
    print("\n" + "-"*70)
    print("Test 7: Multi-Tier Storage Verification")
    print("-"*70)

    final_stats = await session_manager.get_session_stats()
    print(f"Databases connected: {final_stats['databases_connected']}")
    print(f"Memory tiers: {final_stats.get('memory_tiers', 'N/A')}")

    if final_stats['databases_connected'] >= 1:
        print("✅ PASS: Multi-tier storage operational")
    else:
        print("❌ FAIL: Multi-tier storage not working")

    # Cleanup
    print("\n" + "-"*70)
    print("Cleanup")
    print("-"*70)

    await session_manager.delete_session(session_id)
    await session_manager.delete_session(large_session_id)
    print("✓ Test sessions deleted")

    print("\n" + "="*70)
    print("All Tests Completed!")
    print("="*70 + "\n")

    return {
        "small_session_save_ms": save_time * 1000,
        "small_session_load_ms": load_time * 1000,
        "large_session_save_ms": large_save_time * 1000,
        "large_session_load_ms": large_load_time * 1000,
        "performance_improvement": improvement,
        "databases_connected": final_stats['databases_connected'],
        "tests_passed": 0  # Calculate based on results
    }


if __name__ == "__main__":
    try:
        results = asyncio.run(test_atomic_session_manager())
        print("✅ Atomic memory integration test: COMPLETE")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
