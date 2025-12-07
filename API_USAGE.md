# API Usage Guide

## Common API Errors and Solutions

### 1. "Method Not Allowed" (405 Error)

**Error**: `{"detail": "Method Not Allowed"}`

**Cause**: You're using the wrong HTTP method for an endpoint.

**Solutions**:

- **Registration**: Use `POST` not `GET`
  - ❌ Wrong: `GET https://localhost/api/auth/register`
  - ✅ Correct: `POST https://localhost/api/auth/register`
  
- **Login**: Use `POST` not `GET`
  - ❌ Wrong: `GET https://localhost/api/auth/login`
  - ✅ Correct: `POST https://localhost/api/auth/login`

### 2. How to Test API Endpoints

#### Option 1: Using Swagger UI (Recommended)
1. Open `https://localhost/docs` in your browser
2. Click on any endpoint (e.g., `/api/auth/register`)
3. Click "Try it out"
4. Fill in the request body
5. Click "Execute"

#### Option 2: Using cURL
```bash
# Register a new user
curl -X POST https://localhost/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "testuser",
    "password": "SecurePass123"
  }' \
  -k  # -k ignores SSL certificate warnings for self-signed certs

# Login
curl -X POST https://localhost/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123"
  }' \
  -k
```

#### Option 3: Using PowerShell
```powershell
# Register a new user
$body = @{
    email = "user@example.com"
    username = "testuser"
    password = "SecurePass123"
} | ConvertTo-Json

Invoke-RestMethod -Uri "https://localhost/api/auth/register" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body `
    -SkipCertificateCheck

# Login
$loginBody = @{
    email = "user@example.com"
    password = "SecurePass123"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "https://localhost/api/auth/login" `
    -Method POST `
    -ContentType "application/json" `
    -Body $loginBody `
    -SkipCertificateCheck

$token = $response.access_token
Write-Host "Access Token: $token"
```

### 3. Available Endpoints

#### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login and get tokens
- `POST /api/auth/refresh` - Refresh access token
- `GET /api/auth/me` - Get current user (requires auth)

#### Blogs
- `GET /api/blogs/` - List all approved blogs (public)
- `POST /api/blogs/` - Create blog (requires auth)
- `GET /api/blogs/{id}` - Get single blog (public if approved)
- `PUT /api/blogs/{id}` - Update blog (author or admin)
- `DELETE /api/blogs/{id}` - Delete blog (author or admin)
- `POST /api/blogs/{id}/approve` - Approve blog (admin/L1 approver)
- `POST /api/blogs/{id}/reject` - Reject blog (admin/L1 approver)

#### Real-Time Features
- `GET /api/notifications/sse` - SSE notifications (admin only)
- `WS /api/blogs/{id}/ws` - WebSocket chat for blog comments

#### Feature Requests
- `GET /api/feature-requests/` - List feature requests
- `POST /api/feature-requests/` - Create feature request
- `PATCH /api/feature-requests/{id}` - Update feature request (admin)

#### Session Management
- `GET /api/session/draft` - Get draft blog post
- `POST /api/session/draft` - Save draft blog post

### 4. Authentication

Most endpoints require authentication. Include the JWT token in the Authorization header:

```
Authorization: Bearer <your_access_token>
```

Example with cURL:
```bash
curl -X GET https://localhost/api/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -k
```

### 5. SSL Certificate Warning

When accessing `https://localhost`, your browser will show a security warning because we're using self-signed certificates. This is **normal for local development**.

**To proceed**:
1. Click "Advanced" or "Show Details"
2. Click "Proceed to localhost (unsafe)" or "Accept the Risk"
3. The site will load normally

**Note**: In production, use proper SSL certificates (e.g., Let's Encrypt) to avoid this warning.

