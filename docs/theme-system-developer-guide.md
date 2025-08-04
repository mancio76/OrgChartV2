# Developer Guide - Unit Type Theming System

## Architecture Overview

The Unit Type Theming System is a comprehensive solution that replaces hardcoded styling logic with a flexible, database-driven theming approach. The system follows a layered architecture with clear separation of concerns.

### Core Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Templates     │    │    Services     │    │     Models      │
│                 │    │                 │    │                 │
│ - Jinja2 Helpers│◄──►│ ThemeService    │◄──►│ UnitTypeTheme   │
│ - Dynamic CSS   │    │ UnitTypeService │    │ UnitType        │
│ - Theme Rendering│    │ OrgchartService │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │    Database     │
                    │                 │
                    │ unit_type_themes│
                    │ unit_types      │
                    │ units           │
                    └─────────────────┘
```

## Database Schema

### Primary Tables

#### unit_type_themes
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

#### Enhanced unit_types
```sql
-- Added theme relationship
ALTER TABLE unit_types ADD COLUMN theme_id INTEGER REFERENCES unit_type_themes(id);
```

### Foreign Key Relationships

```
unit_types.theme_id → unit_type_themes.id
units.unit_type_id → unit_types.id
```

## Model Layer

### UnitTypeTheme Model

```python
@dataclass
class UnitTypeTheme(BaseModel):
    """
    Represents a visual theme configuration for unit types.
    
    This model encapsulates all visual properties, CSS generation logic,
    and validation rules for unit type themes.
    """
    
    # Core identification
    id: Optional[int] = None
    name: str = ""
    description: Optional[str] = None
    
    # Visual properties
    icon_class: str = "diagram-2"
    emoji_fallback: str = "🏛️"
    
    # Color scheme
    primary_color: str = "#0dcaf0"
    secondary_color: str = "#f0fdff"
    text_color: str = "#0dcaf0"
    border_color: Optional[str] = None
    
    # Layout properties
    border_width: int = 2
    border_style: str = "solid"
    background_gradient: Optional[str] = None
    
    # CSS generation
    css_class_suffix: str = "organizational"
    hover_shadow_color: Optional[str] = None
    hover_shadow_intensity: float = 0.25
    
    # Display properties
    display_label: str = ""
    display_label_plural: Optional[str] = None
    
    # Accessibility
    high_contrast_mode: bool = False
    
    # Metadata
    is_default: bool = False
    is_active: bool = True
    created_by: Optional[str] = None
```

### Key Model Methods

#### Computed Properties
```python
@property
def computed_border_color(self) -> str:
    """Get border color with fallback to primary color."""
    return self.border_color or self.primary_color

@property
def computed_hover_shadow_color(self) -> str:
    """Get hover shadow color with fallback to primary color."""
    return self.hover_shadow_color or self.primary_color
```

#### CSS Generation
```python
def generate_css_class_name(self) -> str:
    """Generate CSS class name for this theme."""
    return f"unit-{self.css_class_suffix}"

def to_css_variables(self) -> dict:
    """Generate CSS custom properties for this theme."""
    return {
        f"--theme-{self.id}-primary": self.primary_color,
        f"--theme-{self.id}-secondary": self.secondary_color,
        f"--theme-{self.id}-text": self.text_color,
        f"--theme-{self.id}-border": self.computed_border_color,
        f"--theme-{self.id}-border-width": f"{self.border_width}px",
        f"--theme-{self.id}-hover-shadow": self.computed_hover_shadow_color,
    }
```

#### Validation
```python
def validate_colors(self) -> List[str]:
    """Validate all color properties."""
    errors = []
    color_fields = ['primary_color', 'secondary_color', 'text_color']
    
    for field in color_fields:
        color = getattr(self, field)
        if not self._is_valid_hex_color(color):
            errors.append(f"Invalid hex color format for {field}: {color}")
    
    return errors

def validate_accessibility(self) -> List[str]:
    """Validate color contrast for accessibility."""
    errors = []
    
    # Check contrast between text and background
    contrast_ratio = self._calculate_contrast_ratio(
        self.text_color, 
        self.secondary_color
    )
    
    if contrast_ratio < 4.5:  # WCAG AA standard
        errors.append(f"Insufficient color contrast: {contrast_ratio:.2f}")
    
    return errors
```

## Service Layer

### UnitTypeThemeService

The service layer handles all business logic for theme management.

#### Core CRUD Operations
```python
class UnitTypeThemeService(BaseService):
    """Service for managing unit type themes."""
    
    def get_default_theme(self) -> UnitTypeTheme:
        """Get the system default theme."""
        query = "SELECT * FROM unit_type_themes WHERE is_default = 1 LIMIT 1"
        row = self.db.execute(query).fetchone()
        
        if not row:
            # Create default theme if none exists
            return self._create_system_default_theme()
        
        return UnitTypeTheme.from_sqlite_row(row)
    
    def get_themes_with_usage_stats(self) -> List[dict]:
        """Get all themes with usage statistics."""
        query = """
        SELECT utt.*, 
               COUNT(ut.id) as usage_count,
               GROUP_CONCAT(ut.name) as used_by_unit_types
        FROM unit_type_themes utt
        LEFT JOIN unit_types ut ON utt.id = ut.theme_id
        WHERE utt.is_active = 1
        GROUP BY utt.id
        ORDER BY usage_count DESC, utt.name
        """
        
        rows = self.db.execute(query).fetchall()
        return [self._row_to_usage_dict(row) for row in rows]
    
    def can_delete_theme(self, theme_id: int) -> Tuple[bool, str]:
        """Check if theme can be safely deleted."""
        # Check if theme is default
        theme = self.get_by_id(theme_id)
        if theme.is_default:
            return False, "Cannot delete default theme"
        
        # Check usage
        usage_count = self._get_theme_usage_count(theme_id)
        if usage_count > 0:
            return False, f"Theme is used by {usage_count} unit types"
        
        return True, "Theme can be deleted"
    
    def clone_theme(self, theme_id: int, new_name: str) -> UnitTypeTheme:
        """Create a copy of existing theme with new name."""
        original = self.get_by_id(theme_id)
        
        # Create new theme with same properties
        cloned = UnitTypeTheme(
            name=new_name,
            description=f"Cloned from {original.name}",
            **{k: v for k, v in original.to_dict().items() 
               if k not in ['id', 'name', 'description', 'is_default']}
        )
        
        return self.create(cloned)
```

#### Dynamic CSS Generation
```python
def generate_dynamic_css(self) -> str:
    """Generate CSS for all active themes."""
    themes = self.get_all_active()
    css_parts = []
    
    # Generate CSS custom properties
    root_vars = []
    for theme in themes:
        root_vars.extend([
            f"  {k}: {v};" for k, v in theme.to_css_variables().items()
        ])
    
    css_parts.append(":root {\n" + "\n".join(root_vars) + "\n}")
    
    # Generate theme-specific classes
    for theme in themes:
        css_parts.append(self._generate_theme_css(theme))
    
    return "\n\n".join(css_parts)

def _generate_theme_css(self, theme: UnitTypeTheme) -> str:
    """Generate CSS for a specific theme."""
    class_name = theme.generate_css_class_name()
    
    return f"""
.{class_name} {{
    border: {theme.border_width}px {theme.border_style} {theme.computed_border_color};
    background: linear-gradient(135deg, #ffffff 0%, {theme.secondary_color} 100%);
    color: {theme.text_color};
}}

.{class_name}:hover {{
    box-shadow: 0 1rem 2rem {theme.computed_hover_shadow_color}{theme.hover_shadow_intensity:02.0f};
    border-color: {theme.primary_color};
    transform: translateY(-2px);
}}

.{class_name} .unit-name {{
    color: {theme.text_color};
    font-weight: 600;
}}

.{class_name} .unit-badge {{
    background-color: {theme.primary_color};
    color: white;
}}
"""
```

### Enhanced UnitTypeService

The UnitTypeService is enhanced to include theme data in all queries.

```python
class UnitTypeService(BaseService):
    """Enhanced service with theme support."""
    
    def get_list_query(self) -> str:
        """Query that includes theme data via JOIN."""
        return """
        SELECT ut.*, 
               utt.name as theme_name,
               utt.icon_class, utt.emoji_fallback,
               utt.primary_color, utt.secondary_color, utt.text_color,
               utt.border_color, utt.border_width, utt.border_style,
               utt.css_class_suffix, utt.display_label, utt.display_label_plural,
               utt.hover_shadow_color, utt.hover_shadow_intensity,
               utt.high_contrast_mode, utt.is_default as theme_is_default,
               COUNT(u.id) as units_count
        FROM unit_types ut
        LEFT JOIN unit_type_themes utt ON ut.theme_id = utt.id
        LEFT JOIN units u ON ut.id = u.unit_type_id
        GROUP BY ut.id
        ORDER BY ut.name
        """
    
    def get_by_id_query(self, id: int) -> str:
        """Query for single unit type with theme data."""
        return f"""
        SELECT ut.*, 
               utt.name as theme_name,
               utt.icon_class, utt.emoji_fallback,
               utt.primary_color, utt.secondary_color, utt.text_color,
               utt.border_color, utt.border_width, utt.border_style,
               utt.css_class_suffix, utt.display_label, utt.display_label_plural,
               utt.hover_shadow_color, utt.hover_shadow_intensity,
               utt.high_contrast_mode, utt.is_default as theme_is_default
        FROM unit_types ut
        LEFT JOIN unit_type_themes utt ON ut.theme_id = utt.id
        WHERE ut.id = {id}
        """
```

## Template Integration

### Jinja2 Template Helpers

The system provides several template helper functions for theme-driven rendering.

```python
def get_unit_theme_data(unit):
    """Get theme data for a unit."""
    if hasattr(unit, 'unit_type') and hasattr(unit.unit_type, 'theme'):
        return unit.unit_type.theme
    return unit.unit_type.effective_theme

def render_unit_icon(unit):
    """Render unit icon based on theme."""
    theme = get_unit_theme_data(unit)
    return f'<i class="bi bi-{theme.icon_class}" aria-hidden="true"></i>'

def get_unit_css_classes(unit):
    """Get CSS classes for unit based on theme."""
    theme = get_unit_theme_data(unit)
    base_classes = "unit-box unit-themed"
    theme_class = theme.generate_css_class_name()
    return f"{base_classes} {theme_class}"

def get_unit_inline_styles(unit):
    """Generate inline CSS variables for unit."""
    theme = get_unit_theme_data(unit)
    variables = theme.to_css_variables()
    
    style_parts = []
    for var_name, var_value in variables.items():
        style_parts.append(f"{var_name}: {var_value}")
    
    return "; ".join(style_parts)
```

### Template Refactoring Pattern

#### Before (Hardcoded)
```html
<div class="unit-box {{ 'unit-function' if node.unit_type_id == 1 else 'unit-organizational' }}">
    <i class="bi bi-{{ 'building' if node.unit_type_id == 1 else 'diagram-2' }}"></i>
    <span class="badge bg-{{ 'primary' if node.unit_type_id == 1 else 'info' }}">
        {{ 'Funzione' if node.unit_type_id == 1 else 'Unità Org.' }}
    </span>
</div>
```

#### After (Theme-Driven)
```html
{% set theme = get_unit_theme_data(node) %}
<div class="{{ get_unit_css_classes(node) }}" 
     style="{{ get_unit_inline_styles(node) }}">
    {{ render_unit_icon(node) | safe }}
    <span class="badge unit-badge">
        {{ theme.display_label }}
    </span>
</div>
```

## CSS Architecture

### Dynamic CSS Generation

The system generates CSS dynamically based on active themes:

```css
/* Generated CSS custom properties */
:root {
  --theme-1-primary: #0d6efd;
  --theme-1-secondary: #f8f9ff;
  --theme-1-text: #0d6efd;
  --theme-1-border: #0d6efd;
  --theme-1-border-width: 4px;
  --theme-1-hover-shadow: #0d6efd;
  
  --theme-2-primary: #0dcaf0;
  --theme-2-secondary: #f0fdff;
  --theme-2-text: #0dcaf0;
  --theme-2-border: #0dcaf0;
  --theme-2-border-width: 2px;
  --theme-2-hover-shadow: #0dcaf0;
}

/* Base themed unit class */
.unit-themed {
    transition: all 0.3s ease;
    border-radius: 8px;
    padding: 1rem;
    margin: 0.5rem;
    position: relative;
}

/* Theme-specific classes */
.unit-function {
    border: var(--theme-1-border-width) solid var(--theme-1-border);
    background: linear-gradient(135deg, #ffffff 0%, var(--theme-1-secondary) 100%);
    color: var(--theme-1-text);
}

.unit-organizational {
    border: var(--theme-2-border-width) solid var(--theme-2-border);
    background: linear-gradient(135deg, #ffffff 0%, var(--theme-2-secondary) 100%);
    color: var(--theme-2-text);
}
```

### CSS Caching Strategy

```python
class CSSCacheManager:
    """Manages CSS generation and caching."""
    
    def __init__(self):
        self._cache = {}
        self._cache_timestamp = None
    
    def get_cached_css(self) -> Optional[str]:
        """Get cached CSS if still valid."""
        if not self._is_cache_valid():
            return None
        return self._cache.get('dynamic_css')
    
    def cache_css(self, css_content: str):
        """Cache generated CSS."""
        self._cache['dynamic_css'] = css_content
        self._cache_timestamp = datetime.now()
    
    def invalidate_cache(self):
        """Invalidate CSS cache when themes change."""
        self._cache.clear()
        self._cache_timestamp = None
```

## Route Layer

### Theme Management Routes

```python
@router.get("/themes", response_class=HTMLResponse)
async def list_themes(request: Request):
    """Display all themes with usage statistics."""
    service = UnitTypeThemeService()
    themes_with_stats = service.get_themes_with_usage_stats()
    
    return templates.TemplateResponse("themes/list.html", {
        "request": request,
        "themes": themes_with_stats,
        "page_title": "Gestione Temi"
    })

@router.get("/themes/new", response_class=HTMLResponse)
async def create_theme_form(request: Request):
    """Display theme creation form."""
    return templates.TemplateResponse("themes/create.html", {
        "request": request,
        "theme": UnitTypeTheme(),  # Empty theme for form
        "page_title": "Nuovo Tema"
    })

@router.post("/themes", response_class=HTMLResponse)
async def create_theme(request: Request):
    """Handle theme creation."""
    form_data = await request.form()
    
    try:
        theme = UnitTypeTheme.from_form_data(form_data)
        service = UnitTypeThemeService()
        
        # Validate theme
        validation_errors = theme.validate()
        if validation_errors:
            return templates.TemplateResponse("themes/create.html", {
                "request": request,
                "theme": theme,
                "errors": validation_errors,
                "page_title": "Nuovo Tema"
            })
        
        # Create theme
        created_theme = service.create(theme)
        
        # Invalidate CSS cache
        css_cache.invalidate_cache()
        
        return RedirectResponse(
            url=f"/themes/{created_theme.id}",
            status_code=303
        )
        
    except Exception as e:
        logger.error(f"Error creating theme: {e}")
        return templates.TemplateResponse("themes/create.html", {
            "request": request,
            "theme": UnitTypeTheme.from_form_data(form_data),
            "errors": [str(e)],
            "page_title": "Nuovo Tema"
        })
```

### Dynamic CSS Route

```python
@router.get("/css/themes.css", response_class=PlainTextResponse)
async def dynamic_theme_css():
    """Serve dynamically generated theme CSS."""
    
    # Check cache first
    cached_css = css_cache.get_cached_css()
    if cached_css:
        return PlainTextResponse(
            cached_css,
            media_type="text/css",
            headers={"Cache-Control": "public, max-age=3600"}
        )
    
    # Generate CSS
    service = UnitTypeThemeService()
    css_content = service.generate_dynamic_css()
    
    # Cache for future requests
    css_cache.cache_css(css_content)
    
    return PlainTextResponse(
        css_content,
        media_type="text/css",
        headers={"Cache-Control": "public, max-age=3600"}
    )
```

## Testing Strategy

### Unit Tests

```python
class TestUnitTypeTheme:
    """Test theme model functionality."""
    
    def test_theme_validation(self):
        """Test theme property validation."""
        theme = UnitTypeTheme(
            name="Test Theme",
            primary_color="#invalid",  # Invalid color
            border_width=0  # Invalid width
        )
        
        errors = theme.validate()
        assert len(errors) > 0
        assert any("Invalid hex color" in error for error in errors)
    
    def test_css_generation(self):
        """Test CSS class and variable generation."""
        theme = UnitTypeTheme(
            id=1,
            css_class_suffix="test",
            primary_color="#ff0000"
        )
        
        class_name = theme.generate_css_class_name()
        assert class_name == "unit-test"
        
        css_vars = theme.to_css_variables()
        assert "--theme-1-primary" in css_vars
        assert css_vars["--theme-1-primary"] == "#ff0000"
    
    def test_accessibility_validation(self):
        """Test color contrast validation."""
        theme = UnitTypeTheme(
            text_color="#ffffff",      # White text
            secondary_color="#ffffff"  # White background - poor contrast
        )
        
        errors = theme.validate_accessibility()
        assert len(errors) > 0
        assert "Insufficient color contrast" in errors[0]
```

### Integration Tests

```python
class TestThemeIntegration:
    """Test theme system integration."""
    
    def test_theme_assignment_to_unit_type(self):
        """Test assigning theme to unit type."""
        # Create theme
        theme_service = UnitTypeThemeService()
        theme = theme_service.create(UnitTypeTheme(
            name="Integration Test Theme",
            primary_color="#00ff00"
        ))
        
        # Assign to unit type
        unit_type_service = UnitTypeService()
        unit_type = unit_type_service.get_by_id(1)
        unit_type.theme_id = theme.id
        unit_type_service.update(unit_type)
        
        # Verify assignment
        updated_unit_type = unit_type_service.get_by_id(1)
        assert updated_unit_type.theme_id == theme.id
        assert updated_unit_type.theme.primary_color == "#00ff00"
    
    def test_dynamic_css_generation(self):
        """Test CSS generation includes all active themes."""
        service = UnitTypeThemeService()
        css_content = service.generate_dynamic_css()
        
        # Should include CSS custom properties
        assert ":root {" in css_content
        assert "--theme-" in css_content
        
        # Should include theme-specific classes
        active_themes = service.get_all_active()
        for theme in active_themes:
            class_name = theme.generate_css_class_name()
            assert f".{class_name}" in css_content
```

## Performance Considerations

### Database Optimization

1. **Indexing Strategy**:
   ```sql
   CREATE INDEX idx_unit_types_theme_id ON unit_types(theme_id);
   CREATE INDEX idx_unit_type_themes_active ON unit_type_themes(is_active);
   CREATE INDEX idx_unit_type_themes_default ON unit_type_themes(is_default);
   ```

2. **Query Optimization**:
   - Use JOINs to fetch theme data with unit types in single query
   - Implement query result caching for frequently accessed themes
   - Use prepared statements for repeated queries

### CSS Generation Optimization

1. **Caching Strategy**:
   - Cache generated CSS until themes are modified
   - Use ETags for browser caching
   - Implement gzip compression for CSS responses

2. **Lazy Loading**:
   - Generate CSS only when requested
   - Cache CSS in memory for subsequent requests
   - Invalidate cache when themes are modified

### Memory Management

1. **Theme Data Caching**:
   - Cache frequently used themes in memory
   - Implement LRU eviction for theme cache
   - Monitor memory usage of cached themes

## Security Considerations

### Input Validation

1. **Color Validation**:
   ```python
   def validate_hex_color(color: str) -> bool:
       """Validate hex color format."""
       pattern = r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$'
       return bool(re.match(pattern, color))
   ```

2. **CSS Injection Prevention**:
   ```python
   def sanitize_css_value(value: str) -> str:
       """Sanitize CSS values to prevent injection."""
       # Remove potentially dangerous characters
       dangerous_chars = [';', '{', '}', '(', ')', 'javascript:', 'expression(']
       for char in dangerous_chars:
           value = value.replace(char, '')
       return value
   ```

### Access Control

1. **Theme Management Permissions**:
   - Restrict theme creation/modification to admin users
   - Log all theme changes for audit trail
   - Implement role-based access control

2. **CSS Generation Security**:
   - Validate all theme properties before CSS generation
   - Escape user-provided values in CSS output
   - Implement rate limiting for CSS generation endpoint

## Migration and Deployment

### Database Migration

The system includes comprehensive migration scripts:

```python
def migrate_to_theme_system():
    """Migrate existing system to use themes."""
    
    # 1. Create theme table
    create_theme_table()
    
    # 2. Create default themes
    create_default_themes()
    
    # 3. Add theme_id column to unit_types
    add_theme_id_column()
    
    # 4. Assign themes to existing unit types
    assign_themes_to_existing_unit_types()
    
    # 5. Validate migration
    validate_theme_migration()
```

### Rollback Procedures

```python
def rollback_theme_system():
    """Rollback theme system migration."""
    
    # 1. Remove theme_id column from unit_types
    remove_theme_id_column()
    
    # 2. Drop theme table
    drop_theme_table()
    
    # 3. Restore hardcoded template logic
    restore_hardcoded_templates()
    
    # 4. Validate rollback
    validate_rollback()
```

## Monitoring and Maintenance

### Health Checks

```python
def check_theme_system_health():
    """Perform health checks on theme system."""
    
    checks = []
    
    # Check default theme exists
    default_theme = UnitTypeThemeService().get_default_theme()
    checks.append({
        'check': 'default_theme_exists',
        'status': 'ok' if default_theme else 'error',
        'message': 'Default theme found' if default_theme else 'No default theme'
    })
    
    # Check orphaned unit types
    orphaned_count = count_orphaned_unit_types()
    checks.append({
        'check': 'orphaned_unit_types',
        'status': 'ok' if orphaned_count == 0 else 'warning',
        'message': f'{orphaned_count} unit types without valid themes'
    })
    
    # Check CSS generation
    try:
        css_content = UnitTypeThemeService().generate_dynamic_css()
        checks.append({
            'check': 'css_generation',
            'status': 'ok',
            'message': f'Generated {len(css_content)} characters of CSS'
        })
    except Exception as e:
        checks.append({
            'check': 'css_generation',
            'status': 'error',
            'message': f'CSS generation failed: {str(e)}'
        })
    
    return checks
```

### Performance Monitoring

```python
def monitor_theme_performance():
    """Monitor theme system performance metrics."""
    
    metrics = {}
    
    # CSS generation time
    start_time = time.time()
    UnitTypeThemeService().generate_dynamic_css()
    metrics['css_generation_time'] = time.time() - start_time
    
    # Theme query performance
    start_time = time.time()
    UnitTypeThemeService().get_themes_with_usage_stats()
    metrics['theme_query_time'] = time.time() - start_time
    
    # Cache hit rate
    metrics['css_cache_hit_rate'] = css_cache.get_hit_rate()
    
    return metrics
```

## Troubleshooting Common Issues

### Theme Not Displaying

1. **Check theme assignment**: Verify unit type has valid theme_id
2. **Verify CSS generation**: Check if dynamic CSS includes theme
3. **Clear browser cache**: Force refresh to get latest CSS
4. **Check console errors**: Look for JavaScript/CSS errors

### Performance Issues

1. **Monitor CSS generation time**: Should be < 100ms
2. **Check database query performance**: Optimize JOINs if needed
3. **Verify caching**: Ensure CSS cache is working properly
4. **Monitor memory usage**: Check for memory leaks in theme cache

### Data Integrity Issues

1. **Run health checks**: Use built-in health check functions
2. **Validate foreign keys**: Ensure all theme references are valid
3. **Check for orphaned data**: Find unit types without themes
4. **Verify default theme**: Ensure default theme exists and is marked correctly

---

*This developer guide covers the complete architecture and implementation details of the Unit Type Theming System. For user-facing documentation, see the Theme Management User Guide.*