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
-- ENHANCEMENT 3: Entity relationships table
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
-- ENHANCEMENT 4: Update function for relationships
-- ===================================================================

CREATE OR REPLACE FUNCTION nova.update_relationship_strength(
    p_from_entity_id TEXT,
    p_to_entity_id TEXT,
    p_relationship_type TEXT,
    p_new_strength FLOAT
) RETURNS VOID AS $$
BEGIN
    UPDATE nova.entity_relationships
    SET strength = p_new_strength,
        context = jsonb_set(context, '{last_updated}', to_jsonb(NOW())),
        updated_at = NOW()
    WHERE from_entity_id = p_from_entity_id
      AND to_entity_id = p_to_entity_id
      AND relationship_type = p_relationship_type;

    IF NOT FOUND THEN
        INSERT INTO nova.entity_relationships (
            from_entity_id,
            to_entity_id,
            relationship_type,
            strength,
            context
        ) VALUES (
            p_from_entity_id,
            p_to_entity_id,
            p_relationship_type,
            p_new_strength,
            jsonb_build_object('created_strength', p_new_strength)
        );
    END IF;
END;
$$ LANGUAGE plpgsql;

-- ===================================================================
-- ENHANCEMENT 5: Create materialized view for active threads
-- ===================================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS nova.active_thread_summary AS
SELECT
    t.thread_id,
    t.title,
    COUNT(DISTINCT s.session_id) as message_count,
    COUNT(DISTINCT t.participants) as participant_count,
    MAX(s.updated_at) as last_activity,
    t.project_id
FROM nova.message_threads t
JOIN nova.master_sessions s ON t.thread_id = s.thread_id
WHERE s.status = 'active'
    AND s.updated_at >= NOW() - INTERVAL '1 hour'
GROUP BY t.thread_id, t.title, t.project_id
ORDER BY last_activity DESC;

CREATE UNIQUE INDEX IF NOT EXISTS idx_active_thread_summary_id
    ON nova.active_thread_summary(thread_id);

-- Refresh every 5 minutes
-- CREATE OR REPLACE RULE refresh_active_threads AS
--     ON SCHEDULE EVERY 5 MINUTES
--     DO REFRESH MATERIALIZED VIEW nova.active_thread_summary;

-- ===================================================================
-- SUCCESS MESSAGE
-- ===================================================================

DO $$
BEGIN
    RAISE NOTICE '================================';
    RAISE NOTICE 'Schema Enhancements Complete!';
    RAISE NOTICE 'Tables added/modified: 5';
    RAISE NOTICE 'Indexes added: 8';
    RAISE NOTICE 'Functions added: 1';
    RAISE NOTICE 'Materialized views: 1';
    RAISE NOTICE 'Ready for NovaThreads integration';
    RAISE NOTICE '================================';
END $$;

-- ===================================================================
-- QUICK REFERENCE: Apply these schemas
-- ===================================================================
-- psql -h localhost -p 18030 -U postgres -d postgres < schema_enhancements.sql
-- psql -h localhost -p 18031 -U postgres -d postgres < schema_enhancements.sql
-- psql -h localhost -p 18032 -U postgres -d postgres < schema_enhancements.sql
