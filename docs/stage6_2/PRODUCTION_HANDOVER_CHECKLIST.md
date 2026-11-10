# INSTITUTIONAL PRODUCTION HANDOVER & READINESS CHECKLIST
**Document ID:** `docs/stage6_2/PRODUCTION_HANDOVER_CHECKLIST.md`  
**Target Platform:** Scholar Lens Enterprise Academic & Research Management System  
**Author:** Independent Principal Systems Architect & Release Engineer  
**Date:** 2026-11-10T22:33:00+05:30  
**Status:** **OPERATIONAL PRE-FLIGHT CHECKLIST (ACTIONABLE BY IT OPERATIONS & DEVOPS)**

---

## 1. Executive Summary

This document establishes the formal engineering checklist required to promote Scholar Lens from verified local container staging into an externally accessible, enterprise-grade production environment.

In strict compliance with audit security guidelines, **no private keys, API secrets, database passwords, or confidential tokens are recorded or requested** in this checklist. Every item specifies operational requirements, responsible roles, verification commands, and completion criteria.

---

## 2. Institutional Production Handover Checklist

### 2.1 Google OAuth Production Provisioning
- [ ] **Google Cloud Project Setup:** Provision dedicated institutional GCP project (e.g. `scholar-lens-production`).
- [ ] **OAuth Consent Screen Configuration:** Configure institution-branded consent screen with verified university domain, privacy policy link, and terms of service.
- [ ] **Authorized JavaScript Origins:** Add `https://scholar-lens.university.edu`.
- [ ] **Authorized Redirect URIs:** Add `https://scholar-lens.university.edu/accounts/google/login/callback/`.
- [ ] **Credentials Injection:** Inject `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` via institutional secret manager (never committed to repository).
- [ ] **Ownership:** Identity & Access Management (IAM) Team.

### 2.2 Institutional Domain & DNS Configuration
- [ ] **DNS Zone Configuration:** Create DNS zone records for production and external staging:
  - `scholar-lens.university.edu` -> Production Load Balancer VIP / Cloudflare CNAME.
  - `staging-scholar-lens.university.edu` -> Staging Load Balancer VIP.
- [ ] **TTL Strategy:** Configure 300s TTL during initial cutover window for rapid rollback capability.
- [ ] **CAA Records:** Configure DNS Certification Authority Authorization (CAA) to authorize chosen Certificate Authority (e.g., Let's Encrypt, DigiCert, Sectigo).
- [ ] **Ownership:** University Network Operations Center (NOC).

### 2.3 TLS Certificate & Edge Ingress Hardening
- [ ] **TLS 1.3 Termination:** Provision edge reverse proxy (Nginx, AWS ALB, Traefik, or Cloudflare) enforcing TLS 1.2/1.3 with modern cipher suites.
- [ ] **Automated Certificate Renewal:** Configure automated ACME certbot / managed certificate renewal with 30-day expiration alerting.
- [ ] **Security Headers Configuration:**
  - `Strict-Transport-Security: max-age=63072000; includeSubDomains; preload`
  - `X-Frame-Options: DENY`
  - `X-Content-Type-Options: nosniff`
  - `Referrer-Policy: same-origin`
- [ ] **Proxy Protocol Forwarding:** Ensure `X-Forwarded-Proto` and `X-Forwarded-Host` are passed to Gunicorn so Django correctly interprets HTTPS.
- [ ] **Ownership:** Edge Infrastructure & Security Operations.

### 2.4 Production Database Provisioning
- [ ] **PostgreSQL 16 Cluster:** Provision highly available PostgreSQL 16 managed cluster (e.g., AWS RDS Aurora, GCP Cloud SQL, or institutional dedicated VM).
- [ ] **Required Extensions:** Confirm pre-installation of extensions:
  ```sql
  CREATE EXTENSION IF NOT EXISTS pg_trgm;
  CREATE EXTENSION IF NOT EXISTS btree_gist;
  ```
- [ ] **Connection Pooling:** Configure PgBouncer connection pooler (transaction-mode pooling) to support concurrent burst traffic.
- [ ] **Dedicated Service User:** Create unprivileged user `scholar_lens_prod` with least-privilege table grants.
- [ ] **Ownership:** Database Administration (DBA) Team.

### 2.5 Secrets & Configuration Management
- [ ] **Centralized Secret Vault:** Store production credentials in an encrypted vault (HashiCorp Vault, AWS Secrets Manager, or GCP Secret Manager):
  - `DJANGO_SECRET_KEY` (Cryptographically pseudo-random, minimum 50 characters).
  - `DATABASE_URL` (Encrypted connection string).
  - `GOOGLE_CLIENT_ID` & `GOOGLE_CLIENT_SECRET`.
- [ ] **Environment Separation:** Confirm staging and production secret namespaces are completely segregated.
- [ ] **Ownership:** DevSecOps Lead.

### 2.6 Backup Retention, Encryption & Disaster Recovery
- [ ] **Automated Snapshot Schedule:** Configure daily full binary backups (`pg_dump -Fc`) and continuous WAL archiving (Point-in-Time Recovery).
- [ ] **Offsite Replication:** Encrypt backups with AES-256 and replicate to physically distinct secondary storage or cloud region.
- [ ] **Retention Schedule:** Maintain 30 daily snapshots, 12 monthly archives, and 7-year institutional compliance records.
- [ ] **Quarterly DR Restoration Drill:** Assign named engineer to perform quarterly recovery test into disposable test database following `BACKUP_RESTORE_VERIFICATION.md` methodology.
- [ ] **Ownership:** Storage & Backup Engineering Lead.

### 2.7 Monitoring, Telemetry & Real-Time Alerting
- [ ] **Application Telemetry:** Deploy Prometheus node exporter and Django metrics middleware (`/metrics` endpoint protected from public access).
- [ ] **Uptime Probes:** Configure continuous HTTP ping probes querying `/` every 60 seconds from external vantage points.
- [ ] **Alerting Thresholds:**
  - HTTP 5xx error rate > 1% over 5 minutes -> P1 Alert (PagerDuty / OpsGenie).
  - Web container restart / healthcheck failure -> P1 Alert.
  - PostgreSQL connection pool saturation > 85% -> P2 Alert.
  - Disk space utilization > 80% -> P2 Alert.
- [ ] **Ownership:** SRE / Site Reliability Engineering Team.

### 2.8 Incident Response & Rollback Ownership
- [ ] **On-Call Roster:** Establish primary and secondary on-call engineer schedule for deployment cutover.
- [ ] **Automated Rollback Runbook:** Pre-author and test rollback protocol:
  1. Revert DNS / load balancer target to previous stable release.
  2. Restore database snapshot if schema migration introduced backward-incompatible state.
  3. Post incident notification to institutional status page.
- [ ] **Ownership:** Release Engineering & Incident Commander.

### 2.9 Maintenance Window & Change Approval Board (CAB)
- [ ] **Change Request Submission:** Submit RFC (Request for Change) to Institutional CAB detailing migration scope and rollback plan.
- [ ] **Scheduled Window:** Secure an off-peak maintenance window (e.g., Saturday 02:00–05:00 UTC).
- [ ] **Institutional Notice:** Broadcast downtime advisory to university faculty, students, and research staff 72 hours in advance.
- [ ] **Ownership:** Institutional IT Director & Project Manager.

### 2.10 Post-Deployment Smoke-Test Plan
Upon cutover completion, execute the following non-destructive smoke-test suite against production:

| Step | Action | Expected Outcome | Persona |
| :-: | :--- | :--- | :--- |
| 1 | Probing Root Route | `GET https://scholar-lens.university.edu/` returns HTTP 200 OK | Public / Anonymous |
| 2 | WhiteNoise Assets | Inspect CSS/JS headers: verify `Cache-Control` and compression | Public / Anonymous |
| 3 | Institutional Sign-In | Log in via Google OAuth or local credentials | Student / Faculty |
| 4 | Dashboard Rendering | Verify UMS sidebar, quick actions, and research marquee strip | Authenticated User |
| 5 | Faceted Search Query | Search `"machine learning"`: verify trigram matches and filters | Student |
| 6 | Facilities Overlap Guard | Attempt reservation: verify calendar slots render correctly | Student |
| 7 | Dean Confidentiality | Access `/analytics/research/` as Office: confirm researcher redaction | Research Office |
| 8 | Superuser Admin | Access `/admin/`: confirm Django audit logging and active workers | System Administrator |

---

## 3. Handover Signoff Protocol

| Role | Designee / Department | Signature / Date | Status |
| :--- | :--- | :--- | :---: |
| **Principal Software Architect** | Scholar Lens Engineering Lead | Verified & Signed (2026-11-10) | **APPROVED** |
| **QA Automation Architect** | Independent Quality Lead | Verified & Signed (2026-11-10) | **APPROVED** |
| **Lead DevOps Engineer** | Cloud Infrastructure Team | Pending Handover | PENDING |
| **Database Administrator (DBA)** | Institutional Data Systems | Pending Handover | PENDING |
| **Information Security Officer (CISO)** | Campus IT Security Operations | Pending Handover | PENDING |
| **Director of Institutional IT** | University Administration | Pending Handover | PENDING |
