# Scholar Lens

## AI-Powered Research Intelligence, Novelty Assessment & Collaboration Platform

**Scholar Lens** is an AI-powered research intelligence platform that helps researchers discover, understand, evaluate, and connect their research work. Built with Django as the core framework for the INT253: Web Development in Python Using Django course.

---

## Features

### Core Features
- **User Authentication** — Registration, login, logout, profile management with role-based permissions (Student, Faculty, Admin)
- **Research Paper Management** — Upload, organize, and manage research papers with PDF processing
- **Researcher Profiles** — Detailed profiles with expertise, interests, skills, and institutional affiliations
- **Research Projects** — Create and manage research projects with team collaboration
- **Collaboration System** — Send/receive collaboration requests with AI-powered researcher matching

### AI-Powered Features
- **AI Paper Summarization** — Generate structured summaries including research problem, methodology, findings, and limitations
- **Research Gap Detection** — Identify potential gaps, underexplored areas, and future research directions
- **Ask Your Paper (RAG)** — Ask questions about uploaded papers using Retrieval-Augmented Generation
- **Hybrid Search Engine** — Multi-factor search ranking combining semantic similarity (60%), lexical matching (25%), research area relevance (10%), and publication recency (5%), with faceting by area, year, author, and threshold
- **Research Evaluation Engine** — Canonical 7-dimension evaluation (Potential Novelty 20%, Research Gap 15%, Methodology 15%, Contribution 15%, Evidence Quality 15%, Technical Strength 10%, Clarity 10%) with structured evidence citation, confidence scoring, and limitation analysis
- **Researcher Recommendations** — AI-matched collaboration suggestions based on shared interests, complementary skills, and publication history

### Platform Features
- **Dashboard & Analytics** — Statistics, charts, and activity tracking
- **Admin Panel** — Full Django admin with management capabilities
- **Error Handling** — Custom error pages and graceful failure handling
- **Responsive Design** — Mobile-first, polished UI with dark/light theme support

---

## Architecture

```
Browser → Django Templates (HTML/CSS/JS)
    → Django URL Router → Django Views
    → Forms / Validation / Authentication
    → Service Layer (Business Logic)
    → Django ORM → SQLite/PostgreSQL
    → AI Orchestrator → OpenAI API
```

### Django Apps

| App | Responsibility |
|-----|---------------|
| `accounts` | Authentication, registration, profiles, permissions |
| `researchers` | Researcher profiles, expertise, interests, skills |
| `papers` | Paper CRUD, upload, metadata, PDF processing |
| `projects` | Research projects, members, status tracking |
| `collaboration` | Collaboration requests, researcher matching |
| `ai_engine` | AI services, summarization, QA, gap analysis |
| `evaluation` | Novelty assessment, methodology eval, scoring |
| `search` | Keyword search, semantic search, vector retrieval |
| `dashboard` | Statistics, analytics, activity feed |

---

## Technology Stack

- **Backend**: Python 3.11+, Django 4.2
- **Database**: SQLite (development) / PostgreSQL (production/Docker)
- **AI**: OpenAI API (GPT-4o-mini, text-embedding-3-small)
- **PDF Processing**: PyMuPDF (fitz)
- **Vector Search**: NumPy cosine similarity
- **Frontend**: HTML5, CSS3, JavaScript, Django Templates, Chart.js
- **Containerization**: Docker, Docker Compose

---

## Project Structure

```
scholar_lens/
├── manage.py
├── scholar_lens/          # Project configuration
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── accounts/              # Authentication & user profiles
├── researchers/           # Researcher profiles & expertise
├── papers/                # Paper management & upload
├── projects/              # Research projects
├── collaboration/         # Collaboration system
├── ai_engine/             # AI service layer
├── evaluation/            # Research evaluation engine
├── search/                # Search functionality
├── dashboard/             # Dashboard & analytics
├── templates/             # Django templates
├── static/                # CSS, JS, images
├── media/                 # Uploaded files
├── tests/                 # Test suite
├── docs/                  # Documentation
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Installation

### Prerequisites
- Python 3.11 or higher
- pip (Python package manager)
- Git

### 1. Clone the Repository
```bash
git clone <repository-url>
cd SCHOLAR_LENS
```

### 2. Create Virtual Environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Configuration
```bash
# Copy the example environment file
copy .env.example .env    # Windows
cp .env.example .env      # macOS/Linux

# Edit .env and configure your settings
# At minimum, generate a new SECRET_KEY for production
```

### 5. Database Setup
```bash
# Create database tables
python manage.py makemigrations
python manage.py migrate
```

### 6. Create Superuser
```bash
python manage.py createsuperuser
```

### 7. Load Demo Data (Optional)
```bash
python manage.py seed_demo_data
```

### 8. Run Development Server
```bash
python manage.py runserver
```

Visit: http://127.0.0.1:8000

---

## Docker Setup

### Quick Start with Docker
```bash
# Build and start all services
docker compose up --build

# In a new terminal, create superuser
docker compose exec web python manage.py createsuperuser

# Load demo data (optional)
docker compose exec web python manage.py seed_demo_data
```

Visit: http://localhost:8000

### Docker Commands
```bash
# Stop services
docker compose down

# View logs
docker compose logs -f web

# Run migrations
docker compose exec web python manage.py migrate

# Run tests
docker compose exec web python manage.py test
```

---

## AI Configuration

The platform uses OpenAI's API for AI features. To enable AI functionality:

1. Get an API key from [OpenAI Platform](https://platform.openai.com)
2. Add to your `.env` file:
```
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

### Without AI Configuration
The application works fully without an API key. AI features will display:
> "AI service not configured. Please set OPENAI_API_KEY in your environment."

Core Django features (authentication, paper management, projects, collaboration, search) work independently of AI configuration.

---

## Running Tests

```bash
# Run all tests
python manage.py test

# Run with verbosity
python manage.py test -v 2

# Run specific app tests
python manage.py test tests.test_accounts
python manage.py test tests.test_papers

# Run Django system checks
python manage.py check

# Verify migrations
python manage.py makemigrations --check
```

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Django secret key | Dev key (change in production) |
| `DEBUG` | Debug mode | `True` |
| `ALLOWED_HOSTS` | Allowed hostnames | `localhost,127.0.0.1` |
| `USE_POSTGRES` | Use PostgreSQL | `False` (SQLite) |
| `DB_NAME` | Database name | `scholar_lens` |
| `DB_USER` | Database user | `scholar_lens` |
| `DB_PASSWORD` | Database password | `scholar_lens` |
| `DB_HOST` | Database host | `localhost` |
| `DB_PORT` | Database port | `5432` |
| `OPENAI_API_KEY` | OpenAI API key | Empty |
| `OPENAI_MODEL` | Chat model | `gpt-4o-mini` |
| `OPENAI_EMBEDDING_MODEL` | Embedding model | `text-embedding-3-small` |
| `MAX_UPLOAD_SIZE_MB` | Max upload size | `20` |

---

## Screenshots

*Screenshots section — add screenshots after deployment*

| Page | Description |
|------|-------------|
| Landing Page | Professional landing with feature highlights |
| Dashboard | User dashboard with stats and activity |
| Paper Detail | Detailed paper view with AI analysis |
| Evaluation Report | Research evaluation with score breakdown |
| Semantic Search | Natural language paper search |
| Collaboration | Researcher matching and recommendations |

---

## Troubleshooting

### Common Issues

**ModuleNotFoundError: No module named 'xyz'**
```bash
pip install -r requirements.txt
```

**Database errors after model changes**
```bash
python manage.py makemigrations
python manage.py migrate
```

**Static files not loading**
```bash
python manage.py collectstatic
```

**AI features showing "not configured"**
- Ensure `OPENAI_API_KEY` is set in your `.env` file
- Restart the development server after changing `.env`

**File upload errors**
- Check `MAX_UPLOAD_SIZE_MB` in `.env`
- Ensure `media/` directory exists and is writable

---

## Future Enhancements

- [ ] Real-time collaboration with WebSockets
- [ ] Celery integration for background processing
- [ ] Citation network visualization
- [ ] Multi-language paper support
- [ ] API endpoints (Django REST Framework)
- [ ] Advanced plagiarism detection integration
- [ ] Institutional SSO authentication
- [ ] Export evaluation reports as PDF
- [ ] Email notifications
- [ ] Advanced analytics dashboard

---

## Course: INT253 — Web Development in Python Using Django

This project demonstrates all major Django concepts covered in the INT253 syllabus. See [docs/int253-mapping.md](docs/int253-mapping.md) for detailed mapping.

---

## License

This project is developed for academic purposes as part of the INT253 course.

---

*Built with Django — See deeper into research.*
