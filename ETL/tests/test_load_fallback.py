import os
from etl import load
from pathlib import Path


def test_load_processed_from_env(tmp_path):
    processed = Path('data') / 'processed'
    processed.mkdir(parents=True, exist_ok=True)
    pfile = processed / 'orders_processed.csv'
    pfile.write_text('order_id,total_amount\n1,10.0\n')

    # ensure DATABASE_URL unset
    if 'DATABASE_URL' in os.environ:
        del os.environ['DATABASE_URL']

    # should not raise and should return None (no DB configured)
    load.load_processed_from_env('orders', str(pfile))
    # file should still exist
    assert pfile.exists()
