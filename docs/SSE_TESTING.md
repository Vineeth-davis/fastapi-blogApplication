# Server-Sent Events (SSE) Testing Guide

## Overview

Server-Sent Events (SSE) provide a one-way real-time communication channel from server to client. In this application, **admins** receive real-time notifications when new blog posts are submitted with `pending` status.

**Endpoint:** `GET /api/notifications/sse`

## How SSE Works

### Architecture

1. **Admin connects** to `/api/notifications/sse` endpoint
2. **Connection stays open** - Server keeps the connection alive
3. **When a new blog is created** with status `pending`, the server:
   - Detects the new pending blog
   - Broadcasts a notification to all connected admin clients
   - Each admin receives the notification in real-time

### Flow Diagram

```
User creates blog → Blog saved with status="pending" 
                 → notifications_manager.notify_new_pending_blog()
                 → All connected admin SSE clients receive notification
```

### Key Components

- **`NotificationsManager`**: In-memory manager that tracks SSE connections
- **`/api/notifications/sse`**: SSE endpoint (admin-only)
- **Blog creation**: Automatically triggers notification when status is `pending`

## Prerequisites

1. **Admin Access Token (REQUIRED)**: You **MUST** use an admin user's JWT token. 
   - ✅ **Admin users** can access SSE endpoint
   - ❌ **Regular users** will get `403 Forbidden`
   - ❌ **L1 Approvers** will get `403 Forbidden` (only admins receive notifications)
2. **Two terminals/tabs**: One for SSE connection, one for creating blogs

## Step 1: Get Admin Access Token

### Using Postman or cURL

**POST** `https://localhost/api/auth/login`

**Body (JSON):**
```json
{
  "email": "admin@example.com",
  "password": "admin@1"
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

**Copy the `access_token`** - you'll need it for the SSE connection.

## Step 2: Connect to SSE Stream

### Option A: Using cURL (Command Line)

```bash
curl -N -H "Authorization: Bearer {your_access_token}" \
  https://localhost/api/notifications/sse
```

**What you'll see:**
```
data: {"type":"connected"}

: heartbeat

: heartbeat
...
```

The connection stays open, waiting for notifications.

### Option B: Using Postman

1. **Create New Request** → Select **GET**
2. **URL:** `https://localhost/api/notifications/sse`
3. **Headers:**
   ```
   Authorization: Bearer {your_access_token}
   ```
4. **Click "Send"** - The connection will stay open and stream events

**Note:** Postman will show the stream in real-time. You'll see:
- Initial connection message: `{"type":"connected"}`
- Heartbeat messages every 30 seconds: `: heartbeat`
- Notifications when blogs are created

### Option C: Using JavaScript (Browser)

```javascript
const token = "your_access_token_here";

const eventSource = new EventSource(
  `https://localhost/api/notifications/sse`,
  {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  }
);

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received notification:', data);
  
  if (data.type === 'new_pending_blog') {
    console.log(`New blog pending: ${data.title} (ID: ${data.blog_id})`);
    // Update UI, show notification, etc.
  }
};

eventSource.onerror = (error) => {
  console.error('SSE error:', error);
  eventSource.close();
};
```

**Note:** Browser's `EventSource` API doesn't support custom headers directly. You may need to:
- Use a proxy
- Pass token as query parameter (less secure)
- Use a library like `eventsource` for Node.js

## Step 3: Create a Blog to Trigger Notification

### In a separate terminal/tab:

**POST** `https://localhost/api/blogs/`

**Headers:**
```
Authorization: Bearer {any_user_token}
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "title": "New Blog Post for Testing",
  "content": "This blog post should trigger an SSE notification to admins."
}
```

**What happens:**
1. Blog is created with status `pending`
2. Notification is sent to all connected admin SSE clients
3. SSE clients receive:
   ```json
   {
     "type": "new_pending_blog",
     "blog_id": 123,
     "title": "New Blog Post for Testing",
     "author_id": 3
   }
   ```

## Expected SSE Message Format

### Connection Message (on connect)
```json
{
  "type": "connected"
}
```

### Notification Message (when blog created)
```json
{
  "type": "new_pending_blog",
  "blog_id": 123,
  "title": "New Blog Post Title",
  "author_id": 3
}
```

### Heartbeat (every 30 seconds)
```
: heartbeat
```
*This is a comment line to keep the connection alive*

## Testing Scenarios

### Scenario 1: Single Admin Connection

1. Connect admin to SSE stream
2. Create a blog as a regular user
3. **Expected:** Admin receives notification immediately

### Scenario 2: Multiple Admin Connections

1. Connect **two admin clients** to SSE stream (two terminals/tabs)
2. Create a blog as a regular user
3. **Expected:** Both admin clients receive the notification (broadcast)

### Scenario 3: Non-Admin Access (Should Fail)

1. Try to connect with a regular user token
2. **Expected:** `403 Forbidden` - Only admins can access SSE

### Scenario 4: Unauthorized Access (Should Fail)

1. Try to connect without a token
2. **Expected:** `401 Unauthorized`

### Scenario 5: Approved Blog (No Notification)

1. Connect admin to SSE stream
2. Create a blog and immediately approve it (status = `approved`)
3. **Expected:** No notification (only `pending` blogs trigger notifications)

## Testing with cURL (Complete Example)

```bash
# Terminal 1: Connect to SSE stream
curl -N -H "Authorization: Bearer {admin_token}" \
  https://localhost/api/notifications/sse

# Terminal 2: Create a blog to trigger notification
curl -X POST https://localhost/api/blogs/ \
  -H "Authorization: Bearer {user_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Blog",
    "content": "This should trigger SSE notification"
  }'

# Terminal 1 should now show:
# data: {"type":"new_pending_blog","blog_id":123,"title":"Test Blog","author_id":3}
```

## Testing with Postman

### Setup

1. **Collection 1: SSE Connection**
   - **GET** `/api/notifications/sse`
   - **Headers:** `Authorization: Bearer {admin_token}`
   - Keep this request open (it will stream)

2. **Collection 2: Create Blog**
   - **POST** `/api/blogs/`
   - **Headers:** `Authorization: Bearer {user_token}`
   - **Body:** `{"title": "Test", "content": "Test content"}`

### Test Flow

1. Open SSE request and send (keep it open)
2. Create a blog using the second request
3. Watch the SSE request - you should see the notification appear

## Common Issues

### Issue: No Notifications Received

**Possible Causes:**
- Blog was created with status other than `pending` (should be automatic)
- Admin token expired (get a fresh token)
- Connection dropped (reconnect)
- No admins connected when blog was created

**Solution:**
- Ensure SSE connection is active before creating blog
- Verify blog status is `pending` after creation
- Check admin token is valid

### Issue: Connection Closes Immediately

**Possible Causes:**
- Invalid or expired token
- User is not an admin
- Network/proxy issues

**Solution:**
- Get a fresh admin token
- Verify user role is `admin`
- Check network connectivity

### Issue: Heartbeat but No Notifications

**Possible Causes:**
- No blogs are being created
- Blogs are being created with `approved` status
- Notification trigger not working

**Solution:**
- Create a blog and verify it has `status: "pending"`
- Check server logs for errors
- Verify `notifications_manager.notify_new_pending_blog()` is called

## Verification

After receiving a notification, verify the blog exists:

**GET** `https://localhost/api/blogs/{blog_id}`

You should see the blog with `status: "pending"`.

## Quick Test Checklist

- [ ] Get admin access token
- [ ] Connect to SSE stream (`/api/notifications/sse`)
- [ ] Verify connection message received
- [ ] Create a blog as regular user
- [ ] Verify notification received in SSE stream
- [ ] Check notification contains correct blog_id and title
- [ ] Test with multiple admin connections (broadcasting)
- [ ] Test non-admin access (should fail with 403)
- [ ] Test unauthorized access (should fail with 401)

## Advanced: Testing with Python

```python
import requests
import json
import time

# Get admin token
login_response = requests.post(
    "https://localhost/api/auth/login",
    json={"email": "admin@example.com", "password": "admin@1"},
    verify=False
)
token = login_response.json()["access_token"]

# Connect to SSE stream
headers = {"Authorization": f"Bearer {token}"}
response = requests.get(
    "https://localhost/api/notifications/sse",
    headers=headers,
    stream=True,
    verify=False
)

print("Connected to SSE stream. Waiting for notifications...")
print("-" * 50)

for line in response.iter_lines():
    if line:
        line_str = line.decode('utf-8')
        if line_str.startswith('data: '):
            data = json.loads(line_str[6:])  # Remove "data: " prefix
            print(f"Received: {json.dumps(data, indent=2)}")
        elif line_str.startswith(':'):
            print("Heartbeat received")
```

## Summary

✅ **SSE Notifications Work When:**
- Admin connects to `/api/notifications/sse`
- A blog is created with status `pending`
- Notification is broadcast to all connected admins

❌ **SSE Notifications Don't Work When:**
- User is not an admin (403 Forbidden)
- No authentication token (401 Unauthorized)
- Blog is created with status other than `pending`
- No admins are connected when blog is created

