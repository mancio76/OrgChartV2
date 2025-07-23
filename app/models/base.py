"""
Base model classes and utilities
"""

from dataclasses import dataclass, field, fields
from datetime import datetime
from typing import Optional, Dict, Any, List
import json


@dataclass
class ValidationError:
    """Validation error model"""
    field: str
    message: str
    value: Any = None


class ModelValidationException(Exception):
    """Exception raised when model validation fails"""
    
    def __init__(self, errors: List[ValidationError]):
        self.errors = errors
        messages = [f"{error.field}: {error.message}" for error in errors]
        super().__init__("Validation failed: " + "; ".join(messages))


@dataclass
class BaseModel:
    """Base model with common audit fields and validation framework"""
    
    datetime_created: Optional[datetime] = field(default=None)
    datetime_updated: Optional[datetime] = field(default=None)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, datetime):
                result[key] = value.isoformat() if value else None
            elif isinstance(value, list):
                result[key] = [item.to_dict() if hasattr(item, 'to_dict') else item for item in value]
            else:
                result[key] = value
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Create model instance from dictionary"""
        # Convert datetime strings back to datetime objects
        converted_data = {}
        for key, value in data.items():
            if key.startswith('datetime_') and isinstance(value, str):
                try:
                    converted_data[key] = datetime.fromisoformat(value)
                except (ValueError, TypeError):
                    converted_data[key] = None
            else:
                converted_data[key] = value
        
        return cls(**converted_data)
    
    @classmethod
    def from_sqlite_row(cls, row):
        """Create model instance from SQLite row"""
        if row is None:
            return None
        
        data = dict(row)
        return cls.from_dict(data)
    
    def validate(self) -> List[ValidationError]:
        """
        Validate the model instance and return list of validation errors.
        Override this method in subclasses to add specific validation rules.
        """
        errors = []
        
        # Base validation can be extended by subclasses
        # For now, just return empty list as base implementation
        return errors
    
    def is_valid(self) -> bool:
        """Check if the model instance is valid"""
        return len(self.validate()) == 0
    
    def validate_and_raise(self) -> None:
        """Validate the model and raise ModelValidationException if invalid"""
        errors = self.validate()
        if errors:
            raise ModelValidationException(errors)
    
    def set_audit_fields(self, is_update: bool = False) -> None:
        """Set audit fields for create/update operations"""
        now = datetime.now()
        if not is_update and self.datetime_created is None:
            self.datetime_created = now
        if is_update or self.datetime_updated is None:
            self.datetime_updated = now


@dataclass
class Alias:
    """Alias model for multilingual support"""
    value: str
    lang: str = "it-IT"
    
    def to_dict(self) -> Dict[str, str]:
        return {"value": self.value, "lang": self.lang}
    
    @classmethod
    def from_dict(cls, data: Dict[str, str]):
        return cls(value=data["value"], lang=data.get("lang", "it-IT"))


def parse_aliases(aliases_json: Optional[str]) -> List[Alias]:
    """Parse JSON aliases string to list of Alias objects"""
    if not aliases_json:
        return []
    
    try:
        aliases_data = json.loads(aliases_json)
        if isinstance(aliases_data, str):
            # Handle case where it's a simple string
            return [Alias(value=aliases_data)]
        elif isinstance(aliases_data, list):
            return [Alias.from_dict(alias) if isinstance(alias, dict) else Alias(value=str(alias)) 
                   for alias in aliases_data]
        else:
            return []
    except (json.JSONDecodeError, TypeError):
        return []


def serialize_aliases(aliases: List[Alias]) -> str:
    """Serialize list of Alias objects to JSON string"""
    if not aliases:
        return "[]"
    
    return json.dumps([alias.to_dict() for alias in aliases], ensure_ascii=False)