"""
Comprehensive unit tests for the conflict resolution system.

This module tests the conflict resolution manager, duplicate detection,
and resolution strategies for import operations.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import date, datetime

from app.services.conflict_resolution import (
    ConflictResolutionManager, DuplicateDetector, ConflictResolver,
    ConflictResolutionResult, DuplicateRecord, ConflictResolutionError
)
from app.models.import_export import (
    ConflictResolutionStrategy, ImportOptions, ImportExportValidationError,
    ImportErrorType
)


class TestConflictResolutionManager:
    """Test cases for ConflictResolutionManager class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.manager = ConflictResolutionManager()
    
    def test_initialization(self):
        """Test that the manager initializes correctly."""
        assert self.manager.detector is not None
        assert self.manager.resolver is not None
        assert isinstance(self.manager.detector, DuplicateDetector)
        assert isinstance(self.manager.resolver, ConflictResolver)
    
    def test_resolve_conflicts_skip_duplicates(self):
        """Test conflict resolution with skip duplicates strategy."""
        # Sample import records
        import_records = [
            {'id': 1, 'name': 'John Doe', 'email': 'john@example.com'},
            {'id': 2, 'name': 'Jane Smith', 'email': 'jane@example.com'},
            {'id': 3, 'name': 'Bob Wilson', 'email': 'bob@example.com'}
        ]
        
        # Mock existing records (simulate duplicates)
        existing_records = [
            {'id': 1, 'name': 'John Doe', 'email': 'john@example.com'},
            {'id': 4, 'name': 'Alice Brown', 'email': 'alice@example.com'}
        ]
        
        options = ImportOptions(
            entity_types=['persons'],
            conflict_resolution=ConflictResolutionStrategy.SKIP
        )
        
        with patch.object(self.manager.detector, '_get_existing_records', return_value=existing_records):
            result = self.manager.resolve_conflicts('persons', import_records, options)
        
        assert isinstance(result, ConflictResolutionResult)
        assert result.success == True
        assert len(result.records_to_create) == 2  # Jane and Bob (new records)
        assert len(result.records_to_update) == 0
        assert len(result.records_skipped) == 1  # John (duplicate)
        assert len(result.conflicts_detected) == 1
    
    def test_resolve_conflicts_update_existing(self):
        """Test conflict resolution with update existing strategy."""
        # Sample import records
        import_records = [
            {'id': 1, 'name': 'John Doe Updated', 'email': 'john.new@example.com'},
            {'id': 2, 'name': 'Jane Smith', 'email': 'jane@example.com'}
        ]
        
        # Mock existing records
        existing_records = [
            {'id': 1, 'name': 'John Doe', 'email': 'john@example.com'}
        ]
        
        options = ImportOptions(
            entity_types=['persons'],
            conflict_resolution=ConflictResolutionStrategy.UPDATE
        )
        
        with patch.object(self.manager.detector, '_get_existing_records', return_value=existing_records):
            result = self.manager.resolve_conflicts('persons', import_records, options)
        
        assert result.success == True
        assert len(result.records_to_create) == 1  # Jane (new record)
        assert len(result.records_to_update) == 1  # John (updated)
        assert len(result.records_skipped) == 0
        assert len(result.conflicts_detected) == 1
    
    def test_resolve_conflicts_create_version(self):
        """Test conflict resolution with create version strategy for assignments."""
        # Sample assignment records
        import_records = [
            {
                'person_id': 1,
                'unit_id': 1,
                'job_title_id': 1,
                'percentage': 0.8,
                'valid_from': '2024-01-01',
                'is_current': True
            }
        ]
        
        # Mock existing assignment
        existing_records = [
            {
                'id': 1,
                'person_id': 1,
                'unit_id': 1,
                'job_title_id': 1,
                'version': 1,
                'percentage': 1.0,
                'valid_from': '2023-01-01',
                'is_current': True
            }
        ]
        
        options = ImportOptions(
            entity_types=['assignments'],
            conflict_resolution=ConflictResolutionStrategy.CREATE_VERSION
        )
        
        with patch.object(self.manager.detector, '_get_existing_records', return_value=existing_records):
            result = self.manager.resolve_conflicts('assignments', import_records, options)
        
        assert result.success == True
        assert len(result.records_to_create) == 1  # New version
        assert len(result.records_to_update) == 1  # Update existing to not current
        assert len(result.conflicts_detected) == 1
    
    def test_resolve_conflicts_error_handling(self):
        """Test error handling in conflict resolution."""
        import_records = [{'id': 1, 'name': 'Test'}]
        
        options = ImportOptions(
            entity_types=['persons'],
            conflict_resolution=ConflictResolutionStrategy.SKIP
        )
        
        # Mock detector to raise an exception
        with patch.object(self.manager.detector, 'detect_duplicates', side_effect=Exception("Database error")):
            result = self.manager.resolve_conflicts('persons', import_records, options)
        
        assert result.success == False
        assert len(result.errors) > 0
        assert "Database error" in result.errors[0].message
    
    def test_get_conflict_statistics(self):
        """Test getting conflict resolution statistics."""
        # Create a result with various statistics
        result = ConflictResolutionResult(
            success=True,
            records_to_create=[{'id': 1}, {'id': 2}],
            records_to_update=[{'id': 3}],
            records_skipped=[{'id': 4}],
            conflicts_detected=[
                DuplicateRecord(
                    import_record={'id': 3},
                    existing_record={'id': 3},
                    match_fields=['id'],
                    confidence_score=1.0
                )
            ]
        )
        
        stats = self.manager.get_conflict_statistics(result)
        
        assert stats['total_records'] == 4
        assert stats['records_to_create'] == 2
        assert stats['records_to_update'] == 1
        assert stats['records_skipped'] == 1
        assert stats['conflicts_detected'] == 1
        assert stats['resolution_rate'] == 1.0  # All conflicts resolved


class TestDuplicateDetector:
    """Test cases for DuplicateDetector class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.detector = DuplicateDetector()
    
    def test_detect_duplicates_by_id(self):
        """Test duplicate detection by ID field."""
        import_records = [
            {'id': 1, 'name': 'John Doe'},
            {'id': 2, 'name': 'Jane Smith'},
            {'id': 3, 'name': 'Bob Wilson'}
        ]
        
        existing_records = [
            {'id': 1, 'name': 'John Doe'},
            {'id': 4, 'name': 'Alice Brown'}
        ]
        
        with patch.object(self.detector, '_get_existing_records', return_value=existing_records):
            duplicates = self.detector.detect_duplicates('persons', import_records)
        
        assert len(duplicates) == 1
        assert duplicates[0].import_record['id'] == 1
        assert duplicates[0].existing_record['id'] == 1
        assert 'id' in duplicates[0].match_fields
        assert duplicates[0].confidence_score == 1.0  # Exact ID match
    
    def test_detect_duplicates_by_name_email(self):
        """Test duplicate detection by name and email combination."""
        import_records = [
            {'name': 'John Doe', 'email': 'john@example.com'},
            {'name': 'Jane Smith', 'email': 'jane@example.com'}
        ]
        
        existing_records = [
            {'id': 1, 'name': 'John Doe', 'email': 'john@example.com'},
            {'id': 2, 'name': 'Bob Wilson', 'email': 'bob@example.com'}
        ]
        
        with patch.object(self.detector, '_get_existing_records', return_value=existing_records):
            duplicates = self.detector.detect_duplicates('persons', import_records)
        
        assert len(duplicates) == 1
        assert duplicates[0].import_record['name'] == 'John Doe'
        assert duplicates[0].existing_record['name'] == 'John Doe'
        assert 'name' in duplicates[0].match_fields
        assert 'email' in duplicates[0].match_fields
    
    def test_detect_duplicates_assignments(self):
        """Test duplicate detection for assignments (person + unit + job_title)."""
        import_records = [
            {
                'person_id': 1,
                'unit_id': 1,
                'job_title_id': 1,
                'valid_from': '2024-01-01'
            }
        ]
        
        existing_records = [
            {
                'id': 1,
                'person_id': 1,
                'unit_id': 1,
                'job_title_id': 1,
                'version': 1,
                'valid_from': '2023-01-01',
                'is_current': True
            }
        ]
        
        with patch.object(self.detector, '_get_existing_records', return_value=existing_records):
            duplicates = self.detector.detect_duplicates('assignments', import_records)
        
        assert len(duplicates) == 1
        assert duplicates[0].import_record['person_id'] == 1
        assert duplicates[0].existing_record['person_id'] == 1
        assert 'person_id' in duplicates[0].match_fields
        assert 'unit_id' in duplicates[0].match_fields
        assert 'job_title_id' in duplicates[0].match_fields
    
    def test_detect_duplicates_no_matches(self):
        """Test duplicate detection when no duplicates exist."""
        import_records = [
            {'id': 5, 'name': 'New Person', 'email': 'new@example.com'}
        ]
        
        existing_records = [
            {'id': 1, 'name': 'John Doe', 'email': 'john@example.com'}
        ]
        
        with patch.object(self.detector, '_get_existing_records', return_value=existing_records):
            duplicates = self.detector.detect_duplicates('persons', import_records)
        
        assert len(duplicates) == 0
    
    def test_calculate_confidence_score_exact_match(self):
        """Test confidence score calculation for exact matches."""
        import_record = {'id': 1, 'name': 'John Doe', 'email': 'john@example.com'}
        existing_record = {'id': 1, 'name': 'John Doe', 'email': 'john@example.com'}
        match_fields = ['id', 'name', 'email']
        
        score = self.detector._calculate_confidence_score(
            import_record, existing_record, match_fields
        )
        
        assert score == 1.0  # Perfect match
    
    def test_calculate_confidence_score_partial_match(self):
        """Test confidence score calculation for partial matches."""
        import_record = {'name': 'John Doe', 'email': 'john@example.com'}
        existing_record = {'name': 'John Doe', 'email': 'john.doe@example.com'}
        match_fields = ['name']  # Only name matches
        
        score = self.detector._calculate_confidence_score(
            import_record, existing_record, match_fields
        )
        
        assert 0.0 < score < 1.0  # Partial match
    
    def test_get_duplicate_detection_rules(self):
        """Test getting duplicate detection rules for entity types."""
        # Test persons rules
        person_rules = self.detector._get_duplicate_detection_rules('persons')
        assert len(person_rules) > 0
        assert any('id' in rule for rule in person_rules)
        assert any('email' in rule for rule in person_rules)
        
        # Test assignments rules
        assignment_rules = self.detector._get_duplicate_detection_rules('assignments')
        assert len(assignment_rules) > 0
        assert any(all(field in rule for field in ['person_id', 'unit_id', 'job_title_id']) 
                  for rule in assignment_rules)
    
    @patch('app.services.conflict_resolution.get_db_manager')
    def test_get_existing_records_database_call(self, mock_get_db):
        """Test that existing records are fetched from database correctly."""
        # Mock database manager and connection
        mock_db_manager = Mock()
        mock_connection = Mock()
        mock_cursor = Mock()
        
        mock_get_db.return_value = mock_db_manager
        mock_db_manager.get_connection.return_value = mock_connection
        mock_connection.cursor.return_value = mock_cursor
        
        # Mock query results
        mock_cursor.fetchall.return_value = [
            (1, 'John Doe', 'john@example.com'),
            (2, 'Jane Smith', 'jane@example.com')
        ]
        mock_cursor.description = [
            ('id',), ('name',), ('email',)
        ]
        
        # Call method
        records = self.detector._get_existing_records('persons')
        
        # Verify database interaction
        assert len(records) == 2
        assert records[0]['name'] == 'John Doe'
        assert records[1]['name'] == 'Jane Smith'
        mock_cursor.execute.assert_called_once()


class TestConflictResolver:
    """Test cases for ConflictResolver class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.resolver = ConflictResolver()
    
    def test_resolve_skip_duplicates(self):
        """Test resolving conflicts with skip duplicates strategy."""
        duplicates = [
            DuplicateRecord(
                import_record={'id': 1, 'name': 'John Doe'},
                existing_record={'id': 1, 'name': 'John Doe'},
                match_fields=['id'],
                confidence_score=1.0
            )
        ]
        
        import_records = [
            {'id': 1, 'name': 'John Doe'},
            {'id': 2, 'name': 'Jane Smith'}
        ]
        
        result = self.resolver.resolve_conflicts(
            'persons', import_records, duplicates, ConflictResolutionStrategy.SKIP
        )
        
        assert len(result.records_to_create) == 1  # Jane Smith
        assert len(result.records_skipped) == 1  # John Doe
        assert len(result.records_to_update) == 0
        assert result.records_to_create[0]['name'] == 'Jane Smith'
    
    def test_resolve_update_existing(self):
        """Test resolving conflicts with update existing strategy."""
        duplicates = [
            DuplicateRecord(
                import_record={'id': 1, 'name': 'John Doe Updated'},
                existing_record={'id': 1, 'name': 'John Doe'},
                match_fields=['id'],
                confidence_score=1.0
            )
        ]
        
        import_records = [
            {'id': 1, 'name': 'John Doe Updated'},
            {'id': 2, 'name': 'Jane Smith'}
        ]
        
        result = self.resolver.resolve_conflicts(
            'persons', import_records, duplicates, ConflictResolutionStrategy.UPDATE
        )
        
        assert len(result.records_to_create) == 1  # Jane Smith
        assert len(result.records_to_update) == 1  # John Doe Updated
        assert len(result.records_skipped) == 0
        assert result.records_to_update[0]['name'] == 'John Doe Updated'
    
    def test_resolve_create_version_assignments(self):
        """Test resolving conflicts with create version strategy for assignments."""
        duplicates = [
            DuplicateRecord(
                import_record={
                    'person_id': 1,
                    'unit_id': 1,
                    'job_title_id': 1,
                    'percentage': 0.8,
                    'valid_from': '2024-01-01'
                },
                existing_record={
                    'id': 1,
                    'person_id': 1,
                    'unit_id': 1,
                    'job_title_id': 1,
                    'version': 1,
                    'percentage': 1.0,
                    'valid_from': '2023-01-01',
                    'is_current': True
                },
                match_fields=['person_id', 'unit_id', 'job_title_id'],
                confidence_score=1.0
            )
        ]
        
        import_records = [
            {
                'person_id': 1,
                'unit_id': 1,
                'job_title_id': 1,
                'percentage': 0.8,
                'valid_from': '2024-01-01'
            }
        ]
        
        result = self.resolver.resolve_conflicts(
            'assignments', import_records, duplicates, ConflictResolutionStrategy.CREATE_VERSION
        )
        
        assert len(result.records_to_create) == 1  # New version
        assert len(result.records_to_update) == 1  # Update existing to not current
        assert len(result.records_skipped) == 0
        
        # Check that new version has incremented version number
        new_version = result.records_to_create[0]
        assert new_version.get('version', 2) == 2
        assert new_version.get('is_current', True) == True
        
        # Check that existing record is updated to not current
        updated_existing = result.records_to_update[0]
        assert updated_existing.get('is_current', False) == False
    
    def test_resolve_create_version_non_assignments(self):
        """Test that create version strategy falls back to update for non-assignment entities."""
        duplicates = [
            DuplicateRecord(
                import_record={'id': 1, 'name': 'Updated Unit'},
                existing_record={'id': 1, 'name': 'Original Unit'},
                match_fields=['id'],
                confidence_score=1.0
            )
        ]
        
        import_records = [{'id': 1, 'name': 'Updated Unit'}]
        
        result = self.resolver.resolve_conflicts(
            'units', import_records, duplicates, ConflictResolutionStrategy.CREATE_VERSION
        )
        
        # Should fall back to update existing for non-assignment entities
        assert len(result.records_to_update) == 1
        assert len(result.records_to_create) == 0
        assert len(result.records_skipped) == 0
    
    def test_prepare_assignment_version(self):
        """Test preparation of new assignment version."""
        import_record = {
            'person_id': 1,
            'unit_id': 1,
            'job_title_id': 1,
            'percentage': 0.8,
            'valid_from': '2024-01-01'
        }
        
        existing_record = {
            'id': 1,
            'person_id': 1,
            'unit_id': 1,
            'job_title_id': 1,
            'version': 1,
            'percentage': 1.0,
            'valid_from': '2023-01-01',
            'is_current': True
        }
        
        new_version, updated_existing = self.resolver._prepare_assignment_version(
            import_record, existing_record
        )
        
        # Check new version
        assert new_version['version'] == 2
        assert new_version['is_current'] == True
        assert new_version['percentage'] == 0.8
        assert new_version['valid_from'] == '2024-01-01'
        
        # Check updated existing
        assert updated_existing['id'] == 1
        assert updated_existing['is_current'] == False
        assert updated_existing['valid_to'] is not None


class TestDuplicateRecord:
    """Test cases for DuplicateRecord dataclass."""
    
    def test_duplicate_record_creation(self):
        """Test creating DuplicateRecord instances."""
        import_record = {'id': 1, 'name': 'Test'}
        existing_record = {'id': 1, 'name': 'Test'}
        match_fields = ['id', 'name']
        confidence_score = 1.0
        
        duplicate = DuplicateRecord(
            import_record=import_record,
            existing_record=existing_record,
            match_fields=match_fields,
            confidence_score=confidence_score
        )
        
        assert duplicate.import_record == import_record
        assert duplicate.existing_record == existing_record
        assert duplicate.match_fields == match_fields
        assert duplicate.confidence_score == confidence_score
    
    def test_duplicate_record_string_representation(self):
        """Test string representation of DuplicateRecord."""
        duplicate = DuplicateRecord(
            import_record={'id': 1, 'name': 'Test'},
            existing_record={'id': 1, 'name': 'Test'},
            match_fields=['id'],
            confidence_score=1.0
        )
        
        str_repr = str(duplicate)
        assert 'DuplicateRecord' in str_repr
        assert 'confidence_score=1.0' in str_repr


if __name__ == '__main__':
    pytest.main([__file__])