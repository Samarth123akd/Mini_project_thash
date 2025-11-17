# Deploying ETL to Render

This repository includes a `render.yaml` that you can import into Render to create:
- a Web Service running the Flask dashboard
- a managed Postgres database
- a scheduled Cron Job that runs `scripts/run_etl.py` daily

Quick manual steps

1. Create a Render account and connect your Git repository.
2. In Render create a Managed Database (Postgres). Note the DATABASE_URL.
3. Create a new Web Service pointing to this repository (or import `render.yaml`):
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn wsgi:app -b 0.0.0.0:$PORT --workers 2`
4. Add an Environment Variable `DATABASE_URL` in the Web Service settings with the
   connection string from step 2.
5. Add a Cron Job (Render Scheduling) that runs `python scripts/run_etl.py` on a
   schedule (see `render.yaml` example). Configure the Cron Job service to
   inherit the `DATABASE_URL` env var as well.

Plotly and interactive charts
-----------------------------

The dashboard includes an interactive Plotly page at `/dashboard-plot`. Render will
serve the HTML produced by Plotly when you use Gunicorn. To ensure the Plotly
pages work correctly:

- Use the recommended Start Command below so static assets and CDN links are
   reachable by the client:

   `gunicorn wsgi:app -b 0.0.0.0:$PORT --workers 2`

- Ensure `plotly` is listed in `requirements.txt` (it is). Render will install
   it during build. The dashboard uses Plotly's CDN by default, so no extra
   static hosting is required.

- If you prefer to render plots client-side, the app contains a small client-side
   embed that fetches `/dashboard-plot-data` and draws the chart with Plotly.js.
   (This is helpful for very large datasets or if you want incremental updates.)


Notes
- `scripts/run_etl.py` will run the transform and (if `DATABASE_URL` is set)
  load processed data into Postgres.
- The dashboard will prefer Postgres when `DATABASE_URL` is configured. If not
  found it will fall back to reading `data/processed/orders_processed.csv`.

If you'd like, I can generate a fully filled `render.yaml` with placeholders
for your Render service names and push it into the repo (it already exists as
an example). Let me know if you want that filled in with specific names.
