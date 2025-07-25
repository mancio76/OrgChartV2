#!/usr/bin/env python3
"""
Application runner script
Organigramma Web App - Enhanced with environment-based configuration
"""

import uvicorn
import sys
import os
from pathlib import Path

# Add app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

def main():
    """Main entry point with enhanced configuration support"""
    
    try:
        # Import settings after adding to path
        from app.config import get_settings
        settings = get_settings()
        
        # Use new configuration system
        config = {
            "app": "app.main:app",
            "host": settings.server.host,
            "port": settings.server.port,
            "reload": settings.server.reload,
            "log_level": settings.logging.level.lower(),
            "access_log": settings.server.access_log,
            "workers": settings.server.workers if not settings.server.reload else 1,
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
        print("=" * 60)
        
        # Production warnings
        if settings.is_production:
            if settings.server.debug:
                print("⚠️  WARNING: Debug mode is enabled in production!")
            if len(settings.security.secret_key) < 32:
                print("⚠️  WARNING: Secret key is too short for production!")
            if not settings.security.https_only:
                print("⚠️  WARNING: HTTPS is not enforced in production!")
        
    except ImportError as e:
        print(f"❌ Configuration error: {e}")
        print("📋 Falling back to legacy configuration...")
        
        # Fallback to legacy environment variables
        config = {
            "app": "app.main:app",
            "host": os.getenv("RUN_HOST", "127.0.0.1"),
            "port": int(os.getenv("RUN_PORT", 8000)),
            "reload": os.getenv("RUN_DEBUG", "true").lower() == "true",
            "log_level": os.getenv("RUN_LOG_LEVEL", "info"),
            "access_log": True,
        }
        
        print("=" * 50)
        print("🏢 ORGANIGRAMMA WEB APP (Legacy Mode)")
        print("=" * 50)
        print(f"🚀 Starting server on http://{config['host']}:{config['port']}")
        print(f"📊 Debug mode: {'ON' if config['reload'] else 'OFF'}")
        print(f"📝 Log level: {config['log_level'].upper()}")
        print("=" * 50)
    
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