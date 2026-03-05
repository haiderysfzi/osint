-- clickhouse/schema.sql
-- Phone OSINT Results Table

CREATE TABLE IF NOT EXISTS phone_osint_results (
    ingested_at DateTime64(3) DEFAULT now64(3),
    phone String,
    owner_name String,
    owner_name_confidence Float64,
    cnic String,
    passport String,
    address String,
    country String,
    companies Array(String),
    sources Array(String),
    raw_json String,
    pipeline_duration UInt32,
    status Enum8('success' = 1, 'partial' = 2, 'failed' = 3)
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(ingested_at)
ORDER BY (phone, ingested_at)
SETTINGS index_granularity = 8192;

-- Materialized view for name hits analytics
CREATE MATERIALIZED VIEW IF NOT EXISTS name_hits_mv
TO phone_osint_stats AS
SELECT 
    country,
    countIf(owner_name != '') as name_hits,
    avg(owner_name_confidence) as avg_confidence
FROM phone_osint_results
GROUP BY country;

-- Stats summary table (target for materialized view)
CREATE TABLE IF NOT EXISTS phone_osint_stats (
    country String,
    name_hits UInt64,
    avg_confidence Float64,
    updated_at DateTime DEFAULT now()
) ENGINE = MergeTree()
ORDER BY country;

-- Index for fast phone lookups
ALTER TABLE phone_osint_results ADD INDEX idx_phone phone TYPE bloom_filter GRANULARITY 1;

-- Index for country-based queries
ALTER TABLE phone_osint_results ADD INDEX idx_country country TYPE set(1000) GRANULARITY 4;
