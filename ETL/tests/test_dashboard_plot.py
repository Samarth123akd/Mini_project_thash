import json

from dashboard.app import create_app


def test_dashboard_plot_endpoints():
    app = create_app({'TESTING': True})
    client = app.test_client()

    # test the server-side plot page (returns HTML)
    r = client.get('/dashboard-plot')
    assert r.status_code == 200
    assert 'text/html' in r.content_type

    # test the data endpoint for client-side plots
    r2 = client.get('/dashboard-plot-data')
    assert r2.status_code == 200
    data = r2.get_json()
    assert isinstance(data, dict)
    assert 'top_products' in data