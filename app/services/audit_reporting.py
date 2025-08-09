"""
Enhanced audit reporting service for import/export operations.

This service provides comprehensive audit reporting capabilities including
operation history analysis, data change tracking, and compliance reporting.

Implements Requirements 7.1, 7.2, 7.3, 7.5.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum

from .audit_trail import (
    get_audit_manager, AuditTrailManager, OperationType, OperationStatus, ChangeType
)

logger = logging.getLogger(__name__)


class ReportPeriod(Enum):
    """Time periods for audit reports."""
    LAST_24_HOURS = "last_24_hours"
    LAST_WEEK = "last_week"
    LAST_MONTH = "last_month"
    LAST_QUARTER = "last_quarter"
    CUSTOM = "custom"


@dataclass
class OperationSummary:
    """Summary statistics for operations."""
    total_operations: int = 0
    successful_operations: int = 0
    failed_operations: int = 0
    cancelled_operations: int = 0
    total_records_processed: int = 0
    total_records_created: int = 0
    total_records_updated: int = 0
    total_records_skipped: int = 0
    average_duration: float = 0.0
    operations_by_type: Dict[str, int] = field(default_factory=dict)
    operations_by_user: Dict[str, int] = field(default_factory=dict)
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_operations == 0:
            return 0.0
        return (self.successful_operations / self.total_operations) * 100
    
    @property
    def failure_rate(self) -> float:
        """Calculate failure rate percentage."""
        if self.total_operations == 0:
            return 0.0
        return (self.failed_operations / self.total_operations) * 100


@dataclass
class DataChangeSummary:
    """Summary of data changes."""
    total_changes: int = 0
    creates: int = 0
    updates: int = 0
    deletes: int = 0
    skips: int = 0
    changes_by_entity: Dict[str, int] = field(default_factory=dict)
    changes_by_operation: Dict[str, int] = field(default_factory=dict)
    most_active_entities: List[Tuple[str, int]] = field(default_factory=list)
    
    def add_change(self, change_type: ChangeType, entity_type: str, operation_id: str):
        """Add a data change to the summary."""
        self.total_changes += 1
        
        if change_type == ChangeType.CREATE:
            self.creates += 1
        elif change_type == ChangeType.UPDATE:
            self.updates += 1
        elif change_type == ChangeType.DELETE:
            self.deletes += 1
        elif change_type == ChangeType.SKIP:
            self.skips += 1
        
        # Update entity counts
        self.changes_by_entity[entity_type] = self.changes_by_entity.get(entity_type, 0) + 1
        
        # Update operation counts
        self.changes_by_operation[operation_id] = self.changes_by_operation.get(operation_id, 0) + 1
    
    def finalize(self):
        """Finalize the summary by calculating derived statistics."""
        # Sort entities by activity
        self.most_active_entities = sorted(
            self.changes_by_entity.items(), 
            key=lambda x: x[1], 
            reverse=True
        )


@dataclass
class ComplianceReport:
    """Compliance and audit report."""
    report_id: str
    generated_at: datetime
    period_start: datetime
    period_end: datetime
    generated_by: Optional[str] = None
    operation_summary: OperationSummary = field(default_factory=OperationSummary)
    data_change_summary: DataChangeSummary = field(default_factory=DataChangeSummary)
    failed_operations: List[Dict[str, Any]] = field(default_factory=list)
    high_risk_activities: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    @property
    def report_period_days(self) -> int:
        """Calculate the number of days covered by this report."""
        return (self.period_end - self.period_start).days + 1
    
    def add_recommendation(self, recommendation: str):
        """Add a recommendation to the report."""
        if recommendation not in self.recommendations:
            self.recommendations.append(recommendation)


class AuditReportingService:
    """
    Enhanced audit reporting service for import/export operations.
    
    This service provides comprehensive audit analysis and reporting capabilities
    for compliance, monitoring, and operational insights.
    """
    
    def __init__(self):
        """Initialize the audit reporting service."""
        self.audit_manager = get_audit_manager()
    
    def generate_operation_summary(
        self,
        period: ReportPeriod = ReportPeriod.LAST_WEEK,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_id: Optional[str] = None,
        operation_type: Optional[OperationType] = None
    ) -> OperationSummary:
        """Generate summary statistics for operations in the specified period."""
        
        # Calculate date range
        if period == ReportPeriod.CUSTOM:
            if not start_date or not end_date:
                raise ValueError("Custom period requires start_date and end_date")
        else:
            start_date, end_date = self._get_period_dates(period)
        
        # Get operation history
        operations = self.audit_manager.get_operation_history(
            user_id=user_id,
            operation_type=operation_type,
            start_date=start_date,
            end_date=end_date,
            limit=10000  # Large limit to get all operations
        )
        
        # Initialize summary
        summary = OperationSummary()
        summary.total_operations = len(operations)
        
        total_duration = 0.0
        duration_count = 0
        
        for operation in operations:
            # Count by status
            status = operation.get('status', '')
            if status == OperationStatus.COMPLETED.value:
                summary.successful_operations += 1
            elif status == OperationStatus.FAILED.value:
                summary.failed_operations += 1
            elif status == OperationStatus.CANCELLED.value:
                summary.cancelled_operations += 1
            
            # Count by type
            op_type = operation.get('operation_type', 'unknown')
            summary.operations_by_type[op_type] = summary.operations_by_type.get(op_type, 0) + 1
            
            # Count by user
            user = operation.get('user_id', 'unknown')
            summary.operations_by_user[user] = summary.operations_by_user.get(user, 0) + 1
            
            # Aggregate record counts
            records_processed = operation.get('records_processed', {})
            records_created = operation.get('records_created', {})
            records_updated = operation.get('records_updated', {})
            records_skipped = operation.get('records_skipped', {})
            
            if isinstance(records_processed, dict):
                summary.total_records_processed += sum(records_processed.values())
            if isinstance(records_created, dict):
                summary.total_records_created += sum(records_created.values())
            if isinstance(records_updated, dict):
                summary.total_records_updated += sum(records_updated.values())
            if isinstance(records_skipped, dict):
                summary.total_records_skipped += sum(records_skipped.values())
            
            # Calculate average duration
            if operation.get('start_time') and operation.get('end_time'):
                try:
                    start = datetime.fromisoformat(operation['start_time'].replace('Z', '+00:00'))
                    end = datetime.fromisoformat(operation['end_time'].replace('Z', '+00:00'))
                    duration = (end - start).total_seconds()
                    total_duration += duration
                    duration_count += 1
                except (ValueError, TypeError):
                    pass
        
        # Calculate average duration
        if duration_count > 0:
            summary.average_duration = total_duration / duration_count
        
        return summary
    
    def generate_data_change_summary(
        self,
        period: ReportPeriod = ReportPeriod.LAST_WEEK,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        entity_type: Optional[str] = None
    ) -> DataChangeSummary:
        """Generate summary of data changes in the specified period."""
        
        # Calculate date range
        if period == ReportPeriod.CUSTOM:
            if not start_date or not end_date:
                raise ValueError("Custom period requires start_date and end_date")
        else:
            start_date, end_date = self._get_period_dates(period)
        
        # Get operations in the period
        operations = self.audit_manager.get_operation_history(
            start_date=start_date,
            end_date=end_date,
            limit=10000
        )
        
        # Initialize summary
        summary = DataChangeSummary()
        
        # Analyze data changes for each operation
        for operation in operations:
            operation_id = operation.get('operation_id')
            if not operation_id:
                continue
            
            # Get detailed operation information including data changes
            operation_details = self.audit_manager.get_operation_details(operation_id)
            if not operation_details or 'data_changes' not in operation_details:
                continue
            
            # Process data changes
            for change in operation_details['data_changes']:
                change_entity_type = change.get('entity_type')
                change_type_str = change.get('change_type')
                
                # Filter by entity type if specified
                if entity_type and change_entity_type != entity_type:
                    continue
                
                # Convert string to enum
                try:
                    change_type = ChangeType(change_type_str)
                    summary.add_change(change_type, change_entity_type, operation_id)
                except ValueError:
                    logger.warning(f"Unknown change type: {change_type_str}")
        
        # Finalize summary
        summary.finalize()
        
        return summary
    
    def generate_compliance_report(
        self,
        period: ReportPeriod = ReportPeriod.LAST_MONTH,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        generated_by: Optional[str] = None
    ) -> ComplianceReport:
        """Generate comprehensive compliance and audit report."""
        
        # Calculate date range
        if period == ReportPeriod.CUSTOM:
            if not start_date or not end_date:
                raise ValueError("Custom period requires start_date and end_date")
        else:
            start_date, end_date = self._get_period_dates(period)
        
        # Generate report ID
        report_id = f"audit_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Initialize report
        report = ComplianceReport(
            report_id=report_id,
            generated_at=datetime.now(),
            period_start=start_date,
            period_end=end_date,
            generated_by=generated_by
        )
        
        # Generate operation summary
        report.operation_summary = self.generate_operation_summary(
            ReportPeriod.CUSTOM, start_date, end_date
        )
        
        # Generate data change summary
        report.data_change_summary = self.generate_data_change_summary(
            ReportPeriod.CUSTOM, start_date, end_date
        )
        
        # Identify failed operations
        failed_operations = self.audit_manager.get_operation_history(
            status=OperationStatus.FAILED,
            start_date=start_date,
            end_date=end_date,
            limit=100
        )
        
        for operation in failed_operations:
            report.failed_operations.append({
                'operation_id': operation.get('operation_id'),
                'operation_type': operation.get('operation_type'),
                'user_id': operation.get('user_id'),
                'start_time': operation.get('start_time'),
                'error_count': operation.get('error_count', 0),
                'file_path': operation.get('file_path')
            })
        
        # Identify high-risk activities
        self._identify_high_risk_activities(report)
        
        # Generate recommendations
        self._generate_recommendations(report)
        
        return report
    
    def get_user_activity_report(
        self,
        user_id: str,
        period: ReportPeriod = ReportPeriod.LAST_MONTH,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Generate activity report for a specific user."""
        
        # Calculate date range
        if period == ReportPeriod.CUSTOM:
            if not start_date or not end_date:
                raise ValueError("Custom period requires start_date and end_date")
        else:
            start_date, end_date = self._get_period_dates(period)
        
        # Get user operations
        operations = self.audit_manager.get_operation_history(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            limit=1000
        )
        
        # Analyze user activity
        activity_report = {
            'user_id': user_id,
            'period_start': start_date.isoformat(),
            'period_end': end_date.isoformat(),
            'total_operations': len(operations),
            'successful_operations': 0,
            'failed_operations': 0,
            'operations_by_type': {},
            'operations_by_day': {},
            'total_records_processed': 0,
            'most_recent_activity': None,
            'average_operation_duration': 0.0
        }
        
        total_duration = 0.0
        duration_count = 0
        
        for operation in operations:
            # Count by status
            status = operation.get('status', '')
            if status == OperationStatus.COMPLETED.value:
                activity_report['successful_operations'] += 1
            elif status == OperationStatus.FAILED.value:
                activity_report['failed_operations'] += 1
            
            # Count by type
            op_type = operation.get('operation_type', 'unknown')
            activity_report['operations_by_type'][op_type] = \
                activity_report['operations_by_type'].get(op_type, 0) + 1
            
            # Count by day
            start_time = operation.get('start_time', '')
            if start_time:
                try:
                    op_date = datetime.fromisoformat(start_time.replace('Z', '+00:00')).date()
                    day_key = op_date.isoformat()
                    activity_report['operations_by_day'][day_key] = \
                        activity_report['operations_by_day'].get(day_key, 0) + 1
                except (ValueError, TypeError):
                    pass
            
            # Track most recent activity
            if not activity_report['most_recent_activity'] or start_time > activity_report['most_recent_activity']:
                activity_report['most_recent_activity'] = start_time
            
            # Aggregate record counts
            records_processed = operation.get('records_processed', {})
            if isinstance(records_processed, dict):
                activity_report['total_records_processed'] += sum(records_processed.values())
            
            # Calculate duration
            if operation.get('start_time') and operation.get('end_time'):
                try:
                    start = datetime.fromisoformat(operation['start_time'].replace('Z', '+00:00'))
                    end = datetime.fromisoformat(operation['end_time'].replace('Z', '+00:00'))
                    duration = (end - start).total_seconds()
                    total_duration += duration
                    duration_count += 1
                except (ValueError, TypeError):
                    pass
        
        # Calculate average duration
        if duration_count > 0:
            activity_report['average_operation_duration'] = total_duration / duration_count
        
        return activity_report
    
    def get_entity_change_history(
        self,
        entity_type: str,
        entity_id: Optional[int] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get change history for a specific entity or entity type."""
        
        changes = self.audit_manager.get_data_changes_for_entity(
            entity_type, entity_id, limit
        )
        
        # Enrich changes with operation information
        enriched_changes = []
        for change in changes:
            operation_id = change.get('operation_id')
            operation_info = {}
            
            if operation_id:
                # Get basic operation info
                operations = self.audit_manager.get_operation_history(limit=1)
                for op in operations:
                    if op.get('operation_id') == operation_id:
                        operation_info = {
                            'operation_type': op.get('operation_type'),
                            'user_id': op.get('user_id'),
                            'start_time': op.get('start_time'),
                            'status': op.get('status')
                        }
                        break
            
            enriched_change = {
                **change,
                'operation_info': operation_info
            }
            enriched_changes.append(enriched_change)
        
        return enriched_changes
    
    def _get_period_dates(self, period: ReportPeriod) -> Tuple[datetime, datetime]:
        """Get start and end dates for a report period."""
        now = datetime.now()
        
        if period == ReportPeriod.LAST_24_HOURS:
            start_date = now - timedelta(days=1)
            end_date = now
        elif period == ReportPeriod.LAST_WEEK:
            start_date = now - timedelta(weeks=1)
            end_date = now
        elif period == ReportPeriod.LAST_MONTH:
            start_date = now - timedelta(days=30)
            end_date = now
        elif period == ReportPeriod.LAST_QUARTER:
            start_date = now - timedelta(days=90)
            end_date = now
        else:
            raise ValueError(f"Unsupported period: {period}")
        
        return start_date, end_date
    
    def _identify_high_risk_activities(self, report: ComplianceReport):
        """Identify high-risk activities for the compliance report."""
        
        # High failure rate
        if report.operation_summary.failure_rate > 20:
            report.high_risk_activities.append({
                'type': 'high_failure_rate',
                'description': f'Tasso di fallimento elevato: {report.operation_summary.failure_rate:.1f}%',
                'severity': 'high',
                'recommendation': 'Investigare le cause dei fallimenti e migliorare la validazione dei dati'
            })
        
        # Large number of skipped records
        if report.data_change_summary.skips > report.data_change_summary.total_changes * 0.3:
            report.high_risk_activities.append({
                'type': 'high_skip_rate',
                'description': f'Alto numero di record saltati: {report.data_change_summary.skips}',
                'severity': 'medium',
                'recommendation': 'Verificare la strategia di risoluzione conflitti e la qualità dei dati'
            })
        
        # Unusual activity patterns (many operations by single user)
        for user, count in report.operation_summary.operations_by_user.items():
            if count > report.operation_summary.total_operations * 0.5:
                report.high_risk_activities.append({
                    'type': 'concentrated_activity',
                    'description': f'Attività concentrata da utente {user}: {count} operazioni',
                    'severity': 'low',
                    'recommendation': 'Verificare se l\'attività è legittima e considerare la distribuzione del carico'
                })
    
    def _generate_recommendations(self, report: ComplianceReport):
        """Generate recommendations based on the compliance report analysis."""
        
        # Based on failure rate
        if report.operation_summary.failure_rate > 10:
            report.add_recommendation(
                "Implementare controlli di qualità più rigorosi sui dati di input per ridurre i fallimenti"
            )
        
        # Based on data changes
        if report.data_change_summary.updates > report.data_change_summary.creates:
            report.add_recommendation(
                "Considerare l'implementazione di controlli per evitare modifiche eccessive ai dati esistenti"
            )
        
        # Based on operation volume
        if report.operation_summary.total_operations > 100:
            report.add_recommendation(
                "Considerare l'automazione di operazioni ricorrenti per migliorare l'efficienza"
            )
        
        # Based on average duration
        if report.operation_summary.average_duration > 300:  # 5 minutes
            report.add_recommendation(
                "Ottimizzare le prestazioni delle operazioni per ridurre i tempi di elaborazione"
            )


# Global audit reporting service instance
_audit_reporting_service = None


def get_audit_reporting_service() -> AuditReportingService:
    """Get global audit reporting service instance."""
    global _audit_reporting_service
    if _audit_reporting_service is None:
        _audit_reporting_service = AuditReportingService()
    return _audit_reporting_service