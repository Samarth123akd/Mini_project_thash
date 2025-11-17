"""
Comprehensive E-Commerce Analytics Backend
Leverages ALL database tables: dim_customers, dim_products, dim_sellers, 
fact_orders, fact_order_items, fact_payments, fact_reviews
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import os
import joblib
import json

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# Database connection
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://etl_user:etl_password_123@localhost:5432/ETL_DB')
engine = create_engine(DATABASE_URL)

# Load ML model
ML_MODEL_PATH = 'ml/models/order_total_model.pkl'
ML_METRICS_PATH = 'ml/reports/evaluation_summary.json'
ml_model = None
ml_metrics = None

try:
    if os.path.exists(ML_MODEL_PATH):
        ml_model = joblib.load(ML_MODEL_PATH)
        print("✅ ML Model loaded successfully")
    if os.path.exists(ML_METRICS_PATH):
        with open(ML_METRICS_PATH, 'r') as f:
            ml_metrics = json.load(f)
        print("✅ ML Metrics loaded successfully")
except Exception as e:
    print(f"⚠️ ML Model loading error: {e}")

# ============================================
# HELPER FUNCTIONS
# ============================================

def get_date_filter(days=None):
    """Generate SQL date filter"""
    if days and days != 'all':
        cutoff_date = datetime.now() - timedelta(days=int(days))
        return f"AND order_purchase_timestamp >= '{cutoff_date.isoformat()}'"
    return ""

def query_to_dict(query):
    """Execute query and return as list of dicts"""
    with engine.connect() as conn:
        result = conn.execute(text(query))
        columns = result.keys()
        return [dict(zip(columns, row)) for row in result]

# ============================================
# DASHBOARD OVERVIEW
# ============================================

@app.route('/api/overview', methods=['GET'])
def get_overview():
    """Complete dashboard overview with KPIs"""
    days = request.args.get('days', 'all')
    date_filter = get_date_filter(days)
    
    try:
        with engine.connect() as conn:
            # Order metrics
            order_query = text(f"""
                SELECT 
                    COUNT(DISTINCT order_id) as total_orders,
                    COUNT(DISTINCT customer_id) as total_customers,
                    SUM(COALESCE(order_total_cents, 0)) / 100.0 as total_revenue,
                    AVG(COALESCE(order_total_cents, 0)) / 100.0 as avg_order_value,
                    SUM(order_item_count) as total_items_sold
                FROM fact_orders
                WHERE 1=1 {date_filter}
            """)
            order_metrics = dict(conn.execute(order_query).fetchone()._mapping)
            
            # Product metrics
            product_count = conn.execute(text("SELECT COUNT(*) FROM dim_products")).scalar()
            
            # Seller metrics
            seller_query = text(f"""
                SELECT COUNT(DISTINCT s.seller_id) as active_sellers
                FROM dim_sellers s
                INNER JOIN fact_order_items oi ON s.seller_id = oi.seller_id
                INNER JOIN fact_orders o ON oi.order_id = o.order_id
                WHERE 1=1 {date_filter}
            """)
            seller_count = conn.execute(seller_query).scalar()
            
            # Payment metrics
            payment_query = text(f"""
                SELECT 
                    COUNT(*) as total_payments,
                    AVG(payment_installments) as avg_installments
                FROM fact_payments p
                INNER JOIN fact_orders o ON p.order_id = o.order_id
                WHERE 1=1 {date_filter}
            """)
            payment_metrics = dict(conn.execute(payment_query).fetchone()._mapping)
            
            # Order status distribution
            status_query = text(f"""
                SELECT 
                    order_status,
                    COUNT(*) as count
                FROM fact_orders
                WHERE 1=1 {date_filter}
                GROUP BY order_status
                ORDER BY count DESC
            """)
            status_dist = [dict(row._mapping) for row in conn.execute(status_query)]
            
            return jsonify({
                'success': True,
                'data': {
                    'total_orders': int(order_metrics['total_orders'] or 0),
                    'total_customers': int(order_metrics['total_customers'] or 0),
                    'total_revenue': float(order_metrics['total_revenue'] or 0),
                    'avg_order_value': float(order_metrics['avg_order_value'] or 0),
                    'total_items_sold': int(order_metrics['total_items_sold'] or 0),
                    'total_products': product_count,
                    'active_sellers': seller_count or 0,
                    'total_payments': int(payment_metrics['total_payments'] or 0),
                    'avg_installments': float(payment_metrics['avg_installments'] or 0),
                    'order_status_distribution': status_dist
                }
            })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================
# ORDER ANALYTICS
# ============================================

@app.route('/api/orders/timeline', methods=['GET'])
def get_orders_timeline():
    """Daily order trends"""
    days = request.args.get('days', '90')
    date_filter = get_date_filter(days)
    
    query = f"""
        SELECT 
            DATE(order_purchase_timestamp) as date,
            COUNT(*) as order_count,
            SUM(COALESCE(order_total_cents, 0)) / 100.0 as revenue,
            AVG(COALESCE(order_total_cents, 0)) / 100.0 as avg_order_value
        FROM fact_orders
        WHERE 1=1 {date_filter}
        GROUP BY DATE(order_purchase_timestamp)
        ORDER BY date
    """
    
    data = query_to_dict(query)
    for row in data:
        row['date'] = row['date'].isoformat() if row['date'] else None
    
    return jsonify({'success': True, 'data': data})

@app.route('/api/orders/by-status', methods=['GET'])
def get_orders_by_status():
    """Order status breakdown over time"""
    days = request.args.get('days', '90')
    date_filter = get_date_filter(days)
    
    query = f"""
        SELECT 
            DATE(order_purchase_timestamp) as date,
            order_status,
            COUNT(*) as count
        FROM fact_orders
        WHERE 1=1 {date_filter}
        GROUP BY DATE(order_purchase_timestamp), order_status
        ORDER BY date, order_status
    """
    
    data = query_to_dict(query)
    for row in data:
        row['date'] = row['date'].isoformat() if row['date'] else None
    
    return jsonify({'success': True, 'data': data})

@app.route('/api/orders/delivery-performance', methods=['GET'])
def get_delivery_performance():
    """Delivery time analysis"""
    days = request.args.get('days', 'all')
    date_filter = get_date_filter(days)
    
    query = f"""
        SELECT 
            EXTRACT(EPOCH FROM (order_delivered_customer_date - order_purchase_timestamp)) / 86400 as delivery_days,
            order_status,
            COUNT(*) as count
        FROM fact_orders
        WHERE order_delivered_customer_date IS NOT NULL 
        AND order_purchase_timestamp IS NOT NULL
        {date_filter}
        GROUP BY 1, 2
        HAVING EXTRACT(EPOCH FROM (order_delivered_customer_date - order_purchase_timestamp)) / 86400 > 0
        ORDER BY delivery_days
    """
    
    data = query_to_dict(query)
    
    # Calculate statistics
    if data:
        delivery_times = [float(row['delivery_days']) for row in data for _ in range(int(row['count']))]
        stats = {
            'avg_delivery_days': np.mean(delivery_times),
            'median_delivery_days': np.median(delivery_times),
            'min_delivery_days': np.min(delivery_times),
            'max_delivery_days': np.max(delivery_times),
            'std_delivery_days': np.std(delivery_times)
        }
    else:
        stats = {}
    
    return jsonify({'success': True, 'data': data, 'stats': stats})

# ============================================
# CUSTOMER ANALYTICS
# ============================================

@app.route('/api/customers/geography', methods=['GET'])
def get_customers_geography():
    """Customer distribution by state"""
    query = """
        SELECT 
            c.customer_state,
            COUNT(DISTINCT c.customer_id) as customer_count,
            COUNT(DISTINCT o.order_id) as order_count,
            SUM(COALESCE(o.order_total_cents, 0)) / 100.0 as total_revenue
        FROM dim_customers c
        LEFT JOIN fact_orders o ON c.customer_id = o.customer_id
        WHERE c.customer_state IS NOT NULL
        GROUP BY c.customer_state
        ORDER BY customer_count DESC
    """
    
    data = query_to_dict(query)
    return jsonify({'success': True, 'data': data})

@app.route('/api/customers/top-cities', methods=['GET'])
def get_top_cities():
    """Top cities by customer count"""
    limit = request.args.get('limit', '20')
    
    query = f"""
        SELECT 
            customer_city,
            customer_state,
            COUNT(DISTINCT c.customer_id) as customer_count,
            COUNT(DISTINCT o.order_id) as order_count
        FROM dim_customers c
        LEFT JOIN fact_orders o ON c.customer_id = o.customer_id
        WHERE customer_city IS NOT NULL
        GROUP BY customer_city, customer_state
        ORDER BY customer_count DESC
        LIMIT {limit}
    """
    
    data = query_to_dict(query)
    return jsonify({'success': True, 'data': data})

@app.route('/api/customers/lifetime-value', methods=['GET'])
def get_customer_lifetime_value():
    """Customer lifetime value segments"""
    query = """
        WITH customer_totals AS (
            SELECT 
                customer_id,
                COUNT(order_id) as order_count,
                SUM(COALESCE(order_total_cents, 0)) / 100.0 as lifetime_value,
                MAX(order_purchase_timestamp) as last_order_date,
                MIN(order_purchase_timestamp) as first_order_date
            FROM fact_orders
            GROUP BY customer_id
        )
        SELECT 
            CASE 
                WHEN lifetime_value >= 5000 THEN 'VIP (R$ 5000+)'
                WHEN lifetime_value >= 2000 THEN 'High (R$ 2000-5000)'
                WHEN lifetime_value >= 500 THEN 'Medium (R$ 500-2000)'
                ELSE 'Low (< R$ 500)'
            END as segment,
            COUNT(*) as customer_count,
            AVG(lifetime_value) as avg_lifetime_value,
            AVG(order_count) as avg_orders_per_customer
        FROM customer_totals
        GROUP BY 1
        ORDER BY avg_lifetime_value DESC
    """
    
    data = query_to_dict(query)
    return jsonify({'success': True, 'data': data})

@app.route('/api/customers/cohort', methods=['GET'])
def get_cohort_analysis():
    """Monthly cohort retention"""
    query = """
        WITH first_purchase AS (
            SELECT 
                customer_id,
                DATE_TRUNC('month', MIN(order_purchase_timestamp)) as cohort_month
            FROM fact_orders
            GROUP BY customer_id
        ),
        monthly_activity AS (
            SELECT 
                fp.customer_id,
                fp.cohort_month,
                DATE_TRUNC('month', o.order_purchase_timestamp) as activity_month
            FROM first_purchase fp
            INNER JOIN fact_orders o ON fp.customer_id = o.customer_id
        )
        SELECT 
            cohort_month,
            activity_month,
            COUNT(DISTINCT customer_id) as customer_count
        FROM monthly_activity
        GROUP BY cohort_month, activity_month
        ORDER BY cohort_month, activity_month
        LIMIT 1000
    """
    
    data = query_to_dict(query)
    for row in data:
        row['cohort_month'] = row['cohort_month'].isoformat() if row['cohort_month'] else None
        row['activity_month'] = row['activity_month'].isoformat() if row['activity_month'] else None
    
    return jsonify({'success': True, 'data': data})

# ============================================
# PRODUCT ANALYTICS
# ============================================

@app.route('/api/products/top-selling', methods=['GET'])
def get_top_selling_products():
    """Top selling products"""
    days = request.args.get('days', 'all')
    limit = request.args.get('limit', '20')
    date_filter = get_date_filter(days)
    
    query = f"""
        SELECT 
            p.product_id,
            p.product_category_name,
            COUNT(DISTINCT oi.order_id) as order_count,
            COUNT(oi.order_item_id) as total_quantity_sold,
            SUM(oi.price_cents) / 100.0 as total_revenue,
            AVG(oi.price_cents) / 100.0 as avg_price
        FROM dim_products p
        INNER JOIN fact_order_items oi ON p.product_id = oi.product_id
        INNER JOIN fact_orders o ON oi.order_id = o.order_id
        WHERE 1=1 {date_filter}
        GROUP BY p.product_id, p.product_category_name
        ORDER BY total_quantity_sold DESC
        LIMIT {limit}
    """
    
    data = query_to_dict(query)
    return jsonify({'success': True, 'data': data})

@app.route('/api/products/categories', methods=['GET'])
def get_product_categories():
    """Product category performance"""
    days = request.args.get('days', 'all')
    date_filter = get_date_filter(days)
    
    query = f"""
        SELECT 
            COALESCE(p.product_category_name, 'Unknown') as category,
            COUNT(DISTINCT p.product_id) as product_count,
            COUNT(DISTINCT oi.order_id) as order_count,
            COUNT(oi.order_item_id) as total_quantity,
            SUM(oi.price_cents) / 100.0 as total_revenue,
            AVG(oi.price_cents) / 100.0 as avg_price
        FROM dim_products p
        INNER JOIN fact_order_items oi ON p.product_id = oi.product_id
        INNER JOIN fact_orders o ON oi.order_id = o.order_id
        WHERE 1=1 {date_filter}
        GROUP BY p.product_category_name
        ORDER BY total_revenue DESC
    """
    
    data = query_to_dict(query)
    return jsonify({'success': True, 'data': data})

@app.route('/api/products/price-distribution', methods=['GET'])
def get_price_distribution():
    """Product price ranges"""
    query = """
        WITH price_ranges AS (
            SELECT 
                CASE 
                    WHEN price_cents < 5000 THEN 'R$ 0-50'
                    WHEN price_cents < 10000 THEN 'R$ 50-100'
                    WHEN price_cents < 20000 THEN 'R$ 100-200'
                    WHEN price_cents < 50000 THEN 'R$ 200-500'
                    ELSE 'R$ 500+'
                END as price_range,
                CASE 
                    WHEN price_cents < 5000 THEN 1
                    WHEN price_cents < 10000 THEN 2
                    WHEN price_cents < 20000 THEN 3
                    WHEN price_cents < 50000 THEN 4
                    ELSE 5
                END as range_order,
                price_cents
            FROM fact_order_items
        )
        SELECT 
            price_range,
            COUNT(*) as item_count,
            SUM(price_cents) / 100.0 as total_revenue
        FROM price_ranges
        GROUP BY price_range, range_order
        ORDER BY range_order
    """
    
    data = query_to_dict(query)
    return jsonify({'success': True, 'data': data})

# ============================================
# SELLER ANALYTICS
# ============================================

@app.route('/api/sellers/performance', methods=['GET'])
def get_seller_performance():
    """Top seller performance"""
    days = request.args.get('days', 'all')
    limit = request.args.get('limit', '20')
    date_filter = get_date_filter(days)
    
    query = f"""
        SELECT 
            s.seller_id,
            s.seller_city,
            s.seller_state,
            COUNT(DISTINCT oi.order_id) as order_count,
            COUNT(oi.order_item_id) as items_sold,
            SUM(oi.price_cents) / 100.0 as total_revenue,
            AVG(oi.price_cents) / 100.0 as avg_item_price
        FROM dim_sellers s
        INNER JOIN fact_order_items oi ON s.seller_id = oi.seller_id
        INNER JOIN fact_orders o ON oi.order_id = o.order_id
        WHERE 1=1 {date_filter}
        GROUP BY s.seller_id, s.seller_city, s.seller_state
        ORDER BY total_revenue DESC
        LIMIT {limit}
    """
    
    data = query_to_dict(query)
    return jsonify({'success': True, 'data': data})

@app.route('/api/sellers/geography', methods=['GET'])
def get_seller_geography():
    """Seller distribution by state"""
    days = request.args.get('days', 'all')
    date_filter = get_date_filter(days)
    
    query = f"""
        SELECT 
            s.seller_state,
            COUNT(DISTINCT s.seller_id) as seller_count,
            COUNT(DISTINCT oi.order_id) as order_count,
            SUM(oi.price_cents) / 100.0 as total_revenue
        FROM dim_sellers s
        INNER JOIN fact_order_items oi ON s.seller_id = oi.seller_id
        INNER JOIN fact_orders o ON oi.order_id = o.order_id
        WHERE s.seller_state IS NOT NULL {date_filter}
        GROUP BY s.seller_state
        ORDER BY total_revenue DESC
    """
    
    data = query_to_dict(query)
    return jsonify({'success': True, 'data': data})

# ============================================
# PAYMENT ANALYTICS
# ============================================

@app.route('/api/payments/methods', methods=['GET'])
def get_payment_methods():
    """Payment type distribution"""
    days = request.args.get('days', 'all')
    date_filter = get_date_filter(days)
    
    query = f"""
        SELECT 
            p.payment_type,
            COUNT(*) as transaction_count,
            SUM(p.payment_value_cents) / 100.0 as total_value,
            AVG(p.payment_value_cents) / 100.0 as avg_value,
            AVG(p.payment_installments) as avg_installments
        FROM fact_payments p
        INNER JOIN fact_orders o ON p.order_id = o.order_id
        WHERE 1=1 {date_filter}
        GROUP BY p.payment_type
        ORDER BY transaction_count DESC
    """
    
    data = query_to_dict(query)
    return jsonify({'success': True, 'data': data})

@app.route('/api/payments/installments', methods=['GET'])
def get_payment_installments():
    """Installment analysis"""
    days = request.args.get('days', 'all')
    date_filter = get_date_filter(days)
    
    query = f"""
        SELECT 
            payment_installments,
            COUNT(*) as transaction_count,
            SUM(payment_value_cents) / 100.0 as total_value,
            AVG(payment_value_cents) / 100.0 as avg_value
        FROM fact_payments p
        INNER JOIN fact_orders o ON p.order_id = o.order_id
        WHERE 1=1 {date_filter}
        GROUP BY payment_installments
        ORDER BY payment_installments
    """
    
    data = query_to_dict(query)
    return jsonify({'success': True, 'data': data})

# ============================================
# ML MODEL ENDPOINTS
# ============================================

@app.route('/api/ml/model-info', methods=['GET'])
def get_ml_model_info():
    """ML model performance metrics"""
    if ml_metrics:
        return jsonify({
            'success': True,
            'data': {
                'r2_score': ml_metrics['regression']['r2'],
                'mae': ml_metrics['regression']['mae'],
                'rmse': ml_metrics['regression']['rmse'],
                'roc_auc': ml_metrics['classification']['roc_auc'],
                'samples_total': ml_metrics['samples_total'],
                'features': ml_metrics['features']
            }
        })
    return jsonify({'success': False, 'error': 'ML metrics not loaded'}), 404

@app.route('/api/ml/predict', methods=['POST'])
def predict_order_value():
    """Predict order value using ML model"""
    if not ml_model:
        return jsonify({'success': False, 'error': 'ML model not loaded'}), 404
    
    try:
        data = request.json
        features = [
            data.get('num_items', 1),
            data.get('avg_item_price', 100),
            data.get('total_items_price', 100),
            data.get('freight_value', 10)
        ]
        
        prediction = ml_model.predict([features])[0]
        
        return jsonify({
            'success': True,
            'data': {
                'predicted_value': float(prediction),
                'features_used': {
                    'num_items': features[0],
                    'avg_item_price': features[1],
                    'total_items_price': features[2],
                    'freight_value': features[3]
                }
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

# ============================================
# HEALTH CHECK
# ============================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """API health check"""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        return jsonify({
            'success': True,
            'status': 'healthy',
            'database': 'connected',
            'ml_model': 'loaded' if ml_model else 'not loaded'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': str(e)
        }), 500

# ============================================
# SERVE DASHBOARD
# ============================================

@app.route('/')
def index():
    """Serve dashboard HTML"""
    from flask import render_template
    return render_template('ecommerce_dashboard.html')

if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("  E-Commerce ETL Analytics Dashboard")
    print("=" * 60)
    print(f"API Server: http://localhost:5001")
    print(f"API Endpoints: http://localhost:5001/api/")
    print(f"ML Model: {'Loaded' if ml_model else 'Not Loaded'}")
    print("=" * 60 + "\n")
    
    app.run(host='0.0.0.0', port=5001, debug=True)
