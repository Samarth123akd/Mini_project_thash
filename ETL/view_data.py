"""
View Brazilian E-commerce Dataset in PostgreSQL
Interactive data browser
"""

import os
from sqlalchemy import create_engine, text
import pandas as pd

os.environ['DATABASE_URL'] = "postgresql://postgres:Sam12kumar%40@localhost:5432/ETL_DB"
engine = create_engine(os.environ['DATABASE_URL'])

pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', 50)

print("=" * 80)
print("  BRAZILIAN E-COMMERCE DATASET VIEWER")
print("=" * 80)

def show_menu():
    print("\nWhat would you like to view?")
    print("  1. Customers (dim_customers)")
    print("  2. Products (dim_products)")
    print("  3. Orders (fact_orders)")
    print("  4. Order Items (fact_order_items)")
    print("  5. Payments (fact_payments)")
    print("  6. Top 10 Best Selling Products")
    print("  7. Top 10 Customers by Spending")
    print("  8. Recent Orders with Details")
    print("  9. Orders by Status")
    print("  0. Exit")
    return input("\nEnter choice (0-9): ").strip()

def view_table(table_name, limit=20):
    """View any table with limit"""
    print(f"\n{'='*80}")
    print(f"  {table_name.upper()}")
    print(f"{'='*80}\n")
    
    query = f"SELECT * FROM {table_name} LIMIT {limit}"
    df = pd.read_sql(query, engine)
    
    print(f"Showing {len(df)} of {get_row_count(table_name):,} total rows\n")
    print(df.to_string(index=False))
    print()

def get_row_count(table_name):
    """Get total row count"""
    with engine.connect() as conn:
        return conn.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()

def top_products():
    """Show top 10 best selling products"""
    print(f"\n{'='*80}")
    print("  TOP 10 BEST SELLING PRODUCTS")
    print(f"{'='*80}\n")
    
    query = text("""
        SELECT 
            p.product_id,
            p.product_category_name,
            COUNT(DISTINCT i.order_id) AS order_count,
            SUM(i.price_cents) / 100.0 AS total_revenue_brl,
            AVG(i.price_cents) / 100.0 AS avg_price_brl
        FROM fact_order_items i
        JOIN dim_products p ON i.product_id = p.product_id
        GROUP BY p.product_id, p.product_category_name
        ORDER BY total_revenue_brl DESC
        LIMIT 10
    """)
    
    df = pd.read_sql(query, engine)
    print(df.to_string(index=False))
    print()

def top_customers():
    """Show top 10 customers by spending"""
    print(f"\n{'='*80}")
    print("  TOP 10 CUSTOMERS BY TOTAL SPENDING")
    print(f"{'='*80}\n")
    
    query = text("""
        SELECT 
            c.customer_id,
            c.customer_city,
            c.customer_state,
            COUNT(DISTINCT o.order_id) AS order_count,
            SUM(o.order_total_cents) / 100.0 AS total_spent_brl,
            AVG(o.order_total_cents) / 100.0 AS avg_order_value_brl
        FROM fact_orders o
        JOIN dim_customers c ON o.customer_id = c.customer_id
        WHERE o.order_total_cents > 0
        GROUP BY c.customer_id, c.customer_city, c.customer_state
        ORDER BY total_spent_brl DESC
        LIMIT 10
    """)
    
    df = pd.read_sql(query, engine)
    print(df.to_string(index=False))
    print()

def recent_orders():
    """Show recent orders with details"""
    print(f"\n{'='*80}")
    print("  20 MOST RECENT ORDERS")
    print(f"{'='*80}\n")
    
    query = text("""
        SELECT 
            o.order_id,
            o.customer_id,
            o.order_status,
            o.order_purchase_timestamp,
            o.order_item_count,
            o.order_total_cents / 100.0 AS total_brl,
            c.customer_city,
            c.customer_state
        FROM fact_orders o
        JOIN dim_customers c ON o.customer_id = c.customer_id
        ORDER BY o.order_purchase_timestamp DESC
        LIMIT 20
    """)
    
    df = pd.read_sql(query, engine)
    print(df.to_string(index=False))
    print()

def orders_by_status():
    """Show order count by status"""
    print(f"\n{'='*80}")
    print("  ORDERS BY STATUS")
    print(f"{'='*80}\n")
    
    query = text("""
        SELECT 
            order_status,
            COUNT(*) AS order_count,
            SUM(order_total_cents) / 100.0 AS total_revenue_brl,
            AVG(order_total_cents) / 100.0 AS avg_order_value_brl
        FROM fact_orders
        GROUP BY order_status
        ORDER BY order_count DESC
    """)
    
    df = pd.read_sql(query, engine)
    print(df.to_string(index=False))
    print()

def main():
    """Main menu loop"""
    while True:
        choice = show_menu()
        
        if choice == '0':
            print("\n👋 Goodbye!")
            break
        elif choice == '1':
            view_table('dim_customers', 20)
        elif choice == '2':
            view_table('dim_products', 20)
        elif choice == '3':
            view_table('fact_orders', 20)
        elif choice == '4':
            view_table('fact_order_items', 20)
        elif choice == '5':
            view_table('fact_payments', 20)
        elif choice == '6':
            top_products()
        elif choice == '7':
            top_customers()
        elif choice == '8':
            recent_orders()
        elif choice == '9':
            orders_by_status()
        else:
            print("❌ Invalid choice. Please try again.")
        
        input("\nPress Enter to continue...")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
