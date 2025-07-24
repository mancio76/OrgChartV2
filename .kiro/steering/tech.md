# Tech Stack & Development Guidelines

## Tech Stack

### Backend

- **FastAPI**: Web framework for building APIs with Python
- **Uvicorn**: ASGI server for running FastAPI applications
- **SQLite**: Embedded database with foreign key constraints enabled
- **Jinja2**: Template engine for HTML rendering

### Frontend

- **Bootstrap 5**: CSS framework for responsive design
- **Bootstrap Icons**: Icon library
- **Vanilla JavaScript**: No external JS frameworks/libraries
- **CSS Modules**: Organized by component and section

## Dependencies

- fastapi==0.104.1
- uvicorn[standard]==0.24.0
- jinja2==3.1.2
- python-multipart==0.0.6
- aiofiles==23.2.1
- python-dotenv==1.0.0

## Database

- SQLite with foreign key constraints enabled
- Connection pooling with singleton pattern
- Write-Ahead Logging (WAL) journal mode
- Automatic versioning for assignments

## Common Commands

### Setup & Installation

```bash
# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# or
source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### Running the Application

```bash
# Start the application
python run.py

# Or directly with uvicorn
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Database Operations

```bash
# Initialize database
python scripts/init_db.py

# Seed test data
python scripts/seed_data.py

# Backup database
python scripts/backup_db.py
```

### Testing

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_models.py
```

## Code Style & Conventions

### Python

- Follow PEP 8 style guide
- Use type hints for function parameters and return values
- Include docstrings for modules, classes, and functions
- Use dataclasses for models
- Implement proper validation in model classes

### HTML/Templates

- Use semantic HTML5 elements
- Follow accessibility best practices
- Organize templates by feature/section
- Use Jinja2 template inheritance

### CSS

- Follow BEM methodology for class naming
- Mobile-first responsive design
- Modular CSS organization by component

### JavaScript

- ES6+ syntax
- camelCase for variables and functions
- JSDoc comments for functions
- Avoid global scope pollution
