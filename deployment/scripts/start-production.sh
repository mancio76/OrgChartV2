#!/bin/bash
# Production startup script for Organigramma Web App
# Handles database initialization, migrations, and server startup

set -e

# Configuration
APP_DIR="/app"
VENV_DIR="/opt/venv"
LOG_DIR="/var/log/orgchart"
DATA_DIR="/app/data"
BACKUP_DIR="/var/backups/orgchart"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $(date '+%Y-%m-%d %H:%M:%S') $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') $1"
}

# Ensure directories exist
ensure_directories() {
    log_info "Ensuring required directories exist..."
    
    mkdir -p "$LOG_DIR" "$DATA_DIR" "$BACKUP_DIR"
    
    # Set proper permissions
    if [[ $(id -u) == 0 ]]; then
        chown -R appuser:appuser "$LOG_DIR" "$DATA_DIR" "$BACKUP_DIR" 2>/dev/null || true
    fi
}

# Activate virtual environment if it exists
activate_venv() {
    if [[ -d "$VENV_DIR" ]]; then
        log_info "Activating virtual environment..."
        source "$VENV_DIR/bin/activate"
    fi
}

# Wait for dependencies (if any)
wait_for_dependencies() {
    log_info "Checking dependencies..."
    
    # Add any dependency checks here (e.g., external databases, services)
    # For SQLite, we just need to ensure the directory exists
    if [[ ! -d "$(dirname "${DATABASE_URL#sqlite:///}")" ]]; then
        mkdir -p "$(dirname "${DATABASE_URL#sqlite:///}")"
    fi
}

# Initialize database
initialize_database() {
    log_info "Initializing database..."
    
    if python scripts/init_db.py; then
        log_info "Database initialized successfully"
    else
        log_error "Database initialization failed"
        exit 1
    fi
}

# Run database migrations
run_migrations() {
    log_info "Running database migrations..."
    
    if python scripts/migrate_db.py apply-all; then
        log_info "Database migrations completed successfully"
    else
        log_error "Database migrations failed"
        exit 1
    fi
}

# Validate configuration
validate_configuration() {
    log_info "Validating configuration..."
    
    if python scripts/validate_config.py; then
        log_info "Configuration validation passed"
    else
        log_error "Configuration validation failed"
        exit 1
    fi
}

# Create initial backup
create_initial_backup() {
    if [[ "${DATABASE_BACKUP_ENABLED:-true}" == "true" ]]; then
        log_info "Creating initial database backup..."
        
        if python scripts/backup_db.py create --compress; then
            log_info "Initial backup created successfully"
        else
            log_warn "Initial backup creation failed (non-critical)"
        fi
    fi
}

# Start the application server
start_server() {
    log_info "Starting Organigramma Web App server..."
    
    # Determine server type based on environment
    case "${ENVIRONMENT:-production}" in
        "development")
            log_info "Starting in development mode with hot reload..."
            exec python run.py
            ;;
        "testing")
            log_info "Starting in testing mode..."
            exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1
            ;;
        "production"|*)
            log_info "Starting in production mode with Gunicorn..."
            exec gunicorn --config gunicorn.conf.py app.main:app
            ;;
    esac
}

# Signal handlers for graceful shutdown
cleanup() {
    log_info "Received shutdown signal, cleaning up..."
    
    # Kill any background processes
    jobs -p | xargs -r kill
    
    # Create final backup if enabled
    if [[ "${DATABASE_BACKUP_ENABLED:-true}" == "true" ]]; then
        log_info "Creating shutdown backup..."
        python scripts/backup_db.py create --compress || true
    fi
    
    log_info "Cleanup completed"
    exit 0
}

# Set up signal handlers
trap cleanup SIGTERM SIGINT

# Health check function
health_check() {
    local max_attempts=30
    local attempt=1
    
    log_info "Performing health check..."
    
    while [[ $attempt -le $max_attempts ]]; do
        if curl -f http://localhost:${SERVER_PORT:-8000}/api/health >/dev/null 2>&1; then
            log_info "Health check passed"
            return 0
        fi
        
        log_info "Health check attempt $attempt/$max_attempts failed, retrying in 2 seconds..."
        sleep 2
        ((attempt++))
    done
    
    log_error "Health check failed after $max_attempts attempts"
    return 1
}

# Pre-flight checks
preflight_checks() {
    log_info "Running pre-flight checks..."
    
    # Check Python version
    python_version=$(python --version 2>&1)
    log_info "Python version: $python_version"
    
    # Check required environment variables
    required_vars=("ENVIRONMENT")
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var}" ]]; then
            log_warn "Environment variable $var is not set"
        fi
    done
    
    # Check disk space
    disk_usage=$(df -h . | tail -1 | awk '{print $5}' | sed 's/%//')
    if [[ $disk_usage -gt 90 ]]; then
        log_warn "Disk usage is high: ${disk_usage}%"
    fi
    
    # Check memory
    if command -v free >/dev/null 2>&1; then
        memory_info=$(free -h | grep "Mem:")
        log_info "Memory info: $memory_info"
    fi
}

# Main execution
main() {
    log_info "Starting Organigramma Web App startup sequence..."
    log_info "Environment: ${ENVIRONMENT:-production}"
    log_info "Server host: ${SERVER_HOST:-0.0.0.0}"
    log_info "Server port: ${SERVER_PORT:-8000}"
    log_info "Workers: ${WORKERS:-4}"
    
    # Change to application directory
    cd "$APP_DIR"
    
    # Run startup sequence
    preflight_checks
    ensure_directories
    activate_venv
    wait_for_dependencies
    validate_configuration
    initialize_database
    run_migrations
    create_initial_backup
    
    # Start server in background for health check
    start_server &
    SERVER_PID=$!
    
    # Wait a bit for server to start
    sleep 5
    
    # Perform health check
    if health_check; then
        log_info "Startup completed successfully"
        
        # Wait for server process
        wait $SERVER_PID
    else
        log_error "Startup failed - health check did not pass"
        kill $SERVER_PID 2>/dev/null || true
        exit 1
    fi
}

# Show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help              Show this help message"
    echo "  --skip-migrations       Skip database migrations"
    echo "  --skip-backup           Skip initial backup creation"
    echo "  --health-check-only     Only perform health check and exit"
    echo "  --validate-only         Only validate configuration and exit"
    echo ""
    echo "Environment variables:"
    echo "  ENVIRONMENT             Deployment environment (development/testing/production)"
    echo "  SERVER_HOST             Server bind host (default: 0.0.0.0)"
    echo "  SERVER_PORT             Server port (default: 8000)"
    echo "  WORKERS                 Number of worker processes (default: 4)"
    echo "  DATABASE_BACKUP_ENABLED Enable/disable backups (default: true)"
}

# Parse command line arguments
SKIP_MIGRATIONS=false
SKIP_BACKUP=false
HEALTH_CHECK_ONLY=false
VALIDATE_ONLY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_usage
            exit 0
            ;;
        --skip-migrations)
            SKIP_MIGRATIONS=true
            shift
            ;;
        --skip-backup)
            SKIP_BACKUP=true
            shift
            ;;
        --health-check-only)
            HEALTH_CHECK_ONLY=true
            shift
            ;;
        --validate-only)
            VALIDATE_ONLY=true
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Handle special modes
if [[ "$HEALTH_CHECK_ONLY" == "true" ]]; then
    health_check
    exit $?
fi

if [[ "$VALIDATE_ONLY" == "true" ]]; then
    cd "$APP_DIR"
    activate_venv
    validate_configuration
    exit $?
fi

# Override functions based on flags
if [[ "$SKIP_MIGRATIONS" == "true" ]]; then
    run_migrations() {
        log_info "Skipping database migrations (--skip-migrations)"
    }
fi

if [[ "$SKIP_BACKUP" == "true" ]]; then
    create_initial_backup() {
        log_info "Skipping initial backup (--skip-backup)"
    }
fi

# Run main function
main