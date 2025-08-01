# Requirements Document

## Introduction

This feature enhances the database structure to support more detailed person information and company management. The changes include splitting person names into firstName/lastName fields, adding registration numbers for persons, and introducing a comprehensive companies table with contact relationships.

## Requirements

### Requirement 1: Person Name Structure Enhancement

**User Story:** As an HR administrator, I want to manage person names with separate first and last name fields, so that I can have better control over name display formats and sorting.

#### Acceptance Criteria

1. WHEN viewing the person creation form THEN the system SHALL display separate firstName and lastName input fields
2. WHEN a user enters firstName and lastName THEN the system SHALL suggest "{lastName}, {firstName}" format in the name field
3. WHEN saving a person record THEN the system SHALL store firstName, lastName, and name fields separately
4. WHEN displaying person names THEN the system SHALL use the existing name field for backward compatibility
5. IF firstName and lastName are provided AND name field is empty THEN the system SHALL auto-populate name with "{lastName}, {firstName}" format

### Requirement 2: Person Registration Number

**User Story:** As an HR administrator, I want to store optional registration numbers for persons, so that I can track employee IDs or other identification numbers.

#### Acceptance Criteria

1. WHEN creating or editing a person THEN the system SHALL provide an optional registration_no field
2. WHEN entering registration_no THEN the system SHALL accept TEXT values up to 25 characters
3. WHEN saving a person THEN the system SHALL store the registration_no if provided
4. WHEN displaying person details THEN the system SHALL show the registration_no if available

### Requirement 3: Companies Management System

**User Story:** As a business administrator, I want to manage company information with detailed contact relationships, so that I can track organizational partnerships and contacts.

#### Acceptance Criteria

1. WHEN accessing the companies section THEN the system SHALL provide CRUD operations for companies
2. WHEN creating a company THEN the system SHALL require name, short_name, and registration_no fields
3. WHEN creating a company THEN the system SHALL provide optional fields for address, website, function, scope
4. WHEN creating a company THEN the system SHALL allow setting valid_from and valid_to dates
5. WHEN creating a company THEN the system SHALL allow selecting main_contact_id and financial_contact_id from persons
6. WHEN selecting contacts THEN the system SHALL only allow selection from existing persons
7. WHEN deleting a person THEN the system SHALL handle foreign key constraints for company contacts appropriately
8. WHEN displaying companies THEN the system SHALL show all company information including contact names

### Requirement 4: Database Migration and Compatibility

**User Story:** As a system administrator, I want the database changes to be applied safely without losing existing data, so that the system continues to work with current information.

#### Acceptance Criteria

1. WHEN applying database migrations THEN the system SHALL preserve all existing person data
2. WHEN migrating person records THEN the system SHALL keep existing name values unchanged
3. WHEN adding new fields THEN the system SHALL set appropriate default values
4. WHEN creating the companies table THEN the system SHALL establish proper foreign key relationships
5. WHEN updating the schema THEN the system SHALL maintain referential integrity

### Requirement 5: User Interface Integration

**User Story:** As a user, I want the new fields to be integrated seamlessly into existing forms and displays, so that I can use the enhanced functionality intuitively.

#### Acceptance Criteria

1. WHEN viewing person forms THEN the system SHALL display firstName and lastName fields prominently
2. WHEN viewing person forms THEN the system SHALL show the name field with suggested format
3. WHEN viewing person lists THEN the system SHALL continue to display names using existing format
4. WHEN accessing companies THEN the system SHALL provide a dedicated companies management interface
5. WHEN selecting company contacts THEN the system SHALL provide dropdown/search functionality for person selection