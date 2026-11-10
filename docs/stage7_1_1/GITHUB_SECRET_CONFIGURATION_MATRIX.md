# Scholar Lens — Stage 7.1.1: GitHub Secret & Variable Configuration Matrix

**Document ID:** `SL-STAGE7-1-1-SECRET-MATRIX-001`  
**Date:** 2026-11-10  
**Phase:** Stage 7.1.1 — Post-Push Verification, CI/CD Validation and Zero-Cost Cloud Preflight  
**Scope:** GitHub Repository Secrets, Environment Variables, and Cloud Run Runtime Mappings  
**Author:** AI Systems Engineer & Configuration Specialist  

---

## 1. Executive Summary

This document provides the authoritative, single-source matrix of all secrets and environment variables required by GitHub Actions workflows (`.github/workflows/ci-cd.yml`) and Google Cloud Run runtime execution for Scholar Lens.

---

## 2. Authoritative Configuration Matrix

| # | Variable / Secret Name | GitHub Classification | Required / Optional | Cloud Runtime Mapping | Purpose & Canonical Format |
|---|---|---|---|---|---|
| 1 | **`GCP_PROJECT_ID`** | Variable / Secret | **REQUIRED** | `--project` flag in CLI | GCP Project ID (e.g., `scholar-lens-staging`). |
| 2 | **`GCP_WIF_PROVIDER`** *(alias: `GCP_WORKLOAD_IDENTITY_PROVIDER`)* | Repository Secret | **REQUIRED** | OIDC provider token exchange | Full provider resource name: `projects/NUM/locations/global/workloadIdentityPools/POOL/providers/PROVIDER`. |
| 3 | **`GCP_WIF_SERVICE_ACCOUNT`** *(alias: `GCP_SERVICE_ACCOUNT`)* | Repository Secret | **REQUIRED** | OIDC service account impersonation | Deployer service account email: `github-deployer@PROJECT_ID.iam.gserviceaccount.com`. |
| 4 | **`GCP_REGION`** | Variable / Secret | **REQUIRED** (Defaults to `us-central1`) | Cloud Run `--region` and Artifact Registry host | Target region (e.g., `us-central1` or `asia-south1`). |
| 5 | **`DATABASE_URL`** | Environment Secret | **REQUIRED** (for Staging DB) | Cloud Run `--set-env-vars` or Secret Manager | External PostgreSQL connection string: `postgresql://user:pass@host:port/dbname?sslmode=require`. |
| 6 | **`DJANGO_SECRET_KEY`** | Environment Secret | **REQUIRED** | Cloud Run `--set-env-vars` or Secret Manager | Cryptographic salt for sessions, CSRF, and tokens (minimum 50 random characters). |
| 7 | **`GOOGLE_CLIENT_ID`** | Environment Secret | Optional (OAuth login) | Cloud Run `--set-env-vars` | Google Identity OAuth 2.0 Web Client ID: `[GOOGLE_CLIENT_ID_PLACEHOLDER]`. |
| 8 | **`GOOGLE_CLIENT_SECRET`** | Environment Secret | Optional (OAuth login) | Cloud Run Secret Manager | Google Identity OAuth 2.0 Client Secret: `[GOOGLE_CLIENT_SECRET_PLACEHOLDER]`. |
| 9 | **`OPENAI_API_KEY`** | Environment Secret | Optional (AI Features) | Cloud Run Secret Manager | OpenAI API key for semantic embeddings and novelty analysis (`sk-...`). |
| 10 | **`SCOPUS_API_KEY`** | Environment Secret | Optional (Publication Sync) | Cloud Run Secret Manager | Elsevier Scopus API key for institutional paper synchronization. |
| 11 | **`DEBUG`** | Environment Variable | **REQUIRED** (Fixed `False`) | Cloud Run `--set-env-vars` | Enforces production security headers and disables debug tracebacks. |
| 12 | **`ALLOWED_HOSTS`** | Environment Variable | **REQUIRED** | Cloud Run `--set-env-vars` | Permitted hostnames (e.g., `*.run.app,scholar-lens-staging.university.edu`). |
| 13 | **`SITE_URL`** | Environment Variable | **REQUIRED** | Cloud Run `--set-env-vars` | Canonical base URL (e.g., `https://scholar-lens-staging-xyz.a.run.app`). |

---

## 3. Reconciliation of Key Variable Names

During the transition across documentation and workflow drafting, four key identifiers were reported:

### 1. `GCP_PROJECT_ID`
- **In Workflow:** Used in `ci-cd.yml` as `${{ secrets.GCP_PROJECT_ID }}`.
- **Reconciliation:** Direct 1:1 match. Can be placed either in Repository Secrets or Repository Variables.

### 2. `GCP_WORKLOAD_IDENTITY_PROVIDER` vs. `GCP_WIF_PROVIDER`
- **In Workflow:** Referenced as `${{ secrets.GCP_WIF_PROVIDER }}` in `ci-cd.yml:146`.
- **In Documentation:** Referenced as `GCP_WORKLOAD_IDENTITY_PROVIDER`.
- **Reconciliation:** To ensure backward compatibility, both secret names are supported. Recommended: Configure `GCP_WIF_PROVIDER` in GitHub Secrets (or configure both pointing to the same value).

### 3. `GCP_SERVICE_ACCOUNT` vs. `GCP_WIF_SERVICE_ACCOUNT`
- **In Workflow:** Referenced as `${{ secrets.GCP_WIF_SERVICE_ACCOUNT }}` in `ci-cd.yml:147`.
- **In Documentation:** Referenced as `GCP_SERVICE_ACCOUNT`.
- **Reconciliation:** Configure `GCP_WIF_SERVICE_ACCOUNT` in GitHub Secrets (or configure both pointing to `github-deployer@PROJECT_ID.iam.gserviceaccount.com`).

### 4. `DATABASE_URL`
- **In Workflow:** Referenced as `${{ secrets.DATABASE_URL }}` for external staging deployments.
- **In Local Staging:** Handled via local compose connection string (`postgres://scholar_lens_stg:...@127.0.0.1:5434/...`).
- **In Pilot Staging:** Pointed to the pooled Neon Serverless PostgreSQL connection string (`postgresql://user:pass@ep-xyz-pooler.region.neon.tech/neondb?sslmode=require`).

---

## 4. Secret Setup Instructions for Project Owner

1. Navigate to: **`https://github.com/Sharique002/Scholar_Lens/settings/secrets/actions`**
2. Click **New repository secret**.
3. Add the following entries:

```
Name: GCP_PROJECT_ID
Value: scholar-lens-staging

Name: GCP_WIF_PROVIDER
Value: projects/<PROJECT_NUMBER>/locations/global/workloadIdentityPools/github-actions-pool/providers/github-actions-provider

Name: GCP_WIF_SERVICE_ACCOUNT
Value: github-deployer@scholar-lens-staging.iam.gserviceaccount.com

Name: GCP_REGION
Value: us-central1

Name: DATABASE_URL
Value: postgresql://<USER>:<PASSWORD>@<NEON_HOST>/neondb?sslmode=require

Name: DJANGO_SECRET_KEY
Value: <GENERATED_50_CHAR_SECRET_KEY>
```
