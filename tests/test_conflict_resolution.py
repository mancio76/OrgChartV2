"""
Tests for the conflict resolution system.

This module tests conflict detection and resolution strategies
for handling duplicate records during import operations.
"""

import pytest
from unittest.mock import Mock, patch
from app.services.conflict_resolution import (
    ConflictDetector, ConflictResolver, ConflictResolutionManager,
    ConflictInfo, ConflictType, ConflictResolutionResult
)
from app.models.import_export import ConflictResolutionStrategy, ImportExportValidationError, ImportErrorType


class TestConflictDetector:
    """Test cases for the ConflictDetector class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.detector = ConflictDetector()
    
    def test_initialization(self):
        """Test that the conflict detector initializes correctly."""
        assert self.detector is not None
        assert len(self.detector.unique_field_combinations) > 0
        
        # Check that all expected entity types have unique field combinations
        expected_entities = ['unit_types', 'unit_type_themes', 'units', 'job_titles', 'persons', 'assignments']
        for entity_type in expected_entities:
            assert entity_type in self.detector.unique_field_combinations
    
    @patch('app.services.conflict_resolution.ConflictDetector._get_existing_records')
    def test_detect_database_conflicts(self, mock_get_existing):
        """Test detection of conflicts with existing database records."""
        # Mock existing records
        mock_get_existing.return_value = [
            {'id': 1, 'name': 'Existing Unit Type', 'short_name': 'EUT'},
            {'id': 2, 'name': 'Another Unit Type', 'short_name': 'AUT'}
        ]
        
        # New records with conflicts
        new_records = [
            {'id': 3, 'name': 'New Unit Type', 'short_name': 'NUT'},  # No conflict
            {'id': 1, 'name': 'Conflicting Unit Type', 'short_name': 'CUT'},  # ID conflict
            {'id': 4, 'name': 'Existing Unit Type', 'short_name': 'EUT2'}  # Name conflict
        ]
        
        conflicts = self.detector.detect_conflicts('unit_types', new_records)
        
        # Should detect 2 conflicts
        assert len(conflicts) >= 2
        
        # Check for ID conflict
        id_conflicts = [c for c in conflicts if c.conflict_type == ConflictType.DUPLICATE_PRIMARY_KEY]
        assert len(id_conflicts) == 1
        assert id_conflicts[0].conflicting_value == 1
        
        # Check for name conflict
        name_conflicts = [c for c in conflicts if c.conflict_type == ConflictType.DUPLICATE_UNIQUE_FIELD and 'name' in c.field_name]
        assert len(name_conflicts) == 1
        assert name_conflicts[0].conflicting_value == ('Existing Unit Type',)
    
    def test_detect_batch_conflicts(self):
        """Test detection of conflicts within the import batch."""
        # Records with internal conflicts
        records = [
            {'id': 1, 'name': 'Unit Type 1', 'short_name': 'UT1'},
            {'id': 2, 'name': 'Unit Type 2', 'short_name': 'UT2'},
            {'id': 3, 'name': 'Unit Type 1', 'short_name': 'UT3'},  # Name conflict with record 1
            {'id': 4, 'name': 'Unit Type 4', 'short_name': 'UT1'}   # Short name conflict with record 1
        ]
        
        conflicts = self.detector._detect_batch_conflicts('unit_types', records)
        
        # Should detect 2 conflicts
        assert len(conflicts) == 2
        
        # All should be business key conflicts
        for conflict in conflicts:
            assert conflict.conflict_type == ConflictType.DUPLICATE_BUSINESS_KEY
    
    def test_suggest_resolution_strategy(self):
        """Test resolution strategy suggestions."""
        # For assignments, should suggest create version
        strategy = self.detector._suggest_resolution_strategy('assignments', ['person_id', 'unit_id'])
        assert strategy == ConflictResolutionStrategy.CREATE_VERSION
        
        # For name conflicts, should suggest update
        strategy = self.detector._suggest_resolution_strategy('unit_types', ['name'])
        assert strategy == ConflictResolutionStrategy.UPDATE
        
        # For other fields, should suggest skip
        strategy = self.detector._suggest_resolution_strategy('unit_types', ['level'])
        assert strategy == ConflictResolutionStrategy.SKIP


class TestConflictResolver:
    """Test cases for the ConflictResolver class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.resolver = ConflictResolver()
    
    def test_initialization(self):
        """Test that the conflict resolver initializes correctly."""
        assert self.resolver is not None
    
    def test_resolve_skip(self):
        """Test skip resolution strategy."""
        conflict = ConflictInfo(
            conflict_type=ConflictType.DUPLICATE_UNIQUE_FIELD,
            entity_type='unit_types',
            field_name='name',
            conflicting_value='Test Unit',
            existing_record={'id': 1, 'name': 'Test Unit'},
            new_record={'id': 2, 'name': 'Test Unit'},
            line_number=2
        )
        
        result = self.resolver._resolve_skip(conflict)
        
        assert result.resolved is True
        assert result.action_taken == 'skipped'
        assert result.skipped is True
        assert len(result.warnings) == 1
        assert result.warnings[0].error_type == ImportErrorType.DUPLICATE_RECORD
    
    def test_resolve_update(self):
        """Test update resolution strategy."""
        conflict = ConflictInfo(
            conflict_type=ConflictType.DUPLICATE_UNIQUE_FIELD,
            entity_type='unit_types',
            field_name='name',
            conflicting_value='Test Unit',
            existing_record={'id': 1, 'name': 'Test Unit', 'short_name': 'TU'},
            new_record={'id': 1, 'name': 'Test Unit', 'short_name': 'TU_NEW', 'level': 2},
            line_number=2
        )
        
        result = self.resolver._resolve_update(conflict)
        
        assert result.resolved is True
        assert result.action_taken == 'updated'
        assert result.updated_record is not None
        assert result.updated_record['short_name'] == 'TU_NEW'
        assert result.updated_record['level'] == 2
        assert 'datetime_updated' in result.updated_record
    
    def test_resolve_create_version_assignments(self):
        """Test create version resolution strategy for assignments."""
        conflict = ConflictInfo(
            conflict_type=ConflictType.DUPLICATE_UNIQUE_FIELD,
            entity_type='assignments',
            field_name='person_id_unit_id_job_title_id_version',
            conflicting_value=(1, 1, 1, 1),
            existing_record={'id': 1, 'person_id': 1, 'unit_id': 1, 'job_title_id': 1, 'version': 1, 'is_current': True},
            new_record={'person_id': 1, 'unit_id': 1, 'job_title_id': 1, 'percentage': 0.8},
            line_number=2
        )
        
        result = self.resolver._resolve_create_version(conflict)
        
        assert result.resolved is True
        assert result.action_taken == 'created_version'
        assert result.updated_record is not None
        assert result.updated_record['version'] == 2
        assert result.updated_record['is_current'] is True
        assert 'datetime_created' in result.updated_record
    
    def test_resolve_create_version_non_assignments(self):
        """Test create version resolution strategy for non-assignment entities."""
        conflict = ConflictInfo(
            conflict_type=ConflictType.DUPLICATE_UNIQUE_FIELD,
            entity_type='unit_types',
            field_name='name',
            conflicting_value='Test Unit',
            existing_record={'id': 1, 'name': 'Test Unit'},
            new_record={'id': 2, 'name': 'Test Unit'},
            line_number=2
        )
        
        result = self.resolver._resolve_create_version(conflict)
        
        assert result.resolved is False
        assert result.action_taken == 'version_not_supported'
        assert len(result.errors) == 1
    
    def test_resolve_conflict_unknown_strategy(self):
        """Test handling of unknown resolution strategy."""
        conflict = ConflictInfo(
            conflict_type=ConflictType.DUPLICATE_UNIQUE_FIELD,
            entity_type='unit_types',
            field_name='name',
            conflicting_value='Test Unit',
            existing_record={'id': 1, 'name': 'Test Unit'},
            new_record={'id': 2, 'name': 'Test Unit'},
            line_number=2
        )
        
        # Use an invalid strategy (this would normally not happen)
        result = self.resolver.resolve_conflict(conflict, 'invalid_strategy')
        
        assert result.resolved is False
        assert result.action_taken == 'unknown_strategy'
        assert len(result.errors) == 1


class TestConflictResolutionManager:
    """Test cases for the ConflictResolutionManager class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.manager = ConflictResolutionManager()
    
    def test_initialization(self):
        """Test that the conflict resolution manager initializes correctly."""
        assert self.manager is not None
        assert self.manager.detector is not None
        assert self.manager.resolver is not None
    
    @patch('app.services.conflict_resolution.ConflictDetector.detect_conflicts')
    def test_process_conflicts_no_conflicts(self, mock_detect):
        """Test processing when no conflicts are detected."""
        mock_detect.return_value = []
        
        records = [
            {'id': 1, 'name': 'Unit Type 1'},
            {'id': 2, 'name': 'Unit Type 2'}
        ]
        
        processed_records, errors, warnings = self.manager.process_conflicts(
            'unit_types', records, ConflictResolutionStrategy.SKIP
        )
        
        assert len(processed_records) == 2
        assert len(errors) == 0
        assert len(warnings) == 0
        assert processed_records == records
    
    @patch('app.services.conflict_resolution.ConflictDetector.detect_conflicts')
    @patch('app.services.conflict_resolution.ConflictResolver.resolve_conflict')
    def test_process_conflicts_with_skip(self, mock_resolve, mock_detect):
        """Test processing conflicts with skip strategy."""
        # Mock conflicts
        conflict = ConflictInfo(
            conflict_type=ConflictType.DUPLICATE_UNIQUE_FIELD,
            entity_type='unit_types',
            field_name='name',
            conflicting_value='Test Unit',
            existing_record={'id': 1, 'name': 'Test Unit'},
            new_record={'id': 2, 'name': 'Test Unit'},
            line_number=2
        )
        mock_detect.return_value = [conflict]
        
        # Mock resolution result (skip)
        resolution_result = ConflictResolutionResult(
            resolved=True,
            action_taken='skipped',
            skipped=True,
            warnings=[ImportExportValidationError(
                field='name',
                message='Skipped duplicate record',
                error_type=ImportErrorType.DUPLICATE_RECORD
            )]
        )
        mock_resolve.return_value = resolution_result
        
        records = [
            {'id': 1, 'name': 'Unit Type 1'},
            {'id': 2, 'name': 'Test Unit'}  # This will be skipped
        ]
        
        processed_records, errors, warnings = self.manager.process_conflicts(
            'unit_types', records, ConflictResolutionStrategy.SKIP
        )
        
        assert len(processed_records) == 1  # One record skipped
        assert processed_records[0]['id'] == 1
        assert len(errors) == 0
        assert len(warnings) == 1
    
    @patch('app.services.conflict_resolution.ConflictDetector.detect_conflicts')
    @patch('app.services.conflict_resolution.ConflictResolver.resolve_conflict')
    def test_process_conflicts_with_update(self, mock_resolve, mock_detect):
        """Test processing conflicts with update strategy."""
        # Mock conflicts
        conflict = ConflictInfo(
            conflict_type=ConflictType.DUPLICATE_UNIQUE_FIELD,
            entity_type='unit_types',
            field_name='name',
            conflicting_value='Test Unit',
            existing_record={'id': 1, 'name': 'Test Unit', 'level': 1},
            new_record={'id': 2, 'name': 'Test Unit', 'level': 2},
            line_number=2
        )
        mock_detect.return_value = [conflict]
        
        # Mock resolution result (update)
        updated_record = {'id': 1, 'name': 'Test Unit', 'level': 2}
        resolution_result = ConflictResolutionResult(
            resolved=True,
            action_taken='updated',
            updated_record=updated_record,
            warnings=[ImportExportValidationError(
                field='name',
                message='Updated existing record',
                error_type=ImportErrorType.DUPLICATE_RECORD
            )]
        )
        mock_resolve.return_value = resolution_result
        
        records = [
            {'id': 1, 'name': 'Unit Type 1'},
            {'id': 2, 'name': 'Test Unit', 'level': 2}  # This will be updated
        ]
        
        processed_records, errors, warnings = self.manager.process_conflicts(
            'unit_types', records, ConflictResolutionStrategy.UPDATE
        )
        
        assert len(processed_records) == 2
        assert processed_records[1]['level'] == 2  # Updated value
        assert len(errors) == 0
        assert len(warnings) == 1
    
    def test_get_conflict_summary_empty(self):
        """Test conflict summary with no conflicts."""
        summary = self.manager.get_conflict_summary([])
        
        assert summary['total_conflicts'] == 0
        assert summary['by_type'] == {}
        assert summary['by_entity'] == {}
        assert summary['suggested_strategies'] == {}
    
    def test_get_conflict_summary_with_conflicts(self):
        """Test conflict summary with conflicts."""
        conflicts = [
            ConflictInfo(
                conflict_type=ConflictType.DUPLICATE_PRIMARY_KEY,
                entity_type='unit_types',
                field_name='id',
                conflicting_value=1,
                existing_record={},
                new_record={},
                suggested_resolution=ConflictResolutionStrategy.UPDATE
            ),
            ConflictInfo(
                conflict_type=ConflictType.DUPLICATE_UNIQUE_FIELD,
                entity_type='unit_types',
                field_name='name',
                conflicting_value='Test',
                existing_record={},
                new_record={},
                suggested_resolution=ConflictResolutionStrategy.SKIP
            ),
            ConflictInfo(
                conflict_type=ConflictType.DUPLICATE_UNIQUE_FIELD,
                entity_type='persons',
                field_name='email',
                conflicting_value='test@example.com',
                existing_record={},
                new_record={},
                suggested_resolution=ConflictResolutionStrategy.UPDATE
            )
        ]
        
        summary = self.manager.get_conflict_summary(conflicts)
        
        assert summary['total_conflicts'] == 3
        assert summary['by_type']['duplicate_primary_key'] == 1
        assert summary['by_type']['duplicate_unique_field'] == 2
        assert summary['by_entity']['unit_types'] == 2
        assert summary['by_entity']['persons'] == 1
        assert summary['suggested_strategies']['update'] == 2
        assert summary['suggested_strategies']['skip'] == 1


if __name__ == '__main__':
    pytest.main([__file__])