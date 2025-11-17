from etl.transform import clean_rows


def test_clean_rows_basic():
    rows = [
        {'InvoiceNo': '1000', 'StockCode': 'A', 'Quantity': '2', 'UnitPrice': '3.5', 'InvoiceDate': '2020-01-01 10:00:00'},
        {'InvoiceNo': '', 'StockCode': 'B', 'Quantity': '1', 'UnitPrice': '5.0'},
    ]
    cleaned = clean_rows(rows)
    # first row kept, second dropped due to missing InvoiceNo
    assert len(cleaned) == 1
    r = cleaned[0]
    assert r['quantity'] == 2
    assert float(r['unit_price']) == 3.5
    assert float(r['total_amount']) == 7.0
