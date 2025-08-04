"""
Jinja2 template helper functions for theme-driven rendering
"""

import logging
from typing import Optional, Dict, Any
from app.models.unit import Unit
from app.models.unit_type_theme import UnitTypeTheme
from app.services.unit_type_theme import UnitTypeThemeService

logger = logging.getLogger(__name__)


def get_unit_theme_data(unit: Unit) -> UnitTypeTheme:
    """
    Get theme data for a unit with comprehensive fallback handling
    
    Args:
        unit: Unit instance with unit_type relationship
        
    Returns:
        UnitTypeTheme instance (never None, always returns a valid theme)
    """
    try:
        if not unit:
            logger.debug("No unit provided, returning default theme")
            return _get_safe_default_theme()
        
        is_dict = type(unit) is dict
        from app.services.unit_type import UnitTypeService

        if is_dict:
            # Check if unit has unit_type with theme
            if 'unit_type' in unit.keys():
                unit_type = unit['unit_type']
                if 'effective_theme' in unit_type.keys():
                    theme = unit_type['effective_theme']
                    if theme and _is_theme_valid(theme):
                        return theme
                    else:
                        logger.warning(f"Unit {unit.id} has invalid effective_theme, using fallback")
                
                # Try to get theme via theme_id
                if 'theme_id' in unit_type.keys():
                    theme_service = UnitTypeThemeService()
                    theme = theme_service.get_theme_with_fallback(unit_type['theme_id'])
                    if theme:
                        return theme
            
            # Fallback: get theme by unit_type_id if available
            if 'unit_type_id' in unit.keys():
                try:
                    unit_type_service = UnitTypeService()
                    unit_type = unit_type_service.get_by_id(unit['unit_type_id'])
                    if unit_type and hasattr(unit_type, 'effective_theme'):
                        theme = unit_type.effective_theme
                        if theme and _is_theme_valid(theme):
                            return theme
                except Exception as e:
                    logger.warning(f"Error getting unit_type for unit {unit.id}: {e}")
        else:
            # Check if unit has unit_type with theme
            if hasattr(unit, 'unit_type') and unit.unit_type:
                if hasattr(unit.unit_type, 'effective_theme'):
                    theme = unit.unit_type.effective_theme
                    if theme and _is_theme_valid(theme):
                        return theme
                    else:
                        logger.warning(f"Unit {unit.id} has invalid effective_theme, using fallback")
                
                # Try to get theme via theme_id
                if hasattr(unit.unit_type, 'theme_id') and unit.unit_type.theme_id:
                    theme_service = UnitTypeThemeService()
                    theme = theme_service.get_theme_with_fallback(unit.unit_type.theme_id)
                    if theme:
                        return theme
            
            # Fallback: get theme by unit_type_id if available
            if hasattr(unit, 'unit_type_id') and unit.unit_type_id:
                try:
                    from app.services.unit_type import UnitTypeService
                    unit_type_service = UnitTypeService()
                    unit_type = unit_type_service.get_by_id(unit.unit_type_id)
                    if unit_type and hasattr(unit_type, 'effective_theme'):
                        theme = unit_type.effective_theme
                        if theme and _is_theme_valid(theme):
                            return theme
                except Exception as e:
                    logger.warning(f"Error getting unit_type for unit {unit.id}: {e}")
        
        # Final fallback: return default theme
        logger.debug(f"Using default theme fallback for unit {getattr(unit, 'id', 'unknown')}")
        return _get_safe_default_theme()
        
    except Exception as e:
        logger.error(f"Error getting theme data for unit: {e}")
        return _get_emergency_fallback_theme()


def render_unit_icon(unit: Unit, css_classes: str = "bi") -> str:
    """
    Render unit icon based on theme with error handling
    
    Args:
        unit: Unit instance
        css_classes: Additional CSS classes for the icon
        
    Returns:
        HTML string for the icon
    """
    try:
        theme = get_unit_theme_data(unit)
        theme = validate_and_repair_theme_in_template(theme)
        
        # Build CSS classes
        icon_classes = f"{css_classes} bi-{theme.icon_class}"
        
        return f'<i class="{icon_classes}" aria-hidden="true"></i>'
        
    except Exception as e:
        logger.error(f"Error rendering unit icon: {e}")
        return f'<i class="{css_classes} bi-diagram-2" aria-hidden="true"></i>'


def get_unit_css_classes(unit: Unit, base_classes: str = "unit-box") -> str:
    """
    Get CSS classes for unit based on theme with error handling
    
    Args:
        unit: Unit instance
        base_classes: Base CSS classes to include
        
    Returns:
        Space-separated CSS class string
    """
    try:
        theme = get_unit_theme_data(unit)
        theme = validate_and_repair_theme_in_template(theme)
        
        # Build class list
        classes = [base_classes]
        
        # Add theme-specific class
        theme_class = theme.generate_css_class_name()
        classes.append(theme_class)
        
        return " ".join(classes)
        
    except Exception as e:
        logger.error(f"Error getting unit CSS classes: {e}")
        return f"{base_classes} unit-fallback"


def get_unit_css_variables(unit: Unit) -> Dict[str, str]:
    """
    Generate inline CSS variables from theme data with error handling
    
    Args:
        unit: Unit instance
        
    Returns:
        Dictionary of CSS custom properties
    """
    try:
        theme = get_unit_theme_data(unit)
        theme = validate_and_repair_theme_in_template(theme)
        
        # Get theme CSS variables
        css_vars = theme.to_css_variables()
        
        # Add unit-specific variables for easier template usage
        unit_vars = {
            '--unit-primary': theme.primary_color,
            '--unit-secondary': theme.secondary_color,
            '--unit-text': theme.text_color,
            '--unit-border': theme.computed_border_color,
            '--unit-border-width': f"{theme.border_width}px",
            '--unit-hover-shadow': theme.computed_hover_shadow_color,
        }
        
        # Merge theme variables with unit-specific ones
        css_vars.update(unit_vars)
        
        return css_vars
        
    except Exception as e:
        logger.error(f"Error getting unit CSS variables: {e}")
        # Return fallback variables
        return {
            '--unit-primary': '#6c757d',
            '--unit-secondary': '#f8f9fa',
            '--unit-text': '#495057',
            '--unit-border': '#6c757d',
            '--unit-border-width': '2px',
            '--unit-hover-shadow': '#6c757d',
        }


def render_unit_css_variables(unit: Unit) -> str:
    """
    Render inline CSS variables as a style attribute value
    
    Args:
        unit: Unit instance
        
    Returns:
        CSS style attribute value string
    """
    css_vars = get_unit_css_variables(unit)
    
    # Convert to CSS style string
    style_parts = [f"{key}: {value}" for key, value in css_vars.items()]
    
    return "; ".join(style_parts)


def get_unit_theme_badge_text(unit: Unit) -> str:
    """
    Get theme-based badge text for unit with error handling
    
    Args:
        unit: Unit instance
        
    Returns:
        Display label from theme
    """
    try:
        theme = get_unit_theme_data(unit)
        theme = validate_and_repair_theme_in_template(theme)
        return theme.display_label
    except Exception as e:
        logger.error(f"Error getting unit theme badge text: {e}")
        return "Unità"


def get_unit_theme_emoji(unit: Unit) -> str:
    """
    Get theme-based emoji fallback for unit with error handling
    
    Args:
        unit: Unit instance
        
    Returns:
        Emoji fallback from theme
    """
    try:
        theme = get_unit_theme_data(unit)
        theme = validate_and_repair_theme_in_template(theme)
        return theme.emoji_fallback
    except Exception as e:
        logger.error(f"Error getting unit theme emoji: {e}")
        return "🏛️"


def get_unit_theme_colors(unit: Unit) -> Dict[str, str]:
    """
    Get theme color palette for unit
    
    Args:
        unit: Unit instance
        
    Returns:
        Dictionary with color values
    """
    theme = get_unit_theme_data(unit)
    
    return {
        'primary': theme.primary_color,
        'secondary': theme.secondary_color,
        'text': theme.text_color,
        'border': theme.computed_border_color,
        'hover_shadow': theme.computed_hover_shadow_color,
    }


def is_unit_theme_high_contrast(unit: Unit) -> bool:
    """
    Check if unit theme uses high contrast mode
    
    Args:
        unit: Unit instance
        
    Returns:
        True if high contrast mode is enabled
    """
    theme = get_unit_theme_data(unit)
    return theme.high_contrast_mode


def get_theme_css_class_by_id(theme_id: Optional[int]) -> str:
    """
    Get CSS class name by theme ID (for cases where we only have theme_id)
    
    Args:
        theme_id: Theme ID
        
    Returns:
        CSS class name
    """
    try:
        if not theme_id:
            # Return default theme class
            default_theme = _get_safe_default_theme()
            return default_theme.generate_css_class_name()
        
        theme_service = UnitTypeThemeService()
        theme = theme_service.get_theme_with_fallback(theme_id)
        
        if theme and _is_theme_valid(theme):
            return theme.generate_css_class_name()
        else:
            # Fallback to default theme
            logger.warning(f"Invalid theme {theme_id}, using default theme class")
            default_theme = _get_safe_default_theme()
            return default_theme.generate_css_class_name()
            
    except Exception as e:
        logger.error(f"Error getting CSS class for theme {theme_id}: {e}")
        return "unit-fallback"


def _get_safe_default_theme() -> UnitTypeTheme:
    """
    Get default theme with error handling
    
    Returns:
        Default UnitTypeTheme instance
    """
    try:
        theme_service = UnitTypeThemeService()
        return theme_service.get_default_theme()
    except Exception as e:
        logger.error(f"Error getting default theme: {e}")
        return _get_emergency_fallback_theme()


def _get_emergency_fallback_theme() -> UnitTypeTheme:
    """
    Get emergency fallback theme when all else fails
    
    Returns:
        Emergency fallback UnitTypeTheme instance
    """
    logger.warning("Using emergency fallback theme")
    return UnitTypeTheme(
        id=-1,
        name="Emergency Fallback",
        description="Tema di emergenza",
        icon_class="diagram-2",
        emoji_fallback="🏛️",
        primary_color="#6c757d",
        secondary_color="#f8f9fa",
        text_color="#495057",
        border_width=2,
        border_style="solid",
        css_class_suffix="emergency",
        display_label="Unità",
        display_label_plural="Unità",
        is_default=True,
        is_active=True
    )


def _is_theme_valid(theme: Optional[UnitTypeTheme]) -> bool:
    """
    Check if theme is valid and has required data
    
    Args:
        theme: Theme to validate
        
    Returns:
        True if theme is valid
    """
    if not theme:
        return False
    
    try:
        # Check required fields
        required_fields = [
            'name', 'icon_class', 'emoji_fallback', 'primary_color',
            'secondary_color', 'text_color', 'css_class_suffix', 'display_label'
        ]
        
        for field in required_fields:
            value = getattr(theme, field, None)
            if not value or (isinstance(value, str) and not value.strip()):
                logger.debug(f"Theme {theme.id} missing required field: {field}")
                return False
        
        # Basic validation of critical fields
        if not theme._is_valid_color(theme.primary_color):
            logger.debug(f"Theme {theme.id} has invalid primary color: {theme.primary_color}")
            return False
        
        if not theme._is_valid_icon_class(theme.icon_class):
            logger.debug(f"Theme {theme.id} has invalid icon class: {theme.icon_class}")
            return False
        
        return True
        
    except Exception as e:
        logger.warning(f"Error validating theme {getattr(theme, 'id', 'unknown')}: {e}")
        return False


def validate_and_repair_theme_in_template(theme: UnitTypeTheme) -> UnitTypeTheme:
    """
    Validate theme and attempt basic repairs for template rendering
    
    Args:
        theme: Theme to validate and repair
        
    Returns:
        Valid theme (repaired if necessary)
    """
    try:
        if not theme:
            return _get_emergency_fallback_theme()
        
        # Create a copy to avoid modifying the original
        repaired_theme = UnitTypeTheme(
            id=theme.id,
            name=theme.name or "Unnamed Theme",
            description=theme.description,
            icon_class=theme.icon_class if theme._is_valid_icon_class(theme.icon_class) else "diagram-2",
            emoji_fallback=theme.emoji_fallback if theme.emoji_fallback and theme._is_valid_emoji(theme.emoji_fallback) else "🏛️",
            primary_color=theme.primary_color if theme._is_valid_color(theme.primary_color) else "#0dcaf0",
            secondary_color=theme.secondary_color if theme._is_valid_color(theme.secondary_color) else "#f0fdff",
            text_color=theme.text_color if theme._is_valid_color(theme.text_color) else "#0dcaf0",
            border_color=theme.border_color if theme.border_color and theme._is_valid_color(theme.border_color) else None,
            border_width=theme.border_width if 0 <= theme.border_width <= 20 else 2,
            border_style=theme.border_style if theme.border_style in ["solid", "dashed", "dotted", "double"] else "solid",
            background_gradient=theme.background_gradient if theme.background_gradient and theme._is_valid_css_gradient(theme.background_gradient) else None,
            css_class_suffix=theme.css_class_suffix if theme._is_valid_css_class_suffix(theme.css_class_suffix) else "repaired",
            hover_shadow_color=theme.hover_shadow_color if theme.hover_shadow_color and theme._is_valid_color(theme.hover_shadow_color) else None,
            hover_shadow_intensity=theme.hover_shadow_intensity if 0 <= theme.hover_shadow_intensity <= 1 else 0.25,
            display_label=theme.display_label or "Unità",
            display_label_plural=theme.display_label_plural,
            high_contrast_mode=theme.high_contrast_mode,
            is_default=theme.is_default,
            is_active=theme.is_active,
            created_by=theme.created_by
        )
        
        return repaired_theme
        
    except Exception as e:
        logger.error(f"Error repairing theme for template: {e}")
        return _get_emergency_fallback_theme()


# Template helper functions registry
TEMPLATE_HELPERS = {
    'get_unit_theme_data': get_unit_theme_data,
    'render_unit_icon': render_unit_icon,
    'get_unit_css_classes': get_unit_css_classes,
    'get_unit_css_variables': get_unit_css_variables,
    'render_unit_css_variables': render_unit_css_variables,
    'get_unit_theme_badge_text': get_unit_theme_badge_text,
    'get_unit_theme_emoji': get_unit_theme_emoji,
    'get_unit_theme_colors': get_unit_theme_colors,
    'is_unit_theme_high_contrast': is_unit_theme_high_contrast,
    'get_theme_css_class_by_id': get_theme_css_class_by_id,
    'validate_and_repair_theme_in_template': validate_and_repair_theme_in_template,
}