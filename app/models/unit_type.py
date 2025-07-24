"""
Unit Type model
"""

from dataclasses import dataclass, field
from typing import Optional, List
from app.models.base import BaseModel, Alias, parse_aliases, serialize_aliases, ValidationError


@dataclass
class UnitType(BaseModel):
    """Unit Type model"""
    id: Optional[int] = None
    name: str = ""
    short_name: Optional[str] = None
    aliases: List[Alias] = field(default_factory=list)
    level: Optional[int] = None
    
    # Computed fields (not stored in DB)
    units_count: int = field(default=0, init=False)
    
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
        """Get display name"""
        return self.name
    
    def get_alias_by_language(self, lang: str = "en-US") -> Optional[str]:
        """Get alias value for specific language"""
        for alias in self.aliases:
            if alias.lang == lang:
                return alias.value
        return None
    
    def add_alias(self, value: str, lang: str = "it-IT") -> None:
        """Add a new alias for the unit type"""
        # Remove existing alias for the same language
        self.aliases = [alias for alias in self.aliases if alias.lang != lang]
        # Add new alias
        self.aliases.append(Alias(value=value, lang=lang))
    
    def get_localized_name(self, lang: str = "it-IT") -> str:
        """Get localized name, fallback to default name if not found"""
        alias = self.get_alias_by_language(lang)
        return alias if alias else self.name
    
    def validate(self) -> List[ValidationError]:
        """Validate unit type data"""
        errors = []
        
        if not self.name or not self.name.strip():
            errors.append(ValidationError("name", "Name is required"))
        
        # Validate aliases
        for alias in self.aliases:
            if not alias.value or not alias.value.strip():
                errors.append(ValidationError("aliases", f"Alias value cannot be empty for language {alias.lang}"))
            if not alias.lang or not alias.lang.strip():
                errors.append(ValidationError("aliases", "Alias language cannot be empty"))
        
        return errors
    
    @classmethod
    def from_sqlite_row(cls, row):
        """Create UnitType instance from SQLite row"""
        if row is None:
            return None
        
        data = dict(row)
        
        # Parse aliases
        if 'aliases' in data:
            data['aliases'] = parse_aliases(data['aliases'])
        
        # Extract computed fields (init=False fields)
        computed_fields = {
            'units_count': data.pop('units_count', 0)
        }
        
        # Create instance with regular fields
        instance = cls.from_dict(data)
        
        # Set computed fields
        for field_name, value in computed_fields.items():
            if hasattr(instance, field_name):
                setattr(instance, field_name, int(value) if value is not None else 0)
        
        return instance
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        result = super().to_dict()
        
        # Convert aliases to dict format
        result['aliases'] = [alias.to_dict() for alias in self.aliases]
        
        return result