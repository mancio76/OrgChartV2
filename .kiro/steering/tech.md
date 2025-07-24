---
inclusion: always
---

# Tech Stack & Development Guidelines

## Core Technologies

### Backend Stack

- **FastAPI**: Primary web framework - use for all API endpoints and route handlers
- **Uvicorn**: ASGI server - standard for running the application
- **SQLite**: Database with foreign key constraints ALWAYS enabled
- **Jinja2**: Template engine for HTML rendering

### Frontend Stack

- **Bootstrap 5**: CSS framework - use for responsive layouts and components
- **Bootstrap Icons**: Icon library - prefer over custom icons
- **Vanilla JavaScript**: No external JS frameworks - keep it simple
- **Modular CSS**: Organize by component, use BEM methodology

### Key Dependencies

```plaintext
fastapi==0.104.1
uvicorn[standard]==0.24.0
jinja2==3.1.2
python-multipart==0.0.6
aiofiles==23.2.1
python-dotenv==1.0.0
```

## Architecture Patterns

### Database Layer

- Use singleton pattern for database connections
- Enable WAL journal mode for SQLite
- Implement automatic versioning for assignments (critical requirement)
- Always enable foreign key constraints

### Code Organization

- **Models**: Use dataclasses with validation methods
- **Services**: Business logic layer between routes and models
- **Routes**: Handle HTTP requests, delegate to services
- **Templates**: Organize by feature (units/, persons/, assignments/, etc.)

## Development Commands

### Application Lifecycle

```bash
# Start application
python run.py

# Initialize database (required for new setups)
python scripts/init_db.py

# Seed test data
python scripts/seed_data.py
```

### Testing

```bash
pytest tests/                    # Run all tests
pytest tests/test_models.py      # Run specific test file
```

## Code Standards

### Python Requirements

- **Type hints**: Required for all function parameters and return values
- **Docstrings**: Required for modules, classes, and public functions
- **PEP 8**: Follow style guide strictly
- **Dataclasses**: Use for all model definitions
- **Validation**: Implement in model classes, not routes
- **Logging**: Use centralized logging system

### Template Standards

- **Semantic HTML5**: Use appropriate elements
- **Accessibility**: Follow WCAG guidelines
- **Jinja2 inheritance**: Use base templates consistently
- **Feature organization**: Group templates by entity type

### CSS/JS Standards

- **BEM methodology**: For CSS class naming
- **Mobile-first**: Design approach
- **ES6+ syntax**: For JavaScript
- **JSDoc comments**: For JavaScript functions
- **File organization**:
  - `/static/css/base.css` - Global styles
  - `/static/css/components.css` - Component styles
  - `/static/js/base.js` - Global scripts
  - `/static/js/components.js` - Component scripts

## Critical Rules

1. **Assignment versioning**: Every assignment change MUST create a new version
2. **Foreign keys**: MUST be enabled in SQLite
3. **Italian language**: Primary language for UI text and error messages
4. **Hierarchical units**: Maintain parent-child relationships
5. **No external JS frameworks**: Keep frontend dependencies minimal  
