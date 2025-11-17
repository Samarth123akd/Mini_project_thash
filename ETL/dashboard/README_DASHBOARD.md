# E-Commerce Analytics Dashboard

A modern, responsive web dashboard built with HTML, CSS, JavaScript, and Flask for visualizing Brazilian e-commerce data.

## 🎨 Features

- **Real-time KPIs**: Total Revenue, Orders, Customers, Average Order Value
- **Interactive Charts**:
  - Sales trends over time (dual-axis line chart)
  - Top products by revenue
  - Customer segmentation
  - Orders by status
  - Revenue by state
  - Revenue by category
  - Review score distribution
- **Recent Orders Table**: View latest transactions
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Clean UI**: Modern, professional interface with smooth animations

## 📁 Project Structure

```
dashboard/
├── backend_api.py              # Flask REST API server
├── requirements_dashboard.txt   # Python dependencies
├── static/
│   ├── css/
│   │   └── style.css           # Dashboard styles
│   └── js/
│       └── dashboard.js        # Dashboard logic & charts
└── templates/
    └── index.html              # Main dashboard page
```

## 🚀 Quick Start

### 1. Install Dependencies

```powershell
cd dashboard
pip install -r requirements_dashboard.txt
```

### 2. Set Database Connection

```powershell
$env:DATABASE_URL = "postgresql://etl_user:etl_password_123@localhost:5432/ETL_DB"
```

### 3. Start the Server

```powershell
python backend_api.py
```

### 4. Open Dashboard

Open your browser and navigate to:
```
http://localhost:5000
```

## 🔌 API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /` | Main dashboard page |
| `GET /api/kpis` | Key performance indicators |
| `GET /api/sales-trends?days=30` | Sales trends over time |
| `GET /api/top-products?limit=10` | Top selling products |
| `GET /api/customer-segments` | Customer distribution by spend |
| `GET /api/orders-by-status` | Order status breakdown |
| `GET /api/revenue-by-state?limit=10` | Revenue by state |
| `GET /api/recent-orders?limit=20` | Latest orders |
| `GET /api/revenue-by-category` | Revenue by product category |
| `GET /api/reviews-stats` | Review score distribution |
| `GET /api/health` | Health check |

## 📊 Dashboard Sections

### 1. KPI Cards
- Total Revenue (R$)
- Total Orders
- Unique Customers
- Average Order Value

### 2. Sales Trends Chart
Dual-axis line chart showing:
- Revenue over time (left axis)
- Number of orders (right axis)

### 3. Top Products
Horizontal bar chart showing top 10 products by revenue.

### 4. Customer Segments
Doughnut chart categorizing customers by total spend:
- Low Value (< R$100)
- Medium Value (R$100-500)
- High Value (R$500-1000)
- VIP (> R$1000)

### 5. Order Status Distribution
Pie chart showing current orders by status.

### 6. Revenue by State
Bar chart showing top 10 states by revenue.

### 7. Recent Orders Table
Interactive table displaying the latest 20 orders with:
- Order ID
- Customer ID
- Total Amount
- Status (with colored badges)
- Date

## 🎨 Technology Stack

### Frontend
- **HTML5**: Semantic markup
- **CSS3**: Modern styling with CSS Grid & Flexbox
- **JavaScript (ES6+)**: Async/await, Fetch API
- **Chart.js 4.4**: Interactive charts and visualizations

### Backend
- **Flask 3.0**: Lightweight web framework
- **Flask-CORS**: Cross-origin resource sharing
- **SQLAlchemy**: Database ORM
- **Pandas**: Data manipulation
- **PostgreSQL**: Database (via psycopg2)

## 🔧 Configuration

### Environment Variables

```powershell
# Database connection
$env:DATABASE_URL = "postgresql://user:password@host:port/database"

# Optional: Change server port (default: 5000)
$env:FLASK_PORT = "8080"
```

### Date Filter Options

The dashboard includes a date filter dropdown:
- Last 7 Days
- Last 30 Days (default)
- Last 90 Days
- Last Year
- All Time

## 🎯 Usage Tips

1. **Refresh Data**: Click the "🔄 Refresh" button to reload all dashboard data
2. **Date Filtering**: Use the dropdown to change the time range
3. **Chart Interactions**: 
   - Hover over charts for detailed tooltips
   - Click legend items to show/hide datasets
4. **Responsive**: Resize browser to see mobile-friendly layout

### Unified Data Fetch + Toggles

- The frontend uses a single endpoint `GET /api/dashboard?days=<7|30|90|365|all>&mix=<true|false>` to load all datasets at once, reducing network overhead and keeping charts in sync.
- Use the "Mix recent orders" toggle to randomize the recent orders list without changing the selected time window.
- Use the moon/sun button to toggle a basic dark mode implemented via CSS variables.

## 📝 Customization

### Adding New Charts

1. Add HTML canvas element in `templates/index.html`:
```html
<canvas id="myNewChart"></canvas>
```

2. Create API endpoint in `backend_api.py`:
```python
@app.route('/api/my-data')
def get_my_data():
    # Query and return data
    return jsonify(data)
```

3. Add chart initialization in `static/js/dashboard.js`:
```javascript
async function loadMyChart() {
    const response = await fetch(`${API_BASE_URL}/my-data`);
    const data = await response.json();
    // Create chart with Chart.js
}
```

### Styling

Edit `static/css/style.css` to customize:
- Colors (CSS variables in `:root`)
- Layout (Grid/Flexbox)
- Typography
- Animations

## 🐛 Troubleshooting

### Dashboard shows "Failed to load data"
- Ensure PostgreSQL is running
- Check `DATABASE_URL` is correct
- Verify tables exist: `python scripts/view_data.py`
- Check backend logs for errors

### Charts not displaying
- Open browser console (F12) for JavaScript errors
- Ensure Chart.js CDN is accessible
- Check network tab for failed API calls

### Backend connection errors
- Verify Flask server is running: `python backend_api.py`
- Check firewall settings
- Ensure port 5000 is not in use

## 📦 Production Deployment

### Using Gunicorn (Linux/Mac)

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 backend_api:app
```

### Using Waitress (Windows)

```powershell
pip install waitress
waitress-serve --listen=0.0.0.0:5000 backend_api:app
```

### Environment Variables for Production

```powershell
$env:FLASK_ENV = "production"
$env:DATABASE_URL = "postgresql://user:pass@prod-host:5432/prod_db"
```

## 📄 License

This dashboard is part of the ETL project for Brazilian e-commerce data analysis.

## 🤝 Contributing

To add new features:
1. Create a new API endpoint in `backend_api.py`
2. Add corresponding frontend function in `dashboard.js`
3. Update the HTML template with new UI elements
4. Test thoroughly before deploying

## 📞 Support

For issues or questions:
- Check the main project README
- Review SQL schema in `sql/schema.sql`
- Verify data loaded: `python scripts/view_data.py`
