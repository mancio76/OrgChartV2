"""
Company model
"""

from dataclasses import dataclass, field
from typing import Optional, List
from datetime import date
from app.models.base import BaseModel, ValidationError
import re


@dataclass
class Company(BaseModel):
    """Company model for managing organizational relationships (Requirements 3.1-3.8)"""
    id: Optional[int] = None
    name: str = ""
    short_name: Optional[str] = None
    registration_no: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    country: str = "Italy"
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    main_contact_id: Optional[int] = None
    financial_contact_id: Optional[int] = None
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None
    notes: Optional[str] = None
    
    # Computed fields for display (not stored in DB)
    main_contact_name: Optional[str] = field(default=None, init=False)
    financial_contact_name: Optional[str] = field(default=None, init=False)
    
    @property
    def display_name(self) -> str:
        """Get display name (short_name if available, otherwise name)"""
        return self.short_name if self.short_name else self.name
    
    @property
    def full_address(self) -> str:
        """Get formatted full address"""
        parts = []
        if self.address:
            parts.append(self.address.strip())
        if self.city:
            parts.append(self.city.strip())
        if self.postal_code:
            parts.append(self.postal_code.strip())
        if self.country and self.country != "Italy":
            parts.append(self.country.strip())
        return ", ".join(parts)
    
    @property
    def is_active(self) -> bool:
        """Check if company is currently active based on valid dates"""
        today = date.today()
        
        # If no dates set, consider active
        if not self.valid_from and not self.valid_to:
            return True
        
        # Check if within valid date range
        if self.valid_from and today < self.valid_from:
            return False
        
        if self.valid_to and today > self.valid_to:
            return False
        
        return True
    
    @property
    def has_contacts(self) -> bool:
        """Check if company has any contact persons assigned"""
        return bool(self.main_contact_id or self.financial_contact_id)
    
    @property
    def contact_display(self) -> str:
        """Get formatted contact display for lists"""
        contacts = []
        if self.main_contact_name:
            contacts.append(f"Main: {self.main_contact_name}")
        if self.financial_contact_name:
            contacts.append(f"Financial: {self.financial_contact_name}")
        return " | ".join(contacts) if contacts else "No contacts"
    
    def validate(self) -> List[ValidationError]:
        """Validate company data (Requirements 3.2, 3.3, 3.4)"""
        errors = []
        
        # Required fields validation (Requirement 3.2)
        if not self.name or not self.name.strip():
            errors.append(ValidationError("name", "Company name is required"))
        
        # Registration number validation
        if self.registration_no is not None:
            if len(self.registration_no.strip()) == 0:
                errors.append(ValidationError("registration_no", "Registration number cannot be empty if provided"))
            elif len(self.registration_no) > 50:
                errors.append(ValidationError("registration_no", "Registration number cannot exceed 50 characters"))
        
        # Email validation
        if self.email and not self._is_valid_email(self.email):
            errors.append(ValidationError("email", "Invalid email format"))
        
        # Website URL validation (Requirement 3.3)
        if self.website and not self._is_valid_url(self.website):
            errors.append(ValidationError("website", "Invalid website URL format"))
        
        # Phone validation
        if self.phone and not self._is_valid_phone(self.phone):
            errors.append(ValidationError("phone", "Invalid phone number format"))
        
        # Date range validation (Requirement 3.4)
        if self.valid_from and self.valid_to and self.valid_from > self.valid_to:
            errors.append(ValidationError("valid_to", "End date must be after start date"))
        
        # Contact validation (Requirements 3.5, 3.6)
        if self.main_contact_id is not None and self.main_contact_id <= 0:
            errors.append(ValidationError("main_contact_id", "Invalid main contact ID"))
        
        if self.financial_contact_id is not None and self.financial_contact_id <= 0:
            errors.append(ValidationError("financial_contact_id", "Invalid financial contact ID"))
        
        # Prevent same person as both contacts
        if (self.main_contact_id and self.financial_contact_id and 
            self.main_contact_id == self.financial_contact_id):
            errors.append(ValidationError("financial_contact_id", "Financial contact cannot be the same as main contact"))
        
        return errors
    
    def _is_valid_email(self, email: str) -> bool:
        """Email validation with comprehensive regex pattern"""
        if not email or not email.strip():
            return False
        
        # RFC 5322 compliant email regex pattern
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email.strip()))
    
    def _is_valid_url(self, url: str) -> bool:
        """Basic URL validation (Requirement 3.3)"""
        if not url or not url.strip():
            return False
        
        # Basic URL pattern - must start with http:// or https://
        pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        return bool(re.match(pattern, url.strip()))
    
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
        """Create Company instance from SQLite row"""
        if row is None:
            return None
        
        data = dict(row)
        
        # Extract computed fields (init=False fields)
        computed_fields = {
            'main_contact_name': data.pop('main_contact_name', None),
            'financial_contact_name': data.pop('financial_contact_name', None)
        }
        
        # Handle date fields
        date_fields = ['valid_from', 'valid_to']
        for field in date_fields:
            if field in data and data[field] is not None:
                if isinstance(data[field], str):
                    try:
                        data[field] = date.fromisoformat(data[field])
                    except (ValueError, TypeError):
                        data[field] = None
        
        # Handle optional string fields with proper None handling
        optional_fields = ['short_name', 'registration_no', 'address', 'city', 
                          'postal_code', 'phone', 'email', 'website', 'notes']
        for field in optional_fields:
            if field in data and data[field] is not None:
                # Convert empty strings to None for consistency
                data[field] = data[field].strip() if data[field].strip() else None
        
        # Create instance with regular fields
        instance = cls.from_dict(data)
        
        # Set computed fields
        for field_name, value in computed_fields.items():
            if hasattr(instance, field_name):
                setattr(instance, field_name, value)
        
        return instance
    
    def to_dict(self) -> dict:
        """Convert company to dictionary with proper date serialization"""
        result = super().to_dict()
        
        # Handle date fields for JSON serialization
        if self.valid_from:
            result['valid_from'] = self.valid_from.isoformat()
        if self.valid_to:
            result['valid_to'] = self.valid_to.isoformat()
        
        return result
    
    def get_status_display(self) -> str:
        """Get human-readable status based on validity dates"""
        if not self.valid_from and not self.valid_to:
            return "Active"
        
        today = date.today()
        
        if self.valid_from and today < self.valid_from:
            return f"Future (starts {self.valid_from})"
        
        if self.valid_to and today > self.valid_to:
            return f"Expired (ended {self.valid_to})"
        
        if self.valid_from and self.valid_to:
            return f"Active ({self.valid_from} to {self.valid_to})"
        elif self.valid_from:
            return f"Active (since {self.valid_from})"
        elif self.valid_to:
            return f"Active (until {self.valid_to})"
        
        return "Active"
    
    def get_contact_summary(self) -> dict:
        """Get summary of contact information"""
        return {
            'has_main_contact': bool(self.main_contact_id),
            'has_financial_contact': bool(self.financial_contact_id),
            'main_contact_name': self.main_contact_name,
            'financial_contact_name': self.financial_contact_name,
            'total_contacts': sum([
                1 if self.main_contact_id else 0,
                1 if self.financial_contact_id else 0
            ])
        }
    
    def is_contact_person(self, person_id: int) -> bool:
        """Check if a person is a contact for this company"""
        return person_id in [self.main_contact_id, self.financial_contact_id]
    
    def get_contact_role(self, person_id: int) -> Optional[str]:
        """Get the contact role for a specific person"""
        if person_id == self.main_contact_id:
            return "main"
        elif person_id == self.financial_contact_id:
            return "financial"
        return None