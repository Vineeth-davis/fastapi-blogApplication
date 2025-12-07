# Production Deployment Guide

This guide provides step-by-step instructions for deploying the Blog Platform Backend to production.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Server Setup](#server-setup)
3. [Database Setup](#database-setup)
4. [Application Deployment](#application-deployment)
5. [Nginx Configuration](#nginx-configuration)
6. [SSL Certificate Setup](#ssl-certificate-setup)
7. [Environment Configuration](#environment-configuration)
8. [Database Migrations](#database-migrations)
9. [Monitoring and Logging](#monitoring-and-logging)
10. [Firewall Configuration](#firewall-configuration)
11. [Troubleshooting](#troubleshooting)

---

## Prerequisites

- Ubuntu 20.04+ or similar Linux distribution
- Root or sudo access
- **Domain name (optional)** - Only needed for Let's Encrypt SSL certificates. For self-signed certificates, you can use your server's IP address.
- Python 3.10+ installed
- PostgreSQL 12+ installed
- Nginx installed
- Git installed

**Note:** The assignment requires HTTPS/SSL setup. You can achieve this with either:
- **Let's Encrypt certificates** (requires domain name) - Recommended for production
- **Self-signed certificates** (works with IP address) - Suitable for testing/development

---

## Server Setup

### 1. Update System

```bash
sudo apt update && sudo apt upgrade -y
```

### 2. Create Application User

```bash
sudo adduser --disabled-password --gecos "" appuser
sudo usermod -aG sudo appuser
```

### 3. Install Required Packages

```bash
sudo apt install -y \
    python3.11 \
    python3.11-venv \
    python3-pip \
    postgresql \
    postgresql-contrib \
    nginx \
    certbot \
    python3-certbot-nginx \
    git \
    build-essential
```

---

## Database Setup

### 1. Create PostgreSQL Database and User

```bash
sudo -u postgres psql
```

In PostgreSQL prompt:

```sql
CREATE DATABASE blogdb;
CREATE USER bloguser WITH PASSWORD 'your_secure_password';
ALTER ROLE bloguser SET client_encoding TO 'utf8';
ALTER ROLE bloguser SET default_transaction_isolation TO 'read committed';
ALTER ROLE bloguser SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE blogdb TO bloguser;
\q
```

### 2. Configure PostgreSQL

Edit `/etc/postgresql/15/main/postgresql.conf`:

```bash
sudo nano /etc/postgresql/15/main/postgresql.conf
```

Ensure these settings:
```
listen_addresses = 'localhost'
max_connections = 100
```

Edit `/etc/postgresql/15/main/pg_hba.conf`:

```bash
sudo nano /etc/postgresql/15/main/pg_hba.conf
```

Ensure local connections are trusted:
```
local   all             all                                     peer
host    all             all             127.0.0.1/32            md5
```

Restart PostgreSQL:

```bash
sudo systemctl restart postgresql
```

---

## Application Deployment

### 1. Clone Repository

```bash
cd /opt
sudo git clone <your-repository-url> blog-platform
sudo chown -R appuser:appuser blog-platform
cd blog-platform
```

### 2. Create Virtual Environment

```bash
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configure Environment Variables

```bash
cp .env.example .env
nano .env
```

Set production values:

```env
# Application
ENVIRONMENT=production
DEBUG=false

# Database
DATABASE_URL=postgresql+asyncpg://bloguser:your_secure_password@localhost:5432/blogdb

# JWT
SECRET_KEY=your_generated_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
CORS_CREDENTIALS=true
FRONTEND_URL=https://yourdomain.com

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# SSL/HTTPS
SSL_ENABLED=true
```

**Important:** Generate a strong SECRET_KEY:

```bash
openssl rand -hex 32
```

### 4. Run Database Migrations

```bash
source venv/bin/activate
alembic upgrade head
```

### 5. Create Systemd Service

Create `/etc/systemd/system/blog-platform.service`:

```bash
sudo nano /etc/systemd/system/blog-platform.service
```

```ini
[Unit]
Description=Blog Platform Backend API
After=network.target postgresql.service

[Service]
Type=notify
User=appuser
Group=appuser
WorkingDirectory=/opt/blog-platform
Environment="PATH=/opt/blog-platform/venv/bin"
ExecStart=/opt/blog-platform/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable blog-platform
sudo systemctl start blog-platform
sudo systemctl status blog-platform
```

---

## Nginx Configuration

### 1. Copy Nginx Configuration

```bash
sudo cp nginx.conf /etc/nginx/sites-available/blog-platform
```

### 2. Update Server Name

Edit the configuration:

```bash
sudo nano /etc/nginx/sites-available/blog-platform
```

Replace `yourdomain.com` with your actual domain.

### 3. Enable Site

```bash
sudo ln -s /etc/nginx/sites-available/blog-platform /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

**Note:** SSL certificates must be obtained first (see next section).

---

## SSL Certificate Setup

### 1. Install Certbot

```bash
sudo apt install certbot python3-certbot-nginx
```

### 2. Obtain SSL Certificate

```bash
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

Follow the prompts:
- Enter your email address
- Agree to terms of service
- Choose whether to redirect HTTP to HTTPS (recommended: Yes)

### 3. Auto-Renewal

Certbot sets up automatic renewal. Test it:

```bash
sudo certbot renew --dry-run
```

### 4. Update Nginx Configuration

After obtaining certificates, update `/etc/nginx/sites-available/blog-platform` with the correct certificate paths (Certbot does this automatically, but verify).

---

## Environment Configuration

### Production Environment Variables

Ensure all production settings are configured in `.env`:

- `ENVIRONMENT=production`
- `DEBUG=false`
- Strong `SECRET_KEY`
- Production `DATABASE_URL`
- Correct `CORS_ORIGINS`
- `SSL_ENABLED=true`

### Docker Secrets (If Using Docker)

For containerized deployments, use Docker secrets:

```bash
echo "your_secret_key" | docker secret create secret_key -
echo "postgresql://..." | docker secret create database_url -
```

---

## Database Migrations

### Running Migrations

```bash
cd /opt/blog-platform
source venv/bin/activate
alembic upgrade head
```

### Creating New Migrations

```bash
alembic revision --autogenerate -m "Description"
alembic upgrade head
```

### Rollback (If Needed)

```bash
alembic downgrade -1
```

---

## Monitoring and Logging

### 1. Application Logs

Logs are stored in `/opt/blog-platform/logs/`:

```bash
tail -f /opt/blog-platform/logs/app.log
```

### 2. Systemd Logs

```bash
sudo journalctl -u blog-platform -f
```

### 3. Nginx Logs

```bash
sudo tail -f /var/log/nginx/blog-platform-access.log
sudo tail -f /var/log/nginx/blog-platform-error.log
```

### 4. Database Logs

```bash
sudo tail -f /var/log/postgresql/postgresql-15-main.log
```

### 5. Health Check

```bash
curl https://yourdomain.com/health
```

---

## Firewall Configuration

### 1. Configure UFW (Ubuntu Firewall)

```bash
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp     # HTTP
sudo ufw allow 443/tcp    # HTTPS
sudo ufw enable
sudo ufw status
```

### 2. Cloud Provider Security Groups

If using AWS, Azure, or GCP, configure security groups:

**Inbound Rules:**
- Port 22 (SSH): Your IP only
- Port 80 (HTTP): 0.0.0.0/0
- Port 443 (HTTPS): 0.0.0.0/0

**Outbound Rules:**
- Port 5432 (PostgreSQL): Database security group only
- Port 443 (HTTPS): 0.0.0.0/0 (for external APIs)

### 3. Private Networks

- Database should be in a private network/VPC
- Application servers can be in private network with load balancer
- Only load balancer should be publicly accessible

---

## Troubleshooting

### Application Not Starting

1. Check systemd status:
   ```bash
   sudo systemctl status blog-platform
   ```

2. Check logs:
   ```bash
   sudo journalctl -u blog-platform -n 50
   ```

3. Verify environment variables:
   ```bash
   cat /opt/blog-platform/.env
   ```

### Database Connection Issues

1. Test PostgreSQL connection:
   ```bash
   psql -U bloguser -d blogdb -h localhost
   ```

2. Check PostgreSQL status:
   ```bash
   sudo systemctl status postgresql
   ```

3. Verify DATABASE_URL in `.env`

### Nginx Issues

1. Test configuration:
   ```bash
   sudo nginx -t
   ```

2. Check error logs:
   ```bash
   sudo tail -f /var/log/nginx/error.log
   ```

3. Verify upstream is reachable:
   ```bash
   curl http://127.0.0.1:8000/health
   ```

### SSL Certificate Issues

1. Check certificate expiration:
   ```bash
   sudo certbot certificates
   ```

2. Renew certificate manually:
   ```bash
   sudo certbot renew
   ```

3. Verify certificate paths in Nginx config

### WebSocket/SSE Issues

1. Verify Nginx proxy settings for WebSocket/SSE
2. Check application logs for connection errors
3. Test WebSocket connection:
   ```bash
   wscat -c wss://yourdomain.com/api/blogs/1/ws?token=...
   ```

---

## Backup and Recovery

### Database Backup

```bash
# Create backup
pg_dump -U bloguser -d blogdb > backup_$(date +%Y%m%d).sql

# Restore backup
psql -U bloguser -d blogdb < backup_20240101.sql
```

### Application Backup

```bash
# Backup application files
tar -czf blog-platform-backup.tar.gz /opt/blog-platform

# Backup logs
tar -czf logs-backup.tar.gz /opt/blog-platform/logs
```

### Automated Backups

Set up cron job for daily backups:

```bash
crontab -e
```

Add:
```
0 2 * * * /usr/bin/pg_dump -U bloguser -d blogdb > /backups/blogdb_$(date +\%Y\%m\%d).sql
```

---

## Performance Optimization

### 1. Gunicorn Workers

For production, consider using Gunicorn with Uvicorn workers:

```bash
pip install gunicorn
```

Update systemd service:
```ini
ExecStart=/opt/blog-platform/venv/bin/gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### 2. Database Connection Pooling

Already configured in `app/database.py`:
- `pool_size=10`
- `max_overflow=20`

### 3. Nginx Caching (Optional)

Add caching for static content in Nginx config.

---

## Security Checklist

- [ ] Strong SECRET_KEY generated
- [ ] `.env` file not committed to Git
- [ ] HTTPS enabled and working
- [ ] CORS origins restricted
- [ ] Rate limiting enabled
- [ ] Firewall configured
- [ ] Database credentials secure
- [ ] SSL certificates auto-renewing
- [ ] Security headers enabled
- [ ] Regular backups configured
- [ ] Logs monitored
- [ ] Dependencies up to date

---

## Next Steps

1. Set up monitoring (e.g., Prometheus, Grafana)
2. Configure log aggregation (e.g., ELK stack)
3. Set up CI/CD pipeline
4. Configure automated backups
5. Set up alerting for critical issues

---

For manual steps that require user intervention, see [MANUAL_STEPS.md](./MANUAL_STEPS.md).

