"""WSGI entrypoint for production servers (Gunicorn, Render).

This exposes a top-level ``app`` object so servers can import it with
``wsgi:app``. It serves the full dashboard + API from backend_api.
"""
from dashboard.backend_api import app


if __name__ == '__main__':
    # local debug run
    app.run(host='0.0.0.0', port=5000, debug=True)
