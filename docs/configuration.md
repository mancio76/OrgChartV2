# Environment-Based Configuration Guide

This document describes the environment-based configuration system for the Organigramma Web App.

## Overview

The application uses environment variables and `.env` files to manage configuration across different deployment environments (development, testing, staging, production). This approach follows security-by-design principles and enables flexible deployment without code changes.

## Configuration Files

### `.env` File

The main configuration file for your environment. Copy from `.env.example` and customize:

```bash
cp .env.example .env
```

### `.env.example` File

Template file showing all available configuration options with production-ready defaults.

## Configuration Categories

### Application Settings

```bash
APP_TITLE=Organigramma Web App
APP_DESCRIPTION=Sistema di gestione organigramma aziendale con storicizzazione
APP_VERSION=1.0.0
ENVIRONMENT=development  # development, testing, staging, production
TIMEZONE=Europe/Rome
```

### Server Configuration

```bash
SERVER_HOST=127.0.0.1    # 0.0.0.0 for production
SERVER_PORT=8000
DEBUG=true               # false for production
RELOAD=true              # false for production
WORKERS=1                # 4+ for production
ACCESS_LOG=true
```

### Database Configuration

```bash
DATABASE_URL=sqlite:///database/orgchart.db
DATABASE_ENABLE_FOREIGN_KEYS=true
DATABASE_BACKUP_ENABLED=true
DATABASE_BACKUP_SCHEDULE=daily
DATABASE_BACKUP_DIRECTORY=backups
```

### Logging Configuration

```bash
LOG_LEVEL=INFO           # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_TO_CONSOLE=true
LOG_TO_FILE=true
LOG_FILE_PATH=app.log
LOG_MAX_FILE_SIZE=10485760  # 10MB
LOG_BACKUP_COUNT=5
LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(message)s
```

### Security Configuration

```bash
SECRET_KEY=your-secure-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ORIGINS=                        # comma-separated origins
CSRF_PROTECTION=true
SECURE_COOKIES=false                 # true for production
HTTPS_ONLY=false                     # true for production
```

## Environment-Specific Configurations

### Development Environment

```bash
ENVIRONMENT=development
DEBUG=true
RELOAD=true
LOG_LEVEL=INFO
SERVER_HOST=127.0.0.1
SECURE_COOKIES=false
HTTPS_ONLY=false
```

### Production Environment

```bash
ENVIRONMENT=production
DEBUG=false
RELOAD=false
LOG_LEVEL=WARNING
SERVER_HOST=0.0.0.0
WORKERS=4
SECURE_COOKIES=true
HTTPS_ONLY=true
SECRET_KEY=your-very-secure-production-key
```

## Security Best Practices

### Secret Key Management

1. **Generate Secure Keys**:
   ```bash
   python scripts/generate_secret_key.py
   ```

2. **Use Different Keys per Environment**:
   - Development: Can use shorter keys for convenience
   - Production: Must use cryptographically secure keys (32+ characters)

3. **Never Commit Secret Keys**:
   - Add `.env` to `.gitignore`
   - Use environment variables in CI/CD
   - Use secret management services in production

### Production Security Checklist

- [ ] `DEBUG=false`
- [ ] `HTTPS_ONLY=true`
- [ ] `SECURE_COOKIES=true`
- [ ] Strong `SECRET_KEY` (32+ characters)
- [ ] Appropriate `ALLOWED_HOSTS`
- [ ] `LOG_LEVEL=WARNING` or higher
- [ ] `CSRF_PROTECTION=true`

## Utility Scripts

### Generate Secret Key

```bash
python scripts/generate_secret_key.py
```

Generates a cryptographically secure secret key for production use.

### Validate Configuration

```bash
python scripts/validate_config.py
```

Validates your configuration and provides security recommendations.

### Test Configuration

```bash
python test_configuration.py
```

Tests the configuration system to ensure it's working correctly.

## Configuration Loading

The configuration system loads settings in this order:

1. Default values (defined in `app/config.py`)
2. Environment variables
3. `.env` file values (if present)

Environment variables take precedence over `.env` file values.

## Accessing Configuration in Code

```python
from app.config import get_settings

settings = get_settings()

# Access configuration
print(settings.application.title)
print(settings.server.port)
print(settings.database.url)
```

## Directory Structure

The configuration system automatically creates required directories:

- Database directory (from `DATABASE_URL`)
- Log directory (from `LOG_FILE_PATH`)
- Backup directory (from `DATABASE_BACKUP_DIRECTORY`)

## Troubleshooting

### Common Issues

1. **Configuration Not Loading**:
   - Check `.env` file exists and is readable
   - Verify environment variable names are correct
   - Run `python test_configuration.py` to diagnose

2. **Database Connection Issues**:
   - Ensure database directory exists and is writable
   - Check `DATABASE_URL` format
   - Verify foreign key settings

3. **Logging Issues**:
   - Check log directory permissions
   - Verify `LOG_FILE_PATH` is writable
   - Test with console logging only

### Validation Errors

Run the validation script to identify configuration issues:

```bash
python scripts/validate_config.py
```

Common validation errors:
- Invalid log level
- Port out of range
- Debug mode enabled in production
- Weak secret key
- Missing required directories

## Migration from Legacy Configuration

The system maintains backward compatibility with legacy environment variables:

- `RUN_HOST` → `SERVER_HOST`
- `RUN_PORT` → `SERVER_PORT`
- `RUN_DEBUG` → `DEBUG`
- `RUN_LOG_LEVEL` → `LOG_LEVEL`

## Examples

### Docker Environment

```dockerfile
ENV ENVIRONMENT=production
ENV DEBUG=false
ENV SERVER_HOST=0.0.0.0
ENV SERVER_PORT=8000
ENV DATABASE_URL=sqlite:///data/orgchart.db
ENV SECRET_KEY=your-docker-secret-key
```

### Kubernetes ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: orgchart-config
data:
  ENVIRONMENT: "production"
  DEBUG: "false"
  SERVER_HOST: "0.0.0.0"
  SERVER_PORT: "8000"
  LOG_LEVEL: "WARNING"
```

### CI/CD Pipeline

```yaml
env:
  ENVIRONMENT: testing
  DEBUG: false
  SECRET_KEY: ${{ secrets.SECRET_KEY }}
  DATABASE_URL: sqlite:///test.db
```

## Support

For configuration issues:

1. Run `python scripts/validate_config.py`
2. Check application logs
3. Verify environment variables
4. Test with minimal configuration