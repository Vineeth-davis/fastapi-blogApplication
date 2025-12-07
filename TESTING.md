# Testing Guide for Blog Platform Backend

This guide provides step-by-step instructions to test if the project is working correctly.

## Prerequisites

- Docker and Docker Compose installed and running
- All containers should be up and running

## Quick Health Check

### 1. Check Container Status

```bash
docker-compose ps
```

All containers should show "Up" status:
- `blog_platform_api` - FastAPI application
- `blog_platform_db` - PostgreSQL database
- `blog_platform_nginx` - Nginx reverse proxy
- `blog_platform_redis` - Redis (optional)

### 2. Check Application Logs

```bash
# View API logs
docker-compose logs api --tail 50

# Check for errors
docker-compose logs api | Select-String -Pattern "error|Error|ERROR"
```

### 3. Test Health Endpoint

**Using PowerShell:**
```powershell
Invoke-RestMethod -Uri http://localhost:8000/health
```

**Using curl (if available):**
```bash
curl http://localhost:8000/health
```

**Expected Response:**
```json
{
  "status": "healthy"
}
```

### 4. Test Root Endpoint

```powershell
Invoke-RestMethod -Uri http://localhost:8000/
```

**Expected Response:**
```json
{
  "message": "Welcome to Blog Platform API",
  "version": "1.0.0",
  "docs": "/docs"
}
```

## Access Swagger UI (Interactive API Documentation)

Open your browser and navigate to:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

This provides an interactive interface to test all API endpoints.

## Manual API Testing

### Step 1: Register a New User

**Endpoint:** `POST /api/auth/register`

**PowerShell:**
```powershell
$body = @{
    email = "test@example.com"
    username = "testuser"
    password = "Test1234!"
} | ConvertTo-Json

Invoke-RestMethod -Uri http://localhost:8000/api/auth/register `
    -Method POST `
    -Body $body `
    -ContentType "application/json"
```

**Expected Response:**
```json
{
  "id": 1,
  "email": "test@example.com",
  "username": "testuser",
  "role": "user",
  "is_active": true,
  "created_at": "2025-12-07T00:00:00",
  "updated_at": "2025-12-07T00:00:00"
}
```

### Step 2: Login

**Endpoint:** `POST /api/auth/login`

```powershell
$body = @{
    email = "test@example.com"
    password = "Test1234!"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri http://localhost:8000/api/auth/login `
    -Method POST `
    -Body $body `
    -ContentType "application/json"

# Save the access token
$token = $response.access_token
Write-Host "Access Token: $token"
```

**Expected Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Step 3: Get Current User Info

**Endpoint:** `GET /api/auth/me`

```powershell
$headers = @{
    Authorization = "Bearer $token"
}

Invoke-RestMethod -Uri http://localhost:8000/api/auth/me `
    -Method GET `
    -Headers $headers
```

### Step 4: Create a Blog Post

**Endpoint:** `POST /api/blogs/`

```powershell
$body = @{
    title = "My First Blog Post"
    content = "This is the content of my first blog post."
    images = @()
} | ConvertTo-Json

Invoke-RestMethod -Uri http://localhost:8000/api/blogs/ `
    -Method POST `
    -Body $body `
    -ContentType "application/json" `
    -Headers $headers
```

**Expected Response:**
```json
{
  "id": 1,
  "title": "My First Blog Post",
  "content": "This is the content of my first blog post.",
  "status": "pending",
  "author_id": 1,
  "images": [],
  "created_at": "2025-12-07T00:00:00",
  "updated_at": "2025-12-07T00:00:00"
}
```

### Step 5: List All Blogs (Public)

**Endpoint:** `GET /api/blogs/`

```powershell
Invoke-RestMethod -Uri http://localhost:8000/api/blogs/
```

This should return only approved blogs (empty initially since your blog is pending).

### Step 6: Create Admin User and Approve Blog

To approve blogs, you need an admin user. You can either:
1. Use the role management endpoint (if you have admin access)
2. Manually update the database
3. Use the Swagger UI to test admin endpoints

## Using Swagger UI (Recommended)

1. Open http://localhost:8000/docs in your browser
2. Click on any endpoint to expand it
3. Click "Try it out"
4. Fill in the required parameters
5. Click "Execute"
6. View the response

### Testing Authentication in Swagger UI

1. Go to `/api/auth/register` endpoint
2. Click "Try it out"
3. Fill in the request body:
   ```json
   {
     "email": "admin@example.com",
     "username": "admin",
     "password": "Admin1234!"
   }
   ```
4. Click "Execute"
5. Copy the response (you'll need the user ID)

6. To make a user admin, you can:
   - Use the database directly
   - Or use the role management endpoint if available

## Database Testing

### Connect to Database

```bash
docker-compose exec db psql -U bloguser -d blogdb
```

### Useful SQL Queries

```sql
-- List all users
SELECT id, email, username, role, is_active FROM users;

-- List all blogs
SELECT id, title, status, author_id, created_at FROM blogs;

-- Make a user admin
UPDATE users SET role = 'admin' WHERE email = 'admin@example.com';

-- Approve a blog
UPDATE blogs SET status = 'approved' WHERE id = 1;
```

## Automated Testing

### Run Test Suite

```bash
# Run all tests
docker-compose exec api pytest

# Run with coverage
docker-compose exec api pytest --cov=app --cov-report=html

# Run specific test file
docker-compose exec api pytest tests/test_auth.py

# Run with verbose output
docker-compose exec api pytest -v
```

### Test Categories

- **Authentication Tests**: `tests/test_auth.py`
- **Blog CRUD Tests**: `tests/test_blogs.py`
- **SSE Notification Tests**: `tests/test_sse.py`
- **WebSocket Tests**: `tests/test_websocket.py`

## Testing Real-Time Features

### Server-Sent Events (SSE) Notifications

1. Register and login as an admin user
2. Open http://localhost:8000/api/notifications/sse in your browser
3. In another tab, create a blog post (as a regular user)
4. You should see a notification appear in the SSE stream

### WebSocket Comments

1. Get a blog ID (create a blog first)
2. Connect to: `ws://localhost:8000/api/blogs/{blog_id}/ws?token={access_token}`
3. Send a message:
   ```json
   {
     "type": "comment",
     "content": "This is a test comment"
   }
   ```
4. The comment should be broadcast to all connected clients

## Common Issues and Solutions

### Issue: "Connection refused" or "Cannot connect"

**Solution:**
- Check if containers are running: `docker-compose ps`
- Check logs: `docker-compose logs api`
- Ensure port 8000 is not in use by another application

### Issue: "401 Unauthorized"

**Solution:**
- Make sure you're including the Bearer token in the Authorization header
- Check if the token has expired (tokens expire after 15 minutes)
- Login again to get a new token

### Issue: "Database connection error"

**Solution:**
- Check database container: `docker-compose ps db`
- Check database logs: `docker-compose logs db`
- Verify database credentials in `docker-compose.yml`

### Issue: "Circular import error"

**Solution:**
- This is a code issue that needs to be fixed
- Check the logs for the exact import error
- Fix the circular dependency in the code

## Performance Testing

### Check Response Times

```powershell
Measure-Command {
    Invoke-RestMethod -Uri http://localhost:8000/health
}
```

### Load Testing (if you have Apache Bench or similar)

```bash
# Install Apache Bench (ab) or use a similar tool
ab -n 1000 -c 10 http://localhost:8000/health
```

## Next Steps

1. ✅ Verify all containers are running
2. ✅ Test health endpoint
3. ✅ Test authentication (register/login)
4. ✅ Test blog creation
5. ✅ Test admin features (if you have admin access)
6. ✅ Test real-time features (SSE/WebSocket)
7. ✅ Run automated test suite

## Additional Resources

- **API Documentation**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

