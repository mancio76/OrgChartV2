"""
Unit model - Corrected to match database schema
CORRECTIONS APPLIED:
1. Updated table field names to match units table schema
2. Fixed datetime field handling (managed by SQL triggers and defaults)
3. Corrected field mappings for SQLite row conversion
4. Fixed computed field handling for views like units_types
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Optional, List, Any
from app.models.base import BaseModel, Alias, parse_aliases, serialize_aliases, ValidationError
from app.models.assignment import Assignment

@dataclass
class Unit(BaseModel):
    """Unit organizational model - matches units table"""
    id: Optional[int] = None
    name: str = ""
    short_name: Optional[str] = None
    unit_type_id: int = 1  # References unit_types.id
    parent_unit_id: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    aliases: List[Alias] = field(default_factory=list)
    
    # Computed fields from joins/views (not stored in units table)
    # These come from units_types view and other joins
    unit_name: Optional[str] = field(default=None, init=False)  # From units_types view
    unit_short_name: Optional[str] = field(default=None, init=False)  # From units_types view
    unit_type: Optional[str] = field(default=None, init=True)  # unit_types.name
    unit_type_short: Optional[str] = field(default=None, init=True)  # unit_types.short_name
    unit_aliases: Optional[str] = field(default=None, init=False)  # From units_types view
    parent_name: Optional[str] = field(default=None, init=False)
    children_count: int = field(default=0, init=False)
    person_count: int = field(default=0, init=False)
    level: int = field(default=0, init=False)
    path: str = field(default="", init=False)
    full_path: str = field(default="", init=False)
    full_short_path: str = field(default="", init=False)
    short_path: str = field(default="", init=False)
    assignments: Optional[List[Assignment]] = field(default_factory=list, init=True)
    children: Optional[List[Any]] = field(default_factory=list, init=True)
    
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
        # Use computed fields from views if available
        if hasattr(self, 'unit_short_name') and self.unit_short_name:
            return self.unit_short_name
        elif self.short_name:
            return self.short_name
        elif hasattr(self, 'unit_name') and self.unit_name:
            return self.unit_name
        else:
            return self.name
    
    @property
    def full_name(self) -> str:
        """Get full name for display"""
        # Use computed fields from views if available
        if hasattr(self, 'unit_name') and self.unit_name:
            return self.unit_name
        else:
            return self.name
    
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
        
        if self.unit_type_id <= 0:
            errors.append(ValidationError("unit_type_id", "Unit Type is required"))
        
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
        # These fields come from views like units_types, units_hierarchy, etc.
        computed_fields = {
            'unit_name': data.pop('unit_name', None),
            'unit_short_name': data.pop('unit_short_name', None),
            'unit_type': data.pop('unit_type', None),
            'unit_type_short': data.pop('unit_type_short', None),
            'unit_aliases': data.pop('unit_aliases', None),
            'parent_name': data.pop('parent_name', None),
            'children_count': data.pop('children_count', 0),
            'person_count': data.pop('person_count', 0),
            'level': data.pop('level', 0),
            'path': data.pop('path', ''),
            'full_path': data.pop('full_path', ''),
            'full_short_path': data.pop('full_short_path', ''),
            'short_path': data.pop('short_path', ''),
            'assignments': data.pop('assignments', []),
            'children': data.pop('children', [])
        }
        
        # Create instance with regular fields only
        # Filter out computed fields from data before creating instance
        filtered_data = {k: v for k, v in data.items() 
                        if k not in computed_fields.keys()}
        
        instance = cls.from_dict(filtered_data)
        
        # Set computed fields
        for field_name, value in computed_fields.items():
            if hasattr(instance, field_name):
                if field_name in ['children_count', 'person_count', 'level']:
                    # Ensure numeric fields are properly converted
                    setattr(instance, field_name, int(value) if value is not None else 0)
                else:
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