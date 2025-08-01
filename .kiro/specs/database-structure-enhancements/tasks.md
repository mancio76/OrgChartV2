# Implementation Plan

- [x] 1. Create database migration script for schema changes

  - Write migration script to add first_name, last_name, registration_no, profile_image columns to persons table
  - Create companies table with all required fields and foreign key constraints
  - Add database indexes for performance optimization
  - Include rollback functionality and error handling for safe migration
  - Create profiles directory for profile images
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 6.3_

- [x] 2. Update Person model with enhanced field support

  - Add first_name, last_name, registration_no, profile_image fields to Person dataclass
  - Implement suggested_name_format property for "{lastName}, {firstName}" generation
  - Update validation method to include new field validation rules (registration_no ≤ 25 chars, profile_image ≤ 1024 chars)
  - Enhance from_sqlite_row method to handle new database columns
  - _Requirements: 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 2.4, 6.1, 6.2_

- [x] 3. Create Company model and validation

  - Implement Company dataclass with all required fields (name, short_name, registration_no, etc.)
  - Add validation methods for required fields, URL validation, and date range validation
  - Implement from_sqlite_row method for database integration
  - Create computed fields for contact name display
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8_

- [x] 4. Update PersonService with new field support

  - Modify get_insert_query and get_update_query to include new fields (first_name, last_name, registration_no, profile_image)
  - Update model_to_insert_params and model_to_update_params methods
  - Add suggest_name_format helper method
  - Update get_list_query and get_by_id_query to select new columns
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 2.4, 6.1, 6.2_

- [x] 5. Create CompanyService for business logic

  - Implement CompanyService extending BaseService for companies table
  - Create CRUD query methods (get_list_query, get_by_id_query, insert, update, delete)
  - Add get_active_companies method for filtering by valid dates
  - Implement foreign key constraint handling for person contacts
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8_

- [x] 6. Update person creation and edit forms

  - Add firstName and lastName input fields to person forms
  - Implement JavaScript for "{lastName}, {firstName}" name suggestion
  - Add registration_no field with 25 character limit validation
  - Add profile_image field with avatar preview and file path input
  - Update form validation to handle new fields appropriately
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 2.4, 5.1, 5.2, 6.1, 6.4_

- [x] 7. Update person routes with new field handling

  - Modify create_person and update_person routes to accept new form fields
  - Update form parameter extraction for first_name, last_name, registration_no, profile_image
  - Ensure backward compatibility with existing name field usage
  - Add proper error handling and validation for new fields
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 2.4, 5.1, 5.2, 5.3, 5.4, 6.1, 6.2_

- [x] 8. Create company management routes

  - Implement companies list, create, edit, detail, and delete routes
  - Add person selection functionality for main_contact_id and financial_contact_id
  - Create route handlers with proper validation and error handling
  - Ensure foreign key constraint handling when persons are deleted
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 5.4, 5.5_

- [x] 9. Create company management templates

  - Design companies list template with contact information display
  - Create company creation form with person selection dropdowns
  - Implement company edit form with all fields and validation
  - Add company detail view showing all information and relationships
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 5.4, 5.5_

- [x] 10. Update person display templates

  - Modify person list and detail templates to show registration_no when available
  - Update person forms to display firstName/lastName fields prominently with profile image avatar
  - Ensure name field continues to work for backward compatibility
  - Add visual indicators for suggested name format
  - Display profile images in person cards and lists
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 2.4, 5.1, 5.2, 5.3, 6.4_

- [x] 11. Add navigation and integration for companies

  - Add companies section to main navigation menu
  - Create breadcrumb navigation for company pages
  - Integrate company management into existing application structure
  - Add appropriate icons and styling consistent with existing design
  - _Requirements: 3.1, 5.4, 5.5_

- [x] 12. Create comprehensive test suite

  - Write unit tests for Person model validation with new fields (including profile_image validation)
  - Create unit tests for Company model and validation logic
  - Add service layer tests for PersonService and CompanyService
  - Implement integration tests for form submission and CRUD operations
  - Test profile image handling and display
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 6.1, 6.2, 6.4_

- [x] 13. Run database migration and verify functionality

  - Verify all new columns and tables are created correctly
  - Test backward compatibility with existing person records
  - Validate foreign key constraints and indexes are working
  - Verify profile image directory creation and permissions
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 6.3_
