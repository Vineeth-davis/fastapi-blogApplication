# Docker Quick Start Guide

Run the application using Docker - no need to worry about Python version or system dependencies!

## Prerequisites

- **Docker Desktop** (Windows/Mac) or **Docker Engine** (Linux)
- **Docker Compose** (usually included with Docker Desktop)

## Quick Start (3 Steps!)

### Step 1: .env File

**✅ A production-ready `.env` file has been created for you!**

The `.env` file is already configured with:
- ✅ Randomly generated SECRET_KEY (secure)
- ✅ Production-like settings (ENVIRONMENT=production)
- ✅ PostgreSQL database configuration for Docker
- ✅ Rate limiting enabled
- ✅ JSON logging format
- ✅ All required environment variables

**Note:** The `.env` file is already created and ready to use. If you need to modify it, edit `.env` directly.

### Step 2: Start Everything

```bash
docker-compose up -d
```

This will:
- ✅ Pull required images (if needed)
- ✅ Start PostgreSQL database
- ✅ Start FastAPI application
- ✅ Start Nginx reverse proxy with SSL/HTTPS
- ✅ Run database migrations automatically
- ✅ Start Redis (optional)

### Step 3: Verify It's Running

Open your browser:
- **HTTPS API Docs**: https://localhost/docs
- **HTTPS Health Check**: https://localhost/health
- **HTTP** (redirects to HTTPS): http://localhost

**Note:** Browser will show a security warning for self-signed certificate. Click "Advanced" → "Proceed to localhost" to continue.

That's it! 🎉

**HTTPS is fully configured!** See [docs/HTTPS_DOCKER.md](docs/HTTPS_DOCKER.md) for details.

## Useful Commands

### View Logs

```bash
# All services
docker-compose logs -f

# Just the API
docker-compose logs -f api

# Just the database
docker-compose logs -f db
```

### Stop Services

```bash
docker-compose down
```

### Stop and Remove Data (Fresh Start)

```bash
docker-compose down -v
```

### Restart Services

```bash
docker-compose restart
```

### Run Database Migrations Manually

```bash
docker-compose exec api alembic upgrade head
```

### Access Database Shell

```bash
docker-compose exec db psql -U bloguser -d blogdb
```

### Access API Container Shell

```bash
docker-compose exec api bash
```

### Rebuild After Code Changes

```bash
docker-compose up -d --build
```

## Running Tests in Docker

```bash
# Run all tests
docker-compose exec api pytest

# Run with verbose output
docker-compose exec api pytest -v

# Run with coverage
docker-compose exec api pytest --cov=app --cov-report=html
```

## Troubleshooting

### Port 8000 Already in Use

Edit `docker-compose.yml` and change:
```yaml
ports:
  - "8001:8000"  # Change 8000 to 8001
```

Then access at http://localhost:8001

### Database Connection Errors

Check if database is ready:
```bash
docker-compose logs db
```

Wait a few seconds after starting, the database needs time to initialize.

### Container Won't Start

Check logs:
```bash
docker-compose logs api
```

Common issues:
- Port conflict: Change port in docker-compose.yml
- Missing .env file: Create .env file
- Docker not running: Start Docker Desktop

### Reset Everything

```bash
# Stop and remove everything including volumes
docker-compose down -v

# Remove images (optional)
docker-compose rm -f

# Start fresh
docker-compose up -d
```

### View Running Containers

```bash
docker-compose ps
```

### Check Container Status

```bash
docker ps
```

## Environment Variables

All environment variables are set in:
1. `.env` file (for docker-compose)
2. `docker-compose.yml` (defaults)

The `.env` file takes precedence.

## What Gets Created

- **PostgreSQL Database**: `blogdb` database with `bloguser` user
- **Database Data**: Persisted in Docker volume `postgres_data`
- **Application Logs**: In `./logs/` directory
- **Uploads**: In `./uploads/` directory

## Production Mode

For production, update `.env`:

```env
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=<strong-random-key>
DATABASE_URL=postgresql+asyncpg://bloguser:<strong-password>@db:5432/blogdb
RATE_LIMIT_ENABLED=true
```

## Next Steps

- See [docs/RUNNING.md](docs/RUNNING.md) for detailed instructions
- See [docs/API.md](docs/API.md) for API documentation
- See [README.md](README.md) for full documentation

## Summary

✅ **No Python installation needed**  
✅ **No version conflicts**  
✅ **No system dependencies**  
✅ **Everything runs in containers**  
✅ **Easy to reset and restart**

Just run `docker-compose up -d` and you're done! 🚀

