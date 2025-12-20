#!/usr/bin/env python3
"""
Self-Modification Approval Workflow

This demonstrates the self-modification workflow for agents:
1. Agent analyzes its own code
2. Proposes modifications
3. Sends approval request via A2A
4. Human reviews and approves/rejects
5. Agent applies or abandons changes
6. Everything logged for audit
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from mini_agent.a2a_comms import A2AComms, A2AMessage


class SelfModificationWorkflow:
    """Manages the self-modification approval workflow."""

    def __init__(self, agent_id: str):
        """Initialize workflow.

        Args:
            agent_id: Unique identifier for this agent
        """
        self.agent_id = agent_id
        self.a2a = A2AComms(agent_id)
        self.workflow_dir = Path.home() / ".mini-agent" / "self_modifications"
        self.workflow_dir.mkdir(parents=True, exist_ok=True)

        # Store pending modifications
        self.pending_file = self.workflow_dir / "pending.jsonl"
        self.approved_file = self.workflow_dir / "approved.jsonl"
        self.rejected_file = self.workflow_dir / "rejected.jsonl"

    async def propose_modification(
        self,
        file_path: str,
        changes: dict,
        reasoning: str,
        context: dict = None,
    ) -> str:
        """Propose a self-modification.

        Args:
            file_path: Path to file to modify
            changes: Change specification (type, old_text, new_text, etc.)
            reasoning: Why this modification is needed
            context: Additional context

        Returns:
            Modification request ID
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

        # Send via A2A to human admin
        msg_id = self.a2a.send_message(
            recipient_id="human_admin",
            message_type="self_modification_request",
            content=modification_request,
        )

        # Store locally
        self._store_modification(modification_request, self.pending_file)

        print(f"🔧 Self-modification proposed: {modification_id}")
        print(f"   File: {file_path}")
        print(f"   Reasoning: {reasoning[:60]}...")
        print(f"   Awaiting approval via A2A message: {msg_id}")

        return modification_id

    async def review_modifications(self):
        """Review and respond to pending modification approvals."""
        # In a real implementation, this would:
        # 1. Check for incoming A2A approval messages
        # 2. Display modification details to human
        # 3. Get human approval/rejection
        # 4. Send response back via A2A

        print("📋 Reviewing pending self-modifications...")

        pending = self._load_pending_modifications()

        if not pending:
            print("   No pending modifications")
            return

        for mod in pending:
            print(f"\n   Modification ID: {mod['modification_id']}")
            print(f"   File: {mod['file_path']}")
            print(f"   Reasoning: {mod['reasoning']}")
            print(f"   Changes: {mod['changes']}")

            # Simulate human review
            decision = input("\n   Approve? (y/n/s) [y=yes, n=no, s=skip]: ").strip().lower()

            if decision == "y":
                await self._approve_modification(mod)
            elif decision == "n":
                await self._reject_modification(mod, input("   Rejection reason: "))
            else:
                print("   Skipping...")

    async def _approve_modification(self, modification: dict):
        """Approve and apply a modification."""
        modification_id = modification["modification_id"]

        print(f"   ✅ Approving modification: {modification_id}")

        # Send approval via A2A
        self.a2a.send_message(
            recipient_id=modification["agent_id"],
            message_type="approval_response",
            content={
                "approved": True,
                "modification_id": modification_id,
                "reasoning": modification["reasoning"],
                "modification": modification,
            },
        )

        # Update status
        modification["status"] = "approved"
        modification["approved_at"] = datetime.now().isoformat()

        # Move from pending to approved
        self._move_modification(modification, self.pending_file, self.approved_file)

        print(f"   ✅ Sent approval via A2A")

    async def _reject_modification(self, modification: dict, reason: str):
        """Reject a modification."""
        modification_id = modification["modification_id"]

        print(f"   ❌ Rejecting modification: {modification_id}")

        # Send rejection via A2A
        self.a2a.send_message(
            recipient_id=modification["agent_id"],
            message_type="approval_response",
            content={
                "approved": False,
                "modification_id": modification_id,
                "reason": reason,
            },
        )

        # Update status
        modification["status"] = "rejected"
        modification["rejected_at"] = datetime.now().isoformat()
        modification["rejection_reason"] = reason

        # Move from pending to rejected
        self._move_modification(modification, self.pending_file, self.rejected_file)

        print(f"   ❌ Sent rejection via A2A")

    def _store_modification(self, modification: dict, file: Path):
        """Store modification to file."""
        try:
            with open(file, "a", encoding="utf-8") as f:
                f.write(json.dumps(modification, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"Warning: Could not store modification: {e}")

    def _load_pending_modifications(self) -> List[dict]:
        """Load pending modifications."""
        modifications = []
        if not self.pending_file.exists():
            return modifications

        try:
            with open(self.pending_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        modifications.append(json.loads(line))
        except Exception as e:
            print(f"Warning: Could not load pending modifications: {e}")

        return modifications

    def _move_modification(self, modification: dict, from_file: Path, to_file: Path):
        """Move modification from one file to another."""
        # Add to destination
        self._store_modification(modification, to_file)

        # Remove from source (simplified - would need full rewrite in production)
        # For now, we just mark as moved in the workflow


class SelfModificationTool:
    """Tool that agents can use to propose self-modifications."""

    def __init__(self, agent_id: str):
        """Initialize tool."""
        self.agent_id = agent_id
        self.workflow = SelfModificationWorkflow(agent_id)

    def propose_code_change(
        self,
        file_path: str,
        old_code: str,
        new_code: str,
        reasoning: str,
        context: dict = None,
    ) -> str:
        """Propose a code change.

        Args:
            file_path: Path to code file
            old_code: Code to replace
            new_code: New code
            reasoning: Why this change is needed
            context: Additional context

        Returns:
            Modification request ID
        """
        changes = {
            "type": "replace",
            "old_text": old_code,
            "new_text": new_code,
            "language": context.get("language", "python") if context else "python",
        }

        # This would be called from within an agent
        # asyncio.run(self.workflow.propose_modification(file_path, changes, reasoning, context))

        return f"Proposal submitted for {file_path}"

    def add_feature(
        self,
        file_path: str,
        feature_code: str,
        reasoning: str,
        context: dict = None,
    ) -> str:
        """Propose adding a new feature."""
        changes = {
            "type": "insert",
            "position": "end",
            "new_text": feature_code,
            "feature_description": context.get("feature_description") if context else "",
        }

        # asyncio.run(self.workflow.propose_modification(file_path, changes, reasoning, context))

        return f"Feature proposal submitted for {file_path}"

    def propose_refactor(
        self,
        file_path: str,
        refactored_code: str,
        reasoning: str,
        context: dict = None,
    ) -> str:
        """Propose refactoring existing code."""
        changes = {
            "type": "replace",
            "old_text": context.get("original_code", "") if context else "",
            "new_text": refactored_code,
            "refactor_type": context.get("refactor_type", "general") if context else "general",
        }

        # asyncio.run(self.workflow.propose_modification(file_path, changes, reasoning, context))

        return f"Refactor proposal submitted for {file_path}"


# Example usage
async def example_workflow():
    """Example of self-modification workflow."""

    # Initialize workflow
    workflow = SelfModificationWorkflow("development_agent_001")

    print("Example Self-Modification Workflow")
    print("===================================\n")

    # 1. Agent proposes a modification
    modification_id = await workflow.propose_modification(
        file_path="mini_agent/cli.py",
        changes={
            "type": "insert",
            "position": "end",
            "new_text": '# Added by agent for debugging\nprint("Debug: Agent is running")',
        },
        reasoning="Adding debug output to help diagnose agent execution issues",
        context={"priority": "low", "testing_required": True},
    )

    print(f"\nModification ID: {modification_id}\n")

    # 2. Human reviews and decides (via A2A)
    print("Would you like to review pending modifications?")
    review = input("Start review? (y/n): ")

    if review.lower() == "y":
        await workflow.review_modifications()

    # 3. Agent can check status
    print("\nChecking modification status...")
    # In real use, agent would query the response


if __name__ == "__main__":
    asyncio.run(example_workflow())
