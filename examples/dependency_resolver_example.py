#!/usr/bin/env python3
"""
Example demonstrating the dependency resolution system for import/export operations.

This example shows how to:
1. Determine the correct processing order for entities
2. Resolve foreign key references during import
3. Validate dependencies before processing
4. Handle temporary ID mappings
"""

import sys
import os

# Add the parent directory to the path so we can import from app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.dependency_resolver import DependencyResolver, ForeignKeyResolver


def main():
    """Demonstrate dependency resolution functionality"""
    
    print("=== Dependency Resolution System Example ===\n")
    
    # Initialize the dependency resolver
    dependency_resolver = DependencyResolver()
    fk_resolver = ForeignKeyResolver(dependency_resolver)
    
    # 1. Demonstrate processing order determination
    print("1. Entity Processing Order")
    print("-" * 30)
    
    all_entities = ['assignments', 'persons', 'units', 'unit_types', 'job_titles', 'unit_type_themes']
    processing_order = dependency_resolver.get_processing_order(all_entities)
    
    print(f"Input entities: {all_entities}")
    print(f"Processing order: {processing_order}")
    print(f"Explanation: Entities are ordered so dependencies come before dependents\n")
    
    # 2. Demonstrate dependency information
    print("2. Entity Dependencies")
    print("-" * 25)
    
    for entity_type in processing_order:
        dependencies = dependency_resolver.get_dependencies(entity_type)
        if dependencies:
            dep_names = [dep.depends_on for dep in dependencies]
            print(f"{entity_type}: depends on {dep_names}")
        else:
            print(f"{entity_type}: no dependencies (root entity)")
    print()
    
    # 3. Demonstrate foreign key mappings
    print("3. Foreign Key Mappings")
    print("-" * 25)
    
    for entity_type in ['units', 'assignments']:
        fk_mappings = dependency_resolver.get_foreign_key_mappings(entity_type)
        if fk_mappings:
            print(f"{entity_type}:")
            for fk in fk_mappings:
                required = "required" if fk.is_required else "optional"
                print(f"  - {fk.source_field} -> {fk.target_entity}.{fk.target_field} ({required})")
        print()
    
    # 4. Demonstrate sample import data processing
    print("4. Sample Import Data Processing")
    print("-" * 35)
    
    # Sample import data with temporary IDs
    import_data = {
        'unit_types': [
            {'id': 'temp_ut_1', 'name': 'Department', 'level': 1},
            {'id': 'temp_ut_2', 'name': 'Division', 'level': 2}
        ],
        'persons': [
            {'id': 'temp_p_1', 'name': 'John Manager', 'email': 'john@company.com'},
            {'id': 'temp_p_2', 'name': 'Jane Developer', 'email': 'jane@company.com'}
        ],
        'job_titles': [
            {'id': 'temp_jt_1', 'name': 'Department Manager'},
            {'id': 'temp_jt_2', 'name': 'Senior Developer'}
        ],
        'units': [
            {'id': 'temp_u_1', 'name': 'IT Department', 'unit_type_id': 'temp_ut_1'},
            {'id': 'temp_u_2', 'name': 'Development Team', 'unit_type_id': 'temp_ut_2', 'parent_unit_id': 'temp_u_1'}
        ],
        'assignments': [
            {'person_id': 'temp_p_1', 'unit_id': 'temp_u_1', 'job_title_id': 'temp_jt_1', 'percentage': 1.0},
            {'person_id': 'temp_p_2', 'unit_id': 'temp_u_2', 'job_title_id': 'temp_jt_2', 'percentage': 1.0}
        ]
    }
    
    print("Sample import data:")
    for entity_type, records in import_data.items():
        print(f"  {entity_type}: {len(records)} records")
    print()
    
    # 5. Validate dependencies exist
    print("5. Dependency Validation")
    print("-" * 25)
    
    validation_errors = dependency_resolver.validate_dependencies_exist(import_data)
    if validation_errors:
        print("Validation errors found:")
        for error in validation_errors:
            print(f"  - {error}")
    else:
        print("✓ All required dependencies are present")
    print()
    
    # 6. Simulate processing in correct order
    print("6. Processing Simulation")
    print("-" * 25)
    
    # Get processing order for the entities we have
    entity_types = list(import_data.keys())
    processing_order = dependency_resolver.get_processing_order(entity_types)
    
    # Simulate processing each entity type
    created_mappings = {}
    
    for entity_type in processing_order:
        print(f"Processing {entity_type}...")
        records = import_data[entity_type]
        created_mappings[entity_type] = {}
        
        for i, record in enumerate(records):
            # Resolve foreign keys if this entity has them
            fk_mappings = dependency_resolver.get_foreign_key_mappings(entity_type)
            if fk_mappings:
                try:
                    resolved_record = fk_resolver.resolve_foreign_keys(
                        entity_type, record, created_mappings
                    )
                    print(f"  Record {i+1}: Foreign keys resolved")
                    
                    # Show what was resolved
                    for fk in fk_mappings:
                        original = record.get(fk.source_field)
                        resolved = resolved_record.get(fk.source_field)
                        if original != resolved:
                            print(f"    {fk.source_field}: '{original}' -> {resolved}")
                except Exception as e:
                    print(f"  Record {i+1}: Error resolving foreign keys: {e}")
                    continue
            else:
                resolved_record = record
                print(f"  Record {i+1}: No foreign keys to resolve")
            
            # Simulate database insertion (assign real ID)
            real_id = (i + 1) * 100 + abs(hash(entity_type)) % 100
            temp_id = str(record.get('id', f'temp_{entity_type}_{i}'))
            created_mappings[entity_type][temp_id] = real_id
            
            print(f"    Assigned real ID: {temp_id} -> {real_id}")
        
        print()
    
    # 7. Show final mapping statistics
    print("7. Final Statistics")
    print("-" * 20)
    
    stats = fk_resolver.get_resolution_statistics()
    print("Temporary ID mappings created:")
    for entity_type, count in stats['temporary_mappings'].items():
        print(f"  {entity_type}: {count} mappings")
    
    print(f"\nTotal entities processed: {sum(len(records) for records in import_data.values())}")
    print("✓ Import simulation completed successfully!")


if __name__ == '__main__':
    main()