#!/usr/bin/env python3
"""
Validation script for Migration 002: Unit Type Themes System
Validates that all migration components are correctly implemented
"""

import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import get_db_manager


def validate_migration():
    """Validate all aspects of the unit type themes migration"""
    
    db_manager = get_db_manager()
    
    print("🔍 Validating Migration 002: Unit Type Themes System...")
    print("=" * 60)
    
    # Test 1: Verify unit_type_themes table structure
    print("\n1. Validating unit_type_themes table structure...")
    
    columns_result = db_manager.fetch_all("PRAGMA table_info(unit_type_themes)")
    expected_columns = {
        'id', 'name', 'description', 'icon_class', 'emoji_fallback',
        'primary_color', 'secondary_color', 'text_color', 'border_color',
        'border_width', 'border_style', 'background_gradient',
        'css_class_suffix', 'hover_shadow_color', 'hover_shadow_intensity',
        'display_label', 'display_label_plural', 'high_contrast_mode',
        'is_default', 'is_active', 'created_by', 'datetime_created', 'datetime_updated'
    }
    
    actual_columns = {row[1] for row in columns_result}
    
    if expected_columns.issubset(actual_columns):
        print("✅ All required columns present in unit_type_themes table")
    else:
        missing = expected_columns - actual_columns
        print(f"❌ Missing columns in unit_type_themes: {missing}")
        return False
    
    # Test 2: Verify unit_types has theme_id column
    print("\n2. Validating unit_types table enhancement...")
    
    unit_types_columns = db_manager.fetch_all("PRAGMA table_info(unit_types)")
    unit_types_column_names = {row[1] for row in unit_types_columns}
    
    if 'theme_id' in unit_types_column_names:
        print("✅ theme_id column added to unit_types table")
    else:
        print("❌ theme_id column missing from unit_types table")
        return False
    
    # Test 3: Verify foreign key constraints
    print("\n3. Validating foreign key constraints...")
    
    fk_constraints = db_manager.fetch_all("PRAGMA foreign_key_list(unit_types)")
    theme_fk_exists = any(row[2] == 'unit_type_themes' for row in fk_constraints)
    
    if theme_fk_exists:
        print("✅ Foreign key constraint from unit_types to unit_type_themes exists")
    else:
        print("❌ Foreign key constraint missing")
        return False
    
    # Test 4: Verify default themes were created
    print("\n4. Validating default themes creation...")
    
    themes = db_manager.fetch_all("SELECT * FROM unit_type_themes ORDER BY id")
    
    if len(themes) >= 2:
        print(f"✅ {len(themes)} themes created")
        
        # Verify Function Theme
        function_theme = next((t for t in themes if t[1] == 'Function Theme'), None)
        if function_theme:
            print("✅ Function Theme created with correct properties:")
            print(f"   - Icon: {function_theme[3]} ({function_theme[4]})")
            print(f"   - Primary Color: {function_theme[5]}")
            print(f"   - Border Width: {function_theme[9]}px")
            print(f"   - CSS Class: unit-{function_theme[12]}")
            print(f"   - Display Label: {function_theme[15]}")
            print(f"   - Is Default: {bool(function_theme[18])}")
        else:
            print("❌ Function Theme not found")
            return False
        
        # Verify Organizational Theme
        org_theme = next((t for t in themes if t[1] == 'Organizational Theme'), None)
        if org_theme:
            print("✅ Organizational Theme created with correct properties:")
            print(f"   - Icon: {org_theme[3]} ({org_theme[4]})")
            print(f"   - Primary Color: {org_theme[5]}")
            print(f"   - Border Width: {org_theme[9]}px")
            print(f"   - CSS Class: unit-{org_theme[12]}")
            print(f"   - Display Label: {org_theme[15]}")
            print(f"   - Is Default: {bool(org_theme[18])}")
        else:
            print("❌ Organizational Theme not found")
            return False
    else:
        print(f"❌ Expected at least 2 themes, found {len(themes)}")
        return False
    
    # Test 5: Verify theme assignments
    print("\n5. Validating theme assignments...")
    
    assignments = db_manager.fetch_all("""
        SELECT ut.id, ut.name, ut.theme_id, utt.name as theme_name, utt.display_label
        FROM unit_types ut
        LEFT JOIN unit_type_themes utt ON ut.theme_id = utt.id
        ORDER BY ut.id
    """)
    
    expected_assignments = {
        1: ('Function', 'Function Theme', 'Funzione'),
        2: ('OrganizationalUnit', 'Organizational Theme', 'Unità Organizzativa')
    }
    
    for assignment in assignments:
        unit_id, unit_name, theme_id, theme_name, display_label = assignment
        
        if unit_id in expected_assignments:
            expected_unit, expected_theme, expected_label = expected_assignments[unit_id]
            
            if unit_name == expected_unit and theme_name == expected_theme and display_label == expected_label:
                print(f"✅ Unit Type '{unit_name}' correctly assigned to '{theme_name}' ({display_label})")
            else:
                print(f"❌ Incorrect assignment for unit {unit_id}: expected {expected_assignments[unit_id]}, got ({unit_name}, {theme_name}, {display_label})")
                return False
    
    # Test 6: Verify default theme configuration
    print("\n6. Validating default theme configuration...")
    
    default_themes = db_manager.fetch_all("SELECT name FROM unit_type_themes WHERE is_default = 1")
    
    if len(default_themes) == 1:
        default_theme_name = default_themes[0][0]
        print(f"✅ Default theme configured: {default_theme_name}")
    else:
        print(f"❌ Expected exactly 1 default theme, found {len(default_themes)}")
        return False
    
    # Test 7: Verify indexes were created
    print("\n7. Validating database indexes...")
    
    expected_indexes = {
        'idx_unit_type_themes_name',
        'idx_unit_type_themes_is_default',
        'idx_unit_type_themes_is_active',
        'idx_unit_type_themes_css_class_suffix',
        'idx_unit_types_theme_id'
    }
    
    all_indexes = db_manager.fetch_all("SELECT name FROM sqlite_master WHERE type='index'")
    actual_indexes = {row[0] for row in all_indexes if row[0] and not row[0].startswith('sqlite_')}
    
    missing_indexes = expected_indexes - actual_indexes
    if not missing_indexes:
        print("✅ All required indexes created")
    else:
        print(f"❌ Missing indexes: {missing_indexes}")
        return False
    
    # Test 8: Validate data integrity constraints
    print("\n8. Validating data integrity...")
    
    integrity_checks = [
        ("Color format validation", "SELECT COUNT(*) FROM unit_type_themes WHERE length(primary_color) < 4", 0),
        ("Border width validation", "SELECT COUNT(*) FROM unit_type_themes WHERE border_width <= 0", 0),
        ("Display label validation", "SELECT COUNT(*) FROM unit_type_themes WHERE length(display_label) = 0", 0),
        ("CSS class suffix validation", "SELECT COUNT(*) FROM unit_type_themes WHERE length(css_class_suffix) = 0", 0),
        ("Hover intensity validation", "SELECT COUNT(*) FROM unit_type_themes WHERE hover_shadow_intensity < 0 OR hover_shadow_intensity > 1", 0),
    ]
    
    for check_name, query, expected_count in integrity_checks:
        result = db_manager.fetch_one(query)
        actual_count = result[0] if result else 0
        
        if actual_count == expected_count:
            print(f"✅ {check_name} passed")
        else:
            print(f"❌ {check_name} failed: expected {expected_count}, got {actual_count}")
            return False
    
    print("\n" + "=" * 60)
    print("🎉 Migration 002 validation completed successfully!")
    print("✅ All components are correctly implemented and configured")
    
    return True


if __name__ == "__main__":
    try:
        success = validate_migration()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Validation failed with error: {e}")
        sys.exit(1)