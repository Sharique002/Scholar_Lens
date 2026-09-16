# Testing — Scholar Lens

## Test Framework

Scholar Lens uses Django's built-in test framework (`django.test.TestCase`).

## Running Tests

```bash
# Run all tests
python manage.py test

# Run with verbosity
python manage.py test -v 2

# Run specific test modules
python manage.py test tests.test_accounts
python manage.py test tests.test_papers
python manage.py test tests.test_models
python manage.py test tests.test_views
python manage.py test tests.test_forms
python manage.py test tests.test_ai

# Run Django system checks
python manage.py check

# Verify migrations are up to date
python manage.py makemigrations --check
```

## Test Categories

### Authentication Tests
- User registration (valid/invalid data)
- Login (correct/incorrect credentials)
- Logout
- Protected view access (redirect when not authenticated)
- Profile access and editing

### Model Tests
- Model creation and field validation
- ForeignKey relationships
- ManyToMany relationships
- String representations
- Model constraints
- Default values

### Form Tests
- Form validation with valid/invalid data
- File upload validation (PDF type, size limits)
- CSRF protection
- Custom clean methods
- Required field enforcement

### View Tests
- HTTP status codes (200, 302, 403, 404)
- Template usage verification
- Context data verification
- Authentication requirements
- Ownership permissions
- GET and POST handling

### Search Tests
- Keyword search functionality
- Empty search handling
- Filter by research area
- Pagination

### AI Service Tests
- Service configuration detection
- Graceful handling when AI is not configured
- Cached result retrieval
- Error handling for API failures

## Test Fixtures

Tests create their own test data using Django's `TestCase`:
- `setUp()` creates test users, papers, and related objects
- Each test is isolated with database rollback
- No dependency on external services for core tests

## Coverage

To run with coverage:
```bash
pip install coverage
coverage run manage.py test
coverage report
coverage html  # Generate HTML report
```
