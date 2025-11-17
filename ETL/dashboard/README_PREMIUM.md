# 🚀 Premium Analytics Dashboard - ML-Powered

A stunning, professional analytics dashboard built with Machine Learning integration, advanced visualizations, and modern design principles for Brazilian E-Commerce data analysis.

## ✨ Features

### 🤖 ML-Powered Insights
- **Order Value Prediction**: Real-time ML model for predicting order totals
- **Model Performance Metrics**: Live R², MAE, ROC-AUC scores
- **Revenue Forecasting**: 30-day revenue predictions based on historical trends
- **Customer Lifetime Value**: Advanced CLV segmentation and analysis

### 📊 Advanced Analytics
- **Revenue Forecasting**: Time series forecasting with confidence intervals
- **Customer Lifetime Value**: Segmented CLV analysis (Low, Medium, High, VIP)
- **Cohort Retention**: Monthly cohort retention analysis
- **Delivery Performance**: State-by-state delivery time analytics
- **Product Recommendations**: Frequently bought together analysis
- **Predictive Analytics**: ML-driven business insights

### 🎨 Premium Design
- **Glass Morphism UI**: Modern frosted glass effect throughout
- **Animated Gradients**: Beautiful animated background effects
- **Responsive Grid**: Fully responsive layout for all devices
- **Dark Theme**: Sophisticated dark color palette
- **Smooth Animations**: Micro-interactions and transitions
- **Professional Typography**: Inter font family with optimized weights

### 📈 Visualizations
- Revenue forecast with historical + predicted data
- Customer lifetime value by segment
- Delivery performance heatmap
- Product recommendation network
- ML model performance dashboard
- Interactive Chart.js charts with hover effects

## 🏗️ Architecture

```
dashboard/
├── ml_backend.py                   # Enhanced Flask API with ML endpoints
├── templates/
│   └── premium_dashboard.html      # Premium HTML template
├── static/
│   ├── css/
│   │   └── premium_style.css       # Modern design system
│   └── js/
│       └── premium_dashboard.js    # Advanced chart logic
└── README_PREMIUM.md               # This file
```

## 🚀 Quick Start

### 1. Start the Premium Server

```powershell
cd C:\Users\samar\Desktop\prjct_thash\ETL\dashboard
$env:DATABASE_URL = "postgresql://etl_user:etl_password_123@localhost:5432/ETL_DB"
python ml_backend.py
```

### 2. Open Dashboard

Navigate to:
```
http://localhost:5000
```

## 🔌 API Endpoints

### Core Metrics
- `GET /api/kpis?days=30` - Key performance indicators
- `GET /api/dashboard?days=30` - Unified bundle

### ML Endpoints
- `GET /api/ml/model-performance` - ML model metrics (R², MAE, ROC-AUC)
- `GET /api/ml/predict-order-value?num_items=3&avg_price=100` - Predict order value

### Advanced Analytics
- `GET /api/advanced/revenue-forecast` - 30-day revenue forecast
- `GET /api/advanced/customer-lifetime-value` - CLV segmentation
- `GET /api/advanced/cohort-retention` - Retention analysis
- `GET /api/advanced/delivery-performance` - Delivery metrics by state
- `GET /api/advanced/product-recommendations` - Frequently bought together

### Health Check
- `GET /api/health` - System status + ML model availability

## 📊 Dashboard Sections

### 1. Hero KPIs
Four beautifully designed KPI cards with gradient backgrounds:
- **Total Revenue**: Aggregate revenue with trend indicator
- **Total Orders**: Order count with processing status
- **Active Customers**: Unique customer count
- **Avg Order Value**: Per-transaction average

### 2. ML Model Performance
Real-time machine learning model metrics:
- **R² Score**: Model accuracy (0-1 scale) with progress bar
- **MAE**: Mean Absolute Error in R$
- **ROC AUC**: Classification performance (0-1 scale)
- **Training Samples**: Dataset size used for training

### 3. Revenue Forecast
Interactive time series chart showing:
- 90-day historical revenue (solid line)
- 30-day forecast (dashed line)
- Confidence intervals
- Trend analysis

### 4. Customer Lifetime Value
Segmented bar chart displaying:
- Low CLV (< R$ 500/year)
- Medium CLV (R$ 500-1,500/year)
- High CLV (R$ 1,500-5,000/year)
- VIP CLV (> R$ 5,000/year)

### 5. Delivery Performance
State-by-state horizontal bar chart:
- Average delivery days
- Standard deviation
- Order volume per state

### 6. Product Recommendations
Smart product pairing cards:
- Product A → Product B relationships
- Purchase frequency
- Confidence percentage
- Visual relationship indicators

### 7. Advanced Insights
Three insight cards showing:
- **Predictive Analytics**: Model accuracy
- **Processing Speed**: API response times
- **Prediction Confidence**: Current model confidence level

## 🎨 Design System

### Color Palette
```css
Primary Gradient: #667eea → #764ba2 (Purple)
Success Gradient: #11998e → #38ef7d (Green)
Danger Gradient:  #ee0979 → #ff6a00 (Red)
Info Gradient:    #4facfe → #00f2fe (Blue)
Warning Gradient: #f2994a → #f2c94c (Yellow)
```

### Typography
- **Font Family**: Inter (300-800 weights)
- **Headings**: 700-800 weight
- **Body**: 400-500 weight
- **Labels**: 600 weight uppercase

### Effects
- **Glass Morphism**: `backdrop-filter: blur(20px)`
- **Shadows**: Multi-level elevation system
- **Animations**: Smooth 0.3s cubic-bezier transitions
- **Hover States**: Transform + shadow combinations

## 🔧 Customization

### Add New Visualizations

1. **Backend** (ml_backend.py):
```python
@app.route('/api/your-endpoint')
def your_endpoint():
    query = "SELECT ... FROM ..."
    df = execute_query(query)
    return jsonify(df.to_dict('records'))
```

2. **Frontend** (premium_dashboard.js):
```javascript
async function renderYourChart(data) {
    const ctx = document.getElementById('yourChart');
    charts.your = new Chart(ctx, {
        type: 'bar',
        data: {...},
        options: {...}
    });
}
```

3. **HTML** (premium_dashboard.html):
```html
<div class="chart-card-modern glass">
    <canvas id="yourChart"></canvas>
</div>
```

### Modify Color Scheme

Edit `premium_style.css`:
```css
:root {
    --primary-gradient: linear-gradient(...);
    --bg-primary: #0f0f23;
    /* Add your colors */
}
```

## 🤖 ML Model Integration

The dashboard integrates with your trained RandomForest model:

### Model Location
```
ml/models/order_total_model.pkl
```

### Model Features
- `num_items`: Number of items in order
- `avg_item_price`: Average price per item
- `total_items_price`: Sum of item prices
- `freight_value`: Shipping cost

### Making Predictions
```python
# Via API
GET /api/ml/predict-order-value?num_items=3&avg_price=100&total_price=300&freight=20

# Response
{
    "predicted_value": 325.50,
    "confidence": "high",
    "features": {...}
}
```

## 📊 Data Requirements

### Required Tables
- `fact_orders`: Order transactions
- `fact_order_items`: Line items
- `dim_customers`: Customer information
- `dim_products`: Product catalog
- `fact_payments`: Payment data
- `fact_reviews`: Customer reviews

### Minimum Data
- 1,000+ orders for meaningful analytics
- 90+ days of history for forecasting
- Multiple states for delivery analysis

## 🚀 Performance Optimization

### Frontend
- Chart.js lazy loading
- Parallel API calls with Promise.all
- Debounced filter updates
- Optimized CSS animations

### Backend
- Database connection pooling
- Query result caching (planned)
- Async data loading
- Indexed database queries

## 🐛 Troubleshooting

### Dashboard Not Loading
1. Check Flask server is running: `python ml_backend.py`
2. Verify DATABASE_URL is set correctly
3. Ensure PostgreSQL is running
4. Check browser console (F12) for errors

### ML Model Not Found
```bash
# Train or copy model
cd ml
python evaluate_models.py
```

### Charts Not Rendering
1. Check Chart.js CDN is accessible
2. Verify API endpoints return data
3. Inspect network tab for failed requests
4. Check console for JavaScript errors

### Slow Performance
1. Reduce date range (7 days vs 365 days)
2. Check database indexes
3. Monitor query execution times
4. Enable query caching

## 📈 Future Enhancements

- [ ] Real-time WebSocket updates
- [ ] Export to PDF/Excel
- [ ] Custom date range picker
- [ ] Drill-down capabilities
- [ ] A/B testing dashboard
- [ ] Anomaly detection alerts
- [ ] Multi-language support
- [ ] User authentication
- [ ] Saved dashboard views
- [ ] Mobile app version

## 🎯 Best Practices

### Data Refresh
- **Auto-refresh**: Disabled by default (prevents overload)
- **Manual refresh**: Use refresh button
- **Filter changes**: Trigger automatic reload

### Performance
- Use date filters to limit data volume
- Monitor API response times
- Check database query performance
- Optimize Chart.js render times

### Accessibility
- High contrast ratios
- Semantic HTML structure
- Keyboard navigation support
- Screen reader compatible

## 📞 Support

### Common Questions

**Q: How accurate are the forecasts?**  
A: Forecasts use moving averages with 7-day windows. Accuracy depends on data consistency and seasonality.

**Q: Can I add custom metrics?**  
A: Yes! Add new endpoints in `ml_backend.py` and corresponding charts in `premium_dashboard.js`.

**Q: How do I change the theme?**  
A: Edit CSS variables in `:root` section of `premium_style.css`.

**Q: Is the ML model retrained automatically?**  
A: No. Retrain manually using `ml/evaluate_models.py` with fresh data.

## 📄 License

Part of the Brazilian E-Commerce ETL project.

## 🙏 Credits

- **Design**: Modern glass morphism UI principles
- **Charts**: Chart.js 4.4
- **Fonts**: Google Fonts (Inter)
- **ML Model**: Scikit-learn RandomForest
- **Framework**: Flask + PostgreSQL

---

**Built with ❤️ using ML, modern web technologies, and your Brazilian E-Commerce dataset**
