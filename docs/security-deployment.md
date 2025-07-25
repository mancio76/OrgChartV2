# Security Deployment Guide
## Organigramma Web App - Security-by-Design Implementation

This guide covers the security features implemented in the Organigramma Web App and provides deployment recommendations for production environments.

## 🔒 Security Features Implemented

### 1. Input Validation and Sanitization

#### Comprehensive Input Validation
- **SQL Injection Prevention**: All user inputs are validated against SQL injection patterns
- **XSS Protection**: HTML content is sanitized and escaped
- **Path Traversal Protection**: File path inputs are validated
- **Command Injection Prevention**: System command patterns are blocked

#### Validation Classes
- `InputValidator`: Main validation class with pattern matching
- `SecurityValidationError`: Custom exception for security violations
- Form data sanitization in all CRUD operations

### 2. SQL Injection Protection

#### Database Layer Security
- **Parameterized Queries**: All database operations use parameterized queries
- **Query Safety Validation**: Automatic detection of unsafe query patterns
- **Parameter Sanitization**: All SQL parameters are sanitized before execution

#### Implementation Details
```python
# Example from database.py
def execute_query(self, query: str, params: tuple = None) -> sqlite3.Cursor:
    # Security validation
    if not SecureDatabaseOperations.validate_query_safety(query):
        raise ValueError("Unsafe query pattern detected")
    
    # Sanitize parameters
    if params:
        params = SecureDatabaseOperations.sanitize_sql_params(params)
```

### 3. Security Headers

#### Implemented Headers
- **X-Frame-Options**: `DENY` - Prevents clickjacking
- **X-Content-Type-Options**: `nosniff` - Prevents MIME type sniffing
- **X-XSS-Protection**: `1; mode=block` - Browser XSS protection
- **Content-Security-Policy**: Restrictive CSP policy
- **Referrer-Policy**: `strict-origin-when-cross-origin`
- **Permissions-Policy**: Restricts browser features
- **Strict-Transport-Security**: HTTPS enforcement (production only)

#### Content Security Policy
```
default-src 'self';
script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com;
style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com;
img-src 'self' data: https:;
font-src 'self' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com;
connect-src 'self';
frame-ancestors 'none';
base-uri 'self';
form-action 'self'
```

### 4. CSRF Protection

#### Token-Based Protection
- **CSRF Token Generation**: Secure token generation using secrets module
- **Token Validation**: Automatic validation for state-changing operations
- **Session Integration**: Tokens tied to user sessions

#### Protected Operations
- All POST, PUT, DELETE, PATCH requests
- Form submissions for CRUD operations
- API endpoints that modify data

### 5. Rate Limiting

#### Request Rate Limiting
- **Per-IP Limiting**: 100 requests per minute per IP address
- **Configurable Limits**: Adjustable through environment variables
- **Exempt Paths**: Static files and health checks excluded

#### Implementation
```python
class RateLimiter:
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
```

### 6. Security Middleware Stack

#### Middleware Order (execution order)
1. **SecurityMiddleware**: Main security checks and headers
2. **InputValidationMiddleware**: Input validation and sanitization
3. **SQLInjectionProtectionMiddleware**: SQL injection pattern detection

#### Security Event Logging
All security events are logged with:
- Event type and timestamp
- Client IP address and user agent
- Request path and method
- Security violation details

## 🚀 Production Deployment

### 1. Environment Configuration

#### Production Environment File
Use the provided `config/production.env` template:

```bash
# Copy and customize production configuration
cp config/production.env .env.production

# Generate secure secret key
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

#### Critical Settings for Production
```bash
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=<64-character-secure-key>
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
HTTPS_ONLY=true
SECURE_COOKIES=true
CSRF_PROTECTION=true
```

### 2. SSL/TLS Configuration

#### Requirements
- Valid SSL/TLS certificate
- HTTPS enforcement
- Secure cookie settings
- HSTS headers enabled

#### Nginx Configuration Example
```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;
    
    # Security headers (additional to app headers)
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /static/ {
        alias /path/to/app/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### 3. Database Security

#### SQLite Production Settings
```bash
# Secure database location
DATABASE_URL=sqlite:///data/orgchart.db

# Enable all security features
DATABASE_ENABLE_FOREIGN_KEYS=true

# Secure backup location
DATABASE_BACKUP_DIRECTORY=/var/backups/orgchart
```

#### File Permissions
```bash
# Set secure permissions
chmod 600 /data/orgchart.db
chmod 700 /data/
chmod 700 /var/backups/orgchart/
```

### 4. Logging and Monitoring

#### Production Logging
```bash
LOG_LEVEL=WARNING
LOG_TO_FILE=true
LOG_FILE_PATH=/var/log/orgchart/app.log
LOG_MAX_FILE_SIZE=52428800  # 50MB
LOG_BACKUP_COUNT=10
```

#### Security Event Monitoring
Monitor these log patterns:
- `SECURITY_EVENT`: All security violations
- `RATE_LIMIT_EXCEEDED`: Rate limiting triggers
- `SQL_INJECTION_ATTEMPT`: SQL injection attempts
- `XSS_ATTEMPT`: XSS attempts
- `INVALID_HOST`: Invalid host headers

### 5. Firewall Configuration

#### Required Ports
```bash
# Allow only necessary ports
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP (redirect to HTTPS)
ufw allow 443/tcp   # HTTPS
ufw deny 8000/tcp   # Block direct app access
```

### 6. System Hardening

#### User and Permissions
```bash
# Create dedicated user
useradd -r -s /bin/false orgchart

# Set ownership
chown -R orgchart:orgchart /path/to/app
chown -R orgchart:orgchart /data
chown -R orgchart:orgchart /var/log/orgchart
```

#### Systemd Service
```ini
[Unit]
Description=Organigramma Web App
After=network.target

[Service]
Type=exec
User=orgchart
Group=orgchart
WorkingDirectory=/path/to/app
Environment=PATH=/path/to/venv/bin
EnvironmentFile=/path/to/app/.env.production
ExecStart=/path/to/venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 4
Restart=always
RestartSec=3

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/data /var/log/orgchart /var/backups/orgchart

[Install]
WantedBy=multi-user.target
```

## 🔍 Security Testing

### 1. Automated Security Tests

#### SQL Injection Testing
```python
# Test SQL injection protection
def test_sql_injection_protection():
    malicious_inputs = [
        "'; DROP TABLE units; --",
        "' OR '1'='1",
        "UNION SELECT * FROM users"
    ]
    
    for input_data in malicious_inputs:
        response = client.post("/units/new", data={"name": input_data})
        assert response.status_code == 400
```

#### XSS Testing
```python
# Test XSS protection
def test_xss_protection():
    xss_payloads = [
        "<script>alert('xss')</script>",
        "javascript:alert('xss')",
        "<img src=x onerror=alert('xss')>"
    ]
    
    for payload in xss_payloads:
        response = client.post("/units/new", data={"name": payload})
        assert response.status_code == 400
```

### 2. Manual Security Testing

#### Security Headers Verification
```bash
# Check security headers
curl -I https://yourdomain.com/

# Expected headers:
# X-Frame-Options: DENY
# X-Content-Type-Options: nosniff
# X-XSS-Protection: 1; mode=block
# Content-Security-Policy: ...
# Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
```

#### Rate Limiting Test
```bash
# Test rate limiting
for i in {1..110}; do
    curl -s -o /dev/null -w "%{http_code}\n" https://yourdomain.com/api/health
done
# Should return 429 after 100 requests
```

## 📋 Security Checklist

### Pre-Deployment
- [ ] Generate secure SECRET_KEY (64+ characters)
- [ ] Configure ALLOWED_HOSTS for production domain
- [ ] Enable HTTPS_ONLY and SECURE_COOKIES
- [ ] Set up SSL/TLS certificate
- [ ] Configure reverse proxy (nginx/Apache)
- [ ] Set secure file permissions
- [ ] Configure firewall rules
- [ ] Set up dedicated system user
- [ ] Configure log rotation
- [ ] Test all security features

### Post-Deployment
- [ ] Verify security headers in browser
- [ ] Test rate limiting functionality
- [ ] Verify CSRF protection works
- [ ] Check SSL/TLS configuration
- [ ] Monitor security event logs
- [ ] Set up automated backups
- [ ] Configure monitoring and alerting
- [ ] Perform penetration testing
- [ ] Document incident response procedures
- [ ] Schedule regular security reviews

## 🚨 Incident Response

### Security Event Response
1. **Immediate**: Block malicious IP addresses
2. **Investigation**: Review security event logs
3. **Assessment**: Determine scope of potential breach
4. **Containment**: Isolate affected systems
5. **Recovery**: Restore from secure backups if needed
6. **Documentation**: Record incident details
7. **Prevention**: Update security measures

### Log Analysis
```bash
# Search for security events
grep "SECURITY_EVENT" /var/log/orgchart/app.log

# Monitor failed attempts
grep "SQL_INJECTION\|XSS_ATTEMPT" /var/log/orgchart/app.log

# Check rate limiting
grep "RATE_LIMIT_EXCEEDED" /var/log/orgchart/app.log
```

## 📚 Additional Resources

### Security Best Practices
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [SQLite Security](https://www.sqlite.org/security.html)

### Monitoring Tools
- [Fail2ban](https://www.fail2ban.org/) - Intrusion prevention
- [OSSEC](https://www.ossec.net/) - Host-based intrusion detection
- [Prometheus](https://prometheus.io/) - Monitoring and alerting

### Regular Updates
- Keep Python and dependencies updated
- Monitor security advisories
- Regular security assessments
- Update SSL/TLS certificates
- Review and update security policies

---

**Note**: This security implementation follows industry best practices and provides defense-in-depth protection. Regular security reviews and updates are essential for maintaining security posture.