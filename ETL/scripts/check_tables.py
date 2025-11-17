from sqlalchemy import create_engine, text
import os

os.environ['DATABASE_URL'] = 'postgresql://etl_user:etl_password_123@localhost:5432/ETL_DB'
engine = create_engine(os.environ['DATABASE_URL'])

with engine.connect() as conn:
    tables = ['dim_customers', 'dim_products', 'dim_sellers', 'fact_orders', 'fact_order_items', 'fact_payments', 'fact_reviews']
    print("Table Row Counts:")
    print("-" * 40)
    for t in tables:
        try:
            count = conn.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar()
            print(f'{t}: {count:,}')
        except Exception as e:
            print(f'{t}: ERROR - {e}')
