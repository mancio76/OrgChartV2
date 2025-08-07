# Design Document

## Overview

The data import/export system provides comprehensive functionality for bulk data operations in the organigramma application. The system supports both CSV and JSON formats while maintaining referential integrity through dependency-aware processing. The design follows the existing service layer architecture and integrates with the current validation framework.

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

This order ensures that foreign key references are always available when creating dependent records.

## Components and Interfaces

### 1. Import/Export Service (`app/services/import_export.py`)

**Primary Interface:**
```python
class ImportExportService:
    def import_data(self, file_path: str, file_format: str, options: ImportOptions) -> ImportResult
    def export_data(self, export_format: str, options: ExportOptions) -> ExportResult
    def preview_import(self, file_path: str, file_format: str) -> PreviewResult
    def validate_import_data(self, data: Dict[str, List]) -> ValidationResult
```

**Key Responsibilities:**
- Orchestrate import/export operations
- Manage dependency ordering
- Handle transaction management
- Coordinate with existing services

### 2. File Format Processors

**CSV Processor (`app/services/csv_processor.py`):**
```python
class CSVProcessor:
    def parse_csv_files(self, file_paths: Dict[str, str]) -> Dict[str, List[Dict]]
    def generate_csv_files(self, data: Dict[str, List], output_dir: str) -> List[str]
    def validate_csv_structure(self, file_path: str, entity_type: str) -> List[ValidationError]
```

**JSON Processor (`app/services/json_processor.py`):**
```python
class JSONProcessor:
    def parse_json_file(self, file_path: str) -> Dict[str, List[Dict]]
    def generate_json_file(self, data: Dict[str, List], output_path: str) -> str
    def validate_json_structure(self, file_path: str) -> List[ValidationError]
```

### 3. Data Models

**Import/Export Configuration Models:**
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
```

### 4. Web Interface Components

**Routes (`app/routes/import_export.py`):**
- `/import` - Import data interface
- `/export` - Export data interface  
- `/import/preview` - Preview import data
- `/import/status/{job_id}` - Check import status
- `/export/download/{file_id}` - Download export files

**Templates:**
- `templates/import_export/import.html` - Import interface
- `templates/import_export/export.html` - Export interface
- `templates/import_export/preview.html` - Import preview
- `templates/import_export/status.html` - Operation status

## Data Models

### Entity Field Mappings

**Unit Types:**
```csv
id,name,short_name,aliases,level,theme_id
1,"Direzione Generale","DG","[{""value"":""General Direction"",""lang"":""en-US""}]",1,1
```

**Unit Type Themes:**
```csv
id,name,description,icon_class,emoji_fallback,primary_color,secondary_color,text_color,display_label,is_active
1,"Default Theme","Default organizational theme","diagram-2","🏛️","#0dcaf0","#f0fdff","#0dcaf0","Organizational Unit",true
```

**Units:**
```csv
id,name,short_name,aliases,unit_type_id,parent_unit_id,start_date,end_date
1,"Direzione Generale","DG","[]",1,,2024-01-01,
2,"Ufficio Personale","UP","[]",2,1,2024-01-01,
```

**Job Titles:**
```csv
id,name,short_name,aliases,start_date,end_date
1,"Direttore Generale","DG","[{""value"":""General Director"",""lang"":""en-US""}]",2024-01-01,
```

**Persons:**
```csv
id,name,short_name,email,first_name,last_name,registration_no,profile_image
1,"Mario Rossi","M.Rossi","mario.rossi@example.com","Mario","Rossi","EMP001","profiles/mario.rossi.jpg"
```

**Assignments:**
```csv
id,person_id,unit_id,job_title_id,version,percentage,is_ad_interim,is_unit_boss,notes,valid_from,valid_to,is_current
1,1,1,1,1,1.0,false,true,"Initial assignment",2024-01-01,,true
```

### JSON Structure

```json
{
  "metadata": {
    "export_date": "2024-01-15T10:30:00Z",
    "version": "1.0",
    "total_records": 150
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
  "unit_type_themes": [...],
  "units": [...],
  "job_titles": [...],
  "persons": [...],
  "assignments": [...]
}
```

## Error Handling

### Validation Strategy

1. **File Format Validation**: Verify file structure and required columns
2. **Data Type Validation**: Ensure correct data types for all fields
3. **Foreign Key Validation**: Verify all references exist or will be created
4. **Business Rule Validation**: Apply domain-specific validation rules
5. **Duplicate Detection**: Identify and handle duplicate records

### Error Categories

```python
class ImportErrorType(Enum):
    FILE_FORMAT_ERROR = "file_format_error"
    MISSING_REQUIRED_FIELD = "missing_required_field"
    INVALID_DATA_TYPE = "invalid_data_type"
    FOREIGN_KEY_VIOLATION = "foreign_key_violation"
    DUPLICATE_RECORD = "duplicate_record"
    BUSINESS_RULE_VIOLATION = "business_rule_violation"
    CIRCULAR_REFERENCE = "circular_reference"
```

### Error Recovery

- **Rollback Strategy**: Complete transaction rollback on critical errors
- **Partial Success**: Continue processing with warnings for non-critical issues
- **Error Reporting**: Detailed error logs with line numbers and field names
- **Retry Mechanism**: Allow users to fix errors and retry import

## Testing Strategy

### Unit Tests

1. **Service Layer Tests**: Test import/export business logic
2. **File Processor Tests**: Test CSV/JSON parsing and generation
3. **Validation Tests**: Test all validation scenarios
4. **Model Tests**: Test data model conversions

### Integration Tests

1. **End-to-End Import**: Test complete import workflow
2. **End-to-End Export**: Test complete export workflow
3. **Foreign Key Dependencies**: Test dependency ordering
4. **Error Handling**: Test error scenarios and recovery

### Test Data Sets

1. **Valid Complete Dataset**: All entities with proper relationships
2. **Invalid Data Sets**: Various error conditions
3. **Large Dataset**: Performance testing with 10,000+ records
4. **Edge Cases**: Empty files, malformed data, circular references

## Implementation Details

### Dependency Resolution Algorithm

```python
def resolve_dependencies(self, data: Dict[str, List]) -> List[Tuple[str, List]]:
    """
    Resolve entity dependencies and return processing order.
    Returns list of (entity_type, records) tuples in dependency order.
    """
    dependency_graph = {
        'unit_types': [],
        'unit_type_themes': ['unit_types'],
        'units': ['unit_types', 'unit_type_themes'],
        'job_titles': [],
        'persons': [],
        'assignments': ['persons', 'units', 'job_titles']
    }
    
    # Topological sort implementation
    return self._topological_sort(dependency_graph, data)
```

### Foreign Key Resolution

```python
def resolve_foreign_keys(self, entity_type: str, record: Dict, 
                        created_mappings: Dict[str, Dict]) -> Dict:
    """
    Resolve foreign key references using created record mappings.
    Handles both existing IDs and temporary references.
    """
    fk_mappings = {
        'units': {'unit_type_id': 'unit_types', 'parent_unit_id': 'units'},
        'assignments': {
            'person_id': 'persons',
            'unit_id': 'units', 
            'job_title_id': 'job_titles'
        }
    }
    
    # Implementation details...
```

### Batch Processing

```python
def process_batch(self, entity_type: str, records: List[Dict], 
                 batch_size: int = 100) -> BatchResult:
    """
    Process records in batches to manage memory and transaction size.
    """
    results = []
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        batch_result = self._process_record_batch(entity_type, batch)
        results.append(batch_result)
    
    return self._consolidate_batch_results(results)
```

### File Format Detection

```python
def detect_file_format(self, file_path: str) -> str:
    """
    Auto-detect file format based on extension and content.
    """
    extension = Path(file_path).suffix.lower()
    
    if extension == '.json':
        return 'json'
    elif extension == '.csv':
        return 'csv'
    else:
        # Content-based detection
        return self._detect_by_content(file_path)
```

## Security Considerations

### File Upload Security

1. **File Type Validation**: Restrict to CSV/JSON only
2. **File Size Limits**: Maximum 100MB per file
3. **Content Scanning**: Scan for malicious content
4. **Temporary File Handling**: Secure cleanup of uploaded files

### Data Validation Security

1. **SQL Injection Prevention**: Use parameterized queries
2. **XSS Prevention**: Sanitize all user input
3. **Path Traversal Prevention**: Validate file paths
4. **Access Control**: Verify user permissions for import/export

### Audit Trail

1. **Operation Logging**: Log all import/export operations
2. **User Tracking**: Record which user performed operations
3. **Data Changes**: Track what data was modified
4. **File Retention**: Maintain import/export file history

## Performance Considerations

### Optimization Strategies

1. **Batch Processing**: Process records in configurable batches
2. **Database Transactions**: Use appropriate transaction boundaries
3. **Memory Management**: Stream large files instead of loading entirely
4. **Parallel Processing**: Process independent entity types in parallel
5. **Caching**: Cache foreign key lookups during processing

### Scalability Targets

- **File Size**: Support files up to 100MB
- **Record Count**: Handle 50,000+ records per entity type
- **Processing Time**: Complete import within 5 minutes for typical datasets
- **Memory Usage**: Stay under 512MB during processing
- **Concurrent Operations**: Support 3 simultaneous import/export operations