"""Ingestion helpers.

Functions are written to work with standard library so unit tests can run without
installing heavy dependencies. If pandas or the Kaggle API are available, the
module will use them when appropriate.
"""
from typing import List, Dict, Optional
import csv
import json
import os
from pathlib import Path
from datetime import datetime
import shutil
import gzip
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def read_csv_from_path(path: str) -> List[Dict]:
    """Read a CSV and return a list of dicts (one per row).

    This function uses the Python csv module so it's dependency-light and fast
    for small sample files used in tests and demos.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"CSV file not found: {path}")

    with open(path, newline='', encoding='utf-8') as fh:
        reader = csv.DictReader(fh)
        return [dict(row) for row in reader]


def download_from_kaggle(dataset: str, dest_path: str) -> None:
    """Attempt to download a dataset using the Kaggle CLI or API.

    This function is optional and will raise if the kaggle package/CLI is not
    available. Prefer running the kaggle CLI manually (see README).
    """
    try:
        # Try to use subprocess + kaggle CLI if available
        import subprocess
        subprocess.run(['kaggle', 'datasets', 'download', '-d', dataset, '-p', dest_path, '--unzip'], check=True)
    except Exception as exc:
        raise RuntimeError("Failed to download from Kaggle; ensure kaggle CLI is configured") from exc


def save_raw(payload: any, dest_path: Path, compress: bool = True) -> Path:
    """Save raw payload to staging/raw directory with optional compression.
    
    Args:
        payload: Data to save (dict, list, or dataframe)
        dest_path: Destination file path
        compress: Whether to create a compressed archive copy
    
    Returns:
        Path to saved file
    """
    dest_path = Path(dest_path)
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Determine file format and save
    if dest_path.suffix == '.json':
        with open(dest_path, 'w', encoding='utf-8') as f:
            if isinstance(payload, (dict, list)):
                json.dump(payload, f, indent=2, default=str)
            else:
                json.dump(str(payload), f)
        logger.info(f"Saved raw JSON to {dest_path}")
    
    elif dest_path.suffix == '.csv':
        # Try pandas first, fallback to csv module
        try:
            import pandas as pd
            if isinstance(payload, pd.DataFrame):
                payload.to_csv(dest_path, index=False)
            elif isinstance(payload, list) and payload and isinstance(payload[0], dict):
                pd.DataFrame(payload).to_csv(dest_path, index=False)
            else:
                raise ValueError("CSV format requires DataFrame or list of dicts")
            logger.info(f"Saved raw CSV to {dest_path}")
        except ImportError:
            # Fallback to csv module
            if isinstance(payload, list) and payload and isinstance(payload[0], dict):
                with open(dest_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=payload[0].keys())
                    writer.writeheader()
                    writer.writerows(payload)
                logger.info(f"Saved raw CSV to {dest_path}")
            else:
                raise ValueError("CSV format requires list of dicts")
    
    # Create compressed archive copy
    if compress:
        archive_dir = dest_path.parent.parent.parent / 'archive' / dest_path.parent.name
        archive_dir.mkdir(parents=True, exist_ok=True)
        archive_path = archive_dir / f"{dest_path.stem}.gz"
        
        with open(dest_path, 'rb') as f_in:
            with gzip.open(archive_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        logger.info(f"Archived compressed copy to {archive_path}")
    
    return dest_path


def fetch_shopify_orders(api_key: str, shop_url: str, start_date: str, end_date: str) -> Path:
    """Fetch orders from Shopify API and save to staging/raw.
    
    Args:
        api_key: Shopify API access token
        shop_url: Shop URL (e.g., 'mystore.myshopify.com')
        start_date: Start date (ISO format)
        end_date: End date (ISO format)
    
    Returns:
        Path to saved raw data file
    """
    from etl.api_ingest import APIIngestor
    
    ingestor = APIIngestor(rate_limit_calls=2, rate_limit_window=1)
    orders = ingestor.fetch_shopify_orders(shop_url, api_key)
    
    # Generate destination path
    today = datetime.now().strftime('%Y-%m-%d')
    dest_path = Path('data/staging/raw/shopify') / today / 'orders.json'
    
    return save_raw(orders, dest_path, compress=True)


def fetch_stripe_payments(api_key: str, start_date: Optional[str] = None, 
                         end_date: Optional[str] = None) -> Path:
    """Fetch payments from Stripe API and save to staging/raw.
    
    Args:
        api_key: Stripe secret API key
        start_date: Start date (ISO format)
        end_date: End date (ISO format)
    
    Returns:
        Path to saved raw data file
    """
    from etl.api_ingest import APIIngestor
    
    ingestor = APIIngestor(rate_limit_calls=25, rate_limit_window=1)
    charges = ingestor.fetch_stripe_charges(api_key, limit=100)
    
    # Generate destination path
    today = datetime.now().strftime('%Y-%m-%d')
    dest_path = Path('data/staging/raw/stripe') / today / 'payments.json'
    
    return save_raw(charges, dest_path, compress=True)


def read_csv_batch(path: str, chunksize: int = 10000) -> List[Dict]:
    """Read CSV in batches to handle large files.
    
    Args:
        path: Path to CSV file
        chunksize: Number of rows per batch
    
    Returns:
        List of dictionaries (one per row)
    """
    try:
        import pandas as pd
        chunks = []
        for chunk in pd.read_csv(path, chunksize=chunksize):
            chunks.append(chunk.to_dict('records'))
        
        # Flatten chunks
        all_rows = []
        for chunk in chunks:
            all_rows.extend(chunk)
        
        logger.info(f"Read {len(all_rows)} rows from {path} in batches")
        return all_rows
    except ImportError:
        # Fallback to standard CSV reading
        return read_csv_from_path(path)


def fetch_from_source(source_config: Dict) -> Path:
    """Generic function to fetch from various sources.
    
    Args:
        source_config: Dict with keys:
            - type: 'shopify', 'stripe', 'csv', 'api', 'database'
            - Additional config specific to source type
    
    Returns:
        Path to saved raw data file
    
    Example:
        config = {
            'type': 'shopify',
            'api_key': 'xxx',
            'shop_url': 'mystore.myshopify.com',
            'start_date': '2024-01-01',
            'end_date': '2024-12-31'
        }
        path = fetch_from_source(config)
    """
    source_type = source_config.get('type', '').lower()
    
    if source_type == 'shopify':
        return fetch_shopify_orders(
            source_config['api_key'],
            source_config['shop_url'],
            source_config.get('start_date'),
            source_config.get('end_date')
        )
    
    elif source_type == 'stripe':
        return fetch_stripe_payments(
            source_config['api_key'],
            source_config.get('start_date'),
            source_config.get('end_date')
        )
    
    elif source_type == 'csv':
        # Copy CSV to staging/raw
        source_path = Path(source_config['path'])
        today = datetime.now().strftime('%Y-%m-%d')
        dest_path = Path('data/staging/raw/csv') / today / source_path.name
        
        data = read_csv_from_path(str(source_path))
        return save_raw(data, dest_path, compress=True)
    
    elif source_type == 'database':
        from etl.db_ingest import ingest_from_database
        
        data = ingest_from_database(
            source_config['db_config'],
            source_config['table_name'],
            source_config.get('limit')
        )
        
        today = datetime.now().strftime('%Y-%m-%d')
        db_type = source_config['db_config'].get('type', 'database')
        dest_path = Path(f'data/staging/raw/{db_type}') / today / f"{source_config['table_name']}.json"
        
        return save_raw(data, dest_path, compress=True)
    
    elif source_type == 'api':
        from etl.api_ingest import fetch_from_api
        
        data = fetch_from_api(
            source_config['api_type'],
            source_config['api_config']
        )
        
        today = datetime.now().strftime('%Y-%m-%d')
        dest_path = Path(f'data/staging/raw/api') / today / 'data.json'
        
        return save_raw(data, dest_path, compress=True)
    
    else:
        raise ValueError(f"Unsupported source type: {source_type}")


if __name__ == '__main__':
    # small debug helper
    print('ETL ingest module. Use read_csv_from_path(path)')
