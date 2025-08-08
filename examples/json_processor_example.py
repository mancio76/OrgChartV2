#!/usr/bin/env python3
"""
Example usage of the JSON processor for import/export operations.

This script demonstrates how to use the JSONProcessor class to:
1. Export organizational data to JSON format
2. Parse JSON files for import
3. Handle metadata and relationship information
"""

import json
import os
import tempfile
from datetime import date

# Add the app directory to the path so we can import our modules
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.services.json_processor import JSONProcessor
from app.models.import_export import ExportOptions


def create_sample_data():
    """Create sample organizational data for demonstration."""
    return {
        "unit_types": [
            {
                "id": 1,
                "name": "Direzione Generale",
                "short_name": "DG",
                "aliases": [{"value": "General Direction", "lang": "en-US"}],
                "level": 1,
                "theme_id": 1
            },
            {
                "id": 2,
                "name": "Ufficio",
                "short_name": "UFF",
                "aliases": [],
                "level": 2,
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
                "is_active": True
            }
        ],
        "units": [
            {
                "id": 1,
                "name": "Direzione Generale",
                "short_name": "DG",
                "aliases": [],
                "unit_type_id": 1,
                "parent_unit_id": None,
                "start_date": "2024-01-01",
                "end_date": None
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
        "job_titles": [
            {
                "id": 1,
                "name": "Direttore Generale",
                "short_name": "DG",
                "aliases": [{"value": "General Director", "lang": "en-US"}],
                "start_date": "2024-01-01",
                "end_date": None
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
                "is_ad_interim": False,
                "is_unit_boss": True,
                "notes": "Initial assignment",
                "valid_from": "2024-01-01",
                "valid_to": None,
                "is_current": True
            }
        ]
    }


def main():
    """Main demonstration function."""
    print("JSON Processor Example")
    print("=" * 50)
    
    # Create temporary directory for examples
    temp_dir = tempfile.mkdtemp()
    print(f"Working in temporary directory: {temp_dir}")
    
    try:
        # Initialize JSON processor
        processor = JSONProcessor()
        
        # Create sample data
        sample_data = create_sample_data()
        print(f"\nCreated sample data with {sum(len(records) for records in sample_data.values())} total records")
        
        # Example 1: Export data to JSON
        print("\n1. Exporting data to JSON...")
        export_options = ExportOptions(
            entity_types=["unit_types", "unit_type_themes", "units", "job_titles", "persons", "assignments"],
            output_directory=temp_dir,
            file_prefix="example_export",
            include_metadata=True,
            json_indent=2
        )
        
        generated_files = processor.export_to_json(sample_data, export_options)
        print(f"   Generated files: {generated_files}")
        
        # Show the generated JSON structure
        if generated_files:
            with open(generated_files[0], 'r', encoding='utf-8') as f:
                exported_data = json.load(f)
            
            print(f"   File size: {os.path.getsize(generated_files[0])} bytes")
            print(f"   Metadata included: {'metadata' in exported_data}")
            print(f"   Entity types: {[key for key in exported_data.keys() if key != 'metadata']}")
            
            if 'metadata' in exported_data:
                metadata = exported_data['metadata']
                print(f"   Total records in export: {metadata['total_records']}")
                print(f"   Export timestamp: {metadata['export_timestamp']}")
        
        # Example 2: Parse the exported JSON file
        print("\n2. Parsing the exported JSON file...")
        if generated_files:
            parse_result = processor.parse_json_file(generated_files[0])
            
            print(f"   Parse successful: {parse_result.success}")
            print(f"   Total records parsed: {parse_result.total_records}")
            print(f"   Records processed: {parse_result.processed_records}")
            print(f"   Errors: {len(parse_result.errors)}")
            print(f"   Warnings: {len(parse_result.warnings)}")
            
            if parse_result.metadata:
                print(f"   Original export timestamp: {parse_result.metadata.get('export_timestamp', 'N/A')}")
        
        # Example 3: Get export statistics
        print("\n3. Export statistics...")
        stats = processor.get_export_statistics(sample_data)
        print(f"   Total records: {stats['total_records']}")
        print(f"   Entity counts: {stats['entity_counts']}")
        print(f"   Empty entities: {stats['empty_entities']}")
        print(f"   Format: {stats['format']}")
        
        # Example 4: Validate JSON structure
        print("\n4. Validating JSON structure...")
        if generated_files:
            validation_errors = processor.validate_json_structure(generated_files[0])
            print(f"   Validation errors: {len(validation_errors)}")
            if validation_errors:
                for error in validation_errors[:3]:  # Show first 3 errors
                    print(f"   - {error.message}")
        
        print("\n✅ JSON processor example completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error during example execution: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up temporary directory
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
        print(f"\nCleaned up temporary directory: {temp_dir}")


if __name__ == "__main__":
    main()