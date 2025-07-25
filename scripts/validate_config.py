#!/usr/bin/env python3
"""
Configuration validation script for Organigramma Web App
This script validates the application configuration and provides recommendations.
"""

import sys
from pathlib import Path

# Add app directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

def validate_configuration():
    """Validate application configuration"""
    try:
        from app.config import get_settings
        settings = get_settings()
        
        print("🔍 Configuration Validation Report")
        print("=" * 50)
        
        # Basic info
        print(f"📋 Application: {settings.application.title} v{settings.application.version}")
        print(f"🌍 Environment: {settings.application.environment}")
        print(f"🚀 Server: {settings.server.host}:{settings.server.port}")
        print()
        
        # Validation results
        issues = []
        warnings = []
        
        # Environment-specific validations
        if settings.is_production:
            print("🏭 Production Environment Checks:")
            
            if settings.server.debug:
                issues.append("Debug mode is enabled in production")
            else:
                print("✅ Debug mode is disabled")
            
            if len(settings.security.secret_key) < 32:
                issues.append("Secret key is too short for production (minimum 32 characters)")
            else:
                print("✅ Secret key length is adequate")
            
            if not settings.security.https_only:
                warnings.append("HTTPS is not enforced in production")
            else:
                print("✅ HTTPS enforcement is enabled")
            
            if not settings.security.secure_cookies:
                warnings.append("Secure cookies are not enabled")
            else:
                print("✅ Secure cookies are enabled")
            
            if settings.logging.level == "DEBUG":
                warnings.append("Debug logging is enabled in production")
            else:
                print("✅ Appropriate log level for production")
                
        elif settings.is_development:
            print("🛠️  Development Environment Checks:")
            print("✅ Development environment detected")
            
        # Database checks
        print("\n💾 Database Configuration:")
        db_path = Path(settings.database.url.replace("sqlite:///", ""))
        if db_path.parent.exists():
            print("✅ Database directory exists")
        else:
            warnings.append(f"Database directory does not exist: {db_path.parent}")
        
        if settings.database.enable_foreign_keys:
            print("✅ Foreign key constraints are enabled")
        else:
            warnings.append("Foreign key constraints are disabled")
        
        # Logging checks
        print("\n📝 Logging Configuration:")
        if settings.logging.to_file:
            log_path = Path(settings.logging.file_path)
            if log_path.parent.exists():
                print("✅ Log directory exists")
            else:
                warnings.append(f"Log directory does not exist: {log_path.parent}")
        
        if settings.logging.to_console or settings.logging.to_file:
            print("✅ Logging is properly configured")
        else:
            issues.append("No logging output configured")
        
        # Security checks
        print("\n🔒 Security Configuration:")
        if settings.security.secret_key == "your-secret-key-here-change-in-production":
            issues.append("Default secret key is being used - change immediately!")
        else:
            print("✅ Custom secret key is configured")
        
        if settings.security.csrf_protection:
            print("✅ CSRF protection is enabled")
        else:
            warnings.append("CSRF protection is disabled")
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 Validation Summary:")
        
        if not issues and not warnings:
            print("✅ Configuration is valid with no issues!")
        else:
            if issues:
                print(f"❌ {len(issues)} critical issue(s) found:")
                for issue in issues:
                    print(f"   • {issue}")
            
            if warnings:
                print(f"⚠️  {len(warnings)} warning(s) found:")
                for warning in warnings:
                    print(f"   • {warning}")
        
        print("\n💡 Recommendations:")
        if settings.is_production:
            print("• Regularly rotate secret keys")
            print("• Monitor log files for security events")
            print("• Use HTTPS in production")
            print("• Enable all security features")
        else:
            print("• Test configuration in staging before production")
            print("• Use different secret keys for each environment")
        
        return len(issues) == 0
        
    except Exception as e:
        print(f"❌ Configuration validation failed: {e}")
        return False

def main():
    """Main function"""
    success = validate_configuration()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()