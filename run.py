#!/usr/bin/env python3
"""
Application runner script
Organigramma Web App
"""

import uvicorn
import sys
import os
from pathlib import Path

# Add app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

def main():
    """Main entry point"""
    
    # Configuration
    config = {
        "app": "app.main:app",
        "host": os.getenv("RUN_HOST", "127.0.0.1"),
        "port": int(os.getenv("RUN_PORT", 8000)),
        "reload": os.getenv("RUN_DEBUG", "true").lower() == "true",
        "log_level": os.getenv("RUN_LOG_LEVEL", "info"),
        "access_log": True,
    }
    
    print("=" * 50)
    print("🏢 ORGANIGRAMMA WEB APP")
    print("=" * 50)
    print(f"🚀 Starting server on http://{config['host']}:{config['port']}")
    print(f"📊 Debug mode: {'ON' if config['reload'] else 'OFF'}")
    print(f"📝 Log level: {config['log_level'].upper()}")
    print("=" * 50)
    
    # Start server
    uvicorn.run(**config)

if __name__ == "__main__":
    main()