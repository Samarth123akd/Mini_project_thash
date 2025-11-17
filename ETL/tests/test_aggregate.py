import os
import runpy
from pathlib import Path


def test_aggregate_orders(tmp_path):
    repo = Path('.').resolve()
    staging = repo / 'data' / 'staging'
    processed = repo / 'data' / 'processed'
    staging.mkdir(parents=True, exist_ok=True)
    processed.mkdir(parents=True, exist_ok=True)

    # create minimal orders.csv
    orders_csv = staging / 'orders.csv'
    orders_csv.write_text('order_id,customer_id,order_purchase_timestamp\n1,cust1,2021-01-01\n2,cust2,2021-01-02\n')

    # create minimal order_items csv
    items_csv = staging / 'order_items.csv'
    items_csv.write_text('order_id,order_item_id,product_id,price,quantity\n1,1,prodA,10.0,2\n1,2,prodB,5.0,1\n2,1,prodC,7.5,1\n')

    # run aggregation
    runpy.run_path(str(repo / 'scripts' / 'aggregate_orders.py'), run_name='__main__')

    out = processed / 'orders_processed.csv'
    assert out.exists()

    # read and check totals
    txt = out.read_text()
    assert '1' in txt  # order id present
    assert '25.00' in txt or '25.0' in txt  # total for order 1 = 10*2 + 5*1 = 25
