"""
JSON file processor for import/export operations.

This module provides functionality to parse JSON files for import and generate
JSON files for export, handling structured data parsing for nested entities,
metadata handling, and proper date/datetime serialization.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from datetime import date, datetime

from ..models.import_export import (
    ImportExportValidationError, ImportErrorType, ImportOptions, ExportOptions
)
from ..models.entity_mappings import (
    ENTITY_MAPPINGS, DEPENDENCY_ORDER, get_entity_mapping,
    parse_json_field, serialize_json_field
)


@dataclass
class JSONParseResult:
    """Result of JSON parsing operation."""
    success: bool
    data: Dict[str, List[Dict[str, Any]]]
    errors: List[ImportExportValidationError]
    warnings: List[ImportExportValidationError]
    metadata: Dict[str, Any]
    total_records: int
    processed_records: int


class JSONProcessor:
    """Handles JSON file parsing and generation for import/export operations."""
    
    def __init__(self, options: Optional[Union[ImportOptions, ExportOptions]] = None):
        """Initialize JSON processor with options."""
        self.options = options
        self.encoding = getattr(options, 'encoding', 'utf-8') if options else 'utf-8'
        self.json_indent = getattr(options, 'json_indent', 2) if options else 2
        self.include_empty_fields = getattr(options, 'include_empty_fields', False) if options else False
    
    def parse_json_file(self, file_path: str) -> JSONParseResult:
        """
        Parse a JSON file containing organizational data.
        
        Args:
            file_path: Path to the JSON file
            
        Returns:
            JSONParseResult with parsed data and any errors/warnings
        """
        errors = []
        warnings = []
        data = {}
        metadata = {}
        total_records = 0
        processed_records = 0
        
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                errors.append(ImportExportValidationError(
                    field="file_path",
                    message=f"File not found: {file_path}",
                    error_type=ImportErrorType.FILE_FORMAT_ERROR
                ))
                return JSONParseResult(False, {}, errors, warnings, {}, 0, 0)
            
            # Read and parse JSON file
            with open(file_path, 'r', encoding=self.encoding) as jsonfile:
                try:
                    json_data = json.load(jsonfile)
                except json.JSONDecodeError as e:
                    errors.append(ImportExportValidationError(
                        field="json_format",
                        message=f"Invalid JSON format: {str(e)}",
                        error_type=ImportErrorType.FILE_FORMAT_ERROR,
                        line_number=getattr(e, 'lineno', None)
                    ))
                    return JSONParseResult(False, {}, errors, warnings, {}, 0, 0)
            
            # Validate JSON structure
            if not isinstance(json_data, dict):
                errors.append(ImportExportValidationError(
                    field="json_structure",
                    message="JSON file must contain a root object",
                    error_type=ImportErrorType.FILE_FORMAT_ERROR
                ))
                return JSONParseResult(False, {}, errors, warnings, {}, 0, 0)
            
            # Extract metadata if present
            metadata = json_data.get('metadata', {})
            
            # Process each entity type
            for entity_type in DEPENDENCY_ORDER:
                if entity_type in json_data:
                    entity_data = json_data[entity_type]
                    
                    if not isinstance(entity_data, list):
                        errors.append(ImportExportValidationError(
                            field=entity_type,
                            message=f"Entity data for {entity_type} must be a list",
                            error_type=ImportErrorType.FILE_FORMAT_ERROR,
                            entity_type=entity_type
                        ))
                        continue
                    
                    # Process entity records
                    processed_entity_data = []
                    entity_mapping = get_entity_mapping(entity_type)
                    
                    for record_index, record in enumerate(entity_data):
                        total_records += 1
                        
                        if not isinstance(record, dict):
                            errors.append(ImportExportValidationError(
                                field="record_structure",
                                message=f"Record must be an object",
                                error_type=ImportErrorType.FILE_FORMAT_ERROR,
                                entity_type=entity_type,
                                line_number=record_index + 1
                            ))
                            continue
                        
                        try:
                            # Process and validate record data
                            processed_record = self._process_record_data(
                                record, entity_type, entity_mapping, record_index + 1
                            )
                            
                            if processed_record is not None:
                                processed_entity_data.append(processed_record)
                                processed_records += 1
                        
                        except Exception as e:
                            errors.append(ImportExportValidationError(
                                field="record_processing",
                                message=f"Error processing record: {str(e)}",
                                error_type=ImportErrorType.FILE_FORMAT_ERROR,
                                entity_type=entity_type,
                                line_number=record_index + 1
                            ))
                            
                            # Stop if too many errors
                            if len(errors) >= getattr(self.options, 'max_errors', 1000):
                                warnings.append(ImportExportValidationError(
                                    field="processing",
                                    message="Maximum error limit reached, stopping processing",
                                    error_type=ImportErrorType.FILE_FORMAT_ERROR,
                                    entity_type=entity_type,
                                    line_number=record_index + 1
                                ))
                                break
                    
                    if processed_entity_data:
                        data[entity_type] = processed_entity_data
        
        except Exception as e:
            errors.append(ImportExportValidationError(
                field="file_processing",
                message=f"Failed to read JSON file: {str(e)}",
                error_type=ImportErrorType.FILE_FORMAT_ERROR
            ))
        
        success = len(errors) == 0 and processed_records > 0
        return JSONParseResult(success, data, errors, warnings, metadata, total_records, processed_records)
    
    def generate_json_file(self, data: Dict[str, List[Dict[str, Any]]], 
                          output_path: str, include_metadata: bool = True) -> bool:
        """
        Generate a JSON file with organizational data.
        
        Args:
            data: Dictionary mapping entity_type to list of records
            output_path: Path where to save the JSON file
            include_metadata: Whether to include metadata in the output
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Prepare JSON structure with proper ordering
            json_data = self._build_structured_json(data, include_metadata)
            
            # Write JSON file with proper formatting
            with open(output_path, 'w', encoding=self.encoding) as jsonfile:
                json.dump(
                    json_data, 
                    jsonfile, 
                    indent=self.json_indent,
                    ensure_ascii=False,
                    default=self._json_serializer,
                    separators=(',', ': ') if self.json_indent else (',', ':')
                )
            
            return True
            
        except Exception as e:
            # Log error (would use proper logging in production)
            print(f"Error generating JSON file {output_path}: {str(e)}")
            return False
    
    def _build_structured_json(self, data: Dict[str, List[Dict[str, Any]]], 
                              include_metadata: bool) -> Dict[str, Any]:
        """Build properly structured JSON with metadata and relationship information."""
        json_data = {}
        
        # Add metadata if requested
        if include_metadata:
            json_data["metadata"] = self._generate_metadata(data)
        
        # Add entity data in dependency order to maintain relationships
        for entity_type in DEPENDENCY_ORDER:
            if entity_type in data:
                records = data[entity_type]
                entity_mapping = get_entity_mapping(entity_type)
                
                # Process records for JSON output
                processed_records = []
                for record in records:
                    processed_record = self._prepare_record_for_json(record, entity_mapping)
                    processed_records.append(processed_record)
                
                json_data[entity_type] = processed_records
        
        return json_data
    
    def export_to_json(self, data: Dict[str, List[Dict[str, Any]]], 
                      export_options: ExportOptions) -> List[str]:
        """
        Export data to JSON file with comprehensive options handling.
        
        Args:
            data: Dictionary mapping entity_type to list of records
            export_options: Export configuration options
            
        Returns:
            List of generated file paths
        """
        from datetime import datetime
        
        generated_files = []
        
        # Determine output directory
        if export_options.output_directory:
            output_dir = export_options.output_directory
        else:
            # Create timestamped directory
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = f"exports/json_{timestamp}"
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate filename with timestamp if requested
        filename = export_options.file_prefix
        if export_options.include_metadata:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{filename}_{timestamp}" if filename else f"export_{timestamp}"
        
        filename = f"{filename}.json" if filename else "orgchart_export.json"
        output_path = os.path.join(output_dir, filename)
        
        # Filter data based on requested entity types
        filtered_data = {
            entity_type: records 
            for entity_type, records in data.items() 
            if entity_type in export_options.entity_types
        }
        
        # Apply date range filtering if specified
        if export_options.date_range:
            filtered_data = self._apply_date_range_filter(filtered_data, export_options.date_range)
        
        # Generate JSON file
        if self.generate_json_file(filtered_data, output_path, export_options.include_metadata):
            generated_files.append(output_path)
        
        return generated_files
    
    def validate_json_structure(self, file_path: str) -> List[ImportExportValidationError]:
        """
        Validate JSON file structure without parsing all data.
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            List of validation errors
        """
        errors = []
        
        try:
            if not os.path.exists(file_path):
                errors.append(ImportExportValidationError(
                    field="file_path",
                    message=f"File not found: {file_path}",
                    error_type=ImportErrorType.FILE_FORMAT_ERROR
                ))
                return errors
            
            with open(file_path, 'r', encoding=self.encoding) as jsonfile:
                try:
                    json_data = json.load(jsonfile)
                except json.JSONDecodeError as e:
                    errors.append(ImportExportValidationError(
                        field="json_format",
                        message=f"Invalid JSON format: {str(e)}",
                        error_type=ImportErrorType.FILE_FORMAT_ERROR,
                        line_number=getattr(e, 'lineno', None)
                    ))
                    return errors
            
            # Validate root structure
            if not isinstance(json_data, dict):
                errors.append(ImportExportValidationError(
                    field="json_structure",
                    message="JSON file must contain a root object",
                    error_type=ImportErrorType.FILE_FORMAT_ERROR
                ))
                return errors
            
            # Validate entity structures
            for entity_type in ENTITY_MAPPINGS.keys():
                if entity_type in json_data:
                    entity_data = json_data[entity_type]
                    if not isinstance(entity_data, list):
                        errors.append(ImportExportValidationError(
                            field=entity_type,
                            message=f"Entity data for {entity_type} must be a list",
                            error_type=ImportErrorType.FILE_FORMAT_ERROR,
                            entity_type=entity_type
                        ))
        
        except Exception as e:
            errors.append(ImportExportValidationError(
                field="file_processing",
                message=f"Error reading JSON file: {str(e)}",
                error_type=ImportErrorType.FILE_FORMAT_ERROR
            ))
        
        return errors
    
    def _process_record_data(self, record: Dict[str, Any], entity_type: str,
                           entity_mapping, record_index: int) -> Optional[Dict[str, Any]]:
        """Process and validate a single record of data."""
        processed_record = {}
        
        for field_name, field_mapping in entity_mapping.fields.items():
            raw_value = record.get(field_name)
            
            try:
                # Handle None/null values
                if raw_value is None:
                    if field_mapping.required:
                        raise ValueError(f"Required field {field_name} is null")
                    processed_record[field_name] = field_mapping.default_value
                    continue
                
                # Apply field transformation
                if field_mapping.transformer:
                    processed_value = field_mapping.transformer(raw_value)
                else:
                    # Handle type conversion for JSON data
                    if field_mapping.data_type == int and not isinstance(raw_value, int):
                        processed_value = int(raw_value) if raw_value != "" else None
                    elif field_mapping.data_type == float and not isinstance(raw_value, float):
                        processed_value = float(raw_value) if raw_value != "" else None
                    elif field_mapping.data_type == bool and not isinstance(raw_value, bool):
                        processed_value = bool(raw_value) if isinstance(raw_value, bool) else str(raw_value).lower() in ('true', '1', 'yes', 'on')
                    elif field_mapping.data_type == date and isinstance(raw_value, str):
                        processed_value = self._parse_date_from_json(raw_value)
                    elif field_mapping.data_type == datetime and isinstance(raw_value, str):
                        processed_value = self._parse_datetime_from_json(raw_value)
                    else:
                        processed_value = raw_value
                
                # Validate processed value
                if not field_mapping.validate(processed_value):
                    raise ValueError(f"Invalid value for {field_name}: {processed_value}")
                
                processed_record[field_name] = processed_value
                
            except (ValueError, TypeError) as e:
                # For now, skip invalid records - in production we'd collect errors
                print(f"Record {record_index}, field {field_name}: {str(e)}")
                return None
        
        return processed_record
    
    def _prepare_record_for_json(self, record: Dict[str, Any], 
                                entity_mapping) -> Dict[str, Any]:
        """Prepare a record for JSON output by handling special types."""
        json_record = {}
        
        for field_name, field_mapping in entity_mapping.fields.items():
            value = record.get(field_name)
            
            if value is None:
                if self.include_empty_fields:
                    json_record[field_name] = None
                continue
            
            # Handle special field types
            if field_name == 'aliases' and isinstance(value, list):
                # Keep aliases as list structure in JSON
                json_record[field_name] = value
            elif isinstance(value, (date, datetime)):
                # Convert dates to ISO format strings
                json_record[field_name] = value.isoformat()
            else:
                # Keep value as-is for JSON
                json_record[field_name] = value
        
        return json_record
    
    def _generate_metadata(self, data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Generate metadata for the JSON export."""
        from datetime import datetime
        
        # Calculate relationship information
        relationship_info = self._calculate_relationship_info(data)
        
        metadata = {
            "export_timestamp": datetime.now().isoformat(),
            "version": "1.0",
            "format": "json",
            "total_records": sum(len(records) for records in data.values()),
            "entity_counts": {
                entity_type: len(records) 
                for entity_type, records in data.items()
            },
            "dependency_order": DEPENDENCY_ORDER,
            "exported_entities": list(data.keys()),
            "relationships": relationship_info,
            "export_options": {
                "encoding": self.encoding,
                "json_indent": self.json_indent,
                "include_empty_fields": self.include_empty_fields
            }
        }
        
        return metadata
    
    def _calculate_relationship_info(self, data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Calculate relationship information for metadata."""
        relationships = {}
        
        for entity_type, records in data.items():
            if entity_type in ENTITY_MAPPINGS:
                entity_mapping = get_entity_mapping(entity_type)
                if entity_mapping.foreign_keys:
                    relationships[entity_type] = {
                        "foreign_keys": entity_mapping.foreign_keys,
                        "dependencies": entity_mapping.dependencies,
                        "record_count": len(records)
                    }
        
        return relationships
    
    def _apply_date_range_filter(self, data: Dict[str, List[Dict[str, Any]]], 
                                date_range: tuple) -> Dict[str, List[Dict[str, Any]]]:
        """Apply date range filtering to the data."""
        start_date, end_date = date_range
        filtered_data = {}
        
        for entity_type, records in data.items():
            filtered_records = []
            entity_mapping = get_entity_mapping(entity_type)
            
            # Check if entity has date fields to filter on
            date_fields = [
                field_name for field_name, field_mapping in entity_mapping.fields.items()
                if field_mapping.data_type in (date, datetime)
            ]
            
            if not date_fields:
                # No date fields, include all records
                filtered_records = records
            else:
                # Filter records based on date fields
                for record in records:
                    include_record = False
                    
                    for date_field in date_fields:
                        if date_field in record and record[date_field]:
                            record_date = record[date_field]
                            if isinstance(record_date, str):
                                try:
                                    record_date = self._parse_date_from_json(record_date)
                                except ValueError:
                                    continue
                            
                            if isinstance(record_date, datetime):
                                record_date = record_date.date()
                            
                            if start_date <= record_date <= end_date:
                                include_record = True
                                break
                    
                    if include_record:
                        filtered_records.append(record)
            
            filtered_data[entity_type] = filtered_records
        
        return filtered_data
    
    def _json_serializer(self, obj):
        """Custom JSON serializer for special types."""
        if isinstance(obj, datetime):
            # Handle datetime with timezone information
            return obj.isoformat()
        elif isinstance(obj, date):
            # Handle date objects
            return obj.isoformat()
        elif hasattr(obj, '__dict__'):
            # Handle custom objects
            return obj.__dict__
        else:
            # Fallback to string representation
            return str(obj)
    
    def _parse_date_from_json(self, value: str) -> Optional[date]:
        """Parse date string from JSON format."""
        if not value or value.strip() == "":
            return None
        
        formats = ["%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"]
        for fmt in formats:
            try:
                parsed = datetime.strptime(value.strip(), fmt)
                return parsed.date()
            except ValueError:
                continue
        
        raise ValueError(f"Unable to parse date: {value}")
    
    def _parse_datetime_from_json(self, value: str) -> Optional[datetime]:
        """Parse datetime string from JSON format."""
        if not value or value.strip() == "":
            return None
        
        formats = ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"]
        for fmt in formats:
            try:
                return datetime.strptime(value.strip(), fmt)
            except ValueError:
                continue
        
        raise ValueError(f"Unable to parse datetime: {value}")
    
    def get_export_statistics(self, data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Get statistics about the data to be exported."""
        stats = {
            "entity_counts": {},
            "total_records": 0,
            "entity_types": list(data.keys()),
            "empty_entities": [],
            "format": "json"
        }
        
        for entity_type, records in data.items():
            count = len(records)
            stats["entity_counts"][entity_type] = count
            stats["total_records"] += count
            
            if count == 0:
                stats["empty_entities"].append(entity_type)
        
        return stats