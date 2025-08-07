# Requirements Document

## Introduction

This document outlines the technical requirements for the Organigramma Web App, a comprehensive organizational chart management system built with FastAPI, SQLite, and Bootstrap. The system provides CRUD operations for organizational entities with automatic versioning of assignments and a responsive web interface.

Organigramma Web App should implement centralized style UX/UI based on models deriving from database tables.
Organigramma Web App should implement multi-language user interface based on models deriving from database tables.

Each table in Organigramma Web App database should have a datetime_created DATETIME and datetime_updated DATETIME column which are managed by database triggers and not visible to app models.

Organigramma Web App must be compliant with WCAG.
Organigramma Web App must implement API calls with Swagger documentation.

## Requirements

### Requirement 1

**User Story:** As a company HR manager, I want a robust database management system, so that organizational data is stored securely with referential integrity and automatic versioning.

#### Database Management Acceptance Criteria

1. WHEN the application starts THEN the system SHALL initialize the SQLite database with proper schema
2. WHEN database operations are performed THEN the system SHALL enforce foreign key constraints
3. WHEN assignment data is modified THEN the system SHALL automatically create new versions while preserving historical data
4. WHEN database connections are established THEN the system SHALL enable row factory for dict-like access
5. IF database initialization fails THEN the system SHALL log errors and prevent application startup

### Requirement 2

**User Story:** As a user, I want a responsive web interface, so that I can manage organizational data from any device with an intuitive user experience.

#### Web Interface Acceptance Criteria

1. WHEN users access the application THEN the system SHALL serve a Bootstrap 5 responsive interface
2. WHEN users navigate between sections THEN the system SHALL provide consistent navigation and layout
3. WHEN forms are submitted THEN the system SHALL validate input data and provide clear feedback
4. WHEN errors occur THEN the system SHALL display user-friendly error messages
5. WHEN static assets are requested THEN the system SHALL serve CSS, JavaScript, and images efficiently
6. WHEN the application is accessed THEN the system SHALL follow WCAG accessibility directives

### Requirement 3

**User Story:** As an HR manager, I want comprehensive CRUD operations for all entities, so that I can maintain accurate organizational structure and personnel data.

#### Acceptance Criteria

1. WHEN managing units THEN the system SHALL support creation, reading, updating, and deletion with hierarchical validation
2. WHEN managing persons THEN the system SHALL provide complete personnel data management with email validation
3. WHEN managing job titles THEN the system SHALL allow role definition with multilingual support
4. WHEN managing assignments THEN the system SHALL create, modify, and terminate assignments with automatic versioning
5. WHEN managing assignments THEN the system SHALL verify if the assisment is the boss of the unit
6. WHEN managing assignments THEN the system SHALL verify if the assisment is ad interim
7. WHEN deleting entities THEN the system SHALL check referential integrity and prevent orphaned records
8. WHEN managing person profile images THEN the system SHALL allow users to upload, change, and remove image files directly through the web interface
9. WHEN a profile image is uploaded THEN the system SHALL store it in the static/profiles directory with the naming convention "[last_name].[first_name].[extension]"
10. WHEN a profile image is uploaded THEN the system SHALL store the file path in the profile_image field of the persons table
11. WHEN displaying persons THEN the system SHALL show profile images when available and fallback to initials when not available

### Requirement 4

**User Story:** As a business user, I want automatic assignment versioning, so that I can track the complete history of organizational changes over time.

#### Assignment Versioning Acceptance Criteria

1. WHEN a new assignment is created THEN the system SHALL automatically set it as version 1 with is_current = TRUE
2. WHEN an existing assignment is modified THEN the system SHALL create a new version and mark previous versions as historical
3. WHEN an assignment is terminated THEN the system SHALL set valid_to date and is_current = FALSE
4. WHEN viewing assignment history THEN the system SHALL display all versions with clear version tracking
5. WHEN querying current assignments THEN the system SHALL only return active assignments with is_current = TRUE

### Requirement 5

**User Story:** As a system administrator, I want comprehensive logging and error handling, so that I can monitor system health and troubleshoot issues effectively.

#### Logging and Error Handling Acceptance Criteria

1. WHEN the application runs THEN the system SHALL log to both console and file with appropriate log levels
2. WHEN database operations fail THEN the system SHALL log detailed error information and rollback transactions
3. WHEN HTTP errors occur THEN the system SHALL serve custom error pages with proper status codes
4. WHEN exceptions are raised THEN the system SHALL handle them gracefully without exposing sensitive information
5. WHEN the application starts or stops THEN the system SHALL log lifecycle events

### Requirement 6

**User Story:** As a user, I want an organizational chart visualization, so that I can understand the company structure and hierarchy at a glance.

#### Organizational Chart Acceptance Criteria

1. WHEN accessing the orgchart THEN the system SHALL display a tree-like visualization of the organizational structure
2. WHEN viewing units THEN the system SHALL show statistics and personnel counts for each unit
3. WHEN navigating the orgchart THEN the system SHALL provide interactive elements for exploration
4. WHEN units have parent-child relationships THEN the system SHALL display proper hierarchical structure
5. WHEN organizational data changes THEN the system SHALL reflect updates in the orgchart view
6. WHEN displaying units with unit_type_id=1 (Functions) THEN the system SHALL render them with bold-framed boxes
7. WHEN displaying units with unit_type_id=2 (Organizational Units) THEN the system SHALL render them with normal-framed boxes
8. WHEN a unit has an emoji or image THEN the system SHALL display it within the unit box

### Requirement 7

**User Story:** As a developer, I want a modular architecture, so that the system is maintainable, testable, and extensible.

#### Modular Architecture Acceptance Criteria

1. WHEN organizing code THEN the system SHALL separate models, services, routes, and utilities into distinct modules
2. WHEN implementing business logic THEN the system SHALL encapsulate it in service classes separate from route handlers
3. WHEN handling HTTP requests THEN the system SHALL use FastAPI routers organized by functional area
4. WHEN managing database operations THEN the system SHALL use a centralized database manager with connection pooling
5. WHEN adding new features THEN the system SHALL follow established patterns for models, services, and routes

### Requirement 8

**User Story:** As an HR manager, I want to upload and manage profile images for persons, so that I can maintain visual identification and professional presentation in the organizational system.

#### Profile Image Management Acceptance Criteria

1. WHEN creating or editing a person THEN the system SHALL provide a file upload interface for profile images
2. WHEN a user selects an image file THEN the system SHALL validate the file type and size before upload
3. WHEN an image is uploaded THEN the system SHALL save it to the static/profiles directory with the naming convention "[last_name].[first_name].[extension]"
4. WHEN an image is uploaded THEN the system SHALL store the relative file path in the profile_image field of the persons table
5. WHEN a user uploads a new image for an existing person THEN the system SHALL replace the old image file and update the database
6. WHEN a user removes a profile image THEN the system SHALL delete the file from the filesystem and clear the profile_image field
7. WHEN displaying persons THEN the system SHALL show the profile image if available, otherwise display initials in a circular avatar
8. WHEN the profile image file is missing THEN the system SHALL gracefully fallback to displaying initials
9. WHEN validating image uploads THEN the system SHALL only accept common image formats (jpg, jpeg, png, gif, webp)
10. WHEN handling file uploads THEN the system SHALL implement proper error handling for file system operations

### Requirement 9

**User Story:** As a system administrator, I want configurable deployment options, so that I can deploy the application in different environments with appropriate settings and security best practices.

#### Deployment and Security Acceptance Criteria

1. WHEN deploying the application THEN the system SHALL support environment-based configuration via .env files
2. WHEN running in production THEN the system SHALL disable debug mode and use appropriate log levels
3. WHEN scaling the application THEN the system SHALL support ASGI servers like Gunicorn with multiple workers
4. WHEN managing database files THEN the system SHALL provide backup and migration scripts
5. WHEN configuring security THEN the system SHALL support secret key management and input validation
6. WHEN implementing security THEN the system SHALL follow security-by-design and security-by-default principles
7. WHEN deploying to cloud environments THEN the system SHALL support cloud-native deployment patterns
