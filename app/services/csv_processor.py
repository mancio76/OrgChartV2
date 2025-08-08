"""
CSV file processor for import/export operations.

This module provides functionality to parse CSV files for import and generate
CSV files for export, handling data type conversion, validation, and special
field processing like JSON aliases.
"""

import csv
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, TextIO
from dataclasses import dataclass
from io import StringIO

from ..models.import_export import (
    ImportExportValidationError, ImportErrorType, ImportOptions, ExportOptions
)
from ..models.entity_mappings import (
    ENTITY_MAPPINGS, CSV_COLUMN_MAPPINGS, get_entity_mapping,
    parse_json_field, serialize_json_field
)


@dataclass
class CSVParseResult:
    """Result of CSV parsing operation."""
    success: bool
    data: List[Dict[str, Any]]
    errors: List[ImportExportValidationError]
    warnings: List[ImportExportValidationError]
    total_rows: int
    processed_rows: int


class CSVProcessor:
    """Handles CSV file parsing and generation for import/export operations."""
    
    def __init__(self, options: Optional[Union[ImportOptions, ExportOptions]] = None):
        """Initialize CSV processor with options."""
        self.options = options
        self.delimiter = getattr(options, 'csv_delimiter', ',') if options else ','
        self.quote_char = getattr(options, 'csv_quote_char', '"') if options else '"'
        self.encoding = getattr(options, 'encoding', 'utf-8') if options else 'utf-8'
    
    def parse_csv_file(self, file_path: str, entity_type: str) -> CSVParseResult:
        """
        Parse a single CSV file for a specific entity type.
        
        Args:
            file_path: Path to the CSV file
            entity_type: Type of entity (unit_types, units, etc.)
            
        Returns:
            CSVParseResult with parsed data and any errors/warnings
        """
        errors = []
        warnings = []
        data = []
        total_rows = 0
        processed_rows = 0
        
        try:
            # Validate entity type
            if entity_type not in ENTITY_MAPPINGS:
                errors.append(ImportExportValidationError(
                    field="entity_type",
                    message=f"Unknown entity type: {entity_type}",
                    error_type=ImportErrorType.FILE_FORMAT_ERROR,
                    entity_type=entity_type
                ))
                return CSVParseResult(False, [], errors, warnings, 0, 0)
            
            # Check if file exists
            if not os.path.exists(file_path):
                errors.append(ImportExportValidationError(
                    field="file_path",
                    message=f"File not found: {file_path}",
                    error_type=ImportErrorType.FILE_FORMAT_ERROR,
                    entity_type=entity_type
                ))
                return CSVParseResult(False, [], errors, warnings, 0, 0)
            
            # Get entity mapping
            entity_mapping = get_entity_mapping(entity_type)
            column_mapping = CSV_COLUMN_MAPPINGS.get(entity_type, {})
            
            with open(file_path, 'r', encoding=self.encoding, newline='') as csvfile:
                # Detect dialect
                sample = csvfile.read(1024)
                csvfile.seek(0)
                
                try:
                    dialect = csv.Sniffer().sniff(sample, delimiters=',;\t')
                    reader = csv.DictReader(csvfile, dialect=dialect)
                except csv.Error:
                    # Fallback to configured delimiter
                    reader = csv.DictReader(
                        csvfile, 
                        delimiter=self.delimiter,
                        quotechar=self.quote_char
                    )
                
                # Validate headers
                headers = reader.fieldnames or []
                header_errors = self._validate_headers(headers, entity_type, column_mapping)
                errors.extend(header_errors)
                
                if header_errors:
                    return CSVParseResult(False, [], errors, warnings, 0, 0)
                
                # Process rows
                for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
                    total_rows += 1
                    
                    try:
                        # Map column names to field names
                        mapped_row = self._map_column_names(row, column_mapping)
                        
                        # Process and validate row data
                        processed_row = self._process_row_data(
                            mapped_row, entity_type, entity_mapping, row_num
                        )
                        
                        if processed_row is not None:
                            data.append(processed_row)
                            processed_rows += 1
                        
                    except Exception as e:
                        errors.append(ImportExportValidationError(
                            field="row_data",
                            message=f"Error processing row: {str(e)}",
                            error_type=ImportErrorType.FILE_FORMAT_ERROR,
                            entity_type=entity_type,
                            line_number=row_num
                        ))
                        
                        # Stop if too many errors
                        if len(errors) >= getattr(self.options, 'max_errors', 1000):
                            warnings.append(ImportExportValidationError(
                                field="processing",
                                message="Maximum error limit reached, stopping processing",
                                error_type=ImportErrorType.FILE_FORMAT_ERROR,
                                entity_type=entity_type,
                                line_number=row_num
                            ))
                            break
        
        except Exception as e:
            errors.append(ImportExportValidationError(
                field="file_processing",
                message=f"Failed to read CSV file: {str(e)}",
                error_type=ImportErrorType.FILE_FORMAT_ERROR,
                entity_type=entity_type
            ))
        
        success = len(errors) == 0 and processed_rows > 0
        return CSVParseResult(success, data, errors, warnings, total_rows, processed_rows)
    
    def parse_csv_files(self, file_paths: Dict[str, str]) -> Dict[str, CSVParseResult]:
        """
        Parse multiple CSV files for different entity types.
        
        Args:
            file_paths: Dictionary mapping entity_type to file_path
            
        Returns:
            Dictionary mapping entity_type to CSVParseResult
        """
        results = {}
        
        for entity_type, file_path in file_paths.items():
            results[entity_type] = self.parse_csv_file(file_path, entity_type)
        
        return results
    
    def generate_csv_file(self, data: List[Dict[str, Any]], entity_type: str, 
                         output_path: str) -> bool:
        """
        Generate a CSV file for a specific entity type.
        
        Args:
            data: List of entity records
            entity_type: Type of entity
            output_path: Path where to save the CSV file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not data:
                # Create empty file with headers only
                entity_mapping = get_entity_mapping(entity_type)
                headers = list(entity_mapping.fields.keys())
                
                with open(output_path, 'w', encoding=self.encoding, newline='') as csvfile:
                    writer = csv.DictWriter(
                        csvfile, 
                        fieldnames=headers,
                        delimiter=self.delimiter,
                        quotechar=self.quote_char,
                        quoting=csv.QUOTE_MINIMAL
                    )
                    writer.writeheader()
                return True
            
            # Get field names from first record and entity mapping
            entity_mapping = get_entity_mapping(entity_type)
            fieldnames = list(entity_mapping.fields.keys())
            
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with open(output_path, 'w', encoding=self.encoding, newline='') as csvfile:
                writer = csv.DictWriter(
                    csvfile,
                    fieldnames=fieldnames,
                    delimiter=self.delimiter,
                    quotechar=self.quote_char,
                    quoting=csv.QUOTE_MINIMAL
                )
                
                writer.writeheader()
                
                for record in data:
                    # Process record for CSV output
                    csv_record = self._prepare_record_for_csv(record, entity_mapping)
                    writer.writerow(csv_record)
            
            return True
            
        except Exception as e:
            # Log error (would use proper logging in production)
            print(f"Error generating CSV file {output_path}: {str(e)}")
            return False
    
    def generate_csv_files(self, data: Dict[str, List[Dict[str, Any]]], 
                          output_dir: str, file_prefix: str = "") -> List[str]:
        """
        Generate separate CSV files for each entity type.
        
        Args:
            data: Dictionary mapping entity_type to list of records
            output_dir: Directory where to save CSV files
            file_prefix: Optional prefix for filenames
            
        Returns:
            List of generated file paths
        """
        generated_files = []
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        for entity_type, records in data.items():
            if entity_type not in ENTITY_MAPPINGS:
                continue
            
            entity_mapping = get_entity_mapping(entity_type)
            filename = entity_mapping.csv_filename
            
            # Add prefix if provided
            if file_prefix:
                filename = f"{file_prefix}_{filename}"
            
            output_path = os.path.join(output_dir, filename)
            
            if self.generate_csv_file(records, entity_type, output_path):
                generated_files.append(output_path)
        
        return generated_files
    
    def export_to_csv(self, data: Dict[str, List[Dict[str, Any]]], 
                     export_options: ExportOptions) -> List[str]:
        """
        Export data to CSV files with comprehensive options handling.
        
        Args:
            data: Dictionary mapping entity_type to list of records
            export_options: Export configuration options
            
        Returns:
            List of generated file paths
        """
        from datetime import datetime
        
        # Determine output directory
        if export_options.output_directory:
            output_dir = export_options.output_directory
        else:
            # Create timestamped directory
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = f"exports/csv_{timestamp}"
        
        # Generate file prefix with timestamp if requested
        file_prefix = export_options.file_prefix
        if export_options.include_metadata:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_prefix = f"{file_prefix}_{timestamp}" if file_prefix else f"export_{timestamp}"
        
        # Filter data based on requested entity types
        filtered_data = {
            entity_type: records 
            for entity_type, records in data.items() 
            if entity_type in export_options.entity_types
        }
        
        # Generate CSV files
        generated_files = self.generate_csv_files(filtered_data, output_dir, file_prefix)
        
        # Generate metadata file if requested
        if export_options.include_metadata:
            metadata_file = self._generate_metadata_file(
                filtered_data, output_dir, file_prefix, export_options
            )
            if metadata_file:
                generated_files.append(metadata_file)
        
        return generated_files
    
    def validate_csv_structure(self, file_path: str, entity_type: str) -> List[ImportExportValidationError]:
        """
        Validate CSV file structure without parsing all data.
        
        Args:
            file_path: Path to CSV file
            entity_type: Expected entity type
            
        Returns:
            List of validation errors
        """
        errors = []
        
        try:
            if not os.path.exists(file_path):
                errors.append(ImportExportValidationError(
                    field="file_path",
                    message=f"File not found: {file_path}",
                    error_type=ImportErrorType.FILE_FORMAT_ERROR,
                    entity_type=entity_type
                ))
                return errors
            
            if entity_type not in ENTITY_MAPPINGS:
                errors.append(ImportExportValidationError(
                    field="entity_type",
                    message=f"Unknown entity type: {entity_type}",
                    error_type=ImportErrorType.FILE_FORMAT_ERROR,
                    entity_type=entity_type
                ))
                return errors
            
            with open(file_path, 'r', encoding=self.encoding) as csvfile:
                # Read first few lines to validate structure
                sample = csvfile.read(1024)
                csvfile.seek(0)
                
                try:
                    dialect = csv.Sniffer().sniff(sample, delimiters=',;\t')
                    reader = csv.DictReader(csvfile, dialect=dialect)
                except csv.Error:
                    reader = csv.DictReader(
                        csvfile,
                        delimiter=self.delimiter,
                        quotechar=self.quote_char
                    )
                
                # Validate headers
                headers = reader.fieldnames or []
                column_mapping = CSV_COLUMN_MAPPINGS.get(entity_type, {})
                header_errors = self._validate_headers(headers, entity_type, column_mapping)
                errors.extend(header_errors)
        
        except Exception as e:
            errors.append(ImportExportValidationError(
                field="file_processing",
                message=f"Error reading CSV file: {str(e)}",
                error_type=ImportErrorType.FILE_FORMAT_ERROR,
                entity_type=entity_type
            ))
        
        return errors
    
    def _validate_headers(self, headers: List[str], entity_type: str, 
                         column_mapping: Dict[str, str]) -> List[ImportExportValidationError]:
        """Validate CSV headers against entity mapping."""
        errors = []
        entity_mapping = get_entity_mapping(entity_type)
        
        # Get expected field names (either direct or through column mapping)
        expected_fields = set(entity_mapping.fields.keys())
        mapped_headers = set()
        
        for header in headers:
            if header in expected_fields:
                mapped_headers.add(header)
            elif header in column_mapping:
                mapped_headers.add(column_mapping[header])
        
        # Check for missing required fields
        required_fields = {name for name, field in entity_mapping.fields.items() if field.required}
        missing_required = required_fields - mapped_headers
        
        for field in missing_required:
            errors.append(ImportExportValidationError(
                field=field,
                message=f"Missing required column: {field}",
                error_type=ImportErrorType.MISSING_REQUIRED_FIELD,
                entity_type=entity_type
            ))
        
        return errors
    
    def _map_column_names(self, row: Dict[str, str], 
                         column_mapping: Dict[str, str]) -> Dict[str, str]:
        """Map CSV column names to field names."""
        mapped_row = {}
        
        for csv_column, value in row.items():
            if csv_column in column_mapping:
                field_name = column_mapping[csv_column]
                mapped_row[field_name] = value
            else:
                # Use column name as-is if no mapping exists
                mapped_row[csv_column] = value
        
        return mapped_row
    
    def _process_row_data(self, row: Dict[str, str], entity_type: str,
                         entity_mapping, row_num: int) -> Optional[Dict[str, Any]]:
        """Process and validate a single row of data."""
        processed_row = {}
        
        for field_name, field_mapping in entity_mapping.fields.items():
            raw_value = row.get(field_name, '').strip()
            
            try:
                # Handle empty values
                if not raw_value:
                    if field_mapping.required:
                        raise ValueError(f"Required field {field_name} is empty")
                    processed_row[field_name] = field_mapping.default_value
                    continue
                
                # Apply field transformation
                if field_mapping.transformer:
                    processed_value = field_mapping.transformer(raw_value)
                else:
                    # Default type conversion
                    if field_mapping.data_type == int:
                        processed_value = int(raw_value) if raw_value else None
                    elif field_mapping.data_type == float:
                        processed_value = float(raw_value) if raw_value else None
                    elif field_mapping.data_type == bool:
                        processed_value = raw_value.lower() in ('true', '1', 'yes', 'on')
                    else:
                        processed_value = raw_value
                
                # Validate processed value
                if not field_mapping.validate(processed_value):
                    raise ValueError(f"Invalid value for {field_name}: {processed_value}")
                
                processed_row[field_name] = processed_value
                
            except (ValueError, TypeError) as e:
                # For now, skip invalid rows - in production we'd collect errors
                print(f"Row {row_num}, field {field_name}: {str(e)}")
                return None
        
        return processed_row
    
    def _prepare_record_for_csv(self, record: Dict[str, Any], 
                               entity_mapping) -> Dict[str, str]:
        """Prepare a record for CSV output by converting types to strings."""
        csv_record = {}
        
        for field_name, field_mapping in entity_mapping.fields.items():
            value = record.get(field_name)
            
            if value is None:
                csv_record[field_name] = ''
            elif field_name == 'aliases' and isinstance(value, (list, dict)):
                # Special handling for JSON fields
                csv_record[field_name] = serialize_json_field(value)
            elif isinstance(value, bool):
                csv_record[field_name] = 'true' if value else 'false'
            elif isinstance(value, (int, float)):
                csv_record[field_name] = str(value)
            elif hasattr(value, 'isoformat'):  # date/datetime objects
                csv_record[field_name] = value.isoformat()
            else:
                # Convert to string - CSV writer will handle escaping
                csv_record[field_name] = str(value)
        
        return csv_record
    
    def _generate_metadata_file(self, data: Dict[str, List[Dict[str, Any]]], 
                               output_dir: str, file_prefix: str,
                               export_options: ExportOptions) -> Optional[str]:
        """Generate a metadata file with export information."""
        from datetime import datetime
        import json
        
        try:
            metadata = {
                "export_timestamp": datetime.now().isoformat(),
                "export_options": {
                    "entity_types": export_options.entity_types,
                    "include_historical": export_options.include_historical,
                    "date_range": [
                        export_options.date_range[0].isoformat() if export_options.date_range else None,
                        export_options.date_range[1].isoformat() if export_options.date_range else None
                    ] if export_options.date_range else None,
                    "encoding": export_options.encoding,
                    "csv_delimiter": export_options.csv_delimiter,
                    "csv_quote_char": export_options.csv_quote_char
                },
                "exported_entities": {
                    entity_type: {
                        "record_count": len(records),
                        "filename": f"{file_prefix}_{ENTITY_MAPPINGS[entity_type].csv_filename}" if file_prefix else ENTITY_MAPPINGS[entity_type].csv_filename
                    }
                    for entity_type, records in data.items()
                    if entity_type in ENTITY_MAPPINGS
                },
                "total_records": sum(len(records) for records in data.values())
            }
            
            metadata_filename = f"{file_prefix}_metadata.json" if file_prefix else "export_metadata.json"
            metadata_path = os.path.join(output_dir, metadata_filename)
            
            with open(metadata_path, 'w', encoding=export_options.encoding) as f:
                json.dump(metadata, f, indent=export_options.json_indent, ensure_ascii=False)
            
            return metadata_path
            
        except Exception as e:
            # Log error but don't fail the export
            print(f"Warning: Could not generate metadata file: {str(e)}")
            return None
    
    def get_export_statistics(self, data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Get statistics about the data to be exported."""
        stats = {
            "entity_counts": {},
            "total_records": 0,
            "entity_types": list(data.keys()),
            "empty_entities": []
        }
        
        for entity_type, records in data.items():
            count = len(records)
            stats["entity_counts"][entity_type] = count
            stats["total_records"] += count
            
            if count == 0:
                stats["empty_entities"].append(entity_type)
        
        return stats