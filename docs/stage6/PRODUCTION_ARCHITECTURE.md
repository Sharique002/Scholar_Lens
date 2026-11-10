# Scholar Lens — Stage 6 Production Architecture Design
**Document ID:** `DOC-S6-ARCH-01`  
**Execution Date:** 2026-11-07  
**Auditor / Lead:** Principal Software Architect & Infrastructure Engineer  
**Classification:** Institutional Architecture Specification  

---

## 1. Executive Summary

This document specifies the institutional production architecture for Scholar Lens. The design emphasizes **operational simplicity, defense-in-depth security, cost efficiency, and high maintainability** tailored to university IT infrastructure without introducing unneeded microservices or distributed message brokers.

---

## 2. Institutional Architecture Diagram

```
                                  PUBLIC INTERNET
                                         │
                                         ▼
                     ┌───────────────────────────────────────┐
                     │    Edge Network & TLS Termination     │
                     │  (Nginx Reverse Proxy / Cloudflare)   │
                     │    HTTPS :443 (Let's Encrypt / CA)    │
                     └───────────────────┬───────────────────┘
                                         │
                                         │ HTTP :8000 (Internal Private Network)
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           APPLICATION SERVER TIER                               │
│                                                                                 │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │                         Gunicorn WSGI Master                            │   │
│   │            (3-4 Pre-fork Worker Processes, Timeout: 120s)               │   │
│   │                                                                         │   │
│   │   ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────────────┐   │   │
│   │   │ Worker 1 (Core) │ │ Worker 2 (Core) │ │ Worker 3 (Core)         │   │   │
│   │   │ WhiteNoise Cache│ │ WhiteNoise Cache│ │ WhiteNoise Cache        │   │   │
│   │   │ REST API Engine │ │ REST API Engine │ │ REST API Engine         │   │   │
│   │   └────────┬────────┘ └────────┬────────┘ └────────┬────────────────┘   │   │
│   └────────────┼───────────────────┼───────────────────┼────────────────────┘   │
│                │                   │                   │                        │
│                └───────────────────┼───────────────────┘                        │
│                                    │                                            │
│                                    ▼                                            │
│                      [ Persistent Storage Volume ]                              │
│                         /app/media (Uploaded PDFs)                              │
└────────────────────────────────────┼────────────────────────────────────────────┘
                                     │
                                     │ Encrypted TCP :5432 (Internal Private Subnet)
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            DATA PERSISTENCE TIER                                │
│                                                                                 │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │                       PostgreSQL 16 Engine                              │   │
│   │                                                                         │   │
│   │   - Database: scholar_lens                                              │   │
│   │   - Extension: pg_trgm (Full-text GIN trigram indexing)                 │   │
│   │   - Extension: btree_gist (Booking exclusion constraint locks)          │   │
│   │   - 47 Applied Migrations across 15 Applications                        │   │
│   │   - Connection Pool: 20 max connections, SSL mode: verify-full          │   │
│   │   - Automated WAL Archiving & Nightly Snapshot Backups                  │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼ Outbound HTTPS :443
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         EXTERNAL INSTITUTIONAL SERVICES                         │
│                                                                                 │
│   - Google OAuth 2.0 Identity Server (OIDC SSO Authentication)                  │
│   - Elsevier Scopus & Crossref APIs (Publication Harvesters)                    │
│   - Institutional SMTP Server (Notification & Alert Relays)                     │
│   - OpenAI API (Optional Semantic Embeddings & RAG QA Assistant)                │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Tier-by-Tier Component Responsibilities

### 3.1 Edge Tier & Reverse Proxy
- **Component:** Nginx 1.24+ or Institutional Hardware Load Balancer.
- **Port Binding:** Public port 443 (HTTPS) and port 80 (301 redirect to HTTPS).
- **Responsibilities:**
  - TLS 1.3 termination with strong cipher suites (`ECDHE-ECDSA-AES128-GCM-SHA256:...`).
  - HSTS enforcement (`Strict-Transport-Security: max-age=31536000; includeSubDomains; preload`).
  - Request buffering, rate limiting, and DDoS mitigation.
  - Forwarding client IP and protocol via `X-Forwarded-For` and `X-Forwarded-Proto`.

### 3.2 Application Server Tier
- **Component:** Gunicorn WSGI running in Docker container or systemd service as non-root user `appuser`.
- **Worker Model:** Sync workers (`workers = 2 * CPU_CORES + 1`, typically 3–4 workers).
- **Responsibilities:**
  - Django application runtime execution.
  - Static asset serving via WhiteNoise (`CompressedStaticFilesStorage`), removing the need for a separate static file Nginx mount.
  - Local disk persistence for uploaded PDFs in `/app/media`.

### 3.3 Data Persistence Tier
- **Component:** PostgreSQL 16 Cluster in private, non-routable subnet.
- **Responsibilities:**
  - Relational integrity across all 15 applications.
  - Full-text search queries via GIN index on pre-computed `search_document`.
  - Transaction-level concurrency locks preventing double-bookings via `btree_gist` ExclusionConstraint.
  - Nightly encrypted database snapshots and WAL transaction logs.

---

## 4. Multi-Environment Topology Separation

To guarantee stability, four strictly isolated environments are defined:

| Dimension / Characteristic | 1. Local Development | 2. Automated Testing | 3. Staging Environment | 4. Production Environment |
|---|---|---|---|---|
| **Purpose** | Feature engineering & bugfixes | CI/CD regression gates | Final institutional UAT | Live university operation |
| **Database** | PostgreSQL / SQLite | PostgreSQL (`test_scholar_lens`) | PostgreSQL (`scholar_lens_staging`) | PostgreSQL (`scholar_lens`) |
| **`DEBUG`** | `True` | `True` | `False` | `False` |
| **Hostname / URL** | `localhost:8000` | Ephemeral `127.0.0.1:8001` | `staging.scholar-lens.lpu.in` | `scholar-lens.lpu.in` |
| **Secret Management** | Local `.env` file | In-memory environment vars | Cloud Secret Manager | Pinned Vault / Encrypted Env |
| **Security Headers** | Disabled (local HTTP) | Disabled | Fully Enforced | Fully Enforced |
| **OAuth Redirect** | `http://localhost:8000/...` | Mocked test harness | `https://staging.../callback/` | `https://scholar-lens.../callback/` |
| **External Harvesters** | Mock responses | Mock fixture responses | Polite pool / Staging keys | Live institutional keys |

---

## 5. Phase 1 Conclusion

The production architecture provides a clear, defensible, modular structure suited to institutional deployment without unnecessary external overhead.
