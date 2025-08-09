# Data Import/Export System - Technical Documentation

## Overview

The Data Import/Export System provides comprehensive functionality for bulk data operations in the organigramma application. The system supports both CSV and JSON formats while maintaining referential integrity through dependency-aware processing.

## Architecture

### Core Components

The system consists of four main architectural layers:

1. **Import/Export Services Layer**: Business logic for data processing
2. **File Processing Layer**: Format-specific parsers and generators  
3. **Validation Layer**: Data integrity and foreign key validation
4. **Web Interface Layer**: User-facing routes and templates

### Dependency Management

The system processes entities in strict dependency order to maintain referential integrity:

```
Unit Types → Unit Type Themes → Units → Job Titles → Persons → Assignments
```

## API Endpoints

### Import Operations

#### POST /import_export/import
Upload and import data from CSV or JSON files.

**Request:**
```http
POST /import_export/import
Content-Type: multipart/form-data

file: <uploaded_file>
format: csv|json
entity_types: ["unit_types", "units", "persons", "assignments"]
conflict_resolution: skip|update|create_version
validate_only: false
```

**Response:**
```json
{
  "success": true,
  "job_id": "import_job_123",
  "message": "Import started successfully"
}
```

#### GET /import_export/import/preview
Preview import data without committing changes.

**Request:**
```http
POST /import_export/import/preview
Content-Type: multipart/form-data

file: <uploaded_file>
format: csv|json
```

**Response:**
```json
{
  "success": true,
  "preview": {
    "unit_types": [
      {
        "data": {"name": "Direzione Generale", "short_name": "DG"},
        "validation_status": "valid",
        "warnings": []
      }
    ],
    "validation_summary": {
      "total_records": 150,
      "valid_records": 148,
      "invalid_records": 2,
      "warnings": 5
    }
  }
}
```

#### GET /import_export/import/status/{job_id}
Check the status of an import operation.

**Response:**
```json
{
  "job_id": "import_job_123",
  "status": "completed",
  "progress": 100,
  "result": {
    "success": true,
    "records_processed": {"unit_types": 5, "units": 25, "persons": 100},
    "records_created": {"unit_types": 5, "units": 25, "persons": 100},
    "records_updated": {"unit_types": 0, "units": 0, "persons": 0},
    "records_skipped": {"unit_types": 0, "units": 0, "persons": 0},
    "errors": [],
    "warnings": [],
    "execution_time": 12.5
  }
}
```

### Export Operations

#### POST /import_export/export
Generate and download export files.

**Request:**
```http
POST /import_export/export
Content-Type: application/json

{
  "format": "csv|json",
  "entity_types": ["unit_types", "units", "persons", "assignments"],
  "include_historical": true,
  "date_range": {
    "start": "2024-01-01",
    "end": "2024-12-31"
  }
}
```

**Response:**
```json
{
  "success": true,
  "export_id": "export_123",
  "download_url": "/import_export/export/download/export_123",
  "files": [
    "unit_types.csv",
    "units.csv", 
    "persons.csv",
    "assignments.csv"
  ]
}
```

#### GET /import_export/export/download/{export_id}
Download generated export files.

**Response:**
- Content-Type: application/zip
- Content-Disposition: attachment; filename="orgchart_export_20240115.zip"

### Monitoring Operations

#### GET /import_export/operations
List recent import/export operations.

**Response:**
```json
{
  "operations": [
    {
      "id": "import_job_123",
      "type": "import",
      "status": "completed",
      "user": "admin@example.com",
      "created_at": "2024-01-15T10:30:00Z",
      "completed_at": "2024-01-15T10:32:30Z",
      "file_name": "orgchart_data.csv",
      "records_processed": 150
    }
  ]
}
```

## Service Interfaces

### ImportExportService

Main service class for orchestrating import/export operations.

```python
class ImportExportService:
    def __init__(self, db_session):
        self.db = db_session
        self.csv_processor = CSVProcessor()
        self.json_processor = JSONProcessor()
        self.dependency_resolver = DependencyResolver()
        self.validation_framework = ValidationFramework()
    
    async def import_data(self, file_path: str, file_format: str, 
                         options: ImportOptions) -> ImportResult:
        """
        Import data from file with specified options.
        
        Args:
            file_path: Path to the uploaded file
            file_format: 'csv' or 'json'
            options: Import configuration options
            
        Returns:
            ImportResult with success status and detailed results
            
        Raises:
            ValidationError: If file format or data is invalid
            ImportError: If import operation fails
        """
    
    async def export_data(self, export_format: str, 
                         options: ExportOptions) -> ExportResult:
        """
        Export data to specified format with options.
        
        Args:
            export_format: 'csv' or 'json'
            options: Export configuration options
            
        Returns:
            ExportResult with file paths and metadata
            
        Raises:
            ExportError: If export operation fails
        """
    
    async def preview_import(self, file_path: str, 
                           file_format: str) -> PreviewResult:
        """
        Preview import data without persisting changes.
        
        Args:
            file_path: Path to the uploaded file
            file_format: 'csv' or 'json'
            
        Returns:
            PreviewResult with validation results and data preview
        """
```

### CSVProcessor

Handles CSV file parsing and generation.

```python
class CSVProcessor:
    def parse_csv_files(self, file_paths: Dict[str, str]) -> Dict[str, List[Dict]]:
        """
        Parse multiple CSV files for different entity types.
        
        Args:
            file_paths: Dictionary mapping entity_type to file_path
            
        Returns:
            Dictionary mapping entity_type to list of records
            
        Raises:
            CSVParseError: If CSV parsing fails
        """
    
    def generate_csv_files(self, data: Dict[str, List], 
                          output_dir: str) -> List[str]:
        """
        Generate CSV files for each entity type.
        
        Args:
            data: Dictionary mapping entity_type to records
            output_dir: Directory to write CSV files
            
        Returns:
            List of generated file paths
        """
    
    def validate_csv_structure(self, file_path: str, 
                              entity_type: str) -> List[ValidationError]:
        """
        Validate CSV file structure and required columns.
        
        Args:
            file_path: Path to CSV file
            entity_type: Expected entity type
            
        Returns:
            List of validation errors (empty if valid)
        """
```

### JSONProcessor

Handles JSON file parsing and generation.

```python
class JSONProcessor:
    def parse_json_file(self, file_path: str) -> Dict[str, List[Dict]]:
        """
        Parse JSON file with structured entity data.
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            Dictionary mapping entity_type to records
            
        Raises:
            JSONParseError: If JSON parsing fails
        """
    
    def generate_json_file(self, data: Dict[str, List], 
                          output_path: str) -> str:
        """
        Generate structured JSON file with all entity data.
        
        Args:
            data: Dictionary mapping entity_type to records
            output_path: Path for output JSON file
            
        Returns:
            Path to generated JSON file
        """
    
    def validate_json_structure(self, file_path: str) -> List[ValidationError]:
        """
        Validate JSON file structure and schema.
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            List of validation errors (empty if valid)
        """
```

### DependencyResolver

Manages entity dependencies and processing order.

```python
class DependencyResolver:
    def resolve_dependencies(self, data: Dict[str, List]) -> List[Tuple[str, List]]:
        """
        Resolve entity dependencies and return processing order.
        
        Args:
            data: Dictionary mapping entity_type to records
            
        Returns:
            List of (entity_type, records) tuples in dependency order
            
        Raises:
            CircularDependencyError: If circular dependencies detected
        """
    
    def resolve_foreign_keys(self, entity_type: str, record: Dict, 
                           created_mappings: Dict[str, Dict]) -> Dict:
        """
        Resolve foreign key references using created record mappings.
        
        Args:
            entity_type: Type of entity being processed
            record: Record data with potential foreign key references
            created_mappings: Mapping of temporary IDs to actual IDs
            
        Returns:
            Record with resolved foreign key references
        """
```

## Data Models

### Configuration Models

```python
@dataclass
class ImportOptions:
    entity_types: List[str]
    conflict_resolution: str  # 'skip', 'update', 'create_version'
    validate_only: bool = False
    batch_size: int = 100

@dataclass
class ExportOptions:
    entity_types: List[str]
    include_historical: bool = True
    date_range: Optional[Tuple[date, date]] = None
    format_options: Dict[str, Any] = field(default_factory=dict)
```

### Result Models

```python
@dataclass
class ImportResult:
    success: bool
    records_processed: Dict[str, int]
    records_created: Dict[str, int]
    records_updated: Dict[str, int]
    records_skipped: Dict[str, int]
    errors: List[ValidationError]
    warnings: List[ValidationError]
    execution_time: float

@dataclass
class ExportResult:
    success: bool
    file_paths: List[str]
    total_records: Dict[str, int]
    export_metadata: Dict[str, Any]
    execution_time: float

@dataclass
class PreviewResult:
    success: bool
    preview_data: Dict[str, List[Dict]]
    validation_results: Dict[str, List[ValidationError]]
    summary: Dict[str, int]
```

### Error Models

```python
@dataclass
class ValidationError:
    error_type: str
    message: str
    entity_type: Optional[str] = None
    record_index: Optional[int] = None
    field_name: Optional[str] = None
    severity: str = "error"  # "error", "warning", "info"

class ImportErrorType(Enum):
    FILE_FORMAT_ERROR = "file_format_error"
    MISSING_REQUIRED_FIELD = "missing_required_field"
    INVALID_DATA_TYPE = "invalid_data_type"
    FOREIGN_KEY_VIOLATION = "foreign_key_violation"
    DUPLICATE_RECORD = "duplicate_record"
    BUSINESS_RULE_VIOLATION = "business_rule_violation"
    CIRCULAR_REFERENCE = "circular_reference"
```

## File Format Specifications

### CSV Format

Each entity type requires a separate CSV file with specific column headers.

#### Unit Types (unit_types.csv)
```csv
id,name,short_name,aliases,level,theme_id
1,"Direzione Generale","DG","[{""value"":""General Direction"",""lang"":""en-US""}]",1,1
2,"Ufficio","UFF","[]",2,1
```

**Required Columns:**
- `name`: Unit type name (string, max 255 chars)
- `short_name`: Abbreviated name (string, max 50 chars)

**Optional Columns:**
- `id`: Unique identifier (integer, auto-generated if empty)
- `aliases`: JSON array of multilingual aliases
- `level`: Hierarchical level (integer, default 1)
- `theme_id`: Reference to unit type theme (integer)

#### Unit Type Themes (unit_type_themes.csv)
```csv
id,name,description,icon_class,emoji_fallback,primary_color,secondary_color,text_color,display_label,is_active
1,"Default Theme","Default organizational theme","diagram-2","🏛️","#0dcaf0","#f0fdff","#0dcaf0","Organizational Unit",true
```

**Required Columns:**
- `name`: Theme name (string, max 255 chars)
- `primary_color`: Primary color hex code (string)

**Optional Columns:**
- `id`: Unique identifier (integer)
- `description`: Theme description (text)
- `icon_class`: Bootstrap icon class (string)
- `emoji_fallback`: Emoji fallback (string)
- `secondary_color`: Secondary color hex code (string)
- `text_color`: Text color hex code (string)
- `display_label`: Display label (string)
- `is_active`: Active status (boolean, default true)

#### Units (units.csv)
```csv
id,name,short_name,aliases,unit_type_id,parent_unit_id,start_date,end_date
1,"Direzione Generale","DG","[]",1,,2024-01-01,
2,"Ufficio Personale","UP","[]",2,1,2024-01-01,
```

**Required Columns:**
- `name`: Unit name (string, max 255 chars)
- `short_name`: Abbreviated name (string, max 50 chars)
- `unit_type_id`: Reference to unit type (integer)
- `start_date`: Start date (YYYY-MM-DD format)

**Optional Columns:**
- `id`: Unique identifier (integer)
- `aliases`: JSON array of multilingual aliases
- `parent_unit_id`: Reference to parent unit (integer)
- `end_date`: End date (YYYY-MM-DD format)

#### Job Titles (job_titles.csv)
```csv
id,name,short_name,aliases,start_date,end_date
1,"Direttore Generale","DG","[{""value"":""General Director"",""lang"":""en-US""}]",2024-01-01,
```

**Required Columns:**
- `name`: Job title name (string, max 255 chars)
- `short_name`: Abbreviated name (string, max 50 chars)
- `start_date`: Start date (YYYY-MM-DD format)

**Optional Columns:**
- `id`: Unique identifier (integer)
- `aliases`: JSON array of multilingual aliases
- `end_date`: End date (YYYY-MM-DD format)

#### Persons (persons.csv)
```csv
id,name,short_name,email,first_name,last_name,registration_no,profile_image
1,"Mario Rossi","M.Rossi","mario.rossi@example.com","Mario","Rossi","EMP001","profiles/mario.rossi.jpg"
```

**Required Columns:**
- `name`: Full name (string, max 255 chars)
- `short_name`: Display name (string, max 100 chars)
- `email`: Email address (string, max 255 chars, unique)

**Optional Columns:**
- `id`: Unique identifier (integer)
- `first_name`: First name (string, max 100 chars)
- `last_name`: Last name (string, max 100 chars)
- `registration_no`: Employee registration number (string, max 50 chars)
- `profile_image`: Profile image path (string, max 255 chars)

#### Assignments (assignments.csv)
```csv
id,person_id,unit_id,job_title_id,version,percentage,is_ad_interim,is_unit_boss,notes,valid_from,valid_to,is_current
1,1,1,1,1,1.0,false,true,"Initial assignment",2024-01-01,,true
```

**Required Columns:**
- `person_id`: Reference to person (integer)
- `unit_id`: Reference to unit (integer)
- `job_title_id`: Reference to job title (integer)
- `valid_from`: Assignment start date (YYYY-MM-DD format)

**Optional Columns:**
- `id`: Unique identifier (integer)
- `version`: Version number (integer, auto-generated)
- `percentage`: Assignment percentage (decimal, 0.0-1.0, default 1.0)
- `is_ad_interim`: Interim assignment flag (boolean, default false)
- `is_unit_boss`: Unit boss flag (boolean, default false)
- `notes`: Assignment notes (text)
- `valid_to`: Assignment end date (YYYY-MM-DD format)
- `is_current`: Current assignment flag (boolean, auto-calculated)

### JSON Format

JSON format uses a single file with structured data for all entity types.

```json
{
  "metadata": {
    "export_date": "2024-01-15T10:30:00Z",
    "version": "1.0",
    "total_records": 150,
    "entity_counts": {
      "unit_types": 5,
      "unit_type_themes": 3,
      "units": 25,
      "job_titles": 15,
      "persons": 100,
      "assignments": 120
    }
  },
  "unit_types": [
    {
      "id": 1,
      "name": "Direzione Generale",
      "short_name": "DG",
      "aliases": [{"value": "General Direction", "lang": "en-US"}],
      "level": 1,
      "theme_id": 1
    }
  ],
  "unit_type_themes": [
    {
      "id": 1,
      "name": "Default Theme",
      "description": "Default organizational theme",
      "icon_class": "diagram-2",
      "emoji_fallback": "🏛️",
      "primary_color": "#0dcaf0",
      "secondary_color": "#f0fdff",
      "text_color": "#0dcaf0",
      "display_label": "Organizational Unit",
      "is_active": true
    }
  ],
  "units": [
    {
      "id": 1,
      "name": "Direzione Generale",
      "short_name": "DG",
      "aliases": [],
      "unit_type_id": 1,
      "parent_unit_id": null,
      "start_date": "2024-01-01",
      "end_date": null
    }
  ],
  "job_titles": [
    {
      "id": 1,
      "name": "Direttore Generale",
      "short_name": "DG",
      "aliases": [{"value": "General Director", "lang": "en-US"}],
      "start_date": "2024-01-01",
      "end_date": null
    }
  ],
  "persons": [
    {
      "id": 1,
      "name": "Mario Rossi",
      "short_name": "M.Rossi",
      "email": "mario.rossi@example.com",
      "first_name": "Mario",
      "last_name": "Rossi",
      "registration_no": "EMP001",
      "profile_image": "profiles/mario.rossi.jpg"
    }
  ],
  "assignments": [
    {
      "id": 1,
      "person_id": 1,
      "unit_id": 1,
      "job_title_id": 1,
      "version": 1,
      "percentage": 1.0,
      "is_ad_interim": false,
      "is_unit_boss": true,
      "notes": "Initial assignment",
      "valid_from": "2024-01-01",
      "valid_to": null,
      "is_current": true
    }
  ]
}
```

## Error Handling

### Error Categories

The system categorizes errors into different types for better handling and user feedback:

1. **File Format Errors**: Invalid file structure, missing required columns
2. **Data Type Errors**: Invalid data types, format violations
3. **Foreign Key Violations**: References to non-existent entities
4. **Duplicate Record Errors**: Duplicate entries based on business rules
5. **Business Rule Violations**: Domain-specific validation failures
6. **Circular Reference Errors**: Circular dependencies in hierarchical data

### Error Response Format

```json
{
  "success": false,
  "errors": [
    {
      "error_type": "foreign_key_violation",
      "message": "Referenced unit_type_id '999' does not exist",
      "entity_type": "units",
      "record_index": 5,
      "field_name": "unit_type_id",
      "severity": "error"
    }
  ],
  "warnings": [
    {
      "error_type": "missing_optional_field",
      "message": "Optional field 'end_date' is empty",
      "entity_type": "units",
      "record_index": 3,
      "field_name": "end_date",
      "severity": "warning"
    }
  ]
}
```

### Rollback Strategy

The system implements comprehensive rollback mechanisms:

1. **Transaction-level Rollback**: Complete rollback on critical errors
2. **Batch-level Rollback**: Rollback individual batches while continuing others
3. **Entity-level Rollback**: Rollback specific entity types in partial imports
4. **Checkpoint Recovery**: Resume from last successful checkpoint

## Performance Considerations

### Optimization Strategies

1. **Batch Processing**: Process records in configurable batches (default 100)
2. **Streaming**: Stream large files instead of loading entirely into memory
3. **Parallel Processing**: Process independent entity types in parallel
4. **Connection Pooling**: Reuse database connections efficiently
5. **Memory Management**: Clear processed data from memory regularly

### Performance Targets

- **File Size**: Support files up to 100MB
- **Record Count**: Handle 50,000+ records per entity type
- **Processing Time**: Complete import within 5 minutes for typical datasets
- **Memory Usage**: Stay under 512MB during processing
- **Concurrent Operations**: Support 3 simultaneous import/export operations

### Monitoring Metrics

The system tracks the following performance metrics:

- Records processed per second
- Memory usage during processing
- Database transaction time
- File I/O performance
- Error rate by entity type

## Security Considerations

### File Upload Security

1. **File Type Validation**: Restrict to CSV/JSON only
2. **File Size Limits**: Maximum 100MB per file
3. **Content Scanning**: Scan for malicious content patterns
4. **Temporary File Handling**: Secure cleanup of uploaded files
5. **Path Traversal Prevention**: Validate and sanitize file paths

### Data Validation Security

1. **SQL Injection Prevention**: Use parameterized queries exclusively
2. **XSS Prevention**: Sanitize all user input before display
3. **Input Validation**: Validate all data types and formats
4. **Access Control**: Verify user permissions for operations
5. **Audit Logging**: Log all operations with user identification

### Authentication and Authorization

- Import/export operations require authenticated users
- Role-based access control for different operation types
- API endpoints protected with session-based authentication
- File access restricted to authorized users only

## Troubleshooting Guide

### Common Issues and Solutions

#### 1. File Format Errors

**Problem**: "Invalid CSV format" or "JSON parsing failed"

**Solutions:**
- Verify file encoding is UTF-8
- Check for proper CSV delimiter (comma)
- Validate JSON syntax using online validators
- Ensure required columns are present
- Check for special characters in data

**Example Fix:**
```bash
# Convert file encoding to UTF-8
iconv -f ISO-8859-1 -t UTF-8 input.csv > output.csv
```

#### 2. Foreign Key Violations

**Problem**: "Referenced unit_type_id does not exist"

**Solutions:**
- Import entities in dependency order
- Verify referenced IDs exist in target system
- Use preview mode to identify missing references
- Check for typos in foreign key values

**Example Fix:**
```csv
# Ensure unit_types are imported before units
# unit_types.csv first:
1,"Direzione","DIR"

# Then units.csv:
1,"Ufficio A","UA",1  # References unit_type_id=1
```

#### 3. Duplicate Record Errors

**Problem**: "Duplicate record detected for email address"

**Solutions:**
- Choose appropriate conflict resolution strategy
- Use "update" mode to overwrite existing records
- Use "skip" mode to ignore duplicates
- Clean data before import to remove duplicates

#### 4. Memory Issues with Large Files

**Problem**: "Out of memory" during large file processing

**Solutions:**
- Reduce batch size in import options
- Split large files into smaller chunks
- Increase system memory allocation
- Use streaming mode for very large files

**Example Configuration:**
```python
import_options = ImportOptions(
    entity_types=["persons"],
    batch_size=50,  # Reduce from default 100
    validate_only=False
)
```

#### 5. Performance Issues

**Problem**: Import taking too long or timing out

**Solutions:**
- Optimize database indexes
- Reduce batch size for memory-constrained systems
- Use parallel processing for independent entities
- Check database connection pool settings

#### 6. Encoding Issues

**Problem**: Special characters not displaying correctly

**Solutions:**
- Ensure files are saved in UTF-8 encoding
- Check CSV delimiter and quote character settings
- Validate character encoding before upload
- Use proper escape sequences for special characters

### Debugging Tools

#### Enable Debug Logging

```python
import logging
logging.getLogger('import_export').setLevel(logging.DEBUG)
```

#### Validation Preview

Always use preview mode to identify issues before actual import:

```python
result = await import_service.preview_import(file_path, "csv")
for entity_type, errors in result.validation_results.items():
    for error in errors:
        print(f"{entity_type}: {error.message}")
```

#### Performance Profiling

```python
import time
start_time = time.time()
result = await import_service.import_data(file_path, "csv", options)
print(f"Import completed in {time.time() - start_time:.2f} seconds")
```

### Error Recovery Procedures

#### 1. Failed Import Recovery

If an import fails partway through:

1. Check the operation status endpoint for detailed error information
2. Review error logs for specific failure points
3. Fix data issues identified in error messages
4. Use conflict resolution to handle partially imported data
5. Retry import with corrected data

#### 2. Data Corruption Recovery

If data corruption is detected:

1. Stop all import/export operations immediately
2. Restore from the most recent backup
3. Identify the source of corruption
4. Implement additional validation rules
5. Re-run imports with enhanced validation

#### 3. Performance Degradation

If system performance degrades during operations:

1. Monitor system resources (CPU, memory, disk I/O)
2. Check database connection pool status
3. Review active import/export operations
4. Consider reducing concurrent operation limits
5. Optimize database queries and indexes

## Configuration

### Environment Variables

```bash
# Import/Export Configuration
IMPORT_EXPORT_MAX_FILE_SIZE=104857600  # 100MB
IMPORT_EXPORT_BATCH_SIZE=100
IMPORT_EXPORT_TEMP_DIR=/tmp/import_export
IMPORT_EXPORT_EXPORT_DIR=./exports
IMPORT_EXPORT_MAX_CONCURRENT_OPERATIONS=3

# Database Configuration
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20
DATABASE_POOL_TIMEOUT=30

# Security Configuration
UPLOAD_ALLOWED_EXTENSIONS=csv,json
UPLOAD_MAX_CONTENT_LENGTH=104857600
```

### Service Configuration

```python
# app/config.py
class ImportExportConfig:
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
    BATCH_SIZE = 100
    MAX_CONCURRENT_OPERATIONS = 3
    TEMP_DIR = "/tmp/import_export"
    EXPORT_DIR = "./exports"
    ALLOWED_FORMATS = ["csv", "json"]
    
    # Validation settings
    ENABLE_STRICT_VALIDATION = True
    ALLOW_PARTIAL_IMPORTS = True
    DEFAULT_CONFLICT_RESOLUTION = "skip"
    
    # Performance settings
    ENABLE_PARALLEL_PROCESSING = True
    MEMORY_LIMIT_MB = 512
    TIMEOUT_SECONDS = 300
```

This technical documentation provides comprehensive information for developers working with the data import/export system, including API specifications, service interfaces, file formats, error handling, and troubleshooting procedures.