# Scholar Lens — Stage 6 Deployment Baseline Assessment
**Document ID:** `DOC-S6-BASE-01`  
**Execution Date:** 2026-11-07  
**Auditor / Lead:** Principal Software Architect & DevOps Lead  
**Classification:** Institutional Deployment Baseline  

---

## 1. Executive Summary

Before introducing or altering any institutional deployment configurations, an exhaustive baseline assessment of the Scholar Lens repository was conducted. The objective is to map all technical requirements, package runtimes, static asset architectures, database dependencies, background jobs, external integrations, and existing container definitions without unnecessary infrastructural bloat.

---

## 2. Technical Stack & Runtime Baseline

| Component / Layer | Inspected Runtime & Version | Architectural Role | Production Standard |
|---|---|---|---|
| **Programming Language** | Python 3.11.9 (64-bit AMD64) | Core backend runtime | Pinned to Python 3.11.x LTS |
| **Web Framework** | Django 5.2.17 | Backend web application & ORM | Active Django release |
| **Primary Database** | PostgreSQL 16.3 (Port 5433) | Relational store with ACID guarantees | PostgreSQL 15+ with extensions |
| **Database Extensions** | `pg_trgm`, `btree_gist` | Substring trigram GIN indexes & GiST range exclusion | Mandatory in PostgreSQL cluster |
| **Database Drivers** | `psycopg2-binary 2.9.13`, `dj-database-url 3.1.2` | PostgreSQL adapter & URL connection string parser | Installed & tested |
| **WSGI Server** | Gunicorn 26.2.0 | Multi-worker Python WSGI HTTP server | Production HTTP application server |
| **Static File Engine** | WhiteNoise 6.12.0 (`CompressedStaticFilesStorage`) | Self-contained static file compression & caching | Zero external CDN dependency required |
| **Frontend Runtime** | Pure Vanilla JavaScript ES6+ & CSS Custom Properties | Lightweight browser execution | No Node.js build step needed in production |
| **Test Runners** | Django DiscoverRunner + Cypress 13.15.0 (Node 24.14.0) | Automated dual-layer regression testing | CI/CD Quality Gate only |

---

## 3. Storage, Static & Media Asset Architecture

### 3.1 Static Assets
- **Source Directory:** `static/` (CSS design tokens, JavaScript client modules, images).
- **Compilation Target:** `staticfiles/` populated via `python manage.py collectstatic --noinput`.
- **Delivery Strategy:** Managed via `WhiteNoiseMiddleware` directly within Gunicorn.
- **Cache Invalidation:** Hash-based asset fingerprinting (`CompressedStaticFilesStorage`), enabling immutable HTTP cache headers (`Cache-Control: max-age=31536000, public`).

### 3.2 User-Uploaded Media Assets
- **URL Path:** `MEDIA_URL = '/media/'`.
- **Storage Target:** `MEDIA_ROOT = BASE_DIR / 'media'` (or persistent volume mount in containerized deployments).
- **Asset Classes:** Uploaded research paper PDFs, research proposal documents, user profile avatars.
- **Security Control:** File upload limit enforced (`MAX_UPLOAD_SIZE_MB = 20`); MIME type and content inspection enforced before writing to disk.

---

## 4. Background Jobs & Scheduled Automation

Scholar Lens does not require heavy message brokers (such as Celery, RabbitMQ, or Redis) for core operations. Background tasks are encapsulated in standard Django management commands designed to be triggered via simple cron jobs, Kubernetes CronJobs, or institutional systemd timers:

| Task / Job Name | Management Command | Recommended Frequency | Purpose |
|---|---|---|---|
| **Search Document Reindex** | `python manage.py refresh_search_index` | Hourly / Nightly | Recomputes weighted tsvector search documents across profiles |
| **Funding Deadline Alerts** | `python manage.py send_funding_alerts` | Daily at 06:00 | Scans for funding calls closing in 30, 14, 7, or 1 days; emits alerts |
| **Collaboration Suggestions** | `python manage.py compute_suggestions` | Daily at 02:00 | Runs Jaccard overlap algorithm across researcher skills and coauthors |
| **External Paper Harvesting** | `python manage.py harvest_papers` | Weekly | Ingests Crossref and Scopus publications for verified researcher ORCIDs |

---

## 5. Existing Infrastructure Artifacts Audit

An inspection of existing repository deployment files revealed:
1. `Dockerfile`:
   - Base image: `python:3.11-slim`.
   - Copies code, installs dependencies from `requirements.txt`.
   - Runs `collectstatic`.
   - Entrypoint runs `migrate` and starts Gunicorn on `0.0.0.0:${PORT:-8000}`.
   - *Observation:* Currently runs as `root`. For institutional security, it should be updated to execute as a dedicated non-root user (`appuser`).
2. `docker-compose.yml`:
   - Configures PostgreSQL 15 (`db`) and Scholar Lens (`web`).
   - Uses volume mounts for persistence.
   - *Observation:* Functional for local staging and evaluation.
3. `Procfile`:
   - Defines `web: gunicorn scholar_lens.wsgi:application` and `release: python manage.py migrate`.
4. `render.yaml` & `vercel.json`:
   - Existing cloud deployment configurations for managed PaaS targets.

---

## 6. Deployment Dependency Map

```
┌────────────────────────────────────────────────────────────────────────┐
│                    SCHOLAR LENS DEPLOYMENT TOPOLOGY                    │
└────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                     [ HTTPS / TLS Termination Proxy ]
                           (Nginx / Cloudflare)
                                    │
                  ┌─────────────────┴─────────────────┐
                  ▼                                   ▼
          [ Static Assets ]                 [ Dynamic Requests ]
     WhiteNoise Compressed Cache             Port 8000 (HTTP/1.1)
                                                      │
                                                      ▼
                                            [ Gunicorn WSGI ]
                                           (3-4 Python Workers)
                                                      │
                                                      ▼
                                            [ Django Application ]
                                        (Scholar Lens Core Engine)
                                                      │
                       ┌──────────────────────────────┼──────────────────────────────┐
                       ▼                              ▼                              ▼
             [ PostgreSQL 16 DB ]           [ Persistent Volume ]          [ External Cloud APIs ]
             - pg_trgm (GIN Search)          - /app/media (PDFs)           - Google OAuth 2.0 (SSO)
             - btree_gist (Exclusion)                                      - Crossref / Scopus
             - 47 Migrations Applied                                       - OpenAI (Optional RAG)
```

---

## 7. Phase 0 Conclusion

The baseline application is self-contained, clean, and requires no auxiliary message queues. It is ready for production architecture formalization in Phase 1.
