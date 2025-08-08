"""
Enhanced error handling and logging system for import/export operations.

This module provides structured error logging, line-by-line error reporting,
and error categorization with severity levels for comprehensive error tracking.
"""

import logging
import json
import traceback
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field, asdict

from ..models.import_export import ImportExportValidationError, ImportErrorType


class ErrorSeverity(Enum):
    """Error severity levels for categorization."""
    CRITICAL = "critical"  # System-level errors that prevent operation
    ERROR = "error"       # Data errors that prevent record processing
    WARNING = "warning"   # Issues that don't prevent processing
    INFO = "info"         # Informational messages


class ErrorCategory(Enum):
    """Categories for error classification."""
    FILE_PROCESSING = "file_processing"
    DATA_VALIDATION = "data_validation"
    FOREIGN_KEY = "foreign_key"
    BUSINESS_LOGIC = "business_logic"
    SYSTEM = "system"
    TRANSACTION = "transaction"
    DEPENDENCY = "dependency"


@dataclass
class StructuredError:
    """Structured error with comprehensive metadata."""
    error_id: str
    timestamp: datetime
    severity: ErrorSeverity
    category: ErrorCategory
    error_type: ImportErrorType
    message: str
    entity_type: Optional[str] = None
    record_id: Optional[Union[int, str]] = None
    line_number: Optional[int] = None
    field_name: Optional[str] = None
    file_path: Optional[str] = None
    operation_id: Optional[str] = None
    user_id: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    stack_trace: Optional[str] = None
    resolution_hint: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for JSON serialization."""
        data = asdict(self)
        # Convert enums to strings
        data['severity'] = self.severity.value
        data['category'] = self.category.value
        data['error_type'] = self.error_type.value
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    def to_validation_error(self) -> ImportExportValidationError:
        """Convert to ImportExportValidationError for compatibility."""
        return ImportExportValidationError(
            field=self.field_name or "unknown",
            message=self.message,
            severity=self.severity.value,
            error_type=self.error_type,
            line_number=self.line_number,
            entity_type=self.entity_type,
            record_id=self.record_id
        )


@dataclass
class ErrorReport:
    """Comprehensive error report for operations."""
    operation_id: str
    operation_type: str  # 'import' or 'export'
    start_time: datetime
    end_time: Optional[datetime] = None
    total_errors: int = 0
    total_warnings: int = 0
    errors_by_severity: Dict[str, int] = field(default_factory=dict)
    errors_by_category: Dict[str, int] = field(default_factory=dict)
    errors_by_entity: Dict[str, int] = field(default_factory=dict)
    line_errors: Dict[int, List[StructuredError]] = field(default_factory=dict)
    structured_errors: List[StructuredError] = field(default_factory=list)
    
    def add_error(self, error: StructuredError):
        """Add a structured error to the report."""
        self.structured_errors.append(error)
        
        # Update counters
        if error.severity in [ErrorSeverity.CRITICAL, ErrorSeverity.ERROR]:
            self.total_errors += 1
        elif error.severity == ErrorSeverity.WARNING:
            self.total_warnings += 1
        
        # Update severity breakdown
        severity_key = error.severity.value
        self.errors_by_severity[severity_key] = self.errors_by_severity.get(severity_key, 0) + 1
        
        # Update category breakdown
        category_key = error.category.value
        self.errors_by_category[category_key] = self.errors_by_category.get(category_key, 0) + 1
        
        # Update entity breakdown
        if error.entity_type:
            self.errors_by_entity[error.entity_type] = self.errors_by_entity.get(error.entity_type, 0) + 1
        
        # Update line-specific errors
        if error.line_number:
            if error.line_number not in self.line_errors:
                self.line_errors[error.line_number] = []
            self.line_errors[error.line_number].append(error)
    
    def get_errors_by_line(self, line_number: int) -> List[StructuredError]:
        """Get all errors for a specific line number."""
        return self.line_errors.get(line_number, [])
    
    def get_errors_by_entity(self, entity_type: str) -> List[StructuredError]:
        """Get all errors for a specific entity type."""
        return [error for error in self.structured_errors if error.entity_type == entity_type]
    
    def get_critical_errors(self) -> List[StructuredError]:
        """Get all critical errors."""
        return [error for error in self.structured_errors if error.severity == ErrorSeverity.CRITICAL]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary for JSON serialization."""
        return {
            'operation_id': self.operation_id,
            'operation_type': self.operation_type,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'total_errors': self.total_errors,
            'total_warnings': self.total_warnings,
            'errors_by_severity': self.errors_by_severity,
            'errors_by_category': self.errors_by_category,
            'errors_by_entity': self.errors_by_entity,
            'line_errors': {str(k): [e.to_dict() for e in v] for k, v in self.line_errors.items()},
            'structured_errors': [error.to_dict() for error in self.structured_errors]
        }


class ErrorLogger:
    """Enhanced error logger with structured logging capabilities."""
    
    def __init__(self, log_directory: str = "logs"):
        """Initialize error logger with specified log directory."""
        self.log_directory = Path(log_directory)
        self.log_directory.mkdir(exist_ok=True)
        
        # Set up structured logger
        self.logger = logging.getLogger("import_export_errors")
        self.logger.setLevel(logging.DEBUG)
        
        # Create formatters
        self.detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Set up file handler for error logs
        error_log_file = self.log_directory / "import_export_errors.log"
        file_handler = logging.FileHandler(error_log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(self.detailed_formatter)
        
        # Set up console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        console_handler.setFormatter(self.detailed_formatter)
        
        # Add handlers if not already added
        if not self.logger.handlers:
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)
        
        self.error_reports: Dict[str, ErrorReport] = {}
    
    def create_error_report(self, operation_id: str, operation_type: str) -> ErrorReport:
        """Create a new error report for an operation."""
        report = ErrorReport(
            operation_id=operation_id,
            operation_type=operation_type,
            start_time=datetime.now()
        )
        self.error_reports[operation_id] = report
        
        self.logger.info(f"Created error report for operation {operation_id} ({operation_type})")
        return report
    
    def log_structured_error(
        self,
        operation_id: str,
        severity: ErrorSeverity,
        category: ErrorCategory,
        error_type: ImportErrorType,
        message: str,
        entity_type: Optional[str] = None,
        record_id: Optional[Union[int, str]] = None,
        line_number: Optional[int] = None,
        field_name: Optional[str] = None,
        file_path: Optional[str] = None,
        user_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        exception: Optional[Exception] = None,
        resolution_hint: Optional[str] = None
    ) -> StructuredError:
        """Log a structured error with comprehensive metadata."""
        
        # Generate unique error ID
        error_id = f"{operation_id}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        # Capture stack trace if exception provided
        stack_trace = None
        if exception:
            stack_trace = traceback.format_exception(type(exception), exception, exception.__traceback__)
            stack_trace = ''.join(stack_trace)
        
        # Create structured error
        structured_error = StructuredError(
            error_id=error_id,
            timestamp=datetime.now(),
            severity=severity,
            category=category,
            error_type=error_type,
            message=message,
            entity_type=entity_type,
            record_id=record_id,
            line_number=line_number,
            field_name=field_name,
            file_path=file_path,
            operation_id=operation_id,
            user_id=user_id,
            context=context or {},
            stack_trace=stack_trace,
            resolution_hint=resolution_hint
        )
        
        # Add to error report if exists
        if operation_id in self.error_reports:
            self.error_reports[operation_id].add_error(structured_error)
        
        # Log to standard logger
        log_message = self._format_log_message(structured_error)
        
        if severity == ErrorSeverity.CRITICAL:
            self.logger.critical(log_message)
        elif severity == ErrorSeverity.ERROR:
            self.logger.error(log_message)
        elif severity == ErrorSeverity.WARNING:
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)
        
        # Save structured error to JSON file
        self._save_structured_error_to_file(structured_error)
        
        return structured_error
    
    def log_line_error(
        self,
        operation_id: str,
        line_number: int,
        entity_type: str,
        field_name: str,
        error_message: str,
        record_data: Optional[Dict[str, Any]] = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        error_type: ImportErrorType = ImportErrorType.INVALID_DATA_TYPE
    ) -> StructuredError:
        """Log an error specific to a line in an import file."""
        
        context = {}
        if record_data:
            context['record_data'] = record_data
        
        return self.log_structured_error(
            operation_id=operation_id,
            severity=severity,
            category=ErrorCategory.DATA_VALIDATION,
            error_type=error_type,
            message=f"Line {line_number}: {error_message}",
            entity_type=entity_type,
            line_number=line_number,
            field_name=field_name,
            context=context,
            resolution_hint=f"Check data format for field '{field_name}' on line {line_number}"
        )
    
    def finalize_error_report(self, operation_id: str) -> Optional[ErrorReport]:
        """Finalize an error report and save to file."""
        if operation_id not in self.error_reports:
            self.logger.warning(f"No error report found for operation {operation_id}")
            return None
        
        report = self.error_reports[operation_id]
        report.end_time = datetime.now()
        
        # Save report to file
        report_file = self.log_directory / f"error_report_{operation_id}.json"
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Error report saved for operation {operation_id}: {report_file}")
        except Exception as e:
            self.logger.error(f"Failed to save error report for {operation_id}: {e}")
        
        return report
    
    def get_error_report(self, operation_id: str) -> Optional[ErrorReport]:
        """Get error report for an operation."""
        return self.error_reports.get(operation_id)
    
    def _format_log_message(self, error: StructuredError) -> str:
        """Format structured error for standard logging."""
        parts = [f"[{error.operation_id}]"]
        
        if error.entity_type:
            parts.append(f"[{error.entity_type}]")
        
        if error.line_number:
            parts.append(f"[Line {error.line_number}]")
        
        if error.field_name:
            parts.append(f"[{error.field_name}]")
        
        if error.record_id:
            parts.append(f"[ID: {error.record_id}]")
        
        parts.append(error.message)
        
        if error.resolution_hint:
            parts.append(f"Hint: {error.resolution_hint}")
        
        return " ".join(parts)
    
    def _save_structured_error_to_file(self, error: StructuredError):
        """Save individual structured error to JSON file."""
        try:
            error_file = self.log_directory / f"structured_errors_{datetime.now().strftime('%Y%m%d')}.jsonl"
            
            # Append to JSONL file (one JSON object per line)
            with open(error_file, 'a', encoding='utf-8') as f:
                json.dump(error.to_dict(), f, ensure_ascii=False)
                f.write('\n')
        
        except Exception as e:
            self.logger.error(f"Failed to save structured error to file: {e}")


# Global error logger instance
_error_logger = None


def get_error_logger() -> ErrorLogger:
    """Get global error logger instance."""
    global _error_logger
    if _error_logger is None:
        _error_logger = ErrorLogger()
    return _error_logger


def log_import_error(
    operation_id: str,
    message: str,
    entity_type: Optional[str] = None,
    line_number: Optional[int] = None,
    field_name: Optional[str] = None,
    severity: ErrorSeverity = ErrorSeverity.ERROR,
    error_type: ImportErrorType = ImportErrorType.BUSINESS_RULE_VIOLATION,
    **kwargs
) -> StructuredError:
    """Convenience function for logging import errors."""
    logger = get_error_logger()
    return logger.log_structured_error(
        operation_id=operation_id,
        severity=severity,
        category=ErrorCategory.DATA_VALIDATION,
        error_type=error_type,
        message=message,
        entity_type=entity_type,
        line_number=line_number,
        field_name=field_name,
        **kwargs
    )


def log_system_error(
    operation_id: str,
    message: str,
    exception: Optional[Exception] = None,
    **kwargs
) -> StructuredError:
    """Convenience function for logging system errors."""
    logger = get_error_logger()
    return logger.log_structured_error(
        operation_id=operation_id,
        severity=ErrorSeverity.CRITICAL,
        category=ErrorCategory.SYSTEM,
        error_type=ImportErrorType.FILE_FORMAT_ERROR,
        message=message,
        exception=exception,
        **kwargs
    )