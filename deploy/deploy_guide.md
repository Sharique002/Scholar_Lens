# Scholar Lens: Production Deployment Guide

This guide covers step-by-step instructions to deploy **Scholar Lens** to cloud hosting platforms or self-hosted servers.

---

## Architecture in Production

```
Internet (HTTPS)
       │
       ▼
Cloud Load Balancer / Nginx Reverse Proxy
       │ (Port 8000 / $PORT)
       ▼
Gunicorn WSGI Server (3 workers)
       │
 ┌─────┴────────────────────────┐
 │ Scholar Lens Django Backend   │
 ├──────────────────────────────┤
 │ • WhiteNoise (Static Files)  │
 │ • Media Storage (Disks/S3)   │
 └─────┬──────────────────┬─────┘
       │                  │
       ▼                  ▼
PostgreSQL Database    External APIs
(Render/Railway DB)   (OpenAI, SerpApi)
```

---

## 🚀 Option 1: Deploy to Render.com (Recommended Free Cloud Hosting)

Render offers a free web service and free managed PostgreSQL database.

### Step 1: Push Code to GitHub
1. Initialize git (if not already done):
   ```bash
   git init
   git add .
   git commit -m "Scholar Lens production deployment setup"
   ```
2. Create a new repository on [GitHub](https://github.com).
3. Link and push your code:
   ```bash
   git remote add origin https://github.com/<your-username>/<your-repo-name>.git
   git branch -M main
   git push -u origin main
   ```

### Step 2: Create Blueprint on Render
1. Go to [dashboard.render.com](https://dashboard.render.com) and log in.
2. Click **New +** in the top right and select **Blueprint**.
3. Connect your GitHub repository.
4. Render will automatically detect [`render.yaml`](render.yaml) from your repository.
5. Render provisions:
   - **PostgreSQL Database** (`scholar-lens-db`)
   - **Web Service** (`scholar-lens`) with Gunicorn and automated build/migration script
   - **Persistent Disk** for uploaded media PDFs
6. In the Environment Variables section, fill in your secret keys:
   - `OPENAI_API_KEY`: `your_openai_api_key`
   - `SERPAPI_API_KEY`: `your_serpapi_api_key` (optional, for Google Scholar live search)
7. Click **Apply**.
8. Once deployed, Render will provide a live HTTPS URL (e.g. `https://scholar-lens.onrender.com`).

---

## 🚆 Option 2: Deploy to Railway.app

Railway provides one-click repository deployment with automatic PostgreSQL.

1. Go to [railway.app](https://railway.app) and create a project from your GitHub repository.
2. Click **+ New** -> **Database** -> **Add PostgreSQL**.
3. Railway automatically sets `DATABASE_URL` for your web service.
4. Under the Web Service **Variables**, add:
   - `SECRET_KEY`: *(generate a random secret string)*
   - `DEBUG`: `False`
   - `ALLOWED_HOSTS`: `*`
   - `CSRF_TRUSTED_ORIGINS`: `https://${{RAILWAY_PUBLIC_DOMAIN}}`
   - `OPENAI_API_KEY`: `your_openai_api_key`
   - `SERPAPI_API_KEY`: `your_serpapi_api_key`
5. Railway reads `Procfile` and runs migrations automatically via `release:` step.
6. Generate a public domain under Settings -> Networking.

---

## 🐳 Option 3: Deploy with Docker Compose (Local or VPS)

If you have Docker and Docker Compose installed:

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Edit `.env` to configure `SECRET_KEY`, `OPENAI_API_KEY`, and `SERPAPI_API_KEY`.
3. Build and launch the container stack:
   ```bash
   docker compose up --build -d
   ```
4. Run migrations and create an admin user:
   ```bash
   docker compose exec web python manage.py migrate
   docker compose exec web python manage.py createsuperuser
   ```
5. Access your application at `http://localhost:8000`.

---

## 🐧 Option 4: Deploy to Ubuntu Linux VPS (AWS EC2 / DigitalOcean)

### Step 1: System Packages
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-pip python3-venv git nginx postgresql postgresql-contrib libpq-dev
```

### Step 2: Configure PostgreSQL
```bash
sudo -u postgres psql
CREATE DATABASE scholar_lens;
CREATE USER scholar_user WITH PASSWORD 'StrongPassword123!';
ALTER ROLE scholar_user SET client_encoding TO 'utf8';
ALTER ROLE scholar_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE scholar_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE scholar_lens TO scholar_user;
\q
```

### Step 3: Clone Code and Setup Virtual Environment
```bash
cd /var/www
sudo git clone <your-repo-url> scholar_lens
sudo chown -R $USER:$USER /var/www/scholar_lens
cd /var/www/scholar_lens

python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

cp .env.example .env
# Edit .env with your domain, DB credentials, and API keys
nano .env

python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

### Step 4: Systemd Service for Gunicorn (`/etc/systemd/system/scholar_lens.service`)
```ini
[Unit]
Description=Scholar Lens Gunicorn Daemon
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/scholar_lens
ExecStart=/var/www/scholar_lens/venv/bin/gunicorn \
          --access-logfile - \
          --workers 3 \
          --bind unix:/run/scholar_lens.sock \
          --timeout 120 \
          scholar_lens.wsgi:application

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl start scholar_lens
sudo systemctl enable scholar_lens
```

### Step 5: Nginx Configuration (`/etc/nginx/sites-available/scholar_lens`)
```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    client_max_body_size 25M;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        alias /var/www/scholar_lens/staticfiles/;
    }

    location /media/ {
        alias /var/www/scholar_lens/media/;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/run/scholar_lens.sock;
    }
}
```

Enable site and restart Nginx:
```bash
sudo ln -s /etc/nginx/sites-available/scholar_lens /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

Add free SSL certificate via Certbot:
```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

---

## 🔐 Environment Variables Reference

| Variable | Description | Production Example |
| :--- | :--- | :--- |
| `SECRET_KEY` | Django cryptographic signing key | *(A 50+ character random string)* |
| `DEBUG` | Debug mode (MUST BE `False` in prod) | `False` |
| `ALLOWED_HOSTS` | Comma-separated list of domain names | `scholar-lens.onrender.com,your-domain.com` |
| `CSRF_TRUSTED_ORIGINS` | Comma-separated list of HTTPS origins | `https://scholar-lens.onrender.com,https://your-domain.com` |
| `DATABASE_URL` | PostgreSQL connection URI | `postgres://user:pass@host:5432/dbname` |
| `OPENAI_API_KEY` | OpenAI API key for RAG & summaries | `sk-...` |
| `SERPAPI_API_KEY` | SerpApi key for Google Scholar discovery | `...` (optional) |
| `MAX_UPLOAD_SIZE_MB` | Maximum PDF file upload size | `20` |

---

## 🛠️ Post-Deployment Superuser Creation

To log in to the Django admin panel (`/admin/`) on your deployed instance, create a superuser:
* **Render**: Open the web service shell tab -> run `python manage.py createsuperuser`
* **Railway**: Use Railway CLI or bash console -> run `python manage.py createsuperuser`
* **Docker**: `docker compose exec web python manage.py createsuperuser`
* **VPS**: `source venv/bin/activate && python manage.py createsuperuser`
