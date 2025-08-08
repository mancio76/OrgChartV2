"""
Conflict resolution system for import operations.

This module provides comprehensive conflict detection and resolution strategies
for handling duplicate records during import operations. It supports multiple
resolution strategies including skip, update, and create version approaches.

Implements Requirements 4.1, 4.2, 4.3, 4.4.
"""

import logging
from datetime import datetime, date
from typing import Dict, List, Optional, Any, Tuple, Set, Union
from dataclasses import dataclass, field
from enum import Enum

from ..models.import_export import (
    ImportExportValidationError, ImportErrorType, ConflictResolutionStrategy
)
from ..models.entity_mappings import get_entity_mapping
from ..database import get_db_manager

logger = logging.getLogger(__name__)


class ConflictType(Enum):
    """Types of conflicts that can occur during import."""
    DUPLICATE_PRIMARY_KEY = "duplicate_primary_key"
    DUPLICATE_UNIQUE_FIELD = "duplicate_unique_field"
    DUPLICATE_BUSINESS_KEY = "duplicate_business_key"
    VERSION_CONFLICT = "version_conflict"
    REFERENCE_CONFLICT = "reference_conflict"


@dataclass
class ConflictInfo:
    """Information about a detected conflict."""
    conflict_type: ConflictType
    entity_type: str
    field_name: str
    conflicting_value: Any
    existing_record: Dict[str, Any]
    new_record: Dict[str, Any]
    line_number: Optional[int] = None
    suggested_resolution: Optional[ConflictResolutionStrategy] = None
    
    def __str__(self) -> str:
        """Return human-readable conflict description."""
        return (f"{self.conflict_type.value} in {self.entity_type}.{self.field_name}: "
                f"'{self.conflicting_value}' (line {self.line_number or 'unknown'})")


@dataclass
class ConflictResolutionResult:
    """Result of conflict resolution operation."""
    resolved: bool
    action_taken: str
    updated_record: Optional[Dict[str, Any]] = None
    created_record_id: Optional[int] = None
    skipped: bool = False
    errors: List[ImportExportValidationError] = field(default_factory=list)
    warnings: List[ImportExportValidationError] = field(default_factory=list)


class ConflictDetector:
    """
    Detects conflicts in import data by comparing with existing database records
    and identifying duplicates within the import batch.
    """
    
    def __init__(self):
        """Initialize the conflict detector."""
        self.db_manager = get_db_manager()
        
        # Define unique field combinations for each entity type
        self.unique_field_combinations = {
            'unit_types': [
                ['name'],  # Unit type names should be unique
                ['short_name']  # Short names should be unique
            ],
            'unit_type_themes': [
                ['name']  # Theme names should be unique
            ],
            'units': [
                ['name'],  # Unit names should be unique within organization
                ['short_name']  # Short names should be unique
            ],
            'job_titles': [
                ['name'],  # Job title names should be unique
                ['short_name']  # Short names should be unique
            ],
            'persons': [
                ['email'],  # Email addresses should be unique
                ['registration_no']  # Registration numbers should be unique
            ],
            'assignments': [
                ['person_id', 'unit_id', 'job_title_id', 'version']  # Assignment version uniqueness
            ]
        }
        
        logger.info("ConflictDetector initialized")
    
    def detect_conflicts(self, entity_type: str, records: List[Dict[str, Any]], 
                        existing_records: Optional[List[Dict[str, Any]]] = None) -> List[ConflictInfo]:
        """
        Detect conflicts in a batch of records.
        
        Args:
            entity_type: Type of entity being processed
            records: List of records to check for conflicts
            existing_records: Existing records from database (optional, will query if not provided)
            
        Returns:
            List of detected conflicts
        """
        conflicts = []
        
        try:
            # Get existing records if not provided
            if existing_records is None:
                existing_records = self._get_existing_records(entity_type)
            
            # Detect conflicts with existing database records
            db_conflicts = self._detect_database_conflicts(entity_type, records, existing_records)
            conflicts.extend(db_conflicts)
            
            # Detect conflicts within the import batch
            batch_conflicts = self._detect_batch_conflicts(entity_type, records)
            conflicts.extend(batch_conflicts)
            
            logger.info(f"Detected {len(conflicts)} conflicts for {entity_type}")
            
        except Exception as e:
            logger.error(f"Error detecting conflicts for {entity_type}: {e}")
            # Don't raise exception, just log error and return empty list
        
        return conflicts
    
    def _get_existing_records(self, entity_type: str) -> List[Dict[str, Any]]:
        """Get existing records from database for conflict detection."""
        try:
            # Get table name from entity mapping
            entity_mapping = get_entity_mapping(entity_type)
            if not entity_mapping:
                logger.warning(f"No entity mapping found for {entity_type}")
                return []
            
            table_name = entity_mapping.table_name
            
            # Query all records from the table
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"SELECT * FROM {table_name}")
                rows = cursor.fetchall()
                
                # Convert rows to dictionaries
                if rows:
                    columns = [description[0] for description in cursor.description]
                    return [dict(zip(columns, row)) for row in rows]
                else:
                    return []
        
        except Exception as e:
            logger.error(f"Error getting existing records for {entity_type}: {e}")
            return []
    
    def _detect_database_conflicts(self, entity_type: str, records: List[Dict[str, Any]], 
                                 existing_records: List[Dict[str, Any]]) -> List[ConflictInfo]:
        """Detect conflicts between import records and existing database records."""
        conflicts = []
        
        try:
            unique_combinations = self.unique_field_combinations.get(entity_type, [])
            
            for line_num, record in enumerate(records, 1):
                # Check primary key conflicts
                if 'id' in record and record['id'] is not None:
                    existing_with_id = next(
                        (existing for existing in existing_records if existing.get('id') == record['id']),
                        None
                    )
                    if existing_with_id:
                        conflicts.append(ConflictInfo(
                            conflict_type=ConflictType.DUPLICATE_PRIMARY_KEY,
                            entity_type=entity_type,
                            field_name='id',
                            conflicting_value=record['id'],
                            existing_record=existing_with_id,
                            new_record=record,
                            line_number=line_num,
                            suggested_resolution=ConflictResolutionStrategy.UPDATE
                        ))
                
                # Check unique field combination conflicts
                for field_combination in unique_combinations:
                    # Skip if any field in combination is missing or None
                    if not all(field in record and record[field] is not None for field in field_combination):
                        continue
                    
                    # Check if combination exists in database
                    for existing in existing_records:
                        if all(existing.get(field) == record[field] for field in field_combination):
                            # Found a conflict
                            field_name = '_'.join(field_combination)
                            conflicting_value = tuple(record[field] for field in field_combination)
                            
                            conflicts.append(ConflictInfo(
                                conflict_type=ConflictType.DUPLICATE_UNIQUE_FIELD,
                                entity_type=entity_type,
                                field_name=field_name,
                                conflicting_value=conflicting_value,
                                existing_record=existing,
                                new_record=record,
                                line_number=line_num,
                                suggested_resolution=self._suggest_resolution_strategy(entity_type, field_combination)
                            ))
                            break  # Only report first conflict for this combination
        
        except Exception as e:
            logger.error(f"Error detecting database conflicts for {entity_type}: {e}")
        
        return conflicts
    
    def _detect_batch_conflicts(self, entity_type: str, records: List[Dict[str, Any]]) -> List[ConflictInfo]:
        """Detect conflicts within the import batch itself."""
        conflicts = []
        
        try:
            unique_combinations = self.unique_field_combinations.get(entity_type, [])
            
            # Track seen values for each unique combination
            seen_values: Dict[str, Dict[Tuple, int]] = {}
            
            for field_combination in unique_combinations:
                field_key = '_'.join(field_combination)
                seen_values[field_key] = {}
                
                for line_num, record in enumerate(records, 1):
                    # Skip if any field in combination is missing or None
                    if not all(field in record and record[field] is not None for field in field_combination):
                        continue
                    
                    combination_value = tuple(record[field] for field in field_combination)
                    
                    if combination_value in seen_values[field_key]:
                        # Found duplicate within batch
                        first_line = seen_values[field_key][combination_value]
                        conflicts.append(ConflictInfo(
                            conflict_type=ConflictType.DUPLICATE_BUSINESS_KEY,
                            entity_type=entity_type,
                            field_name=field_key,
                            conflicting_value=combination_value,
                            existing_record={'line_number': first_line},
                            new_record=record,
                            line_number=line_num,
                            suggested_resolution=ConflictResolutionStrategy.SKIP
                        ))
                    else:
                        seen_values[field_key][combination_value] = line_num
        
        except Exception as e:
            logger.error(f"Error detecting batch conflicts for {entity_type}: {e}")
        
        return conflicts
    
    def _suggest_resolution_strategy(self, entity_type: str, field_combination: List[str]) -> ConflictResolutionStrategy:
        """Suggest appropriate resolution strategy based on entity type and conflict."""
        # For assignments, suggest creating new version
        if entity_type == 'assignments':
            return ConflictResolutionStrategy.CREATE_VERSION
        
        # For primary entities with business meaning, suggest update
        if any(field in ['name', 'email'] for field in field_combination):
            return ConflictResolutionStrategy.UPDATE
        
        # Default to skip for other cases
        return ConflictResolutionStrategy.SKIP


class ConflictResolver:
    """
    Resolves conflicts using various strategies including skip, update, and create version.
    """
    
    def __init__(self):
        """Initialize the conflict resolver."""
        self.db_manager = get_db_manager()
        logger.info("ConflictResolver initialized")
    
    def resolve_conflict(self, conflict: ConflictInfo, 
                        strategy: ConflictResolutionStrategy) -> ConflictResolutionResult:
        """
        Resolve a single conflict using the specified strategy.
        
        Args:
            conflict: Conflict information
            strategy: Resolution strategy to apply
            
        Returns:
            Result of the conflict resolution
        """
        try:
            if strategy == ConflictResolutionStrategy.SKIP:
                return self._resolve_skip(conflict)
            elif strategy == ConflictResolutionStrategy.UPDATE:
                return self._resolve_update(conflict)
            elif strategy == ConflictResolutionStrategy.CREATE_VERSION:
                return self._resolve_create_version(conflict)
            else:
                return ConflictResolutionResult(
                    resolved=False,
                    action_taken="unknown_strategy",
                    errors=[ImportExportValidationError(
                        field="conflict_resolution",
                        message=f"Unknown resolution strategy: {strategy}",
                        error_type=ImportErrorType.BUSINESS_RULE_VIOLATION,
                        entity_type=conflict.entity_type
                    )]
                )
        
        except Exception as e:
            logger.error(f"Error resolving conflict: {e}")
            return ConflictResolutionResult(
                resolved=False,
                action_taken="error",
                errors=[ImportExportValidationError(
                    field="conflict_resolution",
                    message=f"Conflict resolution failed: {str(e)}",
                    error_type=ImportErrorType.BUSINESS_RULE_VIOLATION,
                    entity_type=conflict.entity_type
                )]
            )
    
    def _resolve_skip(self, conflict: ConflictInfo) -> ConflictResolutionResult:
        """Resolve conflict by skipping the new record."""
        return ConflictResolutionResult(
            resolved=True,
            action_taken="skipped",
            skipped=True,
            warnings=[ImportExportValidationError(
                field=conflict.field_name,
                message=f"Skipped duplicate record: {conflict.conflicting_value}",
                error_type=ImportErrorType.DUPLICATE_RECORD,
                entity_type=conflict.entity_type,
                line_number=conflict.line_number
            )]
        )
    
    def _resolve_update(self, conflict: ConflictInfo) -> ConflictResolutionResult:
        """Resolve conflict by updating the existing record."""
        try:
            # Merge new data with existing record
            updated_record = conflict.existing_record.copy()
            
            # Update fields from new record (excluding ID if it's a primary key conflict)
            for field, value in conflict.new_record.items():
                if field != 'id' or conflict.conflict_type != ConflictType.DUPLICATE_PRIMARY_KEY:
                    if value is not None:  # Only update non-null values
                        updated_record[field] = value
            
            # Set update timestamp
            updated_record['datetime_updated'] = datetime.now()
            
            return ConflictResolutionResult(
                resolved=True,
                action_taken="updated",
                updated_record=updated_record,
                warnings=[ImportExportValidationError(
                    field=conflict.field_name,
                    message=f"Updated existing record: {conflict.conflicting_value}",
                    error_type=ImportErrorType.DUPLICATE_RECORD,
                    entity_type=conflict.entity_type,
                    line_number=conflict.line_number
                )]
            )
        
        except Exception as e:
            logger.error(f"Error in update resolution: {e}")
            return ConflictResolutionResult(
                resolved=False,
                action_taken="update_failed",
                errors=[ImportExportValidationError(
                    field=conflict.field_name,
                    message=f"Failed to update record: {str(e)}",
                    error_type=ImportErrorType.BUSINESS_RULE_VIOLATION,
                    entity_type=conflict.entity_type,
                    line_number=conflict.line_number
                )]
            )
    
    def _resolve_create_version(self, conflict: ConflictInfo) -> ConflictResolutionResult:
        """Resolve conflict by creating a new version (primarily for assignments)."""
        try:
            if conflict.entity_type != 'assignments':
                return ConflictResolutionResult(
                    resolved=False,
                    action_taken="version_not_supported",
                    errors=[ImportExportValidationError(
                        field=conflict.field_name,
                        message=f"Version creation not supported for {conflict.entity_type}",
                        error_type=ImportErrorType.BUSINESS_RULE_VIOLATION,
                        entity_type=conflict.entity_type,
                        line_number=conflict.line_number
                    )]
                )
            
            # For assignments, create new version
            new_record = conflict.new_record.copy()
            
            # Determine next version number
            existing_version = conflict.existing_record.get('version', 1)
            new_record['version'] = existing_version + 1
            
            # Set creation timestamp
            new_record['datetime_created'] = datetime.now()
            new_record['datetime_updated'] = datetime.now()
            
            # Mark previous version as not current
            updated_existing = conflict.existing_record.copy()
            updated_existing['is_current'] = False
            updated_existing['datetime_updated'] = datetime.now()
            
            # Set new version as current
            new_record['is_current'] = True
            
            return ConflictResolutionResult(
                resolved=True,
                action_taken="created_version",
                updated_record=new_record,
                warnings=[ImportExportValidationError(
                    field=conflict.field_name,
                    message=f"Created new version {new_record['version']} for assignment",
                    error_type=ImportErrorType.DUPLICATE_RECORD,
                    entity_type=conflict.entity_type,
                    line_number=conflict.line_number
                )]
            )
        
        except Exception as e:
            logger.error(f"Error in version creation resolution: {e}")
            return ConflictResolutionResult(
                resolved=False,
                action_taken="version_creation_failed",
                errors=[ImportExportValidationError(
                    field=conflict.field_name,
                    message=f"Failed to create version: {str(e)}",
                    error_type=ImportErrorType.BUSINESS_RULE_VIOLATION,
                    entity_type=conflict.entity_type,
                    line_number=conflict.line_number
                )]
            )


class ConflictResolutionManager:
    """
    Main manager for conflict detection and resolution during import operations.
    """
    
    def __init__(self):
        """Initialize the conflict resolution manager."""
        self.detector = ConflictDetector()
        self.resolver = ConflictResolver()
        logger.info("ConflictResolutionManager initialized")
    
    def process_conflicts(self, entity_type: str, records: List[Dict[str, Any]], 
                         strategy: ConflictResolutionStrategy,
                         existing_records: Optional[List[Dict[str, Any]]] = None) -> Tuple[List[Dict[str, Any]], List[ImportExportValidationError], List[ImportExportValidationError]]:
        """
        Process conflicts for a batch of records using the specified strategy.
        
        Args:
            entity_type: Type of entity being processed
            records: List of records to process
            strategy: Conflict resolution strategy
            existing_records: Existing records from database (optional)
            
        Returns:
            Tuple of (processed_records, errors, warnings)
        """
        processed_records = []
        errors = []
        warnings = []
        
        try:
            # Detect conflicts
            conflicts = self.detector.detect_conflicts(entity_type, records, existing_records)
            
            if not conflicts:
                # No conflicts, return all records as-is
                return records, errors, warnings
            
            # Group conflicts by record (line number)
            conflicts_by_line = {}
            for conflict in conflicts:
                line_num = conflict.line_number or 0
                if line_num not in conflicts_by_line:
                    conflicts_by_line[line_num] = []
                conflicts_by_line[line_num].append(conflict)
            
            # Process each record
            for i, record in enumerate(records):
                line_num = i + 1
                record_conflicts = conflicts_by_line.get(line_num, [])
                
                if not record_conflicts:
                    # No conflicts for this record
                    processed_records.append(record)
                else:
                    # Resolve conflicts for this record
                    resolved_record, record_errors, record_warnings = self._resolve_record_conflicts(
                        record, record_conflicts, strategy
                    )
                    
                    if resolved_record is not None:
                        processed_records.append(resolved_record)
                    
                    errors.extend(record_errors)
                    warnings.extend(record_warnings)
            
            logger.info(f"Processed {len(conflicts)} conflicts for {entity_type}: "
                       f"{len(processed_records)} records processed, "
                       f"{len(errors)} errors, {len(warnings)} warnings")
        
        except Exception as e:
            logger.error(f"Error processing conflicts for {entity_type}: {e}")
            errors.append(ImportExportValidationError(
                field="conflict_processing",
                message=f"Conflict processing failed: {str(e)}",
                error_type=ImportErrorType.BUSINESS_RULE_VIOLATION,
                entity_type=entity_type
            ))
        
        return processed_records, errors, warnings
    
    def _resolve_record_conflicts(self, record: Dict[str, Any], conflicts: List[ConflictInfo], 
                                strategy: ConflictResolutionStrategy) -> Tuple[Optional[Dict[str, Any]], List[ImportExportValidationError], List[ImportExportValidationError]]:
        """Resolve all conflicts for a single record."""
        current_record = record
        errors = []
        warnings = []
        
        try:
            for conflict in conflicts:
                resolution_result = self.resolver.resolve_conflict(conflict, strategy)
                
                if resolution_result.resolved:
                    if resolution_result.skipped:
                        # Record was skipped, don't include it
                        current_record = None
                        warnings.extend(resolution_result.warnings)
                        break
                    elif resolution_result.updated_record:
                        # Record was updated
                        current_record = resolution_result.updated_record
                        warnings.extend(resolution_result.warnings)
                    
                    warnings.extend(resolution_result.warnings)
                else:
                    # Resolution failed
                    errors.extend(resolution_result.errors)
        
        except Exception as e:
            logger.error(f"Error resolving record conflicts: {e}")
            errors.append(ImportExportValidationError(
                field="record_conflict_resolution",
                message=f"Record conflict resolution failed: {str(e)}",
                error_type=ImportErrorType.BUSINESS_RULE_VIOLATION
            ))
        
        return current_record, errors, warnings
    
    def get_conflict_summary(self, conflicts: List[ConflictInfo]) -> Dict[str, Any]:
        """Get summary statistics for detected conflicts."""
        if not conflicts:
            return {
                'total_conflicts': 0,
                'by_type': {},
                'by_entity': {},
                'suggested_strategies': {}
            }
        
        by_type = {}
        by_entity = {}
        suggested_strategies = {}
        
        for conflict in conflicts:
            # Count by conflict type
            conflict_type = conflict.conflict_type.value
            by_type[conflict_type] = by_type.get(conflict_type, 0) + 1
            
            # Count by entity type
            entity_type = conflict.entity_type
            by_entity[entity_type] = by_entity.get(entity_type, 0) + 1
            
            # Count suggested strategies
            if conflict.suggested_resolution:
                strategy = conflict.suggested_resolution.value
                suggested_strategies[strategy] = suggested_strategies.get(strategy, 0) + 1
        
        return {
            'total_conflicts': len(conflicts),
            'by_type': by_type,
            'by_entity': by_entity,
            'suggested_strategies': suggested_strategies
        }