"""
Shared Jinja2 templates instance with registered helper functions
"""

from fastapi.templating import Jinja2Templates

# Create templates instance
templates = Jinja2Templates(directory="templates")

# Register template helper functions for theme-driven rendering
from app.utils.template_helpers import TEMPLATE_HELPERS
for helper_name, helper_func in TEMPLATE_HELPERS.items():
    templates.env.globals[helper_name] = helper_func