# INT253 Syllabus Mapping — Scholar Lens

This document maps each INT253 syllabus unit and practical to its implementation in Scholar Lens.

---

## Unit Mapping

### UNIT I — Python + Django Project Setup

| Concept | Implementation |
|---------|---------------|
| Django project structure | `scholar_lens/` project with `settings.py`, `urls.py`, `wsgi.py`, `asgi.py` |
| django-admin | Project created using Django project conventions |
| manage.py | [manage.py](file:///d:/files/OneDrive/Desktop/SCHOLAR_LENS/manage.py) — entry point for all management commands |
| App creation | 9 modular apps: `accounts`, `researchers`, `papers`, `projects`, `collaboration`, `ai_engine`, `evaluation`, `search`, `dashboard` |
| Settings configuration | [settings.py](file:///d:/files/OneDrive/Desktop/SCHOLAR_LENS/scholar_lens/settings.py) — database, auth, static, media, AI config |

### UNIT II — Views and URLs

| Concept | Implementation |
|---------|---------------|
| Views (function-based) | All apps use function-based views: `paper_list`, `dashboard_view`, `register_view`, etc. |
| URL routing | [urls.py](file:///d:/files/OneDrive/Desktop/SCHOLAR_LENS/scholar_lens/urls.py) — root URL config with `include()` for each app |
| URL parameters | `<int:pk>/` in paper detail, `<int:receiver_id>/` in collaboration, `<int:paper_id>/` in AI engine |
| Named URLs | All URL patterns use `name=` parameter: `name='detail'`, `name='upload'`, etc. |
| URL namespaces | Each app has `app_name`: `accounts`, `papers`, `projects`, `collaboration`, `ai_engine`, `evaluation`, `search`, `dashboard` |
| HTTP GET/POST | All forms handle both GET (display) and POST (submit): paper upload, registration, login |
| Request/Response | Views use `HttpRequest`, return `HttpResponse`, `redirect()`, `JsonResponse` |
| Error handling | Custom 404, 403, 500 error handlers in `dashboard/views.py` |

### UNIT III — Templates and DTL

| Concept | Implementation |
|---------|---------------|
| Django Templates | All pages use `.html` templates in `templates/` directory |
| Template inheritance | `{% extends 'base.html' %}` used in ALL templates |
| `{% block %}` | `{% block title %}`, `{% block content %}`, `{% block extra_js %}` in every template |
| Variables | `{{ paper.title }}`, `{{ user.username }}`, `{{ form.errors }}` throughout |
| `{% for %}` loops | Paper lists, author lists, research gaps, activity feeds, search results |
| `{% if/else %}` | Authentication checks `{% if user.is_authenticated %}`, permission checks, empty states |
| Template filters | `{{ text\|truncatewords:30 }}`, `{{ date\|date:"M d, Y" }}`, custom filters |
| Template tags | `{% url %}`, `{% csrf_token %}`, `{% load static %}`, custom tags in `scholar_tags.py` |
| `{% include %}` | Reusable template fragments for cards, navigation, pagination |
| `{% load static %}` | Static file references in all templates |

### UNIT IV — Forms and CSRF

| Concept | Implementation |
|---------|---------------|
| Django Forms | `RegistrationForm`, `LoginForm`, `SearchForm` |
| ModelForms | `PaperUploadForm`, `ProjectForm`, `ResearcherProfileForm`, `CollaborationRequestForm` |
| GET/POST forms | All forms support GET (display) and POST (submission) |
| CSRF protection | `{% csrf_token %}` in every form template |
| Data validation | Server-side validation: file type/size checks, email validation, password strength |
| `clean_` methods | `clean_pdf_file()` validates PDF uploads, `clean_email()` checks uniqueness |
| Form errors | `{{ form.field.errors }}`, `{{ form.non_field_errors }}` displayed in templates |
| Formsets | `PaperAuthorFormSet` — inline formset for managing paper authors |
| Widgets | Custom widget attrs with CSS classes on all form fields |

### UNIT V — Models, Migrations, ORM, Admin

| Concept | Implementation |
|---------|---------------|
| Models | 15+ models: `UserProfile`, `ResearchPaper`, `ResearcherProfile`, `ResearchProject`, `EvaluationReport`, etc. |
| Field types | `CharField`, `TextField`, `IntegerField`, `FloatField`, `BooleanField`, `DateField`, `DateTimeField`, `FileField`, `ImageField`, `URLField`, `JSONField` |
| ForeignKey | `ResearchPaper.uploader → User`, `PaperAuthor.paper → ResearchPaper`, `ProjectMember.project → ResearchProject` |
| OneToOneField | `UserProfile.user → User`, `ResearcherProfile.user → User`, `PaperEmbedding.chunk → PaperChunk` |
| ManyToManyField | `ResearcherProfile.interests → ResearchInterest`, `ResearcherProfile.skills → Skill` |
| Migrations | Auto-generated via `makemigrations`, applied via `migrate` |
| Django ORM | `filter()`, `exclude()`, `annotate()`, `select_related()`, `prefetch_related()`, `order_by()` |
| QuerySets | Chained queries for search, filtering, pagination throughout views |
| Meta class | `ordering`, `unique_together`, `indexes`, `verbose_name` on all models |
| Django Admin | All models registered with `list_display`, `list_filter`, `search_fields`, `ordering` |
| Admin inlines | `PaperAuthorInline` for managing authors within paper admin |

### UNIT VI — Cookies, Sessions, Users, Authentication

| Concept | Implementation |
|---------|---------------|
| Django auth | Built-in `django.contrib.auth` with `User` model |
| Registration | Custom `register_view` with `RegistrationForm` creating User + UserProfile |
| Login | `login_view` using `AuthenticationForm`, `django.contrib.auth.login()` |
| Logout | `logout_view` using `django.contrib.auth.logout()` |
| Sessions | `SESSION_COOKIE_AGE`, `SESSION_COOKIE_HTTPONLY`, `SESSION_EXPIRE_AT_BROWSER_CLOSE` in settings |
| `@login_required` | All protected views use `@login_required` decorator |
| Password hashing | Django's built-in password hashing (PBKDF2) |
| Password validation | 4 validators configured: similarity, minimum length, common, numeric |
| Roles/Permissions | Role choices (STUDENT, FACULTY, ADMIN) on UserProfile, ownership checks in views |
| User groups | Django's built-in Group model available through admin |
| Protected views | Paper upload, dashboard, AI features — all require authentication |
| Ownership checks | Paper edit/delete restricted to owner, project edit restricted to leader |

---

## Practical Mapping

| Practical | Implementation |
|-----------|---------------|
| Project setup | Django project with `manage.py`, `settings.py`, 9 apps |
| App creation | `accounts`, `researchers`, `papers`, `projects`, `collaboration`, `ai_engine`, `evaluation`, `search`, `dashboard` |
| Views | 30+ views across all apps handling GET/POST requests |
| URL mapping | Root `urls.py` + 9 app-level `urls.py` files with named patterns |
| Templates | 25+ templates with inheritance, DTL tags, filters, includes |
| Debugging | Django debug mode, logging configuration, error handling |
| Testing | Comprehensive test suite with `python manage.py test` |
| Forms | 10+ forms with validation, CSRF, widgets, error display |
| Validation | Server-side validation on all forms, file validation, permission checks |
| CSRF | `{% csrf_token %}` in all POST forms, `CsrfViewMiddleware` enabled |
| Models | 15+ models with relationships, constraints, indexes |
| Migrations | Auto-generated migrations for all apps |
| ORM queries | Complex queries with `select_related`, `prefetch_related`, `annotate`, filtering |
| Admin | All models registered with admin customization |
| Sessions | Session-based authentication, configurable session settings |
| Authentication | Complete auth flow: register → login → protected views → logout |
| Permissions | Role-based access, ownership verification, `@login_required` |

---

## Beyond Syllabus (Advanced Features)

| Feature | Technology |
|---------|-----------|
| AI Integration | OpenAI API with service abstraction layer |
| PDF Processing | PyMuPDF for text extraction |
| Semantic Search | Vector embeddings with cosine similarity |
| RAG | Retrieval-Augmented Generation for paper Q&A |
| Research Evaluation | Multi-dimensional scoring engine |
| Docker | Containerized deployment with Docker Compose |
| Responsive Design | Custom CSS with mobile-first approach |
| Charts | Chart.js for dashboard analytics |

---

*Every major INT253 syllabus requirement has a visible, working implementation in Scholar Lens.*
