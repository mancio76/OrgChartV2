"""
Unit Type Theme service for theme management operations
"""

import logging
import time
import hashlib
from typing import List, Optional, Tuple, Dict, Any
from app.services.base import BaseService, ServiceException, ServiceValidationException, ServiceIntegrityException, ServiceNotFoundException
from app.models.unit_type_theme import UnitTypeTheme
from app.models.base import ValidationError

logger = logging.getLogger(__name__)


class CSSCache:
    """Simple in-memory cache for generated CSS with TTL support"""
    
    def __init__(self, ttl_seconds: int = 3600):  # Default 1 hour TTL
        self.cache = {}
        self.ttl = ttl_seconds
    
    def get(self, key: str) -> Optional[str]:
        """Get cached CSS if still valid"""
        if key in self.cache:
            css_content, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                logger.debug(f"CSS cache hit for key: {key}")
                return css_content
            else:
                # Cache expired, remove it
                del self.cache[key]
                logger.debug(f"CSS cache expired for key: {key}")
        return None
    
    def set(self, key: str, css_content: str) -> None:
        """Cache CSS content with current timestamp"""
        self.cache[key] = (css_content, time.time())
        logger.debug(f"CSS cached for key: {key} ({len(css_content)} chars)")
    
    def invalidate(self, key: str = None) -> None:
        """Invalidate specific key or entire cache"""
        if key:
            self.cache.pop(key, None)
            logger.debug(f"CSS cache invalidated for key: {key}")
        else:
            self.cache.clear()
            logger.debug("CSS cache completely invalidated")
    
    def get_cache_key(self, themes: List[UnitTypeTheme]) -> str:
        """Generate cache key based on theme data"""
        # Create hash based on theme IDs and their update timestamps
        theme_data = []
        for theme in themes:
            theme_data.append(f"{theme.id}:{theme.datetime_updated}")
        
        cache_input = "|".join(sorted(theme_data))
        return hashlib.md5(cache_input.encode()).hexdigest()


# Global CSS cache instance
_css_cache = CSSCache()


class UnitTypeThemeService(BaseService):
    """Service for managing unit type themes"""

    def __init__(self):
        super().__init__(UnitTypeTheme, "unit_type_themes")

    def get_list_query(self) -> str:
        """Get query for listing themes with usage statistics"""
        return """
        SELECT utt.*, 
               COUNT(ut.id) as usage_count
        FROM unit_type_themes utt
        LEFT JOIN unit_types ut ON utt.id = ut.theme_id
        GROUP BY utt.id, utt.name, utt.description, utt.icon_class, utt.emoji_fallback,
                 utt.primary_color, utt.secondary_color, utt.text_color, utt.border_color,
                 utt.border_width, utt.border_style, utt.background_gradient,
                 utt.css_class_suffix, utt.hover_shadow_color, utt.hover_shadow_intensity,
                 utt.display_label, utt.display_label_plural, utt.high_contrast_mode,
                 utt.is_default, utt.is_active, utt.created_by, utt.datetime_created, utt.datetime_updated
        ORDER BY utt.is_default DESC, utt.name
        """

    def get_by_id_query(self) -> str:
        """Get query for fetching theme by ID with usage statistics"""
        return """
        SELECT utt.*, 
               COUNT(ut.id) as usage_count
        FROM unit_type_themes utt
        LEFT JOIN unit_types ut ON utt.id = ut.theme_id
        WHERE utt.id = ?
        GROUP BY utt.id, utt.name, utt.description, utt.icon_class, utt.emoji_fallback,
                 utt.primary_color, utt.secondary_color, utt.text_color, utt.border_color,
                 utt.border_width, utt.border_style, utt.background_gradient,
                 utt.css_class_suffix, utt.hover_shadow_color, utt.hover_shadow_intensity,
                 utt.display_label, utt.display_label_plural, utt.high_contrast_mode,
                 utt.is_default, utt.is_active, utt.created_by, utt.datetime_created, utt.datetime_updated
        """

    def get_insert_query(self) -> str:
        """Get query for inserting theme"""
        return """
        INSERT INTO unit_type_themes (
            name, description, icon_class, emoji_fallback,
            primary_color, secondary_color, text_color, border_color,
            border_width, border_style, background_gradient,
            css_class_suffix, hover_shadow_color, hover_shadow_intensity,
            display_label, display_label_plural, high_contrast_mode,
            is_default, is_active, created_by,
            datetime_created, datetime_updated
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """

    def get_update_query(self) -> str:
        """Get query for updating theme"""
        return """
        UPDATE unit_type_themes 
        SET name = ?, description = ?, icon_class = ?, emoji_fallback = ?,
            primary_color = ?, secondary_color = ?, text_color = ?, border_color = ?,
            border_width = ?, border_style = ?, background_gradient = ?,
            css_class_suffix = ?, hover_shadow_color = ?, hover_shadow_intensity = ?,
            display_label = ?, display_label_plural = ?, high_contrast_mode = ?,
            is_default = ?, is_active = ?, created_by = ?,
            datetime_updated = CURRENT_TIMESTAMP
        WHERE id = ?
        """

    def get_delete_query(self) -> str:
        """Get query for deleting theme"""
        return "DELETE FROM unit_type_themes WHERE id = ?"

    def model_to_insert_params(self, theme: UnitTypeTheme) -> tuple:
        """Convert theme to parameters for insert query"""
        return (
            theme.name,
            theme.description,
            theme.icon_class,
            theme.emoji_fallback,
            theme.primary_color,
            theme.secondary_color,
            theme.text_color,
            theme.border_color,
            theme.border_width,
            theme.border_style,
            theme.background_gradient,
            theme.css_class_suffix,
            theme.hover_shadow_color,
            theme.hover_shadow_intensity,
            theme.display_label,
            theme.display_label_plural,
            theme.high_contrast_mode,
            theme.is_default,
            theme.is_active,
            theme.created_by
        )

    def model_to_update_params(self, theme: UnitTypeTheme) -> tuple:
        """Convert theme to parameters for update query"""
        return (
            theme.name,
            theme.description,
            theme.icon_class,
            theme.emoji_fallback,
            theme.primary_color,
            theme.secondary_color,
            theme.text_color,
            theme.border_color,
            theme.border_width,
            theme.border_style,
            theme.background_gradient,
            theme.css_class_suffix,
            theme.hover_shadow_color,
            theme.hover_shadow_intensity,
            theme.display_label,
            theme.display_label_plural,
            theme.high_contrast_mode,
            theme.is_default,
            theme.is_active,
            theme.created_by,
            theme.id
        )

    def get_searchable_fields(self) -> List[str]:
        """Get list of searchable fields for themes"""
        return ["name", "description", "display_label", "css_class_suffix"]

    def get_default_theme(self) -> UnitTypeTheme:
        """
        Get the default theme, creating one if none exists.
        
        Returns:
            Default UnitTypeTheme instance
            
        Raises:
            ServiceException: If unable to retrieve or create default theme
        """
        try:
            logger.debug("Retrieving default theme")
            
            # Try to get existing default theme
            query = """
            SELECT utt.*, 0 as usage_count
            FROM unit_type_themes utt
            WHERE utt.is_default = 1 AND utt.is_active = 1
            ORDER BY utt.datetime_created
            LIMIT 1
            """
            
            row = self.db_manager.fetch_one(query)
            if row:
                theme = UnitTypeTheme.from_sqlite_row(row)
                logger.debug(f"Found default theme: {theme.name} (ID: {theme.id})")
                return theme
            
            # No default theme exists, create one
            logger.info("No default theme found, creating default theme")
            default_theme = UnitTypeTheme(
                name="Default Theme",
                description="Sistema di tema predefinito per unità organizzative",
                icon_class="diagram-2",
                emoji_fallback="🏛️",
                primary_color="#0dcaf0",
                secondary_color="#f0fdff",
                text_color="#0dcaf0",
                border_width=2,
                border_style="solid",
                css_class_suffix="organizational",
                display_label="Unità Organizzativa",
                display_label_plural="Unità Organizzative",
                is_default=True,
                is_active=True
            )
            
            return self.create(default_theme)
            
        except Exception as e:
            logger.error(f"Error retrieving default theme: {e}")
            # Return a hardcoded fallback theme if all else fails
            return self._get_emergency_fallback_theme()
    
    def _get_emergency_fallback_theme(self) -> UnitTypeTheme:
        """
        Get emergency fallback theme when database operations fail.
        This theme is not persisted and serves as a last resort.
        
        Returns:
            Emergency fallback UnitTypeTheme instance
        """
        logger.warning("Using emergency fallback theme - database operations failed")
        return UnitTypeTheme(
            id=-1,  # Special ID to indicate fallback
            name="Emergency Fallback Theme",
            description="Tema di emergenza utilizzato quando il database non è disponibile",
            icon_class="diagram-2",
            emoji_fallback="🏛️",
            primary_color="#6c757d",  # Bootstrap secondary color
            secondary_color="#f8f9fa",  # Bootstrap light color
            text_color="#495057",     # Bootstrap dark color
            border_width=2,
            border_style="solid",
            css_class_suffix="fallback",
            display_label="Unità",
            display_label_plural="Unità",
            is_default=True,
            is_active=True
        )

    def get_themes_with_usage_stats(self) -> List[UnitTypeTheme]:
        """
        Get all themes with usage statistics.
        
        Returns:
            List of themes with usage_count populated
            
        Raises:
            ServiceException: If unable to retrieve themes
        """
        try:
            logger.debug("Retrieving themes with usage statistics")
            return self.get_all()
        except Exception as e:
            logger.error(f"Error retrieving themes with usage stats: {e}")
            raise ServiceException("Failed to retrieve themes with usage statistics") from e

    def can_delete_theme(self, theme_id: int) -> Tuple[bool, str]:
        """
        Check if theme can be deleted by verifying dependencies.
        
        Args:
            theme_id: ID of theme to check
            
        Returns:
            Tuple of (can_delete: bool, reason: str)
            
        Raises:
            ServiceException: If unable to check dependencies
        """
        try:
            logger.debug(f"Checking if theme {theme_id} can be deleted")
            
            # Check if theme exists
            theme = self.get_by_id(theme_id)
            if not theme:
                return False, "Tema non trovato"
            
            # Cannot delete default theme
            if theme.is_default:
                return False, "Impossibile eliminare il tema predefinito"
            
            # Check if any unit types are using this theme
            query = "SELECT COUNT(*) as count FROM unit_types WHERE theme_id = ?"
            row = self.db_manager.fetch_one(query, (theme_id,))
            usage_count = row['count'] if row else 0
            
            if usage_count > 0:
                return False, f"Impossibile eliminare il tema: {usage_count} tipi di unità stanno utilizzando questo tema"
            
            logger.debug(f"Theme {theme_id} can be deleted")
            return True, ""
            
        except Exception as e:
            logger.error(f"Error checking if theme {theme_id} can be deleted: {e}")
            return False, "Errore durante la verifica delle dipendenze del tema"

    def clone_theme(self, theme_id: int, new_name: str, created_by: Optional[str] = None) -> UnitTypeTheme:
        """
        Create a copy of an existing theme with a new name.
        
        Args:
            theme_id: ID of theme to clone
            new_name: Name for the new theme
            created_by: User creating the clone
            
        Returns:
            Newly created theme instance
            
        Raises:
            ServiceNotFoundException: If source theme doesn't exist
            ServiceValidationException: If new name is invalid or already exists
            ServiceException: If cloning operation fails
        """
        try:
            logger.debug(f"Cloning theme {theme_id} with new name '{new_name}'")
            
            # Get source theme
            source_theme = self.get_by_id(theme_id)
            if not source_theme:
                raise ServiceNotFoundException(f"Tema sorgente con ID {theme_id} non trovato")
            
            # Validate new name
            if not new_name or not new_name.strip():
                raise ServiceValidationException("Il nome del nuovo tema è obbligatorio")
            
            # Check if name already exists
            existing = self.get_by_field("utt.name", new_name.strip())
            if existing:
                raise ServiceValidationException(f"Un tema con il nome '{new_name}' esiste già")
            
            # Create clone with new name and reset metadata
            cloned_theme = UnitTypeTheme(
                name=new_name.strip(),
                description=f"Copia di {source_theme.name}" + (f" - {source_theme.description}" if source_theme.description else ""),
                icon_class=source_theme.icon_class,
                emoji_fallback=source_theme.emoji_fallback,
                primary_color=source_theme.primary_color,
                secondary_color=source_theme.secondary_color,
                text_color=source_theme.text_color,
                border_color=source_theme.border_color,
                border_width=source_theme.border_width,
                border_style=source_theme.border_style,
                background_gradient=source_theme.background_gradient,
                css_class_suffix=f"{source_theme.css_class_suffix}-copy",
                hover_shadow_color=source_theme.hover_shadow_color,
                hover_shadow_intensity=source_theme.hover_shadow_intensity,
                display_label=source_theme.display_label,
                display_label_plural=source_theme.display_label_plural,
                high_contrast_mode=source_theme.high_contrast_mode,
                is_default=False,  # Clones are never default
                is_active=True,
                created_by=created_by
            )
            
            # Create the cloned theme
            created_theme = self.create(cloned_theme)
            logger.info(f"Successfully cloned theme {theme_id} to new theme {created_theme.id} with name '{new_name}'")
            
            return created_theme
            
        except (ServiceNotFoundException, ServiceValidationException):
            raise
        except Exception as e:
            logger.error(f"Error cloning theme {theme_id}: {e}")
            raise ServiceException(f"Failed to clone theme {theme_id}") from e

    def generate_dynamic_css(self, use_cache: bool = True, minify: bool = False) -> str:
        """
        Generate comprehensive CSS for all active themes with template system and caching.
        
        Args:
            use_cache: Whether to use caching mechanism
            minify: Whether to minify the generated CSS for production
        
        Returns:
            Complete CSS string for all active themes
            
        Raises:
            ServiceException: If CSS generation fails
        """
        try:
            start_time = time.time()
            logger.debug("Generating dynamic CSS for all active themes")
            
            # Get all active themes with optimized query
            query = """
            SELECT utt.*, 0 as usage_count
            FROM unit_type_themes utt
            WHERE utt.is_active = 1
            ORDER BY utt.is_default DESC, utt.name
            """
            
            rows = self.db_manager.fetch_all(query)
            themes = [UnitTypeTheme.from_sqlite_row(row) for row in rows]
            
            if not themes:
                logger.warning("No active themes found for CSS generation")
                return self._generate_fallback_css()
            
            # Check cache first if enabled
            cache_key = None
            if use_cache:
                cache_key = _css_cache.get_cache_key(themes) + ("_min" if minify else "")
                cached_css = _css_cache.get(cache_key)
                if cached_css:
                    logger.debug(f"Returning cached CSS ({len(cached_css)} chars)")
                    return cached_css
            
            # Generate CSS with performance tracking
            css_parts = []
            
            # CSS Header
            css_parts.extend(self._generate_css_header())
            
            # CSS Custom Properties (CSS Variables)
            css_parts.extend(self._generate_css_variables(themes))
            
            # Base theme classes
            css_parts.extend(self._generate_base_theme_classes())
            
            # Theme-specific CSS rules (optimized generation)
            for theme in themes:
                if not minify:
                    css_parts.append(f"/* Theme: {theme.name} (ID: {theme.id}) */")
                css_parts.append(theme.generate_css_rules())
                if not minify:
                    css_parts.append("")
            
            # Utility and responsive classes
            css_parts.extend(self._generate_utility_classes())
            
            # Accessibility enhancements
            css_parts.extend(self._generate_accessibility_css())
            
            # Print styles
            css_parts.extend(self._generate_print_styles())
            
            generated_css = "\n".join(css_parts)
            
            # Minify CSS if requested
            if minify:
                generated_css = self._minify_css(generated_css)
            
            generation_time = time.time() - start_time
            logger.debug(f"Generated {len(generated_css)} characters of CSS for {len(themes)} themes in {generation_time:.3f}s")
            
            # Cache the result if caching is enabled
            if use_cache and cache_key:
                _css_cache.set(cache_key, generated_css)
            
            return generated_css
            
        except Exception as e:
            logger.error(f"Error generating dynamic CSS: {e}")
            raise ServiceException("Failed to generate dynamic CSS") from e
    
    def _minify_css(self, css: str) -> str:
        """
        Basic CSS minification for performance optimization.
        
        Args:
            css: CSS string to minify
            
        Returns:
            Minified CSS string
        """
        try:
            # Remove comments
            import re
            css = re.sub(r'/\*.*?\*/', '', css, flags=re.DOTALL)
            
            # Remove extra whitespace
            css = re.sub(r'\s+', ' ', css)
            
            # Remove whitespace around specific characters
            css = re.sub(r'\s*([{}:;,>+~])\s*', r'\1', css)
            
            # Remove trailing semicolons before closing braces
            css = re.sub(r';\s*}', '}', css)
            
            # Remove leading/trailing whitespace
            css = css.strip()
            
            return css
            
        except Exception as e:
            logger.warning(f"CSS minification failed: {e}")
            return css  # Return original CSS if minification fails
    
    def get_lazy_theme_data(self, theme_ids: List[int]) -> Dict[int, Dict[str, Any]]:
        """
        Get minimal theme data for lazy loading in large orgcharts.
        
        Args:
            theme_ids: List of theme IDs to load
            
        Returns:
            Dictionary mapping theme ID to minimal theme data
            
        Raises:
            ServiceException: If unable to load theme data
        """
        try:
            if not theme_ids:
                return {}
            
            logger.debug(f"Loading lazy theme data for {len(theme_ids)} themes")
            
            # Create placeholders for IN clause
            placeholders = ','.join(['?' for _ in theme_ids])
            
            # Optimized query for minimal data needed for rendering
            query = f"""
            SELECT id, name, icon_class, emoji_fallback, primary_color, 
                   secondary_color, text_color, border_color, border_width,
                   css_class_suffix, display_label, high_contrast_mode
            FROM unit_type_themes
            WHERE id IN ({placeholders}) AND is_active = 1
            """
            
            rows = self.db_manager.fetch_all(query, theme_ids)
            
            result = {}
            for row in rows:
                theme_data = dict(row)
                
                # Add computed properties for rendering
                theme_data['computed_border_color'] = theme_data['border_color'] or theme_data['primary_color']
                theme_data['css_class_name'] = f"unit-{theme_data['css_class_suffix']}"
                
                result[theme_data['id']] = theme_data
            
            logger.debug(f"Loaded lazy theme data for {len(result)} themes")
            return result
            
        except Exception as e:
            logger.error(f"Error loading lazy theme data: {e}")
            raise ServiceException("Failed to load lazy theme data") from e
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics for the theme system.
        
        Returns:
            Dictionary containing performance metrics
        """
        try:
            metrics = {
                'cache_stats': {
                    'cache_size': len(_css_cache.cache),
                    'cache_ttl': _css_cache.ttl,
                    'cache_hits': 0,  # Would need to track this
                    'cache_misses': 0  # Would need to track this
                },
                'theme_stats': {},
                'css_generation': {},
                'database_stats': {}
            }
            
            # Get theme statistics
            query = """
            SELECT 
                COUNT(*) as total_themes,
                COUNT(CASE WHEN is_active = 1 THEN 1 END) as active_themes,
                COUNT(CASE WHEN high_contrast_mode = 1 THEN 1 END) as high_contrast_themes,
                AVG(border_width) as avg_border_width,
                COUNT(CASE WHEN background_gradient IS NOT NULL THEN 1 END) as themes_with_gradients
            FROM unit_type_themes
            """
            
            row = self.db_manager.fetch_one(query)
            if row:
                metrics['theme_stats'] = dict(row)
            
            # Test CSS generation performance
            start_time = time.time()
            css = self.generate_dynamic_css(use_cache=False)
            generation_time = time.time() - start_time
            
            metrics['css_generation'] = {
                'generation_time_seconds': round(generation_time, 3),
                'css_size_bytes': len(css.encode('utf-8')),
                'css_lines': len(css.split('\n')),
                'estimated_gzip_size': len(css.encode('utf-8')) // 3  # Rough estimate
            }
            
            # Database performance stats
            query = "SELECT COUNT(*) as theme_usage_count FROM unit_types WHERE theme_id IS NOT NULL"
            row = self.db_manager.fetch_one(query)
            if row:
                metrics['database_stats']['theme_usage_count'] = row['theme_usage_count']
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting performance metrics: {e}")
            return {'error': 'Failed to get performance metrics'}
    
    def _generate_css_header(self) -> List[str]:
        """Generate CSS file header with metadata"""
        from datetime import datetime
        
        return [
            "/*",
            " * Dynamic Unit Type Theme CSS",
            " * Auto-generated by Organigramma Web App",
            f" * Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            " * Do not edit manually - changes will be overwritten",
            " */",
            ""
        ]
    
    def _generate_css_variables(self, themes: List[UnitTypeTheme]) -> List[str]:
        """Generate CSS custom properties for all themes"""
        css_parts = []
        css_parts.append("/* CSS Custom Properties for Theme System */")
        css_parts.append(":root {")
        
        # Global theme system variables
        css_parts.append("  /* Global theme system settings */")
        css_parts.append("  --theme-transition-duration: 0.3s;")
        css_parts.append("  --theme-hover-transform: translateY(-2px);")
        css_parts.append("  --theme-border-radius: 0.375rem;")
        css_parts.append("  --theme-box-shadow-base: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);")
        css_parts.append("")
        
        # Theme-specific variables
        for theme in themes:
            css_parts.append(f"  /* Theme: {theme.name} */")
            css_vars = theme.to_css_variables()
            for var_name, var_value in css_vars.items():
                css_parts.append(f"  {var_name}: {var_value};")
            css_parts.append("")
        
        css_parts.append("}")
        css_parts.append("")
        
        return css_parts
    
    def create(self, theme: UnitTypeTheme) -> UnitTypeTheme:
        """
        Create a new theme with enhanced validation.
        
        Args:
            theme: UnitTypeTheme instance to create
            
        Returns:
            Created UnitTypeTheme instance
            
        Raises:
            ServiceValidationException: If validation fails
            ServiceException: If creation fails
        """
        try:
            logger.debug(f"Creating new theme: {theme.name}")
            
            # Validate theme data
            validation_errors = theme.validate()
            if validation_errors:
                raise ServiceValidationException("Errori di validazione del tema", validation_errors)
            
            # Check for name uniqueness
            existing_theme = self.get_by_field("name", theme.name.strip())
            if existing_theme:
                raise ServiceValidationException("Nome tema già esistente", [
                    ValidationError("name", f"Un tema con il nome '{theme.name}' esiste già")
                ])
            
            # Check for CSS class suffix uniqueness
            existing_suffix = self.get_by_field("css_class_suffix", theme.css_class_suffix.strip())
            if existing_suffix:
                raise ServiceValidationException("Suffisso classe CSS già esistente", [
                    ValidationError("css_class_suffix", f"Un tema con il suffisso '{theme.css_class_suffix}' esiste già")
                ])
            
            # If this is marked as default, ensure no other default exists
            if theme.is_default:
                self._ensure_single_default_theme(exclude_id=None)
            
            # Create the theme
            created_theme = super().create(theme)
            
            # Invalidate CSS cache
            _css_cache.invalidate()
            
            logger.info(f"Successfully created theme: {created_theme.name} (ID: {created_theme.id})")
            return created_theme
            
        except ServiceValidationException:
            raise
        except Exception as e:
            logger.error(f"Error creating theme: {e}")
            raise ServiceException(f"Failed to create theme: {str(e)}") from e
    
    def update(self, theme: UnitTypeTheme) -> UnitTypeTheme:
        """
        Update an existing theme with enhanced validation.
        
        Args:
            theme: UnitTypeTheme instance to update
            
        Returns:
            Updated UnitTypeTheme instance
            
        Raises:
            ServiceValidationException: If validation fails
            ServiceNotFoundException: If theme doesn't exist
            ServiceException: If update fails
        """
        try:
            logger.debug(f"Updating theme: {theme.name} (ID: {theme.id})")
            
            # Ensure theme exists
            if not theme.id or not self.get_by_id(theme.id):
                raise ServiceNotFoundException(f"Tema con ID {theme.id} non trovato")
            
            # Validate theme data
            validation_errors = theme.validate()
            if validation_errors:
                raise ServiceValidationException("Errori di validazione del tema", validation_errors)
            
            # Check for name uniqueness (excluding current theme)
            existing_theme = self.get_by_field("name", theme.name.strip())
            if existing_theme and existing_theme.id != theme.id:
                raise ServiceValidationException("Nome tema già esistente", [
                    ValidationError("name", f"Un altro tema con il nome '{theme.name}' esiste già")
                ])
            
            # Check for CSS class suffix uniqueness (excluding current theme)
            existing_suffix = self.get_by_field("css_class_suffix", theme.css_class_suffix.strip())
            if existing_suffix and existing_suffix.id != theme.id:
                raise ServiceValidationException("Suffisso classe CSS già esistente", [
                    ValidationError("css_class_suffix", f"Un altro tema con il suffisso '{theme.css_class_suffix}' esiste già")
                ])
            
            # If this is marked as default, ensure no other default exists
            if theme.is_default:
                self._ensure_single_default_theme(exclude_id=theme.id)
            
            # Update the theme
            updated_theme = super().update(theme)
            
            # Invalidate CSS cache for performance
            self.invalidate_css_cache()
            
            logger.info(f"Successfully updated theme: {updated_theme.name} (ID: {updated_theme.id})")
            return updated_theme
            
        except (ServiceValidationException, ServiceNotFoundException):
            raise
        except Exception as e:
            logger.error(f"Error updating theme {theme.id}: {e}")
            raise ServiceException(f"Failed to update theme: {str(e)}") from e
    
    def delete(self, theme_id: int) -> bool:
        """
        Delete a theme with enhanced validation and cache invalidation.
        
        Args:
            theme_id: ID of theme to delete
            
        Returns:
            True if deletion was successful
            
        Raises:
            ServiceValidationException: If theme cannot be deleted
            ServiceNotFoundException: If theme doesn't exist
            ServiceException: If deletion fails
        """
        try:
            logger.debug(f"Deleting theme: {theme_id}")
            
            # Check if theme can be deleted
            can_delete, reason = self.can_delete_theme(theme_id)
            if not can_delete:
                raise ServiceValidationException(reason)
            
            # Delete the theme
            result = super().delete(theme_id)
            
            # Invalidate CSS cache for performance
            self.invalidate_css_cache()
            
            logger.info(f"Successfully deleted theme: {theme_id}")
            return result
            
        except (ServiceValidationException, ServiceNotFoundException):
            raise
        except Exception as e:
            logger.error(f"Error deleting theme {theme_id}: {e}")
            raise ServiceException(f"Failed to delete theme: {str(e)}") from e
    
    def invalidate_css_cache(self, specific_key: Optional[str] = None) -> None:
        """
        Invalidate CSS cache for performance optimization.
        
        Args:
            specific_key: Specific cache key to invalidate, or None for all
        """
        try:
            _css_cache.invalidate(specific_key)
            logger.debug(f"CSS cache invalidated" + (f" for key: {specific_key}" if specific_key else " (all)"))
        except Exception as e:
            logger.warning(f"Error invalidating CSS cache: {e}")
    
    def preload_themes_for_orgchart(self, unit_type_ids: List[int]) -> Dict[int, Dict[str, Any]]:
        """
        Preload theme data for orgchart rendering to improve performance.
        
        Args:
            unit_type_ids: List of unit type IDs that will be rendered
            
        Returns:
            Dictionary mapping unit_type_id to theme data
            
        Raises:
            ServiceException: If unable to preload theme data
        """
        try:
            if not unit_type_ids:
                return {}
            
            logger.debug(f"Preloading themes for {len(unit_type_ids)} unit types")
            
            # Create placeholders for IN clause
            placeholders = ','.join(['?' for _ in unit_type_ids])
            
            # Query to get theme data for all unit types in one go
            query = f"""
            SELECT ut.id as unit_type_id,
                   utt.id as theme_id, utt.name as theme_name,
                   utt.icon_class, utt.emoji_fallback, utt.primary_color,
                   utt.secondary_color, utt.text_color, utt.border_color,
                   utt.border_width, utt.css_class_suffix, utt.display_label,
                   utt.high_contrast_mode
            FROM unit_types ut
            LEFT JOIN unit_type_themes utt ON ut.theme_id = utt.id
            WHERE ut.id IN ({placeholders})
            """
            
            rows = self.db_manager.fetch_all(query, unit_type_ids)
            
            result = {}
            default_theme = None
            
            for row in rows:
                unit_type_id = row['unit_type_id']
                
                if row['theme_id']:
                    # Unit type has a theme
                    theme_data = {
                        'id': row['theme_id'],
                        'name': row['theme_name'],
                        'icon_class': row['icon_class'],
                        'emoji_fallback': row['emoji_fallback'],
                        'primary_color': row['primary_color'],
                        'secondary_color': row['secondary_color'],
                        'text_color': row['text_color'],
                        'border_color': row['border_color'],
                        'border_width': row['border_width'],
                        'css_class_suffix': row['css_class_suffix'],
                        'display_label': row['display_label'],
                        'high_contrast_mode': bool(row['high_contrast_mode']),
                        'computed_border_color': row['border_color'] or row['primary_color'],
                        'css_class_name': f"unit-{row['css_class_suffix']}"
                    }
                else:
                    # Unit type has no theme, use default
                    if not default_theme:
                        default_theme_obj = self.get_default_theme()
                        default_theme = {
                            'id': default_theme_obj.id,
                            'name': default_theme_obj.name,
                            'icon_class': default_theme_obj.icon_class,
                            'emoji_fallback': default_theme_obj.emoji_fallback,
                            'primary_color': default_theme_obj.primary_color,
                            'secondary_color': default_theme_obj.secondary_color,
                            'text_color': default_theme_obj.text_color,
                            'border_color': default_theme_obj.border_color,
                            'border_width': default_theme_obj.border_width,
                            'css_class_suffix': default_theme_obj.css_class_suffix,
                            'display_label': default_theme_obj.display_label,
                            'high_contrast_mode': default_theme_obj.high_contrast_mode,
                            'computed_border_color': default_theme_obj.computed_border_color,
                            'css_class_name': default_theme_obj.generate_css_class_name()
                        }
                    theme_data = default_theme
                
                result[unit_type_id] = theme_data
            
            logger.debug(f"Preloaded themes for {len(result)} unit types")
            return result
            
        except Exception as e:
            logger.error(f"Error preloading themes for orgchart: {e}")
            raise ServiceException("Failed to preload themes for orgchart") from e
    
    def _ensure_single_default_theme(self, exclude_id: Optional[int] = None):
        """
        Ensure only one theme is marked as default.
        
        Args:
            exclude_id: Theme ID to exclude from the check (for updates)
        """
        try:
            # Find other default themes
            query = "SELECT id FROM unit_type_themes WHERE is_default = 1"
            params = []
            
            if exclude_id:
                query += " AND id != ?"
                params.append(exclude_id)
            
            rows = self.db_manager.fetch_all(query, params)
            
            # Unmark other default themes
            for row in rows:
                update_query = "UPDATE unit_type_themes SET is_default = 0 WHERE id = ?"
                self.db_manager.execute(update_query, (row['id'],))
                logger.debug(f"Unmarked theme {row['id']} as default")
                
        except Exception as e:
            logger.error(f"Error ensuring single default theme: {e}")
            # Don't raise exception here as it's a cleanup operation
    
    def _generate_base_theme_classes(self) -> List[str]:
        """Generate base CSS classes for theme system"""
        return [
            "/* Base Theme Classes */",
            ".unit-themed {",
            "  position: relative;",
            "  border-radius: var(--theme-border-radius);",
            "  transition: all var(--theme-transition-duration) ease;",
            "  box-shadow: var(--theme-box-shadow-base);",
            "}",
            "",
            ".unit-themed:hover {",
            "  transform: var(--theme-hover-transform);",
            "  box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);",
            "}",
            "",
            ".unit-box {",
            "  padding: 1rem;",
            "  margin: 0.5rem;",
            "  border-radius: var(--theme-border-radius);",
            "  position: relative;",
            "  overflow: hidden;",
            "}",
            "",
            ".unit-box::before {",
            "  content: '';",
            "  position: absolute;",
            "  top: 0;",
            "  left: 0;",
            "  right: 0;",
            "  height: 3px;",
            "  background: var(--unit-primary, #0dcaf0);",
            "  opacity: 0;",
            "  transition: opacity var(--theme-transition-duration) ease;",
            "}",
            "",
            ".unit-box:hover::before {",
            "  opacity: 1;",
            "}",
            ""
        ]
    
    def _generate_utility_classes(self) -> List[str]:
        """Generate utility classes for theme system"""
        return [
            "/* Theme Utility Classes */",
            ".theme-primary-bg {",
            "  background-color: var(--unit-primary) !important;",
            "  color: white !important;",
            "}",
            "",
            ".theme-secondary-bg {",
            "  background-color: var(--unit-secondary) !important;",
            "}",
            "",
            ".theme-primary-text {",
            "  color: var(--unit-primary) !important;",
            "}",
            "",
            ".theme-primary-border {",
            "  border-color: var(--unit-primary) !important;",
            "}",
            "",
            "/* Responsive adjustments */",
            "@media (max-width: 768px) {",
            "  .unit-box {",
            "    margin: 0.25rem;",
            "    padding: 0.75rem;",
            "  }",
            "  ",
            "  .unit-themed:hover {",
            "    transform: none; /* Disable hover transform on mobile */",
            "  }",
            "}",
            "",
            "/* Animation classes */",
            ".theme-fade-in {",
            "  animation: themesFadeIn 0.5s ease-in-out;",
            "}",
            "",
            "@keyframes themesFadeIn {",
            "  from {",
            "    opacity: 0;",
            "    transform: translateY(10px);",
            "  }",
            "  to {",
            "    opacity: 1;",
            "    transform: translateY(0);",
            "  }",
            "}",
            ""
        ]
    
    def _generate_accessibility_css(self) -> List[str]:
        """Generate comprehensive accessibility-focused CSS rules"""
        return [
            "/* Accessibility Enhancements */",
            ".unit-themed,",
            ".unit-box {",
            "  /* Ensure minimum touch target size (WCAG 2.1 AA) */",
            "  min-height: 44px;",
            "  min-width: 44px;",
            "}",
            "",
            "/* Enhanced focus indicators for keyboard navigation */",
            ".unit-themed:focus,",
            ".unit-box:focus,",
            ".unit-themed:focus-within,",
            ".unit-box:focus-within {",
            "  outline: 3px solid #005fcc;",
            "  outline-offset: 2px;",
            "  box-shadow: 0 0 0 1px #ffffff, 0 0 0 4px #005fcc;",
            "  z-index: 10;",
            "  position: relative;",
            "}",
            "",
            "/* Reduced motion support */",
            "@media (prefers-reduced-motion: reduce) {",
            "  .unit-themed,",
            "  .unit-box,",
            "  .unit-box::before {",
            "    transition: none !important;",
            "    animation: none !important;",
            "  }",
            "  ",
            "  .unit-themed:hover,",
            "  .unit-box:hover {",
            "    transform: none !important;",
            "  }",
            "  ",
            "  .theme-fade-in {",
            "    animation: none !important;",
            "  }",
            "}",
            "",
            "/* High contrast mode support */",
            "@media (prefers-contrast: high) {",
            "  .unit-themed,",
            "  .unit-box {",
            "    border-width: 3px !important;",
            "    border-style: solid !important;",
            "    background: #ffffff !important;",
            "    color: #000000 !important;",
            "    border-color: #000000 !important;",
            "  }",
            "  ",
            "  .unit-themed .unit-name,",
            "  .unit-box .unit-name {",
            "    color: #000000 !important;",
            "    font-weight: 700 !important;",
            "  }",
            "  ",
            "  .unit-themed .badge,",
            "  .unit-box .badge {",
            "    background-color: #000000 !important;",
            "    color: #ffffff !important;",
            "    border: 2px solid #000000 !important;",
            "  }",
            "  ",
            "  .unit-themed .bi,",
            "  .unit-box .bi {",
            "    color: #000000 !important;",
            "  }",
            "}",
            "",
            "/* Color scheme preference support */",
            "@media (prefers-color-scheme: dark) {",
            "  .unit-themed,",
            "  .unit-box {",
            "    box-shadow: 0 0.125rem 0.25rem rgba(255, 255, 255, 0.075);",
            "  }",
            "}",
            "",
            "/* Screen reader and assistive technology support */",
            ".sr-only {",
            "  position: absolute !important;",
            "  width: 1px !important;",
            "  height: 1px !important;",
            "  padding: 0 !important;",
            "  margin: -1px !important;",
            "  overflow: hidden !important;",
            "  clip: rect(0, 0, 0, 0) !important;",
            "  white-space: nowrap !important;",
            "  border: 0 !important;",
            "}",
            "",
            ".sr-only-focusable:focus {",
            "  position: static !important;",
            "  width: auto !important;",
            "  height: auto !important;",
            "  padding: inherit !important;",
            "  margin: inherit !important;",
            "  overflow: visible !important;",
            "  clip: auto !important;",
            "  white-space: inherit !important;",
            "}",
            "",
            "/* Skip links for keyboard navigation */",
            ".skip-link {",
            "  position: absolute;",
            "  top: -40px;",
            "  left: 6px;",
            "  background: #000000;",
            "  color: #ffffff;",
            "  padding: 8px;",
            "  text-decoration: none;",
            "  border-radius: 0 0 4px 4px;",
            "  z-index: 1000;",
            "}",
            "",
            ".skip-link:focus {",
            "  top: 0;",
            "}",
            "",
            "/* High contrast mode toggle support */",
            "body.high-contrast .unit-themed,",
            "body.high-contrast .unit-box {",
            "  border-width: 3px !important;",
            "  background: #ffffff !important;",
            "  color: #000000 !important;",
            "  border-color: #000000 !important;",
            "}",
            "",
            "body.high-contrast .unit-themed .unit-name,",
            "body.high-contrast .unit-box .unit-name {",
            "  color: #000000 !important;",
            "  font-weight: 700 !important;",
            "}",
            "",
            "body.high-contrast .unit-themed .badge,",
            "body.high-contrast .unit-box .badge {",
            "  background-color: #000000 !important;",
            "  color: #ffffff !important;",
            "  border: 2px solid #000000 !important;",
            "}",
            ""
        ]
    
    def _generate_print_styles(self) -> List[str]:
        """Generate print-specific CSS"""
        return [
            "/* Print Styles */",
            "@media print {",
            "  .unit-themed,",
            "  .unit-box {",
            "    box-shadow: none !important;",
            "    transform: none !important;",
            "    transition: none !important;",
            "    background: white !important;",
            "    border: 1px solid black !important;",
            "  }",
            "  ",
            "  .unit-box::before {",
            "    display: none !important;",
            "  }",
            "  ",
            "  .theme-primary-bg {",
            "    background: white !important;",
            "    color: black !important;",
            "    border: 1px solid black !important;",
            "  }",
            "}",
            ""
        ]
    
    def _generate_fallback_css(self) -> str:
        """Generate fallback CSS when no themes are available"""
        return """/* Fallback CSS - No active themes found */
:root {
  --fallback-primary: #0dcaf0;
  --fallback-secondary: #f0fdff;
  --fallback-text: #0dcaf0;
}

.unit-themed,
.unit-organizational {
  border: 2px solid var(--fallback-primary);
  background: linear-gradient(135deg, #ffffff 0%, var(--fallback-secondary) 100%);
  transition: all 0.3s ease;
}

.unit-themed:hover,
.unit-organizational:hover {
  box-shadow: 0 1rem 2rem rgba(13, 202, 240, 0.25);
  transform: translateY(-2px);
}

.unit-themed .unit-name,
.unit-organizational .unit-name {
  color: var(--fallback-text);
}

.unit-themed .badge,
.unit-organizational .badge {
  background-color: var(--fallback-primary) !important;
}
"""

    def get_theme_usage_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive theme usage statistics.
        
        Returns:
            Dictionary with theme usage statistics
            
        Raises:
            ServiceException: If unable to retrieve statistics
        """
        try:
            logger.debug("Retrieving theme usage statistics")
            
            # Get theme usage counts
            query = """
            SELECT utt.id, utt.name, utt.is_default, utt.is_active,
                   COUNT(ut.id) as usage_count
            FROM unit_type_themes utt
            LEFT JOIN unit_types ut ON utt.id = ut.theme_id
            GROUP BY utt.id, utt.name, utt.is_default, utt.is_active
            ORDER BY usage_count DESC, utt.name
            """
            
            rows = self.db_manager.fetch_all(query)
            
            theme_stats = []
            total_themes = 0
            active_themes = 0
            total_usage = 0
            default_theme_usage = 0
            
            for row in rows:
                usage_count = row['usage_count']
                is_active = bool(row['is_active'])
                is_default = bool(row['is_default'])
                
                total_themes += 1
                if is_active:
                    active_themes += 1
                
                total_usage += usage_count
                if is_default:
                    default_theme_usage = usage_count
                
                theme_stats.append({
                    'id': row['id'],
                    'name': row['name'],
                    'usage_count': usage_count,
                    'is_default': is_default,
                    'is_active': is_active,
                    'usage_percentage': 0  # Will be calculated below
                })
            
            # Calculate usage percentages
            if total_usage > 0:
                for stat in theme_stats:
                    stat['usage_percentage'] = round((stat['usage_count'] / total_usage) * 100, 1)
            
            # Get most and least used themes
            most_used = theme_stats[0] if theme_stats else None
            least_used = None
            for stat in reversed(theme_stats):
                if stat['usage_count'] > 0:
                    least_used = stat
                    break
            
            statistics = {
                'total_themes': total_themes,
                'active_themes': active_themes,
                'inactive_themes': total_themes - active_themes,
                'total_usage': total_usage,
                'default_theme_usage': default_theme_usage,
                'theme_distribution': theme_stats,
                'most_used_theme': most_used,
                'least_used_theme': least_used,
                'unused_themes_count': len([s for s in theme_stats if s['usage_count'] == 0])
            }
            
            logger.debug(f"Retrieved statistics for {total_themes} themes with {total_usage} total usage")
            return statistics
            
        except Exception as e:
            logger.error(f"Error retrieving theme usage statistics: {e}")
            raise ServiceException("Failed to retrieve theme usage statistics") from e
    
    def validate_theme_reference(self, theme_id: Optional[int]) -> Tuple[bool, Optional[UnitTypeTheme], str]:
        """
        Validate a theme reference and return the theme if valid.
        
        Args:
            theme_id: ID of theme to validate (can be None)
            
        Returns:
            Tuple of (is_valid: bool, theme: Optional[UnitTypeTheme], error_message: str)
        """
        try:
            # None/null theme_id is valid (will use default)
            if theme_id is None:
                return True, None, ""
            
            # Check if theme exists and is active
            theme = self.get_by_id(theme_id)
            if not theme:
                logger.warning(f"Theme reference validation failed: theme {theme_id} not found")
                return False, None, f"Tema con ID {theme_id} non trovato"
            
            if not theme.is_active:
                logger.warning(f"Theme reference validation failed: theme {theme_id} is inactive")
                return False, theme, f"Tema '{theme.name}' non è attivo"
            
            # Validate theme data integrity
            validation_errors = theme.validate()
            if validation_errors:
                error_messages = [f"{err.field}: {err.message}" for err in validation_errors]
                logger.warning(f"Theme reference validation failed: theme {theme_id} has validation errors: {error_messages}")
                return False, theme, f"Tema '{theme.name}' contiene dati non validi: {'; '.join(error_messages[:3])}"
            
            logger.debug(f"Theme reference validation successful for theme {theme_id}")
            return True, theme, ""
            
        except Exception as e:
            logger.error(f"Error validating theme reference {theme_id}: {e}")
            return False, None, f"Errore durante la validazione del riferimento al tema: {str(e)}"
    
    def get_theme_with_fallback(self, theme_id: Optional[int]) -> UnitTypeTheme:
        """
        Get theme by ID with automatic fallback to default theme if invalid.
        
        Args:
            theme_id: ID of theme to retrieve
            
        Returns:
            Valid UnitTypeTheme instance (never None)
        """
        try:
            # Validate theme reference
            is_valid, theme, error_message = self.validate_theme_reference(theme_id)
            
            if is_valid and theme:
                return theme
            elif is_valid and theme is None:
                # theme_id was None, get default theme
                return self.get_default_theme()
            else:
                # Invalid theme reference, log warning and use default
                logger.warning(f"Invalid theme reference {theme_id}: {error_message}. Using default theme.")
                return self.get_default_theme()
                
        except Exception as e:
            logger.error(f"Error getting theme with fallback for ID {theme_id}: {e}")
            # Last resort: return emergency fallback
            return self._get_emergency_fallback_theme()
    
    def repair_corrupted_theme_data(self, theme_id: int) -> Tuple[bool, List[str]]:
        """
        Attempt to repair corrupted theme data by applying safe defaults.
        
        Args:
            theme_id: ID of theme to repair
            
        Returns:
            Tuple of (success: bool, repair_actions: List[str])
        """
        try:
            logger.info(f"Attempting to repair corrupted theme data for theme {theme_id}")
            
            theme = self.get_by_id(theme_id)
            if not theme:
                return False, ["Tema non trovato"]
            
            repair_actions = []
            
            # Repair invalid colors
            if not theme._is_valid_color(theme.primary_color):
                theme.primary_color = "#0dcaf0"
                repair_actions.append("Ripristinato colore primario predefinito")
            
            if not theme._is_valid_color(theme.secondary_color):
                theme.secondary_color = "#f0fdff"
                repair_actions.append("Ripristinato colore secondario predefinito")
            
            if not theme._is_valid_color(theme.text_color):
                theme.text_color = theme.primary_color
                repair_actions.append("Ripristinato colore testo predefinito")
            
            # Repair invalid icon class
            if not theme._is_valid_icon_class(theme.icon_class):
                theme.icon_class = "diagram-2"
                repair_actions.append("Ripristinata classe icona predefinita")
            
            # Repair invalid CSS class suffix
            if not theme._is_valid_css_class_suffix(theme.css_class_suffix):
                theme.css_class_suffix = f"theme-{theme.id}" if theme.id else "repaired"
                repair_actions.append("Ripristinato suffisso classe CSS")
            
            # Repair invalid border properties
            if theme.border_width < 0 or theme.border_width > 20:
                theme.border_width = 2
                repair_actions.append("Ripristinata larghezza bordo predefinita")
            
            valid_border_styles = ["solid", "dashed", "dotted", "double", "groove", "ridge", "inset", "outset"]
            if theme.border_style not in valid_border_styles:
                theme.border_style = "solid"
                repair_actions.append("Ripristinato stile bordo predefinito")
            
            # Repair invalid hover shadow intensity
            if theme.hover_shadow_intensity < 0 or theme.hover_shadow_intensity > 1:
                theme.hover_shadow_intensity = 0.25
                repair_actions.append("Ripristinata intensità ombra hover predefinita")
            
            # Repair empty required fields
            if not theme.name or not theme.name.strip():
                theme.name = f"Tema Riparato {theme.id}" if theme.id else "Tema Riparato"
                repair_actions.append("Ripristinato nome tema")
            
            if not theme.display_label or not theme.display_label.strip():
                theme.display_label = "Unità"
                repair_actions.append("Ripristinata etichetta di visualizzazione")
            
            # Repair invalid emoji
            if not theme._is_valid_emoji(theme.emoji_fallback):
                theme.emoji_fallback = "🏛️"
                repair_actions.append("Ripristinato emoji fallback predefinito")
            
            # Repair invalid background gradient
            if theme.background_gradient and not theme._is_valid_css_gradient(theme.background_gradient):
                theme.background_gradient = None
                repair_actions.append("Rimosso gradiente sfondo non valido")
            
            # Save repaired theme if any repairs were made
            if repair_actions:
                self.update(theme)
                logger.info(f"Successfully repaired theme {theme_id}: {'; '.join(repair_actions)}")
                return True, repair_actions
            else:
                logger.info(f"No repairs needed for theme {theme_id}")
                return True, ["Nessuna riparazione necessaria"]
                
        except Exception as e:
            logger.error(f"Error repairing corrupted theme data for theme {theme_id}: {e}")
            return False, [f"Errore durante la riparazione: {str(e)}"]

    def get_unit_types_using_theme(self, theme_id: int) -> List[Dict[str, Any]]:
        """
        Get all unit types that are using a specific theme.
        
        Args:
            theme_id: ID of the theme
            
        Returns:
            List of unit type information using the theme
            
        Raises:
            ServiceException: If unable to retrieve unit types
        """
        try:
            logger.debug(f"Retrieving unit types using theme {theme_id}")
            
            query = """
            SELECT ut.id, ut.name, ut.short_name, ut.level,
                   COUNT(u.id) as units_count
            FROM unit_types ut
            LEFT JOIN units u ON ut.id = u.unit_type_id
            WHERE ut.theme_id = ?
            GROUP BY ut.id, ut.name, ut.short_name, ut.level
            ORDER BY ut.name
            """
            
            rows = self.db_manager.fetch_all(query, (theme_id,))
            
            unit_types = []
            for row in rows:
                unit_types.append({
                    'id': row['id'],
                    'name': row['name'],
                    'short_name': row['short_name'],
                    'level': row['level'],
                    'units_count': row['units_count']
                })
            
            logger.debug(f"Retrieved {len(unit_types)} unit types using theme {theme_id}")
            return unit_types
            
        except Exception as e:
            logger.error(f"Error retrieving unit types using theme {theme_id}: {e}")
            raise ServiceException("Failed to retrieve unit types using theme") from e

    def invalidate_css_cache(self) -> None:
        """Invalidate CSS cache to force regeneration"""
        global _css_cache
        _css_cache.invalidate()
        logger.debug("CSS cache invalidated")

    def create(self, theme: UnitTypeTheme) -> UnitTypeTheme:
        """Override create to invalidate CSS cache"""
        result = super().create(theme)
        if result:
            self.invalidate_css_cache()
        return result

    def get_unit_types_using_theme(self, theme_id: int) -> List[Dict[str, Any]]:
        """
        Get all unit types that are using a specific theme.
        
        Args:
            theme_id: ID of the theme
            
        Returns:
            List of unit type information using the theme
            
        Raises:
            ServiceException: If unable to retrieve unit types
        """
        try:
            logger.debug(f"Retrieving unit types using theme {theme_id}")
            
            query = """
            SELECT ut.id, ut.name, ut.short_name, ut.level,
                   COUNT(u.id) as units_count
            FROM unit_types ut
            LEFT JOIN units u ON ut.id = u.unit_type_id
            WHERE ut.theme_id = ?
            GROUP BY ut.id, ut.name, ut.short_name, ut.level
            ORDER BY ut.name
            """
            
            rows = self.db_manager.fetch_all(query, (theme_id,))
            
            unit_types = []
            for row in rows:
                unit_types.append({
                    'id': row['id'],
                    'name': row['name'],
                    'short_name': row['short_name'],
                    'level': row['level'],
                    'units_count': row['units_count']
                })
            
            logger.debug(f"Retrieved {len(unit_types)} unit types using theme {theme_id}")
            return unit_types
            
        except Exception as e:
            logger.error(f"Error retrieving unit types using theme {theme_id}: {e}")
            raise ServiceException("Failed to retrieve unit types using theme") from e

    def invalidate_css_cache(self) -> None:
        """Invalidate CSS cache to force regeneration"""
        global _css_cache
        _css_cache.invalidate()
        logger.debug("CSS cache invalidated")

    def create(self, theme: UnitTypeTheme) -> UnitTypeTheme:
        """Override create to invalidate CSS cache"""
        result = super().create(theme)
        if result:
            self.invalidate_css_cache()
        return result

    def update(self, theme: UnitTypeTheme) -> UnitTypeTheme:
        """Override update to invalidate CSS cache"""
        result = super().update(theme)
        if result:
            self.invalidate_css_cache()
        return result

    def delete(self, theme_id: int) -> bool:
        """Override delete to invalidate CSS cache"""
        result = super().delete(theme_id)
        if result:
            self.invalidate_css_cache()
        return result

    def get_theme_analytics_dashboard(self) -> Dict[str, Any]:
        """
        Get comprehensive analytics data for theme management dashboard.
        
        Returns:
            Dictionary with complete analytics data for dashboard
            
        Raises:
            ServiceException: If unable to retrieve analytics data
        """
        try:
            logger.debug("Retrieving theme analytics dashboard data")
            
            # Get basic theme statistics
            theme_stats = self.get_theme_usage_statistics()
            
            # Get theme adoption trends (themes created over time)
            adoption_trends = self._get_theme_adoption_trends()
            
            # Get theme performance metrics
            performance_metrics = self._get_theme_performance_metrics()
            
            # Get theme health indicators
            health_indicators = self._get_theme_health_indicators()
            
            # Get recommendations
            recommendations = self._generate_theme_recommendations(theme_stats)
            
            dashboard_data = {
                'overview': {
                    'total_themes': theme_stats['total_themes'],
                    'active_themes': theme_stats['active_themes'],
                    'inactive_themes': theme_stats['inactive_themes'],
                    'total_usage': theme_stats['total_usage'],
                    'unused_themes_count': theme_stats['unused_themes_count']
                },
                'usage_distribution': theme_stats['theme_distribution'],
                'most_used_theme': theme_stats['most_used_theme'],
                'least_used_theme': theme_stats['least_used_theme'],
                'adoption_trends': adoption_trends,
                'performance_metrics': performance_metrics,
                'health_indicators': health_indicators,
                'recommendations': recommendations,
                'last_updated': time.time()
            }
            
            logger.debug("Successfully retrieved theme analytics dashboard data")
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Error retrieving theme analytics dashboard: {e}")
            raise ServiceException("Failed to retrieve theme analytics dashboard") from e

    def _get_theme_adoption_trends(self) -> Dict[str, Any]:
        """Get theme adoption trends over time"""
        try:
            # Get themes created by month for the last 12 months
            query = """
            SELECT 
                strftime('%Y-%m', datetime_created) as month,
                COUNT(*) as themes_created
            FROM unit_type_themes
            WHERE datetime_created >= datetime('now', '-12 months')
            GROUP BY strftime('%Y-%m', datetime_created)
            ORDER BY month
            """
            
            rows = self.db_manager.fetch_all(query)
            
            monthly_creation = []
            for row in rows:
                monthly_creation.append({
                    'month': row['month'],
                    'themes_created': row['themes_created']
                })
            
            # Get theme activation/deactivation trends
            query = """
            SELECT 
                is_active,
                COUNT(*) as count
            FROM unit_type_themes
            GROUP BY is_active
            """
            
            rows = self.db_manager.fetch_all(query)
            activation_status = {}
            for row in rows:
                status = 'active' if row['is_active'] else 'inactive'
                activation_status[status] = row['count']
            
            return {
                'monthly_creation': monthly_creation,
                'activation_status': activation_status
            }
            
        except Exception as e:
            logger.error(f"Error getting theme adoption trends: {e}")
            return {'monthly_creation': [], 'activation_status': {}}

    def _get_theme_performance_metrics(self) -> Dict[str, Any]:
        """Get theme performance and efficiency metrics"""
        try:
            # Calculate average usage per theme
            query = """
            SELECT 
                AVG(CAST(usage_count AS FLOAT)) as avg_usage,
                MAX(usage_count) as max_usage,
                MIN(usage_count) as min_usage
            FROM (
                SELECT COUNT(ut.id) as usage_count
                FROM unit_type_themes utt
                LEFT JOIN unit_types ut ON utt.id = ut.theme_id
                WHERE utt.is_active = 1
                GROUP BY utt.id
            )
            """
            
            row = self.db_manager.fetch_one(query)
            usage_metrics = {
                'average_usage': round(row['avg_usage'] or 0, 2),
                'max_usage': row['max_usage'] or 0,
                'min_usage': row['min_usage'] or 0
            }
            
            # Calculate theme efficiency (usage vs creation ratio)
            query = """
            SELECT 
                COUNT(DISTINCT utt.id) as total_themes,
                COUNT(DISTINCT ut.theme_id) as used_themes
            FROM unit_type_themes utt
            LEFT JOIN unit_types ut ON utt.id = ut.theme_id
            WHERE utt.is_active = 1
            """
            
            row = self.db_manager.fetch_one(query)
            total_themes = row['total_themes'] or 0
            used_themes = row['used_themes'] or 0
            
            efficiency_metrics = {
                'utilization_rate': round((used_themes / total_themes * 100) if total_themes > 0 else 0, 1),
                'unused_themes': total_themes - used_themes
            }
            
            return {
                'usage_metrics': usage_metrics,
                'efficiency_metrics': efficiency_metrics
            }
            
        except Exception as e:
            logger.error(f"Error getting theme performance metrics: {e}")
            return {'usage_metrics': {}, 'efficiency_metrics': {}}

    def _get_theme_health_indicators(self) -> Dict[str, Any]:
        """Get theme system health indicators"""
        try:
            health_indicators = []
            
            # Check for themes with validation issues
            themes = self.get_all()
            invalid_themes = []
            for theme in themes:
                validation_errors = theme.validate()
                if validation_errors:
                    invalid_themes.append({
                        'id': theme.id,
                        'name': theme.name,
                        'error_count': len(validation_errors)
                    })
            
            if invalid_themes:
                health_indicators.append({
                    'type': 'warning',
                    'title': 'Temi con Errori di Validazione',
                    'message': f'{len(invalid_themes)} temi contengono errori di validazione',
                    'details': invalid_themes[:5],  # Show first 5
                    'action': 'repair_themes'
                })
            
            # Check for unused themes
            unused_count = len([t for t in themes if getattr(t, 'usage_count', 0) == 0])
            if unused_count > 0:
                health_indicators.append({
                    'type': 'info',
                    'title': 'Temi Non Utilizzati',
                    'message': f'{unused_count} temi non sono utilizzati da alcun tipo di unità',
                    'action': 'review_unused_themes'
                })
            
            # Check for default theme
            default_themes = [t for t in themes if t.is_default]
            if len(default_themes) == 0:
                health_indicators.append({
                    'type': 'error',
                    'title': 'Nessun Tema Predefinito',
                    'message': 'Non è stato trovato alcun tema predefinito',
                    'action': 'set_default_theme'
                })
            elif len(default_themes) > 1:
                health_indicators.append({
                    'type': 'warning',
                    'title': 'Multipli Temi Predefiniti',
                    'message': f'{len(default_themes)} temi sono marcati come predefiniti',
                    'action': 'fix_default_themes'
                })
            
            # Check for inactive themes still in use
            query = """
            SELECT utt.id, utt.name, COUNT(ut.id) as usage_count
            FROM unit_type_themes utt
            JOIN unit_types ut ON utt.id = ut.theme_id
            WHERE utt.is_active = 0
            GROUP BY utt.id, utt.name
            """
            
            rows = self.db_manager.fetch_all(query)
            if rows:
                inactive_in_use = [{'id': r['id'], 'name': r['name'], 'usage_count': r['usage_count']} for r in rows]
                health_indicators.append({
                    'type': 'warning',
                    'title': 'Temi Inattivi in Uso',
                    'message': f'{len(inactive_in_use)} temi inattivi sono ancora utilizzati',
                    'details': inactive_in_use,
                    'action': 'activate_or_replace_themes'
                })
            
            return {
                'indicators': health_indicators,
                'overall_health': 'good' if len([i for i in health_indicators if i['type'] == 'error']) == 0 else 'warning'
            }
            
        except Exception as e:
            logger.error(f"Error getting theme health indicators: {e}")
            return {'indicators': [], 'overall_health': 'unknown'}

    def _generate_theme_recommendations(self, theme_stats: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate actionable recommendations based on theme statistics"""
        try:
            recommendations = []
            
            # Recommend consolidating unused themes
            if theme_stats['unused_themes_count'] > 3:
                recommendations.append({
                    'type': 'optimization',
                    'priority': 'medium',
                    'title': 'Consolida Temi Non Utilizzati',
                    'description': f'Hai {theme_stats["unused_themes_count"]} temi non utilizzati. Considera di eliminarli per semplificare la gestione.',
                    'action': 'cleanup_unused_themes'
                })
            
            # Recommend creating themes if too few
            if theme_stats['active_themes'] < 2:
                recommendations.append({
                    'type': 'enhancement',
                    'priority': 'low',
                    'title': 'Crea Più Temi',
                    'description': 'Considera di creare temi aggiuntivi per differenziare meglio i tipi di unità.',
                    'action': 'create_additional_themes'
                })
            
            # Recommend balancing theme usage
            if theme_stats['most_used_theme'] and theme_stats['most_used_theme']['usage_percentage'] > 80:
                recommendations.append({
                    'type': 'balance',
                    'priority': 'low',
                    'title': 'Bilancia Utilizzo Temi',
                    'description': f'Il tema "{theme_stats["most_used_theme"]["name"]}" è utilizzato dal {theme_stats["most_used_theme"]["usage_percentage"]}% dei tipi di unità.',
                    'action': 'redistribute_theme_usage'
                })
            
            # Recommend performance optimization
            if theme_stats['total_themes'] > 10:
                recommendations.append({
                    'type': 'performance',
                    'priority': 'low',
                    'title': 'Ottimizza Performance',
                    'description': f'Con {theme_stats["total_themes"]} temi, considera di ottimizzare la cache CSS per migliorare le performance.',
                    'action': 'optimize_css_cache'
                })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating theme recommendations: {e}")
            return []

    def get_theme_impact_analysis(self, theme_id: int) -> Dict[str, Any]:
        """
        Analyze the impact of changes to a specific theme.
        
        Args:
            theme_id: ID of the theme to analyze
            
        Returns:
            Dictionary with impact analysis data
            
        Raises:
            ServiceException: If unable to perform impact analysis
        """
        try:
            logger.debug(f"Performing impact analysis for theme {theme_id}")
            
            theme = self.get_by_id(theme_id)
            if not theme:
                raise ServiceNotFoundException(f"Tema con ID {theme_id} non trovato")
            
            # Get unit types using this theme
            unit_types = self.get_unit_types_using_theme(theme_id)
            
            # Calculate total units affected
            total_units_affected = sum(ut['units_count'] for ut in unit_types)
            
            # Get organizational levels affected
            levels_affected = list(set(ut['level'] for ut in unit_types if ut['level'] is not None))
            levels_affected.sort()
            
            # Determine impact severity
            impact_severity = 'low'
            if total_units_affected > 50:
                impact_severity = 'high'
            elif total_units_affected > 10:
                impact_severity = 'medium'
            
            # Check if this is the default theme
            is_default_theme = theme.is_default
            if is_default_theme:
                impact_severity = 'critical'
            
            # Generate impact warnings
            warnings = []
            if is_default_theme:
                warnings.append("Questo è il tema predefinito - le modifiche influenzeranno tutti i tipi di unità senza tema specifico")
            
            if total_units_affected > 100:
                warnings.append(f"Le modifiche influenzeranno oltre {total_units_affected} unità nell'organigramma")
            
            if len(unit_types) > 5:
                warnings.append(f"Le modifiche influenzeranno {len(unit_types)} diversi tipi di unità")
            
            # Estimate CSS regeneration impact
            css_impact = {
                'cache_invalidation_required': True,
                'estimated_regeneration_time': 'low' if len(unit_types) < 5 else 'medium',
                'affected_css_classes': [f"unit-{theme.css_class_suffix}"]
            }
            
            impact_analysis = {
                'theme': {
                    'id': theme.id,
                    'name': theme.name,
                    'is_default': is_default_theme
                },
                'affected_unit_types': unit_types,
                'total_units_affected': total_units_affected,
                'levels_affected': levels_affected,
                'impact_severity': impact_severity,
                'warnings': warnings,
                'css_impact': css_impact,
                'recommendations': self._generate_impact_recommendations(theme, unit_types, impact_severity)
            }
            
            logger.debug(f"Impact analysis completed for theme {theme_id}: {impact_severity} severity, {total_units_affected} units affected")
            return impact_analysis
            
        except ServiceNotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error performing impact analysis for theme {theme_id}: {e}")
            raise ServiceException("Failed to perform theme impact analysis") from e

    def _generate_impact_recommendations(self, theme: UnitTypeTheme, unit_types: List[Dict], severity: str) -> List[str]:
        """Generate recommendations based on impact analysis"""
        recommendations = []
        
        if severity == 'critical':
            recommendations.append("Testa accuratamente le modifiche in un ambiente di sviluppo prima di applicarle")
            recommendations.append("Considera di creare un backup del tema corrente")
        
        if severity in ['high', 'critical']:
            recommendations.append("Notifica agli utenti le modifiche visive che verranno applicate")
            recommendations.append("Pianifica le modifiche durante orari di basso utilizzo")
        
        if len(unit_types) > 3:
            recommendations.append("Verifica che le modifiche siano coerenti con tutti i tipi di unità interessati")
        
        if theme.is_default:
            recommendations.append("Considera di creare temi specifici per ridurre la dipendenza dal tema predefinito")
        
        return recommendations

    def get_most_least_used_themes_report(self) -> Dict[str, Any]:
        """
        Generate a detailed report of most and least used themes.
        
        Returns:
            Dictionary with detailed usage report
            
        Raises:
            ServiceException: If unable to generate report
        """
        try:
            logger.debug("Generating most/least used themes report")
            
            # Get themes with detailed usage statistics
            query = """
            SELECT utt.id, utt.name, utt.description, utt.is_default, utt.is_active,
                   utt.datetime_created, utt.datetime_updated,
                   COUNT(ut.id) as usage_count,
                   COUNT(DISTINCT u.id) as total_units_count,
                   GROUP_CONCAT(DISTINCT ut.name) as unit_type_names
            FROM unit_type_themes utt
            LEFT JOIN unit_types ut ON utt.id = ut.theme_id
            LEFT JOIN units u ON ut.id = u.unit_type_id
            GROUP BY utt.id, utt.name, utt.description, utt.is_default, utt.is_active,
                     utt.datetime_created, utt.datetime_updated
            ORDER BY usage_count DESC, utt.name
            """
            
            rows = self.db_manager.fetch_all(query)
            
            themes_data = []
            total_usage = 0
            
            for row in rows:
                usage_count = row['usage_count']
                total_usage += usage_count
                
                unit_type_names = row['unit_type_names'].split(',') if row['unit_type_names'] else []
                
                themes_data.append({
                    'id': row['id'],
                    'name': row['name'],
                    'description': row['description'],
                    'is_default': bool(row['is_default']),
                    'is_active': bool(row['is_active']),
                    'usage_count': usage_count,
                    'total_units_count': row['total_units_count'],
                    'unit_type_names': unit_type_names,
                    'created_date': row['datetime_created'],
                    'updated_date': row['datetime_updated'],
                    'usage_percentage': 0  # Will be calculated below
                })
            
            # Calculate usage percentages
            if total_usage > 0:
                for theme_data in themes_data:
                    theme_data['usage_percentage'] = round((theme_data['usage_count'] / total_usage) * 100, 1)
            
            # Separate most and least used
            used_themes = [t for t in themes_data if t['usage_count'] > 0]
            unused_themes = [t for t in themes_data if t['usage_count'] == 0]
            
            # Get top 5 most used and bottom 5 least used (but still used)
            most_used = used_themes[:5] if used_themes else []
            least_used = used_themes[-5:] if len(used_themes) > 5 else []
            
            report = {
                'summary': {
                    'total_themes': len(themes_data),
                    'used_themes': len(used_themes),
                    'unused_themes': len(unused_themes),
                    'total_usage': total_usage
                },
                'most_used_themes': most_used,
                'least_used_themes': least_used,
                'unused_themes': unused_themes,
                'all_themes_data': themes_data,
                'generated_at': time.time()
            }
            
            logger.debug(f"Generated usage report: {len(used_themes)} used themes, {len(unused_themes)} unused themes")
            return report
            
        except Exception as e:
            logger.error(f"Error generating most/least used themes report: {e}")
            raise ServiceException("Failed to generate themes usage report") from e