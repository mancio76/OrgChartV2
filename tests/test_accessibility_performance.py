"""
Tests for accessibility and performance optimizations in the theme system
"""

import pytest
import time
from unittest.mock import Mock, patch
from app.models.unit_type_theme import UnitTypeTheme
from app.services.unit_type_theme import UnitTypeThemeService, CSSCache
from app.models.base import ValidationError


class TestAccessibilityFeatures:
    """Test accessibility features in the theme system"""
    
    def test_color_contrast_validation_wcag_aa(self):
        """Test WCAG AA color contrast validation"""
        # Test theme with good contrast
        good_theme = UnitTypeTheme(
            name="Good Contrast Theme",
            primary_color="#000000",  # Black
            text_color="#ffffff",     # White
            secondary_color="#000000", # Black for better contrast
            display_label="Test"
        )
        
        errors = good_theme.validate()
        contrast_errors = [e for e in errors if "contrasto" in e.message.lower()]
        assert len(contrast_errors) == 0, f"Good contrast theme should not have contrast errors: {[e.message for e in contrast_errors]}"
        
        # Test theme with poor contrast
        poor_theme = UnitTypeTheme(
            name="Poor Contrast Theme",
            primary_color="#ffff00",  # Yellow
            text_color="#ffffff",     # White
            secondary_color="#f8f9fa",
            display_label="Test"
        )
        
        errors = poor_theme.validate()
        contrast_errors = [e for e in errors if "contrasto" in e.message.lower()]
        assert len(contrast_errors) > 0, "Poor contrast theme should have contrast errors"
    
    def test_high_contrast_mode_css_generation(self):
        """Test CSS generation for high contrast mode"""
        theme = UnitTypeTheme(
            name="High Contrast Theme",
            primary_color="#0000ff",
            text_color="#ffffff",
            secondary_color="#f0f0f0",
            display_label="Test",
            high_contrast_mode=True
        )
        
        css_rules = theme.generate_css_rules()
        
        # Check for high contrast specific rules
        assert "high-contrast" in css_rules
        assert "@media (prefers-contrast: high)" in css_rules
        assert "body.high-contrast" in css_rules
        assert "font-weight: 700" in css_rules
    
    def test_accessibility_info_calculation(self):
        """Test accessibility information calculation"""
        theme = UnitTypeTheme(
            name="Test Theme",
            primary_color="#0d6efd",
            text_color="#ffffff",
            secondary_color="#f8f9ff",
            display_label="Test"
        )
        
        accessibility_info = theme.get_accessibility_info()
        
        assert "contrast_ratios" in accessibility_info
        assert "accessibility_score" in accessibility_info
        assert "recommendations" in accessibility_info
        assert isinstance(accessibility_info["accessibility_score"], int)
        assert 0 <= accessibility_info["accessibility_score"] <= 100
    
    def test_reduced_motion_css_support(self):
        """Test CSS generation includes reduced motion support"""
        theme = UnitTypeTheme(
            name="Motion Test Theme",
            primary_color="#0dcaf0",
            text_color="#000000",
            secondary_color="#f0fdff",
            display_label="Test"
        )
        
        css_rules = theme.generate_css_rules()
        
        assert "@media (prefers-reduced-motion: reduce)" in css_rules
        assert "transition: none" in css_rules
        assert "transform: none" in css_rules
    
    def test_focus_styles_generation(self):
        """Test CSS generation includes proper focus styles"""
        theme = UnitTypeTheme(
            name="Focus Test Theme",
            primary_color="#0dcaf0",
            text_color="#000000",
            secondary_color="#f0fdff",
            display_label="Test"
        )
        
        css_rules = theme.generate_css_rules()
        
        assert ":focus" in css_rules
        assert ":focus-within" in css_rules
        assert "outline:" in css_rules
        assert "box-shadow:" in css_rules
    
    def test_color_format_validation(self):
        """Test validation of different color formats"""
        # Test hex colors
        theme_hex = UnitTypeTheme(
            name="Hex Theme",
            primary_color="#ff0000",
            text_color="#000000",
            secondary_color="#ffffff",
            display_label="Test"
        )
        assert theme_hex._color_to_rgb("#ff0000") == (255, 0, 0)
        
        # Test RGB colors
        assert theme_hex._color_to_rgb("rgb(255, 0, 0)") == (255, 0, 0)
        
        # Test named colors
        assert theme_hex._color_to_rgb("red") == (255, 0, 0)
        assert theme_hex._color_to_rgb("white") == (255, 255, 255)
        assert theme_hex._color_to_rgb("black") == (0, 0, 0)
    
    def test_contrast_ratio_calculation(self):
        """Test WCAG contrast ratio calculation"""
        theme = UnitTypeTheme(
            name="Contrast Test",
            primary_color="#000000",
            text_color="#ffffff",
            secondary_color="#f0f0f0",
            display_label="Test"
        )
        
        # Black and white should have maximum contrast (21:1)
        black_rgb = (0, 0, 0)
        white_rgb = (255, 255, 255)
        contrast_ratio = theme._calculate_contrast_ratio(black_rgb, white_rgb)
        
        assert contrast_ratio >= 20.0, f"Black/white contrast should be ~21:1, got {contrast_ratio}"
        
        # Same colors should have minimum contrast (1:1)
        same_contrast = theme._calculate_contrast_ratio(black_rgb, black_rgb)
        assert same_contrast == 1.0, f"Same color contrast should be 1:1, got {same_contrast}"


class TestPerformanceOptimizations:
    """Test performance optimization features"""
    
    def test_css_cache_functionality(self):
        """Test CSS caching mechanism"""
        cache = CSSCache(ttl_seconds=1)
        
        # Test cache miss
        result = cache.get("test_key")
        assert result is None
        
        # Test cache set and hit
        test_css = "body { color: red; }"
        cache.set("test_key", test_css)
        result = cache.get("test_key")
        assert result == test_css
        
        # Test cache expiration
        time.sleep(1.1)
        result = cache.get("test_key")
        assert result is None
        
        # Test cache invalidation
        cache.set("test_key", test_css)
        cache.invalidate("test_key")
        result = cache.get("test_key")
        assert result is None
    
    def test_css_minification(self):
        """Test CSS minification functionality"""
        service = UnitTypeThemeService()
        
        css_with_comments = """
        /* This is a comment */
        .test {
            color: red;
            background: blue;
        }
        
        /* Another comment */
        .test2 {
            margin: 10px;
        }
        """
        
        minified = service._minify_css(css_with_comments)
        
        # Comments should be removed
        assert "/* This is a comment */" not in minified
        assert "/* Another comment */" not in minified
        
        # Whitespace should be reduced
        assert len(minified) < len(css_with_comments)
        
        # CSS should still be valid
        assert ".test{" in minified or ".test {" in minified
        assert "color:red" in minified or "color: red" in minified
    
    def test_lazy_theme_data_loading(self):
        """Test lazy loading of theme data"""
        with patch.object(UnitTypeThemeService, 'db_manager') as mock_db:
            service = UnitTypeThemeService()
            
            # Mock database response
            mock_db.fetch_all.return_value = [
                {
                    'id': 1,
                    'name': 'Test Theme',
                    'icon_class': 'test-icon',
                    'emoji_fallback': '🏛️',
                    'primary_color': '#0dcaf0',
                    'secondary_color': '#f0fdff',
                    'text_color': '#0dcaf0',
                    'border_color': None,
                    'border_width': 2,
                    'css_class_suffix': 'test',
                    'display_label': 'Test',
                    'high_contrast_mode': False
                }
            ]
            
            lazy_data = service.get_lazy_theme_data([1])
            
            assert 1 in lazy_data
            theme_data = lazy_data[1]
            assert theme_data['name'] == 'Test Theme'
            assert theme_data['css_class_name'] == 'unit-test'
            assert theme_data['computed_border_color'] == '#0dcaf0'
    
    def test_performance_metrics_collection(self):
        """Test performance metrics collection"""
        with patch.object(UnitTypeThemeService, 'db_manager') as mock_db:
            service = UnitTypeThemeService()
            
            # Mock database responses
            mock_db.fetch_one.side_effect = [
                {
                    'total_themes': 5,
                    'active_themes': 4,
                    'high_contrast_themes': 1,
                    'avg_border_width': 2.5,
                    'themes_with_gradients': 2
                },
                {
                    'theme_usage_count': 10
                }
            ]
            
            mock_db.fetch_all.return_value = []  # For CSS generation
            
            metrics = service.get_performance_metrics()
            
            assert 'cache_stats' in metrics
            assert 'theme_stats' in metrics
            assert 'css_generation' in metrics
            assert 'database_stats' in metrics
            
            # Check theme stats
            assert metrics['theme_stats']['total_themes'] == 5
            assert metrics['theme_stats']['active_themes'] == 4
    
    def test_theme_complexity_score(self):
        """Test theme complexity scoring for performance estimation"""
        # Simple theme
        simple_theme = UnitTypeTheme(
            name="Simple Theme",
            primary_color="#0dcaf0",
            text_color="#000000",
            secondary_color="#f0fdff",
            display_label="Simple"
        )
        
        simple_score = simple_theme._calculate_complexity_score()
        
        # Complex theme
        complex_theme = UnitTypeTheme(
            name="Complex Theme",
            primary_color="#ff6b35",  # Non-standard color
            text_color="#ffffff",
            secondary_color="#f0fdff",
            display_label="Complex",
            background_gradient="linear-gradient(45deg, #ff6b35, #f7931e)",
            hover_shadow_intensity=0.8,
            high_contrast_mode=True,
            border_style="dashed",
            border_width=5
        )
        
        complex_score = complex_theme._calculate_complexity_score()
        
        assert complex_score > simple_score, "Complex theme should have higher complexity score"
        assert 0 <= simple_score <= 100, "Complexity score should be between 0 and 100"
        assert 0 <= complex_score <= 100, "Complexity score should be between 0 and 100"
    
    def test_preload_themes_for_orgchart(self):
        """Test theme preloading for orgchart performance"""
        with patch.object(UnitTypeThemeService, 'db_manager') as mock_db:
            service = UnitTypeThemeService()
            
            # Mock database response
            mock_db.fetch_all.return_value = [
                {
                    'unit_type_id': 1,
                    'theme_id': 1,
                    'theme_name': 'Function Theme',
                    'icon_class': 'building',
                    'emoji_fallback': '🏢',
                    'primary_color': '#0d6efd',
                    'secondary_color': '#f8f9ff',
                    'text_color': '#0d6efd',
                    'border_color': None,
                    'border_width': 4,
                    'css_class_suffix': 'function',
                    'display_label': 'Funzione',
                    'high_contrast_mode': False
                },
                {
                    'unit_type_id': 2,
                    'theme_id': None,  # No theme, should use default
                    'theme_name': None,
                    'icon_class': None,
                    'emoji_fallback': None,
                    'primary_color': None,
                    'secondary_color': None,
                    'text_color': None,
                    'border_color': None,
                    'border_width': None,
                    'css_class_suffix': None,
                    'display_label': None,
                    'high_contrast_mode': None
                }
            ]
            
            # Mock default theme
            with patch.object(service, 'get_default_theme') as mock_default:
                mock_default.return_value = UnitTypeTheme(
                    id=99,
                    name="Default Theme",
                    icon_class="diagram-2",
                    emoji_fallback="🏛️",
                    primary_color="#0dcaf0",
                    secondary_color="#f0fdff",
                    text_color="#0dcaf0",
                    border_width=2,
                    css_class_suffix="organizational",
                    display_label="Unità Organizzativa"
                )
                
                preloaded_data = service.preload_themes_for_orgchart([1, 2])
                
                assert 1 in preloaded_data
                assert 2 in preloaded_data
                
                # Unit type 1 should have its theme
                assert preloaded_data[1]['name'] == 'Function Theme'
                assert preloaded_data[1]['css_class_name'] == 'unit-function'
                
                # Unit type 2 should have default theme
                assert preloaded_data[2]['name'] == 'Default Theme'
                assert preloaded_data[2]['css_class_name'] == 'unit-organizational'
    
    def test_css_generation_with_caching(self):
        """Test CSS generation with caching enabled/disabled"""
        with patch.object(UnitTypeThemeService, 'db_manager') as mock_db:
            service = UnitTypeThemeService()
            
            # Mock database response
            mock_db.fetch_all.return_value = [
                {
                    'id': 1,
                    'name': 'Test Theme',
                    'description': 'Test',
                    'icon_class': 'test',
                    'emoji_fallback': '🏛️',
                    'primary_color': '#0dcaf0',
                    'secondary_color': '#f0fdff',
                    'text_color': '#0dcaf0',
                    'border_color': None,
                    'border_width': 2,
                    'border_style': 'solid',
                    'background_gradient': None,
                    'css_class_suffix': 'test',
                    'hover_shadow_color': None,
                    'hover_shadow_intensity': 0.25,
                    'display_label': 'Test',
                    'display_label_plural': None,
                    'high_contrast_mode': False,
                    'is_default': True,
                    'is_active': True,
                    'created_by': None,
                    'datetime_created': '2024-01-01 00:00:00',
                    'datetime_updated': '2024-01-01 00:00:00',
                    'usage_count': 0
                }
            ]
            
            # Test without caching
            css_no_cache = service.generate_dynamic_css(use_cache=False)
            assert len(css_no_cache) > 0
            assert "unit-test" in css_no_cache
            
            # Test with caching
            css_with_cache = service.generate_dynamic_css(use_cache=True)
            assert css_with_cache == css_no_cache
            
            # Test minified CSS
            css_minified = service.generate_dynamic_css(use_cache=False, minify=True)
            assert len(css_minified) <= len(css_no_cache)
            assert "unit-test" in css_minified


class TestAccessibilityIntegration:
    """Test integration of accessibility features with the theme system"""
    
    def test_theme_service_cache_invalidation(self):
        """Test that cache is properly invalidated on theme updates"""
        with patch.object(UnitTypeThemeService, 'db_manager') as mock_db:
            service = UnitTypeThemeService()
            
            # Mock theme data
            theme = UnitTypeTheme(
                id=1,
                name="Test Theme",
                primary_color="#0dcaf0",
                text_color="#000000",
                secondary_color="#f0fdff",
                display_label="Test",
                css_class_suffix="test"
            )
            
            # Mock database operations
            mock_db.fetch_one.return_value = {
                'id': 1,
                'name': 'Test Theme',
                'usage_count': 0
            }
            mock_db.execute.return_value = None
            
            with patch.object(service, 'invalidate_css_cache') as mock_invalidate:
                # Update theme should invalidate cache
                with patch('app.services.base.BaseService.update') as mock_update:
                    mock_update.return_value = theme
                    service.update(theme)
                    mock_invalidate.assert_called_once()
    
    def test_accessibility_css_generation_in_service(self):
        """Test that service generates accessibility CSS"""
        with patch.object(UnitTypeThemeService, 'db_manager') as mock_db:
            service = UnitTypeThemeService()
            
            # Mock empty themes for fallback CSS
            mock_db.fetch_all.return_value = []
            
            css = service.generate_dynamic_css(use_cache=False)
            
            # Check for accessibility features
            assert "@media (prefers-reduced-motion: reduce)" in css
            assert "@media (prefers-contrast: high)" in css
            assert "min-height: 44px" in css  # Touch target size
            assert "outline:" in css  # Focus indicators
            assert ".sr-only" in css  # Screen reader support


if __name__ == "__main__":
    pytest.main([__file__])