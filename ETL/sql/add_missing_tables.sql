-- Add missing tables for Brazilian E-commerce Dataset
-- Run this in pgAdmin4 Query Tool for ETL_DB database

-- Dimension: Sellers
CREATE TABLE IF NOT EXISTS dim_sellers (
    seller_id TEXT PRIMARY KEY,
    seller_zip_code_prefix TEXT,
    seller_city TEXT,
    seller_state TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sellers_state ON dim_sellers(seller_state);
CREATE INDEX IF NOT EXISTS idx_sellers_city ON dim_sellers(seller_city);

-- Dimension: Geolocation
CREATE TABLE IF NOT EXISTS dim_geolocation (
    geolocation_id SERIAL PRIMARY KEY,
    geolocation_zip_code_prefix TEXT,
    geolocation_lat DOUBLE PRECISION,
    geolocation_lng DOUBLE PRECISION,
    geolocation_city TEXT,
    geolocation_state TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_geo_zip ON dim_geolocation(geolocation_zip_code_prefix);
CREATE INDEX IF NOT EXISTS idx_geo_state ON dim_geolocation(geolocation_state);
CREATE INDEX IF NOT EXISTS idx_geo_coords ON dim_geolocation(geolocation_lat, geolocation_lng);

-- Dimension: Product Category Translation
CREATE TABLE IF NOT EXISTS dim_product_category_translation (
    product_category_name TEXT PRIMARY KEY,
    product_category_name_english TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Fact: Order Reviews
CREATE TABLE IF NOT EXISTS fact_reviews (
    review_id TEXT PRIMARY KEY,
    order_id TEXT REFERENCES fact_orders(order_id),
    review_score INTEGER,
    review_comment_title TEXT,
    review_comment_message TEXT,
    review_creation_date TIMESTAMP WITH TIME ZONE,
    review_answer_timestamp TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_reviews_order ON fact_reviews(order_id);
CREATE INDEX IF NOT EXISTS idx_reviews_score ON fact_reviews(review_score);
CREATE INDEX IF NOT EXISTS idx_reviews_date ON fact_reviews(review_creation_date);

-- Grant permissions to etl_user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO etl_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO etl_user;

-- Verify tables exist
SELECT 
    table_name,
    pg_size_pretty(pg_total_relation_size(quote_ident(table_name)::regclass)) as size
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_type = 'BASE TABLE'
ORDER BY table_name;
