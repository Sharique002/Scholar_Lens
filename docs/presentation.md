# Presentation — Scholar Lens

## Problem Statement

Researchers face significant challenges in:
1. **Assessing research novelty** — Difficulty determining if their research idea is truly novel
2. **Identifying research gaps** — Hard to systematically find unexplored areas
3. **Evaluating research quality** — Lack of objective, multi-dimensional assessment tools
4. **Finding collaborators** — Difficulty connecting with researchers who have complementary expertise
5. **Understanding papers quickly** — Time-consuming process to extract key insights from papers

## Motivation

- Growing volume of published research makes manual assessment impractical
- Researchers need AI-assisted tools to accelerate literature review
- Collaboration across disciplines is increasingly important
- No single platform combines AI analysis, evaluation, and collaboration

## Proposed Solution

**Scholar Lens** — An AI-powered research intelligence platform that:
- Automatically summarizes research papers
- Detects potential research gaps
- Provides multi-dimensional research evaluation
- Enables natural language paper querying (RAG)
- Connects researchers based on complementary expertise
- Supports semantic search across uploaded papers

## Architecture Highlights

### Django-First Design
- 9 modular Django apps with clear responsibilities
- Function-based views with proper decorators
- Django Template Language for all frontend rendering
- Django ORM for database operations
- Django Admin for management
- Django Forms with server-side validation

### AI Integration
- Clean service abstraction layer
- OpenAI GPT-4o-mini for text analysis
- text-embedding-3-small for semantic representations
- RAG (Retrieval-Augmented Generation) for paper Q&A
- Cosine similarity for semantic search and matching

### Database Design
- 15+ normalized models
- Proper relationships (FK, OneToOne, M2M)
- Database indexes for performance
- Constraint-based data integrity

## Key Features Demo

### 1. Paper Management
- Upload PDF → Extract text → Index → Ready for AI analysis
- Complete CRUD with ownership permissions

### 2. AI Paper Summary
- Structured extraction: problem, methodology, findings, limitations
- Cached results for efficiency

### 3. Research Gap Detection
- Identifies underexplored areas with severity levels
- Provides actionable suggestions

### 4. Ask Your Paper (RAG)
- Natural language questions about uploaded papers
- Grounded answers based on paper content
- Source chunk references

### 5. Research Evaluation Engine (Signature Feature)
- 6-dimension scoring: Novelty, Gap, Methodology, Contribution, Evidence, Clarity
- Weighted overall score with visual breakdown
- Strengths, weaknesses, concerns, recommendations
- Clear disclaimers — AI-assisted, not authoritative

### 6. Semantic Search
- Natural language queries
- Embedding-based similarity ranking
- Hybrid keyword + semantic results

### 7. Researcher Collaboration
- Profile-based matching
- Interest and skill overlap scoring
- Collaboration request system

## Django Concepts Demonstrated

| Concept | Implementation |
|---------|---------------|
| Project setup | manage.py, settings.py, 9 apps |
| Views & URLs | 30+ views, named URLs, namespaces |
| Templates & DTL | extends, block, for, if, filters, tags |
| Forms & CSRF | ModelForms, validation, csrf_token |
| Models & ORM | 15+ models, FK, M2M, select_related |
| Admin | Custom admin registration for all models |
| Auth | Register, login, logout, permissions |
| Sessions | Session-based auth, configurable settings |

## Security Measures

- CSRF protection on all forms
- Password hashing (PBKDF2)
- Server-side validation
- File type/size validation
- Owner-only operations
- Environment variables for secrets
- Production security headers

## Testing

- Automated test suite with `python manage.py test`
- Tests cover auth, models, forms, views, search, AI handling
- System checks pass (`python manage.py check`)

## Future Scope

1. Real-time collaboration (WebSockets)
2. Celery for background processing
3. Citation network visualization
4. REST API (Django REST Framework)
5. Multi-language support
6. Advanced plagiarism detection
7. Institutional SSO
8. PDF report export
9. Email notifications

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11, Django 4.2 |
| Database | SQLite / PostgreSQL |
| AI | OpenAI API |
| PDF | PyMuPDF |
| Search | NumPy cosine similarity |
| Frontend | HTML5, CSS3, JavaScript, Chart.js |
| Deployment | Docker, Docker Compose |
