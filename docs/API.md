# API Documentation

This document provides detailed information about all API endpoints in the Blog Platform Backend.

## Base URL

- **Development**: `http://localhost:8000`
- **Production**: `https://yourdomain.com`

## Authentication

Most endpoints require authentication using JWT (JSON Web Tokens). Include the access token in the Authorization header:

```
Authorization: Bearer <access_token>
```

### Token Types

- **Access Token**: Short-lived (15 minutes), used for API requests
- **Refresh Token**: Long-lived (7 days), used to obtain new access tokens

---

## Endpoints

### Authentication

#### Register User

```http
POST /api/auth/register
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "username": "username",
  "password": "password123"
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "username",
  "role": "user",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z"
}
```

#### Login

```http
POST /api/auth/login
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### Refresh Token

```http
POST /api/auth/refresh
```

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### Get Current User

```http
GET /api/auth/me
```

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`
```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "username",
  "role": "user",
  "is_active": true
}
```

---

### Blogs

#### List Blogs (Public)

```http
GET /api/blogs/?skip=0&limit=10
```

**Query Parameters:**
- `skip` (optional): Number of records to skip (default: 0)
- `limit` (optional): Maximum number of records to return (default: 10)

**Response:** `200 OK`
```json
{
  "items": [
    {
      "id": 1,
      "title": "Blog Post Title",
      "content": "Blog content...",
      "status": "approved",
      "author_id": 1,
      "images": ["https://example.com/image.jpg"],
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 100,
  "skip": 0,
  "limit": 10
}
```

**Note:** Only approved blogs are visible to public.

#### Get Blog by ID

```http
GET /api/blogs/{id}
```

**Response:** `200 OK`
```json
{
  "id": 1,
  "title": "Blog Post Title",
  "content": "Blog content...",
  "status": "approved",
  "author_id": 1,
  "author": {
    "id": 1,
    "username": "author"
  },
  "images": ["https://example.com/image.jpg"],
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

**Visibility Rules:**
- Public: Can see approved blogs only
- Author: Can see own blogs (any status)
- Admin: Can see all blogs

#### Create Blog

```http
POST /api/blogs/
```

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "title": "My Blog Post",
  "content": "Blog content in markdown or HTML...",
  "images": ["https://example.com/image.jpg"]
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "title": "My Blog Post",
  "content": "Blog content...",
  "status": "pending",
  "author_id": 1,
  "created_at": "2024-01-01T00:00:00Z"
}
```

**Note:** New blogs are created with `status: "pending"` and require approval.

#### Update Blog

```http
PUT /api/blogs/{id}
```

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "title": "Updated Title",
  "content": "Updated content...",
  "images": ["https://example.com/new-image.jpg"]
}
```

**Authorization:**
- Author can update own blog (if status != "approved")
- Admin can update any blog

**Response:** `200 OK`

#### Delete Blog

```http
DELETE /api/blogs/{id}
```

**Headers:** `Authorization: Bearer <token>`

**Authorization:**
- Author can delete own blog
- Admin can delete any blog

**Response:** `200 OK`
```json
{
  "message": "Blog deleted successfully"
}
```

**Note:** Soft delete - blog is marked as deleted but not removed from database.

#### Approve Blog

```http
POST /api/blogs/{id}/approve
```

**Headers:** `Authorization: Bearer <token>` (Admin or L1 Approver)

**Response:** `200 OK`
```json
{
  "id": 1,
  "title": "Blog Post",
  "status": "approved",
  ...
}
```

#### Reject Blog

```http
POST /api/blogs/{id}/reject
```

**Headers:** `Authorization: Bearer <token>` (Admin or L1 Approver)

**Response:** `200 OK`
```json
{
  "id": 1,
  "title": "Blog Post",
  "status": "rejected",
  ...
}
```

---

### Real-Time Features

#### Server-Sent Events (SSE) - Admin Notifications

```http
GET /api/notifications/sse
```

**Headers:** `Authorization: Bearer <token>` (Admin only)

**Response:** `200 OK` (Event Stream)
```
data: {"type": "new_pending_blog", "blog_id": 123, "title": "New Blog", "author_id": 1}

data: {"type": "new_pending_blog", "blog_id": 124, "title": "Another Blog", "author_id": 2}
```

**Event Format:**
```json
{
  "type": "new_pending_blog",
  "blog_id": 123,
  "title": "Blog Title",
  "author_id": 1
}
```

**Note:** Connection remains open and receives events in real-time when new blogs are pending approval.

#### WebSocket - Blog Comments

```http
WS /api/blogs/{blog_id}/ws?token=<access_token>
```

**Connection:**
- Requires valid JWT access token as query parameter
- Only authenticated users can connect
- Blog must exist and not be deleted

**Send Message:**
```json
{
  "type": "comment",
  "content": "This is a comment"
}
```

**Receive Message:**
```json
{
  "type": "comment",
  "blog_id": 1,
  "comment_id": 5,
  "content": "This is a comment",
  "user_id": 2,
  "username": "commenter",
  "created_at": "2024-01-01T00:00:00Z"
}
```

**Note:** Comments are broadcast to all connected clients for the blog and persisted to the database.

---

### Feature Requests

#### List Feature Requests

```http
GET /api/feature-requests/?skip=0&limit=10
```

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `skip` (optional): Number of records to skip
- `limit` (optional): Maximum number of records
- `status` (optional): Filter by status (pending, accepted, declined)

**Response:** `200 OK`
```json
{
  "items": [
    {
      "id": 1,
      "title": "Feature Request",
      "description": "Description...",
      "status": "pending",
      "user_id": 1,
      "priority": 3,
      "rating": 5,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 50,
  "skip": 0,
  "limit": 10
}
```

**Visibility:**
- Users see only their own feature requests
- Admins see all feature requests

#### Create Feature Request

```http
POST /api/feature-requests/
```

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "title": "New Feature",
  "description": "Feature description...",
  "priority": 3
}
```

**Response:** `201 Created`

#### Update Feature Request Status

```http
PATCH /api/feature-requests/{id}
```

**Headers:** `Authorization: Bearer <token>` (Admin only)

**Request Body:**
```json
{
  "status": "accepted",
  "priority": 5
}
```

**Response:** `200 OK`

---

### Session Management

#### Get Draft

```http
GET /api/session/draft
```

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`
```json
{
  "user_id": 1,
  "draft_data": {
    "title": "Draft Title",
    "content": "Draft content...",
    "images": []
  },
  "expires_at": "2024-02-01T00:00:00Z",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

**Response:** `404 Not Found` (if no draft exists)

#### Save Draft

```http
POST /api/session/draft
```

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "draft_data": {
    "title": "Draft Title",
    "content": "Draft content...",
    "images": ["https://example.com/image.jpg"]
  }
}
```

**Response:** `200 OK`
```json
{
  "user_id": 1,
  "draft_data": {...},
  "expires_at": "2024-02-01T00:00:00Z",
  ...
}
```

**Note:** Drafts expire after 30 days.

---

### Role Management (Admin Only)

#### List Users

```http
GET /api/roles/users
```

**Headers:** `Authorization: Bearer <token>` (Admin only)

**Response:** `200 OK`
```json
{
  "items": [
    {
      "id": 1,
      "email": "user@example.com",
      "username": "user",
      "role": "user",
      "is_active": true
    }
  ],
  "total": 100
}
```

#### Update User Role

```http
PUT /api/roles/users/{user_id}
```

**Headers:** `Authorization: Bearer <token>` (Admin only)

**Request Body:**
```json
{
  "role": "admin"
}
```

**Response:** `200 OK`

**Note:** Admins cannot demote themselves.

---

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Validation error message"
}
```

### 401 Unauthorized
```json
{
  "detail": "Not authenticated"
}
```

### 403 Forbidden
```json
{
  "detail": "Not enough permissions"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 429 Too Many Requests
```json
{
  "detail": "Rate limit exceeded: 60/minute. Please try again later."
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

---

## Rate Limiting

- **Default Limit**: 60 requests per minute per IP address
- **Response**: HTTP 429 when limit exceeded
- **Headers**: `Retry-After` indicates when to retry

---

## WebSocket Status Codes

- **1000**: Normal closure
- **1008**: Policy violation (authentication failed, invalid blog, etc.)

---

## Interactive API Documentation

FastAPI automatically generates interactive API documentation:

- **Swagger UI**: `/docs`
- **ReDoc**: `/redoc`
- **OpenAPI JSON**: `/openapi.json`

These endpoints provide:
- Complete endpoint documentation
- Request/response schemas
- Try-it-out functionality
- Authentication testing

---

## Real-Time Features Explanation

### Server-Sent Events (SSE)

SSE is used for one-way server-to-client communication. In this API:

- **Endpoint**: `/api/notifications/sse`
- **Access**: Admin only
- **Purpose**: Real-time notifications when new blogs are pending approval
- **Connection**: Long-lived HTTP connection
- **Format**: Server-sent events with JSON payloads

**Client Example (JavaScript):**
```javascript
const eventSource = new EventSource('/api/notifications/sse', {
  headers: {
    'Authorization': 'Bearer ' + token
  }
});

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('New pending blog:', data);
};
```

### WebSockets

WebSockets provide bidirectional communication. In this API:

- **Endpoint**: `/api/blogs/{blog_id}/ws`
- **Access**: Authenticated users
- **Purpose**: Real-time chat/comments under blog posts
- **Connection**: Full-duplex WebSocket connection
- **Format**: JSON messages

**Client Example (JavaScript):**
```javascript
const ws = new WebSocket(`/api/blogs/${blogId}/ws?token=${token}`);

ws.onopen = () => {
  ws.send(JSON.stringify({
    type: 'comment',
    content: 'Hello, world!'
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('New comment:', data);
};
```

---

## Pagination

List endpoints support pagination using `skip` and `limit` query parameters:

- `skip`: Number of records to skip (default: 0)
- `limit`: Maximum number of records to return (default: 10, max: 100)

**Example:**
```
GET /api/blogs/?skip=20&limit=10
```

Returns records 21-30.

---

## Status Codes

- **200 OK**: Successful request
- **201 Created**: Resource created successfully
- **400 Bad Request**: Invalid request data
- **401 Unauthorized**: Authentication required
- **403 Forbidden**: Insufficient permissions
- **404 Not Found**: Resource not found
- **429 Too Many Requests**: Rate limit exceeded
- **500 Internal Server Error**: Server error

---

## Best Practices

1. **Always use HTTPS** in production
2. **Store tokens securely** (httpOnly cookies or secure storage)
3. **Refresh tokens** before they expire
4. **Handle errors gracefully** with appropriate user feedback
5. **Implement retry logic** for rate-limited requests
6. **Close WebSocket connections** when done
7. **Reconnect SSE** if connection drops

