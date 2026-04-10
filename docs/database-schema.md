# Database Schema

## Overview

The TED Bot database is hosted on Supabase (PostgreSQL 15+) with the `pgvector` extension for vector similarity search.

## Schema Diagram

```
┌─────────────────────────┐
│   tender_notices        │
│─────────────────────────│
│ PK id (uuid)            │◄────┐
│    ted_id (text)        │     │
│    title (text)         │     │
│    description (text)   │     │
│    ... (see below)      │     │
└─────────────────────────┘     │
                                │
┌─────────────────────────┐     │
│  tender_embeddings      │     │
│─────────────────────────│     │
│ PK id (uuid)            │     │
│ FK tender_id (uuid)     │─────┘
│    embedding (vector)   │
│    model_name (text)    │
│    created_at           │
└─────────────────────────┘

┌─────────────────────────┐
│  user_preferences       │
│─────────────────────────│
│ PK id (uuid)            │
│    pref_key (text)      │
│    pref_value (jsonb)   │
│    updated_at           │
└─────────────────────────┘

┌─────────────────────────┐     ┌─────────────────────────┐
│ notification_subs       │     │  notification_history   │
│─────────────────────────│     │─────────────────────────│
│ PK id (uuid)            │◄────│ PK id (uuid)            │
│    name (text)          │     │ FK subscription_id      │
│    criteria (jsonb)     │     │ FK tender_id (uuid)     │
│    active (boolean)     │     │    sent_at              │
│    created_at           │     │    status (text)        │
└─────────────────────────┘     └─────────────────────────┘

┌─────────────────────────┐
│    query_history        │
│─────────────────────────│
│ PK id (uuid)            │
│    query_text (text)    │
│    session_id (uuid)    │
│    results_count (int)  │
│    filters_used (jsonb) │
│    created_at           │
└─────────────────────────┘

┌─────────────────────────┐
│    sync_status          │
│─────────────────────────│
│ PK id (uuid)            │
│    last_sync            │
│    status (text)        │
│    tenders_fetched (int)│
│    errors (jsonb)       │
└─────────────────────────┘
```

## Detailed Schema

### Table: tender_notices

Stores core tender information from TED platform.

```sql
CREATE TABLE tender_notices (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- TED identifiers
    ted_id TEXT UNIQUE NOT NULL,  -- Official TED notice ID
    ted_url TEXT NOT NULL,         -- Link to TED platform
    
    -- Core information
    title TEXT NOT NULL,
    description TEXT,              -- Full tender description
    summary TEXT,                  -- AI-generated summary
    
    -- Classification
    cpv_codes JSONB DEFAULT '[]'::jsonb,  -- Array of CPV code objects
    procedure_type TEXT,           -- e.g., "Open procedure", "Restricted"
    
    -- Contracting authority
    contracting_authority JSONB,   -- {name, address, contact}
    country TEXT NOT NULL,         -- ISO country code (e.g., "DE")
    location TEXT,                 -- City/region
    
    -- Financial
    value NUMERIC,                 -- Estimated value
    currency TEXT DEFAULT 'EUR',   -- Currency code
    
    -- Timeline
    publication_date TIMESTAMP WITH TIME ZONE NOT NULL,
    deadline TIMESTAMP WITH TIME ZONE,
    start_date TIMESTAMP WITH TIME ZONE,
    end_date TIMESTAMP WITH TIME ZONE,
    
    -- Documents
    documents JSONB DEFAULT '[]'::jsonb,  -- Array of document links
    
    -- Metadata
    raw_data JSONB,                -- Full TED API response
    source TEXT DEFAULT 'TED_API', -- Data source
    status TEXT DEFAULT 'active',  -- active, closed, cancelled
    
    -- Analysis cache
    ai_analysis JSONB,             -- Cached analysis results
    key_requirements TEXT[],       -- Extracted requirements
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Indexes
    CONSTRAINT valid_country CHECK (length(country) = 2)
);

-- Indexes
CREATE INDEX idx_tender_country ON tender_notices(country);
CREATE INDEX idx_tender_deadline ON tender_notices(deadline);
CREATE INDEX idx_tender_publication ON tender_notices(publication_date);
CREATE INDEX idx_tender_value ON tender_notices(value);
CREATE INDEX idx_tender_status ON tender_notices(status);
CREATE INDEX idx_tender_cpv ON tender_notices USING GIN (cpv_codes);
CREATE INDEX idx_tender_ted_id ON tender_notices(ted_id);

-- Full-text search
CREATE INDEX idx_tender_search ON tender_notices 
    USING GIN (to_tsvector('english', title || ' ' || COALESCE(description, '')));
```

### Table: tender_embeddings

Stores vector embeddings for semantic search.

```sql
CREATE TABLE tender_embeddings (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Foreign key
    tender_id UUID NOT NULL REFERENCES tender_notices(id) ON DELETE CASCADE,
    
    -- Vector embedding
    embedding vector(768),  -- Dimension depends on model (768 for nomic-embed-text)
    
    -- Metadata
    model_name TEXT NOT NULL,              -- e.g., "nomic-embed-text"
    model_version TEXT,                    -- Model version
    content_type TEXT DEFAULT 'full',      -- full, title, summary
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    UNIQUE(tender_id, model_name, content_type)
);

-- Vector similarity index (HNSW for fast approximate search)
CREATE INDEX idx_embedding_vector ON tender_embeddings 
    USING hnsw (embedding vector_cosine_ops);

-- Standard index
CREATE INDEX idx_embedding_tender ON tender_embeddings(tender_id);
```

### Table: user_preferences

Stores user preferences and settings.

```sql
CREATE TABLE user_preferences (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Preference key-value
    pref_key TEXT UNIQUE NOT NULL,  -- e.g., "search_defaults", "display_settings"
    pref_value JSONB NOT NULL,      -- JSON object with settings
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Example rows:
-- pref_key: "search_defaults"
-- pref_value: {"countries": ["DE"], "cpv_codes": [], "search_mode": "hybrid"}

-- pref_key: "notification_settings"
-- pref_value: {"enabled": true, "email": null}
```

### Table: notification_subscriptions

Stores user-defined notification/monitoring criteria.

```sql
CREATE TABLE notification_subscriptions (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Subscription details
    name TEXT NOT NULL,                 -- User-friendly name
    description TEXT,
    
    -- Matching criteria
    criteria JSONB NOT NULL,            -- Search filters as JSON
    
    -- Settings
    active BOOLEAN DEFAULT TRUE,
    notification_method TEXT DEFAULT 'log',  -- log, email, webhook
    
    -- Statistics
    match_count INTEGER DEFAULT 0,
    last_triggered TIMESTAMP WITH TIME ZONE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Example criteria:
-- {
--   "countries": ["DE"],
--   "cpv_codes": ["72000000"],
--   "min_value": 100000,
--   "keywords": ["cloud", "infrastructure"]
-- }

-- Indexes
CREATE INDEX idx_subscription_active ON notification_subscriptions(active);
```

### Table: notification_history

Logs notifications sent to user.

```sql
CREATE TABLE notification_history (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Foreign keys
    subscription_id UUID NOT NULL REFERENCES notification_subscriptions(id) ON DELETE CASCADE,
    tender_id UUID NOT NULL REFERENCES tender_notices(id) ON DELETE CASCADE,
    
    -- Notification details
    tender_title TEXT NOT NULL,         -- Denormalized for quick access
    tender_deadline TIMESTAMP WITH TIME ZONE,
    
    -- Delivery
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status TEXT DEFAULT 'pending',      -- pending, delivered, failed
    error_message TEXT,
    
    -- Metadata
    notification_data JSONB             -- Full notification payload
);

-- Indexes
CREATE INDEX idx_notif_subscription ON notification_history(subscription_id);
CREATE INDEX idx_notif_tender ON notification_history(tender_id);
CREATE INDEX idx_notif_sent ON notification_history(sent_at);
CREATE INDEX idx_notif_status ON notification_history(status);
```

### Table: query_history

Stores user query history for analytics and improvements.

```sql
CREATE TABLE query_history (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Query details
    query_text TEXT NOT NULL,
    session_id UUID,                    -- Chat session ID
    
    -- Search parameters
    filters_used JSONB,                 -- Filters applied
    search_mode TEXT,                   -- keyword, semantic, hybrid
    
    -- Results
    results_count INTEGER,
    
    -- Performance
    execution_time_ms INTEGER,          -- Query execution time
    
    -- Agent info
    agent_used TEXT,                    -- Which agent handled query
    
    -- Timestamp
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_query_session ON query_history(session_id);
CREATE INDEX idx_query_created ON query_history(created_at);
```

### Table: sync_status

Tracks TED API synchronization status.

```sql
CREATE TABLE sync_status (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Sync details
    sync_type TEXT NOT NULL,            -- full, incremental
    date_from DATE,
    date_to DATE,
    
    -- Status
    status TEXT NOT NULL,               -- started, running, completed, failed
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Results
    tenders_fetched INTEGER DEFAULT 0,
    tenders_new INTEGER DEFAULT 0,
    tenders_updated INTEGER DEFAULT 0,
    
    -- Errors
    errors JSONB,                       -- Array of error messages
    
    -- Metadata
    triggered_by TEXT DEFAULT 'scheduled'  -- scheduled, manual, webhook
);

-- Indexes
CREATE INDEX idx_sync_status ON sync_status(status);
CREATE INDEX idx_sync_started ON sync_status(started_at);
```

## Views

### View: active_tenders

Shows only active tenders with relevant fields.

```sql
CREATE VIEW active_tenders AS
SELECT 
    id,
    ted_id,
    title,
    summary,
    contracting_authority->>'name' AS authority_name,
    country,
    value,
    currency,
    deadline,
    publication_date,
    ted_url
FROM tender_notices
WHERE status = 'active'
  AND (deadline IS NULL OR deadline > NOW())
ORDER BY publication_date DESC;
```

### View: subscription_matches

Shows recent tenders matching active subscriptions.

```sql
CREATE VIEW subscription_matches AS
SELECT 
    ns.id AS subscription_id,
    ns.name AS subscription_name,
    tn.id AS tender_id,
    tn.title AS tender_title,
    tn.country,
    tn.value,
    tn.deadline,
    tn.publication_date
FROM notification_subscriptions ns
CROSS JOIN tender_notices tn
WHERE ns.active = TRUE
  AND tn.status = 'active'
  -- Note: Actual matching logic implemented in application layer
ORDER BY tn.publication_date DESC;
```

## Functions

### Function: update_updated_at()

Trigger function to automatically update `updated_at` timestamp.

```sql
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to relevant tables
CREATE TRIGGER update_tender_notices_updated_at
    BEFORE UPDATE ON tender_notices
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_user_preferences_updated_at
    BEFORE UPDATE ON user_preferences
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_notification_subscriptions_updated_at
    BEFORE UPDATE ON notification_subscriptions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();
```

### Function: search_similar_tenders()

Vector similarity search function.

```sql
CREATE OR REPLACE FUNCTION search_similar_tenders(
    query_embedding vector(768),
    match_threshold float DEFAULT 0.7,
    match_count int DEFAULT 10
)
RETURNS TABLE (
    tender_id uuid,
    title text,
    similarity float
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        tn.id,
        tn.title,
        1 - (te.embedding <=> query_embedding) AS similarity
    FROM tender_embeddings te
    JOIN tender_notices tn ON te.tender_id = tn.id
    WHERE 1 - (te.embedding <=> query_embedding) > match_threshold
      AND tn.status = 'active'
    ORDER BY te.embedding <=> query_embedding
    LIMIT match_count;
END;
$$ LANGUAGE plpgsql;
```

## Row Level Security (RLS)

**Current**: Not enabled (single user)
**Future**: Enable RLS for multi-user support

```sql
-- Example for future multi-user setup
ALTER TABLE tender_notices ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view all tenders"
    ON tender_notices FOR SELECT
    USING (true);

CREATE POLICY "Users can insert their own queries"
    ON query_history FOR INSERT
    WITH CHECK (auth.uid() = user_id);
```

## Indexes Summary

Key indexes for performance:

1. **Vector search**: `idx_embedding_vector` (HNSW)
2. **Text search**: `idx_tender_search` (GIN)
3. **Date range queries**: `idx_tender_deadline`, `idx_tender_publication`
4. **Filter queries**: `idx_tender_country`, `idx_tender_value`, `idx_tender_cpv`
5. **Foreign keys**: All foreign key columns indexed

## Maintenance

### Partitioning (Future)

For large datasets, consider partitioning `tender_notices` by publication date:

```sql
-- Example: partition by year
CREATE TABLE tender_notices_2026 PARTITION OF tender_notices
    FOR VALUES FROM ('2026-01-01') TO ('2027-01-01');
```

### Vacuum and Analyze

Regular maintenance:

```sql
-- Analyze tables for query planning
ANALYZE tender_notices;
ANALYZE tender_embeddings;

-- Vacuum to reclaim space
VACUUM ANALYZE tender_notices;
```

## Migration Strategy

1. **Initial setup**: Run all CREATE TABLE statements
2. **Enable extensions**: `CREATE EXTENSION IF NOT EXISTS vector;`
3. **Create indexes**: After initial data load for better performance
4. **Create views and functions**: After tables are populated
5. **Test queries**: Verify performance with sample data

## Backup and Recovery

- **Supabase automatic backups**: Daily (included in Supabase)
- **Point-in-time recovery**: Available on paid plans
- **Manual exports**: Use `pg_dump` for local backups
