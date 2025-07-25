"""
Test configuration and fixtures for the Organigramma Web App test suite.
"""

import pytest
import tempfile
import os
from unittest.mock import patch, Mock
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Import routes directly for test app
from app.routes import api, health


@pytest.fixture
def test_app():
    """Create a test FastAPI app without security middleware"""
    app = FastAPI(title="Test Organigramma App")
    
    # Include only the routes we need for testing
    app.include_router(health.router, tags=["Health"])
    app.include_router(api.router, prefix="/api", tags=["API"])
    
    return app


@pytest.fixture
def client(test_app):
    """FastAPI test client fixture using test app without security middleware"""
    return TestClient(test_app)


@pytest.fixture
def mock_db_manager():
    """Mock database manager for testing"""
    with patch('app.database.DatabaseManager') as mock_db_class:
        mock_instance = Mock()
        mock_db_class.return_value = mock_instance
        mock_db_class._instance = mock_instance
        
        # Setup default responses
        mock_instance.fetch_all.return_value = []
        mock_instance.fetch_one.return_value = None
        mock_instance.execute_query.return_value = Mock(lastrowid=1, rowcount=1)
        
        yield mock_instance


@pytest.fixture
def temp_database():
    """Create a temporary database for testing"""
    temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    temp_db.close()
    
    yield temp_db.name
    
    # Cleanup
    try:
        os.unlink(temp_db.name)
    except OSError:
        pass