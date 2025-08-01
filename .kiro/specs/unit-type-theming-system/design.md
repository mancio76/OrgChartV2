# Design Document

## Overview

The Unit Type Theming System introduces a flexible, database-driven approach to customize the visual appearance and behavior of organizational units. By implementing a `unit_type_themes` table that separates theming concerns from unit type definitions, the system eliminates hardcoded styling logic and enables unlimited customization possibilities.

The design follows a theme-based architecture where visual properties are defined once in themes and can be reused across multiple unit types, promoting consistency and maintainability.

## Architecture

### Database Schema Design

#### New Tables

**unit_type_themes**
```sql
CREATE TABLE unit_type_themes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    
    -- Visual Properties
    icon_class TEXT NOT NULL DEFAULT 'diagram-2',
    emoji_fallback TEXT NOT NULL DEFAULT '🏛️',
    
    -- Color Scheme
    primary_color TEXT NOT NULL DEFAULT '#0dcaf0',
    secondary_color TEXT NOT NULL DEFAULT '#f0fdff',
    text_color TEXT NOT NULL DEFAULT '#0dcaf0',
    border_color TEXT,
    
    -- Layout Properties
    border_width INTEGER NOT NULL DEFAULT 2,
    border_style TEXT NOT NULL DEFAULT 'solid',
    background_gradient TEXT,
    
    -- CSS Generation
    css_class_suffix TEXT NOT NULL,
    hover_shadow_color TEXT,
    hover_shadow_intensity REAL DEFAULT 0.25,
    
    -- Display Properties
    display_label TEXT NOT NULL,
    display_label_plural TEXT,
    
    -- Accessibility
    high_contrast_mode BOOLEAN DEFAULT FALSE,
    
    -- Metadata
    is_default BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_by TEXT,
    datetime_created DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    datetime_updated DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

#### Modified Tables

**unit_types** (add theme reference)
```sql
ALTER TABLE unit_types ADD COLUMN theme_id INTEGER REFERENCES unit_type_themes(id);
```

#### Default Themes Migration
```sql
-- Create default themes for existing unit types
INSERT INTO unit_type_themes (
    name, description, icon_class, emoji_fallback, primary_color, 
    secondary_color, text_color, border_width, css_class_suffix, 
    display_label, display_label_plural, is_default
) VALUES 
(
    'Function Theme', 
    'Bold styling for organizational functions',
    'building', '🏢', '#0d6efd', '#f8f9ff', '#0d6efd', 4, 
    'function', 'Funzione', 'Funzioni', TRUE
),
(
    'Organizational Theme',
    'Standard styling for organizational units', 
    'diagram-2', '🏛️', '#0dcaf0', '#f0fdff', '#0dcaf0', 2,
    'organizational', 'Unità Organizzativa', 'Unità Organizzative', FALSE
);

-- Assign themes to existing unit types
UPDATE unit_types SET theme_id = 1 WHERE id = 1;
UPDATE unit_types SET theme_id = 2 WHERE id = 2;
```

### Component Architecture

#### Models

**UnitTypeTheme Model**
```python
@dataclass
class UnitTypeTheme(BaseModel):
    id: Optional[int] = None
    name: str = ""
    description: Optional[str] = None
    
    # Visual Properties
    icon_class: str = "diagram-2"
    emoji_fallback: str = "🏛️"
    
    # Color Scheme
    primary_color: str = "#0dcaf0"
    secondary_color: str = "#f0fdff"
    text_color: str = "#0dcaf0"
    border_color: Optional[str] = None
    
    # Layout Properties
    border_width: int = 2
    border_style: str = "solid"
    background_gradient: Optional[str] = None
    
    # CSS Generation
    css_class_suffix: str = "organizational"
    hover_shadow_color: Optional[str] = None
    hover_shadow_intensity: float = 0.25
    
    # Display Properties
    display_label: str = ""
    display_label_plural: Optional[str] = None
    
    # Accessibility
    high_contrast_mode: bool = False
    
    # Metadata
    is_default: bool = False
    is_active: bool = True
    created_by: Optional[str] = None
    
    @property
    def computed_border_color(self) -> str:
        """Get border color, fallback to primary color"""
        return self.border_color or self.primary_color
    
    @property
    def computed_hover_shadow_color(self) -> str:
        """Get hover shadow color, fallback to primary color"""
        return self.hover_shadow_color or self.primary_color
    
    def generate_css_class_name(self) -> str:
        """Generate CSS class name for this theme"""
        return f"unit-{self.css_class_suffix}"
    
    def to_css_variables(self) -> dict:
        """Generate CSS custom properties for this theme"""
        return {
            f"--theme-{self.id}-primary": self.primary_color,
            f"--theme-{self.id}-secondary": self.secondary_color,
            f"--theme-{self.id}-text": self.text_color,
            f"--theme-{self.id}-border": self.computed_border_color,
            f"--theme-{self.id}-border-width": f"{self.border_width}px",
            f"--theme-{self.id}-hover-shadow": self.computed_hover_shadow_color,
        }
```

**Enhanced UnitType Model**
```python
@dataclass
class UnitType(BaseModel):
    # ... existing fields ...
    theme_id: Optional[int] = None
    
    # Computed theme data (loaded via joins)
    theme: Optional[UnitTypeTheme] = field(default=None, init=False)
    
    @property
    def effective_theme(self) -> UnitTypeTheme:
        """Get theme or default theme"""
        if self.theme:
            return self.theme
        return UnitTypeThemeService().get_default_theme()
```

#### Services

**UnitTypeThemeService**
```python
class UnitTypeThemeService(BaseService):
    def get_default_theme(self) -> UnitTypeTheme:
        """Get the default theme"""
        
    def get_themes_with_usage_stats(self) -> List[dict]:
        """Get all themes with unit type usage statistics"""
        
    def can_delete_theme(self, theme_id: int) -> Tuple[bool, str]:
        """Check if theme can be deleted"""
        
    def clone_theme(self, theme_id: int, new_name: str) -> UnitTypeTheme:
        """Create a copy of existing theme"""
        
    def generate_dynamic_css(self) -> str:
        """Generate CSS for all active themes"""
```

**Enhanced UnitTypeService**
```python
class UnitTypeService(BaseService):
    def get_list_query(self) -> str:
        """Enhanced query to include theme data"""
        return """
        SELECT ut.*, utt.*,
               COUNT(u.id) as units_count
        FROM unit_types ut
        LEFT JOIN unit_type_themes utt ON ut.theme_id = utt.id
        LEFT JOIN units u ON ut.id = u.unit_type_id
        GROUP BY ut.id
        ORDER BY ut.name
        """
```

## Components and Interfaces

### Template Integration

#### Dynamic Template Helpers

**Jinja2 Template Functions**
```python
def get_unit_theme_data(unit):
    """Get theme data for a unit"""
    return unit.unit_type.effective_theme

def render_unit_icon(unit):
    """Render unit icon based on theme"""
    theme = get_unit_theme_data(unit)
    return f'<i class="bi bi-{theme.icon_class}"></i>'

def get_unit_css_classes(unit):
    """Get CSS classes for unit based on theme"""
    theme = get_unit_theme_data(unit)
    return f"unit-box {theme.generate_css_class_name()}"
```

#### Template Refactoring Examples

**Before (Hardcoded)**
```html
<div class="unit-box {{ 'unit-function' if node.unit_type_id == 1 else 'unit-organizational' }}">
    <i class="bi bi-{{ 'building' if node.unit_type_id == 1 else 'diagram-2' }}"></i>
    <span class="badge bg-{{ 'primary' if node.unit_type_id == 1 else 'info' }}">
        {{ 'Funzione' if node.unit_type_id == 1 else 'Unità Org.' }}
    </span>
</div>
```

**After (Theme-Driven)**
```html
{% set theme = node.unit_type.effective_theme %}
<div class="unit-box {{ theme.generate_css_class_name() }}" 
     style="--unit-primary: {{ theme.primary_color }}; --unit-border-width: {{ theme.border_width }}px;">
    <i class="bi bi-{{ theme.icon_class }}"></i>
    <span class="badge" style="background-color: {{ theme.primary_color }};">
        {{ theme.display_label }}
    </span>
</div>
```

### CSS Architecture

#### Dynamic CSS Generation

**CSS Template System**
```css
/* Generated CSS for each theme */
.unit-{{ theme.css_class_suffix }} {
    border: {{ theme.border_width }}px {{ theme.border_style }} {{ theme.computed_border_color }};
    background: linear-gradient(135deg, #ffffff 0%, {{ theme.secondary_color }} 100%);
}

.unit-{{ theme.css_class_suffix }}:hover {
    box-shadow: 0 1rem 2rem {{ theme.computed_hover_shadow_color }}{{ theme.hover_shadow_intensity }};
    border-color: {{ theme.primary_color }};
}

.unit-{{ theme.css_class_suffix }} .unit-name {
    color: {{ theme.text_color }};
}
```

#### CSS Custom Properties Approach
```css
:root {
    /* Generated for each theme */
    --theme-1-primary: #0d6efd;
    --theme-1-secondary: #f8f9ff;
    --theme-1-border-width: 4px;
    
    --theme-2-primary: #0dcaf0;
    --theme-2-secondary: #f0fdff;
    --theme-2-border-width: 2px;
}

.unit-themed {
    border: var(--unit-border-width) solid var(--unit-primary);
    background: linear-gradient(135deg, #ffffff 0%, var(--unit-secondary) 100%);
}
```

## Data Models

### Theme Configuration Schema

```json
{
  "theme": {
    "id": 1,
    "name": "Executive Theme",
    "visual": {
      "icon_class": "building-fill",
      "emoji_fallback": "🏢",
      "colors": {
        "primary": "#0d6efd",
        "secondary": "#f8f9ff",
        "text": "#0d6efd",
        "border": "#0d6efd"
      },
      "layout": {
        "border_width": 4,
        "border_style": "solid",
        "background_gradient": "linear-gradient(135deg, #ffffff 0%, #f8f9ff 100%)"
      }
    },
    "css": {
      "class_suffix": "executive",
      "hover_effects": {
        "shadow_color": "#0d6efd",
        "shadow_intensity": 0.4
      }
    },
    "display": {
      "label": "Direzione",
      "label_plural": "Direzioni"
    },
    "accessibility": {
      "high_contrast_mode": false
    }
  }
}
```

## Error Handling

### Theme Validation
- **Color format validation**: Ensure hex colors are valid
- **Icon class validation**: Verify Bootstrap icon classes exist
- **CSS property validation**: Check for valid CSS values
- **Theme reference integrity**: Ensure unit types reference valid themes

### Fallback Mechanisms
- **Missing theme**: Use default theme if theme_id is invalid
- **Invalid theme data**: Fall back to system defaults for invalid properties
- **CSS generation errors**: Skip invalid themes, log errors

### Migration Safety
- **Backup existing data**: Before applying theme migrations
- **Rollback capability**: Ability to revert to hardcoded system
- **Validation checks**: Ensure all unit types have valid theme references

## Testing Strategy

### Unit Tests
- **Theme model validation**: Test all theme property validations
- **CSS generation**: Test dynamic CSS output for various theme configurations
- **Template helpers**: Test Jinja2 helper functions with different theme data
- **Service methods**: Test theme CRUD operations and business logic

### Integration Tests
- **Database migrations**: Test theme table creation and data migration
- **Template rendering**: Test orgchart templates with theme data
- **CSS application**: Test that generated CSS is properly applied
- **Theme management UI**: Test administrative interface functionality

### Visual Regression Tests
- **Orgchart rendering**: Compare before/after screenshots
- **Theme variations**: Test multiple themes render correctly
- **Responsive behavior**: Test themes work across device sizes
- **Accessibility compliance**: Test color contrast and accessibility features

### Performance Tests
- **CSS generation time**: Measure dynamic CSS generation performance
- **Template rendering**: Test rendering speed with theme data
- **Database queries**: Ensure theme joins don't impact query performance
- **Memory usage**: Monitor memory impact of theme data caching