"""
Person model
"""

from dataclasses import dataclass, field
from typing import Optional, List
from app.models.base import BaseModel, ValidationError
import re


@dataclass
class Person(BaseModel):
    """Person model with email validation and contact details"""
    id: Optional[int] = None
    name: str = ""
    short_name: Optional[str] = None
    email: Optional[str] = None
    
    # Computed fields (not stored in DB)
    current_assignments_count: int = field(default=0, init=False)
    total_assignments_count: int = field(default=0, init=False)
    
    @property
    def full_name(self) -> str:
        """Get full name"""
        return self.name.strip() if self.name else ""
    
    @property
    def display_name(self) -> str:
        """Get display name (short_name if available, otherwise name)"""
        return self.short_name if self.short_name else self.name
    
    @property
    def initials(self) -> str:
        """Get person initials from name"""
        if not self.name:
            return ""
        parts = self.name.split()
        return "".join(part[0].upper() for part in parts if part)
    
    @property
    def last_name_first(self) -> str:
        """Get name in display format"""
        return self.display_name
    
    def validate(self) -> List[ValidationError]:
        """Validate person data"""
        errors = []
        
        if not self.name or not self.name.strip():
            errors.append(ValidationError("name", "Name is required"))
        
        if self.email and not self._is_valid_email(self.email):
            errors.append(ValidationError("email", "Invalid email format"))
        
        return errors
    
    def _is_valid_email(self, email: str) -> bool:
        """Email validation with comprehensive regex pattern"""
        if not email or not email.strip():
            return False
        
        # RFC 5322 compliant email regex pattern
        ##pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        ##return bool(re.match(pattern, email.strip()))
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email.strip())) if email else False
    
    def _is_valid_phone(self, phone: str) -> bool:
        """Basic phone validation - allows various international formats"""
        if not phone or not phone.strip():
            return False
        
        # Remove common separators and spaces
        cleaned_phone = re.sub(r'[\s\-\(\)\+\.]', '', phone)
        
        # Check if it contains only digits and is reasonable length
        if not cleaned_phone.isdigit():
            return False
        
        # Phone should be between 7 and 15 digits (international standard)
        return 7 <= len(cleaned_phone) <= 15
    
    @classmethod
    def from_sqlite_row(cls, row):
        """Create Person instance from SQLite row"""
        if row is None:
            return None
        
        data = dict(row)
        
        # Extract computed fields (init=False fields)
        computed_fields = {
            'current_assignments_count': data.pop('current_assignments_count', 0),
            'total_assignments_count': data.pop('total_assignments_count', 0)
        }
        
        # Create instance with regular fields
        instance = cls.from_dict(data)
        
        # Set computed fields
        for field_name, value in computed_fields.items():
            if hasattr(instance, field_name):
                setattr(instance, field_name, int(value) if value is not None else 0)
        
        return instance