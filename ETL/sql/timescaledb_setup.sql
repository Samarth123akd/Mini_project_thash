-- TimescaleDB setup for time-series optimized data warehouse
-- This script sets up hypertables with automatic partitioning for efficient
-- time-series queries on order and transaction data

-- Enable TimescaleDB extension (requires superuser privileges)
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- =====================================================================
-- ORDERS TABLE WITH TIMESCALE HYPERTABLE
-- =====================================================================

DROP TABLE IF EXISTS orders CASCADE;

CREATE TABLE orders (
    order_id TEXT NOT NULL,
    invoice_no TEXT,
    stock_code TEXT,
    description TEXT,
    quantity INTEGER,
    unit_price NUMERIC,
    total_amount NUMERIC,
    invoice_date TIMESTAMP NOT NULL,
    invoice_date_normalized TIMESTAMP,
    customer_id TEXT,
    customer_lifetime_value NUMERIC,
    avg_order_value NUMERIC,
    order_frequency NUMERIC,
    item_count INTEGER,
    -- Additional metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create index before converting to hypertable
CREATE INDEX idx_orders_customer_id ON orders (customer_id);
CREATE INDEX idx_orders_order_id ON orders (order_id);

-- Convert to hypertable partitioned by invoice_date
-- Partitions will be created automatically with 7-day chunks
SELECT create_hypertable(
    'orders',
    'invoice_date',
    chunk_time_interval => INTERVAL '7 days',
    if_not_exists => TRUE
);

-- Add compression policy to automatically compress chunks older than 30 days
-- This reduces storage by 90%+ for historical data
ALTER TABLE orders SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'customer_id',
    timescaledb.compress_orderby = 'invoice_date DESC'
);

SELECT add_compression_policy('orders', INTERVAL '30 days');

-- Retention policy: automatically drop chunks older than 3 years
SELECT add_retention_policy('orders', INTERVAL '3 years');

-- =====================================================================
-- ORDER ITEMS TABLE (for detailed line-item analysis)
-- =====================================================================

DROP TABLE IF EXISTS order_items CASCADE;

CREATE TABLE order_items (
    order_item_id BIGSERIAL,
    order_id TEXT NOT NULL,
    product_id TEXT,
    product_name TEXT,
    product_category TEXT,
    quantity INTEGER,
    price NUMERIC,
    discount NUMERIC DEFAULT 0,
    item_total NUMERIC,
    order_timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_order_items_order_id ON order_items (order_id);
CREATE INDEX idx_order_items_product_id ON order_items (product_id);

-- Convert to hypertable
SELECT create_hypertable(
    'order_items',
    'order_timestamp',
    chunk_time_interval => INTERVAL '7 days',
    if_not_exists => TRUE
);

-- Compression for order_items
ALTER TABLE order_items SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'order_id, product_id',
    timescaledb.compress_orderby = 'order_timestamp DESC'
);

SELECT add_compression_policy('order_items', INTERVAL '30 days');

-- =====================================================================
-- CUSTOMER METRICS TABLE (for aggregated customer analytics)
-- =====================================================================

DROP TABLE IF EXISTS customer_metrics CASCADE;

CREATE TABLE customer_metrics (
    customer_id TEXT NOT NULL,
    metric_date DATE NOT NULL,
    total_orders INTEGER DEFAULT 0,
    total_spent NUMERIC DEFAULT 0,
    avg_order_value NUMERIC DEFAULT 0,
    order_frequency NUMERIC DEFAULT 0,
    lifetime_value NUMERIC DEFAULT 0,
    days_since_last_order INTEGER,
    customer_segment TEXT,  -- 'high_value', 'medium_value', 'low_value', 'at_risk'
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (customer_id, metric_date)
);

-- Convert to hypertable
SELECT create_hypertable(
    'customer_metrics',
    'metric_date',
    chunk_time_interval => INTERVAL '1 month',
    if_not_exists => TRUE
);

-- Compression for customer metrics
ALTER TABLE customer_metrics SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'customer_id',
    timescaledb.compress_orderby = 'metric_date DESC'
);

SELECT add_compression_policy('customer_metrics', INTERVAL '90 days');

-- =====================================================================
-- CONTINUOUS AGGREGATES (Pre-computed materialized views)
-- =====================================================================

-- Daily sales summary (auto-refreshed)
CREATE MATERIALIZED VIEW daily_sales_summary
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', invoice_date) AS day,
    COUNT(DISTINCT order_id) AS order_count,
    SUM(total_amount) AS total_revenue,
    AVG(total_amount) AS avg_order_value,
    COUNT(DISTINCT customer_id) AS unique_customers,
    SUM(item_count) AS total_items_sold
FROM orders
GROUP BY day
WITH NO DATA;

-- Refresh policy: auto-update daily aggregates every hour
SELECT add_continuous_aggregate_policy('daily_sales_summary',
    start_offset => INTERVAL '3 days',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour');

-- Hourly sales (for real-time dashboards)
CREATE MATERIALIZED VIEW hourly_sales_summary
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', invoice_date) AS hour,
    COUNT(DISTINCT order_id) AS order_count,
    SUM(total_amount) AS total_revenue,
    AVG(total_amount) AS avg_order_value
FROM orders
GROUP BY hour
WITH NO DATA;

SELECT add_continuous_aggregate_policy('hourly_sales_summary',
    start_offset => INTERVAL '1 day',
    end_offset => INTERVAL '10 minutes',
    schedule_interval => INTERVAL '10 minutes');

-- Monthly customer metrics aggregate
CREATE MATERIALIZED VIEW monthly_customer_summary
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 month', invoice_date) AS month,
    customer_id,
    COUNT(DISTINCT order_id) AS order_count,
    SUM(total_amount) AS total_spent,
    AVG(total_amount) AS avg_order_value,
    MAX(customer_lifetime_value) AS lifetime_value
FROM orders
WHERE customer_id IS NOT NULL
GROUP BY month, customer_id
WITH NO DATA;

SELECT add_continuous_aggregate_policy('monthly_customer_summary',
    start_offset => INTERVAL '3 months',
    end_offset => INTERVAL '1 day',
    schedule_interval => INTERVAL '1 day');

-- =====================================================================
-- INDEXES FOR QUERY OPTIMIZATION
-- =====================================================================

-- Additional indexes for common query patterns
CREATE INDEX idx_orders_total_amount ON orders (total_amount) WHERE total_amount > 0;
CREATE INDEX idx_orders_customer_date ON orders (customer_id, invoice_date DESC);
CREATE INDEX idx_order_items_product_timestamp ON order_items (product_id, order_timestamp DESC);

-- Partial index for high-value orders
CREATE INDEX idx_orders_high_value ON orders (invoice_date, total_amount) 
WHERE total_amount > 1000;

-- =====================================================================
-- HELPER FUNCTIONS
-- =====================================================================

-- Function to refresh all continuous aggregates
CREATE OR REPLACE FUNCTION refresh_all_continuous_aggregates()
RETURNS void AS $$
BEGIN
    CALL refresh_continuous_aggregate('daily_sales_summary', NULL, NULL);
    CALL refresh_continuous_aggregate('hourly_sales_summary', NULL, NULL);
    CALL refresh_continuous_aggregate('monthly_customer_summary', NULL, NULL);
END;
$$ LANGUAGE plpgsql;

-- Function to get chunk statistics
CREATE OR REPLACE FUNCTION get_chunk_statistics()
RETURNS TABLE (
    hypertable_name TEXT,
    chunk_count BIGINT,
    total_size TEXT,
    compressed_chunks BIGINT,
    compression_ratio NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        h.table_name::TEXT,
        COUNT(*)::BIGINT,
        pg_size_pretty(SUM(ch.total_bytes))::TEXT,
        SUM(CASE WHEN ch.compressed_chunk_id IS NOT NULL THEN 1 ELSE 0 END)::BIGINT,
        CASE 
            WHEN SUM(ch.uncompressed_total_bytes) > 0 
            THEN ROUND((1 - SUM(ch.compressed_total_bytes)::NUMERIC / SUM(ch.uncompressed_total_bytes)) * 100, 2)
            ELSE 0 
        END
    FROM timescaledb_information.hypertables h
    LEFT JOIN timescaledb_information.chunks ch ON ch.hypertable_name = h.table_name
    GROUP BY h.table_name;
END;
$$ LANGUAGE plpgsql;

-- =====================================================================
-- GRANT PERMISSIONS (adjust user as needed)
-- =====================================================================

-- Grant access to application user (replace 'etl_user' with your username)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON orders, order_items, customer_metrics TO etl_user;
-- GRANT SELECT ON daily_sales_summary, hourly_sales_summary, monthly_customer_summary TO etl_user;

-- =====================================================================
-- VERIFICATION QUERIES
-- =====================================================================

-- Check hypertables
SELECT * FROM timescaledb_information.hypertables;

-- Check compression policies
SELECT * FROM timescaledb_information.jobs WHERE proc_name LIKE '%compress%';

-- View chunk information
SELECT * FROM timescaledb_information.chunks ORDER BY range_start DESC LIMIT 10;

-- Check continuous aggregates
SELECT * FROM timescaledb_information.continuous_aggregates;

COMMENT ON TABLE orders IS 'Main orders table with TimescaleDB hypertable partitioning by invoice_date';
COMMENT ON TABLE order_items IS 'Order line items with time-series optimization';
COMMENT ON TABLE customer_metrics IS 'Aggregated customer metrics with daily snapshots';
COMMENT ON VIEW daily_sales_summary IS 'Continuous aggregate: daily sales metrics auto-refreshed hourly';
COMMENT ON VIEW hourly_sales_summary IS 'Continuous aggregate: hourly sales metrics for real-time dashboards';
COMMENT ON VIEW monthly_customer_summary IS 'Continuous aggregate: monthly customer behavior metrics';
