"""A minimal dashboard app.

This file provides a very small Flask app that reads the processed CSV (if
available) and returns JSON summaries. It's intentionally dependency-light so
it can run where Flask is installed. For a production UI, swap to Streamlit or
Dash and add interactive charts.
"""
from flask import Flask, jsonify
import os
import csv
from .components import top_products_from_staging

# Try to use SQLAlchemy when DATABASE_URL is present. Fall back to CSV.
# Use importlib to avoid static analyzers complaining about unresolved imports.
try:
    import importlib
    _sqlalchemy = importlib.import_module('sqlalchemy')
    create_engine = getattr(_sqlalchemy, 'create_engine', None)
    # try to get `text` from sqlalchemy or sqlalchemy.sql if available
    text = getattr(_sqlalchemy, 'text', None)
    if text is None:
        try:
            _sqlalchemy_sql = importlib.import_module('sqlalchemy.sql')
            text = getattr(_sqlalchemy_sql, 'text', None)
        except Exception:
            text = None
except Exception:
    create_engine = None
    text = None


def create_app(test_config=None):
    app = Flask(__name__)

    @app.get('/')
    def index():
        return jsonify({'service': 'ecommerce-etl-dashboard', 'status': 'ok'})

    @app.get('/summary')
    def summary():
        # Prefer DATABASE_URL + SQLAlchemy when available
        db_url = os.environ.get('DATABASE_URL')
        if db_url and create_engine is not None:
            try:
                eng = create_engine(db_url)
                with eng.connect() as conn:
                    # count rows and sum total_amount (if column exists)
                    res_count = conn.execute(text("SELECT COUNT(*) FROM orders;"))
                    count = int(res_count.scalar() or 0)
                    try:
                        res_sum = conn.execute(text("SELECT SUM(CAST(total_amount AS numeric)) FROM orders;"))
                        total = float(res_sum.scalar() or 0.0)
                    except Exception:
                        total = 0.0
                return jsonify({'rows': count, 'total_amount_sum': total})
            except Exception:
                # fall back to CSV if DB query fails
                pass

        processed = os.path.join('data', 'processed', 'orders_processed.csv')
        if not os.path.exists(processed):
            return jsonify({'error': 'no processed data found', 'path': processed}), 404
        # compute a small summary without external libs
        totals = 0.0
        count = 0
        with open(processed, newline='', encoding='utf-8') as fh:
            reader = csv.DictReader(fh)
            for r in reader:
                try:
                    totals += float(r.get('total_amount') or 0)
                except Exception:
                    pass
                count += 1
        return jsonify({'rows': count, 'total_amount_sum': totals})

    @app.get('/dashboard')
    def dashboard_page():
        """Simple HTML page showing summary and top products.

        This is intentionally minimal and does not require JS so it can be
        served directly by Render/Gunicorn.
        """
        # reuse existing logic
        summary_json = summary()
        top_json = top_products()
        # summary() and top_products() return flask Responses; extract data
        try:
            sdata = summary_json.get_json()
        except Exception:
            sdata = {'rows': 0, 'total_amount_sum': 0}
        try:
            tdata = top_json.get_json()
        except Exception:
            tdata = {'top_products': []}

        rows = sdata.get('rows', 0)
        total = sdata.get('total_amount_sum', 0.0)
        products = tdata.get('top_products', [])

        # Build simple HTML with a client-side Plotly embed that fetches
        # `/dashboard-plot-data` and renders the chart in-browser. This gives a
        # better UX while still falling back to a simple HTML table when JS is
        # disabled or Plotly isn't available client-side.
        html = ['<html><head><title>ETL Dashboard</title>']
        # include Plotly.js from CDN (client-side). It's safe if the client
        # doesn't load it (table fallback will remain).
        html.append('<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>')
        html.append('</head><body>')
        html.append(f'<h1>ETL Dashboard</h1>')
        html.append(f'<p>Processed rows: <strong>{rows}</strong></p>')
        html.append(f'<p>Total amount (sum): <strong>{total}</strong></p>')
        html.append('<h2>Top products</h2>')
        html.append('<table border="1" cellpadding="4"><tr><th>Rank</th><th>Product</th><th>Quantity</th></tr>')
        for i, p in enumerate(products, start=1):
            name = p.get('product_name') or p.get('product') or p.get('product_id')
            qty = p.get('quantity') or p.get('qty') or 0
            html.append(f'<tr><td>{i}</td><td>{name}</td><td>{qty}</td></tr>')
        html.append('</table>')
        # Div where client-side Plotly will be rendered
        html.append('<h2>Interactive chart</h2>')
        html.append('<div id="plotly-div" style="width:100%;height:500px;">')
        html.append('<p>Loading interactive chart...</p>')
        html.append('</div>')

        # Client-side script: fetch data and render Plotly bar chart. If the
        # fetch or Plotly fails, the static table above remains visible.
        html.append('<script>')
        html.append("fetch('/dashboard-plot-data').then(r=>r.json()).then(d=>{\n"
                    "  try{\n"
                    "    const names = d.top_products.map(x=>x.product_name||x.product||x.product_id);\n"
                    "    const qtys = d.top_products.map(x=>Number(x.quantity||0));\n"
                    "    const data=[{x:names,y:qtys,type:'bar'}];\n"
                    "    Plotly.newPlot('plotly-div', data, {margin:{t:30},title:'Top Products'});\n"
                    "  }catch(e){ console.warn('Plotly chart error',e); }\n"
                    "}).catch(e=>{ console.warn('Fetch plot data failed', e); });")
        html.append('</script>')
        html.append('</body></html>')
        return '\n'.join(html)

    @app.get('/dashboard-plot-data')
    def dashboard_plot_data():
        """Return JSON data for client-side Plotly charts.

        This endpoint returns the same top-products structure as `/top-products`
        but is provided here for clarity and to separate chart-data from
        server-rendered HTML.
        """
        resp = top_products()
        try:
            if hasattr(resp, 'get_json'):
                data = resp.get_json()
            else:
                data = resp
        except Exception:
            data = {'top_products': []}
        return jsonify(data)

    @app.get('/dashboard-plot')
    def dashboard_plot():
        """Interactive Plotly bar chart of top products.

        If Plotly is not installed or data source not available, fall back to
        the HTML table dashboard.
        """
        # get top products JSON (reuses existing logic)
        top_json = top_products()
        # top_json is a Response object or dict depending on calling context
        products = []
        try:
            if hasattr(top_json, 'get_json'):
                tdata = top_json.get_json()
            else:
                tdata = top_json
            products = tdata.get('top_products', []) if isinstance(tdata, dict) else []
        except Exception:
            products = []

        # Prepare data for plotting
        names = [p.get('product_name') or p.get('product') or p.get('product_id') for p in products]
        qtys = [int(p.get('quantity') or 0) for p in products]

        try:
            import importlib
            # dynamically import plotly.express to avoid static resolver errors
            px = importlib.import_module('plotly.express')
        except Exception:
            # plotly not installed; fall back to HTML dashboard
            return dashboard_page()

        if not names:
            return dashboard_page()

        fig = px.bar(x=names, y=qtys, labels={'x': 'Product', 'y': 'Quantity'}, title='Top Products')
        # return full HTML (includes CDN plotly js)
        return fig.to_html(full_html=True, include_plotlyjs='cdn')

    @app.get('/top-products')
    def top_products():
        # Prefer DB-backed top-products when possible
        db_url = os.environ.get('DATABASE_URL')
        if db_url and create_engine is not None:
            try:
                eng = create_engine(db_url)
                with eng.connect() as conn:
                    # try join order_items -> products if available
                    q = text("""
                        SELECT oi.product_id, p.product_name, COUNT(*) as qty
                        FROM order_items oi
                        LEFT JOIN products p ON p.product_id = oi.product_id
                        GROUP BY oi.product_id, p.product_name
                        ORDER BY qty DESC
                        LIMIT 20
                    """)
                    rows = conn.execute(q).fetchall()
                    items = []
                    for r in rows:
                        pid = r[0]
                        name = r[1] or pid
                        qty = int(r[2] or 0)
                        items.append({'product_id': pid, 'product_name': name, 'quantity': qty})
                    return jsonify({'top_products': items})
            except Exception:
                pass

        staging = os.path.join('data', 'staging')
        items = top_products_from_staging(staging, top_n=20)
        return jsonify({'top_products': items})

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=8050, debug=True)
