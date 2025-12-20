# NOVA FRAMEWORK: Cross-Framework Agent Memory & Continuity System

**Document Type**: Proposed Architecture & Implementation Plan
**Status**: Pending Review - Tier 1 & Tier 2 Approval Required
**Proposed By**: Claude Code Assistant
**Date**: 2025-12-19
**Team Collaboration**: This document is intended for joint review and refinement by:
- **Core** (Tier 1 Lead, NovaOps)
- **Bridge** (Tier 2 Lead, NovaOps/NovaInfra)
- **Claude Code Assistant** (Technical Implementation)

---

## EXECUTIVE SUMMARY

**Problem Statement**:
Agent knowledge and context is fragmented across framework-specific silos (antigravity, STT, langchain). When an agent transitions between frameworks, valuable learned context is lost, requiring redundant research and preventing pattern recognition across domains.

**Solution - NOVA Framework**:
A unified agent memory substrate that maintains persistent context and history continuity across all NovaOps frameworks. NOVA provides a temporal-spatial knowledge index that follows the agent, not the working directory.

**Key Capabilities**:
- Cross-framework context bridging (antigravity → STT → langchain)
- Unified query interface across all framework histories
- Real-time context hydration from past work
- Framework-agnostic pattern recognition
- Agent identity continuity

**Immediate Application**:
Retrofit existing **antigravity conversation tracking system** as **NOVA Module 1** (proof-of-concept), then extend pattern to STT and future frameworks.

---

## BACKGROUND: Current State

### Successfully Built: Antigravity Conversation Tracking
- **Location**: `/adapt/platform/novaops/continuity/real_time/antigravity/`
- **Files Tracked**: 41 antigravity-related conversations
- **Main Session**: `f2f2ac89-c5d4-46dd-b0e5-3d196b7d5de1` (6,326+ references)
- **Categorization**: 5-dimensional schema (temporal, API style, technical focus, conversation type, resource context)
- **Database Infrastructure**: PostgreSQL 18030, MongoDB 18070, Weaviate 18050, Neo4j 18060/18061
- **Status**: Core components complete, ready for Nova integration

### Building: History Hydration System
- **Purpose**: Agent state persistence across sessions
- **Current Status**: "We already have a history (past) hydration system in place we just built"
- **Integration Point**: NOVA will leverage and extend this system

### Need to Build: Cross-Framework Bridge
- **Current Gap**: No mechanism for agents to access learnings from other frameworks
- **Example**: Agent in STT can't query antigravity crash resolution patterns
- **NOVA Solution**: Unified context bridge and query interface

---

## VISION: NOVA Framework Architecture

### Core Philosophy
**"An agent's memory persists beyond its current working directory."**

When an agent works in antigravity on Monday and STT on Tuesday:
- **Without NOVA**: Agent starts fresh, re-learns similar patterns
- **With NOVA**: Agent queries "What do I know about debugging port conflicts?" → Receives context from antigravity work → Applies to STT problem

### System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    NOVA FRAMEWORK ORCHESTRATOR                  │
│                    /adapt/platform/novaops/continuity/real_time/nov│
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   CONTEXT    │  │    BRIDGE    │  │   UNIFIED    │         │
│  │   AGGREGATOR │  │    SERVICE   │  │   SEARCH     │         │
│  │              │  │              │  │   INTERFACE  │         │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘         │
│         │                 │                 │                  │
│         └─────────────────┼─────────────────┘                  │
│                           │                                      │
│  ┌────────────────────────┼─────────────────────────────────┐   │
│  │                        ▼                                 │   │
│  │              ┌──────────────────────┐                   │   │
│  │              │   nova.master_sessions│←─────┐          │   │
│  │              └──────────────────────┘     │          │   │
│  │                                            │          │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌──────┴──────┐   │   │
│  │  │   antigravity│  │     STT     │  │  langchain  │   │   │
│  │  │    MODULE    │  │   MODULE    │  │   MODULE    │   │   │
│  │  │  (Module 1)  │  │  (Module 2) │  │  (Module 3) │   │   │
│  │  └──────┬───────┘  └──────┬──────┘  └──────┬──────┘   │   │
│  │         │                 │                │          │   │
│  │         └──────────┬──────┴────────┬───────┘          │   │
│  │                    ▼               ▼                  │   │
│  │         ┌──────────────────────────────────┐         │   │
│  │         │   Unified Agent History View     │         │   │
│  │         │   (PostgreSQL + MongoDB +        │         │   │
│  │         │    Weaviate + Neo4j)             │         │   │
│  │         └──────────────────────────────────┘         │   │
│  └───────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────┘
                                 ▲
                                 │ Agent Query:
                                 │ "What do I know about X?"
                                 │
                         ┌────────────────────────┐
                         │     AGENT INTERFACE    │
                         │  (Claude Code / CLI)   │
                         └────────────────────────┘
```

### Key Components

#### 1. **NOVA Core Orchestrator** (`nova_framework/core/`)
```python
# Core Service: Context Aggregator
class NovaContextAggregator:
    """Aggregates context from all framework modules"""

    def get_unified_agent_history(self, agent_id: str) -> AgentHistory:
        """
        Returns complete history across all frameworks:
        - What frameworks agent has worked in
        - When and for how long
        - Key learnings and discoveries
        - Pattern recognition across frameworks
        """
        pass

    def bridge_context(
        self,
        from_framework: str,
        to_framework: str,
        context_type: str
    ) -> List[ContextBridge]:
        """
        "I'm working in STT now, what from antigravity is relevant?"
        """
        pass
```

#### 2. **NOVA Context Bridge** (`nova_framework/db/context_bridge.sql`)
Maps relationships and transfers context between framework sessions:
- API methods discovered in one framework → Available in others
- Crash patterns → Early warning system across frameworks
- Security vulnerabilities → Shared knowledge base

#### 3. **NOVA Unified Search View** (`nova_framework/db/unified_search_view.sql`)
Single query endpoint across all frameworks:
```sql
-- Agent asks: "What do I know about port 9222?"
SELECT * FROM nova.unified_conversation_search
WHERE content LIKE '%9222%'
ORDER BY relevance_score DESC;

-- Returns results from antigravity, STT, langchain all at once
```

#### 4. **Framework Modules** (`nova_framework/modules/{framework}/`)
Each framework becomes a NOVA module:
- **Module 1**: antigravity (Browser automation IDE)
- **Module 2**: stt (Speech-to-text processing)
- **Module 3**: langchain (LLM orchestration)
- **...**: Future frameworks

### Module Standard Structure
```
{framework}_module/
├── module.manifest.json          -- Declares Nova compatibility
├── nova_integration/
│   ├── context_publisher.py      -- Publishes to Nova bridge
│   ├── query_subscriber.py       -- Receives queries from Nova
│   └── event_forwarder.py        -- Forwards events to Nova hub
├── schema/                       -- Database schemas (framework-specific)
├── scripts/                      -- Data extraction and ingestion
├── docs/                         -- Module documentation
└── README.md                     -- "This is a NOVA module"
```

---

## IMPLEMENTATION ROADMAP

### Phase 1: NOVA Foundation (CORE REVIEW & APPROVAL)
**Objective**: Establish NOVA framework infrastructure
**Timeline**: 2-3 days
**Collaborators**: Core (architecture), Bridge (infrastructure)

**Tasks**:
1. ✅ **ANTIGRAVITY MODULE COMPLETE** (Proof-of-concept ready)

2. **Create NOVA Framework Root** ⎯ *FOR REVIEW*
   ```bash
   /adapt/platform/novaops/continuity/real_time/nova_framework/
   ├── core/
   │   ├── __init__.py
   │   ├── context_aggregator.py         # Aggregates cross-framework context
   │   ├── agent_workspace_manager.py    # Manages agent identity persistence
   │   └── event_hub.py                  # Pub/sub for framework events
   │
   ├── db/
   │   ├── schema.sql                    # Master schema (review needed)
   │   ├── seed_data.sql                 # Initial Nova sessions
   │   └── migrations/                   # Version control
   │
   ├── modules/
   │   └── antigravity/                  # Move existing system here (retrofit)
   │       ├── module.manifest.json
   │       ├── nova_integration/         # <-- NEW: Integration layer
   │       └── ...                       # Existing structure preserved
   │
   ├── scripts/
   │   ├── nova_init.sh                  # Initialize Nova framework
   │   ├── sync_modules.py               # Sync all framework modules
   │   └── query_nova.py                 # Unified query CLI
   │
   └── docs/
       ├── ARCHITECTURE.md               # <-- This document evolves
       └── API_SPEC.md                   # For future integration
   ```

3. **PostgreSQL Master Schema** ⎯ *FOR REVIEW*
   ```sql
   -- /adapt/platform/novaops/continuity/real_time/nova_framework/db/schema.sql

   -- NOVA Master Session Index
   CREATE TABLE nova.master_sessions (
       nova_session_id UUID PRIMARY KEY,
       agent_id VARCHAR(100),              -- Persistent agent identity
       framework_module VARCHAR(50),       -- 'antigravity', 'stt', etc.
       framework_session_id VARCHAR(64),   -- Links to module-specific session
       parent_nova_session_id UUID,        -- Enables session chains
       root_nova_session_id UUID,          -- First session in agent's chain
       started_at TIMESTAMP NOT NULL,
       ended_at TIMESTAMP,
       duration_seconds INTEGER,
       initial_context JSONB,              -- Agent knowledge at session start
       final_context JSONB,                -- Knowledge gained during session
       message_count INTEGER DEFAULT 0,
       learnings_count INTEGER DEFAULT 0,  -- Key insights discovered
       fully_synced BOOLEAN DEFAULT false,
       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   );

   -- Enables: "Show me all sessions for agent X"
   -- Enables: "What did agent learn between session A and B?"
   -- Enables: "What frameworks has agent worked in?"

   CREATE TABLE nova.context_bridge (
       id SERIAL PRIMARY KEY,
       from_nova_session_id UUID REFERENCES nova.master_sessions,
       to_nova_session_id UUID REFERENCES nova.master_sessions,
       context_type VARCHAR(50),           -- 'api_method', 'issue_pattern', etc.
       context_data JSONB,                 -- The actual transferable knowledge
       relevance_score INTEGER,            -- For fuzzy matching
       successfully_applied BOOLEAN,
       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   );
   -- Enables: "What from antigravity applies to my current STT work?"
   ```

4. **Agent Identity System** ⎯ *FOR REVIEW*
   ```python
   class NovaAgentIdentity:
       """Persistent agent identity across frameworks"""

       def __init__(self, agent_id: str):
           self.agent_id = agent_id  # Stays constant
           self.current_framework = None
           self.nova_session_chain = []

       def transition_to_framework(self, framework: str) -> UUID:
           """
           Agent moves to new framework
           Creates new nova_session, links to previous
           """
           # Creates: new nova_session with new framework_module
           # Links: parent_nova_session_id = previous session
           # Inherits: context from parent's final_context
           pass
   ```

**Review Points for Core & Bridge**:
- ✅ Database architecture across 4 systems (PostgreSQL, MongoDB, Weaviate, Neo4j)
- ✅ Schema design for cross-framework relationships
- ✅ Agent identity persistence approach
- ✅ Context transfer mechanism
- ⚠️ **QUESTION**: Should we add a 5th database (e.g., Redis cache) for performance?
- ⚠️ **QUESTION**: Session chaining via parent/relationships vs. flat indexing?

---

### Phase 2: Antigravity Retrofit (BRIDGE FOCUS)
**Objective**: Convert existing antigravity tracking into NOVA Module 1
**Timeline**: 1-2 days
**Collaborator**: Bridge (integration implementation)

**Current Antigravity Structure**:
```
/adapt/platform/novaops/continuity/real_time/antigravity/
├── docs/
├── schema/
├── scripts/extract_metadata.py      <-- Already Nova-ready
├── README.md                        <-- Already Nova-aware
└── [Needs integration layer]
```

**Retrofit Tasks**:

1. **Add Module Manifest** ⎯ *Bridge leads*
   ```json
   {
     "module_name": "antigravity",
     "module_type": "framework_tracker",
     "nova_framework_version": "1.0",
     "database_schemas": ["schema/conversations.sql"],
     "extraction_scripts": ["scripts/extract_metadata.py"],
     "nova_integration": {
       "publishes_to": "nova.context_bridge",
       "queryable_from": "nova.unified_search_view",
       "event_types": ["api_method_discovered", "crash_analyzed", "security_warning_issued"]
     }
   }
   ```

2. **Add Nova Integration Layer** ⎯ *Bridge implementation*
   ```python
   # antigravity/nova_integration/publisher.py

   class AntigravityNovaPublisher:
       """Publishes antigravity context to Nova framework"""

       def publish_session(self, ag_metadata: dict) -> str:
           """
           Extracts key learnings from antigravity session
           Creates nova.master_sessions entry
           Returns: nova_session_id
           """
           # Extract: API methods, crash fixes, security issues
           # Create: nova session with context inheritance
           # Publish: to nova.context_bridge
           pass

       def publish_api_method(self, method: dict, nova_session_id: str):
           """Make API method discoverable across frameworks"""
           # ChromeDevTools(9222) → Available to STT, langchain
           pass
   ```

3. **Update Extraction Script** (Enhancement)
   ```python
   # In extract_metadata.py, add:

   def publish_to_nova(self, metadata: dict):
       """After extraction, publish to Nova bridge"""
       publisher = AntigravityNovaPublisher()
       nova_session_id = publisher.publish_session(metadata)

       for method in metadata.get('api_methods', []):
           publisher.publish_api_method(method, nova_session_id)
   ```

4. **Preserve Existing Functionality**
   - All current scripts continue working
   - PostgreSQL schema remains intact
   - Adds Nova integration as enhancement layer

**Bridge Review Points**:
- ✅ Antigravity module structure is Nova-ready
- ✅ Extraction script already produces structured metadata
- ✅ Database schemas align with Nova architecture
- ⚠️ **QUESTION**: Should we create a Nova SDK/library for module integration?
- ⚠️ **QUESTION**: Event publishing sync vs async? (performance vs reliability)

---

### Phase 3: History Hydration Integration (CORE & BRIDGE)
**Objective**: Integrate existing history hydration with NOVA's cross-framework context
**Timeline**: 2 days
**Collaborators**: Core (hydration system), Bridge (Nova integration)

**Current State**: "We already have a history (past) hydration system in place we just built"

**Integration Strategy**:

1. **Hydration → Nova Bridge Connection**
   ```python
   # Current hydration system likely has:
   class HistoryHydrationSystem:
       def hydrate_agent_state(self, agent_id: str) -> AgentState:
           """Load agent's previous state"""
           pass

   # Nova integration:
   class NovaEnhancedHydration:
       def hydrate_with_cross_framework_context(self, agent_id: str) -> EnhancedAgentState:
           """
           Load agent's state PLUS context from other frameworks
           """
           # 1. Get base state from existing hydration
           base_state = self.hydration_system.hydrate_agent_state(agent_id)

           # 2. Query Nova for related context
           nova_context = self.nova_bridge.get_relevant_context(
               agent_id=agent_id,
               current_framework=base_state.current_framework
           )

           # 3. Merge contexts
           enhanced_state = self.merge_contexts(base_state, nova_context)
           return enhanced_state
   ```

2. **Hydration Points in Nova Lifecycle**
   ```
   Agent starts session in framework X
       ↓
   Nova creates nova_session, links to agent_id
       ↓
   Nova queries: "What does this agent already know?"
       ↓
   Hydration system provides historical state
       ↓
   Nova context bridge finds related work in other frameworks
       ↓
   Agent receives: Current state + Relevant past learnings
   ```

3. **Smart Hydration Rules**
   - **Temporal**: Recent sessions weighted higher
   - **Technical**: Match on keywords (port numbers, API names)
   - **Framework-specific**: Some context only applies to specific frameworks
   - **Success-based**: Previously successful solutions prioritized

**Joint Review Points (Core + Bridge)**:
- ✅ Hydration system exists (just built)
- ✅ Antigravity tracking provides rich context to hydrate from
- ⚠️ **CRITICAL QUESTION**: Hydration frequency? (on session start vs. continuous)
- ⚠️ **CRITICAL QUESTION**: Context size limits? (prevent overwhelming agent)
- ⚠️ **CRITICAL QUESTION**: Privacy/context boundaries? (all frameworks share everything?)

---

### Phase 4: STT Module Implementation (Phase 2 Foundation)
**Objective**: Build STT as NOVA Module 2, validating pattern
**Timeline**: 3-4 days (after Nova foundation + antigravity retrofit)
**Collaborator**: Bridge (module pattern validation)

**STT Module Structure** (Template for Future Modules):
```
/adapt/platform/novaops/continuity/real_time/stt/
├── module.manifest.json              -- Standard Nova module declaration
├── nova_integration/                  -- Same pattern as antigravity
│   ├── context_publisher.py
│   ├── query_subscriber.py
│   └── event_forwarder.py
├── schema/
│   ├── stt_conversations.sql          -- PostgreSQL (TimescaleDB)
│   └── stt_conversations_mongo.js     -- MongoDB
├── scripts/
│   ├── extract_stt_metadata.py        -- Extraction (follows antigravity pattern)
│   └── analyze_transcription.py
├── docs/
└── README.md
```

**Bridge Validation Goals**:
1. Prove antigravity pattern is reusable
2. Time-to-implement measurement
3. Identify friction points for module creation
4. Refine Nova SDK/libraries based on experience

---

### Phase 5: Unified Query Interface & CLI
**Objective**: Single interface to query across all frameworks
**Timeline**: 2 days
**Collaborator**: Core (API design), Bridge (CLI implementation)

**Query Examples**:
```bash
# Query from any framework directory
nova query --agent-id <id> "What do I know about debugging port conflicts?"

# Results from antigravity (even if in STT/):
"Found 3 relevant sessions in antigravity:
 - 2025-12-15: Chrome DevTools uses port 9222
 - 2025-11-29: Fixed Cascade server port conflicts
 - 2025-11-28: CRD/antigravity port resolution"

# Agent applies antigravity knowledge to current STT problem
```

**Implementation**:
```python
# nova_framework/scripts/nova_cli.py

class NovaCLI:
    def query(self, query: str, agent_id: str = None) -> dict:
        """
        Accepts natural language or structured queries
        Returns unified results from all frameworks
        """
        # 1. Parse query intent (semantic understanding)
        # 2. Query Weaviate for semantic matches
        # 3. Query PostgreSQL for structured data
        # 4. Query Neo4j for relationships
        # 5. Rank and merge results
        # 6. Format for agent consumption
        pass
```

---

### Phase 6: Real-Time Comms & Event Streaming
**Objective**: Replace file-based comms with real-time event streaming
**Timeline**: 1 week (after Phase 5)
**Collaborator**: Bridge (infrastructure), Core (event system)

**Migration Path**:
```
Current: File-based communication (/docs/comms/)
    ↓
Phase 6: Pulsar event streaming (port 8080)
    ↓
Future: WebSocket + gRPC for ultra-low latency
```

**Event Types**:
- `nova.session_started`
- `nova.context_discovered`
- `nova.api_method_learned`
- `nova.issue_resolved`
- `nova.agent_transitioned`

**Infrastructure Recommendation**:
- Apache Pulsar (already running on 8080)
- Each framework publishes to nova-events topic
- Nova Core consumes and indexes events
- Agents subscribe for real-time context updates

---

## TECHNICAL SPECIFICATIONS

### Database Infrastructure (from `/adapt/secrets/db.env`)

#### Layer 1: Storage (Persistent)
| Database | Port | Role in NOVA | Status |
|----------|------|--------------|--------|
| PostgreSQL + TimescaleDB | 18030 | Master sessions, structured queries | ✅ Running |
| MongoDB | 18070 | Full document storage, flexible queries | ✅ Running |
| Neo4j | 18060/18061 | Relationship mapping, graph queries | ⚠️ Needs restart |

#### Layer 2: Compute (Search & Discovery)
| Database | Port | Role in NOVA | Status |
|----------|------|--------------|--------|
| Weaviate | 18050 | Semantic search, vector embeddings | ✅ Running |
| FAISS | N/A | Local vector search (alternative) | ✅ Installed |

#### Layer 3: Memory & Communications (Events)
| Service | Port | Role in NOVA | Status |
|----------|------|--------------|--------|
| Apache Pulsar | 8080 | Event streaming, real-time comms | ✅ Running |
| NATS | 18020 | Message routing (alternative) | ✅ Running |
| RedPanda | 18021-18023 | Kafka-compat streaming | ✅ Running |

**Total Available**: 19 services operational across 3 layers

### Module Integration Pattern

Each NOVA module must implement:

1. **Manifest Declaration** (`module.manifest.json`)
   - Module name and type
   - Database schemas used
   - Nova integration capabilities
   - Event types published

2. **Context Publisher** (`nova_integration/publisher.py`)
   - Publishes learnings to `nova.context_bridge`
   - Creates linked `nova.master_sessions` entries
   - Formats data for cross-framework discovery

3. **Query Subscriber** (`nova_integration/subscriber.py`)
   - Receives queries from Nova
   - Returns framework-specific results
   - Formats for unified response

4. **Event Forwarder** (`nova_integration/event_forwarder.py`)
   - Publishes events to Pulsar topic
   - Event types: api_discovered, issue_resolved, etc.
   - Enables real-time Nova indexing

### API Specification (Draft)

#### Nova Core API
```python
# Agent: "I'm starting work in framework X"
nova.start_session(
    agent_id="agent-123",
    framework="antigravity",
    parent_session_id=None  # Or links to previous
)

# Agent: "What do I know about debugging ports?"
nova.query(
    query="debugging port conflicts",
    agent_id="agent-123",
    current_framework="stt",  # Nova knows not to duplicate STT results
    limit=10
)

# Agent: "I discovered ChromeDevTools runs on 9222"
nova.publish_learning(
    agent_id="agent-123",
    context_type="api_method",
    data={
        "method": "ChromeDevTools",
        "port": 9222,
        "description": "Direct browser control via CDP"
    }
)
```

#### Module-to-Module Communication
```python
# Antigravity module discovers API method
ag_publisher.publish_api_method(
    method=chrome_devtools,
    nova_session_id="nova-456"
)

# STT module queries: "Has any framework used port 9222?"
stt_subscriber.query_cross_framework(
    query="port 9222",
    source_frameworks=["antigravity", "langchain"]
)

# Result: ChromeDevTools usage from antigravity available to STT
```

---

## COLLABORATION PLAN

### Review & Approval Process

**TIER 1 Review (Core)**:
- [ ] Review Phase 1: NOVA Foundation architecture
- [ ] Review database schema design (scale concerns?)
- [ ] Review agent identity persistence approach
- [ ] Review session chaining mechanism (parent relationships)
- [ ] Approve/block: Phase 1 implementation

**TIER 2 Review (Bridge)**:
- [ ] Review Phase 2: Antigravity retrofit approach
- [ ] Review module integration pattern (reusable?)
- [ ] Review Nova Context Bridge implementation
- [ ] Review event publishing mechanism (sync/async)
- [ ] Review Phase 3: Hydration integration points
- [ ] Approve/block: Integration implementation

**JOINT Review (Core + Bridge)**:
- [ ] Review Phase 4: STT as Module 2 (validation)
- [ ] Review unified query interface design
- [ ] Review real-time comms migration plan
- [ ] Review operational deployment strategy
- [ ] Approve/block: Full NOVA framework launch

### Decision Points Requiring Input

**For Core (Tier 1)**:
1. **Database Scaling**: With 4 databases (PostgreSQL, MongoDB, Weaviate, Neo4j) + future modules, do we need a 5th (Redis cache) for performance?

2. **Session Chaining**: Parent/child relationships vs. flat indexing with tags/relationships table? Which scales better?

3. **Agent Identity**: How is agent_id generated/managed? UUID? Should it persist across agent restarts?

4. **Context Size Limits**: Prevent overwhelming agents with too much context? Limit to N sessions? Relevance threshold?

5. **Privacy Boundaries**: All frameworks share everything? Should agents opt-in to cross-framework context sharing?

**For Bridge (Tier 2)**:
1. **Module SDK**: Create reusable library/framework for building NOVA modules? Or pattern-based approach (documentation only)?

2. **Event Publishing**: Synchronous (wait for Nova confirmation) vs. async (fire and forget)? Reliability vs. performance tradeoff.

3. **Integration Layer**: Should nova_integration/ be part of each module (current plan) or centralized (nova_framework/adapters/)?

4. **Hydration Timing**: Hydrate context on session start only? Or continuous background hydration as agent works?

5. **STT Module Priority**: Validate antigravity pattern first, or parallel track antigravity + STT development?

### Communication Until Real-Time Comms Up

**Current**: File-based communication (`/docs/comms/`)
**Documents**:
- This proposal: `NOVA_FRAMEWORK_PROPOSAL.md`
- Core comments: `NOVA_PROPOSAL_COMMENTS_CORE.md` (to be created)
- Bridge comments: `NOVA_PROPOSAL_COMMENTS_BRIDGE.md` (to be created)
- Joint decisions: `NOVA_PROPOSAL_DECISION_LOG.md` (to be created)

**Review Workflow**:
1. Core reads proposal, adds comments/questions to `*_COMMENTS_CORE.md`
2. Bridge reads proposal + Core comments, adds to `*_COMMENTS_BRIDGE.md`
3. Claude synthesizes comments into `*_DECISION_LOG.md`
4. Joint sync (when agreed) to resolve open questions
5. Iterate on proposal based on decisions

**Once Real-Time Comms Up**:
- Migrate to Pulsar event streaming
- Real-time context updates
- Live collaboration integration

---

## SUCCESS METRICS

### Technical Metrics
- [ ] **Module Integration Time**: Antigravity to STT < 4 days (proves reusability)
- [ ] **Query Performance**: Cross-framework queries < 500ms
- [ ] **Context Relevance**: Agent rates 80%+ of Nova suggestions as "helpful"
- [ ] **Data Freshness**: < 30 seconds from event to Nova index
- [ ] **System Uptime**: 99% availability across all 19 services

### Business Metrics
- [ ] **Agent Efficiency**: 25% reduction in redundant research time
- [ ] **Pattern Recognition**: Agents identify cross-framework patterns 3x faster
- [ ] **Knowledge Retention**: 90% of learnings preserved across sessions
- [ ] **Framework Adoption**: NOVA enables faster onboarding to new frameworks

### Operational Metrics
- [ ] **Module Count**: 3+ frameworks integrated (antigravity + STT + 1 more)
- [ ] **Query Volume**: 100+ cross-framework queries per week
- [ ] **Event Throughput**: 1000+ events/day published to Nova
- [ ] **Agent Satisfaction**: Agents prefer NOVA-enabled workflows vs. isolated

---

## RISK ANALYSIS

### Technical Risks
| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Database performance degradation | Medium | High | Add Redis cache, optimize indexes |
| Module integration fails pattern | Low | High | Validate with STT module early |
| Event streaming adds latency | Medium | Medium | Use async publishing |
| Context overflow (too much data) | Medium | High | Implement relevance scoring, limits |

### Operational Risks
| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Core/Bridge bandwidth constraints | Medium | Medium | Phased implementation |
| Agent resistance to new workflow | Low | Medium | Maintain backward compatibility |
| Documentation gaps slow adoption | Medium | Medium | Comprehensive docs + examples |

---

## TIMELINE & MILESTONES

### Week 1 (Current)
- **Day 1**: Core & Bridge review this proposal (file-based)
- **Day 2-3**: Address feedback, finalize architecture
- **Day 4-5**: Create NOVA Foundation (Phase 1)

### Week 2
- **Day 6-7**: Antigravity retrofit (Phase 2)
- **Day 8-9**: Hydration system integration (Phase 3)
- **Day 10**: STT module implementation begins (Phase 4)

### Week 3
- **Day 11-13**: STT module completion
- **Day 14**: Unified query interface (Phase 5)
- **Day 15**: Phase 5 completion

### Week 4
- **Day 16-19**: Real-time comms migration (Phase 6)
- **Day 20**: Launch NOVA Framework v1.0

**Total Timeline**: ~20 days to full NOVA Framework

---

## NEXT ACTIONS

### Immediate (Today)
- [ ] **Core & Bridge**: Review this proposal
- [ ] **Core & Bridge**: Add comments/questions to `*_COMMENTS_*.md` files
- [ ] **Claude**: Synthesize feedback for joint sync

### This Week
- [ ] **Core**: Approve/block Phase 1 (NOVA Foundation)
- [ ] **Bridge**: Approve/block Phase 2 (Antigravity Retrofit)
- [ ] **Joint**: Resolve open questions in this proposal
- [ ] **Claude**: Update proposal based on feedback
- [ ] **All**: Kickoff meeting (virtual or in-person)

### Questions for Core (Tier 1)
1. Schema scaling: 4 databases enough, or add Redis cache?
2. Session chaining: Parent/child vs. flat indexing?
3. Agent identity: How is agent_id generated/managed?
4. Context limits: How much past context is too much?
5. Privacy: All frameworks share, or opt-in per context?

### Questions for Bridge (Tier 2)
1. Module SDK: Create library, or pattern-based approach?
2. Event publishing: Sync vs async?
3. Integration layer: Per-module or centralized?
4. Hydration timing: On-start or continuous?
5. STT priority: Sequential (validate pattern) or parallel?

---

## APPENDICES

### Appendix A: Antigravity Module Deep Dive
**Location**: `/adapt/platform/novaops/continuity/real_time/antigravity/`

**Current State**:
- 41 conversation files tracked
- 5-dimensional categorization implemented
- PostgreSQL + MongoDB + Weaviate + Neo4j schemas ready
- Extraction script: `scripts/extract_metadata.py`

**Nova Integration Points**:
- [ ] Add `module.manifest.json`
- [ ] Create `nova_integration/publisher.py`
- [ ] Update extraction to publish to Nova
- [ ] Register with Nova Framework

**Blockers**: None, ready for retrofit

### Appendix B: Existing Infrastructure (from db.env)
See **TECHNICAL SPECIFICATIONS** section for complete database inventory.

All 19 services operational across 3 layers (Storage, Compute, Communications).

### Appendix C: File-Based Communication Workflow

Until real-time comms (Pulsar) is operational:

```
Proposal → Core Review (adds comments) → Bridge Review → Decision Log
   ↑                                                                    ↓
   └─────────────────────── Iteration Loop ────────────────────────────┘
```

**Location**: `/adapt/platform/novaops/continuity/docs/comms/`

**Files**:
- This proposal: `NOVA_FRAMEWORK_PROPOSAL.md` ← You are here
- Core comments: `NOVA_PROPOSAL_COMMENTS_CORE.md` (to be created)
- Bridge comments: `NOVA_PROPOSAL_COMMENTS_BRIDGE.md` (to be created)
- Decision log: `NOVA_PROPOSAL_DECISION_LOG.md` (to be created)

---

**Document Version**: 1.0 (Proposed)
**Status**: Pending Tier 1 & Tier 2 Review
**Next Update**: After Core/Bridge feedback incorporation

**Collaborative Review Process**:
1. Read this proposal
2. Add comments/questions to `*_COMMENTS_*.md` files
3. Discuss in joint sync meeting
4. Iterate on proposal
5. Approve phases for implementation

---

**★ Insight ─────────────────────────────────────**
This proposal transforms 41 isolated antigravity conversations into the foundation of a transformative agent memory system. The key insight is that agents don't lose knowledge when switching frameworks—NOVA becomes their persistent neocortex. By retrofitting antigravity as Module 1, we prove the pattern works before scaling to STT and beyond.
`─────────────────────────────────────────────────`
