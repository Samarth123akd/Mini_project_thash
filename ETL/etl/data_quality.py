"""Data quality monitoring and reporting module.

Provides comprehensive data quality metrics, validation reports, and
monitoring dashboards for ETL pipelines.
"""
import logging
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
from pathlib import Path
import json
import csv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataQualityMetrics:
    """Track and compute data quality metrics."""
    
    def __init__(self, dataset_name: str = "unknown"):
        self.dataset_name = dataset_name
        self.metrics = {
            'dataset_name': dataset_name,
            'timestamp': datetime.now().isoformat(),
            'total_records': 0,
            'valid_records': 0,
            'invalid_records': 0,
            'duplicate_records': 0,
            'null_counts': {},
            'completeness_score': 0.0,
            'accuracy_score': 0.0,
            'consistency_score': 0.0,
            'validity_score': 0.0,
            'overall_quality_score': 0.0,
            'field_metrics': {},
            'validation_errors': []
        }
    
    def record_total(self, count: int):
        """Record total number of records."""
        self.metrics['total_records'] = count
    
    def record_valid(self, count: int):
        """Record number of valid records."""
        self.metrics['valid_records'] = count
    
    def record_invalid(self, count: int):
        """Record number of invalid records."""
        self.metrics['invalid_records'] = count
    
    def record_duplicates(self, count: int):
        """Record number of duplicate records."""
        self.metrics['duplicate_records'] = count
    
    def record_null_count(self, field: str, count: int):
        """Record null count for a field."""
        self.metrics['null_counts'][field] = count
    
    def add_validation_error(self, error: Dict):
        """Add a validation error."""
        self.metrics['validation_errors'].append(error)
    
    def add_field_metric(self, field: str, metric: Dict):
        """Add metrics for a specific field."""
        self.metrics['field_metrics'][field] = metric
    
    def compute_scores(self):
        """Compute quality scores."""
        total = self.metrics['total_records']
        if total == 0:
            return
        
        # Completeness: % of records without nulls
        total_nulls = sum(self.metrics['null_counts'].values())
        total_fields = len(self.metrics['null_counts']) * total if self.metrics['null_counts'] else total
        self.metrics['completeness_score'] = round(
            (1 - total_nulls / max(total_fields, 1)) * 100, 2
        )
        
        # Validity: % of valid records
        self.metrics['validity_score'] = round(
            (self.metrics['valid_records'] / total) * 100, 2
        )
        
        # Consistency: % of non-duplicate records
        self.metrics['consistency_score'] = round(
            (1 - self.metrics['duplicate_records'] / total) * 100, 2
        )
        
        # Overall quality score (weighted average)
        self.metrics['overall_quality_score'] = round(
            (self.metrics['completeness_score'] * 0.3 +
             self.metrics['validity_score'] * 0.4 +
             self.metrics['consistency_score'] * 0.3), 2
        )
    
    def get_report(self) -> Dict:
        """Get quality report as dictionary."""
        self.compute_scores()
        return self.metrics
    
    def save_report(self, output_path: str):
        """Save quality report to JSON file."""
        report = self.get_report()
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Quality report saved to {output_path}")
    
    def print_summary(self):
        """Print quality summary to console."""
        report = self.get_report()
        
        print(f"\n{'='*60}")
        print(f"Data Quality Report: {self.dataset_name}")
        print(f"Timestamp: {report['timestamp']}")
        print(f"{'='*60}")
        print(f"Total Records: {report['total_records']:,}")
        print(f"Valid Records: {report['valid_records']:,}")
        print(f"Invalid Records: {report['invalid_records']:,}")
        print(f"Duplicate Records: {report['duplicate_records']:,}")
        print(f"\n{'Quality Scores':^60}")
        print(f"{'-'*60}")
        print(f"Completeness Score: {report['completeness_score']:.2f}%")
        print(f"Validity Score: {report['validity_score']:.2f}%")
        print(f"Consistency Score: {report['consistency_score']:.2f}%")
        print(f"Overall Quality Score: {report['overall_quality_score']:.2f}%")
        
        if report['null_counts']:
            print(f"\n{'Null Counts by Field':^60}")
            print(f"{'-'*60}")
            for field, count in sorted(report['null_counts'].items(), 
                                      key=lambda x: x[1], reverse=True):
                pct = (count / report['total_records']) * 100
                print(f"{field:30} {count:>10,} ({pct:>5.1f}%)")
        
        if report['validation_errors']:
            print(f"\n{'Validation Errors (first 10)':^60}")
            print(f"{'-'*60}")
            for error in report['validation_errors'][:10]:
                print(f"Row: {error.get('row_id', 'N/A'):15} "
                      f"Field: {error.get('field', 'N/A'):20} "
                      f"Reason: {error.get('reason', 'N/A')}")
        
        print(f"{'='*60}\n")


def analyze_csv_quality(csv_path: str, key_fields: Optional[List[str]] = None) -> DataQualityMetrics:
    """Analyze data quality of a CSV file.
    
    Args:
        csv_path: Path to CSV file
        key_fields: Optional list of fields to use for duplicate detection
    
    Returns:
        DataQualityMetrics object with computed metrics
    """
    metrics = DataQualityMetrics(dataset_name=Path(csv_path).name)
    
    if not Path(csv_path).exists():
        logger.error(f"File not found: {csv_path}")
        return metrics
    
    # Read and analyze data
    rows = []
    null_counts = {}
    field_stats = {}
    
    with open(csv_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        
        # Initialize null counters
        for field in fieldnames:
            null_counts[field] = 0
            field_stats[field] = {
                'min_length': float('inf'),
                'max_length': 0,
                'numeric_count': 0,
                'total_values': 0
            }
        
        for row in reader:
            rows.append(row)
            
            # Count nulls and field statistics
            for field in fieldnames:
                value = row.get(field, '')
                
                if value in ('', None, 'NULL', 'null', 'N/A'):
                    null_counts[field] += 1
                else:
                    stats = field_stats[field]
                    stats['total_values'] += 1
                    stats['min_length'] = min(stats['min_length'], len(str(value)))
                    stats['max_length'] = max(stats['max_length'], len(str(value)))
                    
                    # Check if numeric
                    try:
                        float(value)
                        stats['numeric_count'] += 1
                    except:
                        pass
    
    total_rows = len(rows)
    metrics.record_total(total_rows)
    
    # Record null counts
    for field, count in null_counts.items():
        metrics.record_null_count(field, count)
    
    # Add field metrics
    for field, stats in field_stats.items():
        if stats['total_values'] > 0:
            metrics.add_field_metric(field, {
                'min_length': stats['min_length'],
                'max_length': stats['max_length'],
                'is_numeric': stats['numeric_count'] / stats['total_values'] > 0.9,
                'completeness': round((stats['total_values'] / total_rows) * 100, 2)
            })
    
    # Detect duplicates
    if key_fields:
        seen = set()
        duplicates = 0
        for row in rows:
            key = tuple(row.get(f, '') for f in key_fields)
            if key in seen:
                duplicates += 1
            else:
                seen.add(key)
        metrics.record_duplicates(duplicates)
    
    # Assume valid unless proven invalid (would need custom validation logic)
    metrics.record_valid(total_rows - sum(null_counts.values()))
    metrics.record_invalid(0)
    
    logger.info(f"Quality analysis complete for {csv_path}")
    return metrics


def compare_datasets(source_metrics: DataQualityMetrics, 
                    target_metrics: DataQualityMetrics) -> Dict:
    """Compare quality metrics between two datasets.
    
    Args:
        source_metrics: Metrics from source dataset
        target_metrics: Metrics from target dataset
    
    Returns:
        Comparison report dictionary
    """
    source_report = source_metrics.get_report()
    target_report = target_metrics.get_report()
    
    comparison = {
        'source_dataset': source_report['dataset_name'],
        'target_dataset': target_report['dataset_name'],
        'timestamp': datetime.now().isoformat(),
        'record_count_change': target_report['total_records'] - source_report['total_records'],
        'quality_score_change': target_report['overall_quality_score'] - source_report['overall_quality_score'],
        'completeness_change': target_report['completeness_score'] - source_report['completeness_score'],
        'validity_change': target_report['validity_score'] - source_report['validity_score'],
        'consistency_change': target_report['consistency_score'] - source_report['consistency_score'],
        'duplicate_change': target_report['duplicate_records'] - source_report['duplicate_records'],
    }
    
    return comparison


def generate_quality_dashboard(metrics_list: List[DataQualityMetrics], 
                               output_path: str):
    """Generate HTML dashboard for quality metrics.
    
    Args:
        metrics_list: List of DataQualityMetrics objects
        output_path: Path to save HTML dashboard
    """
    html = ['<html><head><title>Data Quality Dashboard</title>']
    html.append('<style>')
    html.append('body { font-family: Arial, sans-serif; margin: 20px; }')
    html.append('table { border-collapse: collapse; width: 100%; margin: 20px 0; }')
    html.append('th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }')
    html.append('th { background-color: #4CAF50; color: white; }')
    html.append('.good { color: green; font-weight: bold; }')
    html.append('.warning { color: orange; font-weight: bold; }')
    html.append('.bad { color: red; font-weight: bold; }')
    html.append('</style>')
    html.append('</head><body>')
    html.append('<h1>Data Quality Dashboard</h1>')
    html.append(f'<p>Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>')
    
    # Summary table
    html.append('<h2>Quality Summary</h2>')
    html.append('<table>')
    html.append('<tr><th>Dataset</th><th>Total Records</th><th>Quality Score</th>'
                '<th>Completeness</th><th>Validity</th><th>Consistency</th></tr>')
    
    for metrics in metrics_list:
        report = metrics.get_report()
        score = report['overall_quality_score']
        score_class = 'good' if score >= 90 else 'warning' if score >= 70 else 'bad'
        
        html.append(f"<tr>")
        html.append(f"<td>{report['dataset_name']}</td>")
        html.append(f"<td>{report['total_records']:,}</td>")
        html.append(f"<td class='{score_class}'>{score:.1f}%</td>")
        html.append(f"<td>{report['completeness_score']:.1f}%</td>")
        html.append(f"<td>{report['validity_score']:.1f}%</td>")
        html.append(f"<td>{report['consistency_score']:.1f}%</td>")
        html.append(f"</tr>")
    
    html.append('</table>')
    html.append('</body></html>')
    
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        f.write('\n'.join(html))
    
    logger.info(f"Quality dashboard saved to {output_path}")


if __name__ == '__main__':
    print("Data Quality Monitoring Module")
    print("Use analyze_csv_quality() to analyze data quality")
