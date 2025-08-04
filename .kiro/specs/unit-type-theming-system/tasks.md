# Implementation Plan

- [x] 1. Create database schema and migration for unit_type_themes table
  - Create unit_type_themes table with all theme configuration fields
  - Add theme_id foreign key column to unit_types table
  - Create database migration script with proper foreign key constraints
  - Write SQL for default theme data insertion and existing unit type assignment
  - _Requirements: 1.1, 5.2, 5.3_

- [x] 2. Implement UnitTypeTheme model with validation and helper methods
  - Create UnitTypeTheme dataclass with all theme properties
  - Implement validation methods for colors, CSS values, and icon classes
  - Add helper methods for CSS class generation and CSS variable creation
  - Implement from_sqlite_row and to_dict methods for database integration
  - _Requirements: 1.1, 1.4, 6.5_

- [x] 3. Create UnitTypeThemeService for theme management operations
  - Implement CRUD operations for theme management
  - Add methods for theme usage statistics and dependency checking
  - Create theme cloning functionality for duplicating existing themes
  - Implement default theme retrieval and fallback mechanisms
  - Write dynamic CSS generation method for all active themes
  - _Requirements: 1.2, 1.3, 3.1, 3.2, 3.4_

- [x] 4. Enhance UnitType model to include theme relationship
  - Add theme_id field to UnitType model
  - Create computed theme property that loads theme data via joins
  - Implement effective_theme property with fallback to default theme
  - Update from_sqlite_row method to handle theme data from joins
  - _Requirements: 1.2, 5.1_

- [x] 5. Update UnitTypeService to include theme data in queries
  - Modify get_list_query to join with unit_type_themes table
  - Update get_by_id_query to include theme data
  - Enhance model_to_insert_params and model_to_update_params for theme_id
  - Update validation to ensure theme references are valid
  - _Requirements: 1.2, 5.5_

- [x] 6. Create Jinja2 template helper functions for theme-driven rendering
  - Implement get_unit_theme_data helper function
  - Create render_unit_icon helper for dynamic icon rendering
  - Add get_unit_css_classes helper for theme-based CSS class generation
  - Write helper for generating inline CSS variables from theme data
  - Register all helpers with Jinja2 environment
  - _Requirements: 2.1, 2.2, 2.3_

- [x] 7. Refactor orgchart tree template to use theme data instead of hardcoded logic
  - Replace hardcoded unit_type_id comparisons with theme property access
  - Update icon rendering to use theme.icon_class
  - Replace hardcoded color classes with theme-based styling
  - Update badge text to use theme.display_label
  - Replace hardcoded emoji fallbacks with theme.emoji_fallback
  - _Requirements: 2.1, 2.2, 2.4, 4.1_

- [x] 8. Refactor orgchart unit detail template for theme-driven styling
  - Update unit detail header to use theme colors and icons
  - Replace hardcoded badge styling with theme-based classes
  - Update child unit cards to use theme styling
  - Ensure all visual elements respect theme configuration
  - _Requirements: 2.1, 2.2, 4.3_

- [x] 9. Refactor orgchart comparison and matrix templates for theme support
  - Update comparison view to use theme-based styling for unit differences
  - Modify matrix template to apply theme colors and icons consistently
  - Replace all hardcoded styling logic with theme property access
  - _Requirements: 2.1, 4.2_

- [x] 10. Refactor orgchart simulation and span of control templates
  - Update simulation template to use theme data for unit visualization
  - Modify span of control template to apply theme styling
  - Ensure vacant position cards use appropriate theme styling
  - _Requirements: 2.1, 4.1_

- [x] 11. Implement dynamic CSS generation system
  - Create CSS template system for generating theme-specific styles
  - Implement CSS custom properties approach for theme variables
  - Add route for serving dynamically generated CSS
  - Create CSS caching mechanism for performance optimization
  - _Requirements: 2.3, 2.5_

- [x] 12. Update orgchart CSS to support dynamic theme classes
  - Refactor existing .unit-function and .unit-organizational classes to be template-based
  - Create base .unit-themed class with CSS custom property support
  - Implement hover effects using CSS custom properties
  - Add high contrast mode support for accessibility
  - _Requirements: 2.3, 2.5, 4.4_

- [x] 13. Create theme management routes and templates
  - Implement routes for theme CRUD operations (list, create, edit, delete)
  - Create theme list template with usage statistics and preview
  - Build theme creation/editing form with live preview functionality
  - Add theme assignment interface for unit types
  - Implement theme cloning functionality in UI
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 3.3_

- [x] 14. Implement theme validation and error handling
  - Add server-side validation for theme color formats and CSS values
  - Implement client-side validation with real-time feedback
  - Create error handling for invalid theme references
  - Add fallback mechanisms for missing or corrupted theme data
  - _Requirements: 6.5, 1.4, 1.5_

- [x] 15. Create database migration script and default theme setup
  - Write migration script to create unit_type_themes table
  - Implement data migration to assign themes to existing unit types
  - Create seed data for default themes matching current styling
  - Add rollback capability for migration safety
  - _Requirements: 5.1, 5.2, 5.4_

- [x] 16. Write comprehensive tests for theme system
  - Create unit tests for UnitTypeTheme model validation and methods
  - Write tests for UnitTypeThemeService CRUD operations and business logic
  - Implement integration tests for template rendering with theme data
  - Add tests for CSS generation and dynamic styling
  - Create tests for theme management UI functionality
  - _Requirements: 1.1, 1.2, 1.3, 2.1, 6.1_

- [x] 17. Update unit management interfaces to support theme selection
  - Modify unit type creation/editing forms to include theme selection
  - Add theme preview in unit type management interface
  - Update unit type list view to show assigned themes
  - Ensure theme changes are reflected immediately in unit displays
  - _Requirements: 1.2, 6.4_

- [x] 18. Implement theme usage analytics and reporting
  - Create analytics for theme usage across unit types
  - Add reporting for most/least used themes
  - Implement theme impact analysis for changes
  - Create dashboard for theme management overview
  - _Requirements: 3.4_

- [x] 19. Add accessibility and performance optimizations
  - Implement color contrast validation for theme colors
  - Add high contrast mode support for accessibility compliance
  - Optimize CSS generation and caching for performance
  - Add lazy loading for theme data in large orgcharts
  - _Requirements: 4.4, 4.5_

- [x] 20. Create documentation and admin guides
  - Write user documentation for theme management interface
  - Create developer documentation for theme system architecture
  - Add troubleshooting guide for theme-related issues
  - Document migration process and rollback procedures
  - _Requirements: 6.1, 6.2_