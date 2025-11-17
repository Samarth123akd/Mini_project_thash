"""Loading helpers for ecommerce ETL.

This module provides a light-weight CSV fallback and an optional Postgres
loader that uses SQLAlchemy when available. The code is defensive so it will
work in minimal environments (writing processed CSVs) and in full environments
that have a database configured.
"""
from typing import List, Dict, Optional
import os
import csv
import tempfile
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def save_to_csv(rows: List[Dict], out_path: str) -> None:
	"""Save cleaned rows to a CSV file (creates directory if needed)."""
	if not rows:
		os.makedirs(os.path.dirname(out_path), exist_ok=True)
		# write an empty file with no rows
		with open(out_path, 'w', newline='', encoding='utf-8') as fh:
			fh.write('')
		return

	fieldnames = list({k for r in rows for k in r.keys()})
	os.makedirs(os.path.dirname(out_path), exist_ok=True)
	with open(out_path, 'w', newline='', encoding='utf-8') as fh:
		writer = csv.DictWriter(fh, fieldnames=fieldnames)
		writer.writeheader()
		for r in rows:
			writer.writerow(r)


def save_to_postgres(rows: List[Dict], table_name: str, connection_string: str) -> None:
	"""Save rows to Postgres using SQLAlchemy. Falls back to CSV if SQLAlchemy
	isn't available.
	"""
	try:
		# import modules at runtime to avoid static analyzer errors when packages
		# aren't installed in minimal environments
		import importlib
		sqlalchemy = importlib.import_module('sqlalchemy')
		create_engine = getattr(sqlalchemy, 'create_engine')
		pd = importlib.import_module('pandas')
	except Exception:
		# fallback: write to csv in data/processed
		out = os.path.join('data', 'processed', f'{table_name}_processed.csv')
		save_to_csv(rows, out)
		return

	df = pd.DataFrame(rows)
	engine = create_engine(connection_string)
	# simple append/replace behaviour: if table exists, append
	df.to_sql(table_name, con=engine, if_exists='append', index=False)


def load_processed_to(table_name: str, conn_str: str, processed_csv: str) -> None:
	"""Convenience: read processed CSV and push to Postgres using SQLAlchemy.
	If SQLAlchemy isn't installed, simply ensures processed CSV exists.
	"""
	if not os.path.exists(processed_csv):
		raise FileNotFoundError(processed_csv)

	rows = []
	with open(processed_csv, newline='', encoding='utf-8') as fh:
		reader = csv.DictReader(fh)
		for r in reader:
			rows.append(r)

	save_to_postgres(rows, table_name, conn_str)


def load_table_copy(df_or_rows: any, table_name: str, connection_string: str, 
                    method: str = 'copy') -> Dict:
	"""Load data using efficient COPY or bulk insert.
	
	Args:
		df_or_rows: DataFrame or list of dicts
		table_name: Target table name
		connection_string: PostgreSQL connection string
		method: 'copy' for COPY FROM, 'bulk' for execute_values
	
	Returns:
		Dict with rows_loaded, method, status
	"""
	try:
		import psycopg2
		import psycopg2.extras
		from io import StringIO
	except ImportError:
		logger.warning("psycopg2 not available, falling back to SQLAlchemy")
		return save_to_postgres(df_or_rows if isinstance(df_or_rows, list) else df_or_rows.to_dict('records'), 
		                        table_name, connection_string)
	
	# Convert to DataFrame if needed
	try:
		import pandas as pd
		if isinstance(df_or_rows, list):
			df = pd.DataFrame(df_or_rows)
		else:
			df = df_or_rows
	except ImportError:
		# Fallback without pandas
		if isinstance(df_or_rows, list):
			return save_to_postgres(df_or_rows, table_name, connection_string)
		raise ValueError("pandas required for DataFrame input")
	
	conn = psycopg2.connect(connection_string)
	cur = conn.cursor()
	
	try:
		if method == 'copy':
			# Use COPY for fastest loading
			# Create temp CSV in memory
			buffer = StringIO()
			df.to_csv(buffer, index=False, header=False)
			buffer.seek(0)
			
			# Get column names
			columns = ', '.join(df.columns)
			
			# COPY command
			copy_sql = f"COPY {table_name} ({columns}) FROM STDIN WITH CSV"
			cur.copy_expert(copy_sql, buffer)
			
			logger.info(f"Loaded {len(df)} rows using COPY to {table_name}")
		
		elif method == 'bulk':
			# Use execute_values for bulk insert
			columns = df.columns.tolist()
			values = [tuple(row) for row in df.values]
			
			cols_str = ', '.join(columns)
			insert_sql = f"INSERT INTO {table_name} ({cols_str}) VALUES %s"
			
			psycopg2.extras.execute_values(cur, insert_sql, values)
			logger.info(f"Loaded {len(df)} rows using execute_values to {table_name}")
		
		conn.commit()
		
		return {
			'rows_loaded': len(df),
			'method': method,
			'status': 'success',
			'table': table_name
		}
	
	except Exception as e:
		conn.rollback()
		logger.error(f"Load failed: {e}")
		raise
	finally:
		cur.close()
		conn.close()


def upsert_dimension(df_or_rows: any, table_name: str, connection_string: str,
                    key_columns: List[str], update_columns: Optional[List[str]] = None) -> Dict:
	"""Upsert dimension table data (INSERT ... ON CONFLICT UPDATE).
	
	Args:
		df_or_rows: DataFrame or list of dicts
		table_name: Target dimension table
		connection_string: PostgreSQL connection string
		key_columns: Columns that define uniqueness
		update_columns: Columns to update on conflict (None = all non-key columns)
	
	Returns:
		Dict with rows_inserted, rows_updated, status
	"""
	try:
		import psycopg2
		import psycopg2.extras
		import pandas as pd
	except ImportError:
		logger.warning("psycopg2/pandas not available, falling back to append")
		return load_table_copy(df_or_rows, table_name, connection_string, method='bulk')
	
	# Convert to DataFrame
	if isinstance(df_or_rows, list):
		df = pd.DataFrame(df_or_rows)
	else:
		df = df_or_rows
	
	conn = psycopg2.connect(connection_string)
	cur = conn.cursor()
	
	try:
		columns = df.columns.tolist()
		
		# Determine update columns
		if update_columns is None:
			update_columns = [col for col in columns if col not in key_columns]
		
		# Build upsert SQL
		cols_str = ', '.join(columns)
		values_placeholder = ', '.join(['%s'] * len(columns))
		key_str = ', '.join(key_columns)
		update_set = ', '.join([f"{col} = EXCLUDED.{col}" for col in update_columns])
		
		upsert_sql = f"""
			INSERT INTO {table_name} ({cols_str})
			VALUES ({values_placeholder})
			ON CONFLICT ({key_str})
			DO UPDATE SET {update_set}
		"""
		
		# Execute upserts
		values = [tuple(row) for row in df.values]
		cur.executemany(upsert_sql, values)
		
		conn.commit()
		
		logger.info(f"Upserted {len(df)} rows to dimension table {table_name}")
		
		return {
			'rows_processed': len(df),
			'status': 'success',
			'table': table_name,
			'operation': 'upsert'
		}
	
	except Exception as e:
		conn.rollback()
		logger.error(f"Upsert failed: {e}")
		raise
	finally:
		cur.close()
		conn.close()


def log_ingestion_audit(run_id: str, connection_string: str, 
                       rows_ingested: int, errors: int = 0,
                       status: str = 'success', metadata: Optional[Dict] = None) -> None:
	"""Log pipeline run to ingest_audit table.
	
	Args:
		run_id: Unique run identifier
		connection_string: PostgreSQL connection string
		rows_ingested: Number of rows loaded
		errors: Number of errors encountered
		status: 'success', 'failed', or 'partial'
		metadata: Additional metadata as JSON
	"""
	try:
		import psycopg2
		import json
		from datetime import datetime
	except ImportError:
		logger.warning("psycopg2 not available, skipping audit log")
		return
	
	conn = psycopg2.connect(connection_string)
	cur = conn.cursor()
	
	try:
		insert_sql = """
			INSERT INTO ingest_audit (run_id, rows_ingested, errors, status, metadata, finished_at)
			VALUES (%s, %s, %s, %s, %s, %s)
		"""
		
		cur.execute(insert_sql, (
			run_id,
			rows_ingested,
			errors,
			status,
			json.dumps(metadata or {}),
			datetime.now()
		))
		
		conn.commit()
		logger.info(f"Logged audit for run_id: {run_id}")
	
	except Exception as e:
		conn.rollback()
		logger.error(f"Audit logging failed: {e}")
	finally:
		cur.close()
		conn.close()
	"""Convenience wrapper: read DATABASE_URL from env and load processed CSV.

	If DATABASE_URL is not set, falls back to CSV behavior (no-op beyond
	ensuring processed CSV exists).
	"""
	conn = os.environ.get('DATABASE_URL')
	if not conn:
		# ensure processed CSV exists and exit gracefully
		if not os.path.exists(processed_csv):
			raise FileNotFoundError(processed_csv)
		# leave processed CSV as-is
		return
	load_processed_to(table_name, conn, processed_csv)


if __name__ == '__main__':
	print('Use load.save_to_csv or load.save_to_postgres')

