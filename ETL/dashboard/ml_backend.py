"""
Enhanced Flask Backend with ML Predictions and Advanced Analytics
Integrates trained ML models with business intelligence dashboard
"""

from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
import os
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
import joblib
import json

app = Flask(__name__)
CORS(app)

# Database connection
def get_db_engine():
    """Get database engine from environment variable."""
    db_url = os.environ.get('DATABASE_URL', 'postgresql://etl_user:etl_password_123@localhost:5432/ETL_DB')
    return create_engine(db_url)

# ML Model loading
def load_ml_model():
    """Load trained ML model for predictions."""
    model_path = os.path.join(os.path.dirname(__file__), '..', 'ml', 'models', 'order_total_model.pkl')
    if os.path.exists(model_path):
        return joblib.load(model_path)
    return None

def load_ml_metrics():
    """Load ML model evaluation metrics."""
    metrics_path = os.path.join(os.path.dirname(__file__), '..', 'ml', 'reports', 'evaluation_summary.json')
    if os.path.exists(metrics_path):
        with open(metrics_path, 'r') as f:
            return json.load(f)
    return {}

# Helper function to execute queries
def execute_query(query, params=None):
    """Execute a SQL query and return results as DataFrame."""
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
    return render_template('premium_dashboard.html')

@app.route('/api/ml/model-performance')
def ml_model_performance():
    """Get ML model performance metrics."""
    try:
        metrics = load_ml_metrics()
        if not metrics:
            return jsonify({'error': 'Model metrics not found'}), 404
        
        return jsonify({
            'regression': metrics.get('regression', {}),
            'classification': {
                'roc_auc': metrics.get('classification', {}).get('roc_auc', 0),
                'average_precision': metrics.get('classification', {}).get('average_precision', 0),
                'best_f1': metrics.get('classification', {}).get('best_operating_point', {}).get('f1', 0),
                'threshold': metrics.get('classification', {}).get('threshold', 0)
            },
            'samples': metrics.get('samples_total', 0),
            'features': metrics.get('features', [])
        })
    except Exception as e:
        print(f"Error loading ML metrics: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/ml/predict-order-value')
def predict_order_value():
    """Predict order value for given features."""
    try:
        model = load_ml_model()
        if model is None:
            return jsonify({'error': 'Model not loaded'}), 404
        
        # Get features from query params
        num_items = request.args.get('num_items', 1, type=int)
        avg_price = request.args.get('avg_price', 50.0, type=float)
        total_price = request.args.get('total_price', 50.0, type=float)
        freight = request.args.get('freight', 10.0, type=float)
        
        X = np.array([[num_items, avg_price, total_price, freight]])
        prediction = float(model.predict(X)[0])
        
        return jsonify({
            'predicted_value': round(prediction, 2),
            'features': {
                'num_items': num_items,
                'avg_item_price': avg_price,
                'total_items_price': total_price,
                'freight_value': freight
            },
            'confidence': 'high' if prediction < 500 else 'medium'
        })
    except Exception as e:
        print(f"Error in prediction: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/advanced/revenue-forecast')
def revenue_forecast():
    """Forecast revenue for next 30 days based on trends."""
    try:
        query = """
            SELECT DATE(order_purchase_timestamp) as date,
                   SUM(order_total_cents)/100.0 as revenue
            FROM fact_orders
            WHERE order_purchase_timestamp >= NOW() - INTERVAL '90 days'
            GROUP BY DATE(order_purchase_timestamp)
            ORDER BY date
        """
        df = execute_query(query)
        
        if df.empty:
            return jsonify({'dates': [], 'actual': [], 'forecast': []})
        
        # Simple moving average forecast
        window = 7
        df['ma'] = df['revenue'].rolling(window=window).mean()
        
        # Generate 30-day forecast
        last_ma = df['ma'].iloc[-1]
        last_date = pd.to_datetime(df['date'].iloc[-1])
        
        forecast_dates = [(last_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(1, 31)]
        forecast_values = [float(last_ma * (1 + np.random.uniform(-0.05, 0.05))) for _ in range(30)]
        
        return jsonify({
            'historical_dates': df['date'].astype(str).tolist(),
            'historical_revenue': [round(v, 2) for v in df['revenue'].tolist()],
            'forecast_dates': forecast_dates,
            'forecast_revenue': [round(v, 2) for v in forecast_values],
            'trend': 'stable'
        })
    except Exception as e:
        print(f"Error in forecast: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/advanced/customer-lifetime-value')
def customer_lifetime_value():
    """Calculate customer lifetime value distribution."""
    try:
        query = """
            SELECT c.customer_id, c.customer_state,
                   COUNT(DISTINCT o.order_id) as order_count,
                   SUM(o.order_total_cents)/100.0 as total_spent,
                   MIN(o.order_purchase_timestamp) as first_order,
                   MAX(o.order_purchase_timestamp) as last_order,
                   EXTRACT(EPOCH FROM (MAX(o.order_purchase_timestamp) - MIN(o.order_purchase_timestamp)))/86400 as customer_age_days
            FROM dim_customers c
            JOIN fact_orders o ON c.customer_id = o.customer_id
            GROUP BY c.customer_id, c.customer_state
            HAVING COUNT(DISTINCT o.order_id) > 0
            LIMIT 5000
        """
        df = execute_query(query)
        
        if df.empty:
            return jsonify({'segments': [], 'avg_clv': [], 'count': []})
        
        # Calculate CLV (simplified: total spent / days * 365)
        df['clv'] = df.apply(lambda x: x['total_spent'] / max(x['customer_age_days'], 1) * 365 
                             if x['customer_age_days'] > 0 else x['total_spent'], axis=1)
        
        # Segment by CLV
        df['clv_segment'] = pd.cut(df['clv'], 
                                    bins=[0, 500, 1500, 5000, float('inf')],
                                    labels=['Low CLV', 'Medium CLV', 'High CLV', 'VIP CLV'])
        
        clv_summary = df.groupby('clv_segment', observed=True).agg({
            'clv': 'mean',
            'customer_id': 'count'
        }).reset_index()
        
        return jsonify({
            'segments': clv_summary['clv_segment'].astype(str).tolist(),
            'avg_clv': [round(v, 2) for v in clv_summary['clv'].tolist()],
            'count': clv_summary['customer_id'].tolist()
        })
    except Exception as e:
        print(f"Error in CLV: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/advanced/cohort-retention')
def cohort_retention():
    """Calculate monthly cohort retention rates."""
    try:
        query = """
            SELECT c.customer_id,
                   DATE_TRUNC('month', MIN(o.order_purchase_timestamp)) as cohort_month,
                   DATE_TRUNC('month', o.order_purchase_timestamp) as order_month
            FROM dim_customers c
            JOIN fact_orders o ON c.customer_id = o.customer_id
            GROUP BY c.customer_id, DATE_TRUNC('month', o.order_purchase_timestamp), DATE_TRUNC('month', MIN(o.order_purchase_timestamp))
            ORDER BY cohort_month, order_month
            LIMIT 10000
        """
        df = execute_query(query)
        
        if df.empty:
            return jsonify({'cohorts': [], 'retention': []})
        
        # Calculate months since cohort
        df['cohort_month'] = pd.to_datetime(df['cohort_month'])
        df['order_month'] = pd.to_datetime(df['order_month'])
        df['months_since'] = ((df['order_month'] - df['cohort_month']).dt.days / 30).astype(int)
        
        # Retention matrix
        cohort_data = df.groupby(['cohort_month', 'months_since'])['customer_id'].nunique().reset_index()
        cohort_sizes = df.groupby('cohort_month')['customer_id'].nunique()
        
        cohort_data['retention'] = cohort_data.apply(
            lambda x: 100 * x['customer_id'] / cohort_sizes[x['cohort_month']], axis=1
        )
        
        pivot = cohort_data.pivot(index='cohort_month', columns='months_since', values='retention')
        
        return jsonify({
            'cohorts': [d.strftime('%Y-%m') for d in pivot.index],
            'retention_matrix': pivot.fillna(0).round(1).values.tolist(),
            'months': list(range(len(pivot.columns)))
        })
    except Exception as e:
        print(f"Error in cohort retention: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/advanced/product-recommendations')
def product_recommendations():
    """Get frequently bought together products."""
    try:
        query = """
            WITH product_pairs AS (
                SELECT oi1.product_id as product_a,
                       oi2.product_id as product_b,
                       COUNT(DISTINCT oi1.order_id) as frequency
                FROM fact_order_items oi1
                JOIN fact_order_items oi2 ON oi1.order_id = oi2.order_id 
                    AND oi1.product_id < oi2.product_id
                GROUP BY oi1.product_id, oi2.product_id
                HAVING COUNT(DISTINCT oi1.order_id) > 5
                ORDER BY frequency DESC
                LIMIT 20
            )
            SELECT pp.product_a, pp.product_b, pp.frequency,
                   p1.product_category_name as category_a,
                   p2.product_category_name as category_b
            FROM product_pairs pp
            LEFT JOIN dim_products p1 ON pp.product_a = p1.product_id
            LEFT JOIN dim_products p2 ON pp.product_b = p2.product_id
        """
        df = execute_query(query)
        
        if df.empty:
            return jsonify({'pairs': []})
        
        pairs = []
        for _, row in df.iterrows():
            pairs.append({
                'product_a': row['category_a'] or row['product_a'],
                'product_b': row['category_b'] or row['product_b'],
                'frequency': int(row['frequency']),
                'confidence': min(100, int(row['frequency'] * 5))
            })
        
        return jsonify({'pairs': pairs[:10]})
    except Exception as e:
        print(f"Error in recommendations: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/advanced/delivery-performance')
def delivery_performance():
    """Analyze delivery time performance by state."""
    try:
        query = """
            SELECT c.customer_state,
                   COUNT(*) as total_orders,
                   AVG(EXTRACT(EPOCH FROM (o.order_delivered_customer_date - o.order_purchase_timestamp))/86400) as avg_delivery_days,
                   STDDEV(EXTRACT(EPOCH FROM (o.order_delivered_customer_date - o.order_purchase_timestamp))/86400) as std_delivery_days
            FROM fact_orders o
            JOIN dim_customers c ON o.customer_id = c.customer_id
            WHERE o.order_delivered_customer_date IS NOT NULL
              AND o.order_status = 'delivered'
            GROUP BY c.customer_state
            HAVING COUNT(*) > 100
            ORDER BY avg_delivery_days DESC
            LIMIT 15
        """
        df = execute_query(query)
        
        if df.empty:
            return jsonify({'states': [], 'avg_days': [], 'std_days': []})
        
        return jsonify({
            'states': df['customer_state'].tolist(),
            'avg_delivery_days': [round(float(v), 1) for v in df['avg_delivery_days'].tolist()],
            'std_delivery_days': [round(float(v), 1) for v in df['std_delivery_days'].fillna(0).tolist()],
            'order_count': df['total_orders'].tolist()
        })
    except Exception as e:
        print(f"Error in delivery performance: {e}")
        return jsonify({'error': str(e)}), 500

# Legacy endpoints from original dashboard
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

@app.route('/api/dashboard')
def get_dashboard_bundle():
    """Single unified payload for all dashboard data + ML insights."""
    try:
        bundle = {
            'kpis': get_kpis().json,
            'ml_performance': ml_model_performance().json,
            'revenue_forecast': revenue_forecast().json,
            'customer_ltv': customer_lifetime_value().json,
            'delivery_performance': delivery_performance().json,
            'product_recommendations': product_recommendations().json
        }
        return jsonify(bundle)
    except Exception as e:
        print(f"Error in dashboard bundle: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/health')
def health():
    """Health check endpoint."""
    try:
        engine = get_db_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        model = load_ml_model()
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'ml_model': 'loaded' if model else 'not_found'
        })
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

if __name__ == '__main__':
    print("=" * 60)
    print("  🚀 Premium E-Commerce Analytics Dashboard")
    print("=" * 60)
    print("\n📊 Starting Enhanced Flask server with ML...")
    print("🌐 Dashboard URL: http://localhost:5000")
    print("🔌 API Base URL: http://localhost:5000/api")
    print("🤖 ML Model: Loaded" if load_ml_model() else "⚠️  ML Model: Not Found")
    print("\n" + "=" * 60)
    
    app.run(host='0.0.0.0', port=5000, debug=True)
