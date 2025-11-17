from dashboard.app import create_app


def test_index():
    app = create_app()
    client = app.test_client()
    rv = client.get('/')
    assert rv.status_code == 200
    data = rv.get_json()
    assert data.get('service') == 'ecommerce-etl-dashboard'
