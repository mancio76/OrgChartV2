"""
Unit Type Theme model
"""

import re
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from app.models.base import BaseModel, ValidationError


@dataclass
class UnitTypeTheme(BaseModel):
    """Unit Type Theme model for customizing unit type appearance"""
    
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
    
    # Computed fields (not stored in DB)
    usage_count: int = field(default=0, init=False)
    
    @property
    def computed_border_color(self) -> str:
        """Get border color, fallback to primary color"""
        return self.border_color or self.primary_color
    
    @property
    def computed_hover_shadow_color(self) -> str:
        """Get hover shadow color, fallback to primary color"""
        return self.hover_shadow_color or self.primary_color
    
    @property
    def computed_display_label_plural(self) -> str:
        """Get plural display label, fallback to singular + 's'"""
        if self.display_label_plural:
            return self.display_label_plural
        return f"{self.display_label}s" if self.display_label else ""
    
    def generate_css_class_name(self) -> str:
        """Generate CSS class name for this theme"""
        return f"unit-{self.css_class_suffix}"
    
    def to_css_variables(self) -> Dict[str, str]:
        """Generate CSS custom properties for this theme"""
        if not self.id:
            return {}
        
        return {
            f"--theme-{self.id}-primary": self.primary_color,
            f"--theme-{self.id}-secondary": self.secondary_color,
            f"--theme-{self.id}-text": self.text_color,
            f"--theme-{self.id}-border": self.computed_border_color,
            f"--theme-{self.id}-border-width": f"{self.border_width}px",
            f"--theme-{self.id}-hover-shadow": self.computed_hover_shadow_color,
        }
    
    def generate_css_rules(self) -> str:
        """Generate comprehensive CSS rules for this theme with accessibility support"""
        class_name = self.generate_css_class_name()
        
        css_rules = []
        
        # Base styles with CSS custom properties support
        base_rule = f""".{class_name} {{
    --unit-primary: {self.primary_color};
    --unit-secondary: {self.secondary_color};
    --unit-text: {self.text_color};
    --unit-border: {self.computed_border_color};
    --unit-border-width: {self.border_width}px;
    --unit-hover-shadow: {self.computed_hover_shadow_color};
    
    border: var(--unit-border-width) {self.border_style} var(--unit-border);
    background: {self.background_gradient or f'linear-gradient(135deg, #ffffff 0%, {self.secondary_color} 100%)'};
    transition: all 0.3s ease;
    position: relative;
}}"""
        css_rules.append(base_rule)
        
        # Hover effects with proper shadow opacity and accessibility considerations
        hover_rule = f""".{class_name}:hover {{
    box-shadow: 0 1rem 2rem {self._add_opacity_to_color(self.computed_hover_shadow_color, self.hover_shadow_intensity)};
    border-color: var(--unit-primary);
    transform: translateY(-2px);
}}

/* Respect user's motion preferences */
@media (prefers-reduced-motion: reduce) {{
    .{class_name} {{
        transition: none;
    }}
    
    .{class_name}:hover {{
        transform: none;
    }}
}}"""
        css_rules.append(hover_rule)
        
        # Text styling with improved readability
        text_rule = f""".{class_name} .unit-name {{
    color: var(--unit-text);
    font-weight: 600;
    line-height: 1.4;
    text-rendering: optimizeLegibility;
}}"""
        css_rules.append(text_rule)
        
        # Badge styling with accessibility improvements
        badge_rule = f""".{class_name} .badge {{
    background-color: var(--unit-primary) !important;
    color: white;
    border: none;
    font-weight: 500;
    padding: 0.375rem 0.75rem;
    border-radius: 0.25rem;
}}"""
        css_rules.append(badge_rule)
        
        # Icon styling with better visibility
        icon_rule = f""".{class_name} .bi {{
    color: var(--unit-primary);
    font-size: 1.1em;
}}"""
        css_rules.append(icon_rule)
        
        # Focus styles for keyboard navigation
        focus_rule = f""".{class_name}:focus,
.{class_name}:focus-within {{
    outline: 2px solid var(--unit-primary);
    outline-offset: 2px;
    box-shadow: 0 0 0 3px {self._add_opacity_to_color(self.primary_color, 0.3)};
}}"""
        css_rules.append(focus_rule)
        
        # High contrast mode support with enhanced accessibility
        if self.high_contrast_mode:
            contrast_rule = f""".{class_name}.high-contrast,
body.high-contrast .{class_name} {{
    border-width: calc(var(--unit-border-width) + 1px);
    background: #ffffff !important;
    color: #000000 !important;
    border-color: #000000 !important;
}}

.{class_name}.high-contrast .unit-name,
body.high-contrast .{class_name} .unit-name {{
    color: #000000 !important;
    font-weight: 700;
}}

.{class_name}.high-contrast .badge,
body.high-contrast .{class_name} .badge {{
    background-color: #000000 !important;
    color: #ffffff !important;
    border: 2px solid #000000 !important;
}}

.{class_name}.high-contrast .bi,
body.high-contrast .{class_name} .bi {{
    color: #000000 !important;
}}"""
            css_rules.append(contrast_rule)
        
        # System high contrast mode detection
        system_contrast_rule = f"""/* System high contrast mode support */
@media (prefers-contrast: high) {{
    .{class_name} {{
        border-width: calc(var(--unit-border-width) + 1px);
        background: #ffffff !important;
        color: #000000 !important;
        border-color: #000000 !important;
    }}
    
    .{class_name} .unit-name {{
        color: #000000 !important;
        font-weight: 700;
    }}
    
    .{class_name} .badge {{
        background-color: #000000 !important;
        color: #ffffff !important;
        border: 2px solid #000000 !important;
    }}
    
    .{class_name} .bi {{
        color: #000000 !important;
    }}
}}"""
        css_rules.append(system_contrast_rule)
        
        return "\n".join(css_rules)
    
    def _add_opacity_to_color(self, color: str, opacity: float) -> str:
        """Add opacity to a color value"""
        if not color:
            return f"rgba(0, 0, 0, {opacity})"
        
        # If it's already rgba, return as is
        if color.startswith('rgba'):
            return color
        
        # If it's rgb, convert to rgba
        if color.startswith('rgb'):
            return color.replace('rgb(', f'rgba(').replace(')', f', {opacity})')
        
        # If it's hex, convert to rgba
        if color.startswith('#'):
            try:
                # Remove # and convert to RGB
                hex_color = color.lstrip('#')
                if len(hex_color) == 3:
                    hex_color = ''.join([c*2 for c in hex_color])
                
                r = int(hex_color[0:2], 16)
                g = int(hex_color[2:4], 16)
                b = int(hex_color[4:6], 16)
                
                return f"rgba({r}, {g}, {b}, {opacity})"
            except ValueError:
                return f"rgba(0, 0, 0, {opacity})"
        
        # For named colors or other formats, wrap in rgba with fallback
        return f"rgba(0, 0, 0, {opacity})"
    
    def validate(self) -> List[ValidationError]:
        """Validate theme data"""
        errors = []
        
        # Required fields validation
        if not self.name or not self.name.strip():
            errors.append(ValidationError("name", "Nome del tema è obbligatorio"))
        
        if not self.display_label or not self.display_label.strip():
            errors.append(ValidationError("display_label", "Etichetta di visualizzazione è obbligatoria"))
        
        if not self.css_class_suffix or not self.css_class_suffix.strip():
            errors.append(ValidationError("css_class_suffix", "Suffisso classe CSS è obbligatorio"))
        
        # Color validation
        color_fields = [
            ("primary_color", self.primary_color),
            ("secondary_color", self.secondary_color),
            ("text_color", self.text_color),
        ]
        
        if self.border_color:
            color_fields.append(("border_color", self.border_color))
        
        if self.hover_shadow_color:
            color_fields.append(("hover_shadow_color", self.hover_shadow_color))
        
        for field_name, color_value in color_fields:
            if not self._is_valid_color(color_value):
                errors.append(ValidationError(field_name, f"Colore non valido: {color_value}"))
        
        # Icon class validation
        if not self._is_valid_icon_class(self.icon_class):
            errors.append(ValidationError("icon_class", f"Classe icona non valida: {self.icon_class}"))
        
        # CSS class suffix validation
        if not self._is_valid_css_class_suffix(self.css_class_suffix):
            errors.append(ValidationError("css_class_suffix", "Suffisso classe CSS deve contenere solo lettere, numeri e trattini"))
        
        # Border width validation
        if self.border_width < 0 or self.border_width > 20:
            errors.append(ValidationError("border_width", "Larghezza bordo deve essere tra 0 e 20 pixel"))
        
        # Border style validation
        valid_border_styles = ["solid", "dashed", "dotted", "double", "groove", "ridge", "inset", "outset"]
        if self.border_style not in valid_border_styles:
            errors.append(ValidationError("border_style", f"Stile bordo non valido. Valori consentiti: {', '.join(valid_border_styles)}"))
        
        # Hover shadow intensity validation
        if self.hover_shadow_intensity < 0 or self.hover_shadow_intensity > 1:
            errors.append(ValidationError("hover_shadow_intensity", "Intensità ombra hover deve essere tra 0 e 1"))
        
        # Background gradient validation
        if self.background_gradient and not self._is_valid_css_gradient(self.background_gradient):
            errors.append(ValidationError("background_gradient", "Gradiente CSS non valido"))
        
        # Name uniqueness validation (will be checked at service level)
        if self.name and len(self.name.strip()) > 100:
            errors.append(ValidationError("name", "Nome del tema troppo lungo (massimo 100 caratteri)"))
        
        # Description length validation
        if self.description and len(self.description) > 500:
            errors.append(ValidationError("description", "Descrizione troppo lunga (massimo 500 caratteri)"))
        
        # Display label length validation
        if self.display_label and len(self.display_label) > 50:
            errors.append(ValidationError("display_label", "Etichetta di visualizzazione troppo lunga (massimo 50 caratteri)"))
        
        if self.display_label_plural and len(self.display_label_plural) > 50:
            errors.append(ValidationError("display_label_plural", "Etichetta plurale troppo lunga (massimo 50 caratteri)"))
        
        # Emoji validation
        if not self._is_valid_emoji(self.emoji_fallback):
            errors.append(ValidationError("emoji_fallback", "Emoji fallback non valido"))
        
        # CSS class suffix additional validation
        if self.css_class_suffix and len(self.css_class_suffix) > 30:
            errors.append(ValidationError("css_class_suffix", "Suffisso classe CSS troppo lungo (massimo 30 caratteri)"))
        
        # Color contrast validation for accessibility
        contrast_errors = self._validate_color_contrast()
        errors.extend(contrast_errors)
        
        return errors
    
    def _is_valid_color(self, color: str) -> bool:
        """Validate color format (hex, rgb, rgba, hsl, hsla, named colors)"""
        if not color:
            return False
        
        color = color.strip().lower()
        
        # Hex colors - support 3 and 6 digit formats
        if re.match(r'^#([0-9a-f]{3}|[0-9a-f]{6})$', color):
            return True
        
        # RGB/RGBA colors - validate ranges and handle decimals
        rgb_match = re.match(r'^rgba?\(\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*(?:,\s*([0-9.]+))?\s*\)$', color)
        if rgb_match:
            try:
                r, g, b, a = rgb_match.groups()
                r, g, b = float(r), float(g), float(b)
                if (0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255):
                    if a is None or (0 <= float(a) <= 1):
                        return True
            except ValueError:
                return False
        
        # HSL/HSLA colors - validate ranges and handle decimals
        hsl_match = re.match(r'^hsla?\(\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)%\s*,\s*(\d+(?:\.\d+)?)%\s*(?:,\s*([0-9.]+))?\s*\)$', color)
        if hsl_match:
            try:
                h, s, l, a = hsl_match.groups()
                h, s, l = float(h), float(s), float(l)
                if (0 <= h <= 360 and 0 <= s <= 100 and 0 <= l <= 100):
                    if a is None or (0 <= float(a) <= 1):
                        return True
            except ValueError:
                return False
        
        # CSS color keywords (extended set)
        named_colors = {
            'aliceblue', 'antiquewhite', 'aqua', 'aquamarine', 'azure', 'beige', 'bisque', 'black',
            'blanchedalmond', 'blue', 'blueviolet', 'brown', 'burlywood', 'cadetblue', 'chartreuse',
            'chocolate', 'coral', 'cornflowerblue', 'cornsilk', 'crimson', 'cyan', 'darkblue',
            'darkcyan', 'darkgoldenrod', 'darkgray', 'darkgrey', 'darkgreen', 'darkkhaki',
            'darkmagenta', 'darkolivegreen', 'darkorange', 'darkorchid', 'darkred', 'darksalmon',
            'darkseagreen', 'darkslateblue', 'darkslategray', 'darkslategrey', 'darkturquoise',
            'darkviolet', 'deeppink', 'deepskyblue', 'dimgray', 'dimgrey', 'dodgerblue',
            'firebrick', 'floralwhite', 'forestgreen', 'fuchsia', 'gainsboro', 'ghostwhite',
            'gold', 'goldenrod', 'gray', 'grey', 'green', 'greenyellow', 'honeydew', 'hotpink',
            'indianred', 'indigo', 'ivory', 'khaki', 'lavender', 'lavenderblush', 'lawngreen',
            'lemonchiffon', 'lightblue', 'lightcoral', 'lightcyan', 'lightgoldenrodyellow',
            'lightgray', 'lightgrey', 'lightgreen', 'lightpink', 'lightsalmon', 'lightseagreen',
            'lightskyblue', 'lightslategray', 'lightslategrey', 'lightsteelblue', 'lightyellow',
            'lime', 'limegreen', 'linen', 'magenta', 'maroon', 'mediumaquamarine', 'mediumblue',
            'mediumorchid', 'mediumpurple', 'mediumseagreen', 'mediumslateblue', 'mediumspringgreen',
            'mediumturquoise', 'mediumvioletred', 'midnightblue', 'mintcream', 'mistyrose',
            'moccasin', 'navajowhite', 'navy', 'oldlace', 'olive', 'olivedrab', 'orange',
            'orangered', 'orchid', 'palegoldenrod', 'palegreen', 'paleturquoise', 'palevioletred',
            'papayawhip', 'peachpuff', 'peru', 'pink', 'plum', 'powderblue', 'purple', 'red',
            'rosybrown', 'royalblue', 'saddlebrown', 'salmon', 'sandybrown', 'seagreen',
            'seashell', 'sienna', 'silver', 'skyblue', 'slateblue', 'slategray', 'slategrey',
            'snow', 'springgreen', 'steelblue', 'tan', 'teal', 'thistle', 'tomato', 'turquoise',
            'violet', 'wheat', 'white', 'whitesmoke', 'yellow', 'yellowgreen', 'transparent',
            'currentcolor', 'inherit', 'initial', 'unset'
        }
        if color in named_colors:
            return True
        
        return False
    
    def _is_valid_icon_class(self, icon_class: str) -> bool:
        """Validate Bootstrap icon class format"""
        if not icon_class:
            return False
        
        icon_class = icon_class.strip()
        
        # Bootstrap icons are typically alphanumeric with hyphens, starting with letter
        if not re.match(r'^[a-z][a-z0-9-]*$', icon_class):
            return False
        
        # Check length constraints
        if len(icon_class) < 2 or len(icon_class) > 50:
            return False
        
        # Ensure it doesn't start or end with hyphen
        if icon_class.startswith('-') or icon_class.endswith('-'):
            return False
        
        # Ensure no consecutive hyphens
        if '--' in icon_class:
            return False
        
        return True
    
    def _is_valid_css_class_suffix(self, suffix: str) -> bool:
        """Validate CSS class suffix format"""
        if not suffix:
            return False
        
        suffix = suffix.strip().lower()
        
        # CSS class names can contain letters, numbers, hyphens, and underscores
        # but should start with a letter
        if not re.match(r'^[a-z][a-z0-9-_]*$', suffix):
            return False
        
        # Ensure it doesn't start or end with hyphen or underscore
        if suffix.startswith('-') or suffix.endswith('-') or suffix.startswith('_') or suffix.endswith('_'):
            return False
        
        return True
    
    def _is_valid_css_gradient(self, gradient: str) -> bool:
        """Enhanced validation for CSS gradient syntax"""
        if not gradient:
            return False
        
        gradient = gradient.strip()
        
        # Check for basic gradient functions
        gradient_functions = ['linear-gradient', 'radial-gradient', 'conic-gradient', 'repeating-linear-gradient', 'repeating-radial-gradient']
        
        # Check if it starts with a valid gradient function and has proper parentheses
        for func in gradient_functions:
            if gradient.lower().startswith(func + '('):
                # Check for balanced parentheses
                if gradient.count('(') == gradient.count(')') and gradient.endswith(')'):
                    # Basic syntax check - should contain at least one color
                    gradient_content = gradient[len(func)+1:-1].strip()
                    if gradient_content:
                        # Check for at least one color-like pattern (hex, rgb, named color)
                        color_pattern = r'(#[0-9a-f]{3,6}|rgba?\([^)]+\)|hsla?\([^)]+\)|[a-z]+)'
                        if re.search(color_pattern, gradient_content, re.IGNORECASE):
                            return True
        
        return False
    
    def _is_valid_emoji(self, emoji: str) -> bool:
        """Validate emoji format"""
        if not emoji:
            return False
        
        emoji = emoji.strip()
        
        # Common emoji ranges
        emoji_ranges = [
            (0x1F600, 0x1F64F),  # Emoticons
            (0x1F300, 0x1F5FF),  # Misc Symbols and Pictographs
            (0x1F680, 0x1F6FF),  # Transport and Map
            (0x1F1E0, 0x1F1FF),  # Regional indicators
            (0x2600, 0x26FF),    # Misc symbols
            (0x2700, 0x27BF),    # Dingbats
            (0x1F900, 0x1F9FF),  # Supplemental Symbols and Pictographs
        ]
        
        # Check if it's a single character and appears to be an emoji
        if len(emoji) == 1:
            code_point = ord(emoji)
            for start, end in emoji_ranges:
                if start <= code_point <= end:
                    return True
        
        # Allow multi-character emojis (like skin tone modifiers) but be more strict
        if 2 <= len(emoji) <= 10:
            # Check if it contains at least one emoji-like character
            for char in emoji:
                code_point = ord(char)
                for start, end in emoji_ranges:
                    if start <= code_point <= end:
                        return True
        
        return False
    
    def _validate_color_contrast(self) -> List[ValidationError]:
        """Enhanced color contrast validation for accessibility compliance"""
        errors = []
        
        try:
            # Convert colors to RGB for contrast calculation
            primary_rgb = self._color_to_rgb(self.primary_color)
            secondary_rgb = self._color_to_rgb(self.secondary_color)
            text_rgb = self._color_to_rgb(self.text_color)
            white_rgb = (255, 255, 255)
            
            # Validate primary background vs text color
            if primary_rgb and text_rgb:
                contrast_ratio = self._calculate_contrast_ratio(primary_rgb, text_rgb)
                
                # WCAG AA requires 4.5:1 for normal text, 3:1 for large text
                # We use 4.5:1 as the standard for better accessibility
                if contrast_ratio < 4.5:
                    errors.append(ValidationError(
                        "text_color", 
                        f"Contrasto insufficiente tra colore primario e testo (ratio: {contrast_ratio:.2f}, minimo WCAG AA: 4.5)"
                    ))
            
            # Validate secondary background vs text color
            if secondary_rgb and text_rgb:
                contrast_ratio = self._calculate_contrast_ratio(secondary_rgb, text_rgb)
                
                if contrast_ratio < 4.5:
                    errors.append(ValidationError(
                        "text_color", 
                        f"Contrasto insufficiente tra colore secondario e testo (ratio: {contrast_ratio:.2f}, minimo WCAG AA: 4.5)"
                    ))
            
            # Validate primary background vs white text (for badges)
            if primary_rgb:
                contrast_ratio = self._calculate_contrast_ratio(primary_rgb, white_rgb)
                
                if contrast_ratio < 3.0:  # More lenient for badges with larger text
                    errors.append(ValidationError(
                        "primary_color", 
                        f"Contrasto insufficiente tra colore primario e testo bianco per badge (ratio: {contrast_ratio:.2f}, minimo: 3.0)"
                    ))
            
            # Additional validation for high contrast mode
            if self.high_contrast_mode:
                # In high contrast mode, we need even better contrast ratios
                if primary_rgb and text_rgb:
                    contrast_ratio = self._calculate_contrast_ratio(primary_rgb, text_rgb)
                    if contrast_ratio < 7.0:  # WCAG AAA standard
                        errors.append(ValidationError(
                            "text_color", 
                            f"Modalità alto contrasto richiede ratio minimo 7.0 (attuale: {contrast_ratio:.2f})"
                        ))
        
        except Exception as e:
            # Log the error but don't fail validation completely
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Error during color contrast validation: {e}")
        
        return errors
    
    def _color_to_rgb(self, color: str) -> Optional[tuple]:
        """Enhanced color to RGB conversion supporting multiple formats"""
        if not color:
            return None
        
        color = color.strip().lower()
        
        # Handle hex colors
        if color.startswith('#'):
            return self._hex_to_rgb(color)
        
        # Handle rgb/rgba colors
        if color.startswith('rgb'):
            return self._rgb_string_to_rgb(color)
        
        # Handle named colors (basic set)
        named_colors = {
            'white': (255, 255, 255),
            'black': (0, 0, 0),
            'red': (255, 0, 0),
            'green': (0, 128, 0),
            'blue': (0, 0, 255),
            'yellow': (255, 255, 0),
            'cyan': (0, 255, 255),
            'magenta': (255, 0, 255),
            'silver': (192, 192, 192),
            'gray': (128, 128, 128),
            'maroon': (128, 0, 0),
            'olive': (128, 128, 0),
            'lime': (0, 255, 0),
            'aqua': (0, 255, 255),
            'teal': (0, 128, 128),
            'navy': (0, 0, 128),
            'fuchsia': (255, 0, 255),
            'purple': (128, 0, 128)
        }
        
        return named_colors.get(color)
    
    def _hex_to_rgb(self, hex_color: str) -> Optional[tuple]:
        """Convert hex color to RGB tuple"""
        if not hex_color or not hex_color.startswith('#'):
            return None
        
        try:
            hex_color = hex_color.lstrip('#')
            if len(hex_color) == 3:
                hex_color = ''.join([c*2 for c in hex_color])
            
            if len(hex_color) == 6:
                return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        except ValueError:
            pass
        
        return None
    
    def _rgb_string_to_rgb(self, rgb_string: str) -> Optional[tuple]:
        """Convert rgb/rgba string to RGB tuple"""
        try:
            # Extract numbers from rgb(r,g,b) or rgba(r,g,b,a)
            import re
            numbers = re.findall(r'(\d+(?:\.\d+)?)', rgb_string)
            if len(numbers) >= 3:
                r, g, b = float(numbers[0]), float(numbers[1]), float(numbers[2])
                if 0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255:
                    return (int(r), int(g), int(b))
        except (ValueError, IndexError):
            pass
        
        return None
    
    def _calculate_contrast_ratio(self, rgb1: tuple, rgb2: tuple) -> float:
        """Calculate WCAG contrast ratio between two RGB colors"""
        def luminance(rgb):
            """Calculate relative luminance"""
            r, g, b = [x / 255.0 for x in rgb]
            
            def gamma_correct(c):
                return c / 12.92 if c <= 0.03928 else pow((c + 0.055) / 1.055, 2.4)
            
            r, g, b = map(gamma_correct, [r, g, b])
            return 0.2126 * r + 0.7152 * g + 0.0722 * b
        
        l1 = luminance(rgb1)
        l2 = luminance(rgb2)
        
        # Ensure l1 is the lighter color
        if l1 < l2:
            l1, l2 = l2, l1
        
        return (l1 + 0.05) / (l2 + 0.05)
    
    @classmethod
    def from_sqlite_row(cls, row):
        """Create UnitTypeTheme instance from SQLite row"""
        if row is None:
            return None
        
        data = dict(row)
        
        # Extract computed fields (init=False fields)
        computed_fields = {
            'usage_count': data.pop('usage_count', 0)
        }
        
        # Create instance with regular fields
        instance = cls.from_dict(data)
        
        # Set computed fields
        for field_name, value in computed_fields.items():
            if hasattr(instance, field_name):
                setattr(instance, field_name, int(value) if value is not None else 0)
        
        return instance
    
    def get_accessibility_info(self) -> Dict[str, Any]:
        """Get accessibility information for this theme"""
        info = {
            'high_contrast_mode': self.high_contrast_mode,
            'contrast_ratios': {},
            'accessibility_score': 0,
            'recommendations': []
        }
        
        try:
            # Calculate contrast ratios
            primary_rgb = self._color_to_rgb(self.primary_color)
            secondary_rgb = self._color_to_rgb(self.secondary_color)
            text_rgb = self._color_to_rgb(self.text_color)
            white_rgb = (255, 255, 255)
            
            if primary_rgb and text_rgb:
                ratio = self._calculate_contrast_ratio(primary_rgb, text_rgb)
                info['contrast_ratios']['primary_text'] = round(ratio, 2)
                
            if secondary_rgb and text_rgb:
                ratio = self._calculate_contrast_ratio(secondary_rgb, text_rgb)
                info['contrast_ratios']['secondary_text'] = round(ratio, 2)
                
            if primary_rgb:
                ratio = self._calculate_contrast_ratio(primary_rgb, white_rgb)
                info['contrast_ratios']['primary_white'] = round(ratio, 2)
            
            # Calculate accessibility score (0-100)
            score = 0
            
            # Base score for having contrast ratios
            if info['contrast_ratios'].get('primary_text', 0) >= 4.5:
                score += 30
            elif info['contrast_ratios'].get('primary_text', 0) >= 3.0:
                score += 15
                
            if info['contrast_ratios'].get('secondary_text', 0) >= 4.5:
                score += 30
            elif info['contrast_ratios'].get('secondary_text', 0) >= 3.0:
                score += 15
                
            if info['contrast_ratios'].get('primary_white', 0) >= 3.0:
                score += 20
            elif info['contrast_ratios'].get('primary_white', 0) >= 2.0:
                score += 10
            
            # Bonus for high contrast mode
            if self.high_contrast_mode:
                score += 20
            
            info['accessibility_score'] = min(score, 100)
            
            # Generate recommendations
            if info['contrast_ratios'].get('primary_text', 0) < 4.5:
                info['recommendations'].append('Migliorare il contrasto tra colore primario e testo')
                
            if info['contrast_ratios'].get('secondary_text', 0) < 4.5:
                info['recommendations'].append('Migliorare il contrasto tra colore secondario e testo')
                
            if info['contrast_ratios'].get('primary_white', 0) < 3.0:
                info['recommendations'].append('Migliorare il contrasto per i badge con testo bianco')
                
            if not self.high_contrast_mode and score < 80:
                info['recommendations'].append('Considerare l\'attivazione della modalità alto contrasto')
        
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Error calculating accessibility info: {e}")
            info['error'] = 'Errore nel calcolo delle informazioni di accessibilità'
        
        return info
    
    def get_performance_info(self) -> Dict[str, Any]:
        """Get performance information for this theme"""
        css_rules = self.generate_css_rules()
        
        return {
            'css_size_bytes': len(css_rules.encode('utf-8')),
            'css_lines': len(css_rules.split('\n')),
            'has_gradients': bool(self.background_gradient),
            'has_shadows': self.hover_shadow_intensity > 0,
            'complexity_score': self._calculate_complexity_score(),
            'cache_key': f"theme_{self.id}_{hash(css_rules) % 10000}"
        }
    
    def _calculate_complexity_score(self) -> int:
        """Calculate theme complexity score (0-100) for performance estimation"""
        score = 0
        
        # Base complexity
        score += 10
        
        # Gradient adds complexity
        if self.background_gradient:
            score += 20
            
        # Shadows add complexity
        if self.hover_shadow_intensity > 0:
            score += 15
            
        # High contrast mode adds complexity
        if self.high_contrast_mode:
            score += 25
            
        # Border styles other than solid add complexity
        if self.border_style != 'solid':
            score += 10
            
        # Thick borders add complexity
        if self.border_width > 3:
            score += 10
            
        # Custom colors (non-standard) add complexity
        standard_colors = ['#0dcaf0', '#f0fdff', '#0d6efd', '#f8f9ff']
        if self.primary_color not in standard_colors:
            score += 5
            
        return min(score, 100)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        result = super().to_dict()
        
        # Add computed properties
        result['computed_border_color'] = self.computed_border_color
        result['computed_hover_shadow_color'] = self.computed_hover_shadow_color
        result['computed_display_label_plural'] = self.computed_display_label_plural
        result['css_class_name'] = self.generate_css_class_name()
        
        # Add accessibility and performance info
        result['accessibility_info'] = self.get_accessibility_info()
        result['performance_info'] = self.get_performance_info()
        
        return result