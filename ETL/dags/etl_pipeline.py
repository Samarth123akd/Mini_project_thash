"""A simple Airflow DAG scaffold for the ecommerce ETL.

This DAG is minimal and uses PythonOperator-style callables that import the
local `etl` package functions. It is intentionally trivial so it runs in a
development Airflow without extra dependencies.
"""
from datetime import datetime, timedelta
import os

from typing import TYPE_CHECKING

try:
    if TYPE_CHECKING:
        # Allow type checkers / linters to see Airflow symbols without failing at runtime.
        from airflow import DAG  # type: ignore
        from airflow.operators.python import PythonOperator  # type: ignore
        from airflow.models import Variable  # type: ignore
    else:
        from airflow import DAG
        from airflow.operators.python import PythonOperator
        from airflow.models import Variable
except Exception:
    # Airflow not available (e.g., in local dev or linter); provide minimal stubs
    from types import SimpleNamespace

    class DAG:
        def __init__(self, *args, **kwargs):
            pass
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc, tb):
            return False

    class PythonOperator:
        def __init__(self, *args, **kwargs):
            pass

    class Variable:
        @staticmethod
        def get(key):
            # raise to preserve original fallback behavior in _load
            raise KeyError(key)

from etl.ingest import read_csv_from_path
from etl.transform import transform_csv
from etl.load import save_to_csv, load_processed_from_env
import logging

logger = logging.getLogger(__name__)


DEFAULT_ARGS = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email': ['alerts@company.com'],  # Configure for your team
    'email_on_failure': True,
    'email_on_retry': True,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
    'retry_exponential_backoff': True,
    'max_retry_delay': timedelta(minutes=30),
    'execution_timeout': timedelta(hours=2),
    'sla': timedelta(hours=4),  # Alert if task takes > 4 hours
}


def _ingest(**context):
    # simple local ingest: expects a sample file in data/staging
    # prefer Olist/Brazilian dataset file names but fall back to generic orders.csv
    olist = 'data/staging/olist_orders_dataset.csv'
    default = 'data/staging/orders.csv'
    src = olist if os.path.exists(olist) else default
    
    try:
        logger.info(f"Starting ingestion from {src}")
        rows = read_csv_from_path(src)
        row_count = len(rows)
        
        # push rows count for logging and monitoring
        context['ti'].xcom_push(key='rows', value=row_count)
        context['ti'].xcom_push(key='source_file', value=src)
        
        logger.info(f"Successfully ingested {row_count} rows from {src}")
        
        # Data quality check
        if row_count == 0:
            raise ValueError(f"No data found in source file: {src}")
        
        return row_count
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        raise


def _transform(**context):
    # prefer Olist orders dataset file if present
    olist = 'data/staging/olist_orders_dataset.csv'
    default = 'data/staging/orders.csv'
    src = olist if os.path.exists(olist) else default
    dest = 'data/processed/orders_processed.csv'
    
    try:
        logger.info(f"Starting transformation: {src} -> {dest}")
        
        # Get ingest count from previous task
        ti = context['ti']
        ingested_rows = ti.xcom_pull(task_ids='ingest', key='rows')
        logger.info(f"Processing {ingested_rows} ingested rows")
        
        transform_csv(src, dest)
        
        # Verify output
        if not os.path.exists(dest):
            raise FileNotFoundError(f"Transform output not created: {dest}")
        
        # Count transformed rows
        with open(dest, 'r') as f:
            transformed_rows = sum(1 for _ in f) - 1  # -1 for header
        
        ti.xcom_push(key='transformed_rows', value=transformed_rows)
        
        logger.info(f"Transformation complete: {transformed_rows} rows written")
        
        # Alert if significant data loss
        if ingested_rows and transformed_rows < ingested_rows * 0.5:
            logger.warning(f"Data loss detected: {ingested_rows} -> {transformed_rows} rows")
        
        return transformed_rows
    except Exception as e:
        logger.error(f"Transformation failed: {e}")
        raise


def _load(**context):
    # Load processed CSV to Postgres. Prefer Airflow Variable 'DATABASE_URL',
    # fall back to environment variable DATABASE_URL when testing locally.
    processed = 'data/processed/orders_processed.csv'
    conn = None
    
    try:
        logger.info("Starting load phase")
        
        # Get transformation metrics
        ti = context['ti']
        transformed_rows = ti.xcom_pull(task_ids='transform', key='transformed_rows')
        
        try:
            conn = Variable.get('DATABASE_URL')
        except Exception:
            conn = os.environ.get('DATABASE_URL')

        if conn:
            logger.info(f"Loading {transformed_rows} rows to database")
            # use helper that expects a conn string
            from etl.load import load_processed_to
            load_processed_to('orders', conn, processed)
            
            ti.xcom_push(key='loaded_rows', value=transformed_rows)
            ti.xcom_push(key='load_target', value='database')
            
            logger.info(f"Successfully loaded {transformed_rows} rows to database")
        else:
            logger.warning("DATABASE_URL not configured, skipping database load")
            # no DB configured; write a small placeholder to indicate run
            save_to_csv([], 'data/processed/_placeholder.txt')
            ti.xcom_push(key='load_target', value='file')
        
        return transformed_rows
    except Exception as e:
        logger.error(f"Load failed: {e}")
        raise


def _notify_success(**context):
    """Send success notification with pipeline metrics."""
    try:
        ti = context['ti']
        ingested = ti.xcom_pull(task_ids='ingest', key='rows')
        transformed = ti.xcom_pull(task_ids='transform', key='transformed_rows')
        loaded = ti.xcom_pull(task_ids='load', key='loaded_rows')
        
        logger.info(f"Pipeline completed successfully: {ingested} ingested, {transformed} transformed, {loaded} loaded")
    except Exception as e:
        logger.error(f"Notification failed: {e}")


def _handle_failure(context):
    """Callback for task failures - sends alerts."""
    try:
        ti = context['task_instance']
        logger.error(f"Task {ti.task_id} failed in DAG {ti.dag_id}")
        logger.error(f"Execution date: {context['execution_date']}")
        logger.error(f"Log URL: {ti.log_url}")
        # Additional alerting logic can be added here (Slack, PagerDuty, etc.)
    except Exception as e:
        logger.error(f"Failure handler error: {e}")


def _validate(**context):
    """Data quality validation checks after load."""
    import os
    
    try:
        logger.info("Starting data quality validation")
        
        # Get load metrics from previous task
        ti = context['ti']
        loaded_rows = ti.xcom_pull(task_ids='load', key='loaded_rows')
        
        # Check 1: Row count > 0
        if not loaded_rows or loaded_rows == 0:
            raise ValueError("Validation failed: No rows loaded")
        
        logger.info(f"✓ Row count check passed: {loaded_rows} rows")
        
        # Check 2: Verify processed file exists
        processed_file = 'data/processed/orders_processed.csv'
        if not os.path.exists(processed_file):
            raise FileNotFoundError(f"Processed file not found: {processed_file}")
        
        logger.info(f"✓ Processed file exists: {processed_file}")
        
        # Check 3: Data quality using data_quality module
        from etl.data_quality import analyze_csv_quality
        
        metrics = analyze_csv_quality(processed_file, key_fields=['order_id'])
        report = metrics.get_report()
        
        # Quality thresholds
        min_quality_score = 80.0
        max_null_pct = 20.0
        max_duplicate_pct = 5.0
        
        quality_score = report['overall_quality_score']
        null_count = sum(report['null_counts'].values())
        null_pct = (null_count / (report['total_records'] * len(report['null_counts']))) * 100 if report['null_counts'] else 0
        duplicate_pct = (report['duplicate_records'] / max(report['total_records'], 1)) * 100
        
        # Validate thresholds
        if quality_score < min_quality_score:
            logger.warning(f"Quality score ({quality_score:.1f}%) below threshold ({min_quality_score}%)")
        
        if null_pct > max_null_pct:
            logger.warning(f"Null percentage ({null_pct:.1f}%) above threshold ({max_null_pct}%)")
        
        if duplicate_pct > max_duplicate_pct:
            logger.warning(f"Duplicate percentage ({duplicate_pct:.1f}%) above threshold ({max_duplicate_pct}%)")
        
        # Store validation results
        ti.xcom_push(key='quality_score', value=quality_score)
        ti.xcom_push(key='null_percentage', value=null_pct)
        ti.xcom_push(key='duplicate_percentage', value=duplicate_pct)
        
        logger.info(f"✓ Data quality validation complete")
        logger.info(f"  Quality Score: {quality_score:.1f}%")
        logger.info(f"  Null %: {null_pct:.1f}%")
        logger.info(f"  Duplicate %: {duplicate_pct:.1f}%")
        
        # Check 4: Database validation (if DATABASE_URL available)
        db_url = os.environ.get('DATABASE_URL')
        if db_url:
            try:
                import importlib
                sqlalchemy = importlib.import_module('sqlalchemy')
                create_engine = getattr(sqlalchemy, 'create_engine')
                text = getattr(sqlalchemy, 'text')
                
                engine = create_engine(db_url)
                with engine.connect() as conn:
                    # Check order count in DB
                    result = conn.execute(text("SELECT COUNT(*) FROM fact_orders"))
                    db_count = result.scalar()
                    
                    logger.info(f"✓ Database check: {db_count} orders in fact_orders table")
                    
                    # Check for nulls in critical columns
                    null_check = conn.execute(text("""
                        SELECT COUNT(*) FROM fact_orders 
                        WHERE order_id IS NULL 
                           OR order_purchase_timestamp IS NULL 
                           OR customer_id IS NULL
                    """))
                    null_critical = null_check.scalar()
                    
                    if null_critical > 0:
                        logger.warning(f"Found {null_critical} records with NULL critical fields")
                    else:
                        logger.info("✓ No NULLs in critical columns")
                    
                    ti.xcom_push(key='db_row_count', value=db_count)
            except Exception as e:
                logger.warning(f"Database validation skipped: {e}")
        
        return {
            'status': 'passed',
            'quality_score': quality_score,
            'rows_validated': loaded_rows
        }
        
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        raise


with DAG(
    dag_id='ecommerce_etl_pipeline',
    default_args=DEFAULT_ARGS,
    schedule_interval='@daily',
    start_date=datetime(2023, 1, 1),
    catchup=False,
    tags=['ecommerce', 'etl', 'production'],
    description='E-commerce ETL pipeline with monitoring and fault tolerance',
    on_failure_callback=_handle_failure,
) as dag:
    task_ingest = PythonOperator(
        task_id='ingest',
        python_callable=_ingest,
        provide_context=True,
        pool='default_pool',
        priority_weight=10,
    )
    
    task_transform = PythonOperator(
        task_id='transform',
        python_callable=_transform,
        provide_context=True,
        pool='default_pool',
        priority_weight=9,
    )
    
    task_load = PythonOperator(
        task_id='load',
        python_callable=_load,
        provide_context=True,
        pool='default_pool',
        priority_weight=8,
    )
    
    task_validate = PythonOperator(
        task_id='validate',
        python_callable=_validate,
        provide_context=True,
        pool='default_pool',
        priority_weight=7,
    )
    
    task_notify = PythonOperator(
        task_id='notify_success',
        python_callable=_notify_success,
        provide_context=True,
        trigger_rule='all_success',
    )

    # Define task dependencies
    task_ingest >> task_transform >> task_load >> task_validate >> task_notify
