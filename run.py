#!/usr/bin/env python3
"""
Application runner script
Organigramma Web App - Enhanced with environment-based configuration
"""

import uvicorn
import sys
import os
import subprocess
import logging
from pathlib import Path
from datetime import datetime

# Add app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

def perform_startup_backup(settings):
    """Perform database backup on startup if enabled"""
    if not settings.database.backup_enabled:
        return
    
    print("🔄 Performing startup database backup...")
    
    try:
        # Determine backup type based on configuration
        backup_commands = []
        
        if settings.database.backup_schema:
            schema_cmd = ["python", "scripts/backup_schema.py", "create"]
            if settings.database.backup_data:
                schema_cmd.append("--include-data")
            backup_commands.append(("Schema", schema_cmd))
        
        # Always create a full database backup if backup is enabled
        db_cmd = ["python", "scripts/backup_db.py", "create"]
        backup_commands.append(("Database", db_cmd))
        
        # Execute backup commands
        for backup_type, cmd in backup_commands:
            try:
                print(f"   📋 Creating {backup_type.lower()} backup...")
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                
                if result.returncode == 0:
                    print(f"   ✅ {backup_type} backup completed successfully")
                    # Log any output from the backup script
                    if result.stdout:
                        for line in result.stdout.strip().split('\n'):
                            if line.strip() and not line.startswith('🚀') and not line.startswith('📁'):
                                print(f"      {line}")
                else:
                    print(f"   ⚠️  {backup_type} backup failed (exit code: {result.returncode})")
                    if result.stderr:
                        print(f"      Error: {result.stderr.strip()}")
                        
            except subprocess.TimeoutExpired:
                print(f"   ⚠️  {backup_type} backup timed out after 60 seconds")
            except FileNotFoundError:
                print(f"   ⚠️  {backup_type} backup script not found")
            except Exception as e:
                print(f"   ⚠️  {backup_type} backup error: {e}")
        
        print("✅ Startup backup process completed")
        
    except Exception as e:
        print(f"⚠️  Startup backup failed: {e}")

def main():
    """Main entry point with enhanced configuration support"""
    
    try:
        # Import settings after adding to path
        from app.config import get_settings
        settings = get_settings()
        
        if settings.is_development:
            settings.logging.level = "DEBUG"

        host = settings.server.host
        port = settings.server.port
        must_reload = settings.server.reload
        log_level = settings.logging.level.lower() if settings.logging.level else 'trace'
        access_log = settings.server.access_log
        workers = settings.server.workers if not settings.server.reload else 1

        # Use new configuration system
        config = {
            "app": "app.main:app",
            "host": host,
            "port": port,
            "reload": must_reload,
            "log_level": log_level,
            "access_log": access_log,
            "workers": workers,
            "reload_dirs": ['/app']
        }
        
        print("=" * 60)
        print("🏢 ORGANIGRAMMA WEB APP")
        print("=" * 60)
        print(f"📋 Application: {settings.application.title} v{settings.application.version}")
        print(f"🌍 Environment: {settings.application.environment.upper()}")
        print(f"🚀 Server: http://{config['host']}:{config['port']}")
        print(f"📊 Debug mode: {'ON' if config['reload'] else 'OFF'}")
        print(f"📝 Log level: {config['log_level'].upper()}")
        print(f"👥 Workers: {config['workers']}")
        print(f"🔒 Security: {'HTTPS' if settings.security.https_only else 'HTTP'}")
        print(f"🔒 CSRF: {'ON' if settings.security.csrf_protection else 'OFF'}")
        print("=" * 60)
        
        # Perform startup backup if enabled
        if settings.database.backup_enabled:
            perform_startup_backup(settings)
        
        # Production warnings
        if settings.is_production:
            if settings.server.debug:
                print("⚠️  WARNING: Debug mode is enabled in production!")
            if len(settings.security.secret_key) < 32:
                print("⚠️  WARNING: Secret key is too short for production!")
            if not settings.security.https_only:
                print("⚠️  WARNING: HTTPS is not enforced in production!")
        
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return 1
    
    try:
        # Start server
        uvicorn.run(**config)
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    main()