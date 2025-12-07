# FastAPI Blog Platform Backend

A production-ready FastAPI backend for a modern blog platform with authentication, real-time features (SSE/WebSockets), approval workflows, and comprehensive security measures.

## 🚀 Quick Start

### Option 1: Docker (Recommended - No Python Required)


1. **Clone the repository:**
   ```bash
   git clone https://github.com/Vineeth-davis/fastapi-blogApplication.git
   cd fastapi-blogApplication
   ```

2. **Start everything:**
   ```bash
   docker-compose up -d
   ```

3. **Access the API:**
   - **Swagger UI**: https://localhost/docs
   - **Health Check**: https://localhost/health
   - **API Base**: https://localhost/api

**That's it!** The application is running with:
- ✅ PostgreSQL database
- ✅ Nginx reverse proxy with HTTPS
- ✅ FastAPI application
- ✅ All migrations applied automatically


### Option 2: Local Python Setup

**If you prefer to run locally with Python:**

1. **Prerequisites:**
   - Python 3.10 or higher
   - PostgreSQL 12+ (or SQLite for development)

2. **Clone and setup:**
   ```bash
   git clone https://github.com/Vineeth-davis/fastapi-blogApplication.git
   cd fastapi-blogApplication
   
   # Create virtual environment
   python -m venv venv
   
   # Activate virtual environment
   # Windows:
   venv\Scripts\activate
   # Linux/Mac:
   source venv/bin/activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

3. **Configure environment:**
   ```bash
   # Copy example environment file
   cp .env.example .env
   
   # Edit .env and set your database URL and secret key
   # For SQLite (development):
   DATABASE_URL=sqlite+aiosqlite:///./blog.db
   # For PostgreSQL:
   DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/blogdb
   ```

4. **Run database migrations:**
   ```bash
   alembic upgrade head
   ```

5. **Start the application:**
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

6. **Access the API:**
   - **Swagger UI**: http://localhost:8000/docs
   - **Health Check**: http://localhost:8000/health
   - **API Base**: http://localhost:8000/api

## 📋 Features

- **Authentication & Authorization**: JWT-based authentication with role-based access control (user, admin, L1 approver)
- **Blog Management**: Full CRUD operations with approval workflow
- **Real-Time Features**: 
  - Server-Sent Events (SSE) for admin notifications
  - WebSocket support for real-time blog comments
- **Feature Requests**: Submit and manage feature requests
- **Session Management**: Draft saving for blog posts
- **Security**: HTTPS, CORS, input validation, rate limiting, secure password hashing
- **Production Ready**: Comprehensive logging, error handling, and deployment documentation

## 🛠️ Tech Stack

- **Framework**: FastAPI 0.109+
- **Database**: PostgreSQL (production) / SQLite (development)
- **ORM**: SQLAlchemy 2.0+ (async)
- **Authentication**: JWT (python-jose)
- **Password Hashing**: bcrypt (passlib)
- **Testing**: Pytest with async support
- **Deployment**: Nginx reverse proxy with SSL

## 👥 Pre-seeded Users

The database includes pre-seeded users for testing:

| Username | Email | Password | Role |
|----------|-------|----------|------|
| admin | admin@example.com | admin@1 | admin |
| approver | approver@example.com | approver@1 | l1_approver |
| user1 | user1@example.com | user1@1 | user |
| user2 | user2@example.com | user2@1 | user |
| user3 | user3@example.com | user3@1 | user |
| user4 | user4@example.com | user4@1 | user |
| user5 | user5@example.com | user5@1 | user |


## 📚 API Documentation

Once the application is running:

- **Swagger UI**: https://localhost/docs (Docker) or http://localhost:8000/docs (Local)
- **ReDoc**: https://localhost/redoc (Docker) or http://localhost:8000/redoc (Local)
- **OpenAPI JSON**: https://localhost/openapi.json (Docker) or http://localhost:8000/openapi.json (Local)

## 🚀 Production Deployment

### Quick Start (Recommended)

Use the unified deployment script that handles everything automatically:

```bash
# Make script executable
chmod +x scripts/deploy-production.sh

# Run deployment (reads from .env or prompts for values)
bash scripts/deploy-production.sh
```

**What the script does:**
- ✅ Reads configuration from `.env` file (or prompts you)
- ✅ Verifies DNS is configured correctly
- ✅ Sets up SSL certificate (Let's Encrypt)
- ✅ Creates/updates Nginx configuration
- ✅ Handles database migrations
- ✅ Deploys application with Docker
- ✅ Seeds initial users (optional)
- ✅ Verifies HTTPS, DNS, and everything works

### Step-by-Step Setup

#### Step 1: Create `.env` File (Optional but Recommended)

Create a `.env` file in the project root:

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

#### Step 2: Run Deployment Script

```bash
bash scripts/deploy-production.sh
```

The script will:
- Use values from `.env` if available
- Prompt for any missing values
- Handle all deployment steps automatically

#### Step 3: Access Your Application

After deployment completes:
- **HTTPS**: https://your-domain.com/docs
- **API**: https://your-domain.com/api
- **Health**: https://your-domain.com/health

### Manual Deployment (Alternative)

If you prefer manual steps:

1. **Get SSL Certificate:**
   ```bash
   sudo bash scripts/setup-ssl-docker.sh
   ```
   (Requires `.env` file with `DOMAIN`, `SSL_EMAIL`, `SERVER_IP`)

2. **Deploy:**
   ```bash
   docker-compose -f docker-compose.production.yml up -d
   ```

### Complete Documentation

For detailed deployment guides, see:
- **[README_DEPLOYMENT.md](README_DEPLOYMENT.md)** - Complete deployment guide ⭐ **START HERE**
- **[DEPLOYMENT_SUMMARY.md](DEPLOYMENT_SUMMARY.md)** - Deployment summary and FAQ
- **[SETUP_AWS_EC2.md](SETUP_AWS_EC2.md)** - AWS EC2 setup guide


## 🔐 Authentication

### Get Access Token

**POST** `/api/auth/login`

```json
{
  "email": "user1@example.com",
  "password": "user1@1"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "...",
  "token_type": "bearer"
}
```

### Use Token

Include the token in the `Authorization` header:
```
Authorization: Bearer {your_access_token}
```

## 🧪 Testing

Run the test suite:

```bash
# Docker
docker-compose exec api pytest

# Local
pytest
```

Run specific test files:
```bash
# Docker
docker-compose exec api pytest tests/test_auth.py -v

# Local
pytest tests/test_auth.py -v
```

## 🔧 Environment Variables

Key environment variables:

- `DATABASE_URL` - Database connection string
- `SECRET_KEY` - JWT secret key (generate a random string)
- `CORS_ORIGINS` - Allowed CORS origins (comma-separated)
- `SSL_ENABLED` - Enable SSL/HTTPS (true/false)

## 🐳 Docker Services

- **api** - FastAPI application (port 8000)
- **db** - PostgreSQL database (port 5432)
- **nginx** - Reverse proxy with SSL (ports 80, 443)
- **redis** - Redis cache (optional, port 6379)

## 📝 Project Structure

```
.
├── app/                    # Application code
│   ├── auth/               # Authentication & authorization
│   ├── blogs/              # Blog CRUD & WebSocket
│   ├── feature_requests/   # Feature requests
│   ├── notifications/       # SSE notifications
│   ├── session/            # Session management
│   ├── models/             # Database models
│   ├── middleware/         # Middleware (security, audit, rate limit)
│   └── main.py             # FastAPI application
├── tests/                  # Test suite
├── scripts/                 # Utility scripts
├── docs/                    # Documentation
├── alembic/                 # Database migrations
├── ssl/                     # SSL certificates (self-signed)
├── docker-compose.yml       # Docker Compose configuration
├── Dockerfile               # Docker image definition
└── requirements.txt         # Python dependencies
```

