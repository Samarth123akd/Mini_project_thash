"""
Flask Backend API for E-Commerce Dashboard

Provides REST API endpoints for dashboard data visualization.
Connects to PostgreSQL database and serves aggregated analytics data.

Usage:
    $env:DATABASE_URL = "postgresql://etl_user:etl_password_123@localhost:5432/ETL_DB"
    python dashboard/backend_api.py
"""

from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
import os
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Database connection
def get_db_engine():
    """Get database engine from environment variable."""
    db_url = os.environ.get('DATABASE_URL', 'postgresql://etl_user:etl_password_123@localhost:5432/ETL_DB')
    return create_engine(db_url)

# Helper function to execute queries
def execute_query(query, params=None):
    """Execute a SQL query and return results as DataFrame (logs errors with SQL)."""
    try:
        engine = get_db_engine()
        with engine.connect() as conn:
            if params:
                result = pd.read_sql(text(query), conn, params=params)
            else:
                result = pd.read_sql(text(query), conn)
        return result
    except Exception as e:
        print(f"Query error: {e}\nSQL: {query}\nParams: {params}")
        return pd.DataFrame()

def get_start_date():
    """Return start datetime based on 'days' query param; None means all time."""
    raw = request.args.get('days', '30').strip().lower()
    if raw == 'all':
        return None
    try:
        days = int(raw)
        if days <= 0:
            return None
        return datetime.utcnow() - timedelta(days=days)
    except ValueError:
        return None

def date_where(column="order_purchase_timestamp"):
    start = get_start_date()
    if start is None:
        return "", {}
    return f"WHERE {column} >= :start_date", {"start_date": start}

# Routes
@app.route('/')
def index():
    """Serve the main dashboard page."""
    return render_template('index.html')

@app.route('/api/kpis')
def get_kpis():
    """Get key performance indicators."""
    try:
        where, params = date_where()
        query = f"""
            SELECT 
                COUNT(DISTINCT order_id) as total_orders,
                SUM(order_total_cents) / 100.0 as total_revenue,
                AVG(order_total_cents) / 100.0 as avg_order_value,
                COUNT(DISTINCT customer_id) as unique_customers
            FROM fact_orders
            WHERE order_purchase_timestamp IS NOT NULL
            { 'AND' if where else '' } {where.replace('WHERE','') if where else '' }
        """.replace('\n            AND ',' AND ').replace('{  ','{')
        df = execute_query(query, params)
        
        if df.empty:
            return jsonify({
                'total_orders': 0,
                'total_revenue': 0,
                'avg_order_value': 0,
                'unique_customers': 0
            })
        
        return jsonify({
            'total_orders': int(df['total_orders'].iloc[0]),
            'total_revenue': float(df['total_revenue'].iloc[0]),
            'avg_order_value': float(df['avg_order_value'].iloc[0]),
            'unique_customers': int(df['unique_customers'].iloc[0])
        })
    except Exception as e:
        print(f"Error in get_kpis: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/sales-trends')
def get_sales_trends():
    """Sales trends (revenue & order counts) for selected period."""
    try:
        where, params = date_where()
        query = f"""
            SELECT DATE(order_purchase_timestamp) AS date,
                   SUM(order_total_cents)/100.0 AS revenue,
                   COUNT(order_id) AS orders
            FROM fact_orders
            {where}
            GROUP BY DATE(order_purchase_timestamp)
            ORDER BY date
        """
        df = execute_query(query, params)
        if df.empty:
            return jsonify({'dates': [], 'revenue': [], 'orders': []})
        return jsonify({
            'dates': df['date'].astype(str).tolist(),
            'revenue': [round(v,2) for v in df['revenue'].tolist()],
            'orders': df['orders'].tolist()
        })
    except Exception as e:
        print(f"Error in get_sales_trends: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/top-products')
def get_top_products():
    """Top products by (price + freight) revenue with optional date filter."""
    try:
        limit = request.args.get('limit', 10, type=int)
        where, params = date_where("o.order_purchase_timestamp")
        params.update({'limit': limit})
        query = f"""
            SELECT oi.product_id,
                   COALESCE(p.product_category_name, oi.product_id) AS product_name,
                   SUM(oi.price_cents + COALESCE(oi.freight_value_cents,0))/100.0 AS revenue,
                   COUNT(DISTINCT oi.order_id) AS order_count
            FROM fact_order_items oi
            JOIN fact_orders o ON oi.order_id = o.order_id
            LEFT JOIN dim_products p ON oi.product_id = p.product_id
            {where}
            GROUP BY oi.product_id, p.product_category_name
            ORDER BY revenue DESC
            LIMIT :limit
        """
        df = execute_query(query, params)
        if df.empty:
            return jsonify({'product_names': [], 'revenue': []})
        return jsonify({
            'product_names': df['product_name'].tolist(),
            'revenue': [round(v,2) for v in df['revenue'].tolist()],
            'order_count': df['order_count'].tolist()
        })
    except Exception as e:
        print(f"Error in get_top_products: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/customer-segments')
def get_customer_segments():
    """Customer value segments for selected period."""
    try:
        where, params = date_where()
        inner_where = where if where else ''
        query = f"""
            WITH customer_totals AS (
                SELECT customer_id, SUM(order_total_cents)/100.0 AS total_spent
                FROM fact_orders
                {inner_where}
                GROUP BY customer_id
            )
            SELECT segment, COUNT(*) AS count
            FROM (
                SELECT CASE
                    WHEN total_spent < 100 THEN 'Low Value (< R$100)'
                    WHEN total_spent < 500 THEN 'Medium Value (R$100-500)'
                    WHEN total_spent < 1000 THEN 'High Value (R$500-1000)'
                    ELSE 'VIP (> R$1000)'
                END AS segment
                FROM customer_totals
            ) s
            GROUP BY segment
            ORDER BY CASE segment
                WHEN 'Low Value (< R$100)' THEN 1
                WHEN 'Medium Value (R$100-500)' THEN 2
                WHEN 'High Value (R$500-1000)' THEN 3
                ELSE 4 END
        """
        df = execute_query(query, params)
        if df.empty:
            return jsonify({'segments': [], 'counts': []})
        return jsonify({'segments': df['segment'].tolist(), 'counts': df['count'].tolist()})
    except Exception as e:
        print(f"Error in get_customer_segments: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/orders-by-status')
def get_orders_by_status():
    """Order counts by status for selected period."""
    try:
        where, params = date_where()
        query = f"""
            SELECT order_status AS status, COUNT(*) AS count
            FROM fact_orders
            {where}
            GROUP BY order_status
            ORDER BY count DESC
        """
        df = execute_query(query, params)
        if df.empty:
            return jsonify({'statuses': [], 'counts': []})
        return jsonify({'statuses': df['status'].tolist(), 'counts': df['count'].tolist()})
    except Exception as e:
        print(f"Error in get_orders_by_status: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/revenue-by-state')
def get_revenue_by_state():
    """Revenue by customer state for selected period."""
    try:
        limit = request.args.get('limit', 10, type=int)
        where, params = date_where("o.order_purchase_timestamp")
        params.update({'limit': limit})
        query = f"""
            SELECT c.customer_state AS state, SUM(o.order_total_cents)/100.0 AS revenue
            FROM fact_orders o
            JOIN dim_customers c ON o.customer_id = c.customer_id
            WHERE c.customer_state IS NOT NULL
            { 'AND' if where else '' } {where.replace('WHERE','') if where else '' }
            GROUP BY c.customer_state
            ORDER BY revenue DESC
            LIMIT :limit
        """.replace('\n             AND ',' AND ').replace('{  ','{')
        df = execute_query(query, params)
        if df.empty:
            return jsonify({'states': [], 'revenue': []})
        return jsonify({'states': df['state'].tolist(), 'revenue': [round(v,2) for v in df['revenue'].tolist()]})
    except Exception as e:
        print(f"Error in get_revenue_by_state: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/recent-orders')
def get_recent_orders():
    """Recent (or mixed) orders list with date filter."""
    try:
        limit = request.args.get('limit', 20, type=int)
        mix = request.args.get('mix', 'false').lower() == 'true'
        where, params = date_where()
        params.update({'limit': limit})
        order_clause = 'RANDOM()' if mix else 'order_purchase_timestamp DESC'
        query = f"""
            SELECT order_id, customer_id,
                   order_total_cents/100.0 AS total_amount,
                   order_status AS status,
                   order_purchase_timestamp AS date
            FROM fact_orders
            {where}
            ORDER BY {order_clause}
            LIMIT :limit
        """
        df = execute_query(query, params)
        if df.empty:
            return jsonify([])
        df['date'] = df['date'].dt.strftime('%Y-%m-%d %H:%M:%S')
        return jsonify(df.to_dict('records'))
    except Exception as e:
        print(f"Error in get_recent_orders: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/revenue-by-category')
def get_revenue_by_category():
    """Revenue by product category (price + freight) with date filter."""
    try:
        limit = request.args.get('limit', 10, type=int)
        where, params = date_where("o.order_purchase_timestamp")
        params.update({'limit': limit})
        query = f"""
            SELECT COALESCE(t.product_category_name_english, p.product_category_name, 'Unknown') AS category,
                   SUM(oi.price_cents + COALESCE(oi.freight_value_cents,0))/100.0 AS revenue,
                   COUNT(DISTINCT oi.order_id) AS order_count
            FROM fact_order_items oi
            JOIN fact_orders o ON oi.order_id = o.order_id
            LEFT JOIN dim_products p ON oi.product_id = p.product_id
            LEFT JOIN dim_product_category_translation t ON p.product_category_name = t.product_category_name
            {where}
            GROUP BY COALESCE(t.product_category_name_english, p.product_category_name, 'Unknown')
            ORDER BY revenue DESC
            LIMIT :limit
        """
        df = execute_query(query, params)
        if df.empty:
            return jsonify({'categories': [], 'revenue': []})
        return jsonify({'categories': df['category'].tolist(), 'revenue': [round(v,2) for v in df['revenue'].tolist()], 'order_count': df['order_count'].tolist()})
    except Exception as e:
        print(f"Error in get_revenue_by_category: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/reviews-stats')
def get_reviews_stats():
    """Review score distribution for selected period."""
    try:
        where, params = date_where("review_creation_date")
        query = f"""
            SELECT review_score, COUNT(*) AS count
            FROM fact_reviews
            {where}
            GROUP BY review_score
            ORDER BY review_score
        """
        df = execute_query(query, params)
        if df.empty:
            return jsonify({'scores': [], 'counts': []})
        return jsonify({'scores': df['review_score'].tolist(), 'counts': df['count'].tolist()})
    except Exception as e:
        print(f"Error in get_reviews_stats: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/dashboard')
def get_dashboard_bundle():
    """Single payload for all dashboard datasets (reduces network calls)."""
    try:
        bundle = {
            'kpis': get_kpis().json,
            'sales_trends': get_sales_trends().json,
            'top_products': get_top_products().json,
            'customer_segments': get_customer_segments().json,
            'orders_status': get_orders_by_status().json,
            'revenue_by_state': get_revenue_by_state().json,
            'recent_orders': get_recent_orders().json,
            'revenue_by_category': get_revenue_by_category().json,
            'reviews_stats': get_reviews_stats().json
        }
        return jsonify(bundle)
    except Exception as e:
        print(f"Error in get_dashboard_bundle: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/health')
def health():
    """Health check endpoint."""
    try:
        engine = get_db_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return jsonify({'status': 'healthy', 'database': 'connected'})
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

if __name__ == '__main__':
    print("=" * 60)
    print("  E-Commerce Dashboard API Server")
    print("=" * 60)
    print("\n📊 Starting Flask server...")
    print("🌐 Dashboard URL: http://localhost:5000")
    print("🔌 API Base URL: http://localhost:5000/api")
    print("\nAvailable endpoints:")
    print("  - GET /api/kpis")
    print("  - GET /api/sales-trends")
    print("  - GET /api/top-products")
    print("  - GET /api/customer-segments")
    print("  - GET /api/orders-by-status")
    print("  - GET /api/revenue-by-state")
    print("  - GET /api/recent-orders")
    print("  - GET /api/revenue-by-category")
    print("  - GET /api/reviews-stats")
    print("  - GET /api/health")
    print("\n" + "=" * 60)
    
    app.run(host='0.0.0.0', port=5000, debug=True)
