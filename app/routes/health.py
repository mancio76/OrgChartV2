"""
Health check endpoints for Organigramma Web App
Provides basic and detailed health status for monitoring and load balancers
"""

import os
import sys
import time
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.database import DatabaseManager

router = APIRouter(prefix="/api", tags=["health"])

def get_database_manager():
    """Dependency to get database manager"""
    return DatabaseManager()

@router.get("/health")
async def basic_health_check():
    """
    Basic health check endpoint for load balancers and monitoring
    Returns simple OK status with minimal overhead
    """
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}

@router.get("/health/detailed")
async def detailed_health_check(db_manager: DatabaseManager = Depends(get_database_manager)):
    """
    Detailed health check with system information
    Includes database connectivity, disk space, and configuration status
    """
    settings = get_settings()
    health_data = {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.application.version,
        "environment": settings.application.environment,
        "checks": {}
    }
    
    overall_status = "ok"
    
    # Database connectivity check
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.execute("SELECT 1")
            cursor.fetchone()
        
        health_data["checks"]["database"] = {
            "status": "ok",
            "message": "Database connection successful"
        }
    except Exception as e:
        health_data["checks"]["database"] = {
            "status": "error",
            "message": f"Database connection failed: {str(e)}"
        }
        overall_status = "error"
    
    # Database file check
    try:
        db_path = Path(settings.database.url.replace("sqlite:///", ""))
        if db_path.exists():
            db_size = db_path.stat().st_size
            health_data["checks"]["database_file"] = {
                "status": "ok",
                "path": str(db_path),
                "size_bytes": db_size,
                "size_mb": round(db_size / (1024 * 1024), 2)
            }
        else:
            health_data["checks"]["database_file"] = {
                "status": "warning",
                "message": "Database file does not exist"
            }
            if overall_status == "ok":
                overall_status = "warning"
    except Exception as e:
        health_data["checks"]["database_file"] = {
            "status": "error",
            "message": f"Database file check failed: {str(e)}"
        }
        overall_status = "error"
    
    # Disk space check
    try:
        disk_usage = os.statvfs('.')
        total_space = disk_usage.f_frsize * disk_usage.f_blocks
        free_space = disk_usage.f_frsize * disk_usage.f_available
        used_space = total_space - free_space
        usage_percent = (used_space / total_space) * 100
        
        disk_status = "ok"
        if usage_percent > 90:
            disk_status = "error"
            overall_status = "error"
        elif usage_percent > 80:
            disk_status = "warning"
            if overall_status == "ok":
                overall_status = "warning"
        
        health_data["checks"]["disk_space"] = {
            "status": disk_status,
            "total_gb": round(total_space / (1024**3), 2),
            "free_gb": round(free_space / (1024**3), 2),
            "used_gb": round(used_space / (1024**3), 2),
            "usage_percent": round(usage_percent, 2)
        }
    except Exception as e:
        health_data["checks"]["disk_space"] = {
            "status": "error",
            "message": f"Disk space check failed: {str(e)}"
        }
        overall_status = "error"
    
    # Memory check (if available)
    try:
        import psutil
        memory = psutil.virtual_memory()
        
        memory_status = "ok"
        if memory.percent > 90:
            memory_status = "error"
            overall_status = "error"
        elif memory.percent > 80:
            memory_status = "warning"
            if overall_status == "ok":
                overall_status = "warning"
        
        health_data["checks"]["memory"] = {
            "status": memory_status,
            "total_gb": round(memory.total / (1024**3), 2),
            "available_gb": round(memory.available / (1024**3), 2),
            "used_gb": round(memory.used / (1024**3), 2),
            "usage_percent": round(memory.percent, 2)
        }
    except ImportError:
        health_data["checks"]["memory"] = {
            "status": "info",
            "message": "psutil not available for memory monitoring"
        }
    except Exception as e:
        health_data["checks"]["memory"] = {
            "status": "error",
            "message": f"Memory check failed: {str(e)}"
        }
        overall_status = "error"
    
    # Configuration check
    try:
        # Check critical configuration
        config_issues = []
        
        if settings.application.environment == "production":
            if settings.server.debug:
                config_issues.append("Debug mode enabled in production")
            
            if len(settings.security.secret_key) < 32:
                config_issues.append("Secret key too short for production")
            
            if not settings.security.https_only:
                config_issues.append("HTTPS not enforced in production")
        
        if config_issues:
            health_data["checks"]["configuration"] = {
                "status": "warning",
                "issues": config_issues
            }
            if overall_status == "ok":
                overall_status = "warning"
        else:
            health_data["checks"]["configuration"] = {
                "status": "ok",
                "message": "Configuration validation passed"
            }
    except Exception as e:
        health_data["checks"]["configuration"] = {
            "status": "error",
            "message": f"Configuration check failed: {str(e)}"
        }
        overall_status = "error"
    
    # Log directory check
    try:
        if settings.logging.to_file:
            log_path = Path(settings.logging.file_path)
            log_dir = log_path.parent
            
            if log_dir.exists() and log_dir.is_dir():
                # Check if log directory is writable
                test_file = log_dir / ".health_check_test"
                try:
                    test_file.touch()
                    test_file.unlink()
                    
                    health_data["checks"]["logging"] = {
                        "status": "ok",
                        "log_directory": str(log_dir),
                        "writable": True
                    }
                except Exception:
                    health_data["checks"]["logging"] = {
                        "status": "error",
                        "log_directory": str(log_dir),
                        "writable": False,
                        "message": "Log directory not writable"
                    }
                    overall_status = "error"
            else:
                health_data["checks"]["logging"] = {
                    "status": "error",
                    "message": f"Log directory does not exist: {log_dir}"
                }
                overall_status = "error"
        else:
            health_data["checks"]["logging"] = {
                "status": "info",
                "message": "File logging disabled"
            }
    except Exception as e:
        health_data["checks"]["logging"] = {
            "status": "error",
            "message": f"Logging check failed: {str(e)}"
        }
        overall_status = "error"
    
    # Backup directory check (if enabled)
    try:
        if settings.database.backup_enabled:
            backup_dir = Path(settings.database.backup_directory)
            
            if backup_dir.exists() and backup_dir.is_dir():
                # Count backup files
                backup_files = list(backup_dir.glob("orgchart_backup_*"))
                
                health_data["checks"]["backup"] = {
                    "status": "ok",
                    "backup_directory": str(backup_dir),
                    "backup_count": len(backup_files)
                }
            else:
                health_data["checks"]["backup"] = {
                    "status": "warning",
                    "message": f"Backup directory does not exist: {backup_dir}"
                }
                if overall_status == "ok":
                    overall_status = "warning"
        else:
            health_data["checks"]["backup"] = {
                "status": "info",
                "message": "Database backup disabled"
            }
    except Exception as e:
        health_data["checks"]["backup"] = {
            "status": "error",
            "message": f"Backup check failed: {str(e)}"
        }
        overall_status = "error"
    
    # System information
    health_data["system"] = {
        "python_version": sys.version,
        "platform": sys.platform,
        "uptime_seconds": time.time() - getattr(sys, 'start_time', time.time()),
        "process_id": os.getpid()
    }
    
    # Set overall status
    health_data["status"] = overall_status
    
    # Return appropriate HTTP status code
    if overall_status == "error":
        return JSONResponse(
            status_code=503,
            content=health_data
        )
    elif overall_status == "warning":
        return JSONResponse(
            status_code=200,
            content=health_data
        )
    else:
        return health_data

@router.get("/health/database")
async def database_health_check(db_manager: DatabaseManager = Depends(get_database_manager)):
    """
    Database-specific health check
    Tests database connectivity and basic operations
    """
    try:
        start_time = time.time()
        
        with db_manager.get_connection() as conn:
            # Test basic query
            cursor = conn.execute("SELECT 1")
            cursor.fetchone()
            
            # Test table existence
            cursor = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
            """)
            tables = [row[0] for row in cursor.fetchall()]
            
            # Test foreign key constraints
            cursor = conn.execute("PRAGMA foreign_keys")
            foreign_keys_enabled = cursor.fetchone()[0] == 1
        
        response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        return {
            "status": "ok",
            "timestamp": datetime.utcnow().isoformat(),
            "response_time_ms": round(response_time, 2),
            "tables": tables,
            "foreign_keys_enabled": foreign_keys_enabled
        }
    
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "error",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
        )

@router.get("/health/ready")
async def readiness_check(db_manager: DatabaseManager = Depends(get_database_manager)):
    """
    Kubernetes readiness probe endpoint
    Checks if the application is ready to serve traffic
    """
    try:
        # Quick database connectivity check
        with db_manager.get_connection() as conn:
            conn.execute("SELECT 1").fetchone()
        
        return {"status": "ready", "timestamp": datetime.utcnow().isoformat()}
    
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
        )

@router.get("/health/live")
async def liveness_check():
    """
    Kubernetes liveness probe endpoint
    Simple check to verify the application is running
    """
    return {"status": "alive", "timestamp": datetime.utcnow().isoformat()}