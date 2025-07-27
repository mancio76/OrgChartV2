"""
CSRF Protection Utilities for Production
File: app/security_csrf.py - THIS FILE
"""

import secrets
import logging
from fastapi import Request, Form, HTTPException, Depends
from app.security import CSRFProtection, get_security_config

logger = logging.getLogger(__name__)

def get_csrf_protection(security_config = Depends(get_security_config)) -> CSRFProtection:
    """FastAPI dependency to get CSRF protection instance"""
    return security_config.get_csrf_protection()

def get_or_create_session_id(request: Request) -> str:
    """Get or create session ID for CSRF token generation"""
    # Now request.session works thanks to SessionMiddleware + itsdangerous
    session_id = request.session.get('session_id')
    if not session_id:
        session_id = secrets.token_urlsafe(32)
        request.session['session_id'] = session_id
        logger.debug(f"Created new session ID: {session_id[:8]}...")
    return session_id

def generate_csrf_token(
    request: Request, 
    csrf_protection: CSRFProtection = Depends(get_csrf_protection)
) -> str:
    """Generate CSRF token for forms"""
    session_id = get_or_create_session_id(request)
    token = csrf_protection.generate_token(session_id)
    logger.debug(f"Generated CSRF token for session: {session_id[:8]}...")
    return token

def validate_csrf_token(
    request: Request,
    csrf_token: str = Form(alias="csrf_token"),
    csrf_protection: CSRFProtection = Depends(get_csrf_protection)
) -> bool:
    """Validate CSRF token from form data"""
    session_id = request.session.get('session_id')
    if not session_id:
        logger.warning("CSRF validation failed: No session ID found")
        raise HTTPException(status_code=403, detail="No valid session found")
    
    if not csrf_protection.validate_token(csrf_token, session_id):
        logger.warning(f"CSRF validation failed for session: {session_id[:8]}...")
        raise HTTPException(status_code=403, detail="CSRF token validation failed")
    
    logger.debug(f"CSRF validation successful for session: {session_id[:8]}...")
    return True

def add_csrf_to_context(request: Request, context: dict) -> dict:
    """Helper function to add CSRF token to template context"""
    from app.security import get_security_config
    
    security_config = get_security_config()
    csrf_protection = security_config.get_csrf_protection()
    csrf_token = generate_csrf_token(request, csrf_protection)
    
    context['csrf_token'] = csrf_token
    return context

# Convenience functions for routes
def csrf_protected_form(request: Request) -> str:
    """Quick helper to get CSRF token for forms"""
    from app.security import get_security_config
    security_config = get_security_config()
    csrf_protection = security_config.get_csrf_protection()
    return generate_csrf_token(request, csrf_protection)