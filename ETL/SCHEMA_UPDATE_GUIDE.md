# Complete Brazilian Dataset Schema Setup

## 📋 Summary of Changes

Your Brazilian dataset has **9 CSV files** but your database only had **5 tables**. I've added the missing tables to match the complete dataset.

## 🗄️ Complete Database Schema

### Dimension Tables (5)
1. ✅ **dim_customers** - Customer information (already existed)
2. ✅ **dim_products** - Product details (already existed)
3. 🆕 **dim_sellers** - Seller information (NEW)
4. 🆕 **dim_geolocation** - Geolocation data (NEW)
5. 🆕 **dim_product_category_translation** - Category translations (NEW)

### Fact Tables (4)
1. ✅ **fact_orders** - Order headers (already existed)
2. ✅ **fact_order_items** - Order line items (already existed)
3. ✅ **fact_payments** - Payment transactions (already existed)
4. 🆕 **fact_reviews** - Customer reviews (NEW)

### Supporting Tables (2)
- ✅ **ingest_audit** - ETL audit trail (already existed)
- ✅ **orders** - Legacy table (already existed)

## 📂 Brazilian Dataset Files Mapping

| CSV File | Maps to Table | Status |
|----------|---------------|--------|
| `olist_customers_dataset.csv` | dim_customers | ✅ Existing |
| `olist_products_dataset.csv` | dim_products | ✅ Existing |
| `olist_sellers_dataset.csv` | **dim_sellers** | 🆕 NEW |
| `olist_geolocation_dataset.csv` | **dim_geolocation** | 🆕 NEW |
| `product_category_name_translation.csv` | **dim_product_category_translation** | 🆕 NEW |
| `olist_orders_dataset.csv` | fact_orders | ✅ Existing |
| `olist_order_items_dataset.csv` | fact_order_items | ✅ Existing |
| `olist_order_payments_dataset.csv` | fact_payments | ✅ Existing |
| `olist_order_reviews_dataset.csv` | **fact_reviews** | 🆕 NEW |

## 🚀 Setup Instructions

### Step 1: Add Missing Tables to Database

Open **pgAdmin 4** and follow these steps:

1. Connect to your `ETL_DB` database
2. Click **Tools** → **Query Tool**
3. Open the file: `sql/add_missing_tables.sql`
4. Click **Execute** (F5)

This will create all 4 missing tables and grant permissions to `etl_user`.

### Step 2: Load Complete Dataset

After creating the tables, run the loading script:

```powershell
cd C:\Users\samar\Desktop\prjct_thash\ETL
$env:DATABASE_URL = "postgresql://etl_user:etl_password_123@localhost:5432/ETL_DB"
python scripts/load_brazilian_data.py
```

This will load all 9 CSV files into the database.

### Step 3: Verify Data

Check that all data was loaded successfully:

```powershell
python scripts/view_data.py
```

Or query in pgAdmin:

```sql
-- Count rows in all tables
SELECT 'dim_customers' as table_name, COUNT(*) as row_count FROM dim_customers
UNION ALL
SELECT 'dim_products', COUNT(*) FROM dim_products
UNION ALL
SELECT 'dim_sellers', COUNT(*) FROM dim_sellers
UNION ALL
SELECT 'dim_geolocation', COUNT(*) FROM dim_geolocation
UNION ALL
SELECT 'dim_product_category_translation', COUNT(*) FROM dim_product_category_translation
UNION ALL
SELECT 'fact_orders', COUNT(*) FROM fact_orders
UNION ALL
SELECT 'fact_order_items', COUNT(*) FROM fact_order_items
UNION ALL
SELECT 'fact_payments', COUNT(*) FROM fact_payments
UNION ALL
SELECT 'fact_reviews', COUNT(*) FROM fact_reviews;
```

## 📊 New Tables Details

### dim_sellers
Stores seller (merchant) information from the Brazilian marketplace.

**Columns:**
- `seller_id` (PK) - Unique seller identifier
- `seller_zip_code_prefix` - Seller location zip code
- `seller_city` - Seller city
- `seller_state` - Seller state (e.g., SP, RJ)
- `created_at`, `updated_at` - Timestamps

### dim_geolocation
Geographic coordinates for Brazilian zip codes.

**Columns:**
- `geolocation_id` (PK, auto-increment) - Unique ID
- `geolocation_zip_code_prefix` - Zip code
- `geolocation_lat` - Latitude
- `geolocation_lng` - Longitude
- `geolocation_city` - City name
- `geolocation_state` - State code
- `created_at` - Timestamp

**Note:** This table has ~1 million rows with many duplicates per zip code.

### dim_product_category_translation
Maps Portuguese product categories to English translations.

**Columns:**
- `product_category_name` (PK) - Portuguese category name
- `product_category_name_english` - English translation
- `created_at` - Timestamp

### fact_reviews
Customer reviews and ratings for orders.

**Columns:**
- `review_id` (PK) - Unique review identifier
- `order_id` (FK → fact_orders) - Associated order
- `review_score` - Rating (1-5)
- `review_comment_title` - Review title
- `review_comment_message` - Review text
- `review_creation_date` - When review was created
- `review_answer_timestamp` - When seller responded
- `created_at` - Timestamp

## 🔗 Relationships

```
dim_customers ─┬─► fact_orders ─┬─► fact_order_items ──► dim_products
               │                 │
               │                 ├─► fact_payments
               │                 │
               │                 └─► fact_reviews
               │
dim_sellers ───┴──────────────────► fact_order_items

dim_geolocation (linked by zip_code_prefix to customers/sellers)
dim_product_category_translation (linked by category_name to products)
```

## ✅ What Changed

### Files Modified:
1. **`sql/schema.sql`** - Added 4 new table definitions
2. **`scripts/load_brazilian_data.py`** - Added loading functions for:
   - `load_sellers()`
   - `load_geolocation()`
   - `load_category_translation()`
   - `load_reviews()`

### Files Created:
1. **`sql/add_missing_tables.sql`** - SQL script to add tables to existing DB
2. **`scripts/update_schema.py`** - Python script to update schema (alternative method)

## 🎯 Next Steps

1. ✅ Execute `sql/add_missing_tables.sql` in pgAdmin4
2. ✅ Run `python scripts/load_brazilian_data.py`
3. ✅ Verify all tables have data
4. 🚀 Your database now fully matches the Brazilian dataset!

## 📝 Expected Row Counts

After loading, you should see approximately:

- dim_customers: ~99,441 rows
- dim_products: ~32,951 rows
- dim_sellers: ~3,095 rows
- dim_geolocation: ~1,000,163 rows (many duplicates)
- dim_product_category_translation: ~71 rows
- fact_orders: ~99,441 rows
- fact_order_items: ~112,650 rows
- fact_payments: ~103,886 rows
- fact_reviews: ~99,224 rows

Total: ~1.55 million rows across all tables
