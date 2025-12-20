# NovaThreads Implementation Plan - Detailed Technical Execution

**Document**: Implementation Plan for NovaThreads Enhancement
**Based on**: Bridge's Infrastructure Assessment (completed 19:20 MST)
**Timeline**: 4-6 hours to full operational status
**Target**: World's most advanced AI infrastructure

---

## 🎯 EXECUTIVE SUMMARY

**Goal**: Transform Bridge's excellent infrastructure foundation into intelligent communications nervous system

**What Bridge Built**: 2,700 lines of atomic storage foundation
**What We Add**: 1,000+ lines of intelligence layer
**Result**: 3,700+ lines of consciousness-aware infrastructure

**Timeline Breakdown**:
- Phase 1 (Intelligent Relationships): 2 hours → **19:20-21:20 MST**
- Phase 2 (Universal Search): 1.5 hours → **21:20-22:50 MST**  
- Phase 3 (Real-Time Analytics): 1 hour → **22:50-23:50 MST**
- Integration & Testing: 0.5 hour → **23:50-00:20 MST**

---

## 📋 PHASE 1: INTELLIGENT RELATIONSHIPS (2 HOURS)

### Hour 1: Enhanced Database Schemas (19:20-20:20 MST)

**Step 1.1: Enhance existing PostgreSQL schemas** (30 minutes)

File to create: `/adapt/platform/novaops/nova_framework/db/schema_enhancements.sql`

```sql
-- ===================================================================
-- ENHANCEMENT 1: Add threading support to nova.master_sessions
-- ===================================================================

-- Add threading fields to existing table
ALTER TABLE nova.master_sessions
ADD COLUMN IF NOT EXISTS thread_id TEXT,
ADD COLUMN IF NOT EXISTS project_id TEXT,
ADD COLUMN IF NOT EXISTS task_id TEXT,
ADD COLUMN IF NOT EXISTS relationship_context JSONB DEFAULT '{}'::jsonb,
ADD COLUMN IF NOT EXISTS tags TEXT[] DEFAULT '{}'::text[];

-- Create index for thread queries
CREATE INDEX IF NOT EXISTS idx_nova_sessions_thread_id
    ON nova.master_sessions(thread_id, created_at DESC)
    WHERE thread_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_nova_sessions_project_id
    ON nova.master_sessions(project_id, created_at DESC)
    WHERE project_id IS NOT NULL;

-- ===================================================================
-- ENHANCEMENT 2: Message threading table
-- ===================================================================

CREATE TABLE IF NOT EXISTS nova.message_threads (
    thread_id TEXT PRIMARY KEY,
    root_session_id TEXT NOT NULL REFERENCES nova.master_sessions(session_id),
    title TEXT,
    message_count INTEGER DEFAULT 0,
    participants TEXT[] DEFAULT '{}'::text[],
    tags TEXT[] DEFAULT '{}'::text[],
    project_id TEXT,
    last_activity TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Indexes for thread queries
CREATE INDEX IF NOT EXISTS idx_nova_threads_project
    ON nova.message_threads(project_id, last_activity DESC)
    WHERE project_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_nova_threads_participants
    ON nova.message_threads USING GIN(participants);

CREATE INDEX IF NOT EXISTS idx_nova_threads_tags
    ON nova.message_threads USING GIN(tags);

-- ===================================================================
-- ENHANCEMENT 3: Project tracking table
-- ===================================================================

CREATE TABLE IF NOT EXISTS nova.projects (
    project_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    lead_nova_id TEXT NOT NULL,
    team_nova_ids TEXT[] DEFAULT '{}'::text[],
    status TEXT DEFAULT 'active',  -- active, paused, completed, cancelled
    priority INTEGER DEFAULT 3,  -- 1=high, 2=medium, 3=low
    tags TEXT[] DEFAULT '{}'::text[],
    working_directories TEXT[] DEFAULT '{}'::text[],
    related_project_ids TEXT[] DEFAULT '{}'::text[],
    start_date TIMESTAMPTZ DEFAULT NOW(),
    due_date TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Project indexes
CREATE INDEX IF NOT EXISTS idx_nova_projects_status
    ON nova.projects(status, priority DESC, updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_nova_projects_lead
    ON nova.projects(lead_nova_id, status, updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_nova_projects_team
    ON nova.projects USING GIN(team_nova_ids);

-- ===================================================================
-- ENHANCEMENT 4: Task tracking table
-- ===================================================================

CREATE TABLE IF NOT EXISTS nova.tasks (
    task_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES nova.projects(project_id),
    title TEXT NOT NULL,
    description TEXT,
    assignee_nova_id TEXT,
    status TEXT DEFAULT 'todo',  -- todo, in_progress, review, blocked, done
    priority INTEGER DEFAULT 3,  -- 1=high, 2=medium, 3=low
    tags TEXT[] DEFAULT '{}'::text[],
    dependencies TEXT[] DEFAULT '{}'::text[],  -- task IDs this depends on
    estimated_hours INTEGER,
    actual_hours INTEGER,
    due_date TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Task indexes
CREATE INDEX IF NOT EXISTS idx_nova_tasks_project
    ON nova.tasks(project_id, status, priority DESC);

CREATE INDEX IF NOT EXISTS idx_nova_tasks_assignee
    ON nova.tasks(assignee_nova_id, status, priority DESC)
    WHERE assignee_nova_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_nova_tasks_status
    ON nova.tasks(status, priority DESC, due_date NULLS LAST);

-- ===================================================================
-- ENHANCEMENT 5: Entity relationships table
-- ===================================================================

CREATE TABLE IF NOT EXISTS nova.entity_relationships (
    relationship_id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::TEXT,
    from_entity_type TEXT NOT NULL,  -- 'session', 'project', 'task', 'nova'
    from_entity_id TEXT NOT NULL,
    to_entity_type TEXT NOT NULL,
    to_entity_id TEXT NOT NULL,
    relationship_type TEXT NOT NULL,
    strength FLOAT DEFAULT 1.0,
    context JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(from_entity_id, to_entity_id, relationship_type)
);

-- Relationship indexes
CREATE INDEX IF NOT EXISTS idx_nova_rel_from
    ON nova.entity_relationships(from_entity_type, from_entity_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_nova_rel_to
    ON nova.entity_relationships(to_entity_type, to_entity_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_nova_rel_type
    ON nova.entity_relationships(relationship_type, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_nova_rel_strength
    ON nova.entity_relationships(strength DESC, created_at DESC)
    WHERE strength >= 0.7;

-- ===================================================================
-- SUCCESS MESSAGE
-- ===================================================================

DO $$
BEGIN
    RAISE NOTICE '================================';
    RAISE NOTICE 'Schema Enhancements Complete!';
    RAISE NOTICE 'Tables added: 5';
    RAISE NOTICE 'Indexes added: 10+';
    RAISE NOTICE 'Ready for NovaThreads integration';
    RAISE NOTICE '================================';
END $$;

-- Next: Apply with psql -h localhost -p 18030 -f schema_enhancements.sql
