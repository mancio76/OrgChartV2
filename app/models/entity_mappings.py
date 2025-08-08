"""
Entity field mappings and configurations for import/export operations.

This module defines the field mappings, validation rules, and dependency
relationships for all entity types in the system.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable, Set, Union
from datetime import date, datetime
import json


@dataclass
class FieldMapping:
    """Defines mapping and validation for a single field."""
    name: str
    data_type: type
    required: bool = False
    nullable: bool = True
    default_value: Any = None
    validator: Optional[Callable[[Any], bool]] = None
    transformer: Optional[Callable[[Any], Any]] = None
    description: str = ""
    
    def validate(self, value: Any) -> bool:
        """Validate a field value."""
        if value is None:
            return self.nullable
        
        # Skip type validation if there's a transformer (it changes the type)
        if not self.transformer and not isinstance(value, self.data_type) and value is not None:
            return False
        
        if self.validator:
            return self.validator(value)
        
        return True
    
    def transform(self, value: Any) -> Any:
        """Transform a field value."""
        if value is None:
            return self.default_value
        
        if self.transformer:
            return self.transformer(value)
        
        return value


@dataclass
class EntityMapping:
    """Defines complete mapping configuration for an entity type."""
    entity_type: str
    table_name: str
    fields: Dict[str, FieldMapping]
    foreign_keys: Dict[str, str] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    unique_constraints: List[List[str]] = field(default_factory=list)
    csv_filename: str = ""
    json_key: str = ""
    
    def __post_init__(self):
        """Set default values after initialization."""
        if not self.csv_filename:
            self.csv_filename = f"{self.entity_type}.csv"
        if not self.json_key:
            self.json_key = self.entity_type


# Field transformers and validators
def parse_json_field(value: str) -> List[Dict[str, Any]]:
    """Parse JSON string field (used for aliases)."""
    if not value or value.strip() == "":
        return []
    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, list) else [parsed]
    except (json.JSONDecodeError, TypeError):
        return []


def serialize_json_field(value: List[Dict[str, Any]]) -> str:
    """Serialize list to JSON string."""
    if not value:
        return "[]"
    return json.dumps(value, ensure_ascii=False)


def parse_date(value: str) -> Optional[date]:
    """Parse date string in various formats."""
    if not value or value.strip() == "":
        return None
    
    formats = ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y-%m-%d %H:%M:%S"]
    for fmt in formats:
        try:
            parsed = datetime.strptime(value.strip(), fmt)
            return parsed.date()
        except ValueError:
            continue
    
    raise ValueError(f"Unable to parse date: {value}")


def parse_datetime(value: str) -> Optional[datetime]:
    """Parse datetime string in various formats."""
    if not value or value.strip() == "":
        return None
    
    formats = ["%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"]
    for fmt in formats:
        try:
            return datetime.strptime(value.strip(), fmt)
        except ValueError:
            continue
    
    raise ValueError(f"Unable to parse datetime: {value}")


def parse_boolean(value: str) -> bool:
    """Parse boolean from string."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes", "on", "t", "y")
    return bool(value)


def parse_float(value: Union[str, float, int]) -> float:
    """Parse float with validation."""
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        if not value or value.strip() == "":
            return 0.0
        return float(value)
    return float(value)


def validate_percentage(value: float) -> bool:
    """Validate percentage value (0.0 to 1.0)."""
    return 0.0 <= value <= 1.0


def validate_positive_int(value: int) -> bool:
    """Validate positive integer."""
    return value > 0


def validate_non_negative_int(value: int) -> bool:
    """Validate non-negative integer."""
    return value >= 0


# Entity mappings configuration
ENTITY_MAPPINGS: Dict[str, EntityMapping] = {
    "unit_types": EntityMapping(
        entity_type="unit_types",
        table_name="unit_types",
        fields={
            "id": FieldMapping("id", int, required=False, nullable=True),
            "name": FieldMapping("name", str, required=True, nullable=False),
            "short_name": FieldMapping("short_name", str, required=True, nullable=False),
            "aliases": FieldMapping(
                "aliases", str, required=False, nullable=True,
                transformer=parse_json_field,
                default_value="[]"
            ),
            "level": FieldMapping(
                "level", int, required=False, nullable=True,
                validator=validate_positive_int,
                default_value=1
            ),
            "theme_id": FieldMapping("theme_id", int, required=False, nullable=True)
        },
        foreign_keys={"theme_id": "unit_type_themes"},
        dependencies=[],
        unique_constraints=[["name"], ["short_name"]]
    ),
    
    "unit_type_themes": EntityMapping(
        entity_type="unit_type_themes",
        table_name="unit_type_themes",
        fields={
            "id": FieldMapping("id", int, required=False, nullable=True),
            "name": FieldMapping("name", str, required=True, nullable=False),
            "description": FieldMapping("description", str, required=False, nullable=True),
            "icon_class": FieldMapping("icon_class", str, required=False, nullable=True),
            "emoji_fallback": FieldMapping("emoji_fallback", str, required=False, nullable=True),
            "primary_color": FieldMapping("primary_color", str, required=False, nullable=True),
            "secondary_color": FieldMapping("secondary_color", str, required=False, nullable=True),
            "text_color": FieldMapping("text_color", str, required=False, nullable=True),
            "display_label": FieldMapping("display_label", str, required=False, nullable=True),
            "is_active": FieldMapping(
                "is_active", bool, required=False, nullable=False,
                transformer=parse_boolean,
                default_value=True
            )
        },
        dependencies=[],
        unique_constraints=[["name"]]
    ),
    
    "units": EntityMapping(
        entity_type="units",
        table_name="units",
        fields={
            "id": FieldMapping("id", int, required=False, nullable=True),
            "name": FieldMapping("name", str, required=True, nullable=False),
            "short_name": FieldMapping("short_name", str, required=True, nullable=False),
            "aliases": FieldMapping(
                "aliases", str, required=False, nullable=True,
                transformer=parse_json_field,
                default_value="[]"
            ),
            "unit_type_id": FieldMapping("unit_type_id", int, required=True, nullable=False),
            "parent_unit_id": FieldMapping("parent_unit_id", int, required=False, nullable=True),
            "start_date": FieldMapping(
                "start_date", date, required=False, nullable=True,
                transformer=parse_date
            ),
            "end_date": FieldMapping(
                "end_date", date, required=False, nullable=True,
                transformer=parse_date
            )
        },
        foreign_keys={
            "unit_type_id": "unit_types",
            "parent_unit_id": "units"
        },
        dependencies=["unit_types", "unit_type_themes"],
        unique_constraints=[["name"], ["short_name"]]
    ),
    
    "job_titles": EntityMapping(
        entity_type="job_titles",
        table_name="job_titles",
        fields={
            "id": FieldMapping("id", int, required=False, nullable=True),
            "name": FieldMapping("name", str, required=True, nullable=False),
            "short_name": FieldMapping("short_name", str, required=True, nullable=False),
            "aliases": FieldMapping(
                "aliases", str, required=False, nullable=True,
                transformer=parse_json_field,
                default_value="[]"
            ),
            "start_date": FieldMapping(
                "start_date", date, required=False, nullable=True,
                transformer=parse_date
            ),
            "end_date": FieldMapping(
                "end_date", date, required=False, nullable=True,
                transformer=parse_date
            )
        },
        dependencies=[],
        unique_constraints=[["name"], ["short_name"]]
    ),
    
    "persons": EntityMapping(
        entity_type="persons",
        table_name="persons",
        fields={
            "id": FieldMapping("id", int, required=False, nullable=True),
            "name": FieldMapping("name", str, required=True, nullable=False),
            "short_name": FieldMapping("short_name", str, required=False, nullable=True),
            "email": FieldMapping("email", str, required=False, nullable=True),
            "first_name": FieldMapping("first_name", str, required=False, nullable=True),
            "last_name": FieldMapping("last_name", str, required=False, nullable=True),
            "registration_no": FieldMapping("registration_no", str, required=False, nullable=True),
            "profile_image": FieldMapping("profile_image", str, required=False, nullable=True)
        },
        dependencies=[],
        unique_constraints=[["name"], ["email"], ["registration_no"]]
    ),
    
    "assignments": EntityMapping(
        entity_type="assignments",
        table_name="assignments",
        fields={
            "id": FieldMapping("id", int, required=False, nullable=True),
            "person_id": FieldMapping("person_id", int, required=True, nullable=False),
            "unit_id": FieldMapping("unit_id", int, required=True, nullable=False),
            "job_title_id": FieldMapping("job_title_id", int, required=True, nullable=False),
            "version": FieldMapping(
                "version", int, required=False, nullable=False,
                validator=validate_positive_int,
                default_value=1
            ),
            "percentage": FieldMapping(
                "percentage", float, required=False, nullable=False,
                transformer=parse_float,
                validator=validate_percentage,
                default_value=1.0
            ),
            "is_ad_interim": FieldMapping(
                "is_ad_interim", bool, required=False, nullable=False,
                transformer=parse_boolean,
                default_value=False
            ),
            "is_unit_boss": FieldMapping(
                "is_unit_boss", bool, required=False, nullable=False,
                transformer=parse_boolean,
                default_value=False
            ),
            "notes": FieldMapping("notes", str, required=False, nullable=True),
            "valid_from": FieldMapping(
                "valid_from", date, required=False, nullable=True,
                transformer=parse_date
            ),
            "valid_to": FieldMapping(
                "valid_to", date, required=False, nullable=True,
                transformer=parse_date
            ),
            "is_current": FieldMapping(
                "is_current", bool, required=False, nullable=False,
                transformer=parse_boolean,
                default_value=True
            )
        },
        foreign_keys={
            "person_id": "persons",
            "unit_id": "units",
            "job_title_id": "job_titles"
        },
        dependencies=["persons", "units", "job_titles"],
        unique_constraints=[["person_id", "unit_id", "job_title_id", "version"]]
    )
}


# Dependency order for processing
DEPENDENCY_ORDER = [
    "unit_types",
    "unit_type_themes", 
    "units",
    "job_titles",
    "persons",
    "assignments"
]


# CSV column mappings (for cases where CSV headers differ from field names)
CSV_COLUMN_MAPPINGS: Dict[str, Dict[str, str]] = {
    "unit_types": {
        "ID": "id",
        "Name": "name",
        "Short Name": "short_name",
        "Aliases": "aliases",
        "Level": "level",
        "Theme ID": "theme_id"
    },
    "unit_type_themes": {
        "ID": "id",
        "Name": "name",
        "Description": "description",
        "Icon Class": "icon_class",
        "Emoji": "emoji_fallback",
        "Primary Color": "primary_color",
        "Secondary Color": "secondary_color",
        "Text Color": "text_color",
        "Display Label": "display_label",
        "Active": "is_active"
    },
    "units": {
        "ID": "id",
        "Name": "name",
        "Short Name": "short_name",
        "Aliases": "aliases",
        "Unit Type ID": "unit_type_id",
        "Parent Unit ID": "parent_unit_id",
        "Start Date": "start_date",
        "End Date": "end_date"
    },
    "job_titles": {
        "ID": "id",
        "Name": "name",
        "Short Name": "short_name",
        "Aliases": "aliases",
        "Start Date": "start_date",
        "End Date": "end_date"
    },
    "persons": {
        "ID": "id",
        "Name": "name",
        "Short Name": "short_name",
        "Email": "email",
        "First Name": "first_name",
        "Last Name": "last_name",
        "Registration No": "registration_no",
        "Profile Image": "profile_image"
    },
    "assignments": {
        "ID": "id",
        "Person ID": "person_id",
        "Unit ID": "unit_id",
        "Job Title ID": "job_title_id",
        "Version": "version",
        "Percentage": "percentage",
        "Ad Interim": "is_ad_interim",
        "Unit Boss": "is_unit_boss",
        "Notes": "notes",
        "Valid From": "valid_from",
        "Valid To": "valid_to",
        "Current": "is_current"
    }
}


def get_entity_mapping(entity_type: str) -> EntityMapping:
    """Get entity mapping configuration for a given entity type."""
    if entity_type not in ENTITY_MAPPINGS:
        raise ValueError(f"Unknown entity type: {entity_type}")
    return ENTITY_MAPPINGS[entity_type]


def get_dependency_order(entity_types: List[str]) -> List[str]:
    """Get processing order for given entity types based on dependencies."""
    return [entity for entity in DEPENDENCY_ORDER if entity in entity_types]


def get_required_fields(entity_type: str) -> List[str]:
    """Get list of required fields for an entity type."""
    mapping = get_entity_mapping(entity_type)
    return [name for name, field in mapping.fields.items() if field.required]


def get_foreign_key_dependencies(entity_type: str) -> Dict[str, str]:
    """Get foreign key dependencies for an entity type."""
    mapping = get_entity_mapping(entity_type)
    return mapping.foreign_keys.copy()


def validate_entity_data(entity_type: str, data: Dict[str, Any]) -> List[str]:
    """Validate entity data against mapping configuration."""
    mapping = get_entity_mapping(entity_type)
    errors = []
    
    # Check required fields
    for field_name, field_mapping in mapping.fields.items():
        if field_mapping.required and field_name not in data:
            errors.append(f"Missing required field: {field_name}")
        
        if field_name in data:
            value = data[field_name]
            if not field_mapping.validate(value):
                errors.append(f"Invalid value for field {field_name}: {value}")
    
    return errors