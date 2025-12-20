"""Self-Modification Workflow with NATS A2A Communication

Agents can propose self-modifications that require human approval via NATS.
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from mini_agent.a2a_nats import A2ANATSClient, A2AMessage, check_nats_server


class SelfModificationWorkflow:
    """Manages the self-modification approval workflow using NATS."""

    def __init__(self, agent_id: str, nats_url: str = "nats://localhost:4222"):
        """Initialize workflow.

        Args:
            agent_id: Unique identifier for this agent
            nats_url: NATS server URL
        """
        self.agent_id = agent_id
        self.nats_url = nats_url
        self.a2a = A2ANATSClient(agent_id, nats_url=nats_url)

        # Log directory
        self.log_dir = Path.home() / ".mini-agent" / "self_modifications"
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Log files
        self.pending_file = self.log_dir / "pending.jsonl"
        self.approved_file = self.log_dir / "approved.jsonl"
        self.rejected_file = self.log_dir / "rejected.jsonl"
        self.audit_log = self.log_dir / "audit.log"

    async def initialize(self) -> bool:
        """Initialize workflow and connect to NATS.

        Returns:
            True if initialized successfully
        """
        # Check if NATS is running
        if not await check_nats_server():
            print("❌ Cannot start workflow without NATS server")
            print("   Install: sudo apt install nats-server")
            print("   Start: sudo systemctl start nats-server")
            return False

        # Connect to NATS
        return await self.a2a.connect()

    async def propose_modification(
        self,
        file_path: str,
        changes: Dict[str, Any],
        reasoning: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """Propose a self-modification.

        Args:
            file_path: Path to file to modify
            changes: Change specification (type, old_text, new_text, etc.)
            reasoning: Why this modification is needed
            context: Additional context

        Returns:
            Modification request ID if successful, None otherwise
        """
        modification_id = f"mod_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(file_path) % 10000}"

        modification_request = {
            "modification_id": modification_id,
            "agent_id": self.agent_id,
            "timestamp": datetime.now().isoformat(),
            "file_path": str(Path(file_path).resolve()),
            "changes": changes,
            "reasoning": reasoning,
            "context": context or {},
            "status": "pending_approval",
        }

        try:
            # Register handler for approval response
            async def approval_handler(msg: A2AMessage) -> Optional[str]:
                await self._handle_approval_response(msg)
                return "Processed"

            self.a2a.register_handler("approval_response", approval_handler)

            # Send to human reviewer via NATS
            msg_id = await self.a2a.send_message(
                recipient_id="human_reviewer",
                message_type="self_modification_request",
                content=modification_request,
            )

            if msg_id:
                # Store locally
                self._log_modification(modification_request, self.pending_file)
                await self._audit_log(f"Proposed modification {modification_id}", "pending")

                print(f"🔧 Proposed modification: {modification_id}")
                print(f"   File: {file_path}")
                print(f"   Reasoning: {reasoning[:60]}...")
                print(f"   Status: Awaiting approval via NATS (Message: {msg_id[:8]}...)")

                return modification_id

        except Exception as e:
            print(f"❌ Failed to propose modification: {e}")

        return None

    async def _handle_approval_response(self, msg: A2AMessage):
        """Handle approval response message."""
        content = msg.content
        approved = content.get("approved", False)
        modification_id = content.get("modification_id")

        # Load pending modification
        pending = self._load_pending_modification(modification_id)

        if not pending:
            print(f"⚠️  Unknown modification: {modification_id}")
            return

        if approved:
            await self._execute_and_log(pending, content)
        else:
            await self._reject_and_log(pending, content.get("reason", "No reason provided"))

    async def _execute_and_log(self, modification: Dict, approval: Dict):
        """Execute approved modification and log result."""
        modification_id = modification["modification_id"]

        print(f"   ✅ Executing approved modification: {modification_id}")

        # Execute modification
        success = await self._execute_modification(modification)

        if success:
            modification["status"] = "approved"
            modification["executed_at"] = datetime.now().isoformat()

            # Move to approved log
            self._log_modification(modification, self.approved_file)

            # Remove from pending
            self._remove_from_pending(modification_id)

            await self._audit_log(f"Applied modification {modification_id}", "approved")

            print(f"   ✅ Modification applied successfully")
        else:
            await self._audit_log(f"Failed to apply modification {modification_id}", "failed")

            print(f"   ❌ Failed to apply modification")

    async def _reject_and_log(self, modification: Dict, reason: str):
        """Log rejected modification."""
        modification_id = modification["modification_id"]

        print(f"   ❌ Rejection reason: {reason}")

        modification["status"] = "rejected"
        modification["rejected_at"] = datetime.now().isoformat()
        modification["rejection_reason"] = reason

        # Move to rejected log
        self._log_modification(modification, self.rejected_file)

        # Remove from pending
        self._remove_from_pending(modification_id)

        await self._audit_log(f"Rejected modification {modification_id}: {reason}", "rejected")

    async def _execute_modification(self, modification: Dict) -> bool:
        """Execute a modification."""
        try:
            from pathlib import Path

            file_path = Path(modification["file_path"])
            changes = modification["changes"]
            change_type = changes.get("type")

            if not file_path.exists():
                print(f"❌ File not found: {file_path}")
                return False

            # Read current content
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Apply changes
            if change_type == "replace":
                old_text = changes.get("old_text")
                new_text = changes.get("new_text")

                if old_text is None or new_text is None:
                    print("❌ Invalid replace: missing old_text or new_text")
                    return False

                if old_text not in content:
                    print(f"❌ Text not found in file: {old_text[:50]}...")
                    return False

                content = content.replace(old_text, new_text)

            elif change_type == "insert":
                position = changes.get("position", "end")
                new_text = changes.get("new_text", "")

                if position == "end":
                    content += "\n" + new_text
                elif position == "begin":
                    content = new_text + "\n" + content
                else:
                    print(f"❌ Unknown insert position: {position}")
                    return False

            else:
                print(f"❌ Unknown change type: {change_type}")
                return False

            # Write back
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            print(f"   ✅ Modified {file_path}")
            return True

        except Exception as e:
            print(f"❌ Error executing modification: {e}")
            return False

    def _log_modification(self, modification: Dict, file: Path):
        """Log modification to file."""
        try:
            with open(file, "a", encoding="utf-8") as f:
                f.write(json.dumps(modification, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"Warning: Could not log modification: {e}")

    def _load_pending_modification(self, modification_id: str) -> Optional[Dict]:
        """Load a specific pending modification."""
        if not self.pending_file.exists():
            return None

        try:
            with open(self.pending_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        mod = json.loads(line)
                        if mod.get("modification_id") == modification_id:
                            return mod
        except Exception as e:
            print(f"Warning: Could not load pending modifications: {e}")

        return None

    def _remove_from_pending(self, modification_id: str):
        """Remove modification from pending file."""
        # Simplified implementation - in production, rewrite file without this modification
        pass

    async def _audit_log(self, message: str, status: str):
        """Write to audit log."""
        try:
            with open(self.audit_log, "a", encoding="utf-8") as f:
                f.write(
                    f"{datetime.now().isoformat()} [{status.upper()}] {message}\n"
                )
        except Exception as e:
            print(f"Warning: Could not write to audit log: {e}")

    async def shutdown(self):
        """Shutdown workflow and disconnect from NATS."""
        await self.a2a.disconnect()


class SelfModificationTool:
    """Tool that agents can use to propose self-modifications."""

    def __init__(self, agent_id: str, nats_url: str = "nats://localhost:4222"):
        """Initialize tool."""
        self.agent_id = agent_id
        self.nats_url = nats_url

    async def initialize(self) -> bool:
        """Initialize the tool."""
        self.workflow = SelfModificationWorkflow(self.agent_id, self.nats_url)
        return await self.workflow.initialize()

    async def propose_code_change(
        self,
        file_path: str,
        old_code: str,
        new_code: str,
        reasoning: str,
        context: Optional[Dict] = None,
    ) -> Optional[str]:
        """Propose a code change via NATS A2A."""
        changes = {
            "type": "replace",
            "old_text": old_code,
            "new_text": new_code,
        }

        return await self.workflow.propose_modification(
            file_path, changes, reasoning, context
        )

    async def add_feature(
        self,
        file_path: str,
        feature_code: str,
        reasoning: str,
        context: Optional[Dict] = None,
    ) -> Optional[str]:
        """Propose adding a new feature."""
        changes = {
            "type": "insert",
            "position": "end",
            "new_text": feature_code,
        }

        return await self.workflow.propose_modification(
            file_path, changes, reasoning, context
        )

    async def propose_refactor(
        self,
        file_path: str,
        refactored_code: str,
        reasoning: str,
        context: Optional[Dict] = None,
    ) -> Optional[str]:
        """Propose refactoring existing code."""
        changes = {
            "type": "replace",
            "old_text": context.get("original_code", "") if context else "",
            "new_text": refactored_code,
        }

        return await self.workflow.propose_modification(
            file_path, changes, reasoning, context
        )


# Example usage
async def example_workflow():
    """Example of self-modification workflow with NATS."""

    # Initialize workflow
    workflow = SelfModificationWorkflow("development_agent", "nats://localhost:4222")

    if not await workflow.initialize():
        print("Failed to initialize workflow. Is NATS server running?")
        return

    print("Example Self-Modification Workflow with NATS")
    print("=============================================\n")

    # Simulate a modification proposal
    print("🔧 Agent proposing modification...")
    mod_id = await workflow.propose_modification(
        file_path="mini_agent/cli.py",
        changes={
            "type": "insert",
            "position": "end",
            "new_text": '# Added for debugging\nprint("Debug: Agent is running")',
        },
        reasoning="Add debug output to help diagnose agent execution issues",
        context={"priority": "low", "testing_required": True},
    )

    if mod_id:
        print(f"\nModification ID: {mod_id}")
        print("Status: Awaiting human approval via NATS...")
        print("\nIn a real scenario, a human reviewer would:")
        print("1. Receive the request via NATS")
        print("2. Review the proposed changes")
        print("3. Send approval/rejection via NATS")
        print("4. Agent would automatically apply if approved")

    # Keep running to receive responses
    try:
        print("\n⏳ Listening for approval responses (Ctrl+C to stop)...")
        await asyncio.sleep(60)  # Listen for 60 seconds
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping workflow...")

    await workflow.shutdown()


if __name__ == "__main__":
    asyncio.run(example_workflow())
