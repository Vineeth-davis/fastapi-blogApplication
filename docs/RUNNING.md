# Running and Testing the Application

This guide provides step-by-step instructions to run and test the Blog Platform Backend application.

## Table of Contents

1. [Quick Start (Development)](#quick-start-development)
2. [Running Tests](#running-tests)
3. [Running with Docker](#running-with-docker)
4. [Verifying the Application](#verifying-the-application)
5. [Common Issues](#common-issues)

---

## Quick Start (Development)

### Step 1: Prerequisites

Ensure you have:
- Python 3.10 or higher
- pip (Python package manager)
- Git (to clone repository)

Check Python version:
```bash
python --version
# or
python3 --version
```

### Step 2: Clone Repository (If Not Already Done)

```bash
git clone <repository-url>
cd marlabs-assignement
```

### Step 3: Create Virtual Environment

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

You should see `(venv)` in your terminal prompt.

### Step 4: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 5: Set Up Environment Variables

Create a `.env` file in the project root:

```bash
# Windows
copy .env.example .env

# Linux/Mac
cp .env.example .env
```

**Note:** If `.env.example` doesn't exist, create `.env` with:

```env
# Application
ENVIRONMENT=development
DEBUG=true

# Database (SQLite for development)
DATABASE_URL=sqlite+aiosqlite:///./blog.db

# JWT Secret Key (generate a new one for production)
SECRET_KEY=dev-secret-key-change-in-production

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
CORS_CREDENTIALS=true
FRONTEND_URL=http://localhost:3000

# Rate Limiting (can disable for development)
RATE_LIMIT_ENABLED=false

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=text
```

### Step 6: Initialize Database

**Option A: Using Alembic Migrations (Recommended)**

```bash
# Create initial migration (if not exists)
alembic revision --autogenerate -m "Initial migration"

# Apply migrations
alembic upgrade head
```

**Option B: Auto-create Tables (Development Only)**

Uncomment the line in `app/main.py`:
```python
@app.on_event("startup")
async def startup_event():
    await init_db()  # Uncomment this line
```

### Step 7: Run the Application

**Development Mode (with auto-reload):**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Or using Python module:**
```bash
python -m uvicorn app.main:app --reload
```

**Production Mode:**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Step 8: Verify Application is Running

Open your browser and visit:
- **API Root**: http://localhost:8000
- **Interactive Docs (Swagger)**: http://localhost:8000/docs
- **Alternative Docs (ReDoc)**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

You should see:
- Root endpoint: Welcome message
- `/docs`: Swagger UI with all endpoints
- `/health`: `{"status": "healthy"}`

---

## Running Tests

### Prerequisites

Ensure you're in the project directory with virtual environment activated.

### Run All Tests

```bash
pytest
```

### Run Tests with Verbose Output

```bash
pytest -v
```

### Run Tests with Coverage

```bash
pytest --cov=app --cov-report=html --cov-report=term-missing
```

This will:
- Show coverage in terminal
- Generate HTML report in `htmlcov/index.html`

### Run Specific Test Files

```bash
# Authentication tests
pytest tests/test_auth.py -v

# Blog tests
pytest tests/test_blogs.py -v

# SSE tests
pytest tests/test_sse.py -v

# WebSocket tests
pytest tests/test_websocket.py -v
```

### Run Tests by Marker

```bash
# Run only auth tests
pytest -m auth

# Run only blog tests
pytest -m blogs

# Run only SSE tests
pytest -m sse

# Run only WebSocket tests
pytest -m websocket
```

### Run Specific Test

```bash
pytest tests/test_auth.py::TestAuthentication::test_register_success -v
```

### Expected Test Results

You should see output like:
```
tests/test_auth.py::TestAuthentication::test_register_success PASSED
tests/test_auth.py::TestAuthentication::test_login_success PASSED
tests/test_blogs.py::TestBlogCRUD::test_create_blog PASSED
...
```

**At minimum, these tests should pass (assignment requirements):**
- `test_create_blog` (user)
- `test_create_blog` (admin)
- `test_sse_notification_delivery`

---

## Running with Docker

### Prerequisites

- Docker installed
- Docker Compose installed

### Step 1: Create .env File

Create `.env` file in project root (see Step 5 above).

### Step 2: Start Services

```bash
docker-compose up -d
```

This will start:
- PostgreSQL database
- FastAPI application
- Redis (optional)

### Step 3: Run Migrations

```bash
docker-compose exec api alembic upgrade head
```

### Step 4: Check Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f db
```

### Step 5: Access Application

- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs

### Step 6: Stop Services

```bash
docker-compose down
```

### Step 7: Stop and Remove Volumes

```bash
docker-compose down -v
```

---

## Verifying the Application

### 1. Health Check

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{"status": "healthy"}
```

### 2. Root Endpoint

```bash
curl http://localhost:8000/
```

Expected response:
```json
{
  "message": "Welcome to Blog Platform API",
  "version": "1.0.0",
  "docs": "/docs"
}
```

### 3. Test User Registration

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "password": "testpassword123"
  }'
```

Expected response: `201 Created` with user data

### 4. Test User Login

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpassword123"
  }'
```

Expected response: `200 OK` with access_token and refresh_token

### 5. Test Protected Endpoint

```bash
# First, get token from login response
TOKEN="your_access_token_here"

curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

Expected response: `200 OK` with user data

### 6. Test Blog Creation

```bash
curl -X POST http://localhost:8000/api/blogs/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My First Blog Post",
    "content": "This is my first blog post content."
  }'
```

Expected response: `201 Created` with blog data

### 7. Test Public Blog Listing

```bash
curl http://localhost:8000/api/blogs/
```

Expected response: `200 OK` with list of approved blogs

### 8. Interactive API Testing

Visit http://localhost:8000/docs and use the Swagger UI to:
- Test all endpoints
- See request/response schemas
- Authenticate and test protected endpoints

---

## Common Issues

### Issue: Module Not Found

**Error:** `ModuleNotFoundError: No module named 'app'`

**Solution:**
```bash
# Ensure you're in the project root directory
cd marlabs-assignement

# Ensure virtual environment is activated
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

### Issue: Database Connection Error

**Error:** `sqlalchemy.exc.OperationalError`

**Solution:**
```bash
# For SQLite (development)
# Ensure DATABASE_URL in .env is correct:
DATABASE_URL=sqlite+aiosqlite:///./blog.db

# For PostgreSQL
# Ensure PostgreSQL is running and DATABASE_URL is correct:
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/dbname

# Check database exists
# SQLite: Check if blog.db file exists
# PostgreSQL: psql -U user -d dbname -h localhost
```

### Issue: Port Already in Use

**Error:** `Address already in use`

**Solution:**
```bash
# Find process using port 8000
# Linux/Mac:
lsof -i :8000
kill -9 <PID>

# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Or use a different port:
uvicorn app.main:app --reload --port 8001
```

### Issue: Migration Errors

**Error:** `alembic.util.exc.CommandError`

**Solution:**
```bash
# Initialize Alembic (if not done)
alembic init alembic

# Create initial migration
alembic revision --autogenerate -m "Initial migration"

# Apply migrations
alembic upgrade head

# If issues persist, check alembic.ini and alembic/env.py
```

### Issue: Import Errors in Tests

**Error:** `ImportError: cannot import name 'X'`

**Solution:**
```bash
# Ensure you're running tests from project root
cd marlabs-assignement

# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt

# Run tests with verbose output to see full error
pytest -v
```

### Issue: Rate Limiting in Development

**Error:** `429 Too Many Requests`

**Solution:**
In `.env` file, disable rate limiting:
```env
RATE_LIMIT_ENABLED=false
```

Or increase the limit:
```env
RATE_LIMIT_PER_MINUTE=1000
```

### Issue: CORS Errors

**Error:** CORS policy blocking requests

**Solution:**
In `.env` file, add your frontend URL:
```env
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000
```

---

## Development Workflow

### Typical Development Session

1. **Activate virtual environment**
   ```bash
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

2. **Start application**
   ```bash
   uvicorn app.main:app --reload
   ```

3. **Make code changes** - Application auto-reloads

4. **Run tests**
   ```bash
   pytest
   ```

5. **Check logs** - Application logs in `logs/` directory

6. **Test endpoints** - Use Swagger UI at http://localhost:8000/docs

---

## Production Checklist

Before deploying to production:

- [ ] Change `SECRET_KEY` to a strong random value
- [ ] Set `ENVIRONMENT=production`
- [ ] Set `DEBUG=false`
- [ ] Configure production database (PostgreSQL)
- [ ] Set up SSL/HTTPS certificates
- [ ] Configure CORS origins for production domain
- [ ] Enable rate limiting
- [ ] Set up logging and monitoring
- [ ] Run all tests and ensure they pass
- [ ] Review security settings

---

## Next Steps

- **API Documentation**: See [API.md](./API.md) for detailed endpoint documentation
- **Deployment**: See [DEPLOYMENT.md](./DEPLOYMENT.md) for production deployment
- **SSL Setup**: See [SSL_SETUP.md](./SSL_SETUP.md) for HTTPS configuration

---

## Quick Reference

```bash
# Start development server
uvicorn app.main:app --reload

# Run all tests
pytest

# Run tests with coverage
pytest --cov=app --cov-report=html

# Run migrations
alembic upgrade head

# Start with Docker
docker-compose up -d

# Check application health
curl http://localhost:8000/health
```

