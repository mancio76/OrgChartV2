"""
Core Import/Export Service for organizational data management.

This service orchestrates import and export operations, managing file format detection,
transaction management, and coordination with existing services while maintaining
referential integrity through dependency-aware processing.
"""

import logging
import os
import tempfile
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass
from datetime import date, datetime

from ..database import get_db_manager
from ..models.import_export import (
    ImportOptions, ExportOptions, ImportResult, ExportResult, PreviewResult,
    ValidationResult, BatchResult, ImportExportValidationError, ImportErrorType,
    FileFormat, ConflictResolutionStrategy
)
from ..models.entity_mappings import DEPENDENCY_ORDER, get_entity_mapping
from ..utils.error_handler import (
    get_error_logger, ErrorSeverity, ErrorCategory, log_import_error, log_system_error
)
from .audit_trail import (
    get_audit_manager, OperationType, OperationStatus, ChangeType
)
from .csv_processor import CSVProcessor
from .json_processor import JSONProcessor
from .dependency_resolver import DependencyResolver, ForeignKeyResolver
from .validation_framework import ValidationFramework
from .conflict_resolution import ConflictResolutionManager
from .base import BaseService, ServiceException, ServiceValidationException

logger = logging.getLogger(__name__)


class ImportExportException(ServiceException):
    """Exception raised for import/export operation errors"""
    pass


class FileFormatDetectionError(ImportExportException):
    """Exception raised when file format cannot be detected"""
    pass


class TransactionRollbackError(ImportExportException):
    """Exception raised when transaction rollback fails"""
    pass


@dataclass
class TransactionContext:
    """Context for managing database transactions during import/export operations"""
    operation_id: str
    is_active: bool = True
    start_time: float = 0.0
    
    def __post_init__(self):
        """Initialize transaction start time"""
        if self.start_time == 0.0:
            self.start_time = time.time()


class ImportExportService:
    """
    Core service for managing import and export operations.
    
    This service provides comprehensive functionality for bulk data operations
    while maintaining referential integrity and supporting multiple file formats.
    Implements Requirements 1.1, 1.4, 1.5, 2.1, 2.2, 6.1, 6.2.
    """
    
    def __init__(self):
        """Initialize the import/export service with required components."""
        self.db_manager = get_db_manager()
        self.dependency_resolver = DependencyResolver()
        self.foreign_key_resolver = ForeignKeyResolver(self.dependency_resolver)
        self.validation_framework = ValidationFramework()
        self.conflict_resolution_manager = ConflictResolutionManager()
        self.error_logger = get_error_logger()
        self.audit_manager = get_audit_manager()
        self._transaction_contexts: Dict[str, TransactionContext] = {}
        
        logger.info("ImportExportService initialized with enhanced error handling and audit trail")
    
    def detect_file_format(self, file_path: str) -> FileFormat:
        """
        Detect file format based on extension and content analysis.
        
        Args:
            file_path: Path to the file to analyze
            
        Returns:
            Detected file format
            
        Raises:
            FileFormatDetectionError: If format cannot be determined
        """
        try:
            if not os.path.exists(file_path):
                raise FileFormatDetectionError(f"File not found: {file_path}")
            
            # Get file extension
            file_extension = Path(file_path).suffix.lower()
            
            # Primary detection by extension
            if file_extension == '.json':
                # Validate JSON content
                if self._validate_json_content(file_path):
                    return FileFormat.JSON
                else:
                    raise FileFormatDetectionError(f"Invalid JSON content in file: {file_path}")
            
            elif file_extension == '.csv':
                # Validate CSV content
                if self._validate_csv_content(file_path):
                    return FileFormat.CSV
                else:
                    raise FileFormatDetectionError(f"Invalid CSV content in file: {file_path}")
            
            else:
                # Content-based detection for unknown extensions
                detected_format = self._detect_format_by_content(file_path)
                if detected_format:
                    return detected_format
                else:
                    raise FileFormatDetectionError(
                        f"Unable to detect file format for: {file_path}. "
                        f"Supported formats: .json, .csv"
                    )
        
        except Exception as e:
            if isinstance(e, FileFormatDetectionError):
                raise
            logger.error(f"Error detecting file format for {file_path}: {e}")
            raise FileFormatDetectionError(f"File format detection failed: {str(e)}")
    
    def validate_file_structure(self, file_path: str, file_format: FileFormat, 
                               entity_type: Optional[str] = None) -> List[ImportExportValidationError]:
        """
        Validate file structure without processing all data.
        
        Args:
            file_path: Path to the file to validate
            file_format: Expected file format
            entity_type: Expected entity type (for CSV files)
            
        Returns:
            List of validation errors
        """
        try:
            logger.debug(f"Validating file structure: {file_path} ({file_format.value})")
            
            if file_format == FileFormat.JSON:
                processor = JSONProcessor()
                return processor.validate_json_structure(file_path)
            
            elif file_format == FileFormat.CSV:
                if not entity_type:
                    return [ImportExportValidationError(
                        field="entity_type",
                        message="Entity type must be specified for CSV validation",
                        error_type=ImportErrorType.FILE_FORMAT_ERROR
                    )]
                
                processor = CSVProcessor()
                return processor.validate_csv_structure(file_path, entity_type)
            
            else:
                return [ImportExportValidationError(
                    field="file_format",
                    message=f"Unsupported file format: {file_format.value}",
                    error_type=ImportErrorType.FILE_FORMAT_ERROR
                )]
        
        except Exception as e:
            logger.error(f"Error validating file structure: {e}")
            return [ImportExportValidationError(
                field="file_validation",
                message=f"File validation failed: {str(e)}",
                error_type=ImportErrorType.FILE_FORMAT_ERROR
            )]
    
    def validate_import_data(self, data: Dict[str, List[Dict[str, Any]]], 
                           options: ImportOptions) -> ValidationResult:
        """
        Comprehensive validation of import data using the validation framework.
        
        This method implements Requirements 1.3, 3.1, 3.2, 3.3 by providing:
        - Data type validation for all fields
        - Business rule validation
        - Foreign key constraint validation
        - Comprehensive error reporting
        
        Args:
            data: Parsed import data
            options: Import options
            
        Returns:
            ValidationResult with detailed validation information
        """
        from ..models.import_export import ValidationResult
        
        all_errors = []
        all_warnings = []
        total_validated = 0
        
        try:
            logger.info("Starting comprehensive data validation")
            
            # Validate each entity type
            for entity_type, records in data.items():
                if entity_type not in options.entity_types:
                    continue
                
                logger.debug(f"Validating {len(records)} records for {entity_type}")
                
                # Validate records using validation framework
                validation_errors = self.validation_framework.validate_records_batch(
                    entity_type, records, start_line=1
                )
                
                # Separate errors and warnings
                for error in validation_errors:
                    if error.error_type in [ImportErrorType.MISSING_REQUIRED_FIELD, 
                                          ImportErrorType.INVALID_DATA_TYPE,
                                          ImportErrorType.FOREIGN_KEY_VIOLATION]:
                        all_errors.append(error)
                    else:
                        all_warnings.append(error)
                
                total_validated += len(records)
            
            # Validate foreign key constraints
            if not options.skip_validation:
                fk_errors = self._validate_comprehensive_foreign_keys(data, options)
                all_errors.extend(fk_errors)
            
            # Create validation result
            is_valid = len(all_errors) == 0
            
            result = ValidationResult(
                is_valid=is_valid,
                errors=all_errors,
                warnings=all_warnings,
                validated_records=total_validated
            )
            
            logger.info(f"Validation completed: {total_validated} records validated, "
                       f"{len(all_errors)} errors, {len(all_warnings)} warnings")
            
            return result
        
        except Exception as e:
            logger.error(f"Error in comprehensive data validation: {e}")
            return ValidationResult(
                is_valid=False,
                errors=[ImportExportValidationError(
                    field="validation_framework",
                    message=f"Validation framework error: {str(e)}",
                    error_type=ImportErrorType.BUSINESS_RULE_VIOLATION
                )],
                validated_records=total_validated
            )
    
    def _validate_comprehensive_foreign_keys(self, data: Dict[str, List[Dict[str, Any]]], 
                                           options: ImportOptions) -> List[ImportExportValidationError]:
        """
        Comprehensive foreign key validation using the validation framework.
        
        Args:
            data: Import data to validate
            options: Import options
            
        Returns:
            List of foreign key validation errors
        """
        errors = []
        
        try:
            # Build reference map including both existing database records and import data
            reference_map = self.foreign_key_resolver.build_reference_map(data)
            
            # Add existing database records to reference map
            for entity_type in options.entity_types:
                if entity_type in data:
                    try:
                        existing_records = self.conflict_resolution_manager.detector._get_existing_records(entity_type)
                        existing_ids = {record.get('id') for record in existing_records if record.get('id') is not None}
                        
                        if entity_type not in reference_map:
                            reference_map[entity_type] = set()
                        reference_map[entity_type].update(existing_ids)
                    
                    except Exception as e:
                        logger.warning(f"Could not load existing records for {entity_type}: {e}")
            
            # Validate foreign key constraints for each entity type
            for entity_type, records in data.items():
                if entity_type in options.entity_types:
                    fk_errors = self.validation_framework.validate_foreign_key_constraints(
                        entity_type, records, reference_map
                    )
                    errors.extend(fk_errors)
        
        except Exception as e:
            logger.error(f"Error in comprehensive foreign key validation: {e}")
            errors.append(ImportExportValidationError(
                field="foreign_key_validation",
                message=f"Foreign key validation failed: {str(e)}",
                error_type=ImportErrorType.BUSINESS_RULE_VIOLATION
            ))
        
        return errors
    
    def create_transaction_context(self, operation_id: str) -> TransactionContext:
        """
        Create a new transaction context for import/export operations.
        
        For this implementation, we'll use a simplified approach that works with
        the existing database manager's transaction handling.
        
        Args:
            operation_id: Unique identifier for the operation
            
        Returns:
            Transaction context for managing database operations
            
        Raises:
            ImportExportException: If transaction creation fails
        """
        try:
            logger.debug(f"Creating transaction context for operation: {operation_id}")
            
            # Create transaction context (simplified approach)
            context = TransactionContext(
                operation_id=operation_id,
                is_active=True
            )
            
            # Store context for management
            self._transaction_contexts[operation_id] = context
            
            logger.info(f"Transaction context created for operation: {operation_id}")
            return context
        
        except Exception as e:
            logger.error(f"Failed to create transaction context for {operation_id}: {e}")
            raise ImportExportException(f"Transaction creation failed: {str(e)}")
    
    def commit_transaction(self, operation_id: str) -> None:
        """
        Commit transaction for the specified operation.
        
        Args:
            operation_id: Operation identifier
            
        Raises:
            ImportExportException: If commit fails
        """
        try:
            context = self._transaction_contexts.get(operation_id)
            if not context or not context.is_active:
                raise ImportExportException(f"No active transaction for operation: {operation_id}")
            
            logger.debug(f"Committing transaction for operation: {operation_id}")
            
            # Mark transaction as committed
            context.is_active = False
            
            # Calculate transaction duration
            duration = time.time() - context.start_time
            logger.info(f"Transaction committed for operation {operation_id} (duration: {duration:.2f}s)")
            
            # Clean up context
            del self._transaction_contexts[operation_id]
        
        except Exception as e:
            logger.error(f"Failed to commit transaction for {operation_id}: {e}")
            # Attempt rollback on commit failure
            try:
                self.rollback_transaction(operation_id)
            except Exception as rollback_error:
                logger.error(f"Rollback after commit failure also failed: {rollback_error}")
            
            raise ImportExportException(f"Transaction commit failed: {str(e)}")
    
    def rollback_transaction(self, operation_id: str) -> None:
        """
        Rollback transaction for the specified operation.
        
        Args:
            operation_id: Operation identifier
            
        Raises:
            TransactionRollbackError: If rollback fails
        """
        try:
            context = self._transaction_contexts.get(operation_id)
            if not context:
                logger.warning(f"No transaction context found for rollback: {operation_id}")
                return
            
            logger.debug(f"Rolling back transaction for operation: {operation_id}")
            
            if context.is_active:
                context.is_active = False
            
            # Calculate transaction duration
            duration = time.time() - context.start_time
            logger.info(f"Transaction rolled back for operation {operation_id} (duration: {duration:.2f}s)")
            
            # Clean up context
            if operation_id in self._transaction_contexts:
                del self._transaction_contexts[operation_id]
        
        except Exception as e:
            logger.error(f"Failed to rollback transaction for {operation_id}: {e}")
            raise TransactionRollbackError(f"Transaction rollback failed: {str(e)}")
    
    def cleanup_transaction_contexts(self) -> None:
        """Clean up any remaining transaction contexts (for error recovery)."""
        try:
            for operation_id, context in list(self._transaction_contexts.items()):
                if context.is_active:
                    logger.warning(f"Cleaning up active transaction context: {operation_id}")
                    try:
                        self.rollback_transaction(operation_id)
                    except Exception as e:
                        logger.error(f"Error during cleanup rollback for {operation_id}: {e}")
            
            self._transaction_contexts.clear()
            logger.info("Transaction contexts cleaned up")
        
        except Exception as e:
            logger.error(f"Error during transaction context cleanup: {e}")
    
    def _validate_json_content(self, file_path: str) -> bool:
        """Validate that file contains valid JSON content."""
        try:
            import json
            with open(file_path, 'r', encoding='utf-8') as f:
                json.load(f)
            return True
        except (json.JSONDecodeError, UnicodeDecodeError, IOError):
            return False
    
    def _validate_csv_content(self, file_path: str) -> bool:
        """Validate that file contains valid CSV content."""
        try:
            import csv
            with open(file_path, 'r', encoding='utf-8') as f:
                # Try to read first few lines as CSV
                reader = csv.reader(f)
                for i, row in enumerate(reader):
                    if i >= 3:  # Check first 3 rows
                        break
                    if not row:  # Empty row
                        continue
            return True
        except (csv.Error, UnicodeDecodeError, IOError):
            return False
    
    def _detect_format_by_content(self, file_path: str) -> Optional[FileFormat]:
        """Detect file format by analyzing content."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
                
                # Check for JSON (starts with { or [)
                if first_line.startswith(('{', '[')):
                    if self._validate_json_content(file_path):
                        return FileFormat.JSON
                
                # Check for CSV (contains commas or semicolons)
                if ',' in first_line or ';' in first_line:
                    if self._validate_csv_content(file_path):
                        return FileFormat.CSV
            
            return None
        
        except Exception:
            return None
    
    def get_supported_formats(self) -> List[FileFormat]:
        """Get list of supported file formats."""
        return [FileFormat.JSON, FileFormat.CSV]
    
    def get_transaction_status(self, operation_id: str) -> Dict[str, Any]:
        """
        Get status information for a transaction.
        
        Args:
            operation_id: Operation identifier
            
        Returns:
            Dictionary containing transaction status information
        """
        context = self._transaction_contexts.get(operation_id)
        if not context:
            return {
                "exists": False,
                "is_active": False,
                "duration": 0.0
            }
        
        return {
            "exists": True,
            "is_active": context.is_active,
            "duration": time.time() - context.start_time,
            "operation_id": context.operation_id
        }
    
    def get_active_transactions(self) -> List[str]:
        """Get list of active transaction operation IDs."""
        return [
            operation_id for operation_id, context in self._transaction_contexts.items()
            if context.is_active
        ]
    
    def preview_import(self, file_path: str, file_format: FileFormat, 
                      options: ImportOptions) -> PreviewResult:
        """
        Preview import data without persisting changes to the database.
        
        This method implements Requirements 3.1, 3.2, 3.3 by providing:
        - Preview data processing without persistence
        - Validation result display with detailed error information
        - Foreign key relationship preview and dependency analysis
        
        Args:
            file_path: Path to the file to preview
            file_format: Format of the file (CSV or JSON)
            options: Import configuration options
            
        Returns:
            PreviewResult with preview data and validation information
        """
        import time
        
        start_time = time.time()
        logger.info(f"Starting import preview for file: {file_path}")
        
        # Initialize preview result
        result = PreviewResult(
            success=False,
            estimated_processing_time=0.0
        )
        
        try:
            # Step 1: Validate file format and structure
            logger.debug(f"Validating file format and structure for preview")
            
            # For CSV files, we need to specify the entity type for validation
            entity_type_for_validation = None
            if file_format == FileFormat.CSV and len(options.entity_types) == 1:
                entity_type_for_validation = options.entity_types[0]
            
            format_errors = self.validate_file_structure(file_path, file_format, entity_type_for_validation)
            if format_errors:
                result.validation_results.extend(format_errors)
                result.estimated_processing_time = time.time() - start_time
                logger.error(f"File validation failed for preview: {len(format_errors)} errors")
                return result
            
            # Step 2: Parse file data based on format
            logger.debug(f"Parsing {file_format.value} file for preview")
            parsed_data = self._parse_import_file(file_path, file_format, options)
            
            if not parsed_data:
                result.validation_results.append(ImportExportValidationError(
                    field="file_parsing",
                    message="No data could be parsed from the file",
                    error_type=ImportErrorType.FILE_FORMAT_ERROR
                ))
                result.estimated_processing_time = time.time() - start_time
                return result
            
            # Store preview data
            result.preview_data = parsed_data
            
            # Step 3: Comprehensive data validation using validation framework
            logger.debug("Performing comprehensive data validation for preview")
            validation_result = self.validate_import_data(parsed_data, options)
            result.validation_results.extend(validation_result.errors)
            result.validation_results.extend(validation_result.warnings)
            
            # Step 4: Determine dependency processing order
            logger.debug("Determining dependency processing order")
            try:
                entity_types = list(parsed_data.keys())
                result.dependency_order = self.dependency_resolver.get_processing_order(entity_types)
                logger.debug(f"Preview dependency order: {result.dependency_order}")
            except Exception as e:
                result.validation_results.append(ImportExportValidationError(
                    field="dependency_order",
                    message=f"Could not determine processing order: {str(e)}",
                    error_type=ImportErrorType.CIRCULAR_REFERENCE
                ))
            
            # Step 5: Build foreign key relationship mappings for preview
            logger.debug("Building foreign key relationship mappings")
            try:
                result.foreign_key_mappings = self._build_preview_foreign_key_mappings(parsed_data, options)
            except Exception as e:
                result.validation_results.append(ImportExportValidationError(
                    field="foreign_key_mappings",
                    message=f"Could not build foreign key mappings: {str(e)}",
                    error_type=ImportErrorType.FOREIGN_KEY_VIOLATION
                ))
            
            # Step 6: Estimate processing time based on record count and complexity
            result.estimated_processing_time = self._estimate_processing_time(parsed_data, options)
            
            # Step 7: Mark preview as successful if no critical errors
            critical_errors = [e for e in result.validation_results 
                             if e.error_type in [ImportErrorType.FILE_FORMAT_ERROR,
                                               ImportErrorType.CIRCULAR_REFERENCE]]
            result.success = len(critical_errors) == 0
            
            processing_time = time.time() - start_time
            logger.info(f"Import preview completed in {processing_time:.2f}s: "
                       f"{result.total_records} records, {len(result.validation_results)} validation issues")
            
            return result
        
        except Exception as e:
            logger.error(f"Critical error in import preview: {e}")
            result.validation_results.append(ImportExportValidationError(
                field="preview_operation",
                message=f"Preview operation failed: {str(e)}",
                error_type=ImportErrorType.BUSINESS_RULE_VIOLATION
            ))
            result.estimated_processing_time = time.time() - start_time
            return result
    
    def _build_preview_foreign_key_mappings(self, data: Dict[str, List[Dict[str, Any]]], 
                                          options: ImportOptions) -> Dict[str, Dict[str, Any]]:
        """
        Build foreign key relationship mappings for preview display.
        
        This method analyzes the import data and existing database records to show
        how foreign key relationships will be resolved during import.
        
        Args:
            data: Parsed import data
            options: Import options
            
        Returns:
            Dictionary mapping entity types to their foreign key relationship information
        """
        mappings = {}
        
        try:
            # Build reference map from import data
            import_reference_map = self.foreign_key_resolver.build_reference_map(data)
            
            # Get existing database records for reference resolution
            existing_reference_map = {}
            for entity_type in options.entity_types:
                try:
                    existing_records = self.conflict_resolution_manager.detector._get_existing_records(entity_type)
                    existing_ids = {record.get('id') for record in existing_records if record.get('id') is not None}
                    existing_reference_map[entity_type] = existing_ids
                except Exception as e:
                    logger.warning(f"Could not load existing records for {entity_type}: {e}")
                    existing_reference_map[entity_type] = set()
            
            # Analyze foreign key relationships for each entity type
            for entity_type, records in data.items():
                if entity_type not in options.entity_types:
                    continue
                
                entity_mapping = get_entity_mapping(entity_type)
                if not entity_mapping or not entity_mapping.foreign_keys:
                    continue
                
                fk_analysis = {
                    'total_records': len(records),
                    'foreign_key_fields': list(entity_mapping.foreign_keys.keys()),
                    'relationships': {},
                    'missing_references': [],
                    'resolved_references': []
                }
                
                # Analyze each foreign key field
                for fk_field, target_entity in entity_mapping.foreign_keys.items():
                    fk_stats = {
                        'target_entity': target_entity,
                        'total_references': 0,
                        'resolved_from_import': 0,
                        'resolved_from_existing': 0,
                        'unresolved': 0,
                        'null_references': 0
                    }
                    
                    # Analyze references in records
                    for record_idx, record in enumerate(records):
                        fk_value = record.get(fk_field)
                        
                        if fk_value is None or fk_value == '':
                            fk_stats['null_references'] += 1
                            continue
                        
                        fk_stats['total_references'] += 1
                        
                        # Check if reference exists in import data
                        if target_entity in import_reference_map and fk_value in import_reference_map[target_entity]:
                            fk_stats['resolved_from_import'] += 1
                            fk_analysis['resolved_references'].append({
                                'record_index': record_idx,
                                'field': fk_field,
                                'value': fk_value,
                                'resolved_from': 'import_data',
                                'target_entity': target_entity
                            })
                        # Check if reference exists in existing database
                        elif target_entity in existing_reference_map and fk_value in existing_reference_map[target_entity]:
                            fk_stats['resolved_from_existing'] += 1
                            fk_analysis['resolved_references'].append({
                                'record_index': record_idx,
                                'field': fk_field,
                                'value': fk_value,
                                'resolved_from': 'existing_data',
                                'target_entity': target_entity
                            })
                        else:
                            fk_stats['unresolved'] += 1
                            fk_analysis['missing_references'].append({
                                'record_index': record_idx,
                                'field': fk_field,
                                'value': fk_value,
                                'target_entity': target_entity
                            })
                    
                    fk_analysis['relationships'][fk_field] = fk_stats
                
                mappings[entity_type] = fk_analysis
            
            return mappings
        
        except Exception as e:
            logger.error(f"Error building preview foreign key mappings: {e}")
            return {}
    
    def _estimate_processing_time(self, data: Dict[str, List[Dict[str, Any]]], 
                                options: ImportOptions) -> float:
        """
        Estimate processing time based on data complexity and record count.
        
        Args:
            data: Parsed import data
            options: Import options
            
        Returns:
            Estimated processing time in seconds
        """
        try:
            total_records = sum(len(records) for records in data.values())
            
            # Base processing time per record (in seconds)
            base_time_per_record = 0.01  # 10ms per record
            
            # Complexity multipliers
            complexity_multiplier = 1.0
            
            # Add complexity for validation
            if not options.skip_validation:
                complexity_multiplier += 0.5
            
            # Add complexity for conflict resolution
            if options.conflict_resolution != ConflictResolutionStrategy.SKIP:
                complexity_multiplier += 0.3
            
            # Add complexity for foreign key resolution
            has_foreign_keys = any(
                get_entity_mapping(entity_type) and get_entity_mapping(entity_type).foreign_keys
                for entity_type in data.keys()
            )
            if has_foreign_keys:
                complexity_multiplier += 0.2
            
            # Calculate estimated time
            estimated_time = total_records * base_time_per_record * complexity_multiplier
            
            # Add minimum processing time
            estimated_time = max(estimated_time, 1.0)
            
            # Add maximum reasonable time cap
            estimated_time = min(estimated_time, 300.0)  # 5 minutes max
            
            return estimated_time
        
        except Exception as e:
            logger.warning(f"Could not estimate processing time: {e}")
            return 30.0  # Default estimate
    
    def import_data(self, file_path: str, file_format: FileFormat, 
                   options: ImportOptions, user_id: Optional[str] = None) -> ImportResult:
        """
        Main import orchestration method that processes data files with comprehensive
        error handling, batch processing, and rollback capabilities.
        
        This method implements Requirements 1.1, 1.4, 1.5, 7.1, 7.2, 7.5 by providing:
        - File format validation and processing
        - Dependency-aware entity processing order
        - Transaction management with rollback on failure
        - Batch processing for large datasets
        - Comprehensive error reporting and validation
        - Structured error logging with line-by-line reporting
        - Audit trail with user tracking and data change logging
        
        Args:
            file_path: Path to the file to import
            file_format: Format of the file (CSV or JSON)
            options: Import configuration options
            user_id: Optional user ID for audit trail
            
        Returns:
            ImportResult with detailed processing information
            
        Raises:
            ImportExportException: If critical import operation fails
        """
        # Generate unique operation ID for transaction management
        operation_id = str(uuid.uuid4())
        start_time = time.time()
        
        # Initialize enhanced error logging and audit trail
        error_report = self.error_logger.create_error_report(operation_id, "import")
        audit_record = self.audit_manager.start_operation(
            operation_id=operation_id,
            operation_type=OperationType.IMPORT,
            user_id=user_id,
            file_path=file_path,
            file_format=file_format.value,
            entity_types=options.entity_types,
            options=options.__dict__,
            metadata={"batch_size": options.batch_size, "conflict_resolution": options.conflict_resolution.value}
        )
        
        logger.info(f"Starting import operation {operation_id} for file: {file_path}")
        
        # Initialize result object
        result = ImportResult(
            success=False,
            imported_files=[file_path],
            execution_time=0.0
        )
        
        try:
            # Update operation status
            self.audit_manager.update_operation_status(operation_id, OperationStatus.IN_PROGRESS)
            
            # Step 1: Validate file format and structure
            logger.debug(f"Validating file format and structure for {file_path}")
            
            # For CSV files, we need to specify the entity type for validation
            entity_type_for_validation = None
            if file_format == FileFormat.CSV and len(options.entity_types) == 1:
                entity_type_for_validation = options.entity_types[0]
            
            format_errors = self.validate_file_structure(file_path, file_format, entity_type_for_validation)
            if format_errors:
                # Log structured errors for file format issues
                for error in format_errors:
                    self.error_logger.log_structured_error(
                        operation_id=operation_id,
                        severity=ErrorSeverity.ERROR,
                        category=ErrorCategory.FILE_PROCESSING,
                        error_type=error.error_type,
                        message=error.message,
                        file_path=file_path,
                        user_id=user_id,
                        resolution_hint="Check file format and structure requirements"
                    )
                
                result.errors.extend(format_errors)
                result.execution_time = time.time() - start_time
                
                # Update audit trail
                self.audit_manager.update_operation_status(
                    operation_id, OperationStatus.FAILED, 
                    error_count=len(format_errors)
                )
                self.error_logger.finalize_error_report(operation_id)
                
                logger.error(f"File validation failed for {file_path}: {len(format_errors)} errors")
                return result
            
            # Step 2: Parse file data based on format
            logger.debug(f"Parsing {file_format.value} file: {file_path}")
            parsed_data = self._parse_import_file(file_path, file_format, options)
            
            if not parsed_data:
                # Log structured error for parsing failure
                self.error_logger.log_structured_error(
                    operation_id=operation_id,
                    severity=ErrorSeverity.CRITICAL,
                    category=ErrorCategory.FILE_PROCESSING,
                    error_type=ImportErrorType.FILE_FORMAT_ERROR,
                    message="No data could be parsed from the file",
                    file_path=file_path,
                    user_id=user_id,
                    resolution_hint="Verify file format and content structure"
                )
                
                result.errors.append(ImportExportValidationError(
                    field="file_parsing",
                    message="No data could be parsed from the file",
                    error_type=ImportErrorType.FILE_FORMAT_ERROR
                ))
                result.execution_time = time.time() - start_time
                
                # Update audit trail
                self.audit_manager.update_operation_status(
                    operation_id, OperationStatus.FAILED, error_count=1
                )
                self.error_logger.finalize_error_report(operation_id)
                
                return result
            
            # Step 3: Comprehensive data validation using validation framework
            logger.debug("Performing comprehensive data validation")
            if not options.skip_validation:
                validation_result = self.validate_import_data(parsed_data, options)
                
                # Log structured errors for validation issues
                for error in validation_result.errors:
                    self.error_logger.log_structured_error(
                        operation_id=operation_id,
                        severity=ErrorSeverity.ERROR,
                        category=ErrorCategory.DATA_VALIDATION,
                        error_type=error.error_type,
                        message=error.message,
                        entity_type=error.entity_type,
                        line_number=error.line_number,
                        field_name=error.field,
                        record_id=error.record_id,
                        user_id=user_id,
                        resolution_hint="Check data format and business rules"
                    )
                
                # Log warnings
                for warning in validation_result.warnings:
                    self.error_logger.log_structured_error(
                        operation_id=operation_id,
                        severity=ErrorSeverity.WARNING,
                        category=ErrorCategory.DATA_VALIDATION,
                        error_type=warning.error_type,
                        message=warning.message,
                        entity_type=warning.entity_type,
                        line_number=warning.line_number,
                        field_name=warning.field,
                        record_id=warning.record_id,
                        user_id=user_id
                    )
                
                result.errors.extend(validation_result.errors)
                result.warnings.extend(validation_result.warnings)
                
                # Check if validation failed critically
                critical_errors = [e for e in validation_result.errors 
                                 if e.error_type in [ImportErrorType.MISSING_REQUIRED_FIELD,
                                                   ImportErrorType.FOREIGN_KEY_VIOLATION, 
                                                   ImportErrorType.CIRCULAR_REFERENCE]]
                if critical_errors:
                    result.execution_time = time.time() - start_time
                    
                    # Update audit trail
                    self.audit_manager.update_operation_status(
                        operation_id, OperationStatus.FAILED, 
                        error_count=len(validation_result.errors),
                        warning_count=len(validation_result.warnings)
                    )
                    self.error_logger.finalize_error_report(operation_id)
                    
                    logger.error(f"Critical validation failed: {len(critical_errors)} errors")
                    return result
            
            # Step 4: Validate dependencies and foreign key references (legacy validation)
            logger.debug("Validating dependencies and foreign key references")
            dependency_errors = self._validate_import_dependencies(parsed_data, options)
            if dependency_errors:
                result.warnings.extend(dependency_errors)  # Treat as warnings since comprehensive validation already ran
            
            # Step 5: Create transaction context for import operation
            logger.debug(f"Creating transaction context for operation {operation_id}")
            transaction_context = self.create_transaction_context(operation_id)
            
            try:
                # Step 6: Process data in dependency order with batch processing and conflict resolution
                logger.info("Starting data processing in dependency order with conflict resolution")
                processing_result = self._process_import_data_batched(
                    parsed_data, options, operation_id, result
                )
                
                # Check if processing was successful
                if not processing_result:
                    logger.error("Data processing failed, rolling back transaction")
                    self.rollback_transaction(operation_id)
                    result.execution_time = time.time() - start_time
                    return result
                
                # Step 7: Validate final state and commit transaction
                if options.validate_only:
                    logger.info("Validation-only mode: rolling back transaction")
                    self.rollback_transaction(operation_id)
                    result.success = True
                    result.execution_time = time.time() - start_time
                    
                    # Update audit trail for validation-only operation
                    self.audit_manager.update_operation_status(
                        operation_id, OperationStatus.COMPLETED,
                        results={"validation_only": True},
                        error_count=len(result.errors),
                        warning_count=len(result.warnings)
                    )
                    self.audit_manager.complete_operation(operation_id)
                    self.error_logger.finalize_error_report(operation_id)
                    
                    logger.info(f"Import validation completed successfully in {result.execution_time:.2f}s")
                    return result
                else:
                    logger.info("Committing import transaction")
                    self.commit_transaction(operation_id)
                    result.success = True
                    result.execution_time = time.time() - start_time
                    
                    # Update audit trail for successful import
                    self.audit_manager.update_operation_status(
                        operation_id, OperationStatus.COMPLETED,
                        results={
                            "total_processed": result.total_processed,
                            "total_created": result.total_created,
                            "total_updated": result.total_updated,
                            "total_skipped": result.total_skipped,
                            "execution_time": result.execution_time
                        },
                        error_count=len(result.errors),
                        warning_count=len(result.warnings)
                    )
                    self.audit_manager.complete_operation(operation_id)
                    self.error_logger.finalize_error_report(operation_id)
                    
                    logger.info(f"Import operation {operation_id} completed successfully in {result.execution_time:.2f}s")
                    return result
            
            except Exception as processing_error:
                # Log structured error for processing failure
                self.error_logger.log_structured_error(
                    operation_id=operation_id,
                    severity=ErrorSeverity.CRITICAL,
                    category=ErrorCategory.SYSTEM,
                    error_type=ImportErrorType.BUSINESS_RULE_VIOLATION,
                    message=f"Data processing failed: {str(processing_error)}",
                    user_id=user_id,
                    exception=processing_error,
                    resolution_hint="Check system logs and data integrity"
                )
                
                logger.error(f"Error during data processing: {processing_error}")
                try:
                    self.rollback_transaction(operation_id)
                    logger.info(f"Successfully rolled back transaction for operation {operation_id}")
                except Exception as rollback_error:
                    # Log rollback failure
                    self.error_logger.log_structured_error(
                        operation_id=operation_id,
                        severity=ErrorSeverity.CRITICAL,
                        category=ErrorCategory.TRANSACTION,
                        error_type=ImportErrorType.BUSINESS_RULE_VIOLATION,
                        message=f"Failed to rollback transaction: {str(rollback_error)}",
                        user_id=user_id,
                        exception=rollback_error,
                        resolution_hint="Manual database cleanup may be required"
                    )
                    
                    logger.error(f"Failed to rollback transaction: {rollback_error}")
                    result.errors.append(ImportExportValidationError(
                        field="transaction_rollback",
                        message=f"Failed to rollback transaction: {str(rollback_error)}",
                        error_type=ImportErrorType.BUSINESS_RULE_VIOLATION
                    ))
                
                result.errors.append(ImportExportValidationError(
                    field="data_processing",
                    message=f"Data processing failed: {str(processing_error)}",
                    error_type=ImportErrorType.BUSINESS_RULE_VIOLATION
                ))
                result.execution_time = time.time() - start_time
                
                # Update audit trail for failed operation
                self.audit_manager.update_operation_status(
                    operation_id, OperationStatus.FAILED,
                    error_count=len(result.errors),
                    warning_count=len(result.warnings)
                )
                self.audit_manager.complete_operation(operation_id)
                self.error_logger.finalize_error_report(operation_id)
                
                return result
        
        except Exception as e:
            # Log critical system error
            self.error_logger.log_structured_error(
                operation_id=operation_id,
                severity=ErrorSeverity.CRITICAL,
                category=ErrorCategory.SYSTEM,
                error_type=ImportErrorType.BUSINESS_RULE_VIOLATION,
                message=f"Critical error in import operation: {str(e)}",
                user_id=user_id,
                exception=e,
                resolution_hint="Check system logs and contact administrator"
            )
            
            logger.error(f"Critical error in import operation {operation_id}: {e}")
            result.errors.append(ImportExportValidationError(
                field="import_operation",
                message=f"Import operation failed: {str(e)}",
                error_type=ImportErrorType.BUSINESS_RULE_VIOLATION
            ))
            result.execution_time = time.time() - start_time
            
            # Attempt cleanup
            try:
                if operation_id in self._transaction_contexts:
                    self.rollback_transaction(operation_id)
            except Exception as cleanup_error:
                # Log cleanup error
                self.error_logger.log_structured_error(
                    operation_id=operation_id,
                    severity=ErrorSeverity.CRITICAL,
                    category=ErrorCategory.TRANSACTION,
                    error_type=ImportErrorType.BUSINESS_RULE_VIOLATION,
                    message=f"Error during cleanup: {str(cleanup_error)}",
                    user_id=user_id,
                    exception=cleanup_error
                )
                logger.error(f"Error during cleanup: {cleanup_error}")
            
            # Update audit trail for critical failure
            self.audit_manager.update_operation_status(
                operation_id, OperationStatus.FAILED,
                error_count=len(result.errors),
                warning_count=len(result.warnings)
            )
            self.audit_manager.complete_operation(operation_id)
            self.error_logger.finalize_error_report(operation_id)
            
            return result
    
    def _parse_import_file(self, file_path: str, file_format: FileFormat, 
                          options: ImportOptions) -> Optional[Dict[str, List[Dict[str, Any]]]]:
        """
        Parse import file based on format and return structured data.
        
        Args:
            file_path: Path to the file to parse
            file_format: Format of the file
            options: Import options
            
        Returns:
            Dictionary mapping entity types to lists of records, or None if parsing fails
        """
        try:
            if file_format == FileFormat.JSON:
                processor = JSONProcessor(options)
                parse_result = processor.parse_json_file(file_path)
                
                if not parse_result.success:
                    logger.error(f"JSON parsing failed: {len(parse_result.errors)} errors")
                    return None
                
                return parse_result.data
            
            elif file_format == FileFormat.CSV:
                processor = CSVProcessor(options)
                
                # For CSV, we need to determine entity types from options or file structure
                # This is a simplified approach - in production, you might have multiple CSV files
                if len(options.entity_types) == 1:
                    entity_type = options.entity_types[0]
                    parse_result = processor.parse_csv_file(file_path, entity_type)
                    
                    if not parse_result.success:
                        logger.error(f"CSV parsing failed: {len(parse_result.errors)} errors")
                        return None
                    
                    return {entity_type: parse_result.data}
                else:
                    # Multiple entity types - would need multiple files or different approach
                    logger.error("Multiple entity types not supported for single CSV file")
                    return None
            
            else:
                logger.error(f"Unsupported file format: {file_format}")
                return None
        
        except Exception as e:
            logger.error(f"Error parsing import file: {e}")
            return None
    
    def _validate_import_dependencies(self, data: Dict[str, List[Dict[str, Any]]], 
                                    options: ImportOptions) -> List[ImportExportValidationError]:
        """
        Validate dependencies and foreign key references in import data.
        
        Args:
            data: Parsed import data
            options: Import options
            
        Returns:
            List of validation errors
        """
        errors = []
        
        try:
            # Validate that required dependencies exist
            dependency_errors = self.dependency_resolver.validate_dependencies_exist(data)
            for error_msg in dependency_errors:
                errors.append(ImportExportValidationError(
                    field="dependencies",
                    message=error_msg,
                    error_type=ImportErrorType.FOREIGN_KEY_VIOLATION
                ))
            
            # Check for circular dependencies
            try:
                processing_order = self.dependency_resolver.get_processing_order(list(data.keys()))
                logger.debug(f"Processing order determined: {processing_order}")
            except Exception as e:
                errors.append(ImportExportValidationError(
                    field="circular_dependencies",
                    message=f"Circular dependency detected: {str(e)}",
                    error_type=ImportErrorType.CIRCULAR_REFERENCE
                ))
            
            # Validate foreign key references
            reference_map = self.foreign_key_resolver.build_reference_map(data)
            
            for entity_type, records in data.items():
                if entity_type in options.entity_types:
                    fk_errors = self.foreign_key_resolver.validate_foreign_key_references(
                        entity_type, records, reference_map
                    )
                    for error_msg in fk_errors:
                        errors.append(ImportExportValidationError(
                            field="foreign_keys",
                            message=error_msg,
                            error_type=ImportErrorType.FOREIGN_KEY_VIOLATION,
                            entity_type=entity_type
                        ))
        
        except Exception as e:
            logger.error(f"Error validating import dependencies: {e}")
            errors.append(ImportExportValidationError(
                field="dependency_validation",
                message=f"Dependency validation failed: {str(e)}",
                error_type=ImportErrorType.BUSINESS_RULE_VIOLATION
            ))
        
        return errors
    
    def _process_import_data_batched(self, data: Dict[str, List[Dict[str, Any]]], 
                                   options: ImportOptions, operation_id: str,
                                   result: ImportResult) -> bool:
        """
        Process import data in batches with dependency order and comprehensive error handling.
        
        Args:
            data: Parsed import data
            options: Import options
            operation_id: Transaction operation ID
            result: Import result object to update
            
        Returns:
            True if processing successful, False otherwise
        """
        try:
            # Get processing order based on dependencies
            entity_types_to_process = [
                entity_type for entity_type in self.dependency_resolver.get_processing_order()
                if entity_type in data and entity_type in options.entity_types
            ]
            
            logger.info(f"Processing entities in order: {entity_types_to_process}")
            
            # Track created mappings for foreign key resolution
            created_mappings: Dict[str, Dict[str, int]] = {}
            
            # Process each entity type in dependency order
            for entity_type in entity_types_to_process:
                records = data[entity_type]
                if not records:
                    logger.debug(f"No records to process for {entity_type}")
                    continue
                
                logger.info(f"Processing {len(records)} records for {entity_type}")
                
                # Initialize counters for this entity type
                result.records_processed[entity_type] = 0
                result.records_created[entity_type] = 0
                result.records_updated[entity_type] = 0
                result.records_skipped[entity_type] = 0
                
                # Apply conflict resolution before processing
                logger.debug(f"Applying conflict resolution for {entity_type}")
                resolved_records, conflict_errors, conflict_warnings = self.conflict_resolution_manager.process_conflicts(
                    entity_type, records, options.conflict_resolution
                )
                
                # Add conflict resolution results to overall result
                result.errors.extend(conflict_errors)
                result.warnings.extend(conflict_warnings)
                
                # Update record counts for skipped records
                skipped_count = len(records) - len(resolved_records)
                result.records_skipped[entity_type] += skipped_count
                
                if conflict_errors:
                    logger.error(f"Conflict resolution failed for {entity_type}: {len(conflict_errors)} errors")
                    return False
                
                # Process resolved records in batches
                batch_success = self._process_entity_batches(
                    entity_type, resolved_records, options, created_mappings, result, operation_id
                )
                
                if not batch_success:
                    logger.error(f"Failed to process batches for {entity_type}")
                    return False
                
                logger.info(f"Completed processing {entity_type}: "
                          f"processed={result.records_processed[entity_type]}, "
                          f"created={result.records_created[entity_type]}, "
                          f"updated={result.records_updated[entity_type]}, "
                          f"skipped={result.records_skipped[entity_type]}")
            
            # Store created mappings in result for reference
            result.created_mappings = created_mappings
            
            return True
        
        except Exception as e:
            logger.error(f"Error in batched data processing: {e}")
            result.errors.append(ImportExportValidationError(
                field="batch_processing",
                message=f"Batch processing failed: {str(e)}",
                error_type=ImportErrorType.BUSINESS_RULE_VIOLATION
            ))
            return False
    
    def _process_entity_batches(self, entity_type: str, records: List[Dict[str, Any]], 
                              options: ImportOptions, created_mappings: Dict[str, Dict[str, int]],
                              result: ImportResult, operation_id: Optional[str] = None) -> bool:
        """
        Process records for a single entity type in batches.
        
        Args:
            entity_type: Type of entity being processed
            records: List of records to process
            options: Import options
            created_mappings: Dictionary to track created ID mappings
            result: Import result object to update
            
        Returns:
            True if all batches processed successfully, False otherwise
        """
        try:
            batch_size = options.batch_size
            total_records = len(records)
            
            logger.debug(f"Processing {total_records} {entity_type} records in batches of {batch_size}")
            
            # Initialize entity mappings
            if entity_type not in created_mappings:
                created_mappings[entity_type] = {}
            
            # Process records in batches
            for batch_start in range(0, total_records, batch_size):
                batch_end = min(batch_start + batch_size, total_records)
                batch_records = records[batch_start:batch_end]
                
                logger.debug(f"Processing batch {batch_start//batch_size + 1} "
                           f"({batch_start+1}-{batch_end} of {total_records}) for {entity_type}")
                
                # Process this batch
                batch_result = self._process_record_batch(
                    entity_type, batch_records, options, created_mappings, operation_id
                )
                
                # Update result counters
                result.records_processed[entity_type] += batch_result.processed_count
                result.records_created[entity_type] += batch_result.created_count
                result.records_updated[entity_type] += batch_result.updated_count
                result.records_skipped[entity_type] += batch_result.skipped_count
                
                # Collect errors and warnings
                result.errors.extend(batch_result.errors)
                result.warnings.extend(batch_result.warnings)
                
                # Check if we should stop due to too many errors
                if len(result.errors) >= options.max_errors:
                    logger.warning(f"Maximum error limit ({options.max_errors}) reached, stopping processing")
                    result.warnings.append(ImportExportValidationError(
                        field="error_limit",
                        message=f"Maximum error limit reached ({options.max_errors}), processing stopped",
                        error_type=ImportErrorType.BUSINESS_RULE_VIOLATION,
                        entity_type=entity_type
                    ))
                    return False
                
                # If batch failed completely, stop processing
                if not batch_result.success:
                    logger.error(f"Batch processing failed for {entity_type}")
                    return False
            
            return True
        
        except Exception as e:
            logger.error(f"Error processing entity batches for {entity_type}: {e}")
            result.errors.append(ImportExportValidationError(
                field="entity_batch_processing",
                message=f"Entity batch processing failed for {entity_type}: {str(e)}",
                error_type=ImportErrorType.BUSINESS_RULE_VIOLATION,
                entity_type=entity_type
            ))
            return False
    
    def _process_record_batch(self, entity_type: str, records: List[Dict[str, Any]], 
                            options: ImportOptions, created_mappings: Dict[str, Dict[str, int]],
                            operation_id: Optional[str] = None) -> BatchResult:
        """
        Process a single batch of records for an entity type.
        
        Args:
            entity_type: Type of entity being processed
            records: List of records in this batch
            options: Import options
            created_mappings: Dictionary to track created ID mappings
            
        Returns:
            BatchResult with processing statistics and errors
        """
        batch_result = BatchResult(success=True)
        
        try:
            logger.debug(f"Processing batch of {len(records)} {entity_type} records")
            
            for record_index, record in enumerate(records):
                try:
                    # Resolve foreign key references
                    resolved_record = self.foreign_key_resolver.resolve_foreign_keys(
                        entity_type, record, created_mappings
                    )
                    
                    # Process the record based on conflict resolution strategy
                    # Calculate line number for error reporting (assuming records are processed in order)
                    line_number = i + 1 if i is not None else None
                    
                    processing_result = self._process_single_record(
                        entity_type, resolved_record, options, created_mappings,
                        operation_id, line_number
                    )
                    
                    # Update batch statistics
                    batch_result.processed_count += 1
                    
                    if processing_result['action'] == 'created':
                        batch_result.created_count += 1
                        batch_result.created_ids.append(processing_result['id'])
                        
                        # Track mapping for foreign key resolution
                        if 'temp_id' in record:
                            created_mappings[entity_type][str(record['temp_id'])] = processing_result['id']
                        elif 'id' in record:
                            created_mappings[entity_type][str(record['id'])] = processing_result['id']
                    
                    elif processing_result['action'] == 'updated':
                        batch_result.updated_count += 1
                    
                    elif processing_result['action'] == 'skipped':
                        batch_result.skipped_count += 1
                
                except Exception as record_error:
                    logger.error(f"Error processing record {record_index + 1} in {entity_type}: {record_error}")
                    batch_result.errors.append(ImportExportValidationError(
                        field="record_processing",
                        message=f"Failed to process record: {str(record_error)}",
                        error_type=ImportErrorType.BUSINESS_RULE_VIOLATION,
                        entity_type=entity_type,
                        line_number=record_index + 1
                    ))
                    
                    # Continue processing other records unless it's a critical error
                    if len(batch_result.errors) >= 10:  # Limit errors per batch
                        logger.warning("Too many errors in batch, stopping batch processing")
                        batch_result.success = False
                        break
        
        except Exception as e:
            logger.error(f"Critical error in batch processing: {e}")
            batch_result.success = False
            batch_result.errors.append(ImportExportValidationError(
                field="batch_processing",
                message=f"Batch processing failed: {str(e)}",
                error_type=ImportErrorType.BUSINESS_RULE_VIOLATION,
                entity_type=entity_type
            ))
        
        return batch_result
    
    def _get_service_for_entity(self, entity_type: str):
        """
        Get the appropriate service instance for an entity type.
        
        Args:
            entity_type: Type of entity
            
        Returns:
            Service instance for the entity type
            
        Raises:
            ImportExportException: If no service is available for the entity type
        """
        try:
            if entity_type == "unit_types":
                from .unit_type import UnitTypeService
                return UnitTypeService()
            elif entity_type == "unit_type_themes":
                from .unit_type_theme import UnitTypeThemeService
                return UnitTypeThemeService()
            elif entity_type == "units":
                from .unit import UnitService
                return UnitService()
            elif entity_type == "job_titles":
                from .job_title import JobTitleService
                return JobTitleService()
            elif entity_type == "persons":
                from .person import PersonService
                return PersonService()
            elif entity_type == "assignments":
                from .assignment import AssignmentService
                return AssignmentService()
            else:
                raise ImportExportException(f"No service available for entity type: {entity_type}")
        
        except ImportError as e:
            logger.error(f"Failed to import service for {entity_type}: {e}")
            raise ImportExportException(f"Service not available for {entity_type}: {str(e)}")
    
    def _convert_dict_to_model(self, entity_type: str, record: Dict[str, Any]):
        """
        Convert dictionary record to model instance.
        
        Args:
            entity_type: Type of entity
            record: Dictionary containing record data
            
        Returns:
            Model instance
            
        Raises:
            ImportExportException: If conversion fails
        """
        try:
            # Get entity mapping for field validation and transformation
            from ..models.entity_mappings import get_entity_mapping
            mapping = get_entity_mapping(entity_type)
            
            # Transform and validate fields
            transformed_record = {}
            for field_name, field_mapping in mapping.fields.items():
                if field_name in record:
                    value = record[field_name]
                    # Apply field transformation if available
                    transformed_value = field_mapping.transform(value)
                    transformed_record[field_name] = transformed_value
                elif field_mapping.required:
                    if field_mapping.default_value is not None:
                        transformed_record[field_name] = field_mapping.default_value
                    else:
                        raise ImportExportException(f"Missing required field: {field_name}")
            
            # Get model class and create instance
            if entity_type == "unit_types":
                from ..models.unit_type import UnitType
                return UnitType.from_dict(transformed_record)
            elif entity_type == "unit_type_themes":
                from ..models.unit_type_theme import UnitTypeTheme
                return UnitTypeTheme.from_dict(transformed_record)
            elif entity_type == "units":
                from ..models.unit import Unit
                return Unit.from_dict(transformed_record)
            elif entity_type == "job_titles":
                from ..models.job_title import JobTitle
                return JobTitle.from_dict(transformed_record)
            elif entity_type == "persons":
                from ..models.person import Person
                return Person.from_dict(transformed_record)
            elif entity_type == "assignments":
                from ..models.assignment import Assignment
                return Assignment.from_dict(transformed_record)
            else:
                raise ImportExportException(f"Unknown entity type: {entity_type}")
        
        except Exception as e:
            logger.error(f"Error converting dict to model for {entity_type}: {e}")
            raise ImportExportException(f"Failed to convert record to {entity_type} model: {str(e)}")
    
    def _find_existing_record(self, entity_type: str, record: Dict[str, Any], service) -> Optional[Any]:
        """
        Find existing record based on unique constraints.
        
        Args:
            entity_type: Type of entity
            record: Record data to check
            service: Service instance for the entity
            
        Returns:
            Existing model instance if found, None otherwise
        """
        try:
            from ..models.entity_mappings import get_entity_mapping
            mapping = get_entity_mapping(entity_type)
            
            # Check unique constraints to find existing records
            for constraint_fields in mapping.unique_constraints:
                constraint_values = {}
                has_all_fields = True
                
                for field_name in constraint_fields:
                    if field_name in record and record[field_name] is not None:
                        constraint_values[field_name] = record[field_name]
                    else:
                        has_all_fields = False
                        break
                
                if has_all_fields and constraint_values:
                    # Try to find existing record using this constraint
                    # This is a simplified approach - in production, you'd have specific search methods
                    all_records = service.get_all()
                    for existing_record in all_records:
                        match = True
                        for field_name, value in constraint_values.items():
                            if getattr(existing_record, field_name, None) != value:
                                match = False
                                break
                        if match:
                            return existing_record
            
            return None
        
        except Exception as e:
            logger.error(f"Error finding existing record for {entity_type}: {e}")
            return None
    
    def _process_single_record(self, entity_type: str, record: Dict[str, Any], 
                             options: ImportOptions, created_mappings: Dict[str, Dict[str, int]],
                             operation_id: Optional[str] = None, line_number: Optional[int] = None) -> Dict[str, Any]:
        """
        Process a single record with conflict resolution and proper service integration.
        
        This method implements the core import logic for individual records:
        1. Convert dictionary to model instance
        2. Check for existing records based on unique constraints
        3. Apply conflict resolution strategy (skip, update, create_version)
        4. Create or update record using appropriate service
        5. Handle assignment versioning for assignments entity type
        
        Args:
            entity_type: Type of entity being processed
            record: Record data to process
            options: Import options including conflict resolution strategy
            created_mappings: Dictionary to track created ID mappings
            
        Returns:
            Dictionary with processing result information including:
            - action: 'created', 'updated', or 'skipped'
            - id: ID of the processed record
            - entity_type: Type of entity processed
            - version: For assignments, the version number
            
        Raises:
            ImportExportException: If record processing fails
        """
        try:
            logger.debug(f"Processing {entity_type} record with conflict resolution: {options.conflict_resolution.value}")
            
            # Step 1: Get appropriate service for this entity type
            service = self._get_service_for_entity(entity_type)
            
            # Step 2: Convert dictionary to model instance with field transformation
            model = self._convert_dict_to_model(entity_type, record)
            
            # Step 3: Check for existing records based on unique constraints
            existing_record = self._find_existing_record(entity_type, record, service)
            
            # Step 4: Apply conflict resolution strategy
            if existing_record:
                logger.debug(f"Found existing {entity_type} record with ID {existing_record.id}")
                
                if options.conflict_resolution == ConflictResolutionStrategy.SKIP:
                    logger.debug(f"Skipping existing {entity_type} record (ID: {existing_record.id})")
                    
                    # Track data change for audit trail
                    if operation_id:
                        self.audit_manager.track_data_change(
                            operation_id=operation_id,
                            entity_type=entity_type,
                            change_type=ChangeType.SKIP,
                            entity_id=existing_record.id,
                            old_values=existing_record.__dict__ if hasattr(existing_record, '__dict__') else None,
                            line_number=line_number
                        )
                    
                    return {
                        'action': 'skipped',
                        'id': existing_record.id,
                        'entity_type': entity_type,
                        'reason': 'duplicate_record'
                    }
                
                elif options.conflict_resolution == ConflictResolutionStrategy.UPDATE:
                    logger.debug(f"Updating existing {entity_type} record (ID: {existing_record.id})")
                    
                    # Capture old values for audit trail
                    old_values = existing_record.__dict__ if hasattr(existing_record, '__dict__') else None
                    
                    # Update the existing record with new data
                    model.id = existing_record.id
                    updated_record = service.update(model)
                    
                    # Track data change for audit trail
                    if operation_id:
                        self.audit_manager.track_data_change(
                            operation_id=operation_id,
                            entity_type=entity_type,
                            change_type=ChangeType.UPDATE,
                            entity_id=updated_record.id,
                            old_values=old_values,
                            new_values=updated_record.__dict__ if hasattr(updated_record, '__dict__') else None,
                            line_number=line_number
                        )
                    
                    return {
                        'action': 'updated',
                        'id': updated_record.id,
                        'entity_type': entity_type
                    }
                
                elif options.conflict_resolution == ConflictResolutionStrategy.CREATE_VERSION:
                    if entity_type == "assignments":
                        logger.debug(f"Creating new version for existing assignment (ID: {existing_record.id})")
                        
                        # Capture old values for audit trail
                        old_values = existing_record.__dict__ if hasattr(existing_record, '__dict__') else None
                        
                        # For assignments, create a new version
                        # First, mark existing assignment as not current
                        existing_record.is_current = False
                        service.update(existing_record)
                        
                        # Create new version with incremented version number
                        model.version = existing_record.version + 1
                        model.is_current = True
                        model.id = None  # Ensure new record is created
                        
                        created_record = service.create(model)
                        
                        # Track data change for audit trail
                        if operation_id:
                            self.audit_manager.track_data_change(
                                operation_id=operation_id,
                                entity_type=entity_type,
                                change_type=ChangeType.CREATE,
                                entity_id=created_record.id,
                                old_values=old_values,
                                new_values=created_record.__dict__ if hasattr(created_record, '__dict__') else None,
                                line_number=line_number
                            )
                        
                        return {
                            'action': 'created',
                            'id': created_record.id,
                            'entity_type': entity_type,
                            'version': created_record.version
                        }
                    else:
                        # For non-assignment entities, create_version behaves like update
                        logger.debug(f"Creating version not supported for {entity_type}, updating instead")
                        
                        # Capture old values for audit trail
                        old_values = existing_record.__dict__ if hasattr(existing_record, '__dict__') else None
                        
                        model.id = existing_record.id
                        updated_record = service.update(model)
                        
                        # Track data change for audit trail
                        if operation_id:
                            self.audit_manager.track_data_change(
                                operation_id=operation_id,
                                entity_type=entity_type,
                                change_type=ChangeType.UPDATE,
                                entity_id=updated_record.id,
                                old_values=old_values,
                                new_values=updated_record.__dict__ if hasattr(updated_record, '__dict__') else None,
                                line_number=line_number
                            )
                        
                        return {
                            'action': 'updated',
                            'id': updated_record.id,
                            'entity_type': entity_type
                        }
            
            else:
                # Step 5: No existing record found, create new record
                logger.debug(f"Creating new {entity_type} record")
                
                # Ensure ID is not set for new records
                model.id = None
                
                # For assignments, ensure proper versioning
                if entity_type == "assignments":
                    if not hasattr(model, 'version') or model.version is None:
                        model.version = 1
                    if not hasattr(model, 'is_current') or model.is_current is None:
                        model.is_current = True
                
                created_record = service.create(model)
                
                # Track data change for audit trail
                if operation_id:
                    self.audit_manager.track_data_change(
                        operation_id=operation_id,
                        entity_type=entity_type,
                        change_type=ChangeType.CREATE,
                        entity_id=created_record.id,
                        new_values=created_record.__dict__ if hasattr(created_record, '__dict__') else None,
                        line_number=line_number
                    )
                
                return {
                    'action': 'created',
                    'id': created_record.id,
                    'entity_type': entity_type,
                    'version': getattr(created_record, 'version', None)
                }
        
        except Exception as e:
            logger.error(f"Error processing single {entity_type} record: {e}")
            raise ImportExportException(f"Failed to process {entity_type} record: {str(e)}")
    
    def get_import_statistics(self, result: ImportResult) -> Dict[str, Any]:
        """
        Generate comprehensive statistics from import result.
        
        Args:
            result: Import result object
            
        Returns:
            Dictionary containing detailed import statistics
        """
        return {
            "success": result.success,
            "execution_time": result.execution_time,
            "total_processed": result.total_processed,
            "total_created": result.total_created,
            "total_updated": result.total_updated,
            "total_skipped": result.total_skipped,
            "error_count": len(result.errors),
            "warning_count": len(result.warnings),
            "entity_statistics": {
                entity_type: {
                    "processed": result.records_processed.get(entity_type, 0),
                    "created": result.records_created.get(entity_type, 0),
                    "updated": result.records_updated.get(entity_type, 0),
                    "skipped": result.records_skipped.get(entity_type, 0)
                }
                for entity_type in set(
                    list(result.records_processed.keys()) +
                    list(result.records_created.keys()) +
                    list(result.records_updated.keys()) +
                    list(result.records_skipped.keys())
                )
            },
            "files_processed": result.imported_files,
            "has_errors": result.has_errors,
            "has_warnings": result.has_warnings
        }
    
    def export_data(self, export_format: FileFormat, options: ExportOptions) -> ExportResult:
        """
        Main export orchestration method that generates data files with filtering,
        date range support, and comprehensive error handling.
        
        This method implements Requirements 2.1, 2.2, 6.1, 6.2 by providing:
        - Data export in dependency order
        - Support for CSV and JSON formats
        - Date range filtering for historical data
        - Scheduled export functionality support
        - Comprehensive error reporting
        
        Args:
            export_format: Format for export (CSV or JSON)
            options: Export configuration options
            
        Returns:
            ExportResult with detailed export information
            
        Raises:
            ImportExportException: If critical export operation fails
        """
        import uuid
        import time
        from datetime import datetime
        
        # Generate unique operation ID for tracking
        operation_id = str(uuid.uuid4())
        start_time = time.time()
        
        logger.info(f"Starting export operation {operation_id} in {export_format.value} format")
        
        # Initialize result object
        result = ExportResult(
            success=False,
            execution_time=0.0,
            export_metadata={
                "operation_id": operation_id,
                "export_format": export_format.value,
                "start_time": datetime.now().isoformat(),
                "options": {
                    "entity_types": options.entity_types,
                    "include_historical": options.include_historical,
                    "date_range": [d.isoformat() if d else None for d in options.date_range] if options.date_range else None
                }
            }
        )
        
        try:
            # Step 1: Validate export options
            logger.debug("Validating export options")
            validation_errors = self._validate_export_options(options)
            if validation_errors:
                result.errors.extend(validation_errors)
                result.execution_time = time.time() - start_time
                logger.error(f"Export options validation failed: {len(validation_errors)} errors")
                return result
            
            # Step 2: Retrieve data from database with filtering
            logger.debug("Retrieving data from database")
            export_data = self._retrieve_export_data(options)
            
            if not export_data or not any(export_data.values()):
                result.warnings.append(ImportExportValidationError(
                    field="data_retrieval",
                    message="No data found matching export criteria",
                    error_type=ImportErrorType.BUSINESS_RULE_VIOLATION
                ))
                result.success = True  # Not an error, just no data
                result.execution_time = time.time() - start_time
                logger.info("Export completed with no data to export")
                return result
            
            # Step 3: Apply date range filtering if specified
            if options.date_range:
                logger.debug(f"Applying date range filter: {options.date_range}")
                export_data = self._apply_date_range_filter(export_data, options)
            
            # Step 4: Generate export files based on format
            logger.info(f"Generating {export_format.value} export files")
            generated_files = self._generate_export_files(export_data, export_format, options)
            
            if not generated_files:
                result.errors.append(ImportExportValidationError(
                    field="file_generation",
                    message="Failed to generate export files",
                    error_type=ImportErrorType.BUSINESS_RULE_VIOLATION
                ))
                result.execution_time = time.time() - start_time
                return result
            
            # Step 5: Update result with export information
            result.exported_files = generated_files
            result.records_exported = {
                entity_type: len(records) for entity_type, records in export_data.items()
            }
            
            # Calculate file sizes
            result.file_sizes = self._calculate_file_sizes(generated_files)
            
            # Update metadata
            result.export_metadata.update({
                "end_time": datetime.now().isoformat(),
                "total_records": sum(result.records_exported.values()),
                "total_files": len(generated_files),
                "total_size_bytes": result.total_file_size
            })
            
            result.success = True
            result.execution_time = time.time() - start_time
            
            logger.info(f"Export operation {operation_id} completed successfully in {result.execution_time:.2f}s")
            logger.info(f"Exported {result.total_exported} records to {len(generated_files)} files")
            
            return result
        
        except Exception as e:
            logger.error(f"Critical error in export operation {operation_id}: {e}")
            result.errors.append(ImportExportValidationError(
                field="export_operation",
                message=f"Export operation failed: {str(e)}",
                error_type=ImportErrorType.BUSINESS_RULE_VIOLATION
            ))
            result.execution_time = time.time() - start_time
            return result
    
    def _validate_export_options(self, options: ExportOptions) -> List[ImportExportValidationError]:
        """
        Validate export options for consistency and feasibility.
        
        Args:
            options: Export configuration options
            
        Returns:
            List of validation errors
        """
        errors = []
        
        try:
            # Validate entity types
            valid_entities = {'unit_types', 'unit_type_themes', 'units', 'job_titles', 'persons', 'assignments'}
            invalid_entities = set(options.entity_types) - valid_entities
            if invalid_entities:
                errors.append(ImportExportValidationError(
                    field="entity_types",
                    message=f"Invalid entity types: {invalid_entities}",
                    error_type=ImportErrorType.BUSINESS_RULE_VIOLATION
                ))
            
            # Validate date range
            if options.date_range:
                start_date, end_date = options.date_range
                if start_date > end_date:
                    errors.append(ImportExportValidationError(
                        field="date_range",
                        message="Start date must be before end date",
                        error_type=ImportErrorType.BUSINESS_RULE_VIOLATION
                    ))
            
            # Validate output directory if specified
            if options.output_directory:
                import os
                if not os.path.exists(options.output_directory):
                    try:
                        os.makedirs(options.output_directory, exist_ok=True)
                    except Exception as e:
                        errors.append(ImportExportValidationError(
                            field="output_directory",
                            message=f"Cannot create output directory: {str(e)}",
                            error_type=ImportErrorType.FILE_FORMAT_ERROR
                        ))
        
        except Exception as e:
            logger.error(f"Error validating export options: {e}")
            errors.append(ImportExportValidationError(
                field="options_validation",
                message=f"Options validation failed: {str(e)}",
                error_type=ImportErrorType.BUSINESS_RULE_VIOLATION
            ))
        
        return errors
    
    def _retrieve_export_data(self, options: ExportOptions) -> Dict[str, List[Dict[str, Any]]]:
        """
        Retrieve data from database for export in dependency order.
        
        Args:
            options: Export configuration options
            
        Returns:
            Dictionary mapping entity types to lists of records
        """
        export_data = {}
        
        try:
            # Process entities in dependency order to maintain referential integrity
            entity_types_to_export = [
                entity_type for entity_type in self.dependency_resolver.get_processing_order()
                if entity_type in options.entity_types
            ]
            
            logger.debug(f"Retrieving data for entities in order: {entity_types_to_export}")
            
            for entity_type in entity_types_to_export:
                logger.debug(f"Retrieving data for {entity_type}")
                
                try:
                    # Get service for entity type
                    service = self._get_service_for_entity_type(entity_type)
                    
                    # Retrieve all records for the entity type
                    records = service.get_all()
                    
                    # Convert models to dictionaries for export
                    record_dicts = []
                    for record in records:
                        record_dict = self._model_to_export_dict(entity_type, record)
                        record_dicts.append(record_dict)
                    
                    export_data[entity_type] = record_dicts
                    logger.debug(f"Retrieved {len(record_dicts)} records for {entity_type}")
                
                except Exception as e:
                    logger.error(f"Error retrieving data for {entity_type}: {e}")
                    # Continue with other entity types
                    export_data[entity_type] = []
            
            return export_data
        
        except Exception as e:
            logger.error(f"Error retrieving export data: {e}")
            return {}
    
    def _apply_date_range_filter(self, data: Dict[str, List[Dict[str, Any]]], 
                                options: ExportOptions) -> Dict[str, List[Dict[str, Any]]]:
        """
        Apply date range filtering to export data.
        
        Args:
            data: Export data to filter
            options: Export options containing date range
            
        Returns:
            Filtered export data
        """
        if not options.date_range:
            return data
        
        start_date, end_date = options.date_range
        filtered_data = {}
        
        try:
            for entity_type, records in data.items():
                filtered_records = []
                
                for record in records:
                    # Apply date filtering based on entity type
                    if self._record_matches_date_range(entity_type, record, start_date, end_date):
                        filtered_records.append(record)
                
                filtered_data[entity_type] = filtered_records
                logger.debug(f"Date filter: {entity_type} {len(records)} -> {len(filtered_records)} records")
            
            return filtered_data
        
        except Exception as e:
            logger.error(f"Error applying date range filter: {e}")
            return data
    
    def _record_matches_date_range(self, entity_type: str, record: Dict[str, Any], 
                                  start_date: date, end_date: date) -> bool:
        """
        Check if a record matches the specified date range.
        
        Args:
            entity_type: Type of entity
            record: Record to check
            start_date: Start of date range
            end_date: End of date range
            
        Returns:
            True if record matches date range
        """
        try:
            from datetime import datetime
            
            # Define date fields for each entity type
            date_fields = {
                'unit_types': ['start_date', 'end_date'],
                'unit_type_themes': [],  # No date filtering for themes
                'units': ['start_date', 'end_date'],
                'job_titles': ['start_date', 'end_date'],
                'persons': [],  # No date filtering for persons
                'assignments': ['valid_from', 'valid_to']
            }
            
            fields_to_check = date_fields.get(entity_type, [])
            if not fields_to_check:
                return True  # Include all records if no date fields
            
            # Check if any date field overlaps with the specified range
            for field in fields_to_check:
                if field in record and record[field]:
                    try:
                        if isinstance(record[field], str):
                            record_date = datetime.strptime(record[field], '%Y-%m-%d').date()
                        else:
                            record_date = record[field]
                        
                        # Check if record date falls within range
                        if start_date <= record_date <= end_date:
                            return True
                    except (ValueError, TypeError):
                        continue
            
            return False
        
        except Exception as e:
            logger.error(f"Error checking date range for {entity_type}: {e}")
            return True  # Include record if date check fails
    
    def _generate_export_files(self, data: Dict[str, List[Dict[str, Any]]], 
                              export_format: FileFormat, options: ExportOptions) -> List[str]:
        """
        Generate export files based on format and options.
        
        Args:
            data: Export data
            export_format: Format for export files
            options: Export configuration options
            
        Returns:
            List of generated file paths
        """
        try:
            if export_format == FileFormat.CSV:
                processor = CSVProcessor(options)
                return processor.export_to_csv(data, options)
            
            elif export_format == FileFormat.JSON:
                processor = JSONProcessor(options)
                return processor.export_to_json(data, options)
            
            else:
                logger.error(f"Unsupported export format: {export_format}")
                return []
        
        except Exception as e:
            logger.error(f"Error generating export files: {e}")
            return []
    
    def _calculate_file_sizes(self, file_paths: List[str]) -> Dict[str, int]:
        """
        Calculate file sizes for exported files.
        
        Args:
            file_paths: List of file paths
            
        Returns:
            Dictionary mapping file paths to sizes in bytes
        """
        file_sizes = {}
        
        try:
            import os
            for file_path in file_paths:
                if os.path.exists(file_path):
                    file_sizes[file_path] = os.path.getsize(file_path)
                else:
                    file_sizes[file_path] = 0
        
        except Exception as e:
            logger.error(f"Error calculating file sizes: {e}")
        
        return file_sizes
    
    def _model_to_export_dict(self, entity_type: str, model) -> Dict[str, Any]:
        """
        Convert a model instance to a dictionary for export.
        
        Args:
            entity_type: Type of entity
            model: Model instance to convert
            
        Returns:
            Dictionary representation of the model
        """
        try:
            # Get entity mapping for field conversion
            entity_mapping = get_entity_mapping(entity_type)
            
            # Convert model to dictionary
            if hasattr(model, 'to_dict'):
                record_dict = model.to_dict()
            else:
                # Fallback: use model attributes
                record_dict = {}
                for field_name in entity_mapping.field_mappings.keys():
                    if hasattr(model, field_name):
                        value = getattr(model, field_name)
                        record_dict[field_name] = value
            
            # Apply any export-specific transformations
            return self._transform_record_for_export(entity_type, record_dict)
        
        except Exception as e:
            logger.error(f"Error converting {entity_type} model to dict: {e}")
            return {}
    
    def _transform_record_for_export(self, entity_type: str, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply export-specific transformations to a record.
        
        Args:
            entity_type: Type of entity
            record: Record to transform
            
        Returns:
            Transformed record
        """
        try:
            # Handle date/datetime formatting
            from datetime import date, datetime
            
            for field_name, value in record.items():
                if isinstance(value, datetime):
                    record[field_name] = value.strftime('%Y-%m-%d %H:%M:%S')
                elif isinstance(value, date):
                    record[field_name] = value.strftime('%Y-%m-%d')
            
            return record
        
        except Exception as e:
            logger.error(f"Error transforming record for export: {e}")
            return record
    
    def schedule_export(self, export_format: FileFormat, options: ExportOptions, 
                       schedule_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Schedule an export operation for future execution.
        
        This method implements Requirements 6.1, 6.2 by providing:
        - Scheduled export configuration
        - Background task setup
        - Export file management
        
        Args:
            export_format: Format for export
            options: Export configuration options
            schedule_config: Scheduling configuration (interval, time, etc.)
            
        Returns:
            Dictionary containing schedule information
        """
        import uuid
        from datetime import datetime, timedelta
        
        schedule_id = str(uuid.uuid4())
        
        try:
            logger.info(f"Scheduling export operation {schedule_id}")
            
            # Validate schedule configuration
            required_fields = ['interval', 'start_time']
            missing_fields = [field for field in required_fields if field not in schedule_config]
            if missing_fields:
                raise ImportExportException(f"Missing required schedule fields: {missing_fields}")
            
            # Calculate next execution time
            next_execution = self._calculate_next_execution_time(schedule_config)
            
            # Store schedule configuration (in a real implementation, this would be persisted)
            schedule_info = {
                'schedule_id': schedule_id,
                'export_format': export_format.value,
                'options': options,
                'schedule_config': schedule_config,
                'next_execution': next_execution.isoformat(),
                'created_at': datetime.now().isoformat(),
                'status': 'active'
            }
            
            logger.info(f"Export scheduled with ID {schedule_id}, next execution: {next_execution}")
            
            return schedule_info
        
        except Exception as e:
            logger.error(f"Error scheduling export: {e}")
            raise ImportExportException(f"Failed to schedule export: {str(e)}")
    
    def _calculate_next_execution_time(self, schedule_config: Dict[str, Any]) -> datetime:
        """
        Calculate the next execution time based on schedule configuration.
        
        Args:
            schedule_config: Schedule configuration
            
        Returns:
            Next execution datetime
        """
        from datetime import datetime, timedelta
        
        interval = schedule_config['interval']  # 'daily', 'weekly', 'monthly'
        start_time = schedule_config.get('start_time', '00:00')
        
        now = datetime.now()
        
        if interval == 'daily':
            next_execution = now + timedelta(days=1)
        elif interval == 'weekly':
            next_execution = now + timedelta(weeks=1)
        elif interval == 'monthly':
            next_execution = now + timedelta(days=30)  # Simplified monthly calculation
        else:
            raise ValueError(f"Unsupported interval: {interval}")
        
        # Set the time component
        try:
            hour, minute = map(int, start_time.split(':'))
            next_execution = next_execution.replace(hour=hour, minute=minute, second=0, microsecond=0)
        except ValueError:
            logger.warning(f"Invalid start_time format: {start_time}, using current time")
        
        return next_execution
    
    def export_data_json(self, options: ExportOptions) -> ExportResult:
        """
        Export organizational data to JSON format.
        
        This method implements Requirements 2.1, 2.2, 2.3 by providing:
        - JSON export with structured data format
        - Dependency-aware export ordering
        - Comprehensive metadata inclusion
        
        Args:
            options: Export configuration options
            
        Returns:
            ExportResult with export status and file information
        """
        import time
        
        start_time = time.time()
        operation_id = str(uuid.uuid4())
        
        logger.info(f"Starting JSON export operation: {operation_id}")
        
        # Initialize result
        result = ExportResult(success=False)
        
        try:
            # Create transaction context
            transaction_context = self.create_transaction_context(operation_id)
            
            # Collect data for export
            export_data = {}
            
            # Process entities in dependency order
            ordered_entities = self.dependency_resolver.get_processing_order(options.entity_types)
            
            for entity_type in ordered_entities:
                logger.debug(f"Collecting {entity_type} data for JSON export")
                
                # Get service for entity type
                service = self._get_service_for_entity(entity_type)
                if not service:
                    logger.warning(f"No service found for entity type: {entity_type}")
                    continue
                
                # Collect records
                records = self._collect_export_records(entity_type, service, options)
                export_data[entity_type] = records
                result.records_exported[entity_type] = len(records)
            
            # Generate JSON file using JSONProcessor
            json_processor = JSONProcessor()
            
            # Prepare output path
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{options.file_prefix}_{timestamp}.json"
            output_path = os.path.join(options.output_directory or "exports", filename)
            
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Generate JSON file
            json_file_path = json_processor.generate_json_file(export_data, output_path)
            
            # Calculate file size
            file_size = os.path.getsize(json_file_path)
            
            # Update result
            result.success = True
            result.exported_files = [json_file_path]
            result.file_sizes = {json_file_path: file_size}
            result.execution_time = time.time() - start_time
            
            # Add metadata
            result.export_metadata = {
                'format': 'json',
                'export_date': datetime.now().isoformat(),
                'entity_types': options.entity_types,
                'total_records': sum(result.records_exported.values()),
                'include_historical': options.include_historical,
                'date_range': [options.date_range[0].isoformat(), 
                              options.date_range[1].isoformat()] if options.date_range else None
            }
            
            # Commit transaction
            self.commit_transaction(operation_id)
            
            logger.info(f"JSON export completed successfully: {result.total_exported} records exported to {json_file_path}")
            
            return result
        
        except Exception as e:
            logger.error(f"Error in JSON export operation {operation_id}: {e}")
            
            # Rollback transaction
            try:
                self.rollback_transaction(operation_id)
            except Exception as rollback_error:
                logger.error(f"Error rolling back transaction {operation_id}: {rollback_error}")
            
            # Update result with error
            result.success = False
            result.errors.append(ImportExportValidationError(
                field="json_export",
                message=f"JSON export failed: {str(e)}",
                error_type=ImportErrorType.BUSINESS_RULE_VIOLATION
            ))
            result.execution_time = time.time() - start_time
            
            return result
    
    def export_data_csv(self, options: ExportOptions) -> ExportResult:
        """
        Export organizational data to CSV format.
        
        This method implements Requirements 2.1, 2.2, 2.3 by providing:
        - CSV export with separate files per entity type
        - Dependency-aware export ordering
        - Proper CSV formatting and encoding
        
        Args:
            options: Export configuration options
            
        Returns:
            ExportResult with export status and file information
        """
        import time
        
        start_time = time.time()
        operation_id = str(uuid.uuid4())
        
        logger.info(f"Starting CSV export operation: {operation_id}")
        
        # Initialize result
        result = ExportResult(success=False)
        
        try:
            # Create transaction context
            transaction_context = self.create_transaction_context(operation_id)
            
            # Collect data for export
            export_data = {}
            
            # Process entities in dependency order
            ordered_entities = self.dependency_resolver.get_processing_order(options.entity_types)
            
            for entity_type in ordered_entities:
                logger.debug(f"Collecting {entity_type} data for CSV export")
                
                # Get service for entity type
                service = self._get_service_for_entity(entity_type)
                if not service:
                    logger.warning(f"No service found for entity type: {entity_type}")
                    continue
                
                # Collect records
                records = self._collect_export_records(entity_type, service, options)
                export_data[entity_type] = records
                result.records_exported[entity_type] = len(records)
            
            # Generate CSV files using CSVProcessor
            csv_processor = CSVProcessor()
            
            # Prepare output directory
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = os.path.join(options.output_directory or "exports", f"csv_export_{timestamp}")
            os.makedirs(output_dir, exist_ok=True)
            
            # Generate CSV files (one per entity type)
            csv_files = csv_processor.generate_csv_files(export_data, output_dir)
            
            # Calculate file sizes
            file_sizes = {}
            for file_path in csv_files:
                file_sizes[file_path] = os.path.getsize(file_path)
            
            # Update result
            result.success = True
            result.exported_files = csv_files
            result.file_sizes = file_sizes
            result.execution_time = time.time() - start_time
            
            # Add metadata
            result.export_metadata = {
                'format': 'csv',
                'export_date': datetime.now().isoformat(),
                'entity_types': options.entity_types,
                'total_records': sum(result.records_exported.values()),
                'include_historical': options.include_historical,
                'date_range': [options.date_range[0].isoformat(), 
                              options.date_range[1].isoformat()] if options.date_range else None,
                'files_generated': len(csv_files)
            }
            
            # Commit transaction
            self.commit_transaction(operation_id)
            
            logger.info(f"CSV export completed successfully: {result.total_exported} records exported to {len(csv_files)} files")
            
            return result
        
        except Exception as e:
            logger.error(f"Error in CSV export operation {operation_id}: {e}")
            
            # Rollback transaction
            try:
                self.rollback_transaction(operation_id)
            except Exception as rollback_error:
                logger.error(f"Error rolling back transaction {operation_id}: {rollback_error}")
            
            # Update result with error
            result.success = False
            result.errors.append(ImportExportValidationError(
                field="csv_export",
                message=f"CSV export failed: {str(e)}",
                error_type=ImportErrorType.BUSINESS_RULE_VIOLATION
            ))
            result.execution_time = time.time() - start_time
            
            return result
    
    def _get_service_for_entity(self, entity_type: str):
        """
        Get the appropriate service for an entity type.
        
        Args:
            entity_type: Type of entity
            
        Returns:
            Service instance for the entity type
        """
        from .unit_type import UnitTypeService
        from .unit_type_theme import UnitTypeThemeService
        from .unit import UnitService
        from .job_title import JobTitleService
        from .person import PersonService
        from .assignment import AssignmentService
        
        service_mapping = {
            'unit_types': UnitTypeService,
            'unit_type_themes': UnitTypeThemeService,
            'units': UnitService,
            'job_titles': JobTitleService,
            'persons': PersonService,
            'assignments': AssignmentService
        }
        
        service_class = service_mapping.get(entity_type)
        if service_class:
            return service_class()
        return None
    
    def _collect_export_records(self, entity_type: str, service, options: ExportOptions) -> List[Dict[str, Any]]:
        """
        Collect records for export from the appropriate service.
        
        Args:
            entity_type: Type of entity to collect
            service: Service instance for the entity
            options: Export options
            
        Returns:
            List of records for export
        """
        try:
            # Get all records from service
            if hasattr(service, 'get_all'):
                records = service.get_all()
            elif hasattr(service, 'list_all'):
                records = service.list_all()
            else:
                logger.warning(f"Service for {entity_type} does not have get_all or list_all method")
                return []
            
            # Convert to dictionaries if needed
            export_records = []
            for record in records:
                if hasattr(record, '__dict__'):
                    # Convert dataclass or object to dict
                    record_dict = record.__dict__.copy()
                elif isinstance(record, dict):
                    record_dict = record.copy()
                else:
                    logger.warning(f"Unknown record type for {entity_type}: {type(record)}")
                    continue
                
                # Apply date range filter if specified
                if options.date_range and entity_type == 'assignments':
                    # Filter assignments by date range
                    valid_from = record_dict.get('valid_from')
                    valid_to = record_dict.get('valid_to')
                    
                    if valid_from:
                        if isinstance(valid_from, str):
                            valid_from = date.fromisoformat(valid_from)
                        
                        # Check if assignment overlaps with date range
                        start_date, end_date = options.date_range
                        if valid_to:
                            if isinstance(valid_to, str):
                                valid_to = date.fromisoformat(valid_to)
                            # Assignment has end date - check overlap
                            if valid_to < start_date or valid_from > end_date:
                                continue
                        else:
                            # Assignment is current - check if it started before end date
                            if valid_from > end_date:
                                continue
                
                # Include historical data filter
                if not options.include_historical and entity_type == 'assignments':
                    # Only include current assignments
                    if not record_dict.get('is_current', False):
                        continue
                
                # Convert dates to strings for serialization
                for key, value in record_dict.items():
                    if isinstance(value, (date, datetime)):
                        record_dict[key] = value.isoformat()
                    elif value is None and not options.include_empty_fields:
                        # Remove empty fields if not including them
                        continue
                
                export_records.append(record_dict)
            
            logger.debug(f"Collected {len(export_records)} records for {entity_type}")
            return export_records
        
        except Exception as e:
            logger.error(f"Error collecting records for {entity_type}: {e}")
            return []