"""
Professional CSV-based Dashboard Backend
Reads Brazilian E-commerce CSV files and serves ML predictions
"""
from flask import Flask, jsonify, render_template, send_from_directory
from flask_cors import CORS
import pandas as pd
import numpy as np
import os
import joblib
import json
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # ETL folder
ROOT_DIR = os.path.dirname(BASE_DIR)  # Project root
DATA_DIR = os.path.join(BASE_DIR, 'data', 'processed')
BRAZILIAN_DIR = os.path.join(ROOT_DIR, 'brazilian dataset')
ML_MODEL_PATH = os.path.join(BASE_DIR, 'ml', 'models', 'order_total_model.pkl')
ML_METRICS_PATH = os.path.join(BASE_DIR, 'ml', 'reports', 'evaluation_summary.json')

# Load data on startup
print("\n" + "="*60)
print("  📊 CSV-Based E-Commerce Analytics Dashboard")
print("="*60)

# Load processed orders
orders_df = None
if os.path.exists(os.path.join(DATA_DIR, 'orders_processed.csv')):
    orders_df = pd.read_csv(os.path.join(DATA_DIR, 'orders_processed.csv'), parse_dates=['order_purchase_timestamp'])
    print(f"✅ Loaded {len(orders_df):,} processed orders")

# Load Brazilian dataset
customers_df = None
products_df = None
sellers_df = None
order_items_df = None
payments_df = None
reviews_df = None

if os.path.exists(os.path.join(BRAZILIAN_DIR, 'olist_customers_dataset.csv')):
    try:
        customers_df = pd.read_csv(os.path.join(BRAZILIAN_DIR, 'olist_customers_dataset.csv'))
        print(f"✅ Loaded {len(customers_df):,} customers")
    except Exception as e:
        print(f"⚠️ Error loading customers: {e}")

if os.path.exists(os.path.join(BRAZILIAN_DIR, 'olist_products_dataset.csv')):
    try:
        products_df = pd.read_csv(os.path.join(BRAZILIAN_DIR, 'olist_products_dataset.csv'))
        print(f"✅ Loaded {len(products_df):,} products")
    except Exception as e:
        print(f"⚠️ Error loading products: {e}")

if os.path.exists(os.path.join(BRAZILIAN_DIR, 'olist_sellers_dataset.csv')):
    try:
        sellers_df = pd.read_csv(os.path.join(BRAZILIAN_DIR, 'olist_sellers_dataset.csv'))
        print(f"✅ Loaded {len(sellers_df):,} sellers")
    except Exception as e:
        print(f"⚠️ Error loading sellers: {e}")

if os.path.exists(os.path.join(BRAZILIAN_DIR, 'olist_order_items_dataset.csv')):
    try:
        order_items_df = pd.read_csv(os.path.join(BRAZILIAN_DIR, 'olist_order_items_dataset.csv'))
        print(f"✅ Loaded {len(order_items_df):,} order items")
    except Exception as e:
        print(f"⚠️ Error loading order items: {e}")

if os.path.exists(os.path.join(BRAZILIAN_DIR, 'olist_order_payments_dataset.csv')):
    try:
        payments_df = pd.read_csv(os.path.join(BRAZILIAN_DIR, 'olist_order_payments_dataset.csv'))
        print(f"✅ Loaded {len(payments_df):,} payments")
    except Exception as e:
        print(f"⚠️ Error loading payments: {e}")

if os.path.exists(os.path.join(BRAZILIAN_DIR, 'olist_order_reviews_dataset.csv')):
    try:
        reviews_df = pd.read_csv(os.path.join(BRAZILIAN_DIR, 'olist_order_reviews_dataset.csv'))
        print(f"✅ Loaded {len(reviews_df):,} reviews")
    except Exception as e:
        print(f"⚠️ Error loading reviews: {e}")
else:
    print(f"⚠️ Brazilian dataset directory not found: {BRAZILIAN_DIR}")

# Load ML model
ml_model = None
ml_metrics = None
try:
    if os.path.exists(ML_MODEL_PATH):
        ml_model = joblib.load(ML_MODEL_PATH)
        print(f"✅ ML model loaded")
    if os.path.exists(ML_METRICS_PATH):
        with open(ML_METRICS_PATH, 'r') as f:
            ml_metrics = json.load(f)
        print(f"✅ ML metrics loaded")
except Exception as e:
    print(f"⚠️ ML loading error: {e}")

print("="*60 + "\n")

# ============================================
# ROUTES
# ============================================

@app.route('/')
def index():
    return render_template('professional_dashboard.html')

@app.route('/api/health')
def health():
    return jsonify({
        'status': 'healthy',
        'orders': len(orders_df) if orders_df is not None else 0,
        'customers': len(customers_df) if customers_df is not None else 0,
        'products': len(products_df) if products_df is not None else 0,
        'ml_model': 'loaded' if ml_model else 'not_found'
    })

@app.route('/api/overview')
def get_overview():
    """Main KPIs from CSV data"""
    try:
        data = {}
        
        if orders_df is not None:
            data['total_orders'] = int(len(orders_df))
            data['total_revenue'] = float(orders_df['total_amount'].sum())
            data['avg_order_value'] = float(orders_df['total_amount'].mean())
            data['unique_customers'] = int(orders_df['customer_id'].nunique())
        
        if customers_df is not None:
            data['total_customers'] = int(len(customers_df))
        
        if products_df is not None:
            data['total_products'] = int(len(products_df))
        
        if sellers_df is not None:
            data['total_sellers'] = int(len(sellers_df))
        
        if order_items_df is not None:
            data['total_items_sold'] = int(len(order_items_df))
        
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/sales-timeline')
def get_sales_timeline():
    """Daily sales trends"""
    try:
        if orders_df is None:
            return jsonify({'success': False, 'error': 'No data'}), 404
        
        df = orders_df.copy()
        df['date'] = pd.to_datetime(df['order_purchase_timestamp']).dt.date
        
        daily = df.groupby('date').agg({
            'order_id': 'count',
            'total_amount': 'sum'
        }).reset_index()
        
        daily.columns = ['date', 'orders', 'revenue']
        daily = daily.sort_values('date').tail(90)  # Last 90 days
        
        return jsonify({
            'success': True,
            'data': {
                'dates': daily['date'].astype(str).tolist(),
                'orders': daily['orders'].tolist(),
                'revenue': [round(float(x), 2) for x in daily['revenue'].tolist()]
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/top-products')
def get_top_products():
    """Top products by revenue"""
    try:
        if order_items_df is None or products_df is None:
            return jsonify({'success': False, 'error': 'No data'}), 404
        
        # Merge with products
        merged = order_items_df.merge(products_df, on='product_id', how='left')
        
        # Calculate revenue per product
        top = merged.groupby(['product_id', 'product_category_name']).agg({
            'price': 'sum',
            'order_id': 'count'
        }).reset_index()
        
        top.columns = ['product_id', 'category', 'revenue', 'count']
        top = top.sort_values('revenue', ascending=False).head(15)
        
        return jsonify({
            'success': True,
            'data': {
                'categories': [str(x) if pd.notna(x) else 'Unknown' for x in top['category'].tolist()],
                'revenue': [round(float(x), 2) for x in top['revenue'].tolist()],
                'count': top['count'].tolist()
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/customer-distribution')
def get_customer_distribution():
    """Customers by state"""
    try:
        if customers_df is None:
            return jsonify({'success': False, 'error': 'No data'}), 404
        
        dist = customers_df.groupby('customer_state').size().reset_index(name='count')
        dist = dist.sort_values('count', ascending=False).head(15)
        
        return jsonify({
            'success': True,
            'data': {
                'states': dist['customer_state'].tolist(),
                'counts': dist['count'].tolist()
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/payment-methods')
def get_payment_methods():
    """Payment type distribution"""
    try:
        if payments_df is None:
            return jsonify({'success': False, 'error': 'No data'}), 404
        
        methods = payments_df.groupby('payment_type').agg({
            'payment_value': 'sum',
            'order_id': 'count'
        }).reset_index()
        
        methods.columns = ['type', 'total_value', 'count']
        
        return jsonify({
            'success': True,
            'data': {
                'types': methods['type'].tolist(),
                'values': [round(float(x), 2) for x in methods['total_value'].tolist()],
                'counts': methods['count'].tolist()
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/order-status')
def get_order_status():
    """Order status breakdown"""
    try:
        if orders_df is None:
            return jsonify({'success': False, 'error': 'No data'}), 404
        
        status = orders_df.groupby('order_status').size().reset_index(name='count')
        status = status.sort_values('count', ascending=False)
        
        return jsonify({
            'success': True,
            'data': {
                'statuses': status['order_status'].tolist(),
                'counts': status['count'].tolist()
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/reviews-stats')
def get_reviews_stats():
    """Review scores distribution"""
    try:
        if reviews_df is None:
            return jsonify({'success': False, 'error': 'No data'}), 404
        
        scores = reviews_df.groupby('review_score').size().reset_index(name='count')
        scores = scores.sort_values('review_score')
        
        return jsonify({
            'success': True,
            'data': {
                'scores': scores['review_score'].tolist(),
                'counts': scores['count'].tolist()
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ml/metrics')
def get_ml_metrics():
    """ML model performance"""
    try:
        if ml_metrics is None:
            return jsonify({'success': False, 'error': 'No metrics'}), 404
        
        return jsonify({
            'success': True,
            'data': {
                'r2_score': ml_metrics.get('regression', {}).get('r2', 0),
                'mae': ml_metrics.get('regression', {}).get('mae', 0),
                'rmse': ml_metrics.get('regression', {}).get('rmse', 0),
                'roc_auc': ml_metrics.get('classification', {}).get('roc_auc', 0),
                'samples': ml_metrics.get('samples_total', 0)
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ml/predict')
def predict_order():
    """Predict order value using ML model"""
    try:
        if ml_model is None:
            return jsonify({'success': False, 'error': 'Model not loaded'}), 404
        
        # Sample prediction (can be parameterized)
        num_items = 2
        avg_price = 100.0
        total_price = 200.0
        freight = 15.0
        
        X = np.array([[num_items, avg_price, total_price, freight]])
        prediction = float(ml_model.predict(X)[0])
        
        return jsonify({
            'success': True,
            'data': {
                'predicted_value': round(prediction, 2),
                'features': {
                    'num_items': num_items,
                    'avg_item_price': avg_price,
                    'total_items_price': total_price,
                    'freight_value': freight
                }
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    print("🌐 Dashboard: http://localhost:5000")
    print("🔌 API: http://localhost:5000/api/")
    print("="*60 + "\n")
    app.run(host='0.0.0.0', port=5000, debug=True)
