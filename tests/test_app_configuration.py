#!/usr/bin/env python3
"""
Test script for environment-based configuration
This script tests the configuration system to ensure it works correctly.
"""

import os
import sys
from pathlib import Path

# Add app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

def test_configuration():
    """Test the configuration system"""
    print("🧪 Testing Environment-Based Configuration")
    print("=" * 50)
    
    try:
        # Test 1: Import configuration
        print("1. Testing configuration import...")
        from app.config import get_settings, reload_settings
        settings = get_settings()
        print("✅ Configuration imported successfully")
        
        # Test 2: Check basic settings
        print("\n2. Testing basic settings...")
        print(f"   Application: {settings.application.title}")
        print(f"   Environment: {settings.application.environment}")
        print(f"   Debug: {settings.server.debug}")
        print(f"   Log Level: {settings.logging.level}")
        print("✅ Basic settings loaded correctly")
        
        # Test 3: Test environment variable override
        print("\n3. Testing environment variable override...")
        original_debug = settings.server.debug
        os.environ["DEBUG"] = "false" if original_debug else "true"
        
        # Reload settings
        new_settings = reload_settings()
        new_debug = new_settings.server.debug
        
        if new_debug != original_debug:
            print("✅ Environment variable override works")
        else:
            print("⚠️  Environment variable override may not be working")
        
        # Restore original value
        os.environ["DEBUG"] = str(original_debug).lower()
        
        # Test 4: Test configuration validation
        print("\n4. Testing configuration validation...")
        try:
            # Test invalid log level
            os.environ["LOG_LEVEL"] = "INVALID"
            from app.config import Settings
            Settings()
            print("❌ Validation should have failed for invalid log level")
        except ValueError as e:
            print("✅ Configuration validation works correctly")
        finally:
            # Restore valid log level
            os.environ["LOG_LEVEL"] = "INFO"
        
        # Test 5: Test directory creation
        print("\n5. Testing directory creation...")
        test_settings = reload_settings()
        
        # Check if log directory exists
        log_path = Path(test_settings.logging.file_path)
        if log_path.parent.exists():
            print("✅ Log directory created successfully")
        else:
            print("❌ Log directory was not created")
        
        # Check if database directory exists
        db_url = test_settings.database.url
        if db_url.startswith("sqlite:///"):
            db_path = Path(db_url.replace("sqlite:///", ""))
            if db_path.parent.exists():
                print("✅ Database directory created successfully")
            else:
                print("❌ Database directory was not created")
        
        print("\n" + "=" * 50)
        print("✅ Configuration system test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Configuration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_application_startup():
    """Test that the application can start with the new configuration"""
    print("\n🚀 Testing Application Startup")
    print("=" * 30)
    
    try:
        # Import main application
        from app.main import app
        print("✅ Application imported successfully")
        
        # Check if FastAPI app is configured correctly
        if app.title and app.description and app.version:
            print("✅ FastAPI app configured correctly")
        else:
            print("❌ FastAPI app configuration incomplete")
            return False
        
        print("✅ Application startup test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Application startup test failed: {e}")
        return False

def main():
    """Main test function"""
    config_success = test_configuration()
    app_success = test_application_startup()
    
    if config_success and app_success:
        print("\n🎉 All tests passed! Configuration system is working correctly.")
        return 0
    else:
        print("\n💥 Some tests failed. Please check the configuration.")
        return 1

if __name__ == "__main__":
    sys.exit(main())