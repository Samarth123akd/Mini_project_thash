"""Database ingestion module for reading from external data sources.

Supports multiple database types:
- PostgreSQL / TimescaleDB
- MySQL / MariaDB
- MongoDB
- SQLite
- Microsoft SQL Server
"""
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseIngestor:
    """Unified database ingestion with connection pooling and error handling."""
    
    def __init__(self, connection_config: Dict[str, Any]):
        """Initialize database connection.
        
        Args:
            connection_config: Dict with keys:
                - type: 'postgres', 'mysql', 'mongodb', 'sqlite', 'mssql'
                - host, port, database, user, password (as needed)
                - connection_string (alternative to individual params)
        """
        self.config = connection_config
        self.db_type = connection_config.get('type', 'postgres').lower()
        self.conn = None
        self.engine = None
    
    def connect(self):
        """Establish database connection."""
        if self.db_type in ['postgres', 'postgresql']:
            self._connect_postgres()
        elif self.db_type == 'mysql':
            self._connect_mysql()
        elif self.db_type == 'mongodb':
            self._connect_mongodb()
        elif self.db_type == 'sqlite':
            self._connect_sqlite()
        elif self.db_type == 'mssql':
            self._connect_mssql()
        else:
            raise ValueError(f"Unsupported database type: {self.db_type}")
    
    def _connect_postgres(self):
        """Connect to PostgreSQL/TimescaleDB."""
        try:
            import importlib
            sqlalchemy = importlib.import_module('sqlalchemy')
            create_engine = getattr(sqlalchemy, 'create_engine')
            
            # Use connection string if provided
            if 'connection_string' in self.config:
                conn_str = self.config['connection_string']
            else:
                host = self.config.get('host', 'localhost')
                port = self.config.get('port', 5432)
                database = self.config['database']
                user = self.config['user']
                password = self.config['password']
                conn_str = f"postgresql://{user}:{password}@{host}:{port}/{database}"
            
            self.engine = create_engine(conn_str, pool_pre_ping=True)
            self.conn = self.engine.connect()
            logger.info(f"Connected to PostgreSQL: {self.config.get('database')}")
        except Exception as e:
            logger.error(f"PostgreSQL connection failed: {e}")
            raise
    
    def _connect_mysql(self):
        """Connect to MySQL/MariaDB."""
        try:
            import importlib
            sqlalchemy = importlib.import_module('sqlalchemy')
            create_engine = getattr(sqlalchemy, 'create_engine')
            
            if 'connection_string' in self.config:
                conn_str = self.config['connection_string']
            else:
                host = self.config.get('host', 'localhost')
                port = self.config.get('port', 3306)
                database = self.config['database']
                user = self.config['user']
                password = self.config['password']
                conn_str = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"
            
            self.engine = create_engine(conn_str, pool_pre_ping=True)
            self.conn = self.engine.connect()
            logger.info(f"Connected to MySQL: {self.config.get('database')}")
        except Exception as e:
            logger.error(f"MySQL connection failed: {e}")
            raise
    
    def _connect_mongodb(self):
        """Connect to MongoDB."""
        try:
            import importlib
            pymongo = importlib.import_module('pymongo')
            MongoClient = getattr(pymongo, 'MongoClient')
            
            if 'connection_string' in self.config:
                conn_str = self.config['connection_string']
            else:
                host = self.config.get('host', 'localhost')
                port = self.config.get('port', 27017)
                user = self.config.get('user')
                password = self.config.get('password')
                
                if user and password:
                    conn_str = f"mongodb://{user}:{password}@{host}:{port}/"
                else:
                    conn_str = f"mongodb://{host}:{port}/"
            
            client = MongoClient(conn_str)
            database = self.config['database']
            self.conn = client[database]
            logger.info(f"Connected to MongoDB: {database}")
        except Exception as e:
            logger.error(f"MongoDB connection failed: {e}")
            raise
    
    def _connect_sqlite(self):
        """Connect to SQLite."""
        try:
            import importlib
            sqlalchemy = importlib.import_module('sqlalchemy')
            create_engine = getattr(sqlalchemy, 'create_engine')
            
            db_path = self.config.get('database', 'data.db')
            conn_str = f"sqlite:///{db_path}"
            
            self.engine = create_engine(conn_str)
            self.conn = self.engine.connect()
            logger.info(f"Connected to SQLite: {db_path}")
        except Exception as e:
            logger.error(f"SQLite connection failed: {e}")
            raise
    
    def _connect_mssql(self):
        """Connect to Microsoft SQL Server."""
        try:
            import importlib
            sqlalchemy = importlib.import_module('sqlalchemy')
            create_engine = getattr(sqlalchemy, 'create_engine')
            
            if 'connection_string' in self.config:
                conn_str = self.config['connection_string']
            else:
                host = self.config.get('host', 'localhost')
                port = self.config.get('port', 1433)
                database = self.config['database']
                user = self.config['user']
                password = self.config['password']
                driver = self.config.get('driver', 'ODBC Driver 17 for SQL Server')
                conn_str = f"mssql+pyodbc://{user}:{password}@{host}:{port}/{database}?driver={driver}"
            
            self.engine = create_engine(conn_str, pool_pre_ping=True)
            self.conn = self.engine.connect()
            logger.info(f"Connected to SQL Server: {self.config.get('database')}")
        except Exception as e:
            logger.error(f"SQL Server connection failed: {e}")
            raise
    
    def fetch_table(self, table_name: str, limit: Optional[int] = None, 
                    where_clause: Optional[str] = None) -> List[Dict]:
        """Fetch data from a table (SQL databases).
        
        Args:
            table_name: Name of table to query
            limit: Maximum rows to fetch
            where_clause: Optional WHERE clause (e.g., "created_at > '2024-01-01'")
        
        Returns:
            List of dictionaries (one per row)
        """
        if self.db_type == 'mongodb':
            return self._fetch_mongodb_collection(table_name, limit)
        
        try:
            import importlib
            sqlalchemy = importlib.import_module('sqlalchemy')
            text = getattr(sqlalchemy, 'text')
            
            query = f"SELECT * FROM {table_name}"
            if where_clause:
                query += f" WHERE {where_clause}"
            if limit:
                query += f" LIMIT {limit}"
            
            result = self.conn.execute(text(query))
            rows = [dict(row) for row in result]
            
            logger.info(f"Fetched {len(rows)} rows from {table_name}")
            return rows
        except Exception as e:
            logger.error(f"Failed to fetch from {table_name}: {e}")
            raise
    
    def _fetch_mongodb_collection(self, collection_name: str, 
                                  limit: Optional[int] = None) -> List[Dict]:
        """Fetch documents from MongoDB collection."""
        try:
            collection = self.conn[collection_name]
            
            cursor = collection.find()
            if limit:
                cursor = cursor.limit(limit)
            
            docs = []
            for doc in cursor:
                # Convert ObjectId to string for JSON serialization
                if '_id' in doc:
                    doc['_id'] = str(doc['_id'])
                docs.append(doc)
            
            logger.info(f"Fetched {len(docs)} documents from {collection_name}")
            return docs
        except Exception as e:
            logger.error(f"Failed to fetch MongoDB collection {collection_name}: {e}")
            raise
    
    def fetch_query(self, query: str) -> List[Dict]:
        """Execute custom SQL query.
        
        Args:
            query: SQL query string
        
        Returns:
            List of dictionaries (one per row)
        """
        if self.db_type == 'mongodb':
            raise NotImplementedError("Use fetch_table for MongoDB")
        
        try:
            import importlib
            sqlalchemy = importlib.import_module('sqlalchemy')
            text = getattr(sqlalchemy, 'text')
            
            result = self.conn.execute(text(query))
            rows = [dict(row) for row in result]
            
            logger.info(f"Query returned {len(rows)} rows")
            return rows
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise
    
    def fetch_incremental(self, table_name: str, timestamp_column: str,
                         last_sync_time: datetime) -> List[Dict]:
        """Fetch only new/updated records since last sync.
        
        Args:
            table_name: Table name
            timestamp_column: Column tracking update time
            last_sync_time: Last synchronization timestamp
        
        Returns:
            List of new/updated records
        """
        where_clause = f"{timestamp_column} > '{last_sync_time.isoformat()}'"
        return self.fetch_table(table_name, where_clause=where_clause)
    
    def close(self):
        """Close database connection."""
        if self.conn:
            try:
                if self.db_type == 'mongodb':
                    # MongoDB client close
                    self.conn.client.close()
                else:
                    self.conn.close()
                logger.info("Database connection closed")
            except Exception as e:
                logger.error(f"Error closing connection: {e}")
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


def ingest_from_database(db_config: Dict, table_name: str, 
                        limit: Optional[int] = None) -> List[Dict]:
    """Convenience function to ingest data from any database.
    
    Args:
        db_config: Database configuration dict
        table_name: Table/collection name
        limit: Optional row limit
    
    Returns:
        List of records as dictionaries
    
    Example:
        config = {
            'type': 'postgres',
            'host': 'localhost',
            'port': 5432,
            'database': 'mydb',
            'user': 'user',
            'password': 'pass'
        }
        data = ingest_from_database(config, 'orders', limit=1000)
    """
    with DatabaseIngestor(db_config) as ingestor:
        return ingestor.fetch_table(table_name, limit=limit)


if __name__ == '__main__':
    print("Database ingestion module")
    print("Supports: PostgreSQL, MySQL, MongoDB, SQLite, SQL Server")
    print("Use ingest_from_database() or DatabaseIngestor class")
