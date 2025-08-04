"""
Unit Type model
"""

from dataclasses import dataclass, field
from typing import Optional, List, TYPE_CHECKING
from app.models.base import BaseModel, Alias, parse_aliases, serialize_aliases, ValidationError

# Import for type hints only to avoid circular imports
if TYPE_CHECKING:
    from app.models.unit_type_theme import UnitTypeTheme


@dataclass
class UnitType(BaseModel):
    """Unit Type model"""
    id: Optional[int] = None
    name: str = ""
    short_name: Optional[str] = None
    aliases: List[Alias] = field(default_factory=list)
    level: Optional[int] = None
    theme_id: Optional[int] = None
    
    # Computed fields (not stored in DB)
    units_count: int = field(default=0, init=False)
    theme: Optional['UnitTypeTheme'] = field(default=None, init=False)
    
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
    
    @property
    def effective_theme(self) -> 'UnitTypeTheme':
        """Get theme or default theme"""
        if self.theme:
            return self.theme
        
        # Import here to avoid circular imports
        from app.services.unit_type_theme import UnitTypeThemeService
        return UnitTypeThemeService().get_default_theme()
    
    def validate(self) -> List[ValidationError]:
        """Validate unit type data"""
        errors = []
        
        if not self.name or not self.name.strip():
            errors.append(ValidationError("name", "Name is required"))
        
        # Validate theme_id if provided
        if self.theme_id is not None:
            if not isinstance(self.theme_id, int) or self.theme_id <= 0:
                errors.append(ValidationError("theme_id", "Theme ID must be a positive integer"))
        
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
        
        # Extract theme data if present (from joins)
        theme_data = {}
        theme_fields = [
            'theme_name', 'theme_description', 'theme_icon_class', 'theme_emoji_fallback',
            'theme_primary_color', 'theme_secondary_color', 'theme_text_color', 'theme_border_color',
            'theme_border_width', 'theme_border_style', 'theme_background_gradient',
            'theme_css_class_suffix', 'theme_hover_shadow_color', 'theme_hover_shadow_intensity',
            'theme_display_label', 'theme_display_label_plural', 'theme_high_contrast_mode',
            'theme_is_default', 'theme_is_active', 'theme_created_by',
            'theme_datetime_created', 'theme_datetime_updated'
        ]
        
        for field in theme_fields:
            if field in data:
                # Remove 'theme_' prefix for the theme model
                theme_field_name = field.replace('theme_', '')
                theme_data[theme_field_name] = data.pop(field)
        
        # If we have theme data, create theme instance
        theme_instance = None
        if theme_data and data.get('theme_id'):
            # Import here to avoid circular imports
            from app.models.unit_type_theme import UnitTypeTheme
            
            # Add the theme ID to theme data
            theme_data['id'] = data.get('theme_id')
            
            # Handle special field mappings
            if 'name' not in theme_data and 'theme_name' in dict(row):
                theme_data['name'] = dict(row)['theme_name']
            
            try:
                theme_instance = UnitTypeTheme.from_dict(theme_data)
            except Exception:
                # If theme creation fails, we'll use the fallback in effective_theme
                theme_instance = None
        
        # Extract computed fields (init=False fields)
        computed_fields = {
            'units_count': data.pop('units_count', 0),
            'theme': theme_instance
        }
        
        # Create instance with regular fields
        instance = cls.from_dict(data)
        
        # Set computed fields
        for field_name, value in computed_fields.items():
            if hasattr(instance, field_name):
                if field_name == 'units_count':
                    setattr(instance, field_name, int(value) if value is not None else 0)
                else:
                    setattr(instance, field_name, value)
        
        return instance
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        result = super().to_dict()
        
        # Convert aliases to dict format
        result['aliases'] = [alias.to_dict() for alias in self.aliases]
        
        # Include theme information if available
        if self.theme:
            result['theme'] = self.theme.to_dict()
        
        # Include effective theme information
        try:
            effective_theme = self.effective_theme
            result['effective_theme'] = effective_theme.to_dict()
        except Exception:
            # If we can't get effective theme, don't include it
            pass
        
        return result