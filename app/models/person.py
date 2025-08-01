"""
Person model
"""

from dataclasses import dataclass, field
from typing import Optional, List
from app.models.base import BaseModel, ValidationError
import re


@dataclass
class Person(BaseModel):
    """Person model with enhanced fields and validation"""
    id: Optional[int] = None
    name: str = ""
    short_name: Optional[str] = None
    email: Optional[str] = None
    
    # Enhanced fields (Requirements 1.3, 1.4, 1.5, 6.1, 6.2)
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    registration_no: Optional[str] = None
    profile_image: Optional[str] = None
    
    # Computed fields (not stored in DB)
    current_assignments_count: int = field(default=0, init=False)
    total_assignments_count: int = field(default=0, init=False)
    
    @property
    def full_name(self) -> str:
        """Get full name - prioritizes first_name/last_name if available, falls back to name"""
        if self.first_name or self.last_name:
            parts = []
            if self.first_name:
                parts.append(self.first_name.strip())
            if self.last_name:
                parts.append(self.last_name.strip())
            return " ".join(parts)
        return self.name.strip() if self.name else ""
    
    @property
    def display_name(self) -> str:
        """Get display name (short_name if available, otherwise full_name)"""
        return self.short_name if self.short_name else self.full_name
    
    @property
    def suggested_name_format(self) -> str:
        """Get suggested name format as '{lastName}, {firstName}' (Requirement 2.1)"""
        if self.last_name and self.first_name:
            return f"{self.last_name.strip()}, {self.first_name.strip()}"
        elif self.last_name:
            return self.last_name.strip()
        elif self.first_name:
            return self.first_name.strip()
        else:
            return self.name.strip() if self.name else ""
    
    @property
    def initials(self) -> str:
        """Get person initials - prioritizes first_name/last_name if available"""
        if self.first_name or self.last_name:
            initials = ""
            if self.first_name:
                initials += self.first_name.strip()[0].upper()
            if self.last_name:
                initials += self.last_name.strip()[0].upper()
            return initials
        elif self.name:
            parts = self.name.split()
            return "".join(part[0].upper() for part in parts if part)
        return ""
    
    @property
    def last_name_first(self) -> str:
        """Get name in last name first format"""
        return self.suggested_name_format
    
    @property
    def has_profile_image(self) -> bool:
        """Check if person has a profile image"""
        return bool(self.profile_image and self.profile_image.strip())
    
    @property
    def profile_image_url(self) -> str:
        """Get profile image URL for display"""
        if self.has_profile_image:
            # Ensure the path starts with /static/ for web access
            if self.profile_image.startswith('/static/'):
                return self.profile_image
            elif self.profile_image.startswith('static/'):
                return f"/{self.profile_image}"
            else:
                return f"/static/profiles/{self.profile_image}"
        return ""
    
    def validate(self) -> List[ValidationError]:
        """Validate person data with enhanced field validation (Requirements 2.2, 2.3, 2.4)"""
        errors = []
        
        # Name validation - require either name OR (first_name/last_name)
        has_name = bool(self.name and self.name.strip())
        has_first_or_last = bool((self.first_name and self.first_name.strip()) or 
                                (self.last_name and self.last_name.strip()))
        
        if not has_name and not has_first_or_last:
            errors.append(ValidationError("name", "Either name or first_name/last_name is required"))
        
        # First name validation
        if self.first_name is not None and len(self.first_name.strip()) == 0:
            errors.append(ValidationError("first_name", "First name cannot be empty if provided"))
        
        # Last name validation  
        if self.last_name is not None and len(self.last_name.strip()) == 0:
            errors.append(ValidationError("last_name", "Last name cannot be empty if provided"))
        
        # Registration number validation (Requirement 2.3)
        if self.registration_no is not None:
            if len(self.registration_no.strip()) == 0:
                errors.append(ValidationError("registration_no", "Registration number cannot be empty if provided"))
            elif len(self.registration_no) > 25:
                errors.append(ValidationError("registration_no", "Registration number cannot exceed 25 characters"))
        
        # Profile image validation (Requirement 6.2)
        if self.profile_image is not None:
            if len(self.profile_image.strip()) == 0:
                errors.append(ValidationError("profile_image", "Profile image path cannot be empty if provided"))
            elif len(self.profile_image) > 1024:
                errors.append(ValidationError("profile_image", "Profile image path cannot exceed 1024 characters"))
            elif not self._is_valid_image_path(self.profile_image):
                errors.append(ValidationError("profile_image", "Profile image must be a valid image file path"))
        
        # Email validation
        if self.email and not self._is_valid_email(self.email):
            errors.append(ValidationError("email", "Invalid email format"))
        
        return errors
    
    def _is_valid_email(self, email: str) -> bool:
        """Email validation with comprehensive regex pattern"""
        if not email or not email.strip():
            return False
        
        # RFC 5322 compliant email regex pattern
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email.strip()))
    
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
    
    def _is_valid_image_path(self, image_path: str) -> bool:
        """Validate profile image path (Requirement 6.2)"""
        if not image_path or not image_path.strip():
            return False
        
        # Check for valid image file extensions
        valid_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg'}
        path_lower = image_path.lower()
        
        # Check if path has a valid image extension
        has_valid_extension = any(path_lower.endswith(ext) for ext in valid_extensions)
        
        # Check for basic path safety (no directory traversal)
        has_unsafe_chars = any(unsafe in image_path for unsafe in ['..', '//', '\\\\'])
        
        return has_valid_extension and not has_unsafe_chars
    
    @classmethod
    def from_sqlite_row(cls, row):
        """Create Person instance from SQLite row with enhanced field support"""
        if row is None:
            return None
        
        data = dict(row)
        
        # Extract computed fields (init=False fields)
        computed_fields = {
            'current_assignments_count': data.pop('current_assignments_count', 0),
            'total_assignments_count': data.pop('total_assignments_count', 0)
        }
        
        # Handle new fields with proper None handling
        enhanced_fields = ['first_name', 'last_name', 'registration_no', 'profile_image']
        for field in enhanced_fields:
            if field in data and data[field] is not None:
                # Convert empty strings to None for consistency
                data[field] = data[field].strip() if data[field].strip() else None
        
        # Create instance with regular fields
        instance = cls.from_dict(data)
        
        # Set computed fields
        for field_name, value in computed_fields.items():
            if hasattr(instance, field_name):
                setattr(instance, field_name, int(value) if value is not None else 0)
        
        return instance
    
    def suggest_name_from_parts(self) -> str:
        """Suggest a name field value from first_name and last_name (Requirement 2.1)"""
        if self.first_name and self.last_name:
            return f"{self.first_name.strip()} {self.last_name.strip()}"
        elif self.first_name:
            return self.first_name.strip()
        elif self.last_name:
            return self.last_name.strip()
        return ""
    
    def populate_name_parts_from_name(self) -> None:
        """Populate first_name and last_name from name field if they are empty"""
        if self.name and not (self.first_name or self.last_name):
            parts = self.name.strip().split()
            if len(parts) >= 2:
                self.first_name = parts[0]
                self.last_name = " ".join(parts[1:])
            elif len(parts) == 1:
                self.first_name = parts[0]
                self.last_name = None
    
    def ensure_name_consistency(self) -> None:
        """Ensure consistency between name and first_name/last_name fields"""
        # If we have first_name/last_name but no name, populate name
        if (self.first_name or self.last_name) and not self.name:
            self.name = self.suggest_name_from_parts()
        
        # If we have name but no first_name/last_name, populate them
        elif self.name and not (self.first_name or self.last_name):
            self.populate_name_parts_from_name()