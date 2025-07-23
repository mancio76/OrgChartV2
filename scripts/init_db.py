#!/usr/bin/env python3
"""
Database initialization script
Organigramma Web App
"""

import sys
import os
from pathlib import Path
import shutil

# Add app directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import init_database, get_db_manager

def create_directories():
    """Create necessary directories"""
    directories = [
        "database",
        "logs",
        "static/css",
        "static/js", 
        "static/images/icons",
        "static/images/logos"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {directory}")

def copy_schema_files():
    """Copy schema files to database directory"""
    # This would copy the schema files we created earlier
    schema_content = """
    -- This is where the actual schema from orgchart_sqlite_schema_v3.sql should go
    -- For now, this is a placeholder
    """
    
    migration_content = """
    -- This is where the actual migration from orgchart_data_migration.sql should go  
    -- For now, this is a placeholder
    """
    
    # Write schema file
    schema_path = Path("database/schema.sql")
    with open(schema_path, 'w', encoding='utf-8') as f:
        f.write(schema_content.strip())
    print(f"✅ Created schema file: {schema_path}")
    
    # Write migration file
    migration_path = Path("database/migration_data.sql")
    with open(migration_path, 'w', encoding='utf-8') as f:
        f.write(migration_content.strip())
    print(f"✅ Created migration file: {migration_path}")

def create_env_file():
    """Create .env file with default settings"""
    env_content = """# Organigramma Web App Configuration
DEBUG=true
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=info

# Database
DATABASE_URL=database/organigramma.db

# Security (change in production)
SECRET_KEY=your-secret-key-here-change-in-production
"""
    
    env_path = Path(".env")
    if not env_path.exists():
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write(env_content.strip())
        print(f"✅ Created environment file: {env_path}")
    else:
        print(f"⚠️  Environment file already exists: {env_path}")

def main():
    """Main initialization function"""
    print("🏢 ORGANIGRAMMA WEB APP - Database Initialization")
    print("=" * 60)
    
    try:
        # Create directories
        print("\n📁 Creating directories...")
        create_directories()
        
        # Create environment file
        print("\n⚙️  Creating configuration files...")
        create_env_file()
        
        # Copy schema files (placeholder for now)
        print("\n📋 Creating database schema files...")
        copy_schema_files()
        
        # Initialize database
        print("\n🗄️  Initializing database...")
        init_database()
        
        # Test database connection
        print("\n🔍 Testing database connection...")
        db_manager = get_db_manager()
        tables = db_manager.fetch_all("SELECT name FROM sqlite_master WHERE type='table'")
        print(f"✅ Database initialized with {len(tables)} tables:")
        for table in tables:
            print(f"   - {table['name']}")
        
        print("\n" + "=" * 60)
        print("🎉 Initialization completed successfully!")
        print("\n📋 Next steps:")
        print("   1. Copy your actual schema to database/schema.sql")
        print("   2. Copy your migration data to database/migration_data.sql") 
        print("   3. Run: python run.py")
        print("   4. Open: http://localhost:8000")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Initialization failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()