"""
Gunicorn configuration for Organigramma Web App
Production ASGI server configuration with multiple workers
"""

import os
import multiprocessing
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# =============================================================================
# SERVER SOCKET
# =============================================================================
bind = f"{os.getenv('SERVER_HOST', '0.0.0.0')}:{os.getenv('SERVER_PORT', '8000')}"
backlog = 2048

# =============================================================================
# WORKER PROCESSES
# =============================================================================
# Calculate workers based on CPU cores (2 * cores + 1) or use environment variable
workers = int(os.getenv('WORKERS', multiprocessing.cpu_count() * 2 + 1))
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
preload_app = True
timeout = 30
keepalive = 2

# =============================================================================
# LOGGING
# =============================================================================
# Logging configuration
log_level = os.getenv('LOG_LEVEL', 'info').lower()
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Log files
log_dir = Path(os.getenv('LOG_FILE_PATH', 'app.log')).parent
log_dir.mkdir(parents=True, exist_ok=True)

accesslog = str(log_dir / 'access.log') if os.getenv('ACCESS_LOG', 'true').lower() == 'true' else None
errorlog = str(log_dir / 'error.log')

# Disable access log if not needed
if os.getenv('ACCESS_LOG', 'true').lower() == 'false':
    accesslog = None

# =============================================================================
# PROCESS NAMING
# =============================================================================
proc_name = 'organigramma-web-app'

# =============================================================================
# SERVER MECHANICS
# =============================================================================
daemon = False
pidfile = '/tmp/gunicorn.pid'
user = None
group = None
tmp_upload_dir = None

# =============================================================================
# SSL (if needed)
# =============================================================================
# Uncomment and configure for HTTPS
# keyfile = '/path/to/keyfile'
# certfile = '/path/to/certfile'

# =============================================================================
# WORKER LIFECYCLE HOOKS
# =============================================================================
def on_starting(server):
    """Called just before the master process is initialized."""
    server.log.info("Starting Organigramma Web App with Gunicorn")

def on_reload(server):
    """Called to recycle workers during a reload via SIGHUP."""
    server.log.info("Reloading Organigramma Web App")

def when_ready(server):
    """Called just after the server is started."""
    server.log.info(f"Organigramma Web App ready. Listening on {bind}")
    server.log.info(f"Workers: {workers}")
    server.log.info(f"Worker class: {worker_class}")

def worker_int(worker):
    """Called just after a worker exited on SIGINT or SIGQUIT."""
    worker.log.info(f"Worker {worker.pid} received INT or QUIT signal")

def pre_fork(server, worker):
    """Called just before a worker is forked."""
    server.log.debug(f"Worker {worker.pid} about to be forked")

def post_fork(server, worker):
    """Called just after a worker has been forked."""
    server.log.debug(f"Worker {worker.pid} spawned")

def post_worker_init(worker):
    """Called just after a worker has initialized the application."""
    worker.log.info(f"Worker {worker.pid} initialized")

def worker_abort(worker):
    """Called when a worker received the SIGABRT signal."""
    worker.log.info(f"Worker {worker.pid} received SIGABRT signal")

# =============================================================================
# ENVIRONMENT-SPECIFIC CONFIGURATIONS
# =============================================================================
environment = os.getenv('ENVIRONMENT', 'development')

if environment == 'production':
    # Production optimizations
    workers = max(workers, 4)  # Minimum 4 workers in production
    worker_connections = 1000
    max_requests = 1000
    max_requests_jitter = 50
    timeout = 30
    
elif environment == 'development':
    # Development settings
    workers = 1
    reload = True
    timeout = 0  # Disable timeout in development
    
elif environment == 'testing':
    # Testing settings
    workers = 1
    timeout = 10

# =============================================================================
# SECURITY SETTINGS
# =============================================================================
# Limit request line size
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# =============================================================================
# PERFORMANCE TUNING
# =============================================================================
# Enable sendfile for static files (if serving static files directly)
sendfile = True

# =============================================================================
# MONITORING AND HEALTH CHECKS
# =============================================================================
def child_exit(server, worker):
    """Called just after a worker has been reaped."""
    server.log.info(f"Worker {worker.pid} exited with code {worker.exitcode}")

# =============================================================================
# HEALTH CHECK ENDPOINT
# =============================================================================
def health_check():
    """Simple health check for load balancers"""
    try:
        # Basic health check - can be extended to check database connectivity
        return True
    except Exception:
        return False

# =============================================================================
# GRACEFUL SHUTDOWN HANDLING
# =============================================================================
def worker_exit(server, worker):
    """Called when a worker is exiting"""
    server.log.info(f"Worker {worker.pid} is shutting down gracefully")

def on_exit(server):
    """Called just before the master process exits"""
    server.log.info("Organigramma Web App is shutting down")

# =============================================================================
# CONFIGURATION VALIDATION
# =============================================================================
def validate_config():
    """Validate Gunicorn configuration"""
    if workers < 1:
        raise ValueError("Workers must be at least 1")
    
    if timeout < 0 and environment != 'development':
        raise ValueError("Timeout must be positive in non-development environments")
    
    # Validate log directory exists
    if errorlog and not Path(errorlog).parent.exists():
        Path(errorlog).parent.mkdir(parents=True, exist_ok=True)
    
    if accesslog and not Path(accesslog).parent.exists():
        Path(accesslog).parent.mkdir(parents=True, exist_ok=True)
    
    # Validate worker count for production
    if environment == 'production' and workers < 2:
        print("WARNING: Running with less than 2 workers in production is not recommended")
    
    # Check if running as root (security warning)
    if os.getuid() == 0:
        print("WARNING: Running as root user is not recommended for security")

# Run validation
validate_config()