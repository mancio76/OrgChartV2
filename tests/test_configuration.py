"""
Test configuration and fixtures for the Organigramma Web App test suite.

This module provides pytest fixtures for database setup, test clients,
and common test data as required by the testing strategy.
"""

import pytest
import tempfile
import os
from datetime import date, datetime
from unittest.mock import Mock, MagicMock
from typing import Dict, Any, List

from app.database import DatabaseManager
from app.models.base import BaseModel, Alias
from app.models.unit_type import UnitType
from app.models.unit import Unit
from app.models.person import Person
from app.models.job_title import JobTitle
from app.models.assignment import Assignment


@pytest.fixture
def temp_db_path():
    """Create temporary database file path for testing"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    yield db_path
    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def mock_db_manager():
    """Mock database manager for unit tests"""
    mock_manager = Mock(spec=DatabaseManager)
    
    # Mock common methods
    mock_manager.fetch_all.return_value = []
    mock_manager.fetch_one.return_value = None
    mock_manager.execute_query.return_value = Mock(lastrowid=1, rowcount=1)
    mock_manager.get_connection.return_value = Mock()
    
    return mock_manager


@pytest.fixture
def sample_unit_type():
    """Sample UnitType for testing"""
    return UnitType(
        id=1,
        name="Function",
        short_name="FUNC",
        aliases=[Alias("Funzione", "it-IT")],
        level=1
    )


@pytest.fixture
def sample_unit():
    """Sample Unit for testing"""
    return Unit(
        id=1,
        name="IT Department",
        short_name="IT",
        unit_type_id=1,
        parent_unit_id=None,
        start_date=date(2023, 1, 1),
        aliases=[Alias("Dipartimento IT", "it-IT")]
    )


@pytest.fixture
def sample_person():
    """Sample Person for testing"""
    return Person(
        id=1,
        name="Mario Rossi",
        short_name="M. Rossi",
        email="mario.rossi@example.com"
    )


@pytest.fixture
def sample_job_title():
    """Sample JobTitle for testing"""
    return JobTitle(
        id=1,
        name="Software Engineer",
        short_name="SW Eng",
        aliases=[Alias("Ingegnere Software", "it-IT")]
    )


@pytest.fixture
def sample_assignment():
    """Sample Assignment for testing"""
    return Assignment(
        id=1,
        person_id=1,
        unit_id=1,
        job_title_id=1,
        version=1,
        percentage=1.0,
        is_ad_interim=False,
        is_unit_boss=False,
        valid_from=date(2023, 1, 1),
        is_current=True
    )


@pytest.fixture
def sample_sqlite_row():
    """Sample SQLite row data for testing from_sqlite_row methods"""
    class MockRow:
        def __init__(self, data: Dict[str, Any]):
            self._data = data
        
        def __getitem__(self, key):
            return self._data[key]
        
        def __contains__(self, key):
            return key in self._data
        
        def get(self, key, default=None):
            return self._data.get(key, default)
        
        def keys(self):
            return self._data.keys()
        
        def values(self):
            return self._data.values()
        
        def items(self):
            return self._data.items()
        
        def __iter__(self):
            return iter(self._data)
    
    return MockRow


@pytest.fixture
def unit_type_row_data():
    """Sample UnitType row data"""
    return {
        'id': 1,
        'name': 'Function',
        'short_name': 'FUNC',
        'aliases': '[{"value": "Funzione", "lang": "it-IT"}]',
        'level': 1,
        'datetime_created': '2023-01-01T10:00:00',
        'datetime_updated': '2023-01-01T10:00:00',
        'units_count': 5
    }


@pytest.fixture
def unit_row_data():
    """Sample Unit row data"""
    return {
        'id': 1,
        'name': 'IT Department',
        'short_name': 'IT',
        'unit_type_id': 1,
        'parent_unit_id': None,
        'start_date': '2023-01-01',
        'end_date': None,
        'aliases': '[{"value": "Dipartimento IT", "lang": "it-IT"}]',
        'datetime_created': '2023-01-01T10:00:00',
        'datetime_updated': '2023-01-01T10:00:00',
        'parent_name': None,
        'children_count': 3,
        'person_count': 10,
        'level': 0,
        'path': '/IT Department',
        'full_path': 'IT Department'
    }


@pytest.fixture
def person_row_data():
    """Sample Person row data"""
    return {
        'id': 1,
        'name': 'Mario Rossi',
        'short_name': 'M. Rossi',
        'email': 'mario.rossi@example.com',
        'datetime_created': '2023-01-01T10:00:00',
        'datetime_updated': '2023-01-01T10:00:00',
        'current_assignments_count': 2,
        'total_assignments_count': 5
    }


@pytest.fixture
def job_title_row_data():
    """Sample JobTitle row data"""
    return {
        'id': 1,
        'name': 'Software Engineer',
        'short_name': 'SW Eng',
        'aliases': '[{"value": "Ingegnere Software", "lang": "it-IT"}]',
        'start_date': '2023-01-01',
        'end_date': None,
        'datetime_created': '2023-01-01T10:00:00',
        'datetime_updated': '2023-01-01T10:00:00',
        'current_assignments_count': 3,
        'total_assignments_count': 8
    }


@pytest.fixture
def assignment_row_data():
    """Sample Assignment row data"""
    return {
        'id': 1,
        'person_id': 1,
        'unit_id': 1,
        'job_title_id': 1,
        'version': 1,
        'percentage': 1.0,
        'is_ad_interim': 0,
        'is_unit_boss': 0,
        'notes': None,
        'flags': None,
        'valid_from': '2023-01-01',
        'valid_to': None,
        'is_current': 1,
        'datetime_created': '2023-01-01T10:00:00',
        'datetime_updated': '2023-01-01T10:00:00',
        'person_name': 'Mario Rossi',
        'person_short_name': 'M. Rossi',
        'unit_name': 'IT Department',
        'unit_short_name': 'IT',
        'job_title_name': 'Software Engineer',
        'job_title_short_name': 'SW Eng'
    }


@pytest.fixture
def validation_error_cases():
    """Common validation error test cases"""
    return {
        'empty_name': {
            'field': 'name',
            'message': 'Name is required',
            'test_values': ['', '   ', None]
        },
        'invalid_email': {
            'field': 'email',
            'message': 'Invalid email format',
            'test_values': ['invalid-email', '@domain.com', 'user@', 'user@domain']
        },
        'invalid_percentage': {
            'field': 'percentage',
            'message': 'Percentage must be between 0 and 100%',
            'test_values': [-0.1, 0.0, 1.1, 2.0]
        },
        'invalid_date_range': {
            'field': 'valid_to',
            'message': 'End date must be after start date',
            'test_data': {
                'valid_from': date(2023, 6, 1),
                'valid_to': date(2023, 1, 1)
            }
        }
    }


# Test data factories for creating test instances

class TestDataFactory:
    """Factory for creating test data instances"""
    
    @staticmethod
    def create_unit_type(**kwargs) -> UnitType:
        """Create UnitType with default values"""
        defaults = {
            'name': 'Test Unit Type',
            'short_name': 'TEST',
            'aliases': [Alias('Tipo Test', 'it-IT')],
            'level': 1
        }
        defaults.update(kwargs)
        return UnitType(**defaults)
    
    @staticmethod
    def create_unit(**kwargs) -> Unit:
        """Create Unit with default values"""
        defaults = {
            'name': 'Test Unit',
            'short_name': 'TEST',
            'unit_type_id': 1,
            'start_date': date(2023, 1, 1),
            'aliases': [Alias('Unità Test', 'it-IT')]
        }
        defaults.update(kwargs)
        return Unit(**defaults)
    
    @staticmethod
    def create_person(**kwargs) -> Person:
        """Create Person with default values"""
        defaults = {
            'name': 'Test Person',
            'short_name': 'T. Person',
            'email': 'test@example.com'
        }
        defaults.update(kwargs)
        return Person(**defaults)
    
    @staticmethod
    def create_job_title(**kwargs) -> JobTitle:
        """Create JobTitle with default values"""
        defaults = {
            'name': 'Test Job Title',
            'short_name': 'TEST',
            'aliases': [Alias('Titolo Test', 'it-IT')]
        }
        defaults.update(kwargs)
        return JobTitle(**defaults)
    
    @staticmethod
    def create_assignment(**kwargs) -> Assignment:
        """Create Assignment with default values"""
        defaults = {
            'person_id': 1,
            'unit_id': 1,
            'job_title_id': 1,
            'version': 1,
            'percentage': 1.0,
            'valid_from': date(2023, 1, 1),
            'is_current': True
        }
        defaults.update(kwargs)
        return Assignment(**defaults)


@pytest.fixture
def test_data_factory():
    """Test data factory fixture"""
    return TestDataFactory