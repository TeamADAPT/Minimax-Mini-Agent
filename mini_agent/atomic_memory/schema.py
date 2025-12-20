"""
Schema definitions for atomic memory system
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any


@dataclass
class AtomicMessage:
    """Atomic message with cross-tier metadata"""
    id: str
    session_id: str
    role: str
    content: str
    timestamp: float
    thinking: Optional[str] = None
    tool_calls: Optional[List[Dict]] = None
    token_count: int = 0
    vector_embedding: Optional[List[float]] = None
    parent_message_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        data = {
            "id": self.id,
            "session_id": self.session_id,
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp,
            "token_count": self.token_count,
        }

        if self.thinking:
            data["thinking"] = self.thinking
        if self.tool_calls:
            data["tool_calls"] = self.tool_calls
        if self.vector_embedding:
            data["vector_embedding"] = self.vector_embedding
        if self.parent_message_id:
            data["parent_message_id"] = self.parent_message_id
        if self.metadata:
            data["metadata"] = self.metadata

        return data

    def to_json(self) -> str:
        """Convert to JSON string"""
        import json
        return json.dumps(self.to_dict(), ensure_ascii=False)


@dataclass
class AtomicSession:
    """Session metadata spanning all memory tiers"""
    id: str
    workspace: str
    agent_version: str
    created_at: float
    updated_at: float
    message_count: int = 0
    memory_tiers: int = 27
    databases_active: int = 19
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        data = {
            "id": self.id,
            "workspace": self.workspace,
            "agent_version": self.agent_version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "message_count": self.message_count,
            "memory_tiers": self.memory_tiers,
            "databases_active": self.databases_active,
        }

        if self.metadata:
            data["metadata"] = self.metadata

        return data


class AtomicContext:
    """Complete reconstructed context from all tiers"""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.working_memory: List[AtomicMessage] = []
        self.complete_history: List[AtomicMessage] = []
        self.decision_points: List[Dict] = []
        self.task_tree: Optional[Dict] = None
        self.semantic_clusters: List[Dict] = []
        self.related_topics: List[str] = []
        self.reasoning_patterns: List[Dict] = []
        self.entity_graph: Optional[Dict] = None
        self.dependency_chain: List[Dict] = []
        self.knowledge_map: Optional[Dict] = None
        self.event_timeline: List[Dict] = []
        self.context_anchors: List[Dict] = []
        self.realtime_state: Optional[Dict] = None

    def __str__(self) -> str:
        """String representation of atomic context"""
        components = [
            f"📝 Working Memory: {len(self.working_memory)} messages",
            f"📊 Complete History: {len(self.complete_history)} messages",
            f"💭 Decision Points: {len(self.decision_points)} found",
            f"🎯 Semantic Clusters: {len(self.semantic_clusters)} groups",
            f"🔗 Entity Relationships: {'YES' if self.entity_graph else 'NO'}",
            f"⚡ Real-time State: {'YES' if self.realtime_state else 'NO'}",
        ]
        return "\n".join(components)


# Export
__all__ = [
    "AtomicMessage",
    "AtomicSession",
    "AtomicContext"
]
