import sys
import subprocess
import time
import urllib.request
import os


def start_flask_server(port=5001):
    """Start the flask dev server in a background process.

    Uses a short inline python command to import and run the app. Returns
    the subprocess.Popen instance.
    """
    cmd = [sys.executable, "-u", "-c",
           (
               "from dashboard.app import create_app;"
               "app=create_app();"
               f"app.run(host='127.0.0.1', port={port})"
           )]
    env = os.environ.copy()
    # ensure Flask doesn't output buffering issues on Windows
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return p


def wait_for_url(url, timeout=10.0, interval=0.25):
    """Polls a URL until it returns or timeout (seconds) elapses.

    Returns the response bytes on success, raises Exception on failure.
    """
    deadline = time.time() + timeout
    last_exc = None
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as r:
                return r.read()
        except Exception as e:
            last_exc = e
            time.sleep(interval)
    raise last_exc or RuntimeError("timeout waiting for %s" % url)


def test_smoke_dashboard():
    port = 5001
    p = start_flask_server(port=port)
    try:
        url = f"http://127.0.0.1:{port}/dashboard"
        body = wait_for_url(url, timeout=12.0)
        text = body.decode('utf-8', errors='replace')
        # Basic smoke assertions
        assert '<h1>ETL Dashboard' in text
        # client-side plot div present
        assert 'id="plotly-div"' in text
    finally:
        # ensure we terminate the server process
        try:
            p.terminate()
        except Exception:
            pass
        p.wait(timeout=5)
