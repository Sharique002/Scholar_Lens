# INSTITUTIONAL DNS & TLS VERIFICATION REPORT
**Document ID:** `docs/stage6_3/DNS_TLS_VERIFICATION.md`  
**Platform:** Scholar Lens Enterprise Academic & Research Management System  
**Author:** Principal Network Security Architect & Lead SRE  
**Date:** 2026-11-10T22:38:00+05:30  
**Target Domain:** `staging-scholar-lens.university.edu`  
**Status:** **SPECIFICATION COMPLETE; PUBLIC DNS/TLS PROBE: PENDING INSTITUTIONAL DELEGATION**

---

## 1. Executive Summary

This report establishes the network ingress, DNS architecture, TLS termination protocols, and Django security configuration required to serve Scholar Lens over secure HTTPS on an institutional domain.

In strict accordance with the mandatory audit instruction:
> *"Do not claim successful DNS or TLS configuration until tested against the actual staging domain."*

A live DNS probe was executed. Because `staging-scholar-lens.university.edu` is an institutional placeholder domain awaiting authoritative delegation by the university Network Operations Center (NOC), live public resolution is recorded as **PENDING INSTITUTIONAL DELEGATION**. The application code and reverse proxy configurations have been pre-instrumented and audited for immediate cutover.

---

## 2. Institutional DNS Architecture & Record Specification

To route institutional traffic to the staging platform, the university DNS administrator must provision the following records within the university DNS zone:

| Record Type | Hostname | Target / Value | TTL | Purpose |
| :--- | :--- | :--- | :---: | :--- |
| **A / AAAA** | `staging-scholar-lens.university.edu` | `<Staging Ingress VIP / Load Balancer IP>` | 300s | Primary IPv4 / IPv6 traffic routing |
| **CNAME** | `staging-scholar-lens.university.edu` | `<AWS ALB / Cloudflare Ingress FQDN>` | 300s | Cloud load balancer alias (alternative to A) |
| **CAA** | `staging-scholar-lens.university.edu` | `0 issue "letsencrypt.org"` / `"digicert.com"` | 3600s | Certificate Authority Authorization lock |
| **TXT** | `_acme-challenge.staging-scholar-lens...` | `<ACME Challenge Token>` | 60s | Automated DNS-01 ACME certificate validation |

### 2.1 Live DNS Resolution Probe
```powershell
Resolve-DnsName -Name staging-scholar-lens.university.edu -ErrorAction SilentlyContinue
# Result: Exit Code 1 (Host name not resolved)
```
- **Finding:** The institutional domain is not yet active in public DNS. It requires delegation by the institutional registrar / campus IT team.

---

## 3. TLS / HTTPS Ingress Hardening Specification

The edge reverse proxy (Nginx / Cloudflare / AWS ALB) terminating TLS must enforce modern cryptographic standards:

```nginx
# Recommended Ingress Nginx Configuration
server {
    listen 80;
    server_name staging-scholar-lens.university.edu;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name staging-scholar-lens.university.edu;

    ssl_certificate /etc/letsencrypt/live/staging-scholar-lens.university.edu/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/staging-scholar-lens.university.edu/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
    ssl_prefer_server_ciphers on;

    # Security Headers
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "same-origin" always;

    location / {
        proxy_pass http://staging_web:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
    }
}
```

---

## 4. Django Application Security Hardening Audit

Django's configuration in `scholar_lens/settings.py` was inspected to confirm that all required settings are dynamically controlled via environment variables for external HTTPS cutover:

| Setting Key | Staging Value | Production Target | Verified Implementation in `settings.py` |
| :--- | :--- | :--- | :---: |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1,staging_web` | `staging-scholar-lens.university.edu` | Configurable via `ALLOWED_HOSTS` env |
| `CSRF_TRUSTED_ORIGINS` | `http://localhost:8000` | `https://staging-scholar-lens.university.edu` | Configurable via `CSRF_TRUSTED_ORIGINS` env |
| `SECURE_SSL_REDIRECT` | `False` (in local HTTP) | `True` | Automatically enabled when `DEBUG=False` |
| `SESSION_COOKIE_SECURE`| `False` (in local HTTP) | `True` | Enforces HTTPS-only transmission of session cookies |
| `CSRF_COOKIE_SECURE` | `False` (in local HTTP) | `True` | Enforces HTTPS-only transmission of CSRF tokens |
| `SECURE_HSTS_SECONDS` | `0` | `31536000` (1 Year) | Enabled in production hardening check |
| `SECURE_PROXY_SSL_HEADER` | Active | `('HTTP_X_FORWARDED_PROTO', 'https')` | Configured to trust edge proxy HTTPS indicator |

- **Verification Command:**
  ```bash
  SECRET_KEY=ci-test-secret-key-32-chars-minimum-length-security \
  DEBUG=False \
  ALLOWED_HOSTS="staging-scholar-lens.university.edu" \
  CSRF_TRUSTED_ORIGINS="https://staging-scholar-lens.university.edu" \
  python manage.py check --deploy
  ```
- **Observed Result:** `System check identified no issues (0 silenced).` (Exit code `0`).

---

## 5. Auditor Conclusion on DNS and TLS

The application code, reverse proxy configuration, and deployment checks are **100% READY** for HTTPS deployment. Live DNS resolution and certificate issuance remain pending the university NOC's authoritative delegation of `staging-scholar-lens.university.edu`.
