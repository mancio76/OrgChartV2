"""
Configuration management for Organigramma Web App
Environment-based configuration with security-by-design principles
"""

import os
import secrets
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

@dataclass
class DatabaseConfig:
    """Database configuration settings"""
    url: str = field(default_factory=lambda: os.getenv("DATABASE_URL", "sqlite:///database/orgchart.db"))
    enable_foreign_keys: bool = field(default_factory=lambda: os.getenv("DATABASE_ENABLE_FOREIGN_KEYS", "true").lower() == "true")
    backup_enabled: bool = field(default_factory=lambda: os.getenv("DATABASE_BACKUP_ENABLED", "true").lower() == "true")
    backup_schedule: str = field(default_factory=lambda: os.getenv("DATABASE_BACKUP_SCHEDULE", "daily"))
    backup_directory: str = field(default_factory=lambda: os.getenv("DATABASE_BACKUP_DIRECTORY", "backups"))
    backup_schema: bool = field(default_factory=lambda: os.getenv("DATABASE_BACKUP_SCHEMA", "true").lower() == "true")
    backup_data: bool = field(default_factory=lambda: os.getenv("DATABASE_BACKUP_DATA", "false").lower() == "true")

@dataclass
class LoggingConfig:
    """Logging configuration settings"""
    level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO").upper())
    to_console: bool = field(default_factory=lambda: os.getenv("LOG_TO_CONSOLE", "true").lower() == "true")
    to_file: bool = field(default_factory=lambda: os.getenv("LOG_TO_FILE", "true").lower() == "true")
    file_path: str = field(default_factory=lambda: os.getenv("LOG_FILE_PATH", "app.log"))
    max_file_size: int = field(default_factory=lambda: int(os.getenv("LOG_MAX_FILE_SIZE", "10485760")))  # 10MB
    backup_count: int = field(default_factory=lambda: int(os.getenv("LOG_BACKUP_COUNT", "5")))
    format: str = field(default_factory=lambda: os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"))

@dataclass
class SecurityConfig:
    """Security configuration settings"""
    secret_key: str = field(default_factory=lambda: os.getenv("SECRET_KEY", secrets.token_urlsafe(32)))
    allowed_hosts: List[str] = field(default_factory=lambda: os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(","))
    cors_origins: List[str] = field(default_factory=lambda: os.getenv("CORS_ORIGINS", "").split(",") if os.getenv("CORS_ORIGINS") else [])
    csrf_protection: bool = field(default_factory=lambda: os.getenv("CSRF_PROTECTION", "true").lower() == "true")
    secure_cookies: bool = field(default_factory=lambda: os.getenv("SECURE_COOKIES", "false").lower() == "true")
    https_only: bool = field(default_factory=lambda: os.getenv("HTTPS_ONLY", "false").lower() == "true")

@dataclass
class ServerConfig:
    """Server configuration settings"""
    host: str = field(default_factory=lambda: os.getenv("SERVER_HOST", "127.0.0.1"))
    port: int = field(default_factory=lambda: int(os.getenv("SERVER_PORT", "8000")))
    debug: bool = field(default_factory=lambda: os.getenv("DEBUG", "false").lower() == "true")
    reload: bool = field(default_factory=lambda: os.getenv("RELOAD", "false").lower() == "true")
    workers: int = field(default_factory=lambda: int(os.getenv("WORKERS", "1")))
    access_log: bool = field(default_factory=lambda: os.getenv("ACCESS_LOG", "true").lower() == "true")

@dataclass
class ApplicationConfig:
    """Application-specific configuration settings"""
    title: str = field(default_factory=lambda: os.getenv("APP_TITLE", "Organigramma Web App"))
    description: str = field(default_factory=lambda: os.getenv("APP_DESCRIPTION", "Sistema di gestione organigramma aziendale con storicizzazione"))
    version: str = field(default_factory=lambda: os.getenv("APP_VERSION", "1.0.0"))
    environment: str = field(default_factory=lambda: os.getenv("ENVIRONMENT", "development"))
    timezone: str = field(default_factory=lambda: os.getenv("TIMEZONE", "Europe/Rome"))

@dataclass
class Settings:
    """Main configuration class combining all settings"""
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    server: ServerConfig = field(default_factory=ServerConfig)
    application: ApplicationConfig = field(default_factory=ApplicationConfig)
    
    def __post_init__(self):
        """Post-initialization validation and setup"""
        self._validate_configuration()
        self._ensure_directories()
    
    def _validate_configuration(self):
        """Validate configuration settings"""
        # Validate log level
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.logging.level not in valid_log_levels:
            raise ValueError(f"Invalid log level: {self.logging.level}. Must be one of {valid_log_levels}")
        
        # Validate port range
        if not (1 <= self.server.port <= 65535):
            raise ValueError(f"Invalid port: {self.server.port}. Must be between 1 and 65535")
        
        # Validate environment
        valid_environments = ["development", "testing", "staging", "production"]
        if self.application.environment not in valid_environments:
            raise ValueError(f"Invalid environment: {self.application.environment}. Must be one of {valid_environments}")
        
        # Security validation for production
        if self.application.environment == "production":
            if self.server.debug:
                raise ValueError("Debug mode must be disabled in production")
            if len(self.security.secret_key) < 32:
                raise ValueError("Secret key must be at least 32 characters in production")
            if not self.security.https_only:
                print("WARNING: HTTPS is not enforced in production environment")
    
    def _ensure_directories(self):
        """Ensure required directories exist"""
        # Create log directory if logging to file
        if self.logging.to_file:
            log_dir = Path(self.logging.file_path).parent
            log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create backup directory if backups are enabled
        if self.database.backup_enabled:
            backup_dir = Path(self.database.backup_directory)
            backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Create database directory
        db_path = Path(self.database.url.replace("sqlite:///", ""))
        db_dir = db_path.parent
        db_dir.mkdir(parents=True, exist_ok=True)
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.application.environment == "development"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.application.environment == "production"
    
    @property
    def is_testing(self) -> bool:
        """Check if running in testing environment"""
        return self.application.environment == "testing"

# Global settings instance
settings = Settings()

def get_settings() -> Settings:
    """Get the global settings instance"""
    return settings

def reload_settings():
    """Reload settings from environment variables"""
    global settings
    load_dotenv(override=True)
    settings = Settings()
    return settings