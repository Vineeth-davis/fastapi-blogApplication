# Quick Start Guide

Get the application running in 5 minutes!

## ⚡ Recommended: Use Docker (No Python/System Requirements!)

**Want to skip Python version issues? Use Docker instead!**

👉 **See [DOCKER_QUICKSTART.md](DOCKER_QUICKSTART.md) for Docker setup (recommended)**

---

## Alternative: Local Python Setup

## Prerequisites

- Python 3.10+ (you have Python 3.8 - consider upgrading or use Python 3.10+)
- pip

## Step-by-Step

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Create .env File

```bash
# Windows
copy .env.example .env

# Linux/Mac
cp .env.example .env
```

The `.env` file is already configured for development with SQLite.

### 3. Initialize Database

**Option A: Using Migrations (Recommended)**
```bash
alembic upgrade head
```

**Option B: Auto-create (Quick)**
Uncomment `await init_db()` in `app/main.py` line 80, then run the app once.

### 4. Run the Application

```bash
uvicorn app.main:app --reload
```

### 5. Verify It's Working

Open your browser:
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### 6. Run Tests

```bash
pytest
```

## Quick Test

Test the API with curl:

```bash
# Health check
curl http://localhost:8000/health

# Register a user
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "username": "testuser", "password": "test123"}'

# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "test123"}'
```

## Troubleshooting

**Python version too old?**
- Install Python 3.10+ from python.org
- Or use pyenv to manage versions

**Port 8000 already in use?**
```bash
uvicorn app.main:app --reload --port 8001
```

**Database errors?**
- Ensure SQLite file can be created (check write permissions)
- Or use PostgreSQL: `DATABASE_URL=postgresql+asyncpg://user:pass@localhost/db`

**Import errors?**
```bash
# Reinstall dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

## Next Steps

- See [docs/RUNNING.md](docs/RUNNING.md) for detailed instructions
- See [docs/API.md](docs/API.md) for API documentation
- See [README.md](README.md) for full documentation

