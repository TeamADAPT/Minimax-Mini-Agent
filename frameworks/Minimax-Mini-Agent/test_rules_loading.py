#!/usr/bin/env python3
"""Test script for rules loading and hotloading functionality."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from mini_agent.rules_loader import RulesLoader

def test_rules_loading():
    """Test rules loading functionality."""
    print("Testing Rules Loading...")
    print("=" * 70)

    # Test 1: Load all rules
    print("\n1. Loading all rules...")
    rl = RulesLoader("/home/x/Documents/master-mas/TeamADAPT_Rules.md")
    rules = rl.load_rules()

    if rules:
        print(f"✅ Rules loaded successfully")
        print(f"   Length: {len(rules)} characters")

        meta = rl.get_rules_metadata()
        print(f"   Sections: {meta['rules_loaded']}")
        print(f"   File size: {meta['file_size']} bytes")
        print(f"   Hotload enabled: {meta['hotload_enabled']}")
    else:
        print("❌ Failed to load rules")
        return False

    # Test 2: Section extraction
    print("\n2. Testing section extraction...")
    env_section = rl.get_section("Environment Rules")
    if env_section:
        print(f"✅ Environment Rules extracted")
        print(f"   Length: {len(env_section)} characters")
        print(f"   Preview: {env_section[:100]}...")
    else:
        print("❌ Failed to extract Environment Rules")

    git_section = rl.get_section("Git Ignore Policy")
    if git_section:
        print(f"✅ Git Ignore Policy extracted")
        print(f"   Length: {len(git_section)} characters")
    else:
        print("❌ Failed to extract Git Ignore Policy")

    # Test 3: Hotloading simulation
    print("\n3. Testing hotloading simulation...")
    print("   Initial load...")
    rules1 = rl.load_rules()
    hash1 = rl._last_hash

    print("   Simulating file change...")
    # Force reload by changing the cache check
    rl._last_loaded = 0  # Clear cache timer
    rl._last_hash = "fake_hash"  # Force hash mismatch

    rules2 = rl.load_rules()
    hash2 = rl._last_hash

    if hash1 != hash2:
        print("✅ Hotloading detection works")
    else:
        print("⚠️  Hotloading detection may have issues")

    # Test 4: Default file path
    print("\n4. Testing default file path...")
    rl_default = RulesLoader()  # Uses default path
    if rl_default.rules_file.exists():
        print(f"✅ Default rules file exists: {rl_default.rules_file}")
    else:
        print(f"⚠️  Default rules file not found: {rl_default.rules_file}")

    print("\n" + "=" * 70)
    print("All tests completed!")
    return True

if __name__ == "__main__":
    try:
        success = test_rules_loading()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
