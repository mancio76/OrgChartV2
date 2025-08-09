"""
Enhanced error reporting service for import/export operations.

This service provides comprehensive error reporting capabilities including
structured error logging, line-by-line error reporting, error categorization,
and severity levels for detailed troubleshooting and analysis.

Implements Requirements 1.5, 7.1, 7.4, 7.5.
"""

import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field

from ..models.import_export import ImportExportValidationError, ImportErrorType, ImportResult, ExportResult
from ..utils.error_handler import (
    ErrorLogger, StructuredError, ErrorReport, ErrorSeverity, ErrorCategory,
    get_error_logger
)
from .audit_trail import get_audit_manager, OperationType, ChangeType

logger = logging.getLogger(__name__)


@dataclass
class LineErrorSummary:
    """Summary of errors for a specific line in an import file."""
    line_number: int
    entity_type: str
    record_data: Dict[str, Any]
    errors: List[StructuredError] = field(default_factory=list)
    warnings: List[StructuredError] = field(default_factory=list)
    
    @property
    def has_critical_errors(self) -> bool:
        """Check if line has critical errors that prevent processing."""
        return any(error.severity in [ErrorSeverity.CRITICAL, ErrorSeverity.ERROR] 
                  for error in self.errors)
    
    @property
    def error_count(self) -> int:
        """Total number of errors for this line."""
        return len(self.errors)
    
    @property
    def warning_count(self) -> int:
        """Total number of warnings for this line."""
        return len(self.warnings)


@dataclass
class EntityErrorSummary:
    """Summary of errors for a specific entity type."""
    entity_type: str
    total_records: int
    processed_records: int
    failed_records: int
    warning_records: int
    line_errors: Dict[int, LineErrorSummary] = field(default_factory=dict)
    field_error_counts: Dict[str, int] = field(default_factory=dict)
    error_type_counts: Dict[str, int] = field(default_factory=dict)
    
    def add_line_error(self, line_error: LineErrorSummary):
        """Add a line error summary to this entity summary."""
        self.line_errors[line_error.line_number] = line_error
        
        if line_error.has_critical_errors:
            self.failed_records += 1
        elif line_error.warning_count > 0:
            self.warning_records += 1
        
        # Update field error counts
        for error in line_error.errors + line_error.warnings:
            if error.field_name:
                self.field_error_counts[error.field_name] = \
                    self.field_error_counts.get(error.field_name, 0) + 1
            
            # Update error type counts
            error_type = error.error_type.value
            self.error_type_counts[error_type] = \
                self.error_type_counts.get(error_type, 0) + 1
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate for this entity type."""
        if self.total_records == 0:
            return 0.0
        return (self.processed_records - self.failed_records) / self.total_records
    
    @property
    def most_common_errors(self) -> List[Tuple[str, int]]:
        """Get most common error types sorted by frequency."""
        return sorted(self.error_type_counts.items(), key=lambda x: x[1], reverse=True)
    
    @property
    def most_problematic_fields(self) -> List[Tuple[str, int]]:
        """Get most problematic fields sorted by error count."""
        return sorted(self.field_error_counts.items(), key=lambda x: x[1], reverse=True)


@dataclass
class ComprehensiveErrorReport:
    """Comprehensive error report for import/export operations."""
    operation_id: str
    operation_type: str
    start_time: datetime
    end_time: Optional[datetime] = None
    total_records: int = 0
    processed_records: int = 0
    failed_records: int = 0
    warning_records: int = 0
    entity_summaries: Dict[str, EntityErrorSummary] = field(default_factory=dict)
    critical_errors: List[StructuredError] = field(default_factory=list)
    system_errors: List[StructuredError] = field(default_factory=list)
    file_errors: List[StructuredError] = field(default_factory=dict)
    
    @property
    def success_rate(self) -> float:
        """Calculate overall success rate."""
        if self.total_records == 0:
            return 0.0
        return (self.processed_records - self.failed_records) / self.total_records
    
    @property
    def has_critical_issues(self) -> bool:
        """Check if there are critical issues that prevent operation completion."""
        return len(self.critical_errors) > 0 or len(self.system_errors) > 0
    
    def get_error_summary_by_severity(self) -> Dict[str, int]:
        """Get error counts grouped by severity."""
        severity_counts = {
            ErrorSeverity.CRITICAL.value: len(self.critical_errors),
            ErrorSeverity.ERROR.value: 0,
            ErrorSeverity.WARNING.value: 0,
            ErrorSeverity.INFO.value: 0
        }
        
        for entity_summary in self.entity_summaries.values():
            for line_error in entity_summary.line_errors.values():
                for error in line_error.errors:
                    severity_counts[error.severity.value] = \
                        severity_counts.get(error.severity.value, 0) + 1
                for warning in line_error.warnings:
                    severity_counts[warning.severity.value] = \
                        severity_counts.get(warning.severity.value, 0) + 1
        
        return severity_counts
    
    def get_top_error_types(self, limit: int = 10) -> List[Tuple[str, int]]:
        """Get top error types across all entities."""
        error_type_counts = {}
        
        for entity_summary in self.entity_summaries.values():
            for error_type, count in entity_summary.error_type_counts.items():
                error_type_counts[error_type] = error_type_counts.get(error_type, 0) + count
        
        return sorted(error_type_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
    
    def get_recommendations(self) -> List[str]:
        """Generate recommendations based on error patterns."""
        recommendations = []
        
        # Check for common patterns
        top_errors = self.get_top_error_types(5)
        
        for error_type, count in top_errors:
            if error_type == ImportErrorType.MISSING_REQUIRED_FIELD.value:
                recommendations.append(
                    f"Verificare che tutti i campi obbligatori siano presenti nei dati di input "
                    f"({count} errori di campi mancanti rilevati)"
                )
            elif error_type == ImportErrorType.INVALID_DATA_TYPE.value:
                recommendations.append(
                    f"Controllare i formati dei dati, specialmente date e numeri "
                    f"({count} errori di tipo dati rilevati)"
                )
            elif error_type == ImportErrorType.FOREIGN_KEY_VIOLATION.value:
                recommendations.append(
                    f"Verificare che tutti i riferimenti esterni esistano nel database "
                    f"({count} errori di chiavi esterne rilevati)"
                )
            elif error_type == ImportErrorType.DUPLICATE_RECORD.value:
                recommendations.append(
                    f"Considerare l'uso di strategie di risoluzione conflitti per i duplicati "
                    f"({count} record duplicati rilevati)"
                )
        
        # Check success rate
        if self.success_rate < 0.5:
            recommendations.append(
                "Il tasso di successo è molto basso. Considerare la revisione completa dei dati di input."
            )
        elif self.success_rate < 0.8:
            recommendations.append(
                "Il tasso di successo potrebbe essere migliorato. Verificare i problemi più comuni."
            )
        
        return recommendations


class ErrorReportingService:
    """
    Enhanced error reporting service for import/export operations.
    
    This service provides comprehensive error analysis, reporting, and recommendations
    for troubleshooting import/export issues.
    """
    
    def __init__(self):
        """Initialize the error reporting service."""
        self.error_logger = get_error_logger()
        self.audit_manager = get_audit_manager()
        self.active_reports: Dict[str, ComprehensiveErrorReport] = {}
    
    def start_error_tracking(
        self,
        operation_id: str,
        operation_type: str,
        total_records: int = 0
    ) -> ComprehensiveErrorReport:
        """Start comprehensive error tracking for an operation."""
        
        report = ComprehensiveErrorReport(
            operation_id=operation_id,
            operation_type=operation_type,
            start_time=datetime.now(),
            total_records=total_records
        )
        
        self.active_reports[operation_id] = report
        
        # Also start error logging in the error logger
        self.error_logger.create_error_report(operation_id, operation_type)
        
        logger.info(f"Started comprehensive error tracking for operation {operation_id}")
        return report
    
    def track_line_error(
        self,
        operation_id: str,
        line_number: int,
        entity_type: str,
        record_data: Dict[str, Any],
        errors: List[ImportExportValidationError]
    ):
        """Track errors for a specific line in an import file."""
        
        if operation_id not in self.active_reports:
            logger.warning(f"No active error report for operation {operation_id}")
            return
        
        report = self.active_reports[operation_id]
        
        # Ensure entity summary exists
        if entity_type not in report.entity_summaries:
            report.entity_summaries[entity_type] = EntityErrorSummary(
                entity_type=entity_type,
                total_records=0,
                processed_records=0,
                failed_records=0,
                warning_records=0
            )
        
        entity_summary = report.entity_summaries[entity_type]
        
        # Create line error summary
        line_error = LineErrorSummary(
            line_number=line_number,
            entity_type=entity_type,
            record_data=record_data
        )
        
        # Convert validation errors to structured errors and log them
        for error in errors:
            severity = self._map_error_type_to_severity(error.error_type)
            category = self._map_error_type_to_category(error.error_type)
            
            structured_error = self.error_logger.log_structured_error(
                operation_id=operation_id,
                severity=severity,
                category=category,
                error_type=error.error_type,
                message=error.message,
                entity_type=entity_type,
                record_id=record_data.get('id'),
                line_number=line_number,
                field_name=error.field,
                context={'record_data': record_data},
                resolution_hint=self._generate_resolution_hint(error)
            )
            
            if severity in [ErrorSeverity.CRITICAL, ErrorSeverity.ERROR]:
                line_error.errors.append(structured_error)
            else:
                line_error.warnings.append(structured_error)
        
        # Add line error to entity summary
        entity_summary.add_line_error(line_error)
        
        # Update report counters
        if line_error.has_critical_errors:
            report.failed_records += 1
        else:
            report.processed_records += 1
            if line_error.warning_count > 0:
                report.warning_records += 1
    
    def track_system_error(
        self,
        operation_id: str,
        error: Exception,
        context: Optional[Dict[str, Any]] = None
    ):
        """Track a system-level error."""
        
        if operation_id not in self.active_reports:
            logger.warning(f"No active error report for operation {operation_id}")
            return
        
        report = self.active_reports[operation_id]
        
        structured_error = self.error_logger.log_structured_error(
            operation_id=operation_id,
            severity=ErrorSeverity.CRITICAL,
            category=ErrorCategory.SYSTEM,
            error_type=ImportErrorType.BUSINESS_RULE_VIOLATION,
            message=f"System error: {str(error)}",
            context=context or {},
            exception=error,
            resolution_hint="Contattare l'amministratore di sistema per assistenza"
        )
        
        report.system_errors.append(structured_error)
    
    def track_file_error(
        self,
        operation_id: str,
        file_path: str,
        error_message: str,
        error_type: ImportErrorType = ImportErrorType.FILE_FORMAT_ERROR
    ):
        """Track a file-level error."""
        
        if operation_id not in self.active_reports:
            logger.warning(f"No active error report for operation {operation_id}")
            return
        
        report = self.active_reports[operation_id]
        
        structured_error = self.error_logger.log_structured_error(
            operation_id=operation_id,
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.FILE_PROCESSING,
            error_type=error_type,
            message=error_message,
            file_path=file_path,
            resolution_hint=self._generate_file_error_hint(error_type)
        )
        
        report.file_errors.append(structured_error)
    
    def finalize_error_report(self, operation_id: str) -> Optional[ComprehensiveErrorReport]:
        """Finalize comprehensive error report and save to file."""
        
        if operation_id not in self.active_reports:
            logger.warning(f"No active error report for operation {operation_id}")
            return None
        
        report = self.active_reports[operation_id]
        report.end_time = datetime.now()
        
        # Finalize error logger report
        error_logger_report = self.error_logger.finalize_error_report(operation_id)
        
        # Save comprehensive report
        self._save_comprehensive_report(report)
        
        # Remove from active reports
        completed_report = self.active_reports.pop(operation_id)
        
        logger.info(f"Finalized comprehensive error report for operation {operation_id}")
        return completed_report
    
    def get_error_report(self, operation_id: str) -> Optional[ComprehensiveErrorReport]:
        """Get comprehensive error report for an operation."""
        return self.active_reports.get(operation_id)
    
    def generate_error_summary_for_result(
        self,
        operation_id: str,
        result: Union[ImportResult, ExportResult]
    ) -> Dict[str, Any]:
        """Generate error summary for inclusion in operation results."""
        
        report = self.active_reports.get(operation_id)
        if not report:
            return {}
        
        summary = {
            'total_records': report.total_records,
            'processed_records': report.processed_records,
            'failed_records': report.failed_records,
            'warning_records': report.warning_records,
            'success_rate': report.success_rate,
            'has_critical_issues': report.has_critical_issues,
            'error_summary_by_severity': report.get_error_summary_by_severity(),
            'top_error_types': report.get_top_error_types(5),
            'recommendations': report.get_recommendations(),
            'entity_summaries': {}
        }
        
        # Add entity-specific summaries
        for entity_type, entity_summary in report.entity_summaries.items():
            summary['entity_summaries'][entity_type] = {
                'total_records': entity_summary.total_records,
                'processed_records': entity_summary.processed_records,
                'failed_records': entity_summary.failed_records,
                'success_rate': entity_summary.success_rate,
                'most_common_errors': entity_summary.most_common_errors[:3],
                'most_problematic_fields': entity_summary.most_problematic_fields[:3]
            }
        
        return summary
    
    def _map_error_type_to_severity(self, error_type: ImportErrorType) -> ErrorSeverity:
        """Map import error type to severity level."""
        severity_mapping = {
            ImportErrorType.FILE_FORMAT_ERROR: ErrorSeverity.CRITICAL,
            ImportErrorType.MISSING_REQUIRED_FIELD: ErrorSeverity.ERROR,
            ImportErrorType.INVALID_DATA_TYPE: ErrorSeverity.ERROR,
            ImportErrorType.FOREIGN_KEY_VIOLATION: ErrorSeverity.ERROR,
            ImportErrorType.DUPLICATE_RECORD: ErrorSeverity.WARNING,
            ImportErrorType.BUSINESS_RULE_VIOLATION: ErrorSeverity.ERROR,
            ImportErrorType.CIRCULAR_REFERENCE: ErrorSeverity.CRITICAL
        }
        return severity_mapping.get(error_type, ErrorSeverity.ERROR)
    
    def _map_error_type_to_category(self, error_type: ImportErrorType) -> ErrorCategory:
        """Map import error type to category."""
        category_mapping = {
            ImportErrorType.FILE_FORMAT_ERROR: ErrorCategory.FILE_PROCESSING,
            ImportErrorType.MISSING_REQUIRED_FIELD: ErrorCategory.DATA_VALIDATION,
            ImportErrorType.INVALID_DATA_TYPE: ErrorCategory.DATA_VALIDATION,
            ImportErrorType.FOREIGN_KEY_VIOLATION: ErrorCategory.FOREIGN_KEY,
            ImportErrorType.DUPLICATE_RECORD: ErrorCategory.DATA_VALIDATION,
            ImportErrorType.BUSINESS_RULE_VIOLATION: ErrorCategory.BUSINESS_LOGIC,
            ImportErrorType.CIRCULAR_REFERENCE: ErrorCategory.DEPENDENCY
        }
        return category_mapping.get(error_type, ErrorCategory.DATA_VALIDATION)
    
    def _generate_resolution_hint(self, error: ImportExportValidationError) -> str:
        """Generate resolution hint based on error type and context."""
        hints = {
            ImportErrorType.FILE_FORMAT_ERROR: "Verificare il formato del file e la struttura dei dati",
            ImportErrorType.MISSING_REQUIRED_FIELD: f"Aggiungere il campo obbligatorio '{error.field}' al record",
            ImportErrorType.INVALID_DATA_TYPE: f"Verificare il formato del campo '{error.field}' (es. date, numeri)",
            ImportErrorType.FOREIGN_KEY_VIOLATION: f"Verificare che il valore del campo '{error.field}' esista nella tabella di riferimento",
            ImportErrorType.DUPLICATE_RECORD: "Utilizzare strategie di risoluzione conflitti o rimuovere duplicati",
            ImportErrorType.BUSINESS_RULE_VIOLATION: "Verificare che i dati rispettino le regole di business",
            ImportErrorType.CIRCULAR_REFERENCE: "Rimuovere riferimenti circolari nella struttura dei dati"
        }
        return hints.get(error.error_type, "Verificare i dati di input")
    
    def _generate_file_error_hint(self, error_type: ImportErrorType) -> str:
        """Generate resolution hint for file-level errors."""
        if error_type == ImportErrorType.FILE_FORMAT_ERROR:
            return "Verificare che il file sia in formato CSV o JSON valido"
        return "Verificare l'integrità del file"
    
    def _save_comprehensive_report(self, report: ComprehensiveErrorReport):
        """Save comprehensive report to file."""
        try:
            reports_dir = Path("logs/comprehensive_reports")
            reports_dir.mkdir(parents=True, exist_ok=True)
            
            report_file = reports_dir / f"comprehensive_report_{report.operation_id}.json"
            
            # Convert report to dictionary for JSON serialization
            report_data = {
                'operation_id': report.operation_id,
                'operation_type': report.operation_type,
                'start_time': report.start_time.isoformat(),
                'end_time': report.end_time.isoformat() if report.end_time else None,
                'total_records': report.total_records,
                'processed_records': report.processed_records,
                'failed_records': report.failed_records,
                'warning_records': report.warning_records,
                'success_rate': report.success_rate,
                'has_critical_issues': report.has_critical_issues,
                'error_summary_by_severity': report.get_error_summary_by_severity(),
                'top_error_types': report.get_top_error_types(),
                'recommendations': report.get_recommendations(),
                'entity_summaries': {},
                'critical_errors': [error.to_dict() for error in report.critical_errors],
                'system_errors': [error.to_dict() for error in report.system_errors],
                'file_errors': [error.to_dict() for error in report.file_errors]
            }
            
            # Add entity summaries
            for entity_type, entity_summary in report.entity_summaries.items():
                report_data['entity_summaries'][entity_type] = {
                    'entity_type': entity_summary.entity_type,
                    'total_records': entity_summary.total_records,
                    'processed_records': entity_summary.processed_records,
                    'failed_records': entity_summary.failed_records,
                    'warning_records': entity_summary.warning_records,
                    'success_rate': entity_summary.success_rate,
                    'most_common_errors': entity_summary.most_common_errors,
                    'most_problematic_fields': entity_summary.most_problematic_fields,
                    'field_error_counts': entity_summary.field_error_counts,
                    'error_type_counts': entity_summary.error_type_counts,
                    'line_errors': {
                        str(line_num): {
                            'line_number': line_error.line_number,
                            'entity_type': line_error.entity_type,
                            'record_data': line_error.record_data,
                            'error_count': line_error.error_count,
                            'warning_count': line_error.warning_count,
                            'has_critical_errors': line_error.has_critical_errors,
                            'errors': [error.to_dict() for error in line_error.errors],
                            'warnings': [warning.to_dict() for warning in line_error.warnings]
                        }
                        for line_num, line_error in entity_summary.line_errors.items()
                    }
                }
            
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Comprehensive error report saved: {report_file}")
        
        except Exception as e:
            logger.error(f"Failed to save comprehensive error report: {e}")


# Global error reporting service instance
_error_reporting_service = None


def get_error_reporting_service() -> ErrorReportingService:
    """Get global error reporting service instance."""
    global _error_reporting_service
    if _error_reporting_service is None:
        _error_reporting_service = ErrorReportingService()
    return _error_reporting_service