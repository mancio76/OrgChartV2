"""
Security middleware for FastAPI application
Integrates security-by-design features into the request/response cycle
"""

import logging
from typing import Dict, Any, Optional
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.security import (
    InputValidator, SecurityValidationError, get_client_ip, 
    log_security_event, SecurityConfig
)

logger = logging.getLogger(__name__)

class SecurityMiddleware(BaseHTTPMiddleware):
    """Comprehensive security middleware"""
    
    def __init__(self, app, security_config: SecurityConfig):
        super().__init__(app)
        self.security_config = security_config
        self.rate_limiter = security_config.get_rate_limiter() if security_config.rate_limit_enabled else None
        
        # Paths that require CSRF protection
        self.csrf_protected_paths = [
            '/units/new', '/units/{id}/edit', '/units/{id}/delete',
            '/persons/new', '/persons/{id}/edit', '/persons/{id}/delete',
            '/job-titles/new', '/job-titles/{id}/edit', '/job-titles/{id}/delete',
            '/assignments/new', '/assignments/{id}/edit', '/assignments/{id}/terminate'
        ]
        
        # Paths that are exempt from rate limiting
        self.rate_limit_exempt_paths = [
            '/static/', '/health', '/api/health'
        ]
    
    async def dispatch(self, request: Request, call_next):
        """Process request through security checks"""
        try:
            # Get client information
            client_ip = get_client_ip(request)
            path = str(request.url.path)
            method = request.method
            
            # Skip security checks for static files
            if path.startswith('/static/'):
                return await call_next(request)
            
            # Host validation
            await self._validate_host(request, client_ip)
            
            # Rate limiting
            if self.rate_limiter and not any(exempt in path for exempt in self.rate_limit_exempt_paths):
                await self._check_rate_limit(request, client_ip)
            
            # Input validation for POST/PUT requests
            if method in ['POST', 'PUT', 'PATCH']:
                await self._validate_request_input(request, client_ip)
            
            # CSRF protection for state-changing operations
            if method in ['POST', 'PUT', 'DELETE', 'PATCH'] and self._requires_csrf_protection(path):
                await self._validate_csrf_token(request, client_ip)
            
            # Process request
            response = await call_next(request)
            
            # Add security headers
            response = self._add_security_headers(response)
            
            return response
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Security middleware error: {e}")
            log_security_event('MIDDLEWARE_ERROR', {'error': str(e)}, request)
            raise HTTPException(status_code=500, detail="Internal security error")
    
    async def _validate_host(self, request: Request, client_ip: str):
        """Validate request host"""
        host = request.headers.get('host', '').split(':')[0]
        
        if self.security_config.allowed_hosts and host not in self.security_config.allowed_hosts:
            log_security_event('INVALID_HOST', {
                'host': host,
                'client_ip': client_ip,
                'allowed_hosts': self.security_config.allowed_hosts
            }, request)
            raise HTTPException(status_code=400, detail="Host non autorizzato")
    
    async def _check_rate_limit(self, request: Request, client_ip: str):
        """Check rate limiting"""
        if not self.rate_limiter.is_allowed(client_ip):
            log_security_event('RATE_LIMIT_EXCEEDED', {
                'client_ip': client_ip,
                'path': str(request.url.path)
            }, request)
            raise HTTPException(status_code=429, detail="Troppe richieste. Riprova più tardi.")
    
    async def _validate_request_input(self, request: Request, client_ip: str):
        """Validate and sanitize request input"""
        try:
            content_type = request.headers.get('content-type', '')
            
            if 'application/json' in content_type:
                # For JSON requests
                try:
                    body = await request.body()
                    if body:
                        import json
                        json_data = json.loads(body)
                        if isinstance(json_data, dict):
                            InputValidator.validate_and_sanitize_input(json_data)
                except json.JSONDecodeError:
                    log_security_event('INVALID_JSON', {'client_ip': client_ip}, request)
                    raise HTTPException(status_code=400, detail="Formato JSON non valido")
            
            elif 'application/x-www-form-urlencoded' in content_type or 'multipart/form-data' in content_type:
                # For form requests - we'll validate in the route handlers
                # since FastAPI handles form parsing
                pass
            
        except SecurityValidationError as e:
            log_security_event('INPUT_VALIDATION_FAILED', {
                'client_ip': client_ip,
                'errors': e.errors
            }, request)
            raise HTTPException(status_code=400, detail="Input non valido rilevato")
    
    def _requires_csrf_protection(self, path: str) -> bool:
        """Check if path requires CSRF protection"""
        # For now, we'll implement a simple check
        # In a full implementation, you'd want more sophisticated path matching
        return any(
            protected_path.replace('{id}', '').rstrip('/') in path 
            for protected_path in self.csrf_protected_paths
        )
    
    async def _validate_csrf_token(self, request: Request, client_ip: str):
        """Validate CSRF token"""
        if not self.security_config.csrf_protection:
            return
        
        # Get CSRF token from header or form data
        csrf_token = request.headers.get('X-CSRF-Token')
        
        if not csrf_token:
            # Try to get from form data (for HTML forms)
            try:
                if request.headers.get('content-type', '').startswith('application/x-www-form-urlencoded'):
                    form_data = await request.form()
                    csrf_token = form_data.get('csrf_token')
            except:
                pass
        
        if not csrf_token:
            log_security_event('MISSING_CSRF_TOKEN', {'client_ip': client_ip}, request)
            raise HTTPException(status_code=403, detail="Token CSRF mancante")
        
        # Validate token
        csrf_protection = self.security_config.get_csrf_protection()
        if not csrf_protection.validate_token(csrf_token):
            log_security_event('INVALID_CSRF_TOKEN', {'client_ip': client_ip}, request)
            raise HTTPException(status_code=403, detail="Token CSRF non valido")
    
    def _add_security_headers(self, response: Response) -> Response:
        """Add security headers to response"""
        security_headers = {
            # Prevent clickjacking
            'X-Frame-Options': 'DENY',
            
            # Prevent MIME type sniffing
            'X-Content-Type-Options': 'nosniff',
            
            # XSS protection
            'X-XSS-Protection': '1; mode=block',
            
            # Content Security Policy
            'Content-Security-Policy': self._get_csp_policy(),
            
            # Referrer policy
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            
            # Permissions policy
            'Permissions-Policy': 'geolocation=(), microphone=(), camera=()',
            
            # Remove server information
            'Server': 'Organigramma-WebApp/1.0'
        }
        
        # HTTPS-only headers (only in production)
        if self.security_config.https_only:
            security_headers.update({
                'Strict-Transport-Security': 'max-age=31536000; includeSubDomains; preload',
                'Upgrade-Insecure-Requests': '1'
            })
        
        # Add all security headers
        for header, value in security_headers.items():
            response.headers[header] = value
        
        return response
    
    def _get_csp_policy(self) -> str:
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

class InputValidationMiddleware(BaseHTTPMiddleware):
    """Specialized middleware for input validation"""
    
    async def dispatch(self, request: Request, call_next):
        """Validate input data"""
        try:
            # Skip validation for GET requests and static files
            if request.method == 'GET' or str(request.url.path).startswith('/static/'):
                return await call_next(request)
            
            # Validate query parameters
            for key, value in request.query_params.items():
                if isinstance(value, str):
                    if InputValidator.detect_sql_injection(value):
                        log_security_event('SQL_INJECTION_ATTEMPT', {
                            'parameter': key,
                            'value': value[:100],
                            'client_ip': get_client_ip(request)
                        }, request)
                        raise HTTPException(status_code=400, detail="Parametro non valido rilevato")
                    
                    if InputValidator.detect_xss(value):
                        log_security_event('XSS_ATTEMPT', {
                            'parameter': key,
                            'value': value[:100],
                            'client_ip': get_client_ip(request)
                        }, request)
                        raise HTTPException(status_code=400, detail="Contenuto non sicuro rilevato")
            
            return await call_next(request)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Input validation middleware error: {e}")
            raise HTTPException(status_code=500, detail="Errore di validazione input")

class SQLInjectionProtectionMiddleware(BaseHTTPMiddleware):
    """Specialized middleware for SQL injection protection"""
    
    def __init__(self, app):
        super().__init__(app)
        self.suspicious_patterns = [
            "' OR '1'='1",
            "' OR 1=1",
            "'; DROP TABLE",
            "UNION SELECT",
            "' UNION SELECT",
            "/**/",
            "' --",
            "' #"
        ]
    
    async def dispatch(self, request: Request, call_next):
        """Check for SQL injection patterns"""
        try:
            # Check URL path
            path = str(request.url.path)
            if self._contains_sql_injection(path):
                log_security_event('SQL_INJECTION_IN_PATH', {
                    'path': path,
                    'client_ip': get_client_ip(request)
                }, request)
                raise HTTPException(status_code=400, detail="Richiesta non valida")
            
            # Check query parameters
            for key, value in request.query_params.items():
                if self._contains_sql_injection(str(value)):
                    log_security_event('SQL_INJECTION_IN_QUERY', {
                        'parameter': key,
                        'value': str(value)[:100],
                        'client_ip': get_client_ip(request)
                    }, request)
                    raise HTTPException(status_code=400, detail="Parametro non sicuro")
            
            return await call_next(request)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"SQL injection protection error: {e}")
            raise HTTPException(status_code=500, detail="Errore di protezione SQL")
    
    def _contains_sql_injection(self, text: str) -> bool:
        """Check if text contains SQL injection patterns"""
        text_upper = text.upper()
        return any(pattern.upper() in text_upper for pattern in self.suspicious_patterns)