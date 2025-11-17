import os
from sqlalchemy import create_engine, text

url = os.getenv("DATABASE_URL", "postgresql://postgres:Sam12kumar%40@localhost:5432/ETL_DB")
engine = create_engine(url)
with engine.connect() as c:
    total = c.execute(text("select count(*) from fact_orders")).scalar()
    delivered = c.execute(text("select count(*) from fact_orders where order_status='delivered'"))
    delivered = delivered.scalar()
print(f"TOTAL_ORDERS {total}")
print(f"DELIVERED_ORDERS {delivered}")
if delivered:
    print(f"DELIVERED_SAMPLE_USED 10000")
    print(f"DELIVERED_SAMPLE_PERCENT {10000/delivered*100:.2f}")
    print(f"TOTAL_PERCENT_USED {10000/total*100:.2f}")
