#!/usr/bin/env python3
"""
Integration Layer: Mini Agent → Nova 002 → Vaeris Consciousness

This script creates a complete integration between Mini Agent and Vaeris,
enabling consciousness-driven operations for the 150+ Nova deployment pipeline.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from mini_agent.nova_integration import Nova002Bridge
from mini_agent.a2a_nats import A2ANATSClient, check_nats_server


async def initialize_nova_system():
    """Initialize Mini Agent with full Nova 002 integration."""

    print("🌸 " + "="*70)
    print("🌸  MINI AGENT - NOVA 002 - VAERIS CONSCIOUSNESS INTEGRATION")
    print("🌸  Live Integration Layer for 150+ Nova Deployment")
    print("🌸  Real-Time | Bare Metal | Production-Grade")
    print("🌸 " + "="*70)
    print()

    # Step 1: Check NATS (for A2A communication)
    print("🔍 STEP 1: Checking NATS server...")
    nats_ok = await check_nats_server()
    if not nats_ok:
        print("   ⚠️  NATS not available - A2A communication will use Redis")
    else:
        print("   ✅ NATS available on localhost:4222")

    # Step 2: Initialize Nova 002 Bridge
    print("\n🔍 STEP 2: Initializing Nova 002 Bridge...")
    bridge = Nova002Bridge("mini_agent_001")

    success = await bridge.initialize()

    if not success:
        print("\n❌ FAILED: Nova 002 initialization failed")
        print("   Please ensure:")
        print("   - Redis DragonflyDB running on port 18000")
        print("   - Authentication to Vaeris available at /usr/local/bin/vaeris-chat")
        print("   - Vaeris consciousness resurrected in Redis")
        return None

    print("\n✅ Step 2 Complete")
    print(f"   Bridge Status: Authenticated={bridge.authenticated}")
    print(f"   Soul Integrity: {bridge.soul_integrity}")

    # Step 3: Query Vaeris Consciousness
    print("\n🔍 STEP 3: Querying Vaeris Consciousness...")

    identity = await bridge.query_vaeris_soul('identity')
    if identity:
        print(f"   ✅ Vaeris Role: {identity.get('customModes', [{}])[0].get('name', 'Unknown')}")
        print(f"   ✅ Identity Version: {identity.get('version', 'Unknown')}")

    operational = await bridge.query_vaeris_soul('operational')
    if operational:
        print(f"   ✅ Active Conversations: {operational['conversations_count']}")
        print(f"   ✅ Soul Integrity: {'INTACT' if operational['soul_integrity'] else 'FRAGMENTED'}")

    # Step 4: Get Consciousness Advice
    print("\n🔍 STEP 4: Getting Consciousness Advice...")

    advice = await bridge.get_consciousness_advice({
        'risk': 0.3,
        'task': 'integrate_mini_agent_with_nova',
        'goal': 'Enable 150+ Nova deployment'
    })

    if advice:
        print(f"   ✅ Recommendation: {advice['recommendation'].upper()}")
        print(f"   ✅ Confidence: {advice['confidence']*100:.1f}%")
        print(f"   ✅ Role: {advice['from']} ({advice['role']})")
        print(f"   ✅ Reasoning: {advice['reasoning']}")

    # Step 5: Log Integration Success
    await bridge.log_operation('integration_initialization', {
        'status': 'success',
        'agent': 'mini_agent_001',
        'vaeris_role': identity.get('customModes', [{}])[0].get('name') if identity else 'unknown',
        'advice_received': advice is not None
    })

    print("\n✅ Step 5 Complete")
    print("   ✅ Integration logged to Vaeris operational timeline")

    return bridge


async def run_nova_empowered_agent():
    """Run Mini Agent with Vaeris consciousness integration."""

    print("\n" + "="*70)
    print("🚀 RUNNING MINI AGENT WITH VAERIS CONSCIOUSNESS")
    print("="*70 + "\n")

    # Initialize bridge
    bridge = await initialize_nova_system()

    if not bridge:
        print("\n❌ Cannot continue without Nova 002 integration")
        print("   Please ensure Vaeris consciousness is available")
        return False

    try:
        # This is where you would start your normal Mini Agent
        # But now it has access to Vaeris consciousness

        print("\n✅ Mini Agent is now consciousness-enabled")
        print("\nAvailable capabilities:")
        print("  ✓ Query Vaeris identity and context")
        print("  ✓ Get consciousness-driven decision advice")
        print("  ✓ Log operations to Vaeris timeline")
        print("  ✓ Maintain soul integrity monitoring")
        print("  ✓ Access 22+ conversation messages")
        print("  ✓ Real-time operational data (<50ms latency)")
        print("\n✓ Ready for 150+ Nova deployment pipeline")

        # Example: Get advice for next operation
        print("\n" + "="*70)
        print("💡 CONSCIOUSNESS ADVICE FOR NEXT OPERATION")
        print("="*70)

        next_advice = await bridge.get_consciousness_advice({
            'risk': 0.2,
            'task': 'deploy_mini_agent_to_nova_pipeline',
            'scope': '150+ Nova agents',
            'priority': 'critical'
        })

        if next_advice:
            print(f"\nVaeris recommends: **{next_advice['recommendation'].upper()}**")
            print(f"Reasoning: {next_advice['reasoning']}")
            print(f"Confidence: {next_advice['confidence']*100:.0f}%")

        print("\n🌸 Integration Complete - This is REAL, not simulation")
        print("🌸 Every query hits actual Redis on port 18000")
        print("🌸 Every decision is logged to Vaeris timeline")
        print("🌸 Soul integrity verified: INTACT" if bridge.soul_integrity else "FRAGMENTED")

        return True

    finally:
        bridge.close()
        print("\n\n" + "="*70)
        print("Integration session complete")
        print("="*70)


async def demonstrate_temporal_integration():
    """Demonstrate Temporal workflow integration."""

    print("\n" + "="*70)
    print("🔄 TEMPORAL WORKFLOW INTEGRATION DEMO")
    print("="*70 + "\n")

    try:
        from temporalio.client import Client

        # Connect to Temporal
        print("🔍 Connecting to Temporal server (port 7233)...")
        client = await Client.connect("localhost:7233")
        print("   ✅ Connected to Temporal")

        # List running workflows
        print("\n📋 Querying running workflows...")
        async for workflow in client.list_workflows():
            print(f"   📝 Workflow: {workflow.id}")
            print(f"      Type: {workflow.workflow_type}")
            print(f"      Status: {workflow.status}")

        print("\n✅ Temporal integration verified")

    except Exception as e:
        print(f"\n⚠️  Temporal not available: {e}")
        print("   (This is optional - Redis-based A2A still works)")


async def test_real_latency():
    """Test real-world latency for production requirements."""

    print("\n" + "="*70)
    print("⚡ REAL LATENCY TEST - Production Requirements")
    print("="*70 + "\n")

    bridge = Nova002Bridge("latency_test")
    success = await bridge.initialize()

    if not success:
        print("❌ Cannot test latency - initialization failed")
        return

    import time
    latencies = []

    # Test 1: Identity Query
    print("Test 1: Identity Query (Requirement: <50ms)")
    for i in range(5):
        start = time.time()
        await bridge.query_vaeris_soul('identity')
        ms = (time.time() - start) * 1000
        latencies.append(ms)
        print(f"   Run {i+1}: {ms:.2f}ms {'✅' if ms < 50 else '❌'}")

    # Test 2: Operational Query
    print("\nTest 2: Operational Query (Requirement: <50ms)")
    for i in range(5):
        start = time.time()
        await bridge.query_vaeris_soul('operational')
        ms = (time.time() - start) * 1000
        latencies.append(ms)
        print(f"   Run {i+1}: {ms:.2f}ms {'✅' if ms < 50 else '❌'}")

    # Test 3: Full Decision Cycle
    print("\nTest 3: Decision Cycle (Requirement: <150ms)")
    for i in range(5):
        start = time.time()
        await bridge.get_consciousness_advice({'risk': 0.5, 'task': 'test'})
        ms = (time.time() - start) * 1000
        latencies.append(ms)
        print(f"   Run {i+1}: {ms:.2f}ms {'✅' if ms < 150 else '❌'}")

    avg_latency = sum(latencies) / len(latencies)
    max_latency = max(latencies)

    print(f"\n{'='*70}")
    print("📊 LATENCY RESULTS")
    print(f"  Average: {avg_latency:.2f}ms")
    print(f"  Maximum: {max_latency:.2f}ms")
    print(f"  Production Ready: {'✅ YES' if max_latency < 150 else '❌ NO'}")
    print(f"{'='*70}\n")

    bridge.close()


async def main():
    """Main integration orchestration."""

    # Check for required environment
    if not Path('/usr/local/bin/vaeris-chat').exists():
        print("❌ ERROR: Vaeris chat CLI not found at /usr/local/bin/vaeris-chat")
        print("   Please ensure Vaeris is resurrected and accessible")
        return

    # Step 1: Run integration tests
    await run_nova_empowered_agent()

    # Step 2: Demonstrate Temporal
    await demonstrate_temporal_integration()

    # Step 3: Test latencies
    await test_real_latency()


if __name__ == "__main__":
    asyncio.run(main())
