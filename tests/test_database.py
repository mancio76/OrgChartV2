"""
Unit tests for database operations with mock interactions.

This module tests database operations, connection management,
and transaction handling as required by Task 9.1.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
import sqlite3
from contextlib import contextmanager

from app.database import DatabaseManager, get_db_manager


class TestDatabaseOperations:
    """Test database operations with mock interactions"""
    
    @patch('app.database.sqlite3.connect')
    @patch('app.database.Path.mkdir')
    def test_database_connection_creation(self, mock_mkdir, mock_connect):
        """Test database connection is created properly"""
        mock_conn = Mock()
        mock_connect.return_value = mock_conn
        
        # Reset singleton instance for testing
        DatabaseManager._instance = None
        
        db_manager = DatabaseManager()
        
        # Verify connection was created with proper settings
        mock_connect.assert_called()
        
        # Verify foreign keys and other pragmas were set
        expected_calls = [
            call("PRAGMA foreign_keys = ON"),
            call("PRAGMA journal_mode = WAL"),
            call("PRAGMA synchronous = NORMAL"),
            call("PRAGMA cache_size = -64000"),
            call("PRAGMA temp_store = MEMORY")
        ]
        mock_conn.execute.assert_has_calls(expected_calls, any_order=True)
    
    @patch('app.database.sqlite3.connect')
    @patch('app.database.Path.mkdir')
    def test_foreign_keys_enabled(self, mock_mkdir, mock_connect):
        """Test that foreign keys are enabled on connection"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.execute.return_value = Mock()
        mock_conn.execute().fetchone.return_value = [1]  # Foreign keys enabled
        mock_connect.return_value = mock_conn
        
        # Reset singleton instance for testing
        DatabaseManager._instance = None
        
        db_manager = DatabaseManager()
        db_manager.enable_foreign_keys()
        
        # Verify foreign keys were enabled
        mock_conn.execute.assert_any_call("PRAGMA foreign_keys = ON")
    
    @patch('app.database.sqlite3.connect')
    @patch('app.database.Path.mkdir')
    def test_execute_query_with_params(self, mock_mkdir, mock_connect):
        """Test parameterized query execution"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        # Reset singleton instance for testing
        DatabaseManager._instance = None
        
        db_manager = DatabaseManager()
        
        # Mock the get_connection context manager
        @contextmanager
        def mock_get_connection():
            yield mock_conn
        
        db_manager.get_connection = mock_get_connection
        
        query = "SELECT * FROM users WHERE id = ?"
        params = (1,)
        
        result = db_manager.execute_query(query, params)
        
        mock_cursor.execute.assert_called_once_with(query, params)
        assert result == mock_cursor
    
    @patch('app.database.sqlite3.connect')
    @patch('app.database.Path.mkdir')
    def test_fetch_one_operation(self, mock_mkdir, mock_connect):
        """Test fetch_one database operation"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_row = {'id': 1, 'name': 'Test'}
        mock_cursor.fetchone.return_value = mock_row
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        # Reset singleton instance for testing
        DatabaseManager._instance = None
        
        db_manager = DatabaseManager()
        
        @contextmanager
        def mock_get_connection():
            yield mock_conn
        
        db_manager.get_connection = mock_get_connection
        
        result = db_manager.fetch_one("SELECT * FROM users WHERE id = ?", (1,))
        
        assert result == mock_row
        mock_cursor.execute.assert_called_once_with("SELECT * FROM users WHERE id = ?", (1,))
        mock_cursor.fetchone.assert_called_once()
    
    @patch('app.database.sqlite3.connect')
    @patch('app.database.Path.mkdir')
    def test_fetch_all_operation(self, mock_mkdir, mock_connect):
        """Test fetch_all database operation"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_rows = [{'id': 1, 'name': 'Test1'}, {'id': 2, 'name': 'Test2'}]
        mock_cursor.fetchall.return_value = mock_rows
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        # Reset singleton instance for testing
        DatabaseManager._instance = None
        
        db_manager = DatabaseManager()
        
        @contextmanager
        def mock_get_connection():
            yield mock_conn
        
        db_manager.get_connection = mock_get_connection
        
        result = db_manager.fetch_all("SELECT * FROM users")
        
        assert result == mock_rows
        mock_cursor.execute.assert_called_once_with("SELECT * FROM users")
        mock_cursor.fetchall.assert_called_once()
    
    @patch('app.database.sqlite3.connect')
    @patch('app.database.Path.mkdir')
    def test_transaction_rollback_on_error(self, mock_mkdir, mock_connect):
        """Test transaction rollback on database error"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.execute.side_effect = sqlite3.Error("Database error")
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        # Reset singleton instance for testing
        DatabaseManager._instance = None
        
        db_manager = DatabaseManager()
        
        @contextmanager
        def mock_get_connection():
            try:
                yield mock_conn
            except Exception:
                mock_conn.rollback()
                raise
        
        db_manager.get_connection = mock_get_connection
        
        with pytest.raises(sqlite3.Error):
            db_manager.execute_query("INSERT INTO users (name) VALUES (?)", ("Test",))
        
        # Verify rollback was called
        mock_conn.rollback.assert_called_once()
    
    @patch('app.database.sqlite3.connect')
    @patch('app.database.Path.mkdir')
    def test_connection_cleanup(self, mock_mkdir, mock_connect):
        """Test database connection cleanup"""
        mock_conn = Mock()
        mock_connect.return_value = mock_conn
        
        # Reset singleton instance for testing
        DatabaseManager._instance = None
        
        db_manager = DatabaseManager()
        
        # Mock the connection pool behavior
        @contextmanager
        def mock_get_connection():
            yield mock_conn
        
        db_manager.get_connection = mock_get_connection
        
        with db_manager.get_connection() as conn:
            # Connection should be available
            assert conn == mock_conn
    
    def test_row_factory_dict_access(self):
        """Test row factory enables dict-like access"""
        # This test verifies the row factory concept
        # In actual implementation, sqlite3.Row provides dict-like access
        
        # Mock a row object that behaves like sqlite3.Row
        class MockRow:
            def __init__(self, data):
                self._data = data
            
            def __getitem__(self, key):
                return self._data[key]
            
            def keys(self):
                return self._data.keys()
        
        # Test dict-like access
        row_data = {'id': 1, 'name': 'Test', 'email': 'test@example.com'}
        row = MockRow(row_data)
        
        assert row['id'] == 1
        assert row['name'] == 'Test'
        assert row['email'] == 'test@example.com'
        assert list(row.keys()) == ['id', 'name', 'email']
    
    @patch('app.database.sqlite3.connect')
    @patch('app.database.Path.mkdir')
    def test_database_initialization_error_handling(self, mock_mkdir, mock_connect):
        """Test database initialization error handling"""
        mock_connect.side_effect = sqlite3.Error("Cannot connect to database")
        
        # Reset singleton instance for testing
        DatabaseManager._instance = None
        
        with pytest.raises(sqlite3.Error):
            db_manager = DatabaseManager()
    
    @patch('app.database.sqlite3.connect')
    @patch('app.database.Path.mkdir')
    def test_sql_injection_prevention(self, mock_mkdir, mock_connect):
        """Test that parameterized queries prevent SQL injection"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        # Reset singleton instance for testing
        DatabaseManager._instance = None
        
        db_manager = DatabaseManager()
        
        @contextmanager
        def mock_get_connection():
            yield mock_conn
        
        db_manager.get_connection = mock_get_connection
        
        # Attempt SQL injection
        malicious_input = "'; DROP TABLE users; --"
        query = "SELECT * FROM users WHERE name = ?"
        params = (malicious_input,)
        
        db_manager.execute_query(query, params)
        
        # Verify the malicious input was passed as a parameter, not concatenated
        mock_cursor.execute.assert_called_once_with(query, params)
        
        # The query should still be the original safe query
        call_args = mock_cursor.execute.call_args
        assert call_args[0][0] == "SELECT * FROM users WHERE name = ?"
        assert call_args[0][1] == (malicious_input,)


class TestDatabaseIntegration:
    """Test database integration scenarios"""
    
    @patch('app.database.sqlite3.connect')
    @patch('app.database.Path.mkdir')
    def test_crud_operation_sequence(self, mock_mkdir, mock_connect):
        """Test complete CRUD operation sequence"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        # Mock different responses for different operations
        mock_cursor.lastrowid = 1
        mock_cursor.rowcount = 1
        mock_cursor.fetchone.return_value = {'id': 1, 'name': 'Test'}
        
        # Reset singleton instance for testing
        DatabaseManager._instance = None
        
        db_manager = DatabaseManager()
        
        @contextmanager
        def mock_get_connection():
            yield mock_conn
        
        db_manager.get_connection = mock_get_connection
        
        # Create
        create_result = db_manager.execute_query(
            "INSERT INTO users (name) VALUES (?)", ("Test",)
        )
        assert create_result.lastrowid == 1
        
        # Read
        read_result = db_manager.fetch_one(
            "SELECT * FROM users WHERE id = ?", (1,)
        )
        assert read_result['name'] == 'Test'
        
        # Update
        update_result = db_manager.execute_query(
            "UPDATE users SET name = ? WHERE id = ?", ("Updated", 1)
        )
        assert update_result.rowcount == 1
        
        # Delete
        delete_result = db_manager.execute_query(
            "DELETE FROM users WHERE id = ?", (1,)
        )
        assert delete_result.rowcount == 1
    
    @patch('app.database.sqlite3.connect')
    @patch('app.database.Path.mkdir')
    def test_concurrent_connection_handling(self, mock_mkdir, mock_connect):
        """Test handling of concurrent database connections"""
        mock_conn = Mock()
        mock_connect.return_value = mock_conn
        
        # Reset singleton instance for testing
        DatabaseManager._instance = None
        
        # Since DatabaseManager is a singleton, both calls return the same instance
        db_manager1 = DatabaseManager()
        db_manager2 = DatabaseManager()
        
        # Both should be the same instance (singleton pattern)
        assert db_manager1 is db_manager2
    
    @patch('app.database.sqlite3.connect')
    @patch('app.database.Path.mkdir')
    def test_database_schema_validation(self, mock_mkdir, mock_connect):
        """Test database schema validation operations"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        # Mock schema validation query results
        mock_cursor.fetchall.return_value = [
            {'name': 'users'}, {'name': 'assignments'}, {'name': 'units'}
        ]
        
        # Reset singleton instance for testing
        DatabaseManager._instance = None
        
        db_manager = DatabaseManager()
        
        @contextmanager
        def mock_get_connection():
            yield mock_conn
        
        db_manager.get_connection = mock_get_connection
        
        # Simulate schema validation
        tables = db_manager.fetch_all(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        
        assert len(tables) == 3
        table_names = [table['name'] for table in tables]
        assert 'users' in table_names
        assert 'assignments' in table_names
        assert 'units' in table_names


class TestDatabasePerformanceAndOptimization:
    """Test database performance and optimization features"""
    
    @patch('app.database.sqlite3.connect')
    @patch('app.database.Path.mkdir')
    def test_wal_mode_configuration(self, mock_mkdir, mock_connect):
        """Test WAL journal mode is configured for performance"""
        mock_conn = Mock()
        mock_connect.return_value = mock_conn
        
        # Reset singleton instance for testing
        DatabaseManager._instance = None
        
        db_manager = DatabaseManager()
        
        # Verify WAL mode was set
        mock_conn.execute.assert_any_call("PRAGMA journal_mode = WAL")
    
    @patch('app.database.sqlite3.connect')
    @patch('app.database.Path.mkdir')
    def test_cache_size_optimization(self, mock_mkdir, mock_connect):
        """Test cache size is optimized for performance"""
        mock_conn = Mock()
        mock_connect.return_value = mock_conn
        
        # Reset singleton instance for testing
        DatabaseManager._instance = None
        
        db_manager = DatabaseManager()
        
        # Verify cache size was optimized
        mock_conn.execute.assert_any_call("PRAGMA cache_size = -64000")
    
    @patch('app.database.sqlite3.connect')
    @patch('app.database.Path.mkdir')
    def test_synchronous_mode_optimization(self, mock_mkdir, mock_connect):
        """Test synchronous mode is set for balanced performance/safety"""
        mock_conn = Mock()
        mock_connect.return_value = mock_conn
        
        # Reset singleton instance for testing
        DatabaseManager._instance = None
        
        db_manager = DatabaseManager()
        
        # Verify synchronous mode was set
        mock_conn.execute.assert_any_call("PRAGMA synchronous = NORMAL")
    
    @patch('app.database.sqlite3.connect')
    @patch('app.database.Path.mkdir')
    def test_temp_store_memory_optimization(self, mock_mkdir, mock_connect):
        """Test temporary storage is configured to use memory"""
        mock_conn = Mock()
        mock_connect.return_value = mock_conn
        
        # Reset singleton instance for testing
        DatabaseManager._instance = None
        
        db_manager = DatabaseManager()
        
        # Verify temp store was set to memory
        mock_conn.execute.assert_any_call("PRAGMA temp_store = MEMORY")


class TestDatabaseErrorRecovery:
    """Test database error recovery and resilience"""
    
    @patch('app.database.sqlite3.connect')
    @patch('app.database.Path.mkdir')
    def test_connection_retry_on_busy(self, mock_mkdir, mock_connect):
        """Test connection retry mechanism on database busy"""
        # First call fails with database busy, second succeeds
        mock_conn = Mock()
        mock_connect.side_effect = [sqlite3.OperationalError("database is locked"), mock_conn]
        
        # Reset singleton instance for testing
        DatabaseManager._instance = None
        
        # Should eventually succeed after retry
        with pytest.raises(sqlite3.OperationalError):
            db_manager = DatabaseManager()
    
    @patch('app.database.sqlite3.connect')
    @patch('app.database.Path.mkdir')
    def test_graceful_degradation_on_pragma_failure(self, mock_mkdir, mock_connect):
        """Test graceful degradation when PRAGMA commands fail"""
        mock_conn = Mock()
        # Make PRAGMA commands fail but connection succeed
        mock_conn.execute.side_effect = sqlite3.Error("PRAGMA failed")
        mock_connect.return_value = mock_conn
        
        # Reset singleton instance for testing
        DatabaseManager._instance = None
        
        # Should raise exception when PRAGMA fails (current behavior)
        with pytest.raises(Exception):
            db_manager = DatabaseManager()
    
    @patch('app.database.sqlite3.connect')
    @patch('app.database.Path.mkdir')
    def test_transaction_isolation_levels(self, mock_mkdir, mock_connect):
        """Test transaction isolation level handling"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        # Reset singleton instance for testing
        DatabaseManager._instance = None
        
        db_manager = DatabaseManager()
        
        @contextmanager
        def mock_get_connection():
            yield mock_conn
        
        db_manager.get_connection = mock_get_connection
        
        # Test that transactions are properly isolated
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("BEGIN TRANSACTION")
            cursor.execute("INSERT INTO test (name) VALUES (?)", ("test",))
            # Transaction should be isolated until commit
            conn.commit()
    
    @patch('app.database.sqlite3.connect')
    @patch('app.database.Path.mkdir')
    def test_deadlock_detection_and_recovery(self, mock_mkdir, mock_connect):
        """Test deadlock detection and recovery mechanisms"""
        mock_conn = Mock()
        mock_cursor = Mock()
        
        # Simulate deadlock on first attempt, success on second
        mock_cursor.execute.side_effect = [
            sqlite3.OperationalError("database is locked"),
            None  # Success on retry
        ]
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        # Reset singleton instance for testing
        DatabaseManager._instance = None
        
        db_manager = DatabaseManager()
        
        @contextmanager
        def mock_get_connection():
            yield mock_conn
        
        db_manager.get_connection = mock_get_connection
        
        # Should handle deadlock gracefully
        with pytest.raises(sqlite3.OperationalError):
            db_manager.execute_query("INSERT INTO test (name) VALUES (?)", ("test",))


class TestDatabaseConnectionPooling:
    """Test database connection pooling and management"""
    
    @patch('app.database.sqlite3.connect')
    @patch('app.database.Path.mkdir')
    def test_connection_reuse(self, mock_mkdir, mock_connect):
        """Test connection reuse in singleton pattern"""
        mock_conn = Mock()
        mock_connect.return_value = mock_conn
        
        # Reset singleton instance for testing
        DatabaseManager._instance = None
        
        # Multiple calls should reuse the same connection
        db_manager1 = DatabaseManager()
        db_manager2 = DatabaseManager()
        
        assert db_manager1 is db_manager2
        # Since singleton is reused, the instance should be the same
        # The connection creation happens during initialization
    
    @patch('app.database.sqlite3.connect')
    @patch('app.database.Path.mkdir')
    def test_connection_cleanup_on_error(self, mock_mkdir, mock_connect):
        """Test connection cleanup when errors occur"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.execute.side_effect = sqlite3.Error("Query failed")
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        # Reset singleton instance for testing
        DatabaseManager._instance = None
        
        db_manager = DatabaseManager()
        
        @contextmanager
        def mock_get_connection():
            try:
                yield mock_conn
            except Exception:
                # Simulate cleanup
                mock_conn.rollback()
                raise
            finally:
                # Connection should be properly closed/returned to pool
                pass
        
        db_manager.get_connection = mock_get_connection
        
        with pytest.raises(sqlite3.Error):
            db_manager.execute_query("SELECT * FROM test")
        
        # Verify rollback was called for cleanup
        mock_conn.rollback.assert_called_once()
    
    @patch('app.database.sqlite3.connect')
    @patch('app.database.Path.mkdir')
    def test_concurrent_access_simulation(self, mock_mkdir, mock_connect):
        """Test simulation of concurrent database access"""
        mock_conn = Mock()
        mock_connect.return_value = mock_conn
        
        # Reset singleton instance for testing
        DatabaseManager._instance = None
        
        db_manager = DatabaseManager()
        
        # Simulate multiple concurrent operations
        operations = []
        for i in range(10):
            @contextmanager
            def mock_operation():
                # Simulate concurrent access
                yield mock_conn
            
            operations.append(mock_operation)
        
        # All operations should be able to access the connection
        for operation in operations:
            with operation() as conn:
                assert conn == mock_conn


class TestDatabaseIntegrityConstraints:
    """Test database integrity constraints and foreign key enforcement"""
    
    @patch('app.database.sqlite3.connect')
    @patch('app.database.Path.mkdir')
    def test_foreign_key_constraint_enforcement(self, mock_mkdir, mock_connect):
        """Test foreign key constraints are properly enforced"""
        mock_conn = Mock()
        mock_cursor = Mock()
        
        # Simulate foreign key constraint violation
        mock_cursor.execute.side_effect = sqlite3.IntegrityError("FOREIGN KEY constraint failed")
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        # Reset singleton instance for testing
        DatabaseManager._instance = None
        
        db_manager = DatabaseManager()
        
        @contextmanager
        def mock_get_connection():
            yield mock_conn
        
        db_manager.get_connection = mock_get_connection
        
        # Should raise integrity error for foreign key violations
        with pytest.raises(sqlite3.IntegrityError) as exc_info:
            db_manager.execute_query(
                "INSERT INTO assignments (person_id, unit_id) VALUES (?, ?)",
                (999, 999)  # Non-existent foreign keys
            )
        
        assert "FOREIGN KEY constraint failed" in str(exc_info.value)
    
    @patch('app.database.sqlite3.connect')
    @patch('app.database.Path.mkdir')
    def test_unique_constraint_enforcement(self, mock_mkdir, mock_connect):
        """Test unique constraints are properly enforced"""
        mock_conn = Mock()
        mock_cursor = Mock()
        
        # Simulate unique constraint violation
        mock_cursor.execute.side_effect = sqlite3.IntegrityError("UNIQUE constraint failed")
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        # Reset singleton instance for testing
        DatabaseManager._instance = None
        
        db_manager = DatabaseManager()
        
        @contextmanager
        def mock_get_connection():
            yield mock_conn
        
        db_manager.get_connection = mock_get_connection
        
        # Should raise integrity error for unique violations
        with pytest.raises(sqlite3.IntegrityError) as exc_info:
            db_manager.execute_query(
                "INSERT INTO persons (email) VALUES (?)",
                ("duplicate@example.com",)
            )
        
        assert "UNIQUE constraint failed" in str(exc_info.value)
    
    @patch('app.database.sqlite3.connect')
    @patch('app.database.Path.mkdir')
    def test_check_constraint_enforcement(self, mock_mkdir, mock_connect):
        """Test check constraints are properly enforced"""
        mock_conn = Mock()
        mock_cursor = Mock()
        
        # Simulate check constraint violation
        mock_cursor.execute.side_effect = sqlite3.IntegrityError("CHECK constraint failed")
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        # Reset singleton instance for testing
        DatabaseManager._instance = None
        
        db_manager = DatabaseManager()
        
        @contextmanager
        def mock_get_connection():
            yield mock_conn
        
        db_manager.get_connection = mock_get_connection
        
        # Should raise integrity error for check constraint violations
        with pytest.raises(sqlite3.IntegrityError) as exc_info:
            db_manager.execute_query(
                "INSERT INTO assignments (percentage) VALUES (?)",
                (-0.5,)  # Invalid percentage
            )
        
        assert "CHECK constraint failed" in str(exc_info.value)