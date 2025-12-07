# Security Documentation

This document outlines the security measures implemented in the Blog Platform Backend API.

## Table of Contents

1. [HTTPS Enforcement](#https-enforcement)
2. [CORS Configuration](#cors-configuration)
3. [Input Validation](#input-validation)
4. [Secrets Management](#secrets-management)
5. [API Rate Limiting](#api-rate-limiting)
6. [Security Headers](#security-headers)
7. [Password Security](#password-security)
8. [Authentication & Authorization](#authentication--authorization)
9. [Audit Logging](#audit-logging)
10. [Firewalls & Private Networks](#firewalls--private-networks)

---

## HTTPS Enforcement

### Implementation

HTTPS is enforced in production through:

1. **HTTPS Redirect Middleware** (`app/middleware/security.py`)
   - Automatically redirects HTTP requests to HTTPS when:
     - `ENVIRONMENT=production`
     - `SSL_ENABLED=true`
   - Returns HTTP 301 (Permanent Redirect)

2. **HSTS (HTTP Strict Transport Security)**
   - Added via `SecurityHeadersMiddleware`
   - Header: `Strict-Transport-Security: max-age=31536000; includeSubDomains`
   - Only enabled in production with SSL enabled

### Configuration

```env
ENVIRONMENT=production
SSL_ENABLED=true
SSL_CERT_PATH=/path/to/cert.pem
SSL_KEY_PATH=/path/to/key.pem
```

### Deployment

For production deployment with Nginx/Caddy:

- Configure SSL certificates via Let's Encrypt
- Set up reverse proxy to handle SSL termination
- Ensure backend receives HTTPS requests or configure proxy headers

---

## CORS Configuration

### Implementation

CORS is configured via FastAPI's `CORSMiddleware`:

- **Allowed Origins**: Configurable via `CORS_ORIGINS` environment variable
- **Credentials**: Enabled (`CORS_CREDENTIALS=true`)
- **Methods**: All HTTP methods allowed
- **Headers**: All headers allowed

### Configuration

```env
# Comma-separated list of allowed origins
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
CORS_CREDENTIALS=true
FRONTEND_URL=https://yourdomain.com
```

### Security Considerations

- **Restrict Origins**: Only include your frontend domain(s)
- **No Wildcards**: Avoid using `*` in production
- **Credentials**: Only enable if you need to send cookies/credentials

---

## Input Validation

### Implementation

All API endpoints use **Pydantic models** for request validation:

1. **Type Validation**: Automatic type checking
2. **Length Validation**: Min/max length constraints
3. **Format Validation**: Email, URL, date formats
4. **Custom Validators**: Business logic validation

### Examples

```python
# Email validation
class UserRegister(BaseModel):
    email: EmailStr  # Validates email format
    password: str = Field(..., min_length=8)  # Minimum 8 characters
```

### SQL Injection Prevention

- **SQLAlchemy ORM**: All queries use parameterized statements
- **No Raw SQL**: Avoid raw SQL queries with string concatenation
- **Type Safety**: SQLAlchemy enforces type safety

### XSS Prevention

- **Content Sanitization**: User-generated content should be sanitized before rendering
- **CSP Headers**: Content Security Policy restricts inline scripts/styles
- **Input Encoding**: FastAPI automatically handles encoding

---

## Secrets Management

### Implementation

All secrets are managed via environment variables:

1. **Environment Variables**: Loaded from `.env` file (development)
2. **Pydantic Settings**: Centralized configuration via `app/config.py`
3. **Never Hardcoded**: No secrets in source code

### Configuration

Create a `.env` file (never commit it):

```env
# JWT Secret Key (generate with: openssl rand -hex 32)
SECRET_KEY=your-secret-key-here

# Database URL
DATABASE_URL=postgresql+asyncpg://user:password@localhost/dbname

# Other secrets...
```

### Best Practices

1. **Generate Strong Keys**: Use `openssl rand -hex 32` for SECRET_KEY
2. **Rotate Secrets**: Regularly rotate secrets, especially after security incidents
3. **Separate Environments**: Use different secrets for dev/staging/production
4. **Docker Secrets**: Use Docker secrets for containerized deployments
5. **CI/CD Secrets**: Store secrets in CI/CD platform's secret management

### Gitignore

The `.gitignore` file includes:

```
.env
.env.local
*.pem
*.key
```

---

## API Rate Limiting

### Implementation

Rate limiting is implemented using `slowapi`:

1. **Global Rate Limiting**: Applied to all endpoints
2. **IP-Based**: Limits by client IP address
3. **Configurable**: Can be enabled/disabled and adjusted

### Configuration

```env
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60
```

### Behavior

- **Default Limit**: 60 requests per minute per IP
- **Response**: HTTP 429 (Too Many Requests) when exceeded
- **Retry-After Header**: Included in 429 responses

### Customization

To add per-endpoint rate limits, use the `@limiter.limit()` decorator:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/api/auth/login")
@limiter.limit("10/minute")  # Stricter limit for login
async def login(...):
    ...
```

---

## Security Headers

### Implementation

Security headers are added via `SecurityHeadersMiddleware`:

1. **X-Content-Type-Options**: `nosniff` - Prevents MIME type sniffing
2. **X-Frame-Options**: `DENY` - Prevents clickjacking
3. **X-XSS-Protection**: `1; mode=block` - XSS protection
4. **Content-Security-Policy**: Restricts resource loading
5. **Referrer-Policy**: `strict-origin-when-cross-origin`
6. **Strict-Transport-Security**: HSTS (production only)

### Content Security Policy

Current CSP (adjustable in `app/middleware/security.py`):

```
default-src 'self';
script-src 'self' 'unsafe-inline' 'unsafe-eval';  # For Swagger UI
style-src 'self' 'unsafe-inline';  # For Swagger UI
img-src 'self' data: https:;
font-src 'self' data:;
connect-src 'self';
frame-ancestors 'none';
```

**Note**: The CSP includes `unsafe-inline` and `unsafe-eval` for Swagger UI compatibility. For production APIs without Swagger UI, these can be removed.

---

## Password Security

### Implementation

1. **Hashing Algorithm**: bcrypt (via `passlib[bcrypt]`)
2. **Salt**: Automatically generated by bcrypt
3. **Rounds**: Default bcrypt rounds (12)
4. **Never Stored**: Passwords are never stored in plain text

### Password Requirements

Enforced via Pydantic validators:

- Minimum 8 characters
- Can be extended with additional requirements (uppercase, numbers, special chars)

### Example

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Hash password
hashed = pwd_context.hash("user_password")

# Verify password
is_valid = pwd_context.verify("user_password", hashed)
```

---

## Authentication & Authorization

### JWT Authentication

1. **Access Tokens**: Short-lived (15 minutes default)
2. **Refresh Tokens**: Longer-lived (7 days default)
3. **Algorithm**: HS256 (HMAC-SHA256)
4. **Secret Key**: Stored in `SECRET_KEY` environment variable

### Token Structure

```json
{
  "sub": "user_id",
  "exp": 1234567890,
  "iat": 1234567890
}
```

### Role-Based Access Control (RBAC)

Three roles implemented:

1. **user**: Regular user (default)
2. **admin**: Administrator (full access)
3. **L1_APPROVER**: Level 1 approver (can approve/reject blogs)

### Authorization Checks

- **Dependencies**: FastAPI dependencies enforce role requirements
- **Middleware**: Audit middleware logs role-based actions
- **Endpoints**: Protected endpoints require authentication

### Example

```python
from app.auth.rbac import require_admin

@router.post("/api/blogs/{id}/approve")
async def approve_blog(
    blog_id: int,
    current_user: User = Depends(require_admin),
    ...
):
    ...
```

---

## Audit Logging

### Implementation

Audit logging is implemented via `AuditMiddleware`:

1. **Role-Based Actions**: Logs all actions requiring specific roles
2. **Request Logging**: Logs important requests (POST, PUT, DELETE, PATCH)
3. **Structured Logging**: JSON format for easy parsing
4. **User Tracking**: Associates actions with user IDs

### Logged Actions

- User registration
- Role changes
- Blog approval/rejection
- Blog creation/update/deletion
- Feature request status updates

### Log Format

```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "level": "INFO",
  "message": "Role-based action",
  "user_id": 123,
  "action": "approve_blog",
  "resource": "/api/blogs/456/approve",
  "method": "POST"
}
```

---

## Firewalls & Private Networks

### Documentation

For production deployments, document:

1. **Firewall Rules**:
   - Inbound ports: 80 (HTTP), 443 (HTTPS)
   - Outbound ports: Database, external APIs
   - SSH access: Restricted to specific IPs

2. **Private Networks**:
   - Database: Should be in private network/VPC
   - Application servers: Can be in private network with load balancer
   - Redis (if used): Private network only

3. **Network Segmentation**:
   - Separate networks for different tiers (web, app, db)
   - VPN access for administrative tasks
   - Bastion hosts for secure access

### Example Configuration

**Nginx/Caddy (Public Network)**:
- Ports: 80, 443
- SSL termination
- Reverse proxy to application

**Application Server (Private Network)**:
- Port: 8000 (internal)
- No direct internet access
- Accessible only via reverse proxy

**Database (Private Network)**:
- No internet access
- Accessible only from application servers
- Firewall rules restrict access by IP

### Security Groups (Cloud Providers)

Example AWS Security Group rules:

```
Inbound:
- Port 443 (HTTPS): 0.0.0.0/0
- Port 80 (HTTP): 0.0.0.0/0 (redirects to 443)
- Port 22 (SSH): Your IP only

Outbound:
- Port 5432 (PostgreSQL): Database security group only
- Port 443 (HTTPS): 0.0.0.0/0 (for external APIs)
```

---

## Security Checklist

Before deploying to production:

- [ ] Strong `SECRET_KEY` generated and set
- [ ] `.env` file not committed to Git
- [ ] HTTPS enabled and SSL certificates configured
- [ ] CORS origins restricted to frontend domain(s)
- [ ] Rate limiting enabled and configured
- [ ] Security headers enabled
- [ ] Database credentials secure
- [ ] Firewall rules configured
- [ ] Private networks configured (if applicable)
- [ ] Audit logging enabled
- [ ] Dependencies up to date
- [ ] Regular security updates scheduled
- [ ] Backup and disaster recovery plan in place

---

## Reporting Security Issues

If you discover a security vulnerability, please:

1. **Do not** open a public issue
2. Email security concerns to: [your-security-email]
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

We will respond within 48 hours and work to resolve the issue promptly.

---

## References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [Python Security Best Practices](https://python.readthedocs.io/en/latest/library/security.html)

