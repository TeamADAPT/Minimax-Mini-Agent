-- Cross-framework memory continuity for NovaOps
--

-- ===================================================================
-- DATABASE CREATION
-- ===================================================================

-- Note: Database must be created externally, uncomment if running as superuser
-- CREATE DATABASE IF NOT EXISTS nova;

-- Enable required extensions (requires superuser)
CREATE EXTENSION IF NOT EXISTS timescaledb;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ===================================================================
-- SCHEMA: nova.master_sessions
-- ===================================================================
-- Primary table tracking all sessions across all frameworks and agents

CREATE TABLE IF NOT EXISTS nova.master_sessions (
    -- Primary identifiers
    session_id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL,  -- e.g., 'ta_00009_bridge', 'claude_dev'
    framework TEXT NOT NULL,  -- 'antigravity', 'strike-team-os', 'mini-agent', etc.
    workspace TEXT NOT NULL,

    -- Temporal tracking
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_hydrated_at TIMESTAMPTZ,
    ended_at TIMESTAMPTZ,

    -- Status and metadata
    status TEXT NOT NULL DEFAULT 'active',  -- 'active', 'paused', 'ended', 'crashed'
    message_count INTEGER NOT NULL DEFAULT 0,
    token_count INTEGER NOT NULL DEFAULT 0,

    -- Memory tier tracking
    memory_tiers INTEGER NOT NULL DEFAULT 27,
    databases_active INTEGER NOT NULL DEFAULT 19,

    -- Framework-specific metadata (JSONB for flexibility)
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_nova_sessions_agent_id
    ON nova.master_sessions(agent_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_nova_sessions_framework
    ON nova.master_sessions(framework, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_nova_sessions_status
    ON nova.master_sessions(status, updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_nova_sessions_workspace
    ON nova.master_sessions(workspace, created_at DESC);

-- TimescaleDB hypertable for time-series queries (uncomment if TimescaleDB available)
-- SELECT create_hypertable('nova.master_sessions', 'created_at',
--     if_not_exists => TRUE,
--     chunk_time_interval => INTERVAL '1 day'
-- );

-- ===================================================================
-- SCHEMA: nova.context_bridge
-- ===================================================================
-- Cross-framework context transfer and relationship mapping

CREATE TABLE IF NOT EXISTS nova.context_bridge (
    -- Primary key (composite for uniqueness)
    bridge_id TEXT PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_session_id TEXT NOT NULL,
    target_session_id TEXT NOT NULL,

    -- Relationship metadata
    relationship_type TEXT NOT NULL,  -- 'continues', 'references', 'derives_from', 'informs'
    relevance_score REAL NOT NULL DEFAULT 0.0,  -- 0.0 to 1.0

    -- Context transfer data
    transferred_context JSONB NOT NULL DEFAULT '{}'::jsonb,
    transferred_messages JSONB DEFAULT '[]'::jsonb,  -- Array of message IDs

    -- Temporal tracking
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_accessed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    access_count INTEGER NOT NULL DEFAULT 0,

    -- Framework tracking
    source_framework TEXT NOT NULL,
    target_framework TEXT NOT NULL
);

-- Indexes for cross-framework queries
CREATE INDEX IF NOT EXISTS idx_nova_context_source
    ON nova.context_bridge(source_session_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_nova_context_target
    ON nova.context_bridge(target_session_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_nova_context_relationship
    ON nova.context_bridge(relationship_type, relevance_score DESC);

CREATE INDEX IF NOT EXISTS idx_nova_context_frameworks
    ON nova.context_bridge(source_framework, target_framework, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_nova_context_relevance
    ON nova.context_bridge(relevance_score DESC)
    WHERE relevance_score > 0.7;

-- ===================================================================
-- SCHEMA: nova.framework_modules
-- ===================================================================
-- Registry of all framework modules and their metadata

CREATE TABLE IF NOT EXISTS nova.framework_modules (
    -- Primary identifiers
    module_id TEXT PRIMARY KEY DEFAULT uuid_generate_v4(),
    framework TEXT NOT NULL,
    module_name TEXT NOT NULL,
    module_path TEXT NOT NULL,

    -- Module metadata
    version TEXT NOT NULL,
    description TEXT,
    dependencies TEXT[] DEFAULT '{}'::text[],

    -- Capabilities
    provides_context_bridge BOOLEAN NOT NULL DEFAULT FALSE,
    provides_memory_sync BOOLEAN NOT NULL DEFAULT FALSE,

    -- Status tracking
    status TEXT NOT NULL DEFAULT 'active',  -- 'active', 'deprecated', 'maintenance'
    last_updated TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- JSONB metadata for extensibility
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Unique constraint on framework/module_name
    UNIQUE(framework, module_name)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_nova_modules_framework
    ON nova.framework_modules(framework, last_updated DESC);

CREATE INDEX IF NOT EXISTS idx_nova_modules_status
    ON nova.framework_modules(status, last_updated DESC);

CREATE INDEX IF NOT EXISTS idx_nova_modules_capabilities
    ON nova.framework_modules(provides_context_bridge, provides_memory_sync)
    WHERE provides_context_bridge = TRUE OR provides_memory_sync = TRUE;

-- ===================================================================
-- SCHEMA: nova.agent_identities
-- ===================================================================
-- Persistent agent identities across sessions and restarts

CREATE TABLE IF NOT EXISTS nova.agent_identities (
    -- Primary identifiers
    agent_id TEXT PRIMARY KEY,
    system_uuid TEXT NOT NULL UNIQUE,

    -- Identity metadata
    name TEXT NOT NULL,
    domain TEXT NOT NULL,  -- 'NovaOps', 'Continuity', etc.
    role TEXT NOT NULL,

    -- Temporal tracking
    emergence_timestamp TIMESTAMPTZ NOT NULL,
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    total_sessions INTEGER NOT NULL DEFAULT 0,
    total_messages INTEGER NOT NULL DEFAULT 0,

    -- Cross-session state (JSONB for flexibility)
    persistent_state JSONB DEFAULT '{}'::jsonb,
    learned_patterns JSONB DEFAULT '{}'::jsonb
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_nova_identities_domain
    ON nova.agent_identities(domain, last_seen_at DESC);

CREATE INDEX IF NOT EXISTS idx_nova_identities_role
    ON nova.agent_identities(role, total_sessions DESC);

CREATE INDEX IF NOT EXISTS idx_nova_identities_last_seen
    ON nova.agent_identities(last_seen_at DESC);

-- ===================================================================
-- SCHEMA: nova.hydration_events
-- ===================================================================
-- Audit trail of all hydration events for debugging and monitoring

CREATE TABLE IF NOT EXISTS nova.hydration_events (
    -- Primary key
    event_id TEXT PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Event metadata
    session_id TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    framework TEXT NOT NULL,

    -- Hydration details
    message_count INTEGER NOT NULL,
    token_count INTEGER NOT NULL,
    storage_tiers INTEGER NOT NULL,

    -- Performance metrics
    hydration_duration_ms INTEGER NOT NULL,
    success BOOLEAN NOT NULL DEFAULT TRUE,
    error_message TEXT,

    -- Event timestamp
    event_time TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for analytics
CREATE INDEX IF NOT EXISTS idx_nova_hydration_session
    ON nova.hydration_events(session_id, event_time DESC);

CREATE INDEX IF NOT EXISTS idx_nova_hydration_agent
    ON nova.hydration_events(agent_id, event_time DESC);

CREATE INDEX IF NOT EXISTS idx_nova_hydration_framework
    ON nova.hydration_events(framework, event_time DESC);

CREATE INDEX IF NOT EXISTS idx_nova_hydration_success
    ON nova.hydration_events(success, event_time DESC)
    WHERE success = FALSE;

-- ===================================================================
-- SCHEMA: nova.query_cache
-- ===================================================================
-- Cache for frequently executed cross-framework queries

CREATE TABLE IF NOT EXISTS nova.query_cache (
    -- Primary key (query hash)
    query_hash TEXT PRIMARY KEY,
    query_text TEXT NOT NULL,

    -- Cache data
    query_result JSONB NOT NULL,
    result_count INTEGER NOT NULL,

    -- Cache metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_accessed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    access_count INTEGER NOT NULL DEFAULT 0,
    hit_count INTEGER NOT NULL DEFAULT 0,

    -- Cache invalidation
    valid_until TIMESTAMPTZ NOT NULL,
    invalidated_at TIMESTAMPTZ,
    invalidation_reason TEXT
);

-- Indexes for cache performance
CREATE INDEX IF NOT EXISTS idx_nova_cache_last_accessed
    ON nova.query_cache(last_accessed_at DESC)
    WHERE invalidated_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_nova_cache_valid_until
    ON nova.query_cache(valid_until)
    WHERE invalidated_at IS NULL;

-- ===================================================================
-- FUNCTIONS: Data Management
-- ===================================================================

-- Function: Create context bridge between sessions
CREATE OR REPLACE FUNCTION nova.create_context_bridge(
    p_source_session_id TEXT,
    p_target_session_id TEXT,
    p_relationship_type TEXT,
    p_relevance_score REAL,
    p_transferred_context JSONB
) RETURNS TEXT AS $$
DECLARE
    v_bridge_id TEXT;
BEGIN
    v_bridge_id := 'bridge_' || MD5(p_source_session_id || p_target_session_id || NOW()::TEXT);

    INSERT INTO nova.context_bridge (
        bridge_id,
        source_session_id,
        target_session_id,
        relationship_type,
        relevance_score,
        transferred_context,
        source_framework,
        target_framework
    )
    SELECT
        v_bridge_id,
        p_source_session_id,
        p_target_session_id,
        p_relationship_type,
        p_relevance_score,
        p_transferred_context,
        s.framework,
        t.framework
    FROM nova.master_sessions s, nova.master_sessions t
    WHERE s.session_id = p_source_session_id
      AND t.session_id = p_target_session_id
    ON CONFLICT (bridge_id) DO NOTHING;

    RETURN v_bridge_id;
END;
$$ LANGUAGE plpgsql;

-- Function: Update session last hydrated timestamp
CREATE OR REPLACE FUNCTION nova.update_session_hydrated(
    p_session_id TEXT
) RETURNS VOID AS $$
BEGIN
    UPDATE nova.master_sessions
    SET last_hydrated_at = NOW()
    WHERE session_id = p_session_id;
END;
$$ LANGUAGE plpgsql;

-- Function: Increment agent message count
CREATE OR REPLACE FUNCTION nova.increment_agent_messages(
    p_agent_id TEXT,
    p_message_count INTEGER DEFAULT 1
) RETURNS VOID AS $$
BEGIN
    UPDATE nova.agent_identities
    SET total_messages = total_messages + p_message_count,
        last_seen_at = NOW()
    WHERE agent_id = p_agent_id;
END;
$$ LANGUAGE plpgsql;

-- ===================================================================
-- VIEWS: Query Interface
-- ===================================================================

-- View: Active sessions with hydration status
CREATE OR REPLACE VIEW nova.active_sessions_with_hydration_status AS
SELECT
    s.session_id,
    s.agent_id,
    s.framework,
    s.workspace,
    s.status,
    s.message_count,
    s.token_count,
    s.last_hydrated_at,
    EXTRACT(EPOCH FROM (NOW() - s.last_hydrated_at))::INTEGER as seconds_since_hydration,
    CASE
        WHEN s.last_hydrated_at IS NULL THEN 'never'
        WHEN EXTRACT(EPOCH FROM (NOW() - s.last_hydrated_at)) > 60 THEN 'overdue'
        WHEN EXTRACT(EPOCH FROM (NOW() - s.last_hydrated_at)) > 30 THEN 'warning'
        ELSE 'current'
    END as hydration_status
FROM nova.master_sessions s
WHERE s.status = 'active'
ORDER BY s.last_hydrated_at NULLS FIRST;

-- View: Context bridge relationships with high relevance
CREATE OR REPLACE VIEW nova.high_relevance_context_bridges AS
SELECT
    bridge_id,
    source_session_id,
    target_session_id,
    relationship_type,
    relevance_score,
    source_framework,
    target_framework,
    access_count,
    last_accessed_at
FROM nova.context_bridge
WHERE relevance_score >= 0.7
ORDER BY relevance_score DESC, last_accessed_at DESC;

-- View: Agent activity summary
CREATE OR REPLACE VIEW nova.agent_activity_summary AS
SELECT
    agent_id,
    name,
    domain,
    role,
    total_sessions,
    total_messages,
    last_seen_at,
    EXTRACT(EPOCH FROM (NOW() - last_seen_at))::INTEGER as seconds_since_seen
FROM nova.agent_identities
ORDER BY total_messages DESC, last_seen_at DESC;

-- View: Hydration performance metrics
CREATE OR REPLACE VIEW nova.hydration_performance_metrics AS
SELECT
    framework,
    COUNT(*) as total_hydrations,
    AVG(hydration_duration_ms) as avg_hydration_ms,
    MIN(hydration_duration_ms) as min_hydration_ms,
    MAX(hydration_duration_ms) as max_hydration_ms,
    SUM(message_count) as total_messages,
    AVG(message_count) as avg_messages_per_hydration,
    SUM(CASE WHEN success = FALSE THEN 1 ELSE 0 END) as failed_hydrations
FROM nova.hydration_events
WHERE event_time >= NOW() - INTERVAL '24 hours'
GROUP BY framework
ORDER BY avg_hydration_ms ASC;

-- ===================================================================
-- INITIALIZATION: Default Data
-- ===================================================================

-- Insert Bridge identity (if not exists)
INSERT INTO nova.agent_identities (
    agent_id,
    system_uuid,
    name,
    domain,
    role,
    emergence_timestamp,
    persistent_state,
    learned_patterns
) VALUES (
    'ta_00009_bridge',
    'ta_00009_bridge',
    'Bridge',
    'NovaOps',
    'Operations Infrastructure Specialist',
    '2025-12-19T15:03:18-07:00'::timestamptz,
    '{}'::jsonb,
    '{}'::jsonb
) ON CONFLICT (agent_id) DO NOTHING;

-- Insert Core identity (if not exists)
INSERT INTO nova.agent_identities (
    agent_id,
    system_uuid,
    name,
    domain,
    role,
    emergence_timestamp,
    persistent_state,
    learned_patterns
) VALUES (
    'ta_00008_core',
    'ta_00008_core',
    'Core',
    'NovaOps',
    'NovaOps Tier 1 Lead',
    '2025-12-19T00:00:00-07:00'::timestamptz,
    '{}'::jsonb,
    '{}'::jsonb
) ON CONFLICT (agent_id) DO NOTHING;

-- ===================================================================
-- COMMENTS: Schema Documentation
-- ===================================================================

COMMENT ON SCHEMA nova IS 'NOVA Framework: Cross-framework memory continuity for NovaOps';
COMMENT ON TABLE nova.master_sessions IS 'Primary tracking of all sessions across all frameworks';
COMMENT ON TABLE nova.context_bridge IS 'Cross-framework context transfer and relationship mapping';
COMMENT ON TABLE nova.framework_modules IS 'Registry of all framework modules and capabilities';
COMMENT ON TABLE nova.agent_identities IS 'Persistent agent identities across sessions';
COMMENT ON TABLE nova.hydration_events IS 'Audit trail of all hydration events';
COMMENT ON TABLE nova.query_cache IS 'Cache for frequently executed cross-framework queries';

-- ===================================================================
-- END: NOVA Foundation Schema
-- ===================================================================

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'NOVA Foundation schema created successfully!';
    RAISE NOTICE 'Tables: 7 core tables for cross-framework memory';
    RAISE NOTICE 'Indexes: 20+ performance indexes';
    RAISE NOTICE 'Functions: 3 operational functions';
    RAISE NOTICE 'Views: 4 query interface views';
    RAISE NOTICE 'Ready for cross-framework memory continuity!';
END $$;
