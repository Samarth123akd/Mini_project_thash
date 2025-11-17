"""
Unit tests for Airflow validation task in dags/etl_pipeline.py
"""
import os
import tempfile
import csv
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
import pytest

# Import validation function
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from dags.etl_pipeline import _validate


class TestValidationTask:
    """Test suite for Airflow _validate() task"""

    def setup_method(self):
        """Set up test fixtures before each test"""
        # Create temporary processed file with quality data
        self.processed_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', newline='')
        writer = csv.DictWriter(self.processed_file, fieldnames=['order_id', 'customer_id', 'total', 'status'])
        writer.writeheader()
        for i in range(100):
            writer.writerow({
                'order_id': i,
                'customer_id': i % 20,  # 20 unique customers
                'total': 50.0 + i,
                'status': 'completed'
            })
        self.processed_file.close()

    def teardown_method(self):
        """Clean up after each test"""
        if hasattr(self, 'processed_file'):
            os.unlink(self.processed_file.name)

    @patch('dags.etl_pipeline.analyze_csv_quality')
    def test_validate_checks_quality_score(self, mock_analyze):
        """Test that _validate checks quality score threshold"""
        # Mock high quality score
        mock_analyze.return_value = (85, {'completeness': 90, 'validity': 80})
        
        # Create mock context
        ti = Mock()
        ti.xcom_pull.return_value = self.processed_file.name
        
        # Should pass validation (score >= 80%)
        result = _validate(ti=ti)
        assert result is True or result == 'passed', "High quality score should pass"

    @patch('dags.etl_pipeline.analyze_csv_quality')
    def test_validate_fails_low_quality_score(self, mock_analyze):
        """Test that _validate fails when quality score below threshold"""
        # Mock low quality score
        mock_analyze.return_value = (65, {'completeness': 70, 'validity': 60})
        
        ti = Mock()
        ti.xcom_pull.return_value = self.processed_file.name
        
        # Should fail validation (score < 80%)
        with pytest.raises(Exception) as exc_info:
            _validate(ti=ti)
        assert 'quality' in str(exc_info.value).lower(), "Should mention quality in error"

    @patch('dags.etl_pipeline.analyze_csv_quality')
    def test_validate_checks_row_count(self, mock_analyze):
        """Test that _validate ensures row count > 0"""
        mock_analyze.return_value = (85, {'row_count': 100})
        
        ti = Mock()
        ti.xcom_pull.return_value = self.processed_file.name
        
        result = _validate(ti=ti)
        assert result is True or result == 'passed', "Non-empty file should pass"
        
        # Now test with empty file
        empty_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', newline='')
        empty_writer = csv.DictWriter(empty_file, fieldnames=['order_id', 'total'])
        empty_writer.writeheader()
        empty_file.close()
        
        try:
            mock_analyze.return_value = (85, {'row_count': 0})
            ti.xcom_pull.return_value = empty_file.name
            
            with pytest.raises(Exception) as exc_info:
                _validate(ti=ti)
            assert 'empty' in str(exc_info.value).lower() or 'rows' in str(exc_info.value).lower()
        finally:
            os.unlink(empty_file.name)

    @patch('dags.etl_pipeline.analyze_csv_quality')
    def test_validate_checks_file_exists(self, mock_analyze):
        """Test that _validate verifies processed file exists"""
        mock_analyze.return_value = (85, {})
        
        ti = Mock()
        ti.xcom_pull.return_value = 'nonexistent_file.csv'
        
        # Should raise FileNotFoundError or similar
        with pytest.raises(Exception):
            _validate(ti=ti)

    @patch('dags.etl_pipeline.analyze_csv_quality')
    def test_validate_checks_null_percentage(self, mock_analyze):
        """Test that _validate enforces null percentage threshold"""
        # Mock high null percentage (25% > 20% threshold)
        mock_analyze.return_value = (85, {
            'completeness': 75,  # 25% nulls
            'null_percentage': 25
        })
        
        ti = Mock()
        ti.xcom_pull.return_value = self.processed_file.name
        
        with pytest.raises(Exception) as exc_info:
            _validate(ti=ti)
        assert 'null' in str(exc_info.value).lower(), "Should mention nulls in error"

    @patch('dags.etl_pipeline.analyze_csv_quality')
    def test_validate_checks_duplicate_percentage(self, mock_analyze):
        """Test that _validate enforces duplicate percentage threshold"""
        # Mock high duplicate percentage (10% > 5% threshold)
        mock_analyze.return_value = (85, {
            'uniqueness': 90,  # 10% duplicates
            'duplicate_percentage': 10
        })
        
        ti = Mock()
        ti.xcom_pull.return_value = self.processed_file.name
        
        with pytest.raises(Exception) as exc_info:
            _validate(ti=ti)
        assert 'duplicate' in str(exc_info.value).lower(), "Should mention duplicates in error"

    @patch('dags.etl_pipeline.analyze_csv_quality')
    @patch('dags.etl_pipeline.create_engine')
    def test_validate_checks_database_integrity(self, mock_engine, mock_analyze):
        """Test that _validate checks database row count matches file"""
        mock_analyze.return_value = (85, {'row_count': 100})
        
        # Mock database connection
        mock_conn = MagicMock()
        mock_result = Mock()
        mock_result.scalar.return_value = 100  # Same row count
        mock_conn.execute.return_value = mock_result
        mock_engine.return_value.connect.return_value.__enter__.return_value = mock_conn
        
        ti = Mock()
        ti.xcom_pull.return_value = self.processed_file.name
        
        # Set DATABASE_URL environment variable
        with patch.dict(os.environ, {'DATABASE_URL': 'postgresql://localhost/test'}):
            result = _validate(ti=ti)
            assert result is True or result == 'passed', "Matching row counts should pass"

    @patch('dags.etl_pipeline.analyze_csv_quality')
    @patch('dags.etl_pipeline.create_engine')
    def test_validate_fails_database_count_mismatch(self, mock_engine, mock_analyze):
        """Test that _validate fails when DB row count != file row count"""
        mock_analyze.return_value = (85, {'row_count': 100})
        
        # Mock database with different row count
        mock_conn = MagicMock()
        mock_result = Mock()
        mock_result.scalar.return_value = 50  # Mismatch: 50 != 100
        mock_conn.execute.return_value = mock_result
        mock_engine.return_value.connect.return_value.__enter__.return_value = mock_conn
        
        ti = Mock()
        ti.xcom_pull.return_value = self.processed_file.name
        
        with patch.dict(os.environ, {'DATABASE_URL': 'postgresql://localhost/test'}):
            with pytest.raises(Exception) as exc_info:
                _validate(ti=ti)
            assert 'mismatch' in str(exc_info.value).lower() or 'count' in str(exc_info.value).lower()

    @patch('dags.etl_pipeline.analyze_csv_quality')
    def test_validate_skips_database_check_without_url(self, mock_analyze):
        """Test that _validate skips database checks if DATABASE_URL not set"""
        mock_analyze.return_value = (85, {'row_count': 100})
        
        ti = Mock()
        ti.xcom_pull.return_value = self.processed_file.name
        
        # Ensure DATABASE_URL is not set
        with patch.dict(os.environ, {}, clear=True):
            # Should pass without database checks
            result = _validate(ti=ti)
            assert result is True or result == 'passed', "Should skip DB checks without DATABASE_URL"

    @patch('dags.etl_pipeline.analyze_csv_quality')
    def test_validate_logs_metrics(self, mock_analyze):
        """Test that _validate logs validation metrics"""
        mock_analyze.return_value = (85, {
            'row_count': 100,
            'completeness': 90,
            'validity': 85,
            'uniqueness': 95
        })
        
        ti = Mock()
        ti.xcom_pull.return_value = self.processed_file.name
        
        with patch('dags.etl_pipeline.logging') as mock_logging:
            _validate(ti=ti)
            
            # Verify logging was called with metrics
            log_calls = [str(call) for call in mock_logging.info.call_args_list]
            assert any('quality' in call.lower() for call in log_calls), "Should log quality metrics"

    @patch('dags.etl_pipeline.analyze_csv_quality')
    def test_validate_all_thresholds_passing(self, mock_analyze):
        """Test that _validate passes when all thresholds are met"""
        # Perfect quality data
        mock_analyze.return_value = (95, {
            'row_count': 100,
            'completeness': 100,
            'validity': 95,
            'uniqueness': 100,
            'null_percentage': 0,
            'duplicate_percentage': 0
        })
        
        ti = Mock()
        ti.xcom_pull.return_value = self.processed_file.name
        
        # Should pass all checks
        result = _validate(ti=ti)
        assert result is True or result == 'passed', "Perfect data should pass all thresholds"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
