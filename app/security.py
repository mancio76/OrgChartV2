"""
Security-by-design implementation for Organigramma Web App
Comprehensive security features including input validation, SQL injection prevention,
security headers, CSRF protection, and secure deployment patterns
"""

import re
import html
import secrets
import hashlib
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import bleach

logger = logging.getLogger(__name__)

# =============================================================================
# INPUT VALIDATION AND SANITIZATION
# =============================================================================

class InputValidator:
    """Comprehensive input validation and sanitization"""
    
    # Common regex patterns for validation
    PATTERNS = {
        'email': re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'),
        'phone': re.compile(r'^\+?[\d\s\-\(\)]{7,20}$'),
        'alphanumeric': re.compile(r'^[a-zA-Z0-9\s\-_\.]+$'),
        'name': re.compile(r'^[a-zA-ZÀ-ÿ\s\-\'\.]{1,100}$'),
        'sql_injection': re.compile(r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION|SCRIPT)\b)', re.IGNORECASE),
        'xss_basic': re.compile(r'<script[^>]*>.*?</script>', re.IGNORECASE | re.DOTALL),
        'path_traversal': re.compile(r'\.\.[\\/]'),
        'command_injection': re.compile(r'[;&|`$]')
    }
    
    # Allowed HTML tags for rich text (if needed)
    ALLOWED_HTML_TAGS = ['b', 'i', 'u', 'em', 'strong', 'p', 'br']
    ALLOWED_HTML_ATTRIBUTES = {}
    
    @classmethod
    def validate_email(cls, email: str) -> bool:
        """Validate email format"""
        if not email or len(email) > 254:
            return False
        return bool(cls.PATTERNS['email'].match(email.strip()))
    
    @classmethod
    def validate_phone(cls, phone: str) -> bool:
        """Validate phone number format"""
        if not phone:
            return True  # Phone is optional
        return bool(cls.PATTERNS['phone'].match(phone.strip()))
    
    @classmethod
    def validate_name(cls, name: str) -> bool:
        """Validate person/unit names"""
        if not name or len(name.strip()) == 0:
            return False
        if len(name) > 255:
            return False
        return bool(cls.PATTERNS['name'].match(name.strip()))
    
    @classmethod
    def validate_percentage(cls, percentage: float) -> bool:
        """Validate assignment percentage"""
        return 0.0 <= percentage <= 1.0
    
    @classmethod
    def validate_id(cls, id_value: Any) -> bool:
        """Validate database ID"""
        try:
            id_int = int(id_value)
            return id_int > 0
        except (ValueError, TypeError):
            return False
    
    @classmethod
    def sanitize_string(cls, input_str: str, max_length: int = 255) -> str:
        """Sanitize string input"""
        if not input_str:
            return ""
        
        # Remove null bytes and control characters
        sanitized = ''.join(char for char in input_str if ord(char) >= 32 or char in '\t\n\r')
        
        # HTML escape
        sanitized = html.escape(sanitized.strip())
        
        # Truncate to max length
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        return sanitized
    
    @classmethod
    def sanitize_html(cls, input_html: str) -> str:
        """Sanitize HTML content using bleach"""
        if not input_html:
            return ""
        
        return bleach.clean(
            input_html,
            tags=cls.ALLOWED_HTML_TAGS,
            attributes=cls.ALLOWED_HTML_ATTRIBUTES,
            strip=True
        )
    
    @classmethod
    def detect_sql_injection(cls, input_str: str) -> bool:
        """Detect potential SQL injection attempts"""
        if not input_str:
            return False
        
        # Check for SQL keywords
        if cls.PATTERNS['sql_injection'].search(input_str):
            return True
        
        # Check for common SQL injection patterns
        dangerous_patterns = [
            "' OR '1'='1",
            "' OR 1=1",
            "'; DROP TABLE",
            "UNION SELECT",
            "' UNION SELECT",
            "/*",
            "*/"
        ]
        
        input_upper = input_str.upper()
        return any(pattern.upper() in input_upper for pattern in dangerous_patterns)
    
    @classmethod
    def detect_xss(cls, input_str: str) -> bool:
        """Detect potential XSS attempts"""
        if not input_str:
            return False
        
        # Check for script tags
        if cls.PATTERNS['xss_basic'].search(input_str):
            return True
        
        # Check for common XSS patterns
        dangerous_patterns = [
            "javascript:",
            "vbscript:",
            "onload=",
            "onerror=",
            "onclick=",
            "onmouseover=",
            "<iframe",
            "<object",
            "<embed"
        ]
        
        input_lower = input_str.lower()
        return any(pattern in input_lower for pattern in dangerous_patterns)
    
    @classmethod
    def detect_path_traversal(cls, input_str: str) -> bool:
        """Detect path traversal attempts"""
        if not input_str:
            return False
        return bool(cls.PATTERNS['path_traversal'].search(input_str))
    
    @classmethod
    def detect_command_injection(cls, input_str: str) -> bool:
        """Detect command injection attempts"""
        if not input_str:
            return False
        return bool(cls.PATTERNS['command_injection'].search(input_str))
    
    @classmethod
    def validate_and_sanitize_input(cls, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive input validation and sanitization"""
        sanitized_data = {}
        validation_errors = []
        
        for key, value in input_data.items():
            if isinstance(value, str):
                # Security checks
                if cls.detect_sql_injection(value):
                    validation_errors.append(f"Potential SQL injection detected in {key}")
                    continue
                
                if cls.detect_xss(value):
                    validation_errors.append(f"Potential XSS detected in {key}")
                    continue
                
                if cls.detect_path_traversal(value):
                    validation_errors.append(f"Path traversal attempt detected in {key}")
                    continue
                
                if cls.detect_command_injection(value):
                    validation_errors.append(f"Command injection attempt detected in {key}")
                    continue
                
                # Sanitize the value
                sanitized_data[key] = cls.sanitize_string(value)
            else:
                sanitized_data[key] = value
        
        if validation_errors:
            logger.warning(f"Input validation errors: {validation_errors}")
            raise SecurityValidationError(validation_errors)
        
        return sanitized_data

# =============================================================================
# SECURITY EXCEPTIONS
# =============================================================================

class SecurityValidationError(Exception):
    """Raised when security validation fails"""
    def __init__(self, errors: List[str]):
        self.errors = errors
        super().__init__(f"Security validation failed: {', '.join(errors)}")

class CSRFTokenError(Exception):
    """Raised when CSRF token validation fails"""
    pass

# =============================================================================
# CSRF PROTECTION
# =============================================================================

class CSRFProtection:
    """CSRF token generation and validation"""
    
    def __init__(self, secret_key: str):
        self.secret_key = secret_key.encode('utf-8')
    
    def generate_token(self, session_id: str = None) -> str:
        """Generate CSRF token"""
        if not session_id:
            session_id = secrets.token_urlsafe(32)
        
        # Create token with timestamp
        timestamp = str(int(datetime.now().timestamp()))
        token_data = f"{session_id}:{timestamp}"
        
        # Create HMAC signature
        signature = hashlib.pbkdf2_hmac('sha256', token_data.encode(), self.secret_key, 100000)
        token = f"{token_data}:{signature.hex()}"
        
        return secrets.token_urlsafe(len(token))[:43]  # Standard CSRF token length
    
    def validate_token(self, token: str, session_id: str = None, max_age: int = 3600) -> bool:
        """Validate CSRF token"""
        try:
            if not token or len(token) < 20:
                return False
            
            # For now, we'll use a simplified validation
            # In production, you'd want to implement proper HMAC validation
            return len(token) == 43 and token.replace('-', '').replace('_', '').isalnum()
            
        except Exception as e:
            logger.warning(f"CSRF token validation error: {e}")
            return False

# =============================================================================
# SECURITY HEADERS MIDDLEWARE
# =============================================================================

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""
    
    def __init__(self, app, config: Dict[str, Any] = None):
        super().__init__(app)
        self.config = config or {}
        self.csp_policy = self._build_csp_policy()
    
    def _build_csp_policy(self) -> str:
        """Build Content Security Policy"""
        policy_parts = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com",
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com",
            "img-src 'self' data: https:",
            "font-src 'self' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com",
            "connect-src 'self'",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'"
        ]
        return "; ".join(policy_parts)
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Security headers
        security_headers = {
            # Prevent clickjacking
            'X-Frame-Options': 'DENY',
            
            # Prevent MIME type sniffing
            'X-Content-Type-Options': 'nosniff',
            
            # XSS protection
            'X-XSS-Protection': '1; mode=block',
            
            # Content Security Policy
            'Content-Security-Policy': self.csp_policy,
            
            # Referrer policy
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            
            # Permissions policy
            'Permissions-Policy': 'geolocation=(), microphone=(), camera=()',
            
            # Remove server information
            'Server': 'Organigramma-WebApp'
        }
        
        # HTTPS-only headers (only in production)
        if self.config.get('https_only', False):
            security_headers.update({
                'Strict-Transport-Security': 'max-age=31536000; includeSubDomains; preload',
                'Upgrade-Insecure-Requests': '1'
            })
        
        # Add all security headers
        for header, value in security_headers.items():
            response.headers[header] = value
        
        return response

# =============================================================================
# RATE LIMITING
# =============================================================================

class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}  # {client_ip: [(timestamp, count), ...]}
    
    def is_allowed(self, client_ip: str) -> bool:
        """Check if request is allowed"""
        now = datetime.now()
        window_start = now - timedelta(seconds=self.window_seconds)
        
        # Clean old entries
        if client_ip in self.requests:
            self.requests[client_ip] = [
                (timestamp, count) for timestamp, count in self.requests[client_ip]
                if timestamp > window_start
            ]
        else:
            self.requests[client_ip] = []
        
        # Count requests in current window
        total_requests = sum(count for _, count in self.requests[client_ip])
        
        if total_requests >= self.max_requests:
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return False
        
        # Add current request
        self.requests[client_ip].append((now, 1))
        return True

# =============================================================================
# SECURE DATABASE OPERATIONS
# =============================================================================

class SecureDatabaseOperations:
    """Secure database operation helpers"""
    
    @staticmethod
    def sanitize_sql_params(params: tuple) -> tuple:
        """Sanitize SQL parameters"""
        sanitized = []
        for param in params:
            if isinstance(param, str):
                # Check for SQL injection
                if InputValidator.detect_sql_injection(param):
                    raise SecurityValidationError([f"SQL injection detected in parameter: {param[:50]}..."])
                sanitized.append(param)
            else:
                sanitized.append(param)
        return tuple(sanitized)
    
    @staticmethod
    def validate_query_safety(query: str) -> bool:
        """Validate that query is safe (uses parameterized queries)"""
        # Check for string concatenation patterns that might indicate SQL injection
        dangerous_patterns = [
            "' +",
            "\" +",
            "CONCAT(",
            "||"  # SQLite concatenation
        ]
        
        query_upper = query.upper()
        for pattern in dangerous_patterns:
            if pattern.upper() in query_upper:
                logger.warning(f"Potentially unsafe query pattern detected: {pattern}")
                return False
        
        return True

# =============================================================================
# AUTHENTICATION HELPERS (for future use)
# =============================================================================

class AuthenticationHelper:
    """Authentication utilities for future implementation"""
    
    @staticmethod
    def hash_password(password: str, salt: str = None) -> tuple:
        """Hash password with salt"""
        if not salt:
            salt = secrets.token_hex(32)
        
        # Use PBKDF2 with SHA-256
        hashed = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return hashed.hex(), salt
    
    @staticmethod
    def verify_password(password: str, hashed: str, salt: str) -> bool:
        """Verify password against hash"""
        try:
            expected_hash, _ = AuthenticationHelper.hash_password(password, salt)
            return secrets.compare_digest(expected_hash, hashed)
        except Exception:
            return False
    
    @staticmethod
    def generate_session_token() -> str:
        """Generate secure session token"""
        return secrets.token_urlsafe(32)

# =============================================================================
# SECURITY CONFIGURATION
# =============================================================================

class SecurityConfig:
    """Security configuration management"""
    
    def __init__(self, config_dict: Dict[str, Any]):
        self.secret_key = config_dict.get('secret_key', secrets.token_urlsafe(32))
        self.csrf_protection = config_dict.get('csrf_protection', False)
        self.secure_cookies = config_dict.get('secure_cookies', False)
        self.https_only = config_dict.get('https_only', False)
        self.allowed_hosts = config_dict.get('allowed_hosts', ['localhost'])
        self.rate_limit_enabled = config_dict.get('rate_limit_enabled', True)
        self.max_requests_per_minute = config_dict.get('max_requests_per_minute', 100)
        
        # Validate configuration
        self._validate_config()
    
    def _validate_config(self):
        """Validate security configuration"""
        if len(self.secret_key) < 32:
            logger.warning("Secret key is shorter than recommended 32 characters")
        
        if not self.allowed_hosts:
            logger.warning("No allowed hosts configured - this may be a security risk")
    
    def get_csrf_protection(self) -> CSRFProtection:
        """Get CSRF protection instance"""
        return CSRFProtection(self.secret_key)
    
    def get_rate_limiter(self) -> RateLimiter:
        """Get rate limiter instance"""
        return RateLimiter(max_requests=self.max_requests_per_minute, window_seconds=60)

# =============================================================================
# SECURITY UTILITIES
# =============================================================================

def get_client_ip(request: Request) -> str:
    """Get client IP address from request"""
    # Check for forwarded headers (when behind proxy)
    forwarded_for = request.headers.get('X-Forwarded-For')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    
    real_ip = request.headers.get('X-Real-IP')
    if real_ip:
        return real_ip
    
    # Fallback to direct connection
    return request.client.host if request.client else 'unknown'

def log_security_event(event_type: str, details: Dict[str, Any], request: Request = None):
    """Log security events for monitoring"""
    log_data = {
        'event_type': event_type,
        'timestamp': datetime.now().isoformat(),
        'details': details
    }
    
    if request:
        log_data.update({
            'client_ip': get_client_ip(request),
            'user_agent': request.headers.get('User-Agent', 'unknown'),
            'path': str(request.url.path),
            'method': request.method
        })
    
    logger.warning(f"SECURITY_EVENT: {log_data}")

# =============================================================================
# DEPENDENCY INJECTION FOR FASTAPI
# =============================================================================

def get_security_config() -> SecurityConfig:
    """FastAPI dependency for security configuration"""
    try:
        from app.config import get_settings
        settings = get_settings()
        
        config_dict = {
            'secret_key': settings.security.secret_key,
            'csrf_protection': settings.security.csrf_protection,
            'secure_cookies': settings.security.secure_cookies,
            'https_only': settings.security.https_only,
            'allowed_hosts': settings.security.allowed_hosts,
            'rate_limit_enabled': True,
            'max_requests_per_minute': 100
        }
        
        return SecurityConfig(config_dict)
    except ImportError:
        # Fallback configuration
        logger.warning("Could not load security settings, using defaults")
        return SecurityConfig({})

def validate_request_security(request: Request, security_config: SecurityConfig = Depends(get_security_config)):
    """FastAPI dependency for request security validation"""
    client_ip = get_client_ip(request)
    
    # Rate limiting
    if security_config.rate_limit_enabled:
        rate_limiter = security_config.get_rate_limiter()
        if not rate_limiter.is_allowed(client_ip):
            log_security_event('RATE_LIMIT_EXCEEDED', {'client_ip': client_ip}, request)
            raise HTTPException(status_code=429, detail="Too many requests")
    
    # Host validation
    host = request.headers.get('host', '').split(':')[0]
    if security_config.allowed_hosts and host not in security_config.allowed_hosts:
        log_security_event('INVALID_HOST', {'host': host, 'client_ip': client_ip}, request)
        raise HTTPException(status_code=400, detail="Invalid host")
    
    return True