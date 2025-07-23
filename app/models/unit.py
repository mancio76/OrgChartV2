"""
Unit model
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Optional, List
from app.models.base import BaseModel, Alias, parse_aliases, serialize_aliases, ValidationError


@dataclass
class Unit(BaseModel):
    """Unit organizational model"""
    id: Optional[int] = None
    name: str = ""
    short_name: Optional[str] = None
    type: str = "function"  # function or OrganizationalUnit
    parent_unit_id: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    aliases: List[Alias] = field(default_factory=list)
    
    # Computed fields (not stored in DB)
    parent_name: Optional[str] = field(default=None, init=False)
    children_count: int = field(default=0, init=False)
    person_count: int = field(default=0, init=False)
    level: int = field(default=0, init=False)
    path: str = field(default="", init=False)
    full_path: str = field(default="", init=False)
    
    def __post_init__(self):
        """Post-initialization validation"""
        if isinstance(self.aliases, str):
            self.aliases = parse_aliases(self.aliases)
    
    @property
    def aliases_json(self) -> str:
        """Get aliases as JSON string for database storage"""
        return serialize_aliases(self.aliases)
    
    @property
    def display_name(self) -> str:
        """Get display name (short_name if available, otherwise name)"""
        return self.short_name if self.short_name else self.name
    
    @property
    def is_root(self) -> bool:
        """Check if this is a root unit"""
        return self.parent_unit_id is None or self.parent_unit_id == -1
    
    @property
    def is_active(self) -> bool:
        """Check if unit is currently active"""
        from datetime import date
        today = date.today()
        
        if self.start_date and self.start_date > today:
            return False
        if self.end_date and self.end_date < today:
            return False
        return True
    
    def validate(self) -> List[ValidationError]:
        """Validate unit data"""
        errors = []
        
        if not self.name or not self.name.strip():
            errors.append(ValidationError("name", "Name is required"))
        
        if self.type not in ["function", "OrganizationalUnit"]:
            errors.append(ValidationError("type", "Type must be 'function' or 'OrganizationalUnit'"))
        
        if self.start_date and self.end_date and self.start_date > self.end_date:
            errors.append(ValidationError("end_date", "End date must be after start date"))
        
        if self.id is not None and self.parent_unit_id == self.id:
            errors.append(ValidationError("parent_unit_id", "Unit cannot be its own parent"))
        
        return errors
    
    @classmethod
    def from_sqlite_row(cls, row):
        """Create Unit instance from SQLite row"""
        if row is None:
            return None
        
        data = dict(row)
        
        # Parse dates
        for date_field in ['start_date', 'end_date']:
            if data.get(date_field):
                try:
                    data[date_field] = date.fromisoformat(data[date_field])
                except (ValueError, TypeError):
                    data[date_field] = None
        
        # Parse aliases
        if 'aliases' in data:
            data['aliases'] = parse_aliases(data['aliases'])
        
        # Extract computed fields (init=False fields)
        computed_fields = {
            'parent_name': data.pop('parent_name', None),
            'children_count': data.pop('children_count', 0),
            'person_count': data.pop('person_count', 0),
            'level': data.pop('level', 0),
            'path': data.pop('path', ''),
            'full_path': data.pop('full_path', '')
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
        if self.start_date:
            result['start_date'] = self.start_date.isoformat()
        if self.end_date:
            result['end_date'] = self.end_date.isoformat()
        
        # Convert aliases to dict format
        result['aliases'] = [alias.to_dict() for alias in self.aliases]
        
        return result