# Migration 002: Unit Type Themes System

## Overview

This migration introduces a comprehensive theming system for unit types, replacing hardcoded styling logic with a flexible, database-driven approach.

## Changes Made

### 1. New Table: `unit_type_themes`

Created a new table to store theme configurations with the following fields:

#### Core Fields
- `id` - Primary key
- `name` - Unique theme name
- `description` - Optional theme description

#### Visual Properties
- `icon_class` - Bootstrap icon class (default: 'diagram-2')
- `emoji_fallback` - Emoji fallback for icons (default: '🏛️')

#### Color Scheme
- `primary_color` - Primary theme color (default: '#0dcaf0')
- `secondary_color` - Secondary theme color (default: '#f0fdff')
- `text_color` - Text color (default: '#0dcaf0')
- `border_color` - Border color (optional, falls back to primary_color)

#### Layout Properties
- `border_width` - Border width in pixels (default: 2)
- `border_style` - CSS border style (default: 'solid')
- `background_gradient` - Optional CSS gradient

#### CSS Generation
- `css_class_suffix` - Suffix for generated CSS classes
- `hover_shadow_color` - Hover effect shadow color (optional)
- `hover_shadow_intensity` - Hover shadow opacity (default: 0.25)

#### Display Properties
- `display_label` - Singular display label
- `display_label_plural` - Plural display label (optional)

#### Accessibility & Metadata
- `high_contrast_mode` - High contrast mode flag (default: FALSE)
- `is_default` - Default theme flag (default: FALSE)
- `is_active` - Active theme flag (default: TRUE)
- `created_by` - Creator identifier
- `datetime_created` - Creation timestamp
- `datetime_updated` - Last update timestamp

### 2. Enhanced Table: `unit_types`

Added a new foreign key column:
- `theme_id` - References `unit_type_themes(id)`

### 3. Default Themes Created

#### Function Theme (ID: 1)
- **Colors**: Primary blue (#0d6efd)
- **Icon**: building (🏢)
- **Border**: 4px solid
- **Display**: "Funzione" / "Funzioni"
- **CSS Class**: unit-function
- **Default**: TRUE

#### Organizational Theme (ID: 2)
- **Colors**: Info cyan (#0dcaf0)
- **Icon**: diagram-2 (🏛️)
- **Border**: 2px solid
- **Display**: "Unità Organizzativa" / "Unità Organizzative"
- **CSS Class**: unit-organizational
- **Default**: FALSE

### 4. Theme Assignments

- Unit Type "Function" (ID: 1) → Function Theme (ID: 1)
- Unit Type "OrganizationalUnit" (ID: 2) → Organizational Theme (ID: 2)

## Database Constraints

### Table Constraints
- `name` must be unique and non-empty
- Color fields must be at least 4 characters (hex color format)
- `border_width` must be greater than 0
- `hover_shadow_intensity` must be between 0 and 1
- Required fields have NOT NULL constraints

### Foreign Key Constraints
- `unit_types.theme_id` references `unit_type_themes.id`
- Foreign key constraints are enabled

### Indexes Created
- `idx_unit_type_themes_name` - For theme name lookups
- `idx_unit_type_themes_is_default` - For default theme queries
- `idx_unit_type_themes_is_active` - For active theme filtering
- `idx_unit_type_themes_css_class_suffix` - For CSS class generation
- `idx_unit_types_theme_id` - For theme relationship queries

## Migration Files

### Forward Migration
- **File**: `migration_002_unit_type_themes.sql`
- **Script**: `scripts/migrate_002_unit_type_themes.py`

### Rollback
- **File**: `rollback_002_unit_type_themes.sql`
- **Script**: `scripts/migrate_002_unit_type_themes.py --rollback`

## Usage

### Run Migration
```bash
python scripts/migrate_002_unit_type_themes.py
```

### Rollback Migration
```bash
python scripts/migrate_002_unit_type_themes.py --rollback
```

### Validate Migration
```bash
python scripts/validate_migration_002.py
```

### Direct SQL Execution (Idempotent)
```bash
sqlite3 database/orgchart.db < database/schema/migration_002_unit_type_themes_idempotent.sql
```

## Migration Safety Features

### Idempotent Execution
The migration script is fully idempotent and can be run multiple times safely:
- Detects if migration has already been completed
- Handles partial migration states gracefully
- Uses `INSERT OR IGNORE` for theme data
- Conditional updates for theme assignments

### Rollback Safety
Complete rollback capability with data preservation:
- Removes `unit_type_themes` table
- Recreates `unit_types` table without `theme_id` column
- Preserves all existing unit type data
- Tested and verified rollback process

## Verification

The migration includes comprehensive verification checks:

1. ✅ `unit_type_themes` table created with all required columns
2. ✅ `theme_id` column added to `unit_types` table
3. ✅ Default themes created (Function Theme and Organizational Theme)
4. ✅ Existing unit types assigned appropriate themes
5. ✅ Foreign key constraints properly configured
6. ✅ Indexes created for performance optimization
7. ✅ Data integrity constraints enforced

### Automated Validation

A comprehensive validation script (`scripts/validate_migration_002.py`) performs:

- **Table Structure Validation**: Verifies all required columns exist
- **Foreign Key Validation**: Confirms proper relationships
- **Theme Data Validation**: Checks default themes and properties
- **Assignment Validation**: Verifies unit types are correctly themed
- **Index Validation**: Ensures performance indexes are created
- **Data Integrity Validation**: Validates constraints and data quality

Run validation with:
```bash
python scripts/validate_migration_002.py
```

## Impact

### Before Migration
- Hardcoded styling logic based on `unit_type_id` comparisons
- Limited to 2 unit types with fixed styling
- No flexibility for customization

### After Migration
- Dynamic theming system supporting unlimited unit types
- Flexible color schemes, icons, and styling options
- Database-driven configuration
- Backward compatibility maintained through default theme assignments

## Next Steps

After this migration, the following development tasks can proceed:

1. **Model Implementation**: Create `UnitTypeTheme` model class
2. **Service Layer**: Implement `UnitTypeThemeService` for CRUD operations
3. **Template Integration**: Update templates to use theme data
4. **CSS Generation**: Implement dynamic CSS generation system
5. **Admin Interface**: Create theme management UI

## Requirements Satisfied

This migration satisfies the following requirements from the Unit Type Theming System spec:

- **Requirement 1.1**: Database-driven theme configuration system
- **Requirement 5.2**: Foreign key relationships properly maintained
- **Requirement 5.3**: Data migration with automatic theme assignment

## Rollback Safety

The migration includes a complete rollback script that:
- Removes the `unit_type_themes` table
- Removes the `theme_id` column from `unit_types`
- Restores the original table structure
- Preserves all existing data integrity

The rollback has been tested and verified to work correctly.