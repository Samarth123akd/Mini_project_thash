"""Transformations for ecommerce data.

This module provides lightweight functions to clean and prepare order data.
It prefers pandas when available but has small pure-Python fallbacks so unit
tests and demos can run in minimal environments.
"""
from typing import List, Dict, Set, Tuple, Optional, Callable
import os
import csv
from datetime import datetime
import hashlib
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def normalize_currency(amount: float, currency: str = 'BRL') -> Dict:
	"""Convert amount to smallest unit (cents) with currency code.
	
	Args:
		amount: Amount in currency units
		currency: Currency code (default BRL for Brazilian Real)
	
	Returns:
		Dict with amount_cents and currency code
	"""
	return {
		'amount_cents': int(amount * 100),
		'currency': currency.upper()
	}


def compute_order_metrics(order_items: List[Dict]) -> Dict:
	"""Compute order-level metrics from items.
	
	Args:
		order_items: List of order item dictionaries
	
	Returns:
		Dict with order_total, order_item_count
	"""
	order_total = sum(item.get('total_amount', 0) for item in order_items)
	item_count = len(order_items)
	
	return {
		'order_total': order_total,
		'order_item_count': item_count
	}


def _parse_float(value: str) -> float:
	try:
		return float(value)
	except Exception:
		return 0.0


class DataQualityReport:
	"""Track data quality metrics during transformation."""
	
	def __init__(self):
		self.total_rows = 0
		self.dropped_rows = 0
		self.duplicates_removed = 0
		self.missing_values_imputed = 0
		self.validation_failures = 0
		self.validation_errors = []
	
	def add_validation_error(self, row_id: str, field: str, reason: str):
		"""Record a validation error."""
		self.validation_failures += 1
		self.validation_errors.append({
			'row_id': row_id,
			'field': field,
			'reason': reason
		})
	
	def summary(self) -> Dict:
		"""Return quality report summary."""
		return {
			'total_rows': self.total_rows,
			'dropped_rows': self.dropped_rows,
			'duplicates_removed': self.duplicates_removed,
			'missing_values_imputed': self.missing_values_imputed,
			'validation_failures': self.validation_failures,
			'clean_rows': self.total_rows - self.dropped_rows - self.duplicates_removed,
			'data_quality_score': round((self.total_rows - self.dropped_rows - self.validation_failures) / max(self.total_rows, 1) * 100, 2)
		}


class BusinessRuleValidator:
	"""Validate data against configurable business rules."""
	
	def __init__(self):
		self.rules = []
	
	def add_rule(self, field: str, validator: Callable, error_message: str):
		"""Add a validation rule.
		
		Args:
			field: Field name to validate
			validator: Function that takes a value and returns True if valid
			error_message: Error message if validation fails
		"""
		self.rules.append({
			'field': field,
			'validator': validator,
			'error': error_message
		})
	
	def validate(self, row: Dict, quality_report: Optional[DataQualityReport] = None) -> Tuple[bool, List[str]]:
		"""Validate a row against all rules.
		
		Returns:
			(is_valid, list_of_errors)
		"""
		errors = []
		for rule in self.rules:
			field = rule['field']
			value = row.get(field)
			
			try:
				if not rule['validator'](value):
					errors.append(f"{field}: {rule['error']}")
					if quality_report:
						quality_report.add_validation_error(
							row.get('InvoiceNo', 'unknown'),
							field,
							rule['error']
						)
			except Exception as e:
				errors.append(f"{field}: validation error - {e}")
		
		return len(errors) == 0, errors


def get_default_business_rules() -> BusinessRuleValidator:
	"""Get standard business rules for ecommerce data."""
	validator = BusinessRuleValidator()
	
	# Quantity rules
	validator.add_rule('quantity', lambda q: q is not None and int(q) > 0, 
	                  'Quantity must be positive')
	validator.add_rule('quantity', lambda q: q is not None and int(q) <= 10000,
	                  'Quantity exceeds maximum (10000)')
	
	# Price rules
	validator.add_rule('unit_price', lambda p: p is not None and float(p) >= 0,
	                  'Price cannot be negative')
	validator.add_rule('unit_price', lambda p: p is not None and float(p) <= 1000000,
	                  'Price exceeds maximum (1M)')
	
	# Total amount rules
	validator.add_rule('total_amount', lambda t: t is not None and float(t) >= 0,
	                  'Total amount cannot be negative')
	
	return validator


def compute_row_hash(row: Dict, key_fields: List[str]) -> str:
	"""Compute hash for duplicate detection.
	
	Args:
		row: Data row
		key_fields: Fields to include in hash
	
	Returns:
		MD5 hash string
	"""
	values = [str(row.get(f, '')) for f in key_fields]
	combined = '|'.join(values)
	return hashlib.md5(combined.encode()).hexdigest()


def remove_duplicates(rows: List[Dict], key_fields: Optional[List[str]] = None) -> Tuple[List[Dict], int]:
	"""Remove duplicate rows based on key fields.
	
	Args:
		rows: List of data rows
		key_fields: Fields to use for duplicate detection (default: all fields)
	
	Returns:
		(deduplicated_rows, number_of_duplicates_removed)
	"""
	if not rows:
		return [], 0
	
	# Default to key fields commonly used in ecommerce
	if key_fields is None:
		key_fields = ['InvoiceNo', 'StockCode', 'invoice_date', 'quantity', 'unit_price']
	
	seen_hashes: Set[str] = set()
	unique_rows = []
	duplicates = 0
	
	for row in rows:
		row_hash = compute_row_hash(row, key_fields)
		
		if row_hash not in seen_hashes:
			seen_hashes.add(row_hash)
			unique_rows.append(row)
		else:
			duplicates += 1
			logger.debug(f"Duplicate detected: {row.get('InvoiceNo', 'unknown')}")
	
	if duplicates > 0:
		logger.info(f"Removed {duplicates} duplicate rows")
	
	return unique_rows, duplicates


def impute_missing_values(rows: List[Dict], strategy: str = 'default') -> Tuple[List[Dict], int]:
	"""Impute missing values using specified strategy.
	
	Args:
		rows: List of data rows
		strategy: 'default' (zeros), 'mean', 'median', or 'mode'
	
	Returns:
		(rows_with_imputed_values, number_of_imputations)
	"""
	if not rows or strategy == 'default':
		return rows, 0  # Default strategy already handled in clean_rows
	
	imputations = 0
	numeric_fields = ['quantity', 'unit_price', 'total_amount']
	
	# Calculate statistics for each field
	stats = {}
	if strategy in ['mean', 'median', 'mode']:
		for field in numeric_fields:
			values = []
			for row in rows:
				val = row.get(field)
				if val not in (None, '', 0):
					try:
						values.append(float(val))
					except:
						pass
			
			if values:
				if strategy == 'mean':
					stats[field] = sum(values) / len(values)
				elif strategy == 'median':
					sorted_vals = sorted(values)
					mid = len(sorted_vals) // 2
					stats[field] = sorted_vals[mid] if len(sorted_vals) % 2 != 0 else (sorted_vals[mid-1] + sorted_vals[mid]) / 2
				elif strategy == 'mode':
					stats[field] = max(set(values), key=values.count)
	
	# Apply imputation
	for row in rows:
		for field in numeric_fields:
			if row.get(field) in (None, '', 0) and field in stats:
				row[field] = stats[field]
				imputations += 1
	
	if imputations > 0:
		logger.info(f"Imputed {imputations} missing values using {strategy} strategy")
	
	return rows, imputations


def clean_rows(rows: List[Dict], remove_dupes: bool = True, 
               imputation_strategy: str = 'default',
               validate_rules: bool = True,
               return_quality_report: bool = False) -> List[Dict] | Tuple[List[Dict], DataQualityReport]:
	"""Clean a list of dict rows and compute derived fields.

	- removes duplicates (optional)
	- imputes missing values (configurable strategy)
	- validates business rules (optional)
	- ensures `quantity` and `unit_price` are numbers
	- computes `total_amount` = quantity * unit_price
	- drops rows missing essential fields like InvoiceNo or StockCode
	- normalizes InvoiceDate to ISO8601 string when possible
	
	Args:
		rows: Raw data rows
		remove_dupes: Remove duplicate rows
		imputation_strategy: 'default', 'mean', 'median', or 'mode'
		validate_rules: Apply business rule validation
		return_quality_report: Return quality metrics
	
	Returns:
		Cleaned rows or (cleaned_rows, quality_report) if return_quality_report=True
	"""
	quality_report = DataQualityReport()
	quality_report.total_rows = len(rows)
	
	# Remove duplicates
	if remove_dupes:
		rows, dupes_removed = remove_duplicates(rows)
		quality_report.duplicates_removed = dupes_removed
	
	# Setup business rule validator
	validator = get_default_business_rules() if validate_rules else None
	
	out = []
	for r in rows:
		invoice = r.get('InvoiceNo') or r.get('Invoice') or r.get('invoice')
		stock = r.get('StockCode') or r.get('stockcode')
		if not invoice or not stock:
			quality_report.dropped_rows += 1
			continue

		# quantity
		q = r.get('Quantity') or r.get('quantity') or r.get('Qty')
		try:
			quantity = int(float(q)) if q is not None and q != '' else 0
		except Exception:
			quantity = 0
			quality_report.missing_values_imputed += 1

		# unit price
		up = r.get('UnitPrice') or r.get('unit_price') or r.get('Price')
		unit_price = _parse_float(up)
		if unit_price == 0.0 and up in (None, ''):
			quality_report.missing_values_imputed += 1

		total_amount = quantity * unit_price

		# InvoiceDate normalization
		date_s = r.get('InvoiceDate') or r.get('invoice_date') or r.get('date')
		iso_date = None
		if date_s:
			for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d/%m/%Y %H:%M", "%d/%m/%Y"):
				try:
					dt = datetime.strptime(date_s, fmt)
					iso_date = dt.isoformat(sep=' ')
					break
				except Exception:
					continue

		cleaned = dict(r)
		cleaned['quantity'] = quantity
		cleaned['unit_price'] = unit_price
		cleaned['total_amount'] = total_amount
		if iso_date:
			cleaned['invoice_date_normalized'] = iso_date
		
		# Validate business rules
		if validator:
			is_valid, errors = validator.validate(cleaned, quality_report)
			if not is_valid:
				logger.warning(f"Validation errors for {invoice}: {errors}")
				# Still include row but log the issue
		
		out.append(cleaned)
	
	# Apply advanced imputation if requested
	if imputation_strategy != 'default':
		out, imputations = impute_missing_values(out, imputation_strategy)
		quality_report.missing_values_imputed += imputations
	
	logger.info(f"Data quality: {quality_report.summary()}")
	
	if return_quality_report:
		return out, quality_report
	return out


def transform_csv(in_path: str, out_path: str, output_format: str = 'csv') -> None:
	"""Read CSV at in_path, clean it, and write a processed file to out_path.

	This is a small convenience used by the simple dashboard and tests.
	
	Args:
		in_path: Input CSV path
		out_path: Output file path
		output_format: 'csv' or 'parquet'
	"""
	if not os.path.exists(in_path):
		raise FileNotFoundError(in_path)

	with open(in_path, newline='', encoding='utf-8') as fh:
		reader = csv.DictReader(fh)
		rows = [dict(r) for r in reader]

	cleaned = clean_rows(rows)
	
	# Add enrichment metadata
	for row in cleaned:
		row['ingest_metadata'] = json.dumps({
			'source': 'csv',
			'raw_path': in_path,
			'ingested_at': datetime.now().isoformat()
		})

	# Write output based on format
	if output_format == 'parquet':
		try:
			import pandas as pd
			df = pd.DataFrame(cleaned)
			os.makedirs(os.path.dirname(out_path), exist_ok=True)
			df.to_parquet(out_path, index=False, engine='pyarrow', compression='snappy')
			logger.info(f"Wrote {len(cleaned)} rows to Parquet: {out_path}")
		except ImportError:
			logger.warning("pandas/pyarrow not available, falling back to CSV")
			output_format = 'csv'
	
	if output_format == 'csv':
		# Write out fields in a stable order
		fieldnames = list({k for row in cleaned for k in row.keys()})
		os.makedirs(os.path.dirname(out_path), exist_ok=True)
		with open(out_path, 'w', newline='', encoding='utf-8') as fh:
			writer = csv.DictWriter(fh, fieldnames=fieldnames)
			writer.writeheader()
			for r in cleaned:
				writer.writerow(r)
		logger.info(f"Wrote {len(cleaned)} rows to CSV: {out_path}")


if __name__ == '__main__':
	print('Use transform.transform_csv(in_path, out_path)')

