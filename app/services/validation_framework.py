"""
Comprehensive validation framework for import/export operations.

This module provides a robust validation system that handles file format validation,
data type validation, business rule validation, and foreign key constraint validation
for the import/export system.

Implements Requirements 1.3, 3.1, 3.2, 3.3.
"""

import logging
import re
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from typing import Dict, List, Optional, Any, Union, Callable, Set
from dataclasses import dataclass, field
from enum import Enum

from ..models.base import ValidationError as BaseValidationError
from ..models.import_export import ImportExportValidationError, ImportErrorType
from ..models.entity_mappings import get_entity_mapping, ENTITY_MAPPINGS

logger = logging.getLogger(__name__)


class ValidationSeverity(Enum):
    """Severity levels for validation errors."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class DataType(Enum):
    """Supported data types for validation."""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    DECIMAL = "decimal"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    EMAIL = "email"
    JSON = "json"
    PERCENTAGE = "percentage"


@dataclass
class FieldValidationRule:
    """Validation rule for a specific field."""
    field_name: str
    data_type: DataType
    required: bool = False
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    min_value: Optional[Union[int, float, Decimal]] = None
    max_value: Optional[Union[int, float, Decimal]] = None
    pattern: Optional[str] = None
    allowed_values: Optional[Set[Any]] = None
    custom_validator: Optional[Callable[[Any], Optional[str]]] = None
    foreign_key_entity: Optional[str] = None
    nullable: bool = True
    
    def __post_init__(self):
        """Compile regex pattern if provided."""
        if self.pattern:
            try:
                self.compiled_pattern = re.compile(self.pattern)
            except re.error as e:
                logger.error(f"Invalid regex pattern for field {self.field_name}: {e}")
                self.compiled_pattern = None
        else:
            self.compiled_pattern = None


@dataclass
class BusinessRule:
    """Business rule for cross-field validation."""
    name: str
    description: str
    validator: Callable[[Dict[str, Any]], Optional[str]]
    severity: ValidationSeverity = ValidationSeverity.ERROR
    applies_to_entities: Optional[Set[str]] = None


class ValidationFramework:
    """
    Comprehensive validation framework for import/export operations.
    
    This framework provides multiple layers of validation:
    1. File format validation
    2. Data type validation
    3. Business rule validation
    4. Foreign key constraint validation
    """
    
    def __init__(self):
        """Initialize the validation framework with predefined rules."""
        self.field_rules: Dict[str, Dict[str, FieldValidationRule]] = {}
        self.business_rules: List[BusinessRule] = []
        self._initialize_field_rules()
        self._initialize_business_rules()
        
        logger.info("ValidationFramework initialized")
    
    def _initialize_field_rules(self) -> None:
        """Initialize field validation rules for all entity types."""
        # Unit Types validation rules
        self.field_rules['unit_types'] = {
            'id': FieldValidationRule(
                field_name='id',
                data_type=DataType.INTEGER,
                required=False,  # Can be auto-generated
                min_value=1
            ),
            'name': FieldValidationRule(
                field_name='name',
                data_type=DataType.STRING,
                required=True,
                min_length=1,
                max_length=255
            ),
            'short_name': FieldValidationRule(
                field_name='short_name',
                data_type=DataType.STRING,
                required=True,
                min_length=1,
                max_length=50
            ),
            'aliases': FieldValidationRule(
                field_name='aliases',
                data_type=DataType.JSON,
                required=False,
                nullable=True
            ),
            'level': FieldValidationRule(
                field_name='level',
                data_type=DataType.INTEGER,
                required=True,
                min_value=1,
                max_value=10
            ),
            'theme_id': FieldValidationRule(
                field_name='theme_id',
                data_type=DataType.INTEGER,
                required=False,
                foreign_key_entity='unit_type_themes',
                nullable=True
            )
        }
        
        # Unit Type Themes validation rules
        self.field_rules['unit_type_themes'] = {
            'id': FieldValidationRule(
                field_name='id',
                data_type=DataType.INTEGER,
                required=False,
                min_value=1
            ),
            'name': FieldValidationRule(
                field_name='name',
                data_type=DataType.STRING,
                required=True,
                min_length=1,
                max_length=255
            ),
            'description': FieldValidationRule(
                field_name='description',
                data_type=DataType.STRING,
                required=False,
                max_length=1000,
                nullable=True
            ),
            'icon_class': FieldValidationRule(
                field_name='icon_class',
                data_type=DataType.STRING,
                required=False,
                max_length=100,
                nullable=True
            ),
            'emoji_fallback': FieldValidationRule(
                field_name='emoji_fallback',
                data_type=DataType.STRING,
                required=False,
                max_length=10,
                nullable=True
            ),
            'primary_color': FieldValidationRule(
                field_name='primary_color',
                data_type=DataType.STRING,
                required=False,
                pattern=r'^#[0-9A-Fa-f]{6}$',
                nullable=True
            ),
            'secondary_color': FieldValidationRule(
                field_name='secondary_color',
                data_type=DataType.STRING,
                required=False,
                pattern=r'^#[0-9A-Fa-f]{6}$',
                nullable=True
            ),
            'text_color': FieldValidationRule(
                field_name='text_color',
                data_type=DataType.STRING,
                required=False,
                pattern=r'^#[0-9A-Fa-f]{6}$',
                nullable=True
            ),
            'display_label': FieldValidationRule(
                field_name='display_label',
                data_type=DataType.STRING,
                required=False,
                max_length=255,
                nullable=True
            ),
            'is_active': FieldValidationRule(
                field_name='is_active',
                data_type=DataType.BOOLEAN,
                required=False,
                nullable=True
            )
        }
        
        # Units validation rules
        self.field_rules['units'] = {
            'id': FieldValidationRule(
                field_name='id',
                data_type=DataType.INTEGER,
                required=False,
                min_value=1
            ),
            'name': FieldValidationRule(
                field_name='name',
                data_type=DataType.STRING,
                required=True,
                min_length=1,
                max_length=255
            ),
            'short_name': FieldValidationRule(
                field_name='short_name',
                data_type=DataType.STRING,
                required=True,
                min_length=1,
                max_length=50
            ),
            'aliases': FieldValidationRule(
                field_name='aliases',
                data_type=DataType.JSON,
                required=False,
                nullable=True
            ),
            'unit_type_id': FieldValidationRule(
                field_name='unit_type_id',
                data_type=DataType.INTEGER,
                required=True,
                foreign_key_entity='unit_types'
            ),
            'parent_unit_id': FieldValidationRule(
                field_name='parent_unit_id',
                data_type=DataType.INTEGER,
                required=False,
                foreign_key_entity='units',
                nullable=True
            ),
            'start_date': FieldValidationRule(
                field_name='start_date',
                data_type=DataType.DATE,
                required=False,
                nullable=True
            ),
            'end_date': FieldValidationRule(
                field_name='end_date',
                data_type=DataType.DATE,
                required=False,
                nullable=True
            )
        }
        
        # Job Titles validation rules
        self.field_rules['job_titles'] = {
            'id': FieldValidationRule(
                field_name='id',
                data_type=DataType.INTEGER,
                required=False,
                min_value=1
            ),
            'name': FieldValidationRule(
                field_name='name',
                data_type=DataType.STRING,
                required=True,
                min_length=1,
                max_length=255
            ),
            'short_name': FieldValidationRule(
                field_name='short_name',
                data_type=DataType.STRING,
                required=True,
                min_length=1,
                max_length=50
            ),
            'aliases': FieldValidationRule(
                field_name='aliases',
                data_type=DataType.JSON,
                required=False,
                nullable=True
            ),
            'start_date': FieldValidationRule(
                field_name='start_date',
                data_type=DataType.DATE,
                required=False,
                nullable=True
            ),
            'end_date': FieldValidationRule(
                field_name='end_date',
                data_type=DataType.DATE,
                required=False,
                nullable=True
            )
        }
        
        # Persons validation rules
        self.field_rules['persons'] = {
            'id': FieldValidationRule(
                field_name='id',
                data_type=DataType.INTEGER,
                required=False,
                min_value=1
            ),
            'name': FieldValidationRule(
                field_name='name',
                data_type=DataType.STRING,
                required=True,
                min_length=1,
                max_length=255
            ),
            'short_name': FieldValidationRule(
                field_name='short_name',
                data_type=DataType.STRING,
                required=False,
                max_length=50,
                nullable=True
            ),
            'email': FieldValidationRule(
                field_name='email',
                data_type=DataType.EMAIL,
                required=False,
                max_length=255,
                nullable=True
            ),
            'first_name': FieldValidationRule(
                field_name='first_name',
                data_type=DataType.STRING,
                required=False,
                max_length=100,
                nullable=True
            ),
            'last_name': FieldValidationRule(
                field_name='last_name',
                data_type=DataType.STRING,
                required=False,
                max_length=100,
                nullable=True
            ),
            'registration_no': FieldValidationRule(
                field_name='registration_no',
                data_type=DataType.STRING,
                required=False,
                max_length=50,
                nullable=True
            ),
            'profile_image': FieldValidationRule(
                field_name='profile_image',
                data_type=DataType.STRING,
                required=False,
                max_length=500,
                nullable=True
            )
        }
        
        # Assignments validation rules
        self.field_rules['assignments'] = {
            'id': FieldValidationRule(
                field_name='id',
                data_type=DataType.INTEGER,
                required=False,
                min_value=1
            ),
            'person_id': FieldValidationRule(
                field_name='person_id',
                data_type=DataType.INTEGER,
                required=True,
                foreign_key_entity='persons'
            ),
            'unit_id': FieldValidationRule(
                field_name='unit_id',
                data_type=DataType.INTEGER,
                required=True,
                foreign_key_entity='units'
            ),
            'job_title_id': FieldValidationRule(
                field_name='job_title_id',
                data_type=DataType.INTEGER,
                required=True,
                foreign_key_entity='job_titles'
            ),
            'version': FieldValidationRule(
                field_name='version',
                data_type=DataType.INTEGER,
                required=False,
                min_value=1
            ),
            'percentage': FieldValidationRule(
                field_name='percentage',
                data_type=DataType.PERCENTAGE,
                required=False,
                min_value=0.0,
                max_value=1.0,
                nullable=True
            ),
            'is_ad_interim': FieldValidationRule(
                field_name='is_ad_interim',
                data_type=DataType.BOOLEAN,
                required=False,
                nullable=True
            ),
            'is_unit_boss': FieldValidationRule(
                field_name='is_unit_boss',
                data_type=DataType.BOOLEAN,
                required=False,
                nullable=True
            ),
            'notes': FieldValidationRule(
                field_name='notes',
                data_type=DataType.STRING,
                required=False,
                max_length=1000,
                nullable=True
            ),
            'valid_from': FieldValidationRule(
                field_name='valid_from',
                data_type=DataType.DATE,
                required=False,
                nullable=True
            ),
            'valid_to': FieldValidationRule(
                field_name='valid_to',
                data_type=DataType.DATE,
                required=False,
                nullable=True
            ),
            'is_current': FieldValidationRule(
                field_name='is_current',
                data_type=DataType.BOOLEAN,
                required=False,
                nullable=True
            )
        }
        
        logger.debug(f"Initialized field rules for {len(self.field_rules)} entity types")
    
    def _initialize_business_rules(self) -> None:
        """Initialize business rules for cross-field validation."""
        
        # Date range validation rule
        def validate_date_range(record: Dict[str, Any]) -> Optional[str]:
            """Validate that start_date is before end_date."""
            start_date = record.get('start_date')
            end_date = record.get('end_date')
            
            if start_date and end_date:
                try:
                    if isinstance(start_date, str):
                        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                    if isinstance(end_date, str):
                        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
                    
                    if start_date >= end_date:
                        return f"Start date ({start_date}) must be before end date ({end_date})"
                except (ValueError, TypeError) as e:
                    return f"Invalid date format: {e}"
            
            return None
        
        self.business_rules.append(BusinessRule(
            name="date_range_validation",
            description="Start date must be before end date",
            validator=validate_date_range,
            applies_to_entities={'units', 'job_titles', 'assignments'}
        ))
        
        # Assignment validity period rule
        def validate_assignment_validity(record: Dict[str, Any]) -> Optional[str]:
            """Validate assignment validity period."""
            valid_from = record.get('valid_from')
            valid_to = record.get('valid_to')
            
            if valid_from and valid_to:
                try:
                    if isinstance(valid_from, str):
                        valid_from = datetime.strptime(valid_from, '%Y-%m-%d').date()
                    if isinstance(valid_to, str):
                        valid_to = datetime.strptime(valid_to, '%Y-%m-%d').date()
                    
                    if valid_from >= valid_to:
                        return f"Valid from date ({valid_from}) must be before valid to date ({valid_to})"
                except (ValueError, TypeError) as e:
                    return f"Invalid date format in validity period: {e}"
            
            return None
        
        self.business_rules.append(BusinessRule(
            name="assignment_validity_validation",
            description="Assignment validity period must be valid",
            validator=validate_assignment_validity,
            applies_to_entities={'assignments'}
        ))
        
        # Percentage validation rule
        def validate_percentage_range(record: Dict[str, Any]) -> Optional[str]:
            """Validate that percentage is between 0 and 1."""
            percentage = record.get('percentage')
            
            if percentage is not None:
                try:
                    percentage_val = float(percentage)
                    if percentage_val < 0.0 or percentage_val > 1.0:
                        return f"Percentage must be between 0.0 and 1.0, got {percentage_val}"
                except (ValueError, TypeError):
                    return f"Invalid percentage value: {percentage}"
            
            return None
        
        self.business_rules.append(BusinessRule(
            name="percentage_range_validation",
            description="Percentage must be between 0.0 and 1.0",
            validator=validate_percentage_range,
            applies_to_entities={'assignments'}
        ))
        
        # Unit hierarchy validation rule
        def validate_unit_hierarchy(record: Dict[str, Any]) -> Optional[str]:
            """Validate that unit doesn't reference itself as parent."""
            unit_id = record.get('id')
            parent_unit_id = record.get('parent_unit_id')
            
            if unit_id and parent_unit_id and unit_id == parent_unit_id:
                return f"Unit cannot be its own parent (id: {unit_id})"
            
            return None
        
        self.business_rules.append(BusinessRule(
            name="unit_hierarchy_validation",
            description="Unit cannot be its own parent",
            validator=validate_unit_hierarchy,
            applies_to_entities={'units'}
        ))
        
        logger.debug(f"Initialized {len(self.business_rules)} business rules")
    
    def validate_field_value(self, entity_type: str, field_name: str, 
                           value: Any, record: Dict[str, Any] = None) -> List[ImportExportValidationError]:
        """
        Validate a single field value against its validation rules.
        
        Args:
            entity_type: Type of entity being validated
            field_name: Name of the field being validated
            value: Value to validate
            record: Complete record for context (optional)
            
        Returns:
            List of validation errors
        """
        errors = []
        
        # Get field rules for this entity type
        entity_rules = self.field_rules.get(entity_type, {})
        field_rule = entity_rules.get(field_name)
        
        if not field_rule:
            # No validation rule defined for this field - log warning but don't fail
            logger.debug(f"No validation rule defined for {entity_type}.{field_name}")
            return errors
        
        try:
            # Check if field is required
            if field_rule.required and (value is None or value == ''):
                errors.append(ImportExportValidationError(
                    field=field_name,
                    message=f"Field '{field_name}' is required but was empty or missing",
                    error_type=ImportErrorType.MISSING_REQUIRED_FIELD,
                    entity_type=entity_type
                ))
                return errors  # Don't continue validation if required field is missing
            
            # Skip validation if value is None/empty and field is nullable
            if (value is None or value == '') and field_rule.nullable:
                return errors
            
            # Data type validation
            type_errors = self._validate_data_type(field_rule, value, entity_type)
            errors.extend(type_errors)
            
            # If data type validation failed, don't continue with other validations
            if type_errors:
                return errors
            
            # Length validation for strings
            if field_rule.data_type == DataType.STRING and isinstance(value, str):
                if field_rule.min_length is not None and len(value) < field_rule.min_length:
                    errors.append(ImportExportValidationError(
                        field=field_name,
                        message=f"Field '{field_name}' must be at least {field_rule.min_length} characters long, got {len(value)}",
                        error_type=ImportErrorType.INVALID_DATA_TYPE,
                        entity_type=entity_type
                    ))
                
                if field_rule.max_length is not None and len(value) > field_rule.max_length:
                    errors.append(ImportExportValidationError(
                        field=field_name,
                        message=f"Field '{field_name}' must be at most {field_rule.max_length} characters long, got {len(value)}",
                        error_type=ImportErrorType.INVALID_DATA_TYPE,
                        entity_type=entity_type
                    ))
            
            # Numeric range validation
            if field_rule.data_type in [DataType.INTEGER, DataType.FLOAT, DataType.DECIMAL, DataType.PERCENTAGE]:
                numeric_value = self._convert_to_numeric(value, field_rule.data_type)
                if numeric_value is not None:
                    if field_rule.min_value is not None and numeric_value < field_rule.min_value:
                        errors.append(ImportExportValidationError(
                            field=field_name,
                            message=f"Field '{field_name}' must be at least {field_rule.min_value}, got {numeric_value}",
                            error_type=ImportErrorType.INVALID_DATA_TYPE,
                            entity_type=entity_type
                        ))
                    
                    if field_rule.max_value is not None and numeric_value > field_rule.max_value:
                        errors.append(ImportExportValidationError(
                            field=field_name,
                            message=f"Field '{field_name}' must be at most {field_rule.max_value}, got {numeric_value}",
                            error_type=ImportErrorType.INVALID_DATA_TYPE,
                            entity_type=entity_type
                        ))
            
            # Pattern validation
            if field_rule.compiled_pattern and isinstance(value, str):
                if not field_rule.compiled_pattern.match(value):
                    errors.append(ImportExportValidationError(
                        field=field_name,
                        message=f"Field '{field_name}' does not match required pattern: {field_rule.pattern}",
                        error_type=ImportErrorType.INVALID_DATA_TYPE,
                        entity_type=entity_type
                    ))
            
            # Allowed values validation
            if field_rule.allowed_values and value not in field_rule.allowed_values:
                errors.append(ImportExportValidationError(
                    field=field_name,
                    message=f"Field '{field_name}' must be one of {field_rule.allowed_values}, got '{value}'",
                    error_type=ImportErrorType.INVALID_DATA_TYPE,
                    entity_type=entity_type
                ))
            
            # Custom validator
            if field_rule.custom_validator:
                try:
                    custom_error = field_rule.custom_validator(value)
                    if custom_error:
                        errors.append(ImportExportValidationError(
                            field=field_name,
                            message=custom_error,
                            error_type=ImportErrorType.BUSINESS_RULE_VIOLATION,
                            entity_type=entity_type
                        ))
                except Exception as e:
                    logger.error(f"Custom validator failed for {entity_type}.{field_name}: {e}")
                    errors.append(ImportExportValidationError(
                        field=field_name,
                        message=f"Custom validation failed: {str(e)}",
                        error_type=ImportErrorType.BUSINESS_RULE_VIOLATION,
                        entity_type=entity_type
                    ))
        
        except Exception as e:
            logger.error(f"Error validating field {entity_type}.{field_name}: {e}")
            errors.append(ImportExportValidationError(
                field=field_name,
                message=f"Field validation failed: {str(e)}",
                error_type=ImportErrorType.BUSINESS_RULE_VIOLATION,
                entity_type=entity_type
            ))
        
        return errors
    
    def validate_record(self, entity_type: str, record: Dict[str, Any], 
                       line_number: Optional[int] = None) -> List[ImportExportValidationError]:
        """
        Validate a complete record against all field and business rules.
        
        Args:
            entity_type: Type of entity being validated
            record: Record data to validate
            line_number: Line number in source file (for error reporting)
            
        Returns:
            List of validation errors
        """
        errors = []
        
        try:
            # Validate each field in the record
            for field_name, value in record.items():
                field_errors = self.validate_field_value(entity_type, field_name, value, record)
                for error in field_errors:
                    if line_number:
                        error.line_number = line_number
                    errors.append(error)
            
            # Check for missing required fields
            entity_rules = self.field_rules.get(entity_type, {})
            for field_name, field_rule in entity_rules.items():
                if field_rule.required and field_name not in record:
                    errors.append(ImportExportValidationError(
                        field=field_name,
                        message=f"Required field '{field_name}' is missing from record",
                        error_type=ImportErrorType.MISSING_REQUIRED_FIELD,
                        entity_type=entity_type,
                        line_number=line_number
                    ))
            
            # Apply business rules
            business_rule_errors = self._validate_business_rules(entity_type, record, line_number)
            errors.extend(business_rule_errors)
        
        except Exception as e:
            logger.error(f"Error validating record for {entity_type}: {e}")
            errors.append(ImportExportValidationError(
                field="record_validation",
                message=f"Record validation failed: {str(e)}",
                error_type=ImportErrorType.BUSINESS_RULE_VIOLATION,
                entity_type=entity_type,
                line_number=line_number
            ))
        
        return errors
    
    def validate_records_batch(self, entity_type: str, records: List[Dict[str, Any]], 
                             start_line: int = 1) -> List[ImportExportValidationError]:
        """
        Validate a batch of records.
        
        Args:
            entity_type: Type of entity being validated
            records: List of records to validate
            start_line: Starting line number for error reporting
            
        Returns:
            List of validation errors
        """
        errors = []
        
        try:
            for i, record in enumerate(records):
                line_number = start_line + i
                record_errors = self.validate_record(entity_type, record, line_number)
                errors.extend(record_errors)
        
        except Exception as e:
            logger.error(f"Error validating record batch for {entity_type}: {e}")
            errors.append(ImportExportValidationError(
                field="batch_validation",
                message=f"Batch validation failed: {str(e)}",
                error_type=ImportErrorType.BUSINESS_RULE_VIOLATION,
                entity_type=entity_type
            ))
        
        return errors
    
    def validate_foreign_key_constraints(self, entity_type: str, records: List[Dict[str, Any]], 
                                       reference_map: Dict[str, Set[Any]]) -> List[ImportExportValidationError]:
        """
        Validate foreign key constraints for records.
        
        Args:
            entity_type: Type of entity being validated
            records: List of records to validate
            reference_map: Map of entity types to available IDs
            
        Returns:
            List of validation errors
        """
        errors = []
        
        try:
            entity_rules = self.field_rules.get(entity_type, {})
            
            for i, record in enumerate(records):
                for field_name, field_rule in entity_rules.items():
                    if field_rule.foreign_key_entity and field_name in record:
                        fk_value = record[field_name]
                        
                        # Skip validation if value is None and field is nullable
                        if fk_value is None and field_rule.nullable:
                            continue
                        
                        # Check if foreign key reference exists
                        available_ids = reference_map.get(field_rule.foreign_key_entity, set())
                        if fk_value not in available_ids:
                            errors.append(ImportExportValidationError(
                                field=field_name,
                                message=f"Foreign key reference '{fk_value}' not found in {field_rule.foreign_key_entity}",
                                error_type=ImportErrorType.FOREIGN_KEY_VIOLATION,
                                entity_type=entity_type,
                                line_number=i + 1
                            ))
        
        except Exception as e:
            logger.error(f"Error validating foreign key constraints for {entity_type}: {e}")
            errors.append(ImportExportValidationError(
                field="foreign_key_validation",
                message=f"Foreign key validation failed: {str(e)}",
                error_type=ImportErrorType.BUSINESS_RULE_VIOLATION,
                entity_type=entity_type
            ))
        
        return errors
    
    def _validate_data_type(self, field_rule: FieldValidationRule, value: Any, 
                          entity_type: str) -> List[ImportExportValidationError]:
        """Validate data type of a field value."""
        errors = []
        
        try:
            if field_rule.data_type == DataType.STRING:
                if not isinstance(value, str):
                    errors.append(ImportExportValidationError(
                        field=field_rule.field_name,
                        message=f"Expected string, got {type(value).__name__}",
                        error_type=ImportErrorType.INVALID_DATA_TYPE,
                        entity_type=entity_type
                    ))
            
            elif field_rule.data_type == DataType.INTEGER:
                try:
                    int(value)
                except (ValueError, TypeError):
                    errors.append(ImportExportValidationError(
                        field=field_rule.field_name,
                        message=f"Expected integer, got '{value}'",
                        error_type=ImportErrorType.INVALID_DATA_TYPE,
                        entity_type=entity_type
                    ))
            
            elif field_rule.data_type == DataType.FLOAT:
                try:
                    float(value)
                except (ValueError, TypeError):
                    errors.append(ImportExportValidationError(
                        field=field_rule.field_name,
                        message=f"Expected float, got '{value}'",
                        error_type=ImportErrorType.INVALID_DATA_TYPE,
                        entity_type=entity_type
                    ))
            
            elif field_rule.data_type == DataType.DECIMAL:
                try:
                    Decimal(str(value))
                except (InvalidOperation, TypeError):
                    errors.append(ImportExportValidationError(
                        field=field_rule.field_name,
                        message=f"Expected decimal, got '{value}'",
                        error_type=ImportErrorType.INVALID_DATA_TYPE,
                        entity_type=entity_type
                    ))
            
            elif field_rule.data_type == DataType.BOOLEAN:
                if not isinstance(value, bool) and str(value).lower() not in ['true', 'false', '1', '0', 'yes', 'no']:
                    errors.append(ImportExportValidationError(
                        field=field_rule.field_name,
                        message=f"Expected boolean, got '{value}'",
                        error_type=ImportErrorType.INVALID_DATA_TYPE,
                        entity_type=entity_type
                    ))
            
            elif field_rule.data_type == DataType.DATE:
                try:
                    if isinstance(value, str):
                        datetime.strptime(value, '%Y-%m-%d')
                    elif not isinstance(value, date):
                        raise ValueError("Invalid date type")
                except (ValueError, TypeError):
                    errors.append(ImportExportValidationError(
                        field=field_rule.field_name,
                        message=f"Expected date in YYYY-MM-DD format, got '{value}'",
                        error_type=ImportErrorType.INVALID_DATA_TYPE,
                        entity_type=entity_type
                    ))
            
            elif field_rule.data_type == DataType.DATETIME:
                try:
                    if isinstance(value, str):
                        # Try multiple datetime formats
                        for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d']:
                            try:
                                datetime.strptime(value, fmt)
                                break
                            except ValueError:
                                continue
                        else:
                            raise ValueError("No valid datetime format found")
                    elif not isinstance(value, datetime):
                        raise ValueError("Invalid datetime type")
                except (ValueError, TypeError):
                    errors.append(ImportExportValidationError(
                        field=field_rule.field_name,
                        message=f"Expected datetime, got '{value}'",
                        error_type=ImportErrorType.INVALID_DATA_TYPE,
                        entity_type=entity_type
                    ))
            
            elif field_rule.data_type == DataType.EMAIL:
                if isinstance(value, str):
                    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                    if not re.match(email_pattern, value):
                        errors.append(ImportExportValidationError(
                            field=field_rule.field_name,
                            message=f"Invalid email format: '{value}'",
                            error_type=ImportErrorType.INVALID_DATA_TYPE,
                            entity_type=entity_type
                        ))
                else:
                    errors.append(ImportExportValidationError(
                        field=field_rule.field_name,
                        message=f"Expected email string, got {type(value).__name__}",
                        error_type=ImportErrorType.INVALID_DATA_TYPE,
                        entity_type=entity_type
                    ))
            
            elif field_rule.data_type == DataType.JSON:
                try:
                    if isinstance(value, str):
                        import json
                        json.loads(value)
                    elif not isinstance(value, (dict, list)):
                        raise ValueError("Invalid JSON type")
                except (ValueError, TypeError):
                    errors.append(ImportExportValidationError(
                        field=field_rule.field_name,
                        message=f"Expected valid JSON, got '{value}'",
                        error_type=ImportErrorType.INVALID_DATA_TYPE,
                        entity_type=entity_type
                    ))
            
            elif field_rule.data_type == DataType.PERCENTAGE:
                try:
                    percentage_val = float(value)
                    if percentage_val < 0.0 or percentage_val > 1.0:
                        errors.append(ImportExportValidationError(
                            field=field_rule.field_name,
                            message=f"Percentage must be between 0.0 and 1.0, got {percentage_val}",
                            error_type=ImportErrorType.INVALID_DATA_TYPE,
                            entity_type=entity_type
                        ))
                except (ValueError, TypeError):
                    errors.append(ImportExportValidationError(
                        field=field_rule.field_name,
                        message=f"Expected percentage (0.0-1.0), got '{value}'",
                        error_type=ImportErrorType.INVALID_DATA_TYPE,
                        entity_type=entity_type
                    ))
        
        except Exception as e:
            logger.error(f"Error in data type validation for {field_rule.field_name}: {e}")
            errors.append(ImportExportValidationError(
                field=field_rule.field_name,
                message=f"Data type validation failed: {str(e)}",
                error_type=ImportErrorType.BUSINESS_RULE_VIOLATION,
                entity_type=entity_type
            ))
        
        return errors
    
    def _convert_to_numeric(self, value: Any, data_type: DataType) -> Optional[Union[int, float, Decimal]]:
        """Convert value to numeric type for range validation."""
        try:
            if data_type == DataType.INTEGER:
                return int(value)
            elif data_type == DataType.FLOAT or data_type == DataType.PERCENTAGE:
                return float(value)
            elif data_type == DataType.DECIMAL:
                return Decimal(str(value))
        except (ValueError, TypeError, InvalidOperation):
            return None
        
        return None
    
    def _validate_business_rules(self, entity_type: str, record: Dict[str, Any], 
                               line_number: Optional[int] = None) -> List[ImportExportValidationError]:
        """Apply business rules to a record."""
        errors = []
        
        try:
            for rule in self.business_rules:
                # Check if rule applies to this entity type
                if rule.applies_to_entities and entity_type not in rule.applies_to_entities:
                    continue
                
                try:
                    error_message = rule.validator(record)
                    if error_message:
                        error_type = ImportErrorType.BUSINESS_RULE_VIOLATION
                        if rule.severity == ValidationSeverity.CRITICAL:
                            error_type = ImportErrorType.BUSINESS_RULE_VIOLATION
                        
                        errors.append(ImportExportValidationError(
                            field=rule.name,
                            message=error_message,
                            error_type=error_type,
                            entity_type=entity_type,
                            line_number=line_number
                        ))
                
                except Exception as e:
                    logger.error(f"Business rule '{rule.name}' failed for {entity_type}: {e}")
                    errors.append(ImportExportValidationError(
                        field=rule.name,
                        message=f"Business rule validation failed: {str(e)}",
                        error_type=ImportErrorType.BUSINESS_RULE_VIOLATION,
                        entity_type=entity_type,
                        line_number=line_number
                    ))
        
        except Exception as e:
            logger.error(f"Error applying business rules for {entity_type}: {e}")
            errors.append(ImportExportValidationError(
                field="business_rules",
                message=f"Business rule validation failed: {str(e)}",
                error_type=ImportErrorType.BUSINESS_RULE_VIOLATION,
                entity_type=entity_type,
                line_number=line_number
            ))
        
        return errors
    
    def get_field_rules(self, entity_type: str) -> Dict[str, FieldValidationRule]:
        """Get field validation rules for an entity type."""
        return self.field_rules.get(entity_type, {})
    
    def get_business_rules(self, entity_type: Optional[str] = None) -> List[BusinessRule]:
        """Get business rules, optionally filtered by entity type."""
        if entity_type is None:
            return self.business_rules
        
        return [
            rule for rule in self.business_rules
            if rule.applies_to_entities is None or entity_type in rule.applies_to_entities
        ]
    
    def add_custom_field_rule(self, entity_type: str, field_rule: FieldValidationRule) -> None:
        """Add a custom field validation rule."""
        if entity_type not in self.field_rules:
            self.field_rules[entity_type] = {}
        
        self.field_rules[entity_type][field_rule.field_name] = field_rule
        logger.info(f"Added custom field rule for {entity_type}.{field_rule.field_name}")
    
    def add_custom_business_rule(self, rule: BusinessRule) -> None:
        """Add a custom business rule."""
        self.business_rules.append(rule)
        logger.info(f"Added custom business rule: {rule.name}")