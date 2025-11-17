"""Streamlit Dashboard for E-Commerce ETL Pipeline.

Displays sales trends, top products, and customer lifetime value analytics.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os

# Page configuration
st.set_page_config(
    page_title="E-Commerce Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Database connection
@st.cache_resource
def get_database_connection():
    """Get database connection from environment or use CSV fallback."""
    db_url = os.environ.get('DATABASE_URL')
    
    if db_url:
        try:
            from sqlalchemy import create_engine
            engine = create_engine(db_url)
            return engine, 'database'
        except Exception as e:
            st.warning(f"Database connection failed: {e}. Using CSV fallback.")
            return None, 'csv'
    else:
        return None, 'csv'


@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_orders_data(_engine, source_type):
    """Load orders data from database or CSV."""
    if source_type == 'database' and _engine:
        try:
            query = """
                SELECT 
                    order_id,
                    customer_id,
                    order_purchase_timestamp,
                    order_total_cents / 100.0 AS total_amount,
                    currency,
                    order_item_count,
                    order_status
                FROM fact_orders
                WHERE order_purchase_timestamp IS NOT NULL
                ORDER BY order_purchase_timestamp DESC
                LIMIT 100000
            """
            df = pd.read_sql(query, _engine)
            df['order_purchase_timestamp'] = pd.to_datetime(df['order_purchase_timestamp'])
            return df
        except Exception as e:
            st.error(f"Database query failed: {e}")
            return None
    else:
        # Fallback to CSV
        csv_path = 'data/processed/orders_processed.csv'
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            # Convert date columns
            date_cols = [col for col in df.columns if 'date' in col.lower() or 'timestamp' in col.lower()]
            for col in date_cols:
                df[col] = pd.to_datetime(df[col], errors='coerce')
            return df
        else:
            st.error(f"Data file not found: {csv_path}")
            return None


@st.cache_data(ttl=300)
def load_customer_metrics(_engine, source_type):
    """Load customer metrics."""
    if source_type == 'database' and _engine:
        try:
            query = """
                SELECT 
                    customer_id,
                    COUNT(DISTINCT order_id) AS order_count,
                    SUM(order_total_cents) / 100.0 AS total_spent,
                    AVG(order_total_cents) / 100.0 AS avg_order_value,
                    MAX(order_purchase_timestamp) AS last_order_date
                FROM fact_orders
                GROUP BY customer_id
            """
            return pd.read_sql(query, _engine)
        except:
            return None
    return None


def calculate_metrics(df):
    """Calculate key business metrics."""
    if df is None or df.empty:
        return None
    
    metrics = {
        'total_orders': len(df),
        'total_revenue': df['total_amount'].sum() if 'total_amount' in df.columns else 0,
        'avg_order_value': df['total_amount'].mean() if 'total_amount' in df.columns else 0,
        'unique_customers': df['customer_id'].nunique() if 'customer_id' in df.columns else 0
    }
    return metrics


def plot_sales_trends(df):
    """Plot sales trends over time."""
    if df is None or df.empty:
        return None
    
    # Prepare data
    date_col = 'order_purchase_timestamp' if 'order_purchase_timestamp' in df.columns else df.columns[0]
    df['date'] = pd.to_datetime(df[date_col]).dt.date
    
    daily_sales = df.groupby('date').agg({
        'total_amount': 'sum',
        'order_id': 'count'
    }).reset_index()
    daily_sales.columns = ['date', 'revenue', 'orders']
    
    # Create figure with secondary y-axis
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=daily_sales['date'],
        y=daily_sales['revenue'],
        name='Revenue',
        line=dict(color='#1f77b4', width=2)
    ))
    
    fig.add_trace(go.Bar(
        x=daily_sales['date'],
        y=daily_sales['orders'],
        name='Orders',
        yaxis='y2',
        opacity=0.3,
        marker=dict(color='#ff7f0e')
    ))
    
    fig.update_layout(
        title='Sales Trends Over Time',
        xaxis=dict(title='Date'),
        yaxis=dict(title='Revenue (R$)', side='left'),
        yaxis2=dict(title='Number of Orders', side='right', overlaying='y'),
        hovermode='x unified',
        height=400
    )
    
    return fig


def plot_top_products(df):
    """Plot top products by revenue."""
    if df is None or df.empty or 'product_id' not in df.columns:
        return None
    
    top_products = df.groupby('product_id')['total_amount'].sum().sort_values(ascending=False).head(10)
    
    fig = px.bar(
        x=top_products.values,
        y=top_products.index,
        orientation='h',
        labels={'x': 'Revenue (R$)', 'y': 'Product ID'},
        title='Top 10 Products by Revenue'
    )
    fig.update_layout(height=400)
    
    return fig


def plot_customer_segments(customer_df):
    """Plot customer segments by value."""
    if customer_df is None or customer_df.empty:
        return None
    
    # Create segments
    customer_df['segment'] = pd.cut(
        customer_df['total_spent'],
        bins=[0, 100, 500, 1000, float('inf')],
        labels=['Low Value', 'Medium Value', 'High Value', 'VIP']
    )
    
    segment_counts = customer_df['segment'].value_counts()
    
    fig = px.pie(
        values=segment_counts.values,
        names=segment_counts.index,
        title='Customer Segmentation by Total Spend'
    )
    fig.update_layout(height=400)
    
    return fig


# Main app
def main():
    st.title("📊 E-Commerce Analytics Dashboard")
    st.markdown("---")
    
    # Sidebar
    st.sidebar.title("Dashboard Controls")
    st.sidebar.markdown("### Data Source")
    
    # Get database connection
    engine, source_type = get_database_connection()
    st.sidebar.info(f"Source: **{source_type.upper()}**")
    
    # Refresh button
    if st.sidebar.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()
    
    # Load data
    with st.spinner("Loading data..."):
        df = load_orders_data(engine, source_type)
        customer_df = load_customer_metrics(engine, source_type)
    
    if df is None or df.empty:
        st.error("No data available. Please run the ETL pipeline first.")
        st.info("Run: `python scripts/run_etl.py`")
        return
    
    # Calculate metrics
    metrics = calculate_metrics(df)
    
    # Display KPIs
    st.markdown("### 📈 Key Performance Indicators")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Orders",
            f"{metrics['total_orders']:,}",
            delta=None
        )
    
    with col2:
        st.metric(
            "Total Revenue",
            f"R$ {metrics['total_revenue']:,.2f}",
            delta=None
        )
    
    with col3:
        st.metric(
            "Avg Order Value",
            f"R$ {metrics['avg_order_value']:.2f}",
            delta=None
        )
    
    with col4:
        st.metric(
            "Unique Customers",
            f"{metrics['unique_customers']:,}",
            delta=None
        )
    
    st.markdown("---")
    
    # Sales trends
    st.markdown("### 📊 Sales Trends")
    fig_trends = plot_sales_trends(df)
    if fig_trends:
        st.plotly_chart(fig_trends, use_container_width=True)
    
    # Two column layout
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🏆 Top Products")
        fig_products = plot_top_products(df)
        if fig_products:
            st.plotly_chart(fig_products, use_container_width=True)
        else:
            st.info("Product data not available")
    
    with col2:
        st.markdown("### 👥 Customer Segments")
        fig_segments = plot_customer_segments(customer_df)
        if fig_segments:
            st.plotly_chart(fig_segments, use_container_width=True)
        else:
            st.info("Customer data not available")
    
    # Data quality section
    st.markdown("---")
    st.markdown("### 🔍 Data Quality")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        null_pct = (df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100
        st.metric("Null Values %", f"{null_pct:.2f}%")
    
    with col2:
        duplicate_pct = (df.duplicated().sum() / len(df)) * 100
        st.metric("Duplicate Records %", f"{duplicate_pct:.2f}%")
    
    with col3:
        completeness = ((1 - null_pct / 100) * 100)
        st.metric("Data Completeness", f"{completeness:.1f}%")
    
    # Raw data viewer
    with st.expander("📋 View Raw Data"):
        st.dataframe(df.head(100), use_container_width=True)
        st.caption(f"Showing first 100 rows of {len(df)} total records")
    
    # Footer
    st.markdown("---")
    st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
