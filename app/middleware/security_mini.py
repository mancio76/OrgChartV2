# Create: app/middleware/simple_csrf.py
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import secrets
import hmac
import hashlib

class MiniSecurityMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, secret_key: str):
        super().__init__(app)
        self.secret_key = secret_key.encode()
    
    async def dispatch(self, request, call_next):
        # Generate CSRF token for GET requests
        if request.method == "GET":
            csrf_token = self._generate_token(request)
            request.state.csrf_token = csrf_token
        
        # Validate CSRF token for POST requests
        elif request.method in ["POST", "PUT", "DELETE", "PATCH"]:
            if not await self._validate_token(request):
                return Response("CSRF token invalid", status_code=403)
        
        response = await call_next(request)
        return response
    
    def _generate_token(self, request) -> str:
        """Generate CSRF token"""
        session_id = request.session.get('session_id')
        if not session_id:
            session_id = secrets.token_urlsafe(32)
            request.session['session_id'] = session_id
        
        # Create HMAC-based token
        message = f"{session_id}:{request.client.host}"
        signature = hmac.new(self.secret_key, message.encode(), hashlib.sha256).hexdigest()
        return f"{session_id}.{signature}"
    
    async def _validate_token(self, request) -> bool:
        """Validate CSRF token"""
        # Get token from form or header
        token = None
        
        if request.headers.get("content-type", "").startswith("application/x-www-form-urlencoded"):
            form = await request.form()
            token = form.get("csrf_token")
        else:
            token = request.headers.get("X-CSRF-Token")
        
        if not token:
            return False
        
        try:
            session_id, signature = token.split('.', 1)
        except ValueError:
            return False
        
        # Verify signature
        expected_message = f"{session_id}:{request.client.host}"
        expected_signature = hmac.new(self.secret_key, expected_message.encode(), hashlib.sha256).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)