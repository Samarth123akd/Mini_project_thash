# 📊 Professional E-Commerce Analytics Dashboard

## Overview
A modern, professional dashboard built with **HTML/CSS/JavaScript + Flask** that directly reads your Brazilian e-commerce CSV datasets and integrates your trained ML models. Features a stylish gradient UI with glassmorphism effects and real-time Chart.js visualizations.

---

## ✨ Features

### 📈 **Data Visualizations**
- **Sales Timeline**: Dual-axis chart showing revenue and order volume over time
- **Top Products**: Horizontal bar chart of best-selling product categories
- **Customer Distribution**: Geographic distribution of customers by state
- **Payment Methods**: Doughnut chart breaking down payment types
- **Order Status**: Pie chart showing order lifecycle stages
- **Review Ratings**: Bar chart displaying customer satisfaction scores

### 💎 **KPI Cards**
- Total Revenue (R$)
- Total Orders
- Unique Customers
- Total Products

### 🤖 **ML Integration**
- Model Performance Metrics (R² Score, MAE, ROC AUC)
- Training Dataset Information
- Prediction API Endpoint

### 🎨 **Modern UI**
- **Gradient Backgrounds**: Purple to blue atmospheric theme
- **Glassmorphism Cards**: Frosted glass effect with backdrop blur
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Smooth Animations**: Fade-in effects and hover interactions
- **Professional Typography**: Inter + JetBrains Mono fonts

---

## 🚀 Quick Start

### **Option 1: PowerShell Script (Recommended)**
```powershell
cd C:\Users\samar\Desktop\prjct_thash\ETL\dashboard
.\start_professional_dashboard.ps1
```

### **Option 2: Manual Start**
```powershell
C:/Users/samar/Desktop/prjct_thash/.venv/Scripts/python.exe C:\Users\samar\Desktop\prjct_thash\ETL\dashboard\csv_dashboard.py
```

### **Access Dashboard**
Open your browser and navigate to:
```
http://localhost:5000
```

---

## 📁 Architecture

### **Backend: `csv_dashboard.py`**
- **Framework**: Flask 3.1.2 with CORS enabled
- **Data Source**: Direct CSV file reading (bypasses database)
- **CSV Files Used**:
  - `data/processed/orders_processed.csv` (99,441 orders)
  - `brazilian dataset/olist_customers_dataset.csv`
  - `brazilian dataset/olist_products_dataset.csv`
  - `brazilian dataset/olist_sellers_dataset.csv`
  - `brazilian dataset/olist_order_items_dataset.csv`
  - `brazilian dataset/olist_order_payments_dataset.csv`
  - `brazilian dataset/olist_order_reviews_dataset.csv`
- **ML Model**: `ml/models/order_total_model.pkl`
- **ML Metrics**: `ml/reports/evaluation_summary.json`

### **Frontend: `templates/professional_dashboard.html`**
- **Styling**: Custom CSS with CSS variables and animations
- **Charts**: Chart.js 4.4.0
- **Layout**: CSS Grid + Flexbox responsive design
- **Effects**: Glassmorphism, gradients, animations

### **JavaScript: `static/js/professional_dashboard.js`**
- Fetches data from Flask API endpoints
- Renders Chart.js visualizations
- Updates KPIs and ML metrics
- Handles loading states and errors

---

## 🔌 API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /` | Main dashboard HTML page |
| `GET /api/health` | Server health check |
| `GET /api/overview` | KPIs (revenue, orders, customers, products) |
| `GET /api/sales-timeline` | Time series data for sales chart |
| `GET /api/top-products` | Best-selling product categories |
| `GET /api/customer-distribution` | Customer counts by state |
| `GET /api/payment-methods` | Payment type breakdown |
| `GET /api/order-status` | Order status distribution |
| `GET /api/reviews-stats` | Review score distribution |
| `GET /api/ml/metrics` | ML model performance metrics |
| `POST /api/ml/predict` | Make predictions with trained model |

### **Example API Response**
```json
// GET /api/overview
{
  "success": true,
  "data": {
    "total_orders": 99441,
    "total_revenue": 13591643.70,
    "avg_order_value": 136.71,
    "unique_customers": 96096,
    "total_products": 32951,
    "total_sellers": 3095
  }
}
```

---

## 📊 Data Flow

```
Brazilian CSV Files (9 files)
        ↓
   csv_dashboard.py (Flask)
   - Load CSVs with pandas
   - Aggregate data
   - Serve JSON via API
        ↓
   professional_dashboard.js
   - Fetch API data
   - Parse JSON
   - Render Chart.js
        ↓
   professional_dashboard.html
   - Display visualizations
   - Show KPIs
   - Interactive UI
```

---

## 🎨 UI Components

### **Color Palette**
- **Primary Gradient**: `#667eea` → `#764ba2` (Purple-Blue)
- **Success**: `#43e97b` → `#38f9d7` (Green)
- **Info**: `#4facfe` → `#00f2fe` (Cyan)
- **Warning**: `#fa709a` → `#fee140` (Pink-Yellow)
- **Background**: `#0f1419` (Dark Blue-Black)
- **Cards**: `rgba(255, 255, 255, 0.05)` with blur

### **Typography**
- **Headings**: Inter (Google Fonts)
- **Monospace**: JetBrains Mono (Code/Numbers)
- **Icons**: Unicode emojis + Font Awesome

### **Animations**
- **Fade In**: 0.6s ease-out on page load
- **Card Hover**: Transform scale + glow effect
- **Loading**: Spinning gradient overlay

---

## 🔧 Technical Details

### **Dependencies**
```
Flask==3.1.2
Flask-Cors==6.0.1
pandas==2.3.3
numpy==2.2.3
scikit-learn==1.7.2
joblib==1.5.1
```

### **Chart.js Configuration**
- **Version**: 4.4.0 (CDN)
- **Chart Types**: Line, Bar, Pie, Doughnut
- **Responsive**: Maintains aspect ratio on resize
- **Tooltips**: Custom formatted with currency/numbers
- **Colors**: Gradient fills matching UI theme

### **Performance**
- CSV data loaded once on Flask startup
- In-memory pandas DataFrames for fast queries
- Client-side Chart.js rendering
- Lazy loading for charts (render on data arrival)

---

## 🛠️ Customization

### **Change Color Theme**
Edit CSS variables in `professional_dashboard.html`:
```css
:root {
    --gradient-1: linear-gradient(135deg, #YOUR_COLOR_1, #YOUR_COLOR_2);
    --gradient-2: linear-gradient(135deg, #YOUR_COLOR_3, #YOUR_COLOR_4);
    /* ... */
}
```

### **Add New Chart**
1. Add API endpoint in `csv_dashboard.py`:
```python
@app.route('/api/your-endpoint')
def your_endpoint():
    # Query dataframes
    return jsonify({'success': True, 'data': {...}})
```

2. Add canvas in HTML:
```html
<canvas id="yourChart"></canvas>
```

3. Render in `professional_dashboard.js`:
```javascript
async function renderYourChart(data) {
    const ctx = document.getElementById('yourChart');
    charts.yourChart = new Chart(ctx, { /* config */ });
}
```

### **Modify KPIs**
Edit `get_overview()` function in `csv_dashboard.py` to add/change metrics.

---

## 📸 Screenshots

### Main Dashboard View
- **Top Section**: 4 KPI cards with gradient icons
- **Middle Section**: 4 ML performance metrics
- **Charts Grid**: 6 interactive visualizations in 2x3 grid

### Responsive Design
- **Desktop**: Full 2-column layout
- **Tablet**: Stacked cards with 2-column charts
- **Mobile**: Single column, full-width elements

---

## 🐛 Troubleshooting

### **Dashboard won't start**
```powershell
# Check if port 5000 is available
netstat -ano | findstr :5000

# If occupied, kill the process or change port in csv_dashboard.py:
# app.run(debug=True, host='0.0.0.0', port=5001)
```

### **Charts not rendering**
1. Open browser DevTools (F12)
2. Check Console for JavaScript errors
3. Verify API endpoints return data:
   ```
   http://localhost:5000/api/overview
   http://localhost:5000/api/sales-timeline
   ```

### **CSV files not loading**
- Verify file paths in terminal output on startup
- Check that files exist in:
  - `data/processed/orders_processed.csv`
  - `brazilian dataset/*.csv`

### **ML model errors**
- Ensure `ml/models/order_total_model.pkl` exists
- Ensure `ml/reports/evaluation_summary.json` exists
- Model and metrics are optional; dashboard works without them

---

## 🎯 Why This Dashboard?

### **CSV-First Approach**
- ✅ No database setup required
- ✅ Direct access to your uploaded datasets
- ✅ Fast iteration and development
- ✅ Easy deployment (just copy files)

### **Modern UI/UX**
- ✅ Professional gradient design
- ✅ Glassmorphism effects (trendy!)
- ✅ Smooth animations
- ✅ Responsive for all devices

### **ML Integration**
- ✅ Uses your trained `order_total_model.pkl`
- ✅ Displays model performance metrics
- ✅ Prediction API ready for extensions

### **Performance**
- ✅ Loads 99K+ orders instantly
- ✅ In-memory data processing with pandas
- ✅ Client-side rendering with Chart.js
- ✅ No database query latency

---

## 📦 File Structure

```
ETL/dashboard/
├── csv_dashboard.py                      # Flask backend (CSV reader)
├── start_professional_dashboard.ps1      # Quick start script
├── PROFESSIONAL_DASHBOARD_README.md      # This file
├── templates/
│   └── professional_dashboard.html       # HTML with embedded CSS
└── static/
    └── js/
        └── professional_dashboard.js     # Chart.js rendering logic
```

---

## 🚀 Next Steps

### **Enhancements You Can Add**
1. **Export Functionality**: Download charts as PNG/PDF
2. **Date Range Filters**: Add date pickers to filter data
3. **Real-time Updates**: WebSocket for live data refresh
4. **User Authentication**: Add login/signup pages
5. **More ML Features**: 
   - Customer segmentation visualization
   - Revenue forecasting chart
   - Product recommendations table
6. **Backend Optimization**:
   - Cache aggregated results
   - Add pagination for large datasets
   - Implement rate limiting

### **Production Deployment**
```powershell
# Install production server
pip install gunicorn  # (Linux/Mac) or waitress (Windows)

# Run with Waitress (Windows)
pip install waitress
waitress-serve --host=0.0.0.0 --port=5000 csv_dashboard:app
```

---

## 📄 License & Credits

- **Data**: Brazilian E-Commerce Public Dataset by Olist
- **Charts**: Chart.js (MIT License)
- **Framework**: Flask (BSD License)
- **Fonts**: Inter (OFL), JetBrains Mono (OFL)

---

## 🎉 Enjoy Your Dashboard!

Your professional dashboard is now ready with:
- ✅ 99,441 orders from CSV files
- ✅ 6 interactive Chart.js visualizations
- ✅ ML model performance metrics
- ✅ Modern gradient + glassmorphism UI
- ✅ Responsive design for all devices

**Access it at:** [http://localhost:5000](http://localhost:5000)

---

**Built with ❤️ using your Brazilian E-Commerce datasets**
