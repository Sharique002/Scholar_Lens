# Architecture — Scholar Lens

## System Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Browser (Client)                  │
│          HTML5 / CSS3 / JavaScript / Chart.js         │
└───────────────────────┬─────────────────────────────┘
                        │ HTTP
┌───────────────────────▼─────────────────────────────┐
│                 Django Web Server                     │
│                                                       │
│  ┌─────────────────────────────────────────────────┐ │
│  │              URL Router (urls.py)                │ │
│  │  /accounts/ /papers/ /projects/ /ai/ /search/   │ │
│  └──────────────────┬──────────────────────────────┘ │
│                     │                                 │
│  ┌──────────────────▼──────────────────────────────┐ │
│  │              Views Layer                         │ │
│  │  Function-based views with decorators            │ │
│  │  @login_required, error handling, pagination     │ │
│  └──────────────────┬──────────────────────────────┘ │
│                     │                                 │
│  ┌──────────────────▼──────────────────────────────┐ │
│  │         Forms / Validation Layer                 │ │
│  │  Django Forms, ModelForms, CSRF, clean methods   │ │
│  └──────────────────┬──────────────────────────────┘ │
│                     │                                 │
│  ┌──────────────────▼──────────────────────────────┐ │
│  │           Service Layer                          │ │
│  │  AIService, PaperProcessor, PaperSummarizer      │ │
│  │  ResearchGapDetector, ResearchEvaluator           │ │
│  │  SemanticSearchService, SimilarityAnalyzer        │ │
│  └──────┬───────────────────────────┬──────────────┘ │
│         │                           │                 │
│  ┌──────▼──────┐           ┌────────▼─────────────┐ │
│  │  Django ORM │           │   AI Orchestrator     │ │
│  │  Models     │           │   OpenAI API Client   │ │
│  │  QuerySets  │           │   Embedding Service   │ │
│  └──────┬──────┘           └────────┬─────────────┘ │
│         │                           │                 │
└─────────┼───────────────────────────┼─────────────────┘
          │                           │
┌─────────▼──────────┐     ┌─────────▼──────────┐
│  SQLite/PostgreSQL  │     │   OpenAI API       │
│  Database           │     │   GPT-4o-mini      │
│                     │     │   Embeddings       │
└────────────────────┘     └────────────────────┘
```

## Application Modules

### Core Modules
- **accounts** — User authentication, registration, profiles, role-based access
- **researchers** — Extended researcher profiles with expertise and skills
- **papers** — Research paper management and PDF processing
- **projects** — Research project lifecycle management
- **collaboration** — Collaboration requests and researcher matching

### AI Modules
- **ai_engine** — AI service abstraction, summarization, RAG, gap detection
- **evaluation** — Multi-dimensional research evaluation engine

### Support Modules
- **search** — Keyword and semantic search
- **dashboard** — Analytics, statistics, activity tracking

## Data Flow

### Paper Upload & Processing
```
User uploads PDF → Validate file → Store in media/
→ Extract text (PyMuPDF) → Clean text → Split into chunks
→ Generate embeddings (OpenAI) → Store in database
→ Update paper status (UPLOADED → TEXT_EXTRACTED → INDEXED)
```

### AI Analysis Flow
```
User requests analysis → Check for cached result
→ If cached: return stored analysis
→ If not: Build prompt → Call OpenAI API → Parse response
→ Store result in database → Return to user
```

### RAG Question Answering
```
User asks question → Generate question embedding
→ Find similar chunks (cosine similarity) → Build context
→ Call LLM with context + question → Return grounded answer
→ Store conversation in ChatMessage
```

### Research Evaluation
```
User triggers evaluation → Extract paper content
→ Evaluate across canonical 7 dimensions (Novelty 20%, Gap 15%, Methodology 15%, Contribution 15%, Evidence 15%, Technical Strength 10%, Clarity 10%)
→ Score each dimension with structured evidence, confidence, and limitations
→ Calculate weighted overall score (sum of weights = 100%) → Generate report with provenance (UUID, model version, prompt version)
→ Store EvaluationReport + ResearchScore objects
→ Update paper status to EVALUATED
```

## Security Architecture

- CSRF protection on all POST requests
- Session-based authentication with Django auth
- Password hashing (PBKDF2) with 4 validators
- Owner-only access for edit/delete operations
- File validation (type, size) on uploads
- Environment variables for secrets (never hardcoded)
- XSS prevention via Django template auto-escaping
- Production security headers (HSTS, XSS filter, etc.)
