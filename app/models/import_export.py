"""
Data models for import/export functionality.

This module defines the core data structures used for importing and exporting
organizational data, including configuration options, results, and validation models.
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any, Union
from pathlib import Path
from .base import ValidationError as BaseValidationError


class ImportErrorType(Enum):
    """Types of errors that can occur during import operations."""
    FILE_FORMAT_ERROR = "file_format_error"
    MISSING_REQUIRED_FIELD = "missing_required_field"
    INVALID_DATA_TYPE = "invalid_data_type"
    FOREIGN_KEY_VIOLATION = "foreign_key_violation"
    DUPLICATE_RECORD = "duplicate_record"
    BUSINESS_RULE_VIOLATION = "business_rule_violation"
    CIRCULAR_REFERENCE = "circular_reference"


class ConflictResolutionStrategy(Enum):
    """Strategies for handling duplicate records during import."""
    SKIP = "skip"
    UPDATE = "update"
    CREATE_VERSION = "create_version"


class FileFormat(Enum):
    """Supported file formats for import/export."""
    CSV = "csv"
    JSON = "json"


@dataclass
class ImportExportValidationError(BaseValidationError):
    """Extended validation error for import/export operations."""
    error_type: ImportErrorType = ImportErrorType.BUSINESS_RULE_VIOLATION
    line_number: Optional[int] = None
    entity_type: Optional[str] = None
    record_id: Optional[Union[int, str]] = None
    
    def __str__(self) -> str:
        """Return a human-readable error message."""
        parts = []
        if self.entity_type:
            parts.append(f"[{self.entity_type}]")
        if self.line_number:
            parts.append(f"Line {self.line_number}")
        if self.field:
            parts.append(f"Field '{self.field}'")
        if self.record_id:
            parts.append(f"Record ID: {self.record_id}")
        
        prefix = " - ".join(parts)
        return f"{prefix}: {self.message}" if prefix else self.message


@dataclass
class ImportOptions:
    """Configuration options for import operations."""
    entity_types: List[str]
    conflict_resolution: ConflictResolutionStrategy = ConflictResolutionStrategy.SKIP
    validate_only: bool = False
    batch_size: int = 100
    skip_validation: bool = False
    create_missing_references: bool = False
    import_historical_data: bool = True
    date_format: str = "%Y-%m-%d"
    datetime_format: str = "%Y-%m-%d %H:%M:%S"
    encoding: str = "utf-8"
    csv_delimiter: str = ","
    csv_quote_char: str = '"'
    max_errors: int = 1000
    
    def __post_init__(self):
        """Validate import options after initialization."""
        if not self.entity_types:
            raise ValueError("At least one entity type must be specified")
        
        valid_entities = {
            'unit_types', 'unit_type_themes', 'units', 
            'job_titles', 'persons', 'assignments'
        }
        invalid_entities = set(self.entity_types) - valid_entities
        if invalid_entities:
            raise ValueError(f"Invalid entity types: {invalid_entities}")


@dataclass
class ExportOptions:
    """Configuration options for export operations."""
    entity_types: List[str]
    include_historical: bool = True
    date_range: Optional[Tuple[date, date]] = None
    format_options: Dict[str, Any] = field(default_factory=dict)
    output_directory: Optional[str] = None
    file_prefix: str = "orgchart_export"
    include_metadata: bool = True
    compress_output: bool = False
    split_by_entity: bool = True  # For CSV: separate files per entity
    encoding: str = "utf-8"
    csv_delimiter: str = ","
    csv_quote_char: str = '"'
    json_indent: int = 2
    include_empty_fields: bool = False
    
    def __post_init__(self):
        """Validate export options after initialization."""
        if not self.entity_types:
            raise ValueError("At least one entity type must be specified")
        
        valid_entities = {
            'unit_types', 'unit_type_themes', 'units', 
            'job_titles', 'persons', 'assignments'
        }
        invalid_entities = set(self.entity_types) - valid_entities
        if invalid_entities:
            raise ValueError(f"Invalid entity types: {invalid_entities}")
        
        if self.date_range:
            start_date, end_date = self.date_range
            if start_date > end_date:
                raise ValueError("Start date must be before end date")


@dataclass
class ImportResult:
    """Result of an import operation."""
    success: bool
    records_processed: Dict[str, int] = field(default_factory=dict)
    records_created: Dict[str, int] = field(default_factory=dict)
    records_updated: Dict[str, int] = field(default_factory=dict)
    records_skipped: Dict[str, int] = field(default_factory=dict)
    errors: List[ImportExportValidationError] = field(default_factory=list)
    warnings: List[ImportExportValidationError] = field(default_factory=list)
    execution_time: float = 0.0
    imported_files: List[str] = field(default_factory=list)
    created_mappings: Dict[str, Dict[str, int]] = field(default_factory=dict)
    
    @property
    def total_processed(self) -> int:
        """Total number of records processed across all entity types."""
        return sum(self.records_processed.values())
    
    @property
    def total_created(self) -> int:
        """Total number of records created across all entity types."""
        return sum(self.records_created.values())
    
    @property
    def total_updated(self) -> int:
        """Total number of records updated across all entity types."""
        return sum(self.records_updated.values())
    
    @property
    def total_skipped(self) -> int:
        """Total number of records skipped across all entity types."""
        return sum(self.records_skipped.values())
    
    @property
    def has_errors(self) -> bool:
        """Check if there are any errors in the result."""
        return len(self.errors) > 0
    
    @property
    def has_warnings(self) -> bool:
        """Check if there are any warnings in the result."""
        return len(self.warnings) > 0


@dataclass
class ExportResult:
    """Result of an export operation."""
    success: bool
    exported_files: List[str] = field(default_factory=list)
    records_exported: Dict[str, int] = field(default_factory=dict)
    errors: List[ImportExportValidationError] = field(default_factory=list)
    warnings: List[ImportExportValidationError] = field(default_factory=list)
    execution_time: float = 0.0
    file_sizes: Dict[str, int] = field(default_factory=dict)
    export_metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def total_exported(self) -> int:
        """Total number of records exported across all entity types."""
        return sum(self.records_exported.values())
    
    @property
    def total_file_size(self) -> int:
        """Total size of all exported files in bytes."""
        return sum(self.file_sizes.values())
    
    @property
    def has_errors(self) -> bool:
        """Check if there are any errors in the result."""
        return len(self.errors) > 0
    
    @property
    def has_warnings(self) -> bool:
        """Check if there are any warnings in the result."""
        return len(self.warnings) > 0


@dataclass
class PreviewResult:
    """Result of an import preview operation."""
    success: bool
    preview_data: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)
    validation_results: List[ImportExportValidationError] = field(default_factory=list)
    dependency_order: List[str] = field(default_factory=list)
    foreign_key_mappings: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    estimated_processing_time: float = 0.0
    
    @property
    def total_records(self) -> int:
        """Total number of records in preview."""
        return sum(len(records) for records in self.preview_data.values())
    
    @property
    def has_validation_errors(self) -> bool:
        """Check if there are validation errors in preview."""
        return any(error.severity == "error" for error in self.validation_results)


@dataclass
class BatchResult:
    """Result of processing a batch of records."""
    success: bool
    processed_count: int = 0
    created_count: int = 0
    updated_count: int = 0
    skipped_count: int = 0
    errors: List[ImportExportValidationError] = field(default_factory=list)
    warnings: List[ImportExportValidationError] = field(default_factory=list)
    created_ids: List[int] = field(default_factory=list)
    
    @property
    def has_errors(self) -> bool:
        """Check if there are any errors in the batch result."""
        return len(self.errors) > 0


@dataclass
class ValidationResult:
    """Result of data validation operations."""
    is_valid: bool
    errors: List[ImportExportValidationError] = field(default_factory=list)
    warnings: List[ImportExportValidationError] = field(default_factory=list)
    validated_records: int = 0
    
    @property
    def error_count(self) -> int:
        """Number of validation errors."""
        return len(self.errors)
    
    @property
    def warning_count(self) -> int:
        """Number of validation warnings."""
        return len(self.warnings)