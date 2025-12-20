-- ============================================================================
-- Antigravity Conversation Tracking Database Schema
-- PostgreSQL + TimescaleDB (AI Data Platform)
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS timescaledb;

-- ============================================================================
-- TABLE: antigravity_conversations
-- Primary index of all antigravity-related conversations
-- ============================================================================
CREATE TABLE IF NOT EXISTS antigravity_conversations (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(64) UNIQUE NOT NULL,
    file_path TEXT NOT NULL,

    -- Temporal data
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    duration_minutes NUMERIC(10,2),

    -- Categorization (Five-dimensional system)
    conversation_type VARCHAR(50),
    api_access_style VARCHAR(50)[],  -- Array for multiple styles
    technical_focus TEXT[],
    resource_context VARCHAR(50),

    -- Content metrics
    word_count INTEGER,
    line_count INTEGER,
    message_count INTEGER,
    has_code_examples BOOLEAN DEFAULT false,
    has_scripts BOOLEAN DEFAULT false,
    has_api_endpoints BOOLEAN DEFAULT false,
    has_security_warnings BOOLEAN DEFAULT false,
    security_warning_count INTEGER DEFAULT 0,

    -- Conversation metadata
    parent_session_id VARCHAR(64),
    is_sidechain BOOLEAN DEFAULT false,
    user_type VARCHAR(20),
    version VARCHAR(20),
    git_branch VARCHAR(100),
    slug VARCHAR(100),

    -- Full-text for search optimization
    full_text TSVECTOR,
    summary TEXT,

    -- API methods discovered
    api_methods_count INTEGER DEFAULT 0,

    -- File tracking
    file_size_bytes BIGINT,
    last_accessed TIMESTAMP,
    access_count INTEGER DEFAULT 0,

    -- External references
    raw_content_location TEXT,
    extracted_text_location TEXT,

    -- Ingestion tracking
    ingestion_status VARCHAR(20) DEFAULT 'pending',
    last_ingested TIMESTAMP,
    ingestion_errors TEXT[],

    -- Database metadata
    created_at_db TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at_db TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create TimescaleDB hypertable for time-based queries
SELECT create_hypertable('antigravity_conversations', 'created_at', if_not_exists => true);

-- ============================================================================
-- INDEXES: antigravity_conversations
-- ============================================================================

-- Primary access indexes
CREATE INDEX IF NOT EXISTS idx_antigravity_session_id
    ON antigravity_conversations(session_id);

CREATE INDEX IF NOT EXISTS idx_antigravity_created_at
    ON antigravity_conversations(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_antigravity_updated_at
    ON antigravity_conversations(updated_at DESC);

-- Categorization indexes
CREATE INDEX IF NOT EXISTS idx_antigravity_conversation_type
    ON antigravity_conversations(conversation_type);

CREATE INDEX IF NOT EXISTS idx_antigravity_api_access_style
    ON antigravity_conversations USING GIN(api_access_style);

CREATE INDEX IF NOT EXISTS idx_antigravity_technical_focus
    ON antigravity_conversations USING GIN(technical_focus);

CREATE INDEX IF NOT EXISTS idx_antigravity_resource_context
    ON antigravity_conversations(resource_context);

-- Content search indexes
CREATE INDEX IF NOT EXISTS idx_antigravity_full_text
    ON antigravity_conversations USING GIN(full_text);

CREATE INDEX IF NOT EXISTS idx_antigravity_has_code_examples
    ON antigravity_conversations(has_code_examples) WHERE has_code_examples = true;

CREATE INDEX IF NOT EXISTS idx_antigravity_has_security_warnings
    ON antigravity_conversations(has_security_warnings) WHERE has_security_warnings = true;

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_antigravity_type_created
    ON antigravity_conversations(conversation_type, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_antigravity_style_focus
    ON antigravity_conversations USING GIN(api_access_style, technical_focus);

-- Performance monitoring index
CREATE INDEX IF NOT EXISTS idx_antigravity_ingestion_status
    ON antigravity_conversations(ingestion_status) WHERE ingestion_status != 'completed';

-- ============================================================================
-- TABLE: antigravity_api_methods
-- Individual API methods referenced in conversations
-- ============================================================================
CREATE TABLE IF NOT EXISTS antigravity_api_methods (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER NOT NULL
        REFERENCES antigravity_conversations(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    -- Method identification
    method_name VARCHAR(200) NOT NULL,
    protocol VARCHAR(20),        -- CDP, MCP, REST, WebSocket, Extension, Proxy
    port INTEGER,
    access_level VARCHAR(20),    -- dev_style, internal, proxy, browser_extension

    -- Description and documentation
    description TEXT,
    implementation_notes TEXT,
    security_notes TEXT,
    limitations TEXT,

    -- Usage data
    bash_example TEXT,
    python_example TEXT,
    config_example TEXT,

    -- References
    documentation_url TEXT,
    conversation_context TEXT,   -- How this method is used in the conversation

    -- Metrics
    citation_count INTEGER DEFAULT 0,
    last_cited TIMESTAMP,

    -- Database metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- INDEXES: antigravity_api_methods
-- ============================================================================

-- Primary relationship index
CREATE INDEX IF NOT EXISTS idx_api_methods_conversation_id
    ON antigravity_api_methods(conversation_id);

-- Method search indexes
CREATE INDEX IF NOT EXISTS idx_api_methods_method_name
    ON antigravity_api_methods(method_name);

CREATE INDEX IF NOT EXISTS idx_api_methods_protocol
    ON antigravity_api_methods(protocol);

CREATE INDEX IF NOT EXISTS idx_api_methods_port
    ON antigravity_api_methods(port);

CREATE INDEX IF NOT EXISTS idx_api_methods_access_level
    ON antigravity_api_methods(access_level);

-- Protocol-specific queries
CREATE INDEX IF NOT EXISTS idx_api_methods_protocol_port
    ON antigravity_api_methods(protocol, port);

-- Usage tracking
CREATE INDEX IF NOT EXISTS idx_api_methods_citation_count
    ON antigravity_api_methods(citation_count DESC);

-- Materialized view for popular methods
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_popular_api_methods AS
SELECT
    method_name,
    protocol,
    port,
    access_level,
    COUNT(*) as conversation_count,
    SUM(citation_count) as total_citations
FROM antigravity_api_methods
GROUP BY method_name, protocol, port, access_level
ORDER BY conversation_count DESC;

CREATE INDEX IF NOT EXISTS idx_mv_popular_methods_count
    ON mv_popular_api_methods(conversation_count DESC);

-- Refresh schedule: hourly
SELECT cron.schedule('refresh-popular-methods', '0 * * * *',
    $$REFRESH MATERIALIZED VIEW CONCURRENTLY mv_popular_api_methods$$);

-- ============================================================================
-- TABLE: antigravity_relationships
-- Maps relationships between conversations
-- ============================================================================
CREATE TABLE IF NOT EXISTS antigravity_relationships (
    id SERIAL PRIMARY KEY,
    from_conversation_id INTEGER NOT NULL
        REFERENCES antigravity_conversations(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    to_conversation_id INTEGER NOT NULL
        REFERENCES antigravity_conversations(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    relationship_type VARCHAR(50),    -- references, extends, contradicts, updates, prerequisites
    relationship_strength INTEGER DEFAULT 1,  -- 1-10 scale
    context TEXT,                       -- Why this relationship exists

    -- Database metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Prevent duplicate relationships
CREATE UNIQUE INDEX IF NOT EXISTS uq_relationship_pair
    ON antigravity_relationships(from_conversation_id, to_conversation_id, relationship_type);

-- ============================================================================
-- INDEXES: antigravity_relationships
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_relationships_from_conversation
    ON antigravity_relationships(from_conversation_id);

CREATE INDEX IF NOT EXISTS idx_relationships_to_conversation
    ON antigravity_relationships(to_conversation_id);

CREATE INDEX IF NOT EXISTS idx_relationships_type
    ON antigravity_relationships(relationship_type);

CREATE INDEX IF NOT EXISTS idx_relationships_strength
    ON antigravity_relationships(relationship_strength DESC);

-- ============================================================================
-- TABLE: antigravity_security_warnings
-- Tracks security vulnerabilities and concerns
-- ============================================================================
CREATE TABLE IF NOT EXISTS antigravity_security_warnings (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER NOT NULL
        REFERENCES antigravity_conversations(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    warning_type VARCHAR(100),        -- e.g., 'data_exfiltration', 'prompt_injection'
    severity VARCHAR(20),             -- critical, high, medium, low
    description TEXT,
    affected_methods TEXT[],          -- Which API methods are affected
    recommendation TEXT,

    -- CVEs or external references
    external_refs TEXT[],

    -- Verification
    verified BOOLEAN DEFAULT false,
    verified_at TIMESTAMP,

    -- Database metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- INDEXES: antigravity_security_warnings
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_security_conversation_id
    ON antigravity_security_warnings(conversation_id);

CREATE INDEX IF NOT EXISTS idx_security_warning_type
    ON antigravity_security_warnings(warning_type);

CREATE INDEX IF NOT EXISTS idx_security_severity
    ON antigravity_security_warnings(severity);

CREATE INDEX IF NOT EXISTS idx_security_verified
    ON antigravity_security_warnings(verified) WHERE verified = false;

-- Materialized view: Critical security issues
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_critical_security_warnings AS
SELECT
    sw.warning_type,
    sw.severity,
    COUNT(*) as occurrence_count,
    ARRAY_AGG(DISTINCT c.conversation_type) as affected_types
FROM antigravity_security_warnings sw
JOIN antigravity_conversations c ON sw.conversation_id = c.id
WHERE sw.severity IN ('critical', 'high')
GROUP BY sw.warning_type, sw.severity
ORDER BY occurrence_count DESC;

-- ============================================================================
-- FUNCTION: update_antigravity_updated_at()
-- Auto-update timestamps
-- ============================================================================
CREATE OR REPLACE FUNCTION update_antigravity_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    NEW.updated_at_db = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- ============================================================================
-- TRIGGERS: Auto-update timestamps
-- ============================================================================
CREATE TRIGGER trigger_update_antigravity_conversations
    BEFORE UPDATE ON antigravity_conversations
    FOR EACH ROW
    EXECUTE FUNCTION update_antigravity_updated_at();

CREATE TRIGGER trigger_update_antigravity_api_methods
    BEFORE UPDATE ON antigravity_api_methods
    FOR EACH ROW
    EXECUTE FUNCTION update_antigravity_updated_at();

-- ============================================================================
-- FUNCTION: extract_and_index_text()
-- Extracts searchable text from conversation content
-- ============================================================================
CREATE OR REPLACE FUNCTION extract_and_index_text()
RETURNS TRIGGER AS $$
BEGIN
    -- Populate full_text tsvector if summary exists
    IF NEW.summary IS NOT NULL THEN
        NEW.full_text := to_tsvector('english', NEW.summary);
    END IF;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- ============================================================================
-- TRIGGERS: Full-text indexing
-- ============================================================================
CREATE TRIGGER trigger_index_antigravity_text
    BEFORE INSERT OR UPDATE ON antigravity_conversations
    FOR EACH ROW
    EXECUTE FUNCTION extract_and_index_text();

-- ============================================================================
-- VIEW: conversation_overview
-- Comprehensive view for analytics
-- ============================================================================
CREATE OR REPLACE VIEW conversation_overview AS
SELECT
    c.id,
    c.session_id,
    c.created_at,

    -- Categorization
    c.conversation_type,
    c.api_access_style,
    c.technical_focus,
    c.resource_context,

    -- Content metrics
    c.word_count,
    c.message_count,
    c.has_code_examples,
    c.has_security_warnings,
    c.security_warning_count,

    -- API methods
    c.api_methods_count,
    ARRAY(
        SELECT method_name
        FROM antigravity_api_methods
        WHERE conversation_id = c.id
        ORDER BY protocol, method_name
    ) as api_method_names,

    -- Relationships
    (
        SELECT COUNT(*)
        FROM antigravity_relationships r
        WHERE r.from_conversation_id = c.id
    ) as outgoing_relationships,

    (
        SELECT COUNT(*)
        FROM antigravity_relationships r
        WHERE r.to_conversation_id = c.id
    ) as incoming_relationships,

    -- Security
    (
        SELECT COUNT(*)
        FROM antigravity_security_warnings sw
        WHERE sw.conversation_id = c.id
    ) as security_warnings_total

FROM antigravity_conversations c
ORDER BY c.created_at DESC;

-- ============================================================================
-- FUNCTION: get_conversation_by_session_id()
-- Quick lookup by session ID
-- ============================================================================
CREATE OR REPLACE FUNCTION get_conversation_by_session_id(
    p_session_id VARCHAR(64)
)
RETURNS TABLE (
    id INTEGER,
    session_id VARCHAR(64),
    file_path TEXT,
    created_at TIMESTAMP,
    conversation_type VARCHAR(50),
    api_access_style VARCHAR(50)[],
    technical_focus TEXT[],
    summary TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.id,
        c.session_id,
        c.file_path,
        c.created_at,
        c.conversation_type,
        c.api_access_style,
        c.technical_focus,
        c.summary
    FROM antigravity_conversations c
    WHERE c.session_id = p_session_id
    ORDER BY c.created_at DESC
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- FUNCTION: search_conversations_by_api_style()
-- Search for conversations using specific API access styles
-- ============================================================================
CREATE OR REPLACE FUNCTION search_conversations_by_api_style(
    p_api_style VARCHAR(50),
    p_limit INTEGER DEFAULT 10
)
RETURNS TABLE (
    session_id VARCHAR(64),
    created_at TIMESTAMP,
    summary TEXT,
    word_count INTEGER,
    file_path TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.session_id,
        c.created_at,
        c.summary,
        c.word_count,
        c.file_path
    FROM antigravity_conversations c
    WHERE p_api_style = ANY(c.api_access_style)
    ORDER BY c.created_at DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- FUNCTION: get_conversations_by_technical_focus()
-- Search conversations by technical focus area
-- ============================================================================
CREATE OR REPLACE FUNCTION get_conversations_by_technical_focus(
    p_focus TEXT,
    p_date_from DATE DEFAULT NULL,
    p_date_to DATE DEFAULT NULL,
    p_limit INTEGER DEFAULT 10
)
RETURNS TABLE (
    session_id VARCHAR(64),
    created_at TIMESTAMP,
    summary TEXT,
    api_methods_count INTEGER,
    file_path TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.session_id,
        c.created_at,
        c.summary,
        c.api_methods_count,
        c.file_path
    FROM antigravity_conversations c
    WHERE p_focus = ANY(c.technical_focus)
      AND (p_date_from IS NULL OR DATE(c.created_at) >= p_date_from)
      AND (p_date_to IS NULL OR DATE(c.created_at) <= p_date_to)
    ORDER BY c.created_at DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- FUNCTION: get_popular_api_methods()
-- Get most frequently mentioned API methods
-- ============================================================================
CREATE OR REPLACE FUNCTION get_popular_api_methods(
    p_limit INTEGER DEFAULT 20
)
RETURNS TABLE (
    method_name VARCHAR(200),
    protocol VARCHAR(20),
    port INTEGER,
    conversation_count BIGINT,
    total_citations BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        m.method_name,
        m.protocol,
        m.port,
        COUNT(DISTINCT m.conversation_id) as conversation_count,
        SUM(m.citation_count) as total_citations
    FROM antigravity_api_methods m
    GROUP BY m.method_name, m.protocol, m.port
    ORDER BY conversation_count DESC, total_citations DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- FUNCTION: get_security_warnings_summary()
-- Summary of security issues across conversations
-- ============================================================================
CREATE OR REPLACE FUNCTION get_security_warnings_summary()
RETURNS TABLE (
    warning_type VARCHAR(100),
    severity VARCHAR(20),
    occurrence_count BIGINT,
    affected_types TEXT[]
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        sw.warning_type,
        sw.severity,
        COUNT(*)::BIGINT as occurrence_count,
        ARRAY_AGG(DISTINCT c.conversation_type) as affected_types
    FROM antigravity_security_warnings sw
    JOIN antigravity_conversations c ON sw.conversation_id = c.id
    WHERE sw.severity IN ('critical', 'high')
    GROUP BY sw.warning_type, sw.severity
    ORDER BY occurrence_count DESC;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- FUNCTION: get_conversation_relationships()
-- Get network of related conversations
-- ============================================================================
CREATE OR REPLACE FUNCTION get_conversation_relationships(
    p_session_id VARCHAR(64)
)
RETURNS TABLE (
    related_session_id VARCHAR(64),
    relationship_type VARCHAR(50),
    context TEXT,
    strength INTEGER
) AS $$
BEGIN
    RETURN QUERY
    WITH conversation_lookup AS (
        SELECT id FROM antigravity_conversations WHERE session_id = p_session_id
    )
    SELECT
        c2.session_id as related_session_id,
        r.relationship_type,
        r.context,
        r.relationship_strength as strength
    FROM antigravity_relationships r
    JOIN conversation_lookup cl ON r.from_conversation_id = cl.id
    JOIN antigravity_conversations c2 ON r.to_conversation_id = c2.id
    ORDER BY r.relationship_strength DESC;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- GRANT PRIVILEGES
-- ============================================================================
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO postgres_admin_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO postgres_admin_user;

-- ============================================================================
-- END OF SCHEMA
-- ============================================================================
COMMENT ON TABLE antigravity_conversations IS 'Primary index of antigravity IDE conversation files with categorization';
COMMENT ON TABLE antigravity_api_methods IS 'Individual API methods and access patterns extracted from conversations';
COMMENT ON TABLE antigravity_relationships IS 'Maps relationships and references between conversations';
COMMENT ON TABLE antigravity_security_warnings IS 'Security vulnerabilities and concerns identified in conversations';
