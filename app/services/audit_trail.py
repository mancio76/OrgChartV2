"""
Audit trail and operation tracking system for import/export operations.

This module provides comprehensive logging of operations with user tracking,
data change tracking, and operation history for compliance and troubleshooting.
"""

import json
import sqlite3
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field, asdict

from ..database import get_db_manager


class OperationType(Enum):
    """Types of operations that can be tracked."""
    IMPORT = "import"
    EXPORT = "export"
    PREVIEW = "preview"
    VALIDATION = "validation"


class OperationStatus(Enum):
    """Status of tracked operations."""
    STARTED = "started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ChangeType(Enum):
    """Types of data changes that can be tracked."""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    SKIP = "skip"


@dataclass
class DataChange:
    """Represents a single data change during import/export."""
    entity_type: str
    entity_id: Optional[int]
    change_type: ChangeType
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    line_number: Optional[int] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['change_type'] = self.change_type.value
        data['timestamp'] = self.timestamp.isoformat()
        return data


@dataclass
class OperationRecord:
    """Complete record of an import/export operation."""
    operation_id: str
    operation_type: OperationType
    status: OperationStatus
    user_id: Optional[str]
    start_time: datetime
    end_time: Optional[datetime] = None
    file_path: Optional[str] = None
    file_format: Optional[str] = None
    entity_types: List[str] = field(default_factory=list)
    options: Dict[str, Any] = field(default_factory=dict)
    results: Dict[str, Any] = field(default_factory=dict)
    error_count: int = 0
    warning_count: int = 0
    records_processed: Dict[str, int] = field(default_factory=dict)
    records_created: Dict[str, int] = field(default_factory=dict)
    records_updated: Dict[str, int] = field(default_factory=dict)
    records_skipped: Dict[str, int] = field(default_factory=dict)
    data_changes: List[DataChange] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def duration(self) -> Optional[float]:
        """Calculate operation duration in seconds."""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
    
    @property
    def total_records_processed(self) -> int:
        """Total number of records processed across all entity types."""
        return sum(self.records_processed.values())
    
    @property
    def total_records_created(self) -> int:
        """Total number of records created across all entity types."""
        return sum(self.records_created.values())
    
    @property
    def total_records_updated(self) -> int:
        """Total number of records updated across all entity types."""
        return sum(self.records_updated.values())
    
    def add_data_change(self, change: DataChange):
        """Add a data change to the operation record."""
        self.data_changes.append(change)
        
        # Update counters based on change type
        entity_type = change.entity_type
        if change.change_type == ChangeType.CREATE:
            self.records_created[entity_type] = self.records_created.get(entity_type, 0) + 1
        elif change.change_type == ChangeType.UPDATE:
            self.records_updated[entity_type] = self.records_updated.get(entity_type, 0) + 1
        elif change.change_type == ChangeType.SKIP:
            self.records_skipped[entity_type] = self.records_skipped.get(entity_type, 0) + 1
        
        # Always increment processed count
        self.records_processed[entity_type] = self.records_processed.get(entity_type, 0) + 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['operation_type'] = self.operation_type.value
        data['status'] = self.status.value
        data['start_time'] = self.start_time.isoformat()
        data['end_time'] = self.end_time.isoformat() if self.end_time else None
        data['data_changes'] = [change.to_dict() for change in self.data_changes]
        return data


class AuditTrailManager:
    """Manages audit trail and operation tracking for import/export operations."""
    
    def __init__(self):
        """Initialize audit trail manager."""
        self.db_manager = get_db_manager()
        self._ensure_audit_tables()
        self.active_operations: Dict[str, OperationRecord] = {}
    
    def _ensure_audit_tables(self):
        """Ensure audit trail tables exist in the database."""
        create_operations_table = """
        CREATE TABLE IF NOT EXISTS audit_operations (
            operation_id TEXT PRIMARY KEY,
            operation_type TEXT NOT NULL,
            status TEXT NOT NULL,
            user_id TEXT,
            start_time TEXT NOT NULL,
            end_time TEXT,
            file_path TEXT,
            file_format TEXT,
            entity_types TEXT,  -- JSON array
            options TEXT,       -- JSON object
            results TEXT,       -- JSON object
            error_count INTEGER DEFAULT 0,
            warning_count INTEGER DEFAULT 0,
            records_processed TEXT,  -- JSON object
            records_created TEXT,    -- JSON object
            records_updated TEXT,    -- JSON object
            records_skipped TEXT,    -- JSON object
            metadata TEXT,      -- JSON object
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        create_data_changes_table = """
        CREATE TABLE IF NOT EXISTS audit_data_changes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            operation_id TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            entity_id INTEGER,
            change_type TEXT NOT NULL,
            old_values TEXT,    -- JSON object
            new_values TEXT,    -- JSON object
            line_number INTEGER,
            timestamp TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (operation_id) REFERENCES audit_operations (operation_id)
        )
        """
        
        create_operation_files_table = """
        CREATE TABLE IF NOT EXISTS audit_operation_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            operation_id TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_type TEXT,  -- 'input' or 'output'
            file_size INTEGER,
            file_hash TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (operation_id) REFERENCES audit_operations (operation_id)
        )
        """
        
        # Create indexes for better query performance
        create_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_audit_operations_user_id ON audit_operations (user_id)",
            "CREATE INDEX IF NOT EXISTS idx_audit_operations_start_time ON audit_operations (start_time)",
            "CREATE INDEX IF NOT EXISTS idx_audit_operations_status ON audit_operations (status)",
            "CREATE INDEX IF NOT EXISTS idx_audit_data_changes_operation_id ON audit_data_changes (operation_id)",
            "CREATE INDEX IF NOT EXISTS idx_audit_data_changes_entity_type ON audit_data_changes (entity_type)",
            "CREATE INDEX IF NOT EXISTS idx_audit_operation_files_operation_id ON audit_operation_files (operation_id)"
        ]
        
        try:
            with self.db_manager.get_connection() as conn:
                conn.execute(create_operations_table)
                conn.execute(create_data_changes_table)
                conn.execute(create_operation_files_table)
                
                for index_sql in create_indexes:
                    conn.execute(index_sql)
                
                conn.commit()
        
        except Exception as e:
            raise Exception(f"Failed to create audit trail tables: {e}")
    
    def start_operation(
        self,
        operation_id: str,
        operation_type: OperationType,
        user_id: Optional[str] = None,
        file_path: Optional[str] = None,
        file_format: Optional[str] = None,
        entity_types: Optional[List[str]] = None,
        options: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> OperationRecord:
        """Start tracking a new operation."""
        
        operation_record = OperationRecord(
            operation_id=operation_id,
            operation_type=operation_type,
            status=OperationStatus.STARTED,
            user_id=user_id,
            start_time=datetime.now(),
            file_path=file_path,
            file_format=file_format,
            entity_types=entity_types or [],
            options=options or {},
            metadata=metadata or {}
        )
        
        self.active_operations[operation_id] = operation_record
        
        # Save to database
        self._save_operation_to_db(operation_record)
        
        return operation_record
    
    def update_operation_status(
        self,
        operation_id: str,
        status: OperationStatus,
        results: Optional[Dict[str, Any]] = None,
        error_count: Optional[int] = None,
        warning_count: Optional[int] = None
    ):
        """Update the status of an operation."""
        
        if operation_id not in self.active_operations:
            raise ValueError(f"Operation {operation_id} not found in active operations")
        
        operation = self.active_operations[operation_id]
        operation.status = status
        
        if status in [OperationStatus.COMPLETED, OperationStatus.FAILED, OperationStatus.CANCELLED]:
            operation.end_time = datetime.now()
        
        if results:
            operation.results.update(results)
        
        if error_count is not None:
            operation.error_count = error_count
        
        if warning_count is not None:
            operation.warning_count = warning_count
        
        # Update in database
        self._update_operation_in_db(operation)
    
    def track_data_change(
        self,
        operation_id: str,
        entity_type: str,
        change_type: ChangeType,
        entity_id: Optional[int] = None,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        line_number: Optional[int] = None
    ):
        """Track a data change during an operation."""
        
        change = DataChange(
            entity_type=entity_type,
            entity_id=entity_id,
            change_type=change_type,
            old_values=old_values,
            new_values=new_values,
            line_number=line_number
        )
        
        # Add to active operation if exists
        if operation_id in self.active_operations:
            self.active_operations[operation_id].add_data_change(change)
        
        # Save to database
        self._save_data_change_to_db(operation_id, change)
    
    def track_file(
        self,
        operation_id: str,
        file_path: str,
        file_type: str,  # 'input' or 'output'
        file_size: Optional[int] = None,
        file_hash: Optional[str] = None
    ):
        """Track a file associated with an operation."""
        
        try:
            with self.db_manager.get_connection() as conn:
                conn.execute("""
                    INSERT INTO audit_operation_files 
                    (operation_id, file_path, file_type, file_size, file_hash)
                    VALUES (?, ?, ?, ?, ?)
                """, (operation_id, file_path, file_type, file_size, file_hash))
                conn.commit()
        
        except Exception as e:
            raise Exception(f"Failed to track file for operation {operation_id}: {e}")
    
    def complete_operation(self, operation_id: str) -> Optional[OperationRecord]:
        """Complete an operation and remove from active tracking."""
        
        if operation_id not in self.active_operations:
            return None
        
        operation = self.active_operations[operation_id]
        
        if operation.status in [OperationStatus.STARTED, OperationStatus.IN_PROGRESS]:
            operation.status = OperationStatus.COMPLETED
        
        operation.end_time = datetime.now()
        
        # Final update to database
        self._update_operation_in_db(operation)
        
        # Remove from active operations
        completed_operation = self.active_operations.pop(operation_id)
        
        return completed_operation
    
    def get_operation_history(
        self,
        user_id: Optional[str] = None,
        operation_type: Optional[OperationType] = None,
        status: Optional[OperationStatus] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get operation history with optional filters."""
        
        query = "SELECT * FROM audit_operations WHERE 1=1"
        params = []
        
        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)
        
        if operation_type:
            query += " AND operation_type = ?"
            params.append(operation_type.value)
        
        if status:
            query += " AND status = ?"
            params.append(status.value)
        
        if start_date:
            query += " AND start_time >= ?"
            params.append(start_date.isoformat())
        
        if end_date:
            query += " AND start_time <= ?"
            params.append(end_date.isoformat())
        
        query += " ORDER BY start_time DESC LIMIT ?"
        params.append(limit)
        
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute(query, params)
                rows = cursor.fetchall()
                
                operations = []
                for row in rows:
                    operation_data = dict(row)
                    
                    # Parse JSON fields
                    for json_field in ['entity_types', 'options', 'results', 'records_processed', 
                                     'records_created', 'records_updated', 'records_skipped', 'metadata']:
                        if operation_data[json_field]:
                            try:
                                operation_data[json_field] = json.loads(operation_data[json_field])
                            except json.JSONDecodeError:
                                operation_data[json_field] = {}
                    
                    operations.append(operation_data)
                
                return operations
        
        except Exception as e:
            raise Exception(f"Failed to get operation history: {e}")
    
    def get_operation_details(self, operation_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific operation."""
        
        try:
            with self.db_manager.get_connection() as conn:
                # Get operation record
                cursor = conn.execute(
                    "SELECT * FROM audit_operations WHERE operation_id = ?",
                    (operation_id,)
                )
                operation_row = cursor.fetchone()
                
                if not operation_row:
                    return None
                
                operation_data = dict(operation_row)
                
                # Parse JSON fields
                for json_field in ['entity_types', 'options', 'results', 'records_processed', 
                                 'records_created', 'records_updated', 'records_skipped', 'metadata']:
                    if operation_data[json_field]:
                        try:
                            operation_data[json_field] = json.loads(operation_data[json_field])
                        except json.JSONDecodeError:
                            operation_data[json_field] = {}
                
                # Get data changes
                cursor = conn.execute(
                    "SELECT * FROM audit_data_changes WHERE operation_id = ? ORDER BY timestamp",
                    (operation_id,)
                )
                changes_rows = cursor.fetchall()
                
                data_changes = []
                for change_row in changes_rows:
                    change_data = dict(change_row)
                    
                    # Parse JSON fields
                    for json_field in ['old_values', 'new_values']:
                        if change_data[json_field]:
                            try:
                                change_data[json_field] = json.loads(change_data[json_field])
                            except json.JSONDecodeError:
                                change_data[json_field] = {}
                    
                    data_changes.append(change_data)
                
                operation_data['data_changes'] = data_changes
                
                # Get associated files
                cursor = conn.execute(
                    "SELECT * FROM audit_operation_files WHERE operation_id = ?",
                    (operation_id,)
                )
                files_rows = cursor.fetchall()
                operation_data['files'] = [dict(row) for row in files_rows]
                
                return operation_data
        
        except Exception as e:
            raise Exception(f"Failed to get operation details for {operation_id}: {e}")
    
    def get_data_changes_for_entity(
        self,
        entity_type: str,
        entity_id: Optional[int] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get data changes for a specific entity."""
        
        query = "SELECT * FROM audit_data_changes WHERE entity_type = ?"
        params = [entity_type]
        
        if entity_id is not None:
            query += " AND entity_id = ?"
            params.append(entity_id)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute(query, params)
                rows = cursor.fetchall()
                
                changes = []
                for row in rows:
                    change_data = dict(row)
                    
                    # Parse JSON fields
                    for json_field in ['old_values', 'new_values']:
                        if change_data[json_field]:
                            try:
                                change_data[json_field] = json.loads(change_data[json_field])
                            except json.JSONDecodeError:
                                change_data[json_field] = {}
                    
                    changes.append(change_data)
                
                return changes
        
        except Exception as e:
            raise Exception(f"Failed to get data changes for entity {entity_type}: {e}")
    
    def _save_operation_to_db(self, operation: OperationRecord):
        """Save operation record to database."""
        
        try:
            with self.db_manager.get_connection() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO audit_operations 
                    (operation_id, operation_type, status, user_id, start_time, end_time,
                     file_path, file_format, entity_types, options, results,
                     error_count, warning_count, records_processed, records_created,
                     records_updated, records_skipped, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    operation.operation_id,
                    operation.operation_type.value,
                    operation.status.value,
                    operation.user_id,
                    operation.start_time.isoformat(),
                    operation.end_time.isoformat() if operation.end_time else None,
                    operation.file_path,
                    operation.file_format,
                    json.dumps(operation.entity_types),
                    json.dumps(operation.options),
                    json.dumps(operation.results),
                    operation.error_count,
                    operation.warning_count,
                    json.dumps(operation.records_processed),
                    json.dumps(operation.records_created),
                    json.dumps(operation.records_updated),
                    json.dumps(operation.records_skipped),
                    json.dumps(operation.metadata)
                ))
                conn.commit()
        
        except Exception as e:
            raise Exception(f"Failed to save operation {operation.operation_id} to database: {e}")
    
    def _update_operation_in_db(self, operation: OperationRecord):
        """Update operation record in database."""
        
        try:
            with self.db_manager.get_connection() as conn:
                conn.execute("""
                    UPDATE audit_operations SET
                        status = ?, end_time = ?, results = ?, error_count = ?,
                        warning_count = ?, records_processed = ?, records_created = ?,
                        records_updated = ?, records_skipped = ?, metadata = ?
                    WHERE operation_id = ?
                """, (
                    operation.status.value,
                    operation.end_time.isoformat() if operation.end_time else None,
                    json.dumps(operation.results),
                    operation.error_count,
                    operation.warning_count,
                    json.dumps(operation.records_processed),
                    json.dumps(operation.records_created),
                    json.dumps(operation.records_updated),
                    json.dumps(operation.records_skipped),
                    json.dumps(operation.metadata),
                    operation.operation_id
                ))
                conn.commit()
        
        except Exception as e:
            raise Exception(f"Failed to update operation {operation.operation_id} in database: {e}")
    
    def _save_data_change_to_db(self, operation_id: str, change: DataChange):
        """Save data change to database."""
        
        try:
            with self.db_manager.get_connection() as conn:
                conn.execute("""
                    INSERT INTO audit_data_changes 
                    (operation_id, entity_type, entity_id, change_type, old_values, 
                     new_values, line_number, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    operation_id,
                    change.entity_type,
                    change.entity_id,
                    change.change_type.value,
                    json.dumps(change.old_values) if change.old_values else None,
                    json.dumps(change.new_values) if change.new_values else None,
                    change.line_number,
                    change.timestamp.isoformat()
                ))
                conn.commit()
        
        except Exception as e:
            raise Exception(f"Failed to save data change to database: {e}")


# Global audit trail manager instance
_audit_manager = None


def get_audit_manager() -> AuditTrailManager:
    """Get global audit trail manager instance."""
    global _audit_manager
    if _audit_manager is None:
        _audit_manager = AuditTrailManager()
    return _audit_manager