"""
Tests for dynamic CSS generation system (Task 11)
"""

import pytest
import time
from unittest.mock import Mock, patch
from app.services.unit_type_theme import UnitTypeThemeService, CSSCache
from app.models.unit_type_theme import UnitTypeTheme


class TestCSSCache:
    """Test CSS caching mechanism"""
    
    def test_cache_set_and_get(self):
        """Test basic cache set and get operations"""
        cache = CSSCache(ttl_seconds=60)
        
        css_content = "/* test css */"
        cache.set("test_key", css_content)
        
        result = cache.get("test_key")
        assert result == css_content
    
    def test_cache_expiration(self):
        """Test cache TTL expiration"""
        cache = CSSCache(ttl_seconds=1)  # 1 second TTL
        
        css_content = "/* test css */"
        cache.set("test_key", css_content)
        
        # Should be available immediately
        assert cache.get("test_key") == css_content
        
        # Wait for expiration
        time.sleep(1.1)
        
        # Should be expired now
        assert cache.get("test_key") is None
    
    def test_cache_invalidation(self):
        """Test cache invalidation"""
        cache = CSSCache(ttl_seconds=60)
        
        cache.set("key1", "css1")
        cache.set("key2", "css2")
        
        # Invalidate specific key
        cache.invalidate("key1")
        assert cache.get("key1") is None
        assert cache.get("key2") == "css2"
        
        # Invalidate all
        cache.invalidate()
        assert cache.get("key2") is None
    
    def test_cache_key_generation(self):
        """Test cache key generation from themes"""
        cache = CSSCache()
        
        theme1 = UnitTypeTheme(id=1, name="Theme 1", datetime_updated="2024-01-01 10:00:00")
        theme2 = UnitTypeTheme(id=2, name="Theme 2", datetime_updated="2024-01-01 11:00:00")
        
        key1 = cache.get_cache_key([theme1, theme2])
        key2 = cache.get_cache_key([theme2, theme1])  # Different order
        
        # Keys should be the same regardless of order
        assert key1 == key2
        assert len(key1) == 32  # MD5 hash length


class TestDynamicCSSGeneration:
    """Test dynamic CSS generation"""
    
    @pytest.fixture
    def mock_theme_service(self):
        """Create mock theme service with test data"""
        service = UnitTypeThemeService()
        
        # Mock database manager
        service.db_manager = Mock()
        
        return service
    
    @pytest.fixture
    def sample_themes(self):
        """Create sample themes for testing"""
        return [
            UnitTypeTheme(
                id=1,
                name="Function Theme",
                icon_class="building",
                emoji_fallback="🏢",
                primary_color="#0d6efd",
                secondary_color="#f8f9ff",
                text_color="#0d6efd",
                border_width=4,
                css_class_suffix="function",
                display_label="Funzione",
                is_default=True,
                is_active=True,
                datetime_updated="2024-01-01 10:00:00"
            ),
            UnitTypeTheme(
                id=2,
                name="Organizational Theme",
                icon_class="diagram-2",
                emoji_fallback="🏛️",
                primary_color="#0dcaf0",
                secondary_color="#f0fdff",
                text_color="#0dcaf0",
                border_width=2,
                css_class_suffix="organizational",
                display_label="Unità Organizzativa",
                is_default=False,
                is_active=True,
                datetime_updated="2024-01-01 11:00:00"
            )
        ]
    
    def test_generate_fallback_css(self, mock_theme_service):
        """Test fallback CSS generation when no themes available"""
        # Mock empty result
        mock_theme_service.db_manager.fetch_all.return_value = []
        
        css = mock_theme_service.generate_dynamic_css(use_cache=False)
        
        assert "Fallback CSS" in css
        assert ".unit-themed" in css
        assert ".unit-organizational" in css
        assert "var(--fallback-primary)" in css
    
    def test_generate_css_with_themes(self, mock_theme_service, sample_themes):
        """Test CSS generation with actual themes"""
        # Mock database result
        mock_rows = []
        for theme in sample_themes:
            row_dict = theme.to_dict()
            row_dict['usage_count'] = 0
            mock_rows.append(row_dict)
        
        mock_theme_service.db_manager.fetch_all.return_value = mock_rows
        
        # Mock UnitTypeTheme.from_sqlite_row to return our sample themes
        with patch.object(UnitTypeTheme, 'from_sqlite_row', side_effect=sample_themes):
            css = mock_theme_service.generate_dynamic_css(use_cache=False)
        
        # Verify CSS contains expected content (updated to match actual header)
        assert "Dynamic Unit Type Theme CSS" in css
        assert ":root {" in css
        assert "--theme-1-primary: #0d6efd" in css
        assert "--theme-2-primary: #0dcaf0" in css
        assert ".unit-function" in css
        assert ".unit-organizational" in css
        assert "Theme: Function Theme" in css
        assert "Theme: Organizational Theme" in css
    
    def test_css_caching_mechanism(self, mock_theme_service, sample_themes):
        """Test CSS caching works correctly"""
        # Test that cache methods are called correctly
        with patch('app.services.unit_type_theme._css_cache') as mock_cache:
            # Mock database result
            mock_rows = []
            for theme in sample_themes:
                row_dict = theme.to_dict()
                row_dict['usage_count'] = 0
                mock_rows.append(row_dict)
            
            mock_theme_service.db_manager.fetch_all.return_value = mock_rows
            
            # Create a fresh list for each call to avoid side_effect exhaustion
            def mock_from_sqlite_row(row):
                for theme in sample_themes:
                    if theme.to_dict().get('id') == row.get('id'):
                        return theme
                return sample_themes[0]  # fallback
            
            # First call - cache miss
            mock_cache.get_cache_key.return_value = "test_cache_key"
            mock_cache.get.return_value = None  # Cache miss
            
            with patch.object(UnitTypeTheme, 'from_sqlite_row', side_effect=mock_from_sqlite_row):
                css1 = mock_theme_service.generate_dynamic_css(use_cache=True)
                
                # Verify cache was checked and set
                mock_cache.get.assert_called_with("test_cache_key")
                mock_cache.set.assert_called_once_with("test_cache_key", css1)
                
                # Second call - cache hit
                mock_cache.get.return_value = css1  # Cache hit
                css2 = mock_theme_service.generate_dynamic_css(use_cache=True)
                
                # CSS should be identical
                assert css1 == css2
                
                # Cache should have been checked twice
                assert mock_cache.get.call_count == 2
    
    def test_cache_invalidation_on_crud_operations(self, mock_theme_service):
        """Test that cache is invalidated on CRUD operations"""
        # Mock successful operations
        mock_theme_service.db_manager.fetch_one.return_value = None
        mock_theme_service.db_manager.execute_query.return_value = Mock(rowcount=1)
        mock_theme_service.db_manager.lastrowid = 1
        
        theme = UnitTypeTheme(name="Test Theme", css_class_suffix="test", display_label="Test")
        
        # Mock the cache
        with patch('app.services.unit_type_theme._css_cache') as mock_cache:
            # Test create invalidates cache
            with patch.object(mock_theme_service, '_validate_for_create'):
                mock_theme_service.create(theme)
                mock_cache.invalidate.assert_called()
            
            mock_cache.reset_mock()
            
            # Test update invalidates cache
            theme.id = 1
            with patch.object(mock_theme_service, '_validate_for_update'):
                with patch.object(mock_theme_service, 'get_by_id', return_value=theme):
                    mock_theme_service.update(theme)
                    mock_cache.invalidate.assert_called()
            
            mock_cache.reset_mock()
            
            # Test delete invalidates cache
            with patch.object(mock_theme_service, '_validate_for_delete'):
                with patch.object(mock_theme_service, 'get_by_id', return_value=theme):
                    mock_theme_service.delete(1)
                    mock_cache.invalidate.assert_called()
    
    def test_css_contains_required_sections(self, mock_theme_service, sample_themes):
        """Test that generated CSS contains all required sections"""
        # Mock database result
        mock_rows = []
        for theme in sample_themes:
            row_dict = theme.to_dict()
            row_dict['usage_count'] = 0
            mock_rows.append(row_dict)
        
        mock_theme_service.db_manager.fetch_all.return_value = mock_rows
        
        with patch.object(UnitTypeTheme, 'from_sqlite_row', side_effect=sample_themes):
            css = mock_theme_service.generate_dynamic_css(use_cache=False)
        
        # Check for required sections
        assert "CSS Custom Properties for Theme System" in css
        assert ":root {" in css
        assert "Base Theme Classes" in css
        assert ".unit-themed" in css
        assert "Theme Utility Classes" in css
        assert "Accessibility Enhancements" in css
        assert "@media (prefers-reduced-motion: reduce)" in css
        assert "Print Styles" in css
        assert "@media print" in css
    
    def test_css_cache_stats(self, mock_theme_service):
        """Test CSS cache statistics"""
        stats = mock_theme_service.get_css_cache_stats()
        
        assert 'cache_size' in stats
        assert 'ttl_seconds' in stats
        assert 'cached_keys' in stats
        assert isinstance(stats['cache_size'], int)
        assert isinstance(stats['ttl_seconds'], int)
        assert isinstance(stats['cached_keys'], list)


class TestCSSTemplateSystem:
    """Test CSS template system components"""
    
    def test_css_header_generation(self):
        """Test CSS header generation"""
        service = UnitTypeThemeService()
        header = service._generate_css_header()
        
        assert isinstance(header, list)
        assert any("Dynamic Unit Type Theme CSS" in line for line in header)
        assert any("Auto-generated" in line for line in header)
        assert any("Generated:" in line for line in header)
    
    def test_css_variables_generation(self):
        """Test CSS variables generation"""
        service = UnitTypeThemeService()
        
        themes = [
            UnitTypeTheme(
                id=1,
                name="Test Theme",
                primary_color="#ff0000",
                secondary_color="#00ff00"
            )
        ]
        
        variables = service._generate_css_variables(themes)
        
        assert isinstance(variables, list)
        assert any(":root {" in line for line in variables)
        assert any("--theme-transition-duration" in line for line in variables)
        assert any("--theme-1-primary: #ff0000" in line for line in variables)
    
    def test_base_theme_classes_generation(self):
        """Test base theme classes generation"""
        service = UnitTypeThemeService()
        base_classes = service._generate_base_theme_classes()
        
        assert isinstance(base_classes, list)
        assert any(".unit-themed" in line for line in base_classes)
        assert any(".unit-box" in line for line in base_classes)
        assert any("transition:" in line for line in base_classes)
    
    def test_utility_classes_generation(self):
        """Test utility classes generation"""
        service = UnitTypeThemeService()
        utility_classes = service._generate_utility_classes()
        
        assert isinstance(utility_classes, list)
        assert any(".theme-primary-bg" in line for line in utility_classes)
        assert any("@media (max-width: 768px)" in line for line in utility_classes)
        assert any("@keyframes themesFadeIn" in line for line in utility_classes)
    
    def test_accessibility_css_generation(self):
        """Test accessibility CSS generation"""
        service = UnitTypeThemeService()
        accessibility_css = service._generate_accessibility_css()
        
        assert isinstance(accessibility_css, list)
        assert any("@media (prefers-reduced-motion: reduce)" in line for line in accessibility_css)
        assert any("@media (prefers-contrast: high)" in line for line in accessibility_css)
        assert any("outline:" in line for line in accessibility_css)
    
    def test_print_styles_generation(self):
        """Test print styles generation"""
        service = UnitTypeThemeService()
        print_styles = service._generate_print_styles()
        
        assert isinstance(print_styles, list)
        assert any("@media print" in line for line in print_styles)
        assert any("box-shadow: none" in line for line in print_styles)
        assert any("background: white" in line for line in print_styles)