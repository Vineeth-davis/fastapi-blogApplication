# Production Deployment Guide

## Quick Start (3 Steps)

### Step 1: Create `.env` File (Optional but Recommended)

Create a `.env` file in the project root with your configuration:

```bash
# Create .env file
cat > .env << EOF
DOMAIN=your-domain.com
SERVER_IP=your-server-ip
SSL_EMAIL=your-email@example.com
EOF
```

**Required values:**
- `DOMAIN` - Your domain (e.g., `fastapiblogapp.duckdns.org`)
- `SERVER_IP` - Your server's public IP address
- `SSL_EMAIL` - Email for SSL certificate notifications

**Example:**
```env
DOMAIN=fastapiblogapp.duckdns.org
SERVER_IP=13.236.76.18
SSL_EMAIL=lordvineeth@gmail.com
```

### Step 2: Run Deployment Script

```bash
# Make script executable
chmod +x scripts/deploy-production.sh

# Run deployment
bash scripts/deploy-production.sh
```

**What happens:**
- ✅ Script reads from `.env` file (if exists)
- ✅ Prompts for any missing values
- ✅ Verifies DNS configuration
- ✅ Sets up SSL certificate (Let's Encrypt)
- ✅ Updates Nginx configuration
- ✅ Creates/updates database migrations
- ✅ Deploys application with Docker
- ✅ Seeds initial users (optional)
- ✅ Verifies HTTPS, DNS, and everything works

### Step 3: Access Your Application

After deployment completes:
- **HTTPS**: https://your-domain.com/docs
- **API**: https://your-domain.com/api
- **Health**: https://your-domain.com/health

**That's it!** Your application is live with HTTPS. 🎉

## What the Script Does

The `deploy-production.sh` script automates all deployment steps:

1. **Configuration** - Reads from `.env` or prompts user
2. **DNS Verification** - Checks if domain points to correct IP
3. **Docker Setup** - Installs Docker/Docker Compose if needed
4. **Migration Check** - Verifies/creates database migrations
5. **SSL Certificate** - Gets Let's Encrypt certificate
6. **Nginx Config** - Updates with your domain
7. **Firewall** - Configures UFW (ports 22, 80, 443)
8. **Deployment** - Starts all Docker containers
9. **Migrations** - Applies database migrations
10. **User Seeding** - Optionally seeds initial users
11. **Verification** - Tests HTTPS and container health


## Script Details

### `deploy-production.sh` ⭐ (Recommended)

**Purpose:** Complete production deployment in one command

**Features:**
- ✅ Reads from `.env` file (if available)
- ✅ Interactive prompts for missing values
- ✅ DNS verification
- ✅ SSL certificate setup (Let's Encrypt)
- ✅ Nginx configuration update
- ✅ Database migration handling
- ✅ Docker deployment
- ✅ User seeding (optional)
- ✅ Full verification

**Usage:**
```bash
bash scripts/deploy-production.sh
```

**Use when:** First-time deployment or full redeployment

### `setup-ssl-docker.sh`

**Purpose:** SSL certificate setup only

**Features:**
- Gets Let's Encrypt certificate
- Sets up auto-renewal
- Requires `.env` file with `DOMAIN`, `SSL_EMAIL`, `SERVER_IP`

**Usage:**
```bash
sudo bash scripts/setup-ssl-docker.sh
```

**Use when:** Only need to get/update SSL certificate

### `setup-production.sh`

**Purpose:** Initial server setup

**Features:**
- Installs Docker, Docker Compose, Certbot
- Configures firewall
- Updates Nginx config

**Usage:**
```bash
bash scripts/setup-production.sh
```

**Use when:** Setting up a fresh server (before first deployment)

## Migration Handling

**Who handles migrations?**

1. **Automatic (docker-compose.production.yml):**
   - Migrations run automatically when container starts
   - Command: `alembic upgrade head`
   - Runs on every container restart

2. **Manual (if needed):**
   ```bash
   # Create migration
   docker exec blog_platform_api alembic revision --autogenerate -m "Migration name"
   
   # Apply migration
   docker exec blog_platform_api alembic upgrade head
   ```

3. **Deployment Script:**
   - Checks if migrations exist
   - Creates initial migration if needed
   - Applies all migrations

## Environment Variables

### Required for Deployment

Create `.env` file with these **required** values:

```env
# Domain Configuration (REQUIRED)
DOMAIN=your-domain.com
SERVER_IP=your-server-ip-address
SSL_EMAIL=your-email@example.com
```

### Optional Application Settings

You can also add these to `.env` (they have defaults):

```env
# Application Settings (Optional)
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=your-secret-key-here

# Database (usually set in docker-compose)
DATABASE_URL=postgresql+asyncpg://bloguser:changeme@db:5432/blogdb

# CORS
CORS_ORIGINS=https://your-domain.com
CORS_CREDENTIALS=true
SSL_ENABLED=true
```

### Example `.env` File

```env
# Domain Configuration
DOMAIN=fastapiblogapp.duckdns.org
SERVER_IP=13.236.76.18
SSL_EMAIL=lordvineeth@gmail.com

# Application
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=change-this-to-a-random-secret-key
```

## Verification

After deployment, verify:

1. **Containers are running:**
   ```bash
   docker-compose -f docker-compose.production.yml ps
   ```

2. **HTTPS works:**
   ```bash
   curl -I https://your-domain.com/health
   ```

3. **API docs accessible:**
   - Visit: `https://your-domain.com/docs`

4. **Users exist:**
   ```bash
   docker exec blog_platform_api python /app/scripts/list_users.py
   ```

## Troubleshooting

### SSL Certificate Issues

```bash
# Check certificate
sudo ls -la /etc/letsencrypt/live/your-domain.com/

# Regenerate certificate
sudo bash scripts/setup-ssl-docker.sh
```

### Migration Issues

```bash
# Check migration status
docker exec blog_platform_api alembic current

# Create migration if needed
docker exec blog_platform_api alembic revision --autogenerate -m "Migration name"

# Apply migrations
docker exec blog_platform_api alembic upgrade head
```

### DNS Issues

```bash
# Verify DNS
dig your-domain.com

# Should return your SERVER_IP
```

## Quick Reference

### First-Time Deployment

```bash
# 1. Create .env file
cat > .env << EOF
DOMAIN=your-domain.com
SERVER_IP=your-server-ip
SSL_EMAIL=your-email@example.com
EOF

# 2. Run deployment script
chmod +x scripts/deploy-production.sh
bash scripts/deploy-production.sh

# 3. Access your application
# https://your-domain.com/docs
```

### Subsequent Deployments

```bash
# Just run the script again (uses existing .env)
bash scripts/deploy-production.sh
```

### Update SSL Certificate

```bash
# If certificate expires or needs renewal
sudo bash scripts/setup-ssl-docker.sh
```

## Summary

- ✅ **Use `deploy-production.sh`** for complete deployment (recommended)
- ✅ **Create `.env` file** with `DOMAIN`, `SERVER_IP`, `SSL_EMAIL`
- ✅ **Migrations run automatically** on container start
- ✅ **SSL setup** is handled by the deployment script
- ✅ **Everything is verified** at the end
- ✅ **No hardcoded values** - all from `.env` or user input

## Need Help?

- **Troubleshooting**: See troubleshooting section below
- **Detailed Guide**: See [DEPLOYMENT_SUMMARY.md](DEPLOYMENT_SUMMARY.md)
- **AWS Setup**: See [SETUP_AWS_EC2.md](SETUP_AWS_EC2.md)

