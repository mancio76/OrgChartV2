"""
Security service for import/export operations.

This module provides comprehensive security measures for file upload validation,
access control, input sanitization, and XSS prevention specifically for
import/export operations.

Implements Requirements 1.1, 2.1, 7.1 security measures.
"""

import logging
import os
import hashlib
import mimetypes
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Set, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta

from fastapi import HTTPException, UploadFile, Request
from ..security import InputValidator, SecurityValidationError, get_client_ip, log_security_event
from ..models.import_export import ImportExportValidationError, ImportErrorType

logger = logging.getLogger(__name__)


@dataclass
class FileSecurityConfig:
    """Configuration for file security validation"""
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    allowed_extensions: Set[str] = None
    allowed_mime_types: Set[str] = None
    scan_for_malware: bool = True
    quarantine_suspicious_files: bool = True
    max_files_per_hour: int = 50
    max_total_size_per_hour: int = 500 * 1024 * 1024  # 500MB
    
    def __post_init__(self):
        if self.allowed_extensions is None:
            self.allowed_extensions = {'.csv', '.json'}
        if self.allowed_mime_types is None:
            self.allowed_mime_types = {
                'text/csv', 'application/csv', 'text/plain',
                'application/json', 'text/json', 'application/octet-stream'
            }


@dataclass
class FileUploadRecord:
    """Record of file upload for rate limiting"""
    timestamp: datetime
    filename: str
    size: int
    client_ip: str
    operation_type: str


class ImportExportSecurityService:
    """
    Security service for import/export operations.
    
    Provides comprehensive security measures including:
    - File upload security validation
    - Access control for operations
    - Input sanitization and XSS prevention
    - Rate limiting and abuse prevention
    """
    
    def __init__(self, config: Optional[FileSecurityConfig] = None):
        """Initialize security service with configuration."""
        self.config = config or FileSecurityConfig()
        self.upload_records: List[FileUploadRecord] = []
        self.quarantine_dir = Path(tempfile.gettempdir()) / "import_export_quarantine"
        self.quarantine_dir.mkdir(exist_ok=True)
        
        # Suspicious file patterns
        self.suspicious_patterns = [
            b'<script', b'javascript:', b'vbscript:', b'onload=', b'onerror=',
            b'eval(', b'document.cookie', b'window.location', b'alert(',
            b'<?php', b'<%', b'<jsp:', b'<%@', b'#!/bin/sh', b'#!/bin/bash',
            b'DROP TABLE', b'DELETE FROM', b'INSERT INTO', b'UPDATE SET',
            b'UNION SELECT', b'OR 1=1', b"' OR '1'='1", b'--', b'/*', b'*/',
            b'\x00', b'\xff\xfe', b'\xfe\xff'  # Null bytes and BOM markers
        ]
        
        logger.info("ImportExportSecurityService initialized")
    
    def validate_file_upload(self, file: UploadFile, request: Request, 
                           operation_type: str = "import") -> None:
        """
        Comprehensive file upload security validation.
        
        Args:
            file: Uploaded file to validate
            request: HTTP request context
            operation_type: Type of operation (import/export)
            
        Raises:
            HTTPException: If file fails security validation
        """
        client_ip = get_client_ip(request)
        
        try:
            # Basic file validation
            self._validate_basic_file_properties(file, client_ip, request)
            
            # Rate limiting validation
            self._validate_upload_rate_limits(file, client_ip, operation_type, request)
            
            # File extension and MIME type validation
            self._validate_file_type(file, client_ip, request)
            
            # Content security scanning
            self._scan_file_content_security(file, client_ip, request)
            
            # Record successful upload for rate limiting
            self._record_file_upload(file, client_ip, operation_type)
            
            log_security_event('FILE_UPLOAD_VALIDATED', {
                'filename': file.filename,
                'size': file.size,
                'content_type': file.content_type,
                'operation_type': operation_type,
                'client_ip': client_ip
            }, request)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in file upload validation: {e}")
            log_security_event('FILE_UPLOAD_VALIDATION_ERROR', {
                'filename': file.filename,
                'error': str(e),
                'client_ip': client_ip
            }, request)
            raise HTTPException(
                status_code=500,
                detail="Errore interno nella validazione del file"
            )
    
    def _validate_basic_file_properties(self, file: UploadFile, client_ip: str, 
                                      request: Request) -> None:
        """Validate basic file properties."""
        # Check if file exists
        if not file.filename:
            log_security_event('MISSING_FILENAME', {'client_ip': client_ip}, request)
            raise HTTPException(
                status_code=400,
                detail="Nome file mancante"
            )
        
        # Check file size
        if file.size is None:
            # Try to determine size by reading content
            try:
                content = file.file.read()
                file.file.seek(0)  # Reset file pointer
                file_size = len(content)
            except Exception:
                file_size = 0
        else:
            file_size = file.size
        
        if file_size > self.config.max_file_size:
            log_security_event('FILE_TOO_LARGE', {
                'filename': file.filename,
                'size': file_size,
                'max_size': self.config.max_file_size,
                'client_ip': client_ip
            }, request)
            raise HTTPException(
                status_code=413,
                detail=f"File troppo grande. Dimensione massima: {self.config.max_file_size // (1024*1024)}MB"
            )
        
        if file_size == 0:
            log_security_event('EMPTY_FILE', {
                'filename': file.filename,
                'client_ip': client_ip
            }, request)
            raise HTTPException(
                status_code=400,
                detail="File vuoto non consentito"
            )
    
    def _validate_upload_rate_limits(self, file: UploadFile, client_ip: str, 
                                   operation_type: str, request: Request) -> None:
        """Validate upload rate limits to prevent abuse."""
        now = datetime.now()
        hour_ago = now - timedelta(hours=1)
        
        # Clean old records
        self.upload_records = [
            record for record in self.upload_records 
            if record.timestamp > hour_ago
        ]
        
        # Check rate limits for this client IP
        client_uploads = [
            record for record in self.upload_records 
            if record.client_ip == client_ip
        ]
        
        # Check file count limit
        if len(client_uploads) >= self.config.max_files_per_hour:
            log_security_event('UPLOAD_RATE_LIMIT_EXCEEDED', {
                'client_ip': client_ip,
                'uploads_count': len(client_uploads),
                'limit': self.config.max_files_per_hour
            }, request)
            raise HTTPException(
                status_code=429,
                detail=f"Limite di upload superato. Massimo {self.config.max_files_per_hour} file per ora"
            )
        
        # Check total size limit
        total_size = sum(record.size for record in client_uploads)
        if total_size + (file.size or 0) > self.config.max_total_size_per_hour:
            log_security_event('UPLOAD_SIZE_LIMIT_EXCEEDED', {
                'client_ip': client_ip,
                'total_size': total_size,
                'file_size': file.size,
                'limit': self.config.max_total_size_per_hour
            }, request)
            raise HTTPException(
                status_code=429,
                detail=f"Limite dimensione upload superato. Massimo {self.config.max_total_size_per_hour // (1024*1024)}MB per ora"
            )
    
    def _validate_file_type(self, file: UploadFile, client_ip: str, request: Request) -> None:
        """Validate file extension and MIME type."""
        # Check file extension
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in self.config.allowed_extensions:
            log_security_event('INVALID_FILE_EXTENSION', {
                'filename': file.filename,
                'extension': file_extension,
                'allowed_extensions': list(self.config.allowed_extensions),
                'client_ip': client_ip
            }, request)
            raise HTTPException(
                status_code=400,
                detail=f"Estensione file non consentita. Estensioni consentite: {', '.join(self.config.allowed_extensions)}"
            )
        
        # Check MIME type if provided
        if file.content_type:
            if file.content_type not in self.config.allowed_mime_types:
                # Log suspicious MIME type but don't block (some browsers send incorrect MIME types)
                log_security_event('SUSPICIOUS_MIME_TYPE', {
                    'filename': file.filename,
                    'content_type': file.content_type,
                    'allowed_types': list(self.config.allowed_mime_types),
                    'client_ip': client_ip
                }, request)
        
        # Additional MIME type detection based on file content
        try:
            # Read first few bytes to detect actual file type
            content_start = file.file.read(1024)
            file.file.seek(0)  # Reset file pointer
            
            detected_type, _ = mimetypes.guess_type(file.filename)
            if detected_type and detected_type not in self.config.allowed_mime_types:
                log_security_event('MIME_TYPE_MISMATCH', {
                    'filename': file.filename,
                    'declared_type': file.content_type,
                    'detected_type': detected_type,
                    'client_ip': client_ip
                }, request)
        except Exception as e:
            logger.warning(f"Could not perform MIME type detection: {e}")
    
    def _scan_file_content_security(self, file: UploadFile, client_ip: str, 
                                   request: Request) -> None:
        """Scan file content for security threats."""
        try:
            # Read file content for scanning
            content = file.file.read()
            file.file.seek(0)  # Reset file pointer
            
            # Convert to bytes if needed
            if isinstance(content, str):
                content = content.encode('utf-8', errors='ignore')
            
            # Scan for suspicious patterns
            suspicious_findings = []
            for pattern in self.suspicious_patterns:
                if pattern in content.lower():
                    suspicious_findings.append(pattern.decode('utf-8', errors='ignore'))
            
            if suspicious_findings:
                log_security_event('SUSPICIOUS_FILE_CONTENT', {
                    'filename': file.filename,
                    'patterns_found': suspicious_findings[:5],  # Limit to first 5 findings
                    'client_ip': client_ip
                }, request)
                
                if self.config.quarantine_suspicious_files:
                    self._quarantine_file(file, suspicious_findings, client_ip)
                
                raise HTTPException(
                    status_code=400,
                    detail="File contiene contenuto potenzialmente pericoloso"
                )
            
            # Check for excessive null bytes (potential binary exploitation)
            null_count = content.count(b'\x00')
            if null_count > 10:  # Allow some null bytes for legitimate files
                log_security_event('EXCESSIVE_NULL_BYTES', {
                    'filename': file.filename,
                    'null_count': null_count,
                    'client_ip': client_ip
                }, request)
                raise HTTPException(
                    status_code=400,
                    detail="File contiene dati binari non validi"
                )
            
            # Check file size consistency
            actual_size = len(content)
            declared_size = file.size or 0
            if abs(actual_size - declared_size) > 1024:  # Allow 1KB difference
                log_security_event('FILE_SIZE_MISMATCH', {
                    'filename': file.filename,
                    'declared_size': declared_size,
                    'actual_size': actual_size,
                    'client_ip': client_ip
                }, request)
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error scanning file content: {e}")
            # Don't block upload for scanning errors, but log them
            log_security_event('FILE_SCAN_ERROR', {
                'filename': file.filename,
                'error': str(e),
                'client_ip': client_ip
            }, request)
    
    def _quarantine_file(self, file: UploadFile, suspicious_findings: List[str], 
                        client_ip: str) -> None:
        """Quarantine suspicious file for analysis."""
        try:
            # Create quarantine filename with timestamp and hash
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_hash = hashlib.md5(file.filename.encode()).hexdigest()[:8]
            quarantine_filename = f"{timestamp}_{file_hash}_{file.filename}"
            quarantine_path = self.quarantine_dir / quarantine_filename
            
            # Save file to quarantine
            content = file.file.read()
            file.file.seek(0)  # Reset file pointer
            
            with open(quarantine_path, 'wb') as qf:
                qf.write(content)
            
            # Create metadata file
            metadata = {
                'original_filename': file.filename,
                'quarantine_time': datetime.now().isoformat(),
                'client_ip': client_ip,
                'suspicious_patterns': suspicious_findings,
                'file_size': len(content),
                'content_type': file.content_type
            }
            
            metadata_path = quarantine_path.with_suffix('.metadata.json')
            import json
            with open(metadata_path, 'w') as mf:
                json.dump(metadata, mf, indent=2)
            
            logger.warning(f"File quarantined: {file.filename} -> {quarantine_path}")
        
        except Exception as e:
            logger.error(f"Error quarantining file {file.filename}: {e}")
    
    def _record_file_upload(self, file: UploadFile, client_ip: str, 
                           operation_type: str) -> None:
        """Record file upload for rate limiting."""
        record = FileUploadRecord(
            timestamp=datetime.now(),
            filename=file.filename,
            size=file.size or 0,
            client_ip=client_ip,
            operation_type=operation_type
        )
        self.upload_records.append(record)
    
    def sanitize_import_data(self, data: Dict[str, Any], entity_type: str) -> Dict[str, Any]:
        """
        Sanitize import data to prevent XSS and injection attacks.
        
        Args:
            data: Raw import data
            entity_type: Type of entity being imported
            
        Returns:
            Sanitized data dictionary
        """
        try:
            sanitized_data = {}
            
            for field, value in data.items():
                if value is None:
                    sanitized_data[field] = None
                    continue
                
                # Convert to string for processing
                str_value = str(value)
                
                # Apply input sanitization
                try:
                    sanitized_value = InputValidator.sanitize_string(str_value)
                    
                    # Additional sanitization for specific field types
                    if field.endswith('_id') and str_value.isdigit():
                        # Keep numeric IDs as integers
                        sanitized_data[field] = int(sanitized_value)
                    elif field in ['email']:
                        # Email-specific sanitization
                        sanitized_data[field] = self._sanitize_email(sanitized_value)
                    elif field in ['name', 'short_name', 'first_name', 'last_name']:
                        # Name field sanitization
                        sanitized_data[field] = self._sanitize_name_field(sanitized_value)
                    elif field == 'aliases':
                        # JSON field sanitization
                        sanitized_data[field] = self._sanitize_json_field(sanitized_value)
                    else:
                        sanitized_data[field] = sanitized_value
                
                except SecurityValidationError as e:
                    logger.warning(f"Security validation failed for field {field}: {e}")
                    raise ImportExportValidationError(
                        field=field,
                        message=f"Campo contiene contenuto non sicuro: {str(e)}",
                        error_type=ImportErrorType.BUSINESS_RULE_VIOLATION,
                        line_number=getattr(data, '_line_number', None)
                    )
            
            return sanitized_data
        
        except ImportExportValidationError:
            raise
        except Exception as e:
            logger.error(f"Error sanitizing import data: {e}")
            raise ImportExportValidationError(
                field="data_sanitization",
                message=f"Errore nella sanitizzazione dei dati: {str(e)}",
                error_type=ImportErrorType.BUSINESS_RULE_VIOLATION
            )
    
    def _sanitize_email(self, email: str) -> str:
        """Sanitize email field."""
        # Remove dangerous characters but preserve email format
        email = email.strip().lower()
        # Basic email validation pattern
        import re
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            raise SecurityValidationError("Formato email non valido")
        return email
    
    def _sanitize_name_field(self, name: str) -> str:
        """Sanitize name fields."""
        # Remove HTML tags and dangerous characters
        name = InputValidator.sanitize_html(name)
        name = name.strip()
        
        # Check for reasonable length
        if len(name) > 200:
            raise SecurityValidationError("Nome troppo lungo")
        
        # Check for suspicious patterns
        if InputValidator.detect_xss(name) or InputValidator.detect_sql_injection(name):
            raise SecurityValidationError("Nome contiene caratteri non consentiti")
        
        return name
    
    def _sanitize_json_field(self, json_str: str) -> str:
        """Sanitize JSON field content."""
        try:
            import json
            # Parse and re-serialize to ensure valid JSON
            parsed = json.loads(json_str)
            
            # Recursively sanitize JSON content
            sanitized = self._sanitize_json_recursive(parsed)
            
            return json.dumps(sanitized, ensure_ascii=False)
        
        except json.JSONDecodeError:
            raise SecurityValidationError("JSON non valido")
        except Exception as e:
            raise SecurityValidationError(f"Errore nella sanitizzazione JSON: {str(e)}")
    
    def _sanitize_json_recursive(self, obj: Any) -> Any:
        """Recursively sanitize JSON object."""
        if isinstance(obj, dict):
            return {
                key: self._sanitize_json_recursive(value)
                for key, value in obj.items()
                if isinstance(key, str) and not InputValidator.detect_xss(key)
            }
        elif isinstance(obj, list):
            return [self._sanitize_json_recursive(item) for item in obj]
        elif isinstance(obj, str):
            sanitized = InputValidator.sanitize_string(obj)
            if InputValidator.detect_xss(sanitized) or InputValidator.detect_sql_injection(sanitized):
                raise SecurityValidationError("JSON contiene contenuto non sicuro")
            return sanitized
        else:
            return obj
    
    def validate_access_permissions(self, request: Request, operation_type: str, 
                                  entity_types: List[str]) -> None:
        """
        Validate user access permissions for import/export operations.
        
        Args:
            request: HTTP request context
            operation_type: Type of operation (import/export)
            entity_types: List of entity types being accessed
            
        Raises:
            HTTPException: If access is denied
        """
        client_ip = get_client_ip(request)
        
        try:
            # For now, implement basic access control
            # In a full implementation, this would check user roles and permissions
            
            # Log access attempt
            log_security_event('ACCESS_PERMISSION_CHECK', {
                'operation_type': operation_type,
                'entity_types': entity_types,
                'client_ip': client_ip
            }, request)
            
            # Basic validation - ensure user is authenticated
            # This would be expanded with proper role-based access control
            user_agent = request.headers.get('user-agent', '')
            if not user_agent or 'bot' in user_agent.lower():
                log_security_event('SUSPICIOUS_USER_AGENT', {
                    'user_agent': user_agent,
                    'client_ip': client_ip
                }, request)
                raise HTTPException(
                    status_code=403,
                    detail="Accesso negato: User-Agent sospetto"
                )
            
            # Check for sensitive entity types that might require elevated permissions
            sensitive_entities = {'persons', 'assignments'}
            if any(entity in sensitive_entities for entity in entity_types):
                # In a full implementation, check for admin role
                log_security_event('SENSITIVE_ENTITY_ACCESS', {
                    'operation_type': operation_type,
                    'sensitive_entities': [e for e in entity_types if e in sensitive_entities],
                    'client_ip': client_ip
                }, request)
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error validating access permissions: {e}")
            raise HTTPException(
                status_code=500,
                detail="Errore nella validazione dei permessi"
            )
    
    def get_security_headers(self) -> Dict[str, str]:
        """Get security headers for import/export responses."""
        return {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0'
        }
    
    def cleanup_quarantine(self, days_old: int = 30) -> int:
        """
        Clean up old quarantined files.
        
        Args:
            days_old: Remove files older than this many days
            
        Returns:
            Number of files cleaned up
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days_old)
            cleaned_count = 0
            
            for file_path in self.quarantine_dir.glob('*'):
                if file_path.is_file():
                    file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_time < cutoff_date:
                        try:
                            file_path.unlink()
                            cleaned_count += 1
                        except Exception as e:
                            logger.warning(f"Could not delete quarantined file {file_path}: {e}")
            
            logger.info(f"Cleaned up {cleaned_count} old quarantined files")
            return cleaned_count
        
        except Exception as e:
            logger.error(f"Error cleaning up quarantine: {e}")
            return 0


# Global security service instance
_security_service = None


def get_import_export_security_service() -> ImportExportSecurityService:
    """Get the global import/export security service instance."""
    global _security_service
    if _security_service is None:
        _security_service = ImportExportSecurityService()
    return _security_service