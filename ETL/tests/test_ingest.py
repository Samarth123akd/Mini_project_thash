import os
from etl.ingest import read_csv_from_path


def test_read_csv_missing(tmp_path):
    p = tmp_path / 'not_exists.csv'
    try:
        read_csv_from_path(str(p))
        assert False, 'should have raised FileNotFoundError'
    except FileNotFoundError:
        assert True


def test_read_csv_simple(tmp_path):
    p = tmp_path / 'sample.csv'
    p.write_text('col1,col2\n1,2\n3,4\n')
    rows = read_csv_from_path(str(p))
    assert isinstance(rows, list)
    assert len(rows) == 2
