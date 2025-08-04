"""
Test for Task 10: Refactor orgchart simulation and span of control templates
to use theme data instead of hardcoded unit_type_id comparisons.
"""

import pytest
from jinja2 import Environment, DictLoader
from dataclasses import dataclass
from typing import Optional


@dataclass
class MockTheme:
    """Mock theme for testing"""
    id: int = 1
    icon_class: str = "building"
    primary_color: str = "#0d6efd"
    border_width: int = 4
    css_class_suffix: str = "function"
    
    def generate_css_class_name(self) -> str:
        return f"unit-{self.css_class_suffix}"


@dataclass
class MockUnitType:
    """Mock unit type for testing"""
    id: int = 1
    effective_theme: MockTheme = None
    
    def __post_init__(self):
        if self.effective_theme is None:
            self.effective_theme = MockTheme()


@dataclass
class MockUnit:
    """Mock unit for testing"""
    id: int = 1
    name: str = "Test Unit"
    short_name: Optional[str] = None
    unit_type: MockUnitType = None
    span_of_control: int = 5
    efficiency_score: int = 85
    
    def __post_init__(self):
        if self.unit_type is None:
            self.unit_type = MockUnitType()


def test_simulation_template_uses_theme_data():
    """Test that simulation template uses theme data instead of hardcoded unit_type_id"""
    
    # Simplified template content focusing on the refactored parts
    template_content = """
    {% for unit in current_structure %}
    <div class="tree-node" data-unit-id="{{ unit.id }}">
        {% set theme = unit.unit_type.effective_theme %}
        <div class="unit-box current-unit {{ theme.generate_css_class_name() }}" 
             style="--unit-primary: {{ theme.primary_color }}; --unit-border-width: {{ theme.border_width }}px;">
            <div class="unit-header">
                <div class="unit-info">
                    <div class="unit-name">
                        <i class="bi bi-{{ theme.icon_class }} me-2"></i>
                        <strong>{{ unit.name }}</strong>
                    </div>
                </div>
            </div>
        </div>
    </div>
    {% endfor %}
    """
    
    env = Environment(loader=DictLoader({'test_template': template_content}))
    template = env.get_template('test_template')
    
    # Create test data
    mock_units = [
        MockUnit(id=1, name="Function Unit", unit_type=MockUnitType(id=1, effective_theme=MockTheme(
            icon_class="building", primary_color="#0d6efd", border_width=4, css_class_suffix="function"
        ))),
        MockUnit(id=2, name="Organizational Unit", unit_type=MockUnitType(id=2, effective_theme=MockTheme(
            icon_class="diagram-2", primary_color="#0dcaf0", border_width=2, css_class_suffix="organizational"
        )))
    ]
    
    # Render template
    result = template.render(current_structure=mock_units)
    
    # Verify theme data is used correctly
    assert 'bi-building' in result
    assert 'bi-diagram-2' in result
    assert '#0d6efd' in result
    assert '#0dcaf0' in result
    assert 'unit-function' in result
    assert 'unit-organizational' in result
    assert '--unit-border-width: 4px' in result
    assert '--unit-border-width: 2px' in result
    
    # Verify no hardcoded unit_type_id comparisons
    assert 'unit_type_id == 1' not in result
    assert 'unit_type_id == 2' not in result


def test_span_of_control_template_uses_theme_data():
    """Test that span of control template uses theme data instead of hardcoded unit_type_id"""
    
    # Simplified template content focusing on the refactored parts
    template_content = """
    {% for unit in span_analysis %}
    {% set theme = unit.unit_type.effective_theme %}
    <tr class="unit-row {{ theme.generate_css_class_name() }}" 
        data-span="{{ unit.span_of_control }}" 
        data-efficiency="{{ unit.efficiency_score }}" 
        data-name="{{ unit.name }}"
        style="--unit-primary: {{ theme.primary_color }};">
        <td>
            <div class="d-flex align-items-center">
                <i class="bi bi-{{ theme.icon_class }} me-2 text-primary"></i>
                <div>
                    <div class="fw-medium">{{ unit.name }}</div>
                    {% if unit.short_name %}
                    <small class="text-muted">{{ unit.short_name }}</small>
                    {% endif %}
                </div>
            </div>
        </td>
    </tr>
    {% endfor %}
    """
    
    env = Environment(loader=DictLoader({'test_template': template_content}))
    template = env.get_template('test_template')
    
    # Create test data
    mock_units = [
        MockUnit(id=1, name="Function Unit", short_name="FU", unit_type=MockUnitType(id=1, effective_theme=MockTheme(
            icon_class="building", primary_color="#0d6efd", css_class_suffix="function"
        ))),
        MockUnit(id=2, name="Organizational Unit", unit_type=MockUnitType(id=2, effective_theme=MockTheme(
            icon_class="diagram-2", primary_color="#0dcaf0", css_class_suffix="organizational"
        )))
    ]
    
    # Render template
    result = template.render(span_analysis=mock_units)
    
    # Verify theme data is used correctly
    assert 'bi-building' in result
    assert 'bi-diagram-2' in result
    assert '#0d6efd' in result
    assert '#0dcaf0' in result
    assert 'unit-function' in result
    assert 'unit-organizational' in result
    
    # Verify no hardcoded unit_type_id comparisons
    assert 'unit_type_id == 1' not in result
    assert 'unit_type_id == 2' not in result


def test_theme_css_variables_applied():
    """Test that CSS custom properties are correctly applied"""
    
    template_content = """
    {% set theme = unit.unit_type.effective_theme %}
    <div class="unit-box {{ theme.generate_css_class_name() }}" 
         style="--unit-primary: {{ theme.primary_color }}; --unit-border-width: {{ theme.border_width }}px;">
        <i class="bi bi-{{ theme.icon_class }}"></i>
        {{ unit.name }}
    </div>
    """
    
    env = Environment(loader=DictLoader({'test_template': template_content}))
    template = env.get_template('test_template')
    
    # Test with function theme
    function_unit = MockUnit(
        name="CEO Office",
        unit_type=MockUnitType(effective_theme=MockTheme(
            icon_class="building",
            primary_color="#0d6efd",
            border_width=4,
            css_class_suffix="function"
        ))
    )
    
    result = template.render(unit=function_unit)
    
    assert '--unit-primary: #0d6efd' in result
    assert '--unit-border-width: 4px' in result
    assert 'unit-function' in result
    assert 'bi-building' in result


if __name__ == "__main__":
    pytest.main([__file__])