"""
Unit tests for save_raw archiving functionality in etl/ingest.py
"""
import os
import gzip
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import pytest

# Import the function to test
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from etl.ingest import save_raw


class TestSaveRaw:
    """Test suite for save_raw() function"""

    def setup_method(self):
        """Set up test fixtures before each test"""
        # Create temporary directory for test data
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)

    def teardown_method(self):
        """Clean up after each test"""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)

    def test_save_raw_creates_directory_structure(self):
        """Test that save_raw creates proper directory structure"""
        source_type = 'api'
        source_name = 'shopify_orders'
        data = [{'order_id': '123', 'total': 100.50}]
        
        filepath = save_raw(source_type, source_name, data)
        
        # Check that file was created
        assert os.path.exists(filepath), "File should be created"
        
        # Check directory structure: data/staging/raw/{source_type}/{YYYY-MM-DD}/
        today = datetime.now().strftime('%Y-%m-%d')
        expected_dir = Path('data/staging/raw') / source_type / today
        assert expected_dir.exists(), f"Directory {expected_dir} should exist"

    def test_save_raw_json_compression(self):
        """Test that JSON data is properly compressed"""
        source_type = 'api'
        source_name = 'stripe_payments'
        data = [
            {'payment_id': 'ch_123', 'amount': 5000, 'currency': 'usd'},
            {'payment_id': 'ch_456', 'amount': 7500, 'currency': 'usd'}
        ]
        
        filepath = save_raw(source_type, source_name, data, format='json')
        
        # Verify file extension
        assert filepath.endswith('.json.gz'), "File should have .json.gz extension"
        
        # Read and decompress file
        with gzip.open(filepath, 'rt') as f:
            loaded_data = json.load(f)
        
        # Verify data integrity
        assert loaded_data == data, "Data should be preserved after compression"
        assert len(loaded_data) == 2, "Should have 2 payment records"
        assert loaded_data[0]['payment_id'] == 'ch_123'

    def test_save_raw_csv_compression(self):
        """Test that CSV data is properly compressed"""
        source_type = 'database'
        source_name = 'postgres_customers'
        csv_data = "customer_id,name,email\n1,John Doe,john@example.com\n2,Jane Smith,jane@example.com"
        
        filepath = save_raw(source_type, source_name, csv_data, format='csv')
        
        # Verify file extension
        assert filepath.endswith('.csv.gz'), "File should have .csv.gz extension"
        
        # Read and decompress file
        with gzip.open(filepath, 'rt') as f:
            loaded_csv = f.read()
        
        # Verify CSV content
        assert loaded_csv == csv_data, "CSV data should be preserved"
        assert 'customer_id,name,email' in loaded_csv
        assert 'John Doe' in loaded_csv

    def test_save_raw_filename_includes_timestamp(self):
        """Test that filename includes timestamp for uniqueness"""
        source_type = 'csv'
        source_name = 'orders'
        data = "order_id,total\n1,100\n2,200"
        
        filepath1 = save_raw(source_type, source_name, data)
        filepath2 = save_raw(source_type, source_name, data)
        
        # Files should be different (different timestamps)
        assert filepath1 != filepath2, "Each save should create unique file"
        
        # Both files should exist
        assert os.path.exists(filepath1)
        assert os.path.exists(filepath2)

    def test_save_raw_handles_empty_data(self):
        """Test that save_raw handles empty data gracefully"""
        source_type = 'api'
        source_name = 'empty_test'
        data = []
        
        filepath = save_raw(source_type, source_name, data, format='json')
        
        # File should still be created
        assert os.path.exists(filepath)
        
        # Should contain empty array
        with gzip.open(filepath, 'rt') as f:
            loaded_data = json.load(f)
        assert loaded_data == [], "Should contain empty array"

    def test_save_raw_compression_reduces_size(self):
        """Test that gzip compression actually reduces file size"""
        source_type = 'test'
        source_name = 'large_data'
        
        # Create large repetitive data (compresses well)
        data = [{'id': i, 'value': 'test' * 100} for i in range(100)]
        
        filepath = save_raw(source_type, source_name, data, format='json')
        
        # Compare compressed vs uncompressed size
        compressed_size = os.path.getsize(filepath)
        
        # Write uncompressed version for comparison
        uncompressed_path = filepath.replace('.gz', '.uncompressed')
        with open(uncompressed_path, 'w') as f:
            json.dump(data, f)
        uncompressed_size = os.path.getsize(uncompressed_path)
        
        # Compressed should be smaller
        assert compressed_size < uncompressed_size, "Compressed file should be smaller"
        compression_ratio = compressed_size / uncompressed_size
        assert compression_ratio < 0.5, f"Compression ratio {compression_ratio:.2f} should be < 0.5"

    def test_save_raw_preserves_special_characters(self):
        """Test that save_raw preserves special characters in data"""
        source_type = 'api'
        source_name = 'special_chars'
        data = [
            {'name': 'José García', 'city': 'São Paulo'},
            {'name': '北京', 'emoji': '🚀'}
        ]
        
        filepath = save_raw(source_type, source_name, data, format='json')
        
        with gzip.open(filepath, 'rt', encoding='utf-8') as f:
            loaded_data = json.load(f)
        
        assert loaded_data[0]['name'] == 'José García'
        assert loaded_data[0]['city'] == 'São Paulo'
        assert loaded_data[1]['name'] == '北京'
        assert loaded_data[1]['emoji'] == '🚀'

    def test_save_raw_metadata_in_filename(self):
        """Test that filename includes source name for identification"""
        source_type = 'database'
        source_name = 'mysql_products'
        data = "product_id,name\n1,Widget\n2,Gadget"
        
        filepath = save_raw(source_type, source_name, data)
        
        # Filename should contain source name
        filename = os.path.basename(filepath)
        assert source_name in filename, f"Filename {filename} should contain {source_name}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
