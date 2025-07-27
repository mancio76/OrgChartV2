"""
Assignment model - Corrected to match database schema
CORRECTIONS APPLIED:
1. Updated table field names to match person_job_assignments schema
2. Removed version auto-management (now handled by SQL trigger)
3. Fixed datetime field handling (managed by SQL triggers and defaults)
4. Corrected field mappings for SQLite row conversion
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Optional, List
from app.models.base import BaseModel, ValidationError


@dataclass
class Assignment(BaseModel):
    """Person job assignment model - matches person_job_assignments table"""
    id: Optional[int] = None
    person_id: int = 0
    unit_id: int = 0
    job_title_id: int = 0
    version: Optional[int] = None  # Managed by SQL trigger, don't set manually
    percentage: float = 1.0
    is_ad_interim: bool = False
    is_unit_boss: bool = False
    notes: Optional[str] = None
    flags: Optional[str] = None
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None
    is_current: bool = True
    
    # Computed fields from joins (not stored in assignment table)
    person_name: Optional[str] = field(default=None, init=False)
    person_short_name: Optional[str] = field(default=None, init=False)
    unit_name: Optional[str] = field(default=None, init=False)
    unit_short_name: Optional[str] = field(default=None, init=False)
    job_title_name: Optional[str] = field(default=None, init=False)
    job_title_short_name: Optional[str] = field(default=None, init=False)
    
    @property
    def percentage_display(self) -> str:
        """Get percentage as display string"""
        return f"{self.percentage * 100:.0f}%"
    
    @property
    def status(self) -> str:
        """Get assignment status"""
        if self.is_current:
            return "CURRENT"
        elif self.valid_to is not None:
            return "TERMINATED"
        else:
            return "HISTORICAL"
    
    @property
    def status_color(self) -> str:
        """Get CSS class for status color"""
        status_colors = {
            "CURRENT": "success",
            "TERMINATED": "danger", 
            "HISTORICAL": "warning"
        }
        return status_colors.get(self.status, "secondary")
    
    @property
    def is_active(self) -> bool:
        """Check if assignment is currently active"""
        if not self.is_current:
            return False
        
        today = date.today()
        
        if self.valid_from and self.valid_from > today:
            return False
        if self.valid_to and self.valid_to < today:
            return False
        
        return True
    
    @property
    def duration_days(self) -> Optional[int]:
        """Get assignment duration in days"""
        if not self.valid_from:
            return None
        
        end_date = self.valid_to if self.valid_to else date.today()
        return (end_date - self.valid_from).days
    
    def validate(self) -> List[ValidationError]:
        """Validate assignment data"""
        errors = []
        
        if self.person_id <= 0:
            errors.append(ValidationError("person_id", "Person is required"))
        
        if self.unit_id <= 0:
            errors.append(ValidationError("unit_id", "Unit is required"))
        
        if self.job_title_id <= 0:
            errors.append(ValidationError("job_title_id", "Job title is required"))
        
        if not (0 < self.percentage <= 1.0):
            errors.append(ValidationError("percentage", "Percentage must be between 0 and 100%"))
        
        if self.valid_from and self.valid_to and self.valid_from > self.valid_to:
            errors.append(ValidationError("valid_to", "End date must be after start date"))
        
        # Note: version validation removed as it's now managed by SQL trigger
        
        return errors
    
    @classmethod
    def from_sqlite_row(cls, row):
        """Create Assignment instance from SQLite row"""
        if row is None:
            return None
        
        data = dict(row)
        
        # Parse dates
        for date_field in ['valid_from', 'valid_to']:
            if data.get(date_field):
                try:
                    data[date_field] = date.fromisoformat(data[date_field])
                except (ValueError, TypeError):
                    data[date_field] = None
        
        # Convert boolean fields
        for bool_field in ['is_ad_interim', 'is_unit_boss', 'is_current']:
            if bool_field in data:
                data[bool_field] = bool(data[bool_field])
        
        # Extract computed fields (init=False fields)
        computed_fields = {
            'person_name': data.pop('person_name', None),
            'person_short_name': data.pop('person_short_name', None),
            'unit_name': data.pop('unit_name', None),
            'unit_short_name': data.pop('unit_short_name', None),
            'job_title_name': data.pop('job_title_name', None),
            'job_title_short_name': data.pop('job_title_short_name', None)
        }
        
        # Create instance with regular fields
        instance = cls.from_dict(data)
        
        # Set computed fields
        for field_name, value in computed_fields.items():
            if hasattr(instance, field_name):
                setattr(instance, field_name, value)
        
        return instance
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        result = super().to_dict()
        
        # Convert dates to ISO format
        if self.valid_from:
            result['valid_from'] = self.valid_from.isoformat()
        if self.valid_to:
            result['valid_to'] = self.valid_to.isoformat()
        
        return result