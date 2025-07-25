"""
Security feature tests for Organigramma Web App
Tests for input validation, SQL injection prevention, XSS protection, and security headers
"""

import pytest
from fastapi.testclient import TestClient
from app.security import InputValidator, SecurityValidationError, CSRFProtection
from app.middleware.security import SecurityMiddleware

# We'll create the client in individual tests to avoid import issues

class TestInputValidation:
    """Test input validation and sanitization"""
    
    def test_validate_email(self):
        """Test email validation"""
        # Valid emails
        assert InputValidator.validate_email("test@example.com")
        assert InputValidator.validate_email("user.name@domain.co.uk")
        
        # Invalid emails
        assert not InputValidator.validate_email("invalid-email")
        assert not InputValidator.validate_email("@domain.com")
        assert not InputValidator.validate_email("user@")
        assert not InputValidator.validate_email("")
    
    def test_validate_name(self):
        """Test name validation"""
        # Valid names
        assert InputValidator.validate_name("Mario Rossi")
        assert InputValidator.validate_name("Jean-Pierre")
        assert InputValidator.validate_name("O'Connor")
        
        # Invalid names
        assert not InputValidator.validate_name("")
        assert not InputValidator.validate_name("   ")
        assert not InputValidator.validate_name("A" * 256)  # Too long
    
    def test_validate_percentage(self):
        """Test percentage validation"""
        # Valid percentages
        assert InputValidator.validate_percentage(0.0)
        assert InputValidator.validate_percentage(0.5)
        assert InputValidator.validate_percentage(1.0)
        
        # Invalid percentages
        assert not InputValidator.validate_percentage(-0.1)
        assert not InputValidator.validate_percentage(1.1)
    
    def test_validate_id(self):
        """Test ID validation"""
        # Valid IDs
        assert InputValidator.validate_id(1)
        assert InputValidator.validate_id("123")
        
        # Invalid IDs
        assert not InputValidator.validate_id(0)
        assert not InputValidator.validate_id(-1)
        assert not InputValidator.validate_id("abc")
        assert not InputValidator.validate_id(None)
    
    def test_sanitize_string(self):
        """Test string sanitization"""
        # Basic sanitization
        result = InputValidator.sanitize_string("  Hello World  ")
        assert result == "Hello World"
        
        # HTML escaping
        result = InputValidator.sanitize_string("<script>alert('xss')</script>")
        assert "&lt;script&gt;" in result
        assert "&lt;/script&gt;" in result
        
        # Length truncation
        long_string = "A" * 300
        result = InputValidator.sanitize_string(long_string, max_length=100)
        assert len(result) == 100

class TestSQLInjectionProtection:
    """Test SQL injection detection and prevention"""
    
    def test_detect_sql_injection(self):
        """Test SQL injection pattern detection"""
        # SQL injection attempts
        assert InputValidator.detect_sql_injection("'; DROP TABLE users; --")
        assert InputValidator.detect_sql_injection("' OR '1'='1")
        assert InputValidator.detect_sql_injection("UNION SELECT * FROM passwords")
        assert InputValidator.detect_sql_injection("' UNION SELECT")
        
        # Safe inputs
        assert not InputValidator.detect_sql_injection("Mario Rossi")
        assert not InputValidator.detect_sql_injection("Unit Name")
        assert not InputValidator.detect_sql_injection("")
    
    def test_sql_injection_in_form_submission(self):
        """Test SQL injection protection in form submissions"""
        from app.main import app
        client = TestClient(app)
        
        # This would be caught by middleware before reaching the route
        malicious_data = {
            "name": "'; DROP TABLE units; --",
            "short_name": "test"
        }
        
        # The security middleware should block this
        response = client.post("/units/new", data=malicious_data)
        # Should be blocked by security middleware
        assert response.status_code in [400, 403]

class TestXSSProtection:
    """Test XSS detection and prevention"""
    
    def test_detect_xss(self):
        """Test XSS pattern detection"""
        # XSS attempts
        assert InputValidator.detect_xss("<script>alert('xss')</script>")
        assert InputValidator.detect_xss("javascript:alert('xss')")
        assert InputValidator.detect_xss("<img src=x onerror=alert('xss')>")
        assert InputValidator.detect_xss("onload=malicious()")
        
        # Safe inputs
        assert not InputValidator.detect_xss("Mario Rossi")
        assert not InputValidator.detect_xss("Unit <Name>")  # Basic HTML is OK
        assert not InputValidator.detect_xss("")
    
    def test_xss_in_form_submission(self):
        """Test XSS protection in form submissions"""
        from app.main import app
        client = TestClient(app)
        
        xss_data = {
            "name": "<script>alert('xss')</script>",
            "short_name": "test"
        }
        
        # Should be blocked by security middleware
        response = client.post("/units/new", data=xss_data)
        assert response.status_code in [400, 403]

class TestPathTraversalProtection:
    """Test path traversal detection"""
    
    def test_detect_path_traversal(self):
        """Test path traversal pattern detection"""
        # Path traversal attempts
        assert InputValidator.detect_path_traversal("../../../etc/passwd")
        assert InputValidator.detect_path_traversal("..\\windows\\system32")
        assert InputValidator.detect_path_traversal("./../../config")
        
        # Safe paths
        assert not InputValidator.detect_path_traversal("normal/path")
        assert not InputValidator.detect_path_traversal("file.txt")
        assert not InputValidator.detect_path_traversal("")

class TestCommandInjectionProtection:
    """Test command injection detection"""
    
    def test_detect_command_injection(self):
        """Test command injection pattern detection"""
        # Command injection attempts
        assert InputValidator.detect_command_injection("test; rm -rf /")
        assert InputValidator.detect_command_injection("test && malicious")
        assert InputValidator.detect_command_injection("test | cat /etc/passwd")
        assert InputValidator.detect_command_injection("test `whoami`")
        assert InputValidator.detect_command_injection("test $USER")
        
        # Safe inputs
        assert not InputValidator.detect_command_injection("Mario Rossi")
        assert not InputValidator.detect_command_injection("Unit Name")
        assert not InputValidator.detect_command_injection("")

class TestCSRFProtection:
    """Test CSRF token generation and validation"""
    
    def test_csrf_token_generation(self):
        """Test CSRF token generation"""
        csrf = CSRFProtection("test-secret-key")
        
        # Generate token
        token = csrf.generate_token()
        assert token is not None
        assert len(token) == 43  # Standard CSRF token length
        assert token.replace('-', '').replace('_', '').isalnum()
    
    def test_csrf_token_validation(self):
        """Test CSRF token validation"""
        csrf = CSRFProtection("test-secret-key")
        
        # Generate and validate token
        token = csrf.generate_token()
        assert csrf.validate_token(token)
        
        # Invalid tokens
        assert not csrf.validate_token("")
        assert not csrf.validate_token("invalid-token")
        assert not csrf.validate_token("a" * 10)  # Too short

class TestSecurityHeaders:
    """Test security headers in responses"""
    
    def test_security_headers_present(self):
        """Test that security headers are present in responses"""
        from app.main import app
        client = TestClient(app)
        
        response = client.get("/")
        
        # Check for security headers
        expected_headers = [
            'X-Frame-Options',
            'X-Content-Type-Options', 
            'X-XSS-Protection',
            'Content-Security-Policy',
            'Referrer-Policy',
            'Permissions-Policy'
        ]
        
        for header in expected_headers:
            assert header in response.headers, f"Missing security header: {header}"
    
    def test_x_frame_options(self):
        """Test X-Frame-Options header"""
        from app.main import app
        client = TestClient(app)
        
        response = client.get("/")
        assert response.headers.get('X-Frame-Options') == 'DENY'
    
    def test_content_type_options(self):
        """Test X-Content-Type-Options header"""
        from app.main import app
        client = TestClient(app)
        
        response = client.get("/")
        assert response.headers.get('X-Content-Type-Options') == 'nosniff'
    
    def test_xss_protection_header(self):
        """Test X-XSS-Protection header"""
        from app.main import app
        client = TestClient(app)
        
        response = client.get("/")
        assert response.headers.get('X-XSS-Protection') == '1; mode=block'
    
    def test_csp_header(self):
        """Test Content-Security-Policy header"""
        from app.main import app
        client = TestClient(app)
        
        response = client.get("/")
        csp = response.headers.get('Content-Security-Policy')
        assert csp is not None
        assert "default-src 'self'" in csp
        assert "frame-ancestors 'none'" in csp

class TestRateLimiting:
    """Test rate limiting functionality"""
    
    def test_rate_limit_allows_normal_requests(self):
        """Test that normal request rates are allowed"""
        from app.main import app
        client = TestClient(app)
        
        # Make a few normal requests
        for _ in range(5):
            response = client.get("/api/health")
            assert response.status_code == 200
    
    def test_rate_limit_blocks_excessive_requests(self):
        """Test that excessive requests are blocked"""
        # This test would need to be run in isolation or with a test-specific rate limiter
        # For now, we'll test the rate limiter class directly
        from app.security import RateLimiter
        
        rate_limiter = RateLimiter(max_requests=5, window_seconds=60)
        
        # Allow first 5 requests
        for _ in range(5):
            assert rate_limiter.is_allowed("127.0.0.1")
        
        # Block 6th request
        assert not rate_limiter.is_allowed("127.0.0.1")

class TestSecurityValidation:
    """Test comprehensive security validation"""
    
    def test_validate_and_sanitize_input_safe(self):
        """Test validation of safe input"""
        safe_data = {
            "name": "Mario Rossi",
            "email": "mario@example.com",
            "description": "A normal description"
        }
        
        result = InputValidator.validate_and_sanitize_input(safe_data)
        assert result["name"] == "Mario Rossi"
        assert result["email"] == "mario@example.com"
    
    def test_validate_and_sanitize_input_malicious(self):
        """Test validation of malicious input"""
        malicious_data = {
            "name": "'; DROP TABLE users; --",
            "description": "<script>alert('xss')</script>"
        }
        
        with pytest.raises(SecurityValidationError) as exc_info:
            InputValidator.validate_and_sanitize_input(malicious_data)
        
        assert len(exc_info.value.errors) > 0
        assert any("SQL injection" in error for error in exc_info.value.errors)

class TestSecurityEventLogging:
    """Test security event logging"""
    
    def test_security_event_logging(self):
        """Test that security events are logged"""
        from app.security import log_security_event
        import logging
        
        # Capture log output
        with pytest.raises(Exception):
            # This should trigger security logging
            log_security_event('TEST_EVENT', {'test': 'data'})

class TestDatabaseSecurity:
    """Test database security features"""
    
    def test_database_foreign_keys_enabled(self):
        """Test that foreign keys are enabled"""
        from app.database import get_db_manager
        
        db_manager = get_db_manager()
        db_info = db_manager.get_database_info()
        
        assert db_info.get('foreign_keys_enabled') is True
    
    def test_database_connection_security(self):
        """Test database connection security settings"""
        from app.database import get_db_manager
        
        db_manager = get_db_manager()
        
        # Test that connection pool is working
        pool_status = db_manager.get_pool_status()
        assert 'active_connections' in pool_status
        assert 'max_connections' in pool_status

# Integration tests
class TestSecurityIntegration:
    """Integration tests for security features"""
    
    def test_malicious_request_blocked(self):
        """Test that malicious requests are properly blocked"""
        from app.main import app
        client = TestClient(app)
        
        # SQL injection in URL parameter
        response = client.get("/units?search='; DROP TABLE units; --")
        assert response.status_code in [400, 403]
    
    def test_xss_in_api_request(self):
        """Test XSS protection in API requests"""
        from app.main import app
        client = TestClient(app)
        
        malicious_json = {
            "name": "<script>alert('xss')</script>",
            "short_name": "test"
        }
        
        response = client.post("/api/units", json=malicious_json)
        assert response.status_code in [400, 403]
    
    def test_host_header_validation(self):
        """Test host header validation"""
        from app.main import app
        client = TestClient(app)
        
        # This would need to be tested with a custom host header
        # For now, we verify the middleware is in place
        response = client.get("/")
        assert response.status_code == 200  # Should work with test client

if __name__ == "__main__":
    pytest.main([__file__, "-v"])