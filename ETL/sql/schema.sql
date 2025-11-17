-- Simple schema for orders table (Postgres)
-- Extended with dimension tables and audit tracking

-- Dimension: Customers
CREATE TABLE IF NOT EXISTS dim_customers (
    customer_id TEXT PRIMARY KEY,
    customer_unique_id TEXT,
    customer_zip_code_prefix TEXT,
    customer_city TEXT,
    customer_state TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_customers_unique ON dim_customers(customer_unique_id);
CREATE INDEX idx_customers_state ON dim_customers(customer_state);

-- Dimension: Products
CREATE TABLE IF NOT EXISTS dim_products (
    product_id TEXT PRIMARY KEY,
    product_category_name TEXT,
    product_name_length INTEGER,
    product_description_length INTEGER,
    product_photos_qty INTEGER,
    product_weight_g INTEGER,
    product_length_cm INTEGER,
    product_height_cm INTEGER,
    product_width_cm INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_products_category ON dim_products(product_category_name);

-- Dimension: Sellers
CREATE TABLE IF NOT EXISTS dim_sellers (
    seller_id TEXT PRIMARY KEY,
    seller_zip_code_prefix TEXT,
    seller_city TEXT,
    seller_state TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_sellers_state ON dim_sellers(seller_state);
CREATE INDEX idx_sellers_city ON dim_sellers(seller_city);

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

CREATE INDEX idx_geo_zip ON dim_geolocation(geolocation_zip_code_prefix);
CREATE INDEX idx_geo_state ON dim_geolocation(geolocation_state);
CREATE INDEX idx_geo_coords ON dim_geolocation(geolocation_lat, geolocation_lng);

-- Dimension: Product Category Translation
CREATE TABLE IF NOT EXISTS dim_product_category_translation (
    product_category_name TEXT PRIMARY KEY,
    product_category_name_english TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Fact: Orders
CREATE TABLE IF NOT EXISTS fact_orders (
    order_id TEXT PRIMARY KEY,
    customer_id TEXT REFERENCES dim_customers(customer_id),
    order_status TEXT,
    order_purchase_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    order_approved_at TIMESTAMP WITH TIME ZONE,
    order_delivered_carrier_date TIMESTAMP WITH TIME ZONE,
    order_delivered_customer_date TIMESTAMP WITH TIME ZONE,
    order_estimated_delivery_date TIMESTAMP WITH TIME ZONE,
    order_total_cents BIGINT,
    currency TEXT DEFAULT 'BRL',
    order_item_count INTEGER DEFAULT 0,
    source TEXT,
    raw_path TEXT,
    ingest_metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_orders_customer ON fact_orders(customer_id);
CREATE INDEX idx_orders_time ON fact_orders(order_purchase_timestamp DESC);
CREATE INDEX idx_orders_status ON fact_orders(order_status);
CREATE INDEX idx_orders_source ON fact_orders(source);

-- Fact: Payments
CREATE TABLE IF NOT EXISTS fact_payments (
    payment_id SERIAL PRIMARY KEY,
    order_id TEXT REFERENCES fact_orders(order_id),
    payment_sequential INTEGER,
    payment_type TEXT,
    payment_installments INTEGER,
    payment_value_cents BIGINT,
    currency TEXT DEFAULT 'BRL',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_payments_order ON fact_payments(order_id);
CREATE INDEX idx_payments_type ON fact_payments(payment_type);

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

CREATE INDEX idx_reviews_order ON fact_reviews(order_id);
CREATE INDEX idx_reviews_score ON fact_reviews(review_score);
CREATE INDEX idx_reviews_date ON fact_reviews(review_creation_date);

-- Fact: Order Items
CREATE TABLE IF NOT EXISTS fact_order_items (
    order_item_id SERIAL PRIMARY KEY,
    order_id TEXT REFERENCES fact_orders(order_id),
    order_item_sequence INTEGER,
    product_id TEXT REFERENCES dim_products(product_id),
    seller_id TEXT,
    shipping_limit_date TIMESTAMP WITH TIME ZONE,
    price_cents BIGINT,
    freight_value_cents BIGINT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_order_items_order ON fact_order_items(order_id);
CREATE INDEX idx_order_items_product ON fact_order_items(product_id);
CREATE INDEX idx_order_items_seller ON fact_order_items(seller_id);

-- Ingestion Audit Table
CREATE TABLE IF NOT EXISTS ingest_audit (
    run_id TEXT PRIMARY KEY,
    rows_ingested INTEGER DEFAULT 0,
    errors INTEGER DEFAULT 0,
    status TEXT CHECK (status IN ('success', 'failed', 'partial')),
    metadata JSONB,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    finished_at TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER GENERATED ALWAYS AS (
        EXTRACT(EPOCH FROM (finished_at - started_at))::INTEGER
    ) STORED
);

CREATE INDEX idx_audit_status ON ingest_audit(status);
CREATE INDEX idx_audit_finished ON ingest_audit(finished_at DESC);

-- Legacy orders table (keep for backward compatibility)
CREATE TABLE IF NOT EXISTS orders (
    invoice_no TEXT,
    stock_code TEXT,
    description TEXT,
    quantity INTEGER,
    unit_price NUMERIC,
    total_amount NUMERIC,
    invoice_date TIMESTAMP
);
