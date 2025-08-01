# Design Document

## Overview

This design document outlines the implementation of database structure enhancements to support separate firstName/lastName fields for persons, registration numbers, profile images, and a comprehensive companies management system. The solution maintains backward compatibility while providing enhanced functionality for name management, visual identification, and company relationships.

## Architecture

### Database Schema Changes

#### 1. Person Table Modifications

The `persons` table will be enhanced with additional columns while maintaining backward compatibility:

```sql
-- Enhanced persons table
ALTER TABLE persons ADD COLUMN first_name TEXT;
ALTER TABLE persons ADD COLUMN last_name TEXT;
ALTER TABLE persons ADD COLUMN registration_no TEXT CHECK(length(registration_no) <= 25);
ALTER TABLE persons ADD COLUMN profile_image TEXT CHECK(length(profile_image) <= 1024);
```

**Migration Strategy:**

- Existing `name` field remains unchanged for backward compatibility
- New fields are optional (NULL allowed)
- UI will suggest "{lastName}, {firstName}" format when both new fields are provided
- Existing records continue to work with current `name` field

#### 2. New Companies Table

A new `companies` table will be created to manage company information:

```sql
CREATE TABLE companies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    short_name TEXT NOT NULL,
    registration_no TEXT NOT NULL,
    address TEXT,
    website TEXT,
    function TEXT,
    scope TEXT,
    valid_from DATE,
    valid_to DATE,
    main_contact_id INTEGER,
    financial_contact_id INTEGER,
    datetime_created DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    datetime_updated DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (main_contact_id) REFERENCES persons(id) ON DELETE SET NULL,
    FOREIGN KEY (financial_contact_id) REFERENCES persons(id) ON DELETE SET NULL
);
```

**Indexes for Performance:**

```sql
CREATE INDEX idx_companies_name ON companies(name);
CREATE INDEX idx_companies_registration_no ON companies(registration_no);
CREATE INDEX idx_companies_main_contact ON companies(main_contact_id);
CREATE INDEX idx_companies_financial_contact ON companies(financial_contact_id);
CREATE INDEX idx_companies_valid_dates ON companies(valid_from, valid_to);
```

**Design Rationale:**

- `short_name` is required (NOT NULL) as specified in Requirement 3.2
- Foreign key constraints use ON DELETE SET NULL to handle person deletion gracefully (Requirement 3.7)
- Automatic timestamp management ensures audit trail compliance

### Data Models

#### Enhanced Person Model

```python
@dataclass
class Person(BaseModel):
    """Enhanced Person model with name structure support"""
    id: Optional[int] = None
    name: str = ""  # Backward compatibility - primary display field
    first_name: Optional[str] = None  # New field
    last_name: Optional[str] = None   # New field
    short_name: Optional[str] = None
    email: Optional[str] = None
    registration_no: Optional[str] = None  # New field
    profile_image: Optional[str] = None    # New field
    
    # Computed fields
    current_assignments_count: int = field(default=0, init=False)
    total_assignments_count: int = field(default=0, init=False)
    
    @property
    def suggested_name_format(self) -> str:
        """Generate suggested name format from firstName/lastName"""
        if self.last_name and self.first_name:
            return f"{self.last_name}, {self.first_name}"
        return ""
    
    @property
    def display_name(self) -> str:
        """Get display name (prioritize name field for compatibility)"""
        return self.name if self.name else self.suggested_name_format
    
    def validate(self) -> List[ValidationError]:
        """Enhanced validation including new fields"""
        errors = []
        
        # Name is still required (backward compatibility)
        if not self.name or not self.name.strip():
            errors.append(ValidationError("name", "Name is required"))
        
        # Registration number validation
        if self.registration_no and len(self.registration_no) > 25:
            errors.append(ValidationError("registration_no", "Registration number cannot exceed 25 characters"))
        
        # Profile image validation
        if self.profile_image and len(self.profile_image) > 1024:
            errors.append(ValidationError("profile_image", "Profile image path cannot exceed 1024 characters"))
        
        # Email validation (existing)
        if self.email and not self._is_valid_email(self.email):
            errors.append(ValidationError("email", "Invalid email format"))
        
        return errors
```

#### New Company Model

```python
@dataclass
class Company(BaseModel):
    """Company model for managing organizational relationships"""
    id: Optional[int] = None
    name: str = ""
    short_name: str = ""  # Required field per Requirement 3.2
    registration_no: str = ""
    address: Optional[str] = None
    website: Optional[str] = None
    function: Optional[str] = None
    scope: Optional[str] = None
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None
    main_contact_id: Optional[int] = None
    financial_contact_id: Optional[int] = None
    
    # Computed fields for display
    main_contact_name: Optional[str] = field(default=None, init=False)
    financial_contact_name: Optional[str] = field(default=None, init=False)
    
    def validate(self) -> List[ValidationError]:
        """Validate company data"""
        errors = []
        
        if not self.name or not self.name.strip():
            errors.append(ValidationError("name", "Company name is required"))
        
        if not self.short_name or not self.short_name.strip():
            errors.append(ValidationError("short_name", "Short name is required"))
        
        if not self.registration_no or not self.registration_no.strip():
            errors.append(ValidationError("registration_no", "Registration number is required"))
        
        if self.website and not self._is_valid_url(self.website):
            errors.append(ValidationError("website", "Invalid website URL"))
        
        if self.valid_from and self.valid_to and self.valid_from > self.valid_to:
            errors.append(ValidationError("valid_to", "End date must be after start date"))
        
        return errors
    
    def _is_valid_url(self, url: str) -> bool:
        """Basic URL validation"""
        import re
        pattern = r'^https?://[^\s/$.?#].[^\s]*$'$'$'
        return bool(re.match(pattern, url))
```

## Components and Interfaces

### Service Layer

#### Enhanced PersonService

```python
class PersonService(BaseService):
    """Enhanced PersonService with new field support"""
    
    def get_insert_query(self) -> str:
        return """
        INSERT INTO persons (name, first_name, last_name, short_name, email, registration_no, profile_image)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
    
    def get_update_query(self) -> str:
        return """
        UPDATE persons 
        SET name = ?, first_name = ?, last_name = ?, short_name = ?, email = ?, registration_no = ?, profile_image = ?
        WHERE id = ?
        """
    
    def model_to_insert_params(self, person: Person) -> tuple:
        return (
            person.name,
            person.first_name,
            person.last_name,
            person.short_name,
            person.email,
            person.registration_no,
            person.profile_image
        )
    
    def suggest_name_format(self, first_name: str, last_name: str) -> str:
        """Generate suggested name format"""
        if last_name and first_name:
            return f"{last_name.strip()}, {first_name.strip()}"
        return ""
```

#### New CompanyService

```python
class CompanyService(BaseService):
    """Service for managing companies"""
    
    def __init__(self):
        super().__init__(Company, "companies")
    
    def get_list_query(self) -> str:
        return """
        SELECT c.*,
               p1.name as main_contact_name,
               p2.name as financial_contact_name
        FROM companies c
        LEFT JOIN persons p1 ON c.main_contact_id = p1.id
        LEFT JOIN persons p2 ON c.financial_contact_id = p2.id
        ORDER BY c.name
        """
    
    def get_by_id_query(self) -> str:
        return """
        SELECT c.*,
               p1.name as main_contact_name,
               p2.name as financial_contact_name
        FROM companies c
        LEFT JOIN persons p1 ON c.main_contact_id = p1.id
        LEFT JOIN persons p2 ON c.financial_contact_id = p2.id
        WHERE c.id = ?
        """
    
    def get_active_companies(self) -> List[Company]:
        """Get companies that are currently active"""
        query = """
        SELECT c.*,
               p1.name as main_contact_name,
               p2.name as financial_contact_name
        FROM companies c
        LEFT JOIN persons p1 ON c.main_contact_id = p1.id
        LEFT JOIN persons p2 ON c.financial_contact_id = p2.id
        WHERE (c.valid_from IS NULL OR c.valid_from <= DATE('now'))
        AND (c.valid_to IS NULL OR c.valid_to >= DATE('now'))
        ORDER BY c.name
        """
        rows = self.db_manager.fetch_all(query)
        return [Company.from_sqlite_row(row) for row in rows]
```

### Route Layer

#### Enhanced Person Routes

The person routes will be updated to handle the new fields:

```python
@router.post("/new")
async def create_person(
    request: Request,
    name: str = Form(...),
    first_name: Optional[str] = Form(None),
    last_name: Optional[str] = Form(None),
    short_name: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    registration_no: Optional[str] = Form(None),
    profile_image: Optional[str] = Form(None),
    # ... other parameters
):
    """Enhanced create person with new fields"""
    person = Person(
        name=name.strip(),
        first_name=first_name.strip() if first_name else None,
        last_name=last_name.strip() if last_name else None,
        short_name=short_name.strip() if short_name else None,
        email=email.strip() if email else None,
        registration_no=registration_no.strip() if registration_no else None,
        profile_image=profile_image.strip() if profile_image else None
    )
    # ... rest of implementation
```

#### New Company Routes

```python
@router.get("/companies/", response_class=HTMLResponse)
async def list_companies(
    request: Request,
    company_service: CompanyService = Depends(get_company_service)
):
    """List all companies"""
    companies = company_service.get_all()
    return templates.TemplateResponse("companies/list.html", {
        "request": request,
        "companies": companies,
        "page_title": "Aziende"
    })

@router.get("/companies/new", response_class=HTMLResponse)
async def create_company_form(request: Request):
    """Show create company form"""
    # Get persons for contact selection
    person_service = PersonService()
    persons = person_service.get_all()
    
    return templates.TemplateResponse("companies/create.html", {
        "request": request,
        "persons": persons,
        "page_title": "Nuova Azienda"
    })
```

### User Interface Integration

#### Name Auto-Population Logic

To address Requirement 1.5, the system will implement auto-population logic:

```javascript
// JavaScript for name field auto-population
function updateNameSuggestion() {
    const firstName = document.getElementById('first_name').value.trim();
    const lastName = document.getElementById('last_name').value.trim();
    const nameField = document.getElementById('name');
    
    if (firstName && lastName && !nameField.value.trim()) {
        nameField.value = `${lastName}, ${firstName}`;
        nameField.classList.add('auto-populated');
    }
}

// Event listeners for real-time suggestion
document.getElementById('first_name').addEventListener('input', updateNameSuggestion);
document.getElementById('last_name').addEventListener('input', updateNameSuggestion);
```

#### Person Selection Dropdowns

For company contact selection (Requirement 3.5, 3.6):

```python
@router.get("/companies/new", response_class=HTMLResponse)
async def create_company_form(request: Request):
    """Show create company form with person selection"""
    person_service = PersonService()
    persons = person_service.get_all()
    
    # Sort persons by display name for better UX
    persons.sort(key=lambda p: p.display_name.lower())
    
    return templates.TemplateResponse("companies/create.html", {
        "request": request,
        "persons": persons,
        "page_title": "Nuova Azienda"
    })
```

#### Profile Image Management

The system will support profile image storage and display (Requirement 6):

**File Storage Strategy:**

- Profile images will be stored in `app/static/img/profiles/` directory
- Only the relative file path will be stored in the database (up to 1024 characters)
- Images will be displayed as avatar components in person cards and forms

**Design Rationale:** Storing only file paths in the database keeps the database lightweight while providing flexibility for different image formats and sizes. The 1024-character limit accommodates long filenames and nested directory structures.

#### Template Integration

The forms will be enhanced to prominently display firstName/lastName fields and profile images (Requirements 5.1, 6.1, 6.4):

```html
<!-- Person form enhancement with profile image -->
<div class="row">
    <div class="col-md-3">
        <div class="mb-3">
            <label for="profile_image" class="form-label">Immagine Profilo</label>
            <div class="profile-image-preview mb-2">
                {% if person.profile_image %}
                    <img src="{{ url_for('static', path='img/profiles/' + person.profile_image) }}" 
                         alt="Profile" class="rounded-circle" width="80" height="80">
                {% else %}
                    <div class="rounded-circle bg-secondary d-flex align-items-center justify-content-center" 
                         style="width: 80px; height: 80px;">
                        <i class="bi bi-person-fill text-white"></i>
                    </div>
                {% endif %}
            </div>
            <input type="text" class="form-control" id="profile_image" name="profile_image" 
                   value="{{ person.profile_image or '' }}" maxlength="1024"
                   placeholder="percorso/immagine.jpg">
            <div class="form-text">Percorso relativo in app/static/img/profiles/</div>
        </div>
    </div>
    <div class="col-md-9">
        <div class="row">
            <div class="col-md-6">
                <label for="first_name" class="form-label">Nome</label>
                <input type="text" class="form-control" id="first_name" name="first_name" 
                       value="{{ person.first_name or '' }}">
            </div>
            <div class="col-md-6">
                <label for="last_name" class="form-label">Cognome</label>
                <input type="text" class="form-control" id="last_name" name="last_name" 
                       value="{{ person.last_name or '' }}">
            </div>
        </div>
        <div class="mb-3">
            <label for="name" class="form-label">Nome Completo</label>
            <input type="text" class="form-control" id="name" name="name" 
                   value="{{ person.name or '' }}" required>
            <div class="form-text">Formato suggerito: Cognome, Nome</div>
        </div>
    </div>
</div>
```

## Database Migration and Compatibility

### Migration Strategy

The migration approach ensures zero data loss and maintains backward compatibility:

1. **Additive Changes Only**: New columns are added as nullable fields
2. **Preserve Existing Data**: All current person records remain unchanged
3. **Gradual Adoption**: Users can continue using existing name field while optionally adopting new structure
4. **Safe Rollback**: Migration can be reversed if needed

**Design Rationale**: This approach allows for seamless deployment without disrupting existing workflows while enabling enhanced functionality for new use cases.

### Database Migration Script

A migration script will handle the schema changes safely:

```python
def migrate_database_structure():
    """Apply database structure enhancements"""
    db_manager = get_db_manager()
    
    with db_manager.get_connection() as conn:
        # Add new columns to persons table
        try:
            conn.execute("ALTER TABLE persons ADD COLUMN first_name TEXT")
            print("✅ Added first_name column to persons table")
        except Exception as e:
            if "duplicate column name" not in str(e).lower():
                raise
        
        try:
            conn.execute("ALTER TABLE persons ADD COLUMN last_name TEXT")
            print("✅ Added last_name column to persons table")
        except Exception as e:
            if "duplicate column name" not in str(e).lower():
                raise
        
        try:
            conn.execute("ALTER TABLE persons ADD COLUMN registration_no TEXT CHECK(length(registration_no) <= 25)")
            print("✅ Added registration_no column to persons table")
        except Exception as e:
            if "duplicate column name" not in str(e).lower():
                raise
        
        try:
            conn.execute("ALTER TABLE persons ADD COLUMN profile_image TEXT CHECK(length(profile_image) <= 1024)")
            print("✅ Added profile_image column to persons table")
        except Exception as e:
            if "duplicate column name" not in str(e).lower():
                raise
        
        # Create companies table
        conn.execute("""
        CREATE TABLE IF NOT EXISTS companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            short_name TEXT NOT NULL,
            registration_no TEXT NOT NULL,
            address TEXT,
            website TEXT,
            function TEXT,
            scope TEXT,
            valid_from DATE,
            valid_to DATE,
            main_contact_id INTEGER,
            financial_contact_id INTEGER,
            datetime_created DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            datetime_updated DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (main_contact_id) REFERENCES persons(id) ON DELETE SET NULL,
            FOREIGN KEY (financial_contact_id) REFERENCES persons(id) ON DELETE SET NULL
        )
        """)
        print("✅ Created companies table")
        
        # Create indexes
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_companies_name ON companies(name)",
            "CREATE INDEX IF NOT EXISTS idx_companies_registration_no ON companies(registration_no)",
            "CREATE INDEX IF NOT EXISTS idx_companies_main_contact ON companies(main_contact_id)",
            "CREATE INDEX IF NOT EXISTS idx_companies_financial_contact ON companies(financial_contact_id)",
            "CREATE INDEX IF NOT EXISTS idx_companies_valid_dates ON companies(valid_from, valid_to)"
        ]
        
        for index_sql in indexes:
            conn.execute(index_sql)
        
        print("✅ Created database indexes")
        
        # Create update trigger for companies
        conn.execute("""
        CREATE TRIGGER IF NOT EXISTS update_companies_timestamp
        AFTER UPDATE ON companies
        WHEN NEW.datetime_updated <> OLD.datetime_updated
        BEGIN
            UPDATE companies
            SET datetime_updated = CURRENT_TIMESTAMP
            WHERE id = NEW.id;
        END
        """)
        print("✅ Created companies update trigger")
        
        conn.commit()
        print("✅ Database migration completed successfully")
```

## Error Handling

### Validation Strategy

1. **Client-side validation**: JavaScript validation for immediate feedback
2. **Server-side validation**: Model validation in Python for security
3. **Database constraints**: SQL constraints as final safety net

### Foreign Key Handling

When persons are deleted, company contacts will be set to NULL rather than preventing deletion:

```sql
FOREIGN KEY (main_contact_id) REFERENCES persons(id) ON DELETE SET NULL
FOREIGN KEY (financial_contact_id) REFERENCES persons(id) ON DELETE SET NULL
```

### Migration Safety

- All new columns are nullable to avoid breaking existing data
- Existing `name` field remains primary for backward compatibility
- Migration script includes error handling for already-applied changes

## Testing Strategy

### Unit Tests

1. **Model validation tests**: Test new field validation logic
2. **Service layer tests**: Test CRUD operations with new fields
3. **Migration tests**: Test database schema changes

### Integration Tests

1. **Form submission tests**: Test person creation with new fields
2. **Company management tests**: Test full CRUD cycle for companies
3. **Foreign key tests**: Test contact relationship handling

### UI Tests

1. **Name suggestion tests**: Test "{lastName}, {firstName}" suggestion logic
2. **Form validation tests**: Test client-side validation
3. **Company selection tests**: Test person dropdown functionality

### Test Data

```python
# Test person with new fields
test_person = Person(
    name="Rossi, Mario",
    first_name="Mario",
    last_name="Rossi",
    registration_no="EMP001",
    email="mario.rossi@company.it",
    profile_image="mario_rossi.jpg"
)

# Test company with contacts
test_company = Company(
    name="Acme Corporation",
    short_name="ACME",
    registration_no="12345678901",
    address="Via Roma 1, Milano",
    website="https://www.acme.com",
    main_contact_id=1,
    financial_contact_id=2
)
```

This design ensures backward compatibility while providing enhanced functionality for name management and company relationships, following the existing architectural patterns and maintaining data integrity.
