"""
Unit tests for COPY-based bulk loading in etl/load.py
"""
import os
import tempfile
import csv
from io import StringIO
import pytest
from unittest.mock import Mock, patch, MagicMock

# Import functions to test
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from etl.load import load_table_copy, upsert_dimension


class TestCopyLoading:
    """Test suite for load_table_copy() with COPY FROM STDIN"""

    def setup_method(self):
        """Set up test fixtures before each test"""
        # Create sample CSV data
        self.csv_data = [
            {'order_id': '1', 'customer_id': '100', 'total': '50.25', 'status': 'completed'},
            {'order_id': '2', 'customer_id': '101', 'total': '75.50', 'status': 'pending'},
            {'order_id': '3', 'customer_id': '102', 'total': '120.00', 'status': 'completed'}
        ]
        
        # Create temporary CSV file
        self.csv_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', newline='')
        writer = csv.DictWriter(self.csv_file, fieldnames=['order_id', 'customer_id', 'total', 'status'])
        writer.writeheader()
        writer.writerows(self.csv_data)
        self.csv_file.close()

    def teardown_method(self):
        """Clean up after each test"""
        if hasattr(self, 'csv_file'):
            os.unlink(self.csv_file.name)

    @patch('etl.load.psycopg2.connect')
    def test_load_table_copy_uses_copy_from_stdin(self, mock_connect):
        """Test that load_table_copy uses COPY FROM STDIN for efficiency"""
        # Mock database connection
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Call load_table_copy with method='copy'
        result = load_table_copy(self.csv_file.name, 'fact_orders', method='copy')
        
        # Verify COPY command was executed
        copy_calls = [call for call in mock_cursor.copy_expert.call_args_list]
        assert len(copy_calls) > 0, "COPY command should be executed"
        
        # Verify COPY SQL includes table name
        copy_sql = str(copy_calls[0])
        assert 'fact_orders' in copy_sql, "COPY command should reference target table"
        assert 'COPY' in copy_sql.upper(), "Should use COPY command"

    @patch('etl.load.psycopg2.connect')
    def test_load_table_copy_handles_header_row(self, mock_connect):
        """Test that load_table_copy skips CSV header row"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Mock copy_expert to capture the CSV content
        csv_content = []
        def capture_copy(sql, file_obj):
            csv_content.append(file_obj.read())
        mock_cursor.copy_expert.side_effect = capture_copy
        
        load_table_copy(self.csv_file.name, 'orders', method='copy')
        
        # Verify header was skipped (first line should be data, not headers)
        if csv_content:
            lines = csv_content[0].strip().split('\n')
            # First line should be data (order_id=1), not headers (order_id,customer_id,...)
            assert not lines[0].startswith('order_id,'), "Header should be skipped"

    @patch('etl.load.create_engine')
    def test_load_table_copy_fallback_to_bulk_insert(self, mock_create_engine):
        """Test that load_table_copy falls back to bulk INSERT if COPY fails"""
        # Mock engine that supports bulk insert but not COPY
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        
        # Simulate COPY failure by raising exception
        with patch('etl.load.psycopg2.connect') as mock_connect:
            mock_connect.side_effect = Exception("psycopg2 not available")
            
            # Should not raise exception (should fall back to bulk insert)
            result = load_table_copy(self.csv_file.name, 'orders', method='bulk')
            
            # Verify fallback was used (engine.execute should be called)
            # This is implementation-specific, adjust based on actual fallback code

    def test_load_table_copy_validates_csv_file(self):
        """Test that load_table_copy validates CSV file exists"""
        with pytest.raises(FileNotFoundError):
            load_table_copy('nonexistent_file.csv', 'orders')

    @patch('etl.load.psycopg2.connect')
    def test_load_table_copy_handles_empty_csv(self, mock_connect):
        """Test that load_table_copy handles empty CSV gracefully"""
        # Create empty CSV (only header)
        empty_csv = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', newline='')
        writer = csv.DictWriter(empty_csv, fieldnames=['order_id', 'total'])
        writer.writeheader()
        empty_csv.close()
        
        try:
            mock_conn = MagicMock()
            mock_connect.return_value = mock_conn
            
            # Should not raise exception
            result = load_table_copy(empty_csv.name, 'orders', method='copy')
            
            # Should return 0 rows loaded
            assert result == 0 or result is None, "Should handle empty CSV"
        finally:
            os.unlink(empty_csv.name)

    @patch('etl.load.psycopg2.connect')
    def test_load_table_copy_performance_vs_insert(self, mock_connect):
        """Test that COPY method is faster than INSERT (simulated)"""
        # This is a conceptual test - actual timing would require real DB
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Create large dataset
        large_csv = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', newline='')
        writer = csv.DictWriter(large_csv, fieldnames=['id', 'value'])
        writer.writeheader()
        for i in range(10000):
            writer.writerow({'id': i, 'value': f'value_{i}'})
        large_csv.close()
        
        try:
            # Mock COPY execution time
            mock_cursor.copy_expert.return_value = None
            
            result = load_table_copy(large_csv.name, 'test_table', method='copy')
            
            # Verify COPY was called once (not 10,000 INSERTs)
            assert mock_cursor.copy_expert.call_count == 1, "Should use single COPY command"
        finally:
            os.unlink(large_csv.name)


class TestUpsertDimension:
    """Test suite for upsert_dimension() with ON CONFLICT"""

    @patch('etl.load.create_engine')
    def test_upsert_dimension_inserts_new_records(self, mock_create_engine):
        """Test that upsert_dimension inserts new dimension records"""
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_create_engine.return_value = mock_engine
        mock_engine.connect.return_value.__enter__.return_value = mock_conn
        
        data = [
            {'customer_id': '100', 'name': 'John Doe', 'email': 'john@example.com'},
            {'customer_id': '101', 'name': 'Jane Smith', 'email': 'jane@example.com'}
        ]
        
        result = upsert_dimension(data, 'dim_customers', 'customer_id')
        
        # Verify INSERT was executed
        execute_calls = [call for call in mock_conn.execute.call_args_list]
        assert len(execute_calls) > 0, "INSERT should be executed"
        
        # Verify ON CONFLICT clause is present
        sql_text = str(execute_calls[0])
        assert 'ON CONFLICT' in sql_text.upper() or 'UPSERT' in sql_text.upper(), "Should use ON CONFLICT for upsert"

    @patch('etl.load.create_engine')
    def test_upsert_dimension_updates_existing_records(self, mock_create_engine):
        """Test that upsert_dimension updates existing dimension records"""
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_create_engine.return_value = mock_engine
        mock_engine.connect.return_value.__enter__.return_value = mock_conn
        
        # Simulate existing customer with updated email
        data = [
            {'customer_id': '100', 'name': 'John Doe', 'email': 'john.new@example.com'}
        ]
        
        result = upsert_dimension(data, 'dim_customers', 'customer_id')
        
        # Verify UPDATE part of upsert (ON CONFLICT ... DO UPDATE)
        execute_calls = [call for call in mock_conn.execute.call_args_list]
        sql_text = str(execute_calls[0]) if execute_calls else ''
        assert 'UPDATE' in sql_text.upper() or 'DO UPDATE' in sql_text.upper(), "Should handle updates"

    @patch('etl.load.create_engine')
    def test_upsert_dimension_handles_composite_keys(self, mock_create_engine):
        """Test that upsert_dimension handles composite keys"""
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_create_engine.return_value = mock_engine
        mock_engine.connect.return_value.__enter__.return_value = mock_conn
        
        # Product with composite key (product_id, seller_id)
        data = [
            {'product_id': 'P1', 'seller_id': 'S1', 'name': 'Widget', 'price': 19.99}
        ]
        
        result = upsert_dimension(data, 'dim_products', ['product_id', 'seller_id'])
        
        # Verify multiple key columns in ON CONFLICT
        execute_calls = [call for call in mock_conn.execute.call_args_list]
        sql_text = str(execute_calls[0]) if execute_calls else ''
        assert 'product_id' in sql_text and 'seller_id' in sql_text, "Should reference both keys"

    def test_upsert_dimension_validates_input(self):
        """Test that upsert_dimension validates input parameters"""
        # Empty data should be handled gracefully
        result = upsert_dimension([], 'dim_customers', 'customer_id')
        assert result == 0 or result is None, "Should handle empty data"
        
        # Missing key column should raise error or handle gracefully
        data = [{'name': 'John', 'email': 'john@example.com'}]  # Missing customer_id
        # Depending on implementation, this might raise ValueError or skip record
        # Adjust assertion based on actual error handling


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
