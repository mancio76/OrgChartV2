"""
Tests for Jinja2 template helper functions
"""

import pytest
from unittest.mock import Mock, patch
from app.utils.template_helpers import (
    get_unit_theme_data,
    render_unit_icon,
    get_unit_css_classes,
    get_unit_css_variables,
    render_unit_css_variables,
    get_unit_theme_badge_text,
    get_unit_theme_emoji,
    get_unit_theme_colors,
    is_unit_theme_high_contrast,
    get_theme_css_class_by_id
)
from app.models.unit import Unit
from app.models.unit_type import UnitType
from app.models.unit_type_theme import UnitTypeTheme


@pytest.fixture
def mock_theme():
    """Create a mock theme for testing"""
    return UnitTypeTheme(
        id=1,
        name="Test Theme",
        icon_class="building",
        emoji_fallback="🏢",
        primary_color="#0d6efd",
        secondary_color="#f8f9ff",
        text_color="#0d6efd",
        border_color="#0d6efd",
        border_width=4,
        border_style="solid",
        css_class_suffix="test",
        display_label="Test Unit",
        high_contrast_mode=False
    )


@pytest.fixture
def mock_unit_type(mock_theme):
    """Create a mock unit type with theme"""
    unit_type = UnitType(
        id=1,
        name="Test Unit Type",
        theme_id=1
    )
    unit_type.theme = mock_theme
    return unit_type


@pytest.fixture
def mock_unit(mock_unit_type):
    """Create a mock unit with unit type and theme"""
    unit = Unit(
        id=1,
        name="Test Unit",
        unit_type_id=1
    )
    unit.unit_type = mock_unit_type
    return unit


class TestGetUnitThemeData:
    """Test get_unit_theme_data function"""
    
    def test_get_theme_from_unit_with_unit_type(self, mock_unit, mock_theme):
        """Test getting theme data from unit with unit_type"""
        result = get_unit_theme_data(mock_unit)
        assert result == mock_theme
        assert result.name == "Test Theme"
    
    @patch('app.utils.template_helpers.UnitTypeThemeService')
    def test_get_default_theme_when_no_unit(self, mock_service):
        """Test getting default theme when no unit provided"""
        mock_default_theme = UnitTypeTheme(name="Default Theme")
        mock_service.return_value.get_default_theme.return_value = mock_default_theme
        
        result = get_unit_theme_data(None)
        assert result == mock_default_theme
    
    @patch('app.utils.template_helpers.UnitTypeService')
    @patch('app.utils.template_helpers.UnitTypeThemeService')
    def test_fallback_to_unit_type_service(self, mock_theme_service, mock_unit_type_service):
        """Test fallback to unit type service when unit has no unit_type"""
        mock_unit = Unit(id=1, name="Test Unit", unit_type_id=1)
        mock_theme = UnitTypeTheme(name="Fallback Theme")
        mock_unit_type = UnitType(id=1, name="Test Type")
        mock_unit_type.theme = mock_theme
        
        mock_unit_type_service.return_value.get_by_id.return_value = mock_unit_type
        
        result = get_unit_theme_data(mock_unit)
        mock_unit_type_service.return_value.get_by_id.assert_called_once_with(1)


class TestRenderUnitIcon:
    """Test render_unit_icon function"""
    
    def test_render_icon_with_default_classes(self, mock_unit):
        """Test rendering icon with default CSS classes"""
        result = render_unit_icon(mock_unit)
        expected = '<i class="bi bi-building" aria-hidden="true"></i>'
        assert result == expected
    
    def test_render_icon_with_custom_classes(self, mock_unit):
        """Test rendering icon with custom CSS classes"""
        result = render_unit_icon(mock_unit, "custom-icon")
        expected = '<i class="custom-icon bi-building" aria-hidden="true"></i>'
        assert result == expected


class TestGetUnitCssClasses:
    """Test get_unit_css_classes function"""
    
    def test_get_css_classes_with_default_base(self, mock_unit):
        """Test getting CSS classes with default base classes"""
        result = get_unit_css_classes(mock_unit)
        expected = "unit-box unit-test"
        assert result == expected
    
    def test_get_css_classes_with_custom_base(self, mock_unit):
        """Test getting CSS classes with custom base classes"""
        result = get_unit_css_classes(mock_unit, "custom-base another-class")
        expected = "custom-base another-class unit-test"
        assert result == expected


class TestGetUnitCssVariables:
    """Test get_unit_css_variables function"""
    
    def test_get_css_variables(self, mock_unit, mock_theme):
        """Test getting CSS variables from theme"""
        result = get_unit_css_variables(mock_unit)
        
        # Check that both theme variables and unit-specific variables are included
        assert '--theme-1-primary' in result
        assert '--unit-primary' in result
        assert result['--unit-primary'] == '#0d6efd'
        assert result['--unit-border-width'] == '4px'


class TestRenderUnitCssVariables:
    """Test render_unit_css_variables function"""
    
    def test_render_css_variables_as_style_string(self, mock_unit):
        """Test rendering CSS variables as style attribute string"""
        result = render_unit_css_variables(mock_unit)
        
        # Should contain CSS variable declarations
        assert '--theme-1-primary: #0d6efd' in result
        assert '--unit-primary: #0d6efd' in result
        assert '--unit-border-width: 4px' in result
        
        # Should be properly formatted as CSS style string
        assert '; ' in result  # Variables should be separated by semicolons


class TestGetUnitThemeBadgeText:
    """Test get_unit_theme_badge_text function"""
    
    def test_get_badge_text(self, mock_unit):
        """Test getting badge text from theme"""
        result = get_unit_theme_badge_text(mock_unit)
        assert result == "Test Unit"


class TestGetUnitThemeEmoji:
    """Test get_unit_theme_emoji function"""
    
    def test_get_emoji(self, mock_unit):
        """Test getting emoji from theme"""
        result = get_unit_theme_emoji(mock_unit)
        assert result == "🏢"


class TestGetUnitThemeColors:
    """Test get_unit_theme_colors function"""
    
    def test_get_colors(self, mock_unit):
        """Test getting color palette from theme"""
        result = get_unit_theme_colors(mock_unit)
        
        expected = {
            'primary': '#0d6efd',
            'secondary': '#f8f9ff',
            'text': '#0d6efd',
            'border': '#0d6efd',
            'hover_shadow': '#0d6efd',
        }
        
        assert result == expected


class TestIsUnitThemeHighContrast:
    """Test is_unit_theme_high_contrast function"""
    
    def test_high_contrast_false(self, mock_unit):
        """Test high contrast mode detection when false"""
        result = is_unit_theme_high_contrast(mock_unit)
        assert result is False
    
    def test_high_contrast_true(self, mock_unit, mock_theme):
        """Test high contrast mode detection when true"""
        mock_theme.high_contrast_mode = True
        result = is_unit_theme_high_contrast(mock_unit)
        assert result is True


class TestGetThemeCssClassById:
    """Test get_theme_css_class_by_id function"""
    
    @patch('app.utils.template_helpers.UnitTypeThemeService')
    def test_get_css_class_by_valid_id(self, mock_service):
        """Test getting CSS class by valid theme ID"""
        mock_theme = UnitTypeTheme(css_class_suffix="test")
        mock_service.return_value.get_by_id.return_value = mock_theme
        
        result = get_theme_css_class_by_id(1)
        assert result == "unit-test"
        mock_service.return_value.get_by_id.assert_called_once_with(1)
    
    @patch('app.utils.template_helpers.UnitTypeThemeService')
    def test_get_default_css_class_when_no_id(self, mock_service):
        """Test getting default CSS class when no ID provided"""
        mock_default_theme = UnitTypeTheme(css_class_suffix="default")
        mock_service.return_value.get_default_theme.return_value = mock_default_theme
        
        result = get_theme_css_class_by_id(None)
        assert result == "unit-default"
        mock_service.return_value.get_default_theme.assert_called_once()
    
    @patch('app.utils.template_helpers.UnitTypeThemeService')
    def test_fallback_to_default_when_theme_not_found(self, mock_service):
        """Test fallback to default theme when theme ID not found"""
        mock_default_theme = UnitTypeTheme(css_class_suffix="default")
        mock_service.return_value.get_by_id.return_value = None
        mock_service.return_value.get_default_theme.return_value = mock_default_theme
        
        result = get_theme_css_class_by_id(999)
        assert result == "unit-default"
        mock_service.return_value.get_by_id.assert_called_once_with(999)
        mock_service.return_value.get_default_theme.assert_called_once()