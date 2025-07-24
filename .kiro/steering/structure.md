# Project Structure & Organization

## 1. Directory Structure

```plaintext
orgchart_webapp/
├── app/                    # Core application code
│   ├── models/            # Data models using dataclasses
│   │   ├── base.py       # Base model with common functionality
│   │   └── ...           # Entity-specific models
│   ├── routes/            # FastAPI route handlers
│   │   ├── home.py       # Home/dashboard routes
│   │   ├── units.py      # Unit management routes
│   │   ├── job_titles.py # Job title management routes
│   │   ├── persons.py    # Person management routes
│   │   ├── assignments.py # Assignment management routes
│   │   ├── orgchart.py   # Orgchart visualization routes
│   │   └── api.py        # API endpoints
│   ├── services/          # Business logic layer
│   │   └── ...           # Service implementations
│   ├── utils/             # Utility functions and helpers
│   │   └── ...           # Utility modules
│   ├── database.py        # Database connection and management
│   └── main.py            # FastAPI application entry point
├── static/                # Static assets
│   ├── css/              # CSS stylesheets
│   │   ├── base.css      # Global styles
│   │   └── components.css # Component-specific styles
│   ├── js/               # JavaScript files
│   │   ├── base.js       # Global JavaScript
│   │   └── components.js # Component-specific JavaScript
│   └── images/           # Images and icons
├── templates/             # Jinja2 HTML templates
│   ├── base/             # Base layout templates
│   ├── components/       # Reusable UI components
│   ├── errors/           # Error pages (404, 500)
│   ├── home/             # Home/dashboard templates
│   ├── units/            # Unit management templates
│   ├── job_titles/       # Job title management templates
│   ├── persons/          # Person management templates
│   ├── assignments/      # Assignment management templates
│   └── orgchart/         # Orgchart visualization templates
├── database/              # Database files and schemas
│   ├── schema/           # SQL schema definitions
│   └── orgchart.db       # SQLite database file
├── scripts/               # Utility scripts
│   ├── init_db.py        # Database initialization
│   ├── seed_data.py      # Test data generation
│   └── backup_db.py      # Database backup
├── tests/                 # Test suite
│   ├── test_models.py    # Model tests
│   ├── test_routes.py    # Route tests
│   └── test_services.py  # Service tests
├── config/                # Configuration files
├── .env                   # Environment variables
├── requirements.txt       # Python dependencies
└── run.py                 # Application runner script
```

## 2. Architecture Patterns

### 2.1 Layered Architecture

1. **Presentation Layer**: Templates and routes
2. **Business Logic Layer**: Services
3. **Data Access Layer**: Models and database

### 2.2 Key Design Patterns

- **Repository Pattern**: For data access
- **Service Layer**: For business logic
- **Singleton**: For database connection management
- **Factory**: For model creation
- **Dependency Injection**: For service dependencies

## 3. Module Responsibilities

### 3.1 Models

- Define data structures using dataclasses
- Implement validation logic
- Provide serialization/deserialization methods

### 3.2 Routes

- Handle HTTP requests and responses
- Validate input data
- Call appropriate services
- Return templates or API responses

### 3.3 Services

- Implement business logic
- Coordinate between multiple models
- Handle complex operations and transactions

### 3.4 Database

- Manage database connections
- Provide connection pooling
- Handle database initialization and migrations

## 4. Naming Conventions

### 4.1 Files and Directories

- Use snake_case for Python files and directories
- Use descriptive names that reflect purpose

### 4.2 Routes

- Use plural nouns for resource collections (e.g., `/units`, `/persons`)
- Use singular nouns with IDs for specific resources (e.g., `/units/{id}`)
- Use verbs for actions (e.g., `/assignments/{id}/terminate`)

### 4.3 Templates

- Organize by feature/entity
- Use consistent naming across related templates
