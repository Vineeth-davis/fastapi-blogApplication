# WebSocket Testing Guide

## Overview

The WebSocket endpoint allows real-time chat/comments under each blog post. All connected clients receive broadcasts when a new comment is posted.

**Endpoint:** `ws://localhost/api/blogs/{blog_id}/ws?token={access_token}`

## Prerequisites

1. **Get an Access Token**: First, you need to login and get a JWT access token
2. **Create or Get a Blog ID**: You need a valid blog ID to connect to

## Step 1: Get Access Token

### Using Postman (REST API)

1. **POST** `https://localhost/api/auth/login`
2. **Headers:**
   ```
   Content-Type: application/json
   ```
3. **Body (JSON):**
   ```json
   {
     "email": "user1@example.com",
     "password": "user1@1"
   }
   ```
4. **Response:** You'll get an `access_token` - copy this value

### Alternative: Use Pre-seeded Users

- **Admin:** `admin@example.com` / `admin@1`
- **User:** `user1@example.com` / `user1@1`
- **Approver:** `approver@example.com` / `approver@1`

## Step 2: Get a Blog ID

### Option A: Create a New Blog

1. **POST** `https://localhost/api/blogs/`
2. **Headers:**
   ```
   Authorization: Bearer {your_access_token}
   Content-Type: application/json
   ```
3. **Body (JSON):**
   ```json
   {
     "title": "Test Blog for WebSocket",
     "content": "This is a test blog post for WebSocket testing"
   }
   ```
4. **Response:** Copy the `id` from the response

### Option B: List Existing Blogs

1. **GET** `https://localhost/api/blogs/`
2. Pick any blog `id` from the response

## Step 3: Connect via WebSocket in Postman

### Postman WebSocket Setup

1. **Create New Request** → Select **WebSocket** (not HTTP)
2. **URL:** 
   ```
   ws://localhost/api/blogs/{blog_id}/ws?token={access_token}
   ```
   Replace:
   - `{blog_id}` with your blog ID (e.g., `1`)
   - `{access_token}` with your JWT token

   **Example:**
   ```
   ws://localhost/api/blogs/1/ws?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   ```

3. **Click "Connect"** - You should see "Connected" status

### Note: HTTPS/SSL

If you're using HTTPS (`https://localhost`), use:
```
wss://localhost/api/blogs/{blog_id}/ws?token={access_token}
```

## Step 4: Send Test Messages

### Test Payload 1: Simple Comment

**Send this JSON:**
```json
{
  "type": "comment",
  "content": "This is my first WebSocket comment!"
}
```

**Expected Response:**
```json
{
  "type": "comment",
  "blog_id": 1,
  "comment_id": 123,
  "content": "This is my first WebSocket comment!",
  "user_id": 3,
  "username": "user1",
  "created_at": "2025-12-07T14:20:00.000000Z"
}
```

### Test Payload 2: Another Comment

```json
{
  "type": "comment",
  "content": "Testing real-time broadcasting!"
}
```

### Test Payload 3: Empty Content (Should be Ignored)

```json
{
  "type": "comment",
  "content": ""
}
```
*This should be ignored by the server (no response)*

### Test Payload 4: Invalid Type (Should be Ignored)

```json
{
  "type": "invalid_type",
  "content": "This won't be processed"
}
```
*This should be ignored by the server (no response)*

## Step 5: Test Broadcasting (Multiple Clients)

To test broadcasting, you need **two WebSocket connections**:

### Client 1 (Postman Tab 1)
```
ws://localhost/api/blogs/1/ws?token={token1}
```

### Client 2 (Postman Tab 2 or Another Tool)
```
ws://localhost/api/blogs/1/ws?token={token2}
```

**Test:**
1. Connect both clients to the same blog
2. Send a message from Client 1
3. **Both clients should receive the message** (broadcast)

## Common Issues

### Issue: Connection Refused / 403 Forbidden

**Solution:**
- Check that your token is valid (not expired)
- Ensure the token is in the query parameter: `?token=...`
- Try getting a fresh token by logging in again

### Issue: Blog Not Found

**Solution:**
- Verify the blog ID exists: `GET /api/blogs/{id}`
- Ensure the blog is not deleted

### Issue: Invalid JSON

**Solution:**
- Ensure your message is valid JSON
- Check for trailing commas or syntax errors

### Issue: No Response

**Solution:**
- Empty content messages are ignored
- Invalid message types are ignored
- Only `{"type": "comment", "content": "..."}` messages are processed

## Testing with cURL (Alternative)

If you prefer command-line testing:

```bash
# First, get a token
TOKEN=$(curl -k -X POST https://localhost/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user1@example.com","password":"user1@1"}' \
  | jq -r '.access_token')

# Then connect via WebSocket (requires websocat or similar tool)
echo '{"type":"comment","content":"Test comment"}' | \
  websocat "wss://localhost/api/blogs/1/ws?token=$TOKEN"
```

## Expected Behavior

✅ **Working:**
- Connection with valid token and blog ID
- Sending `{"type": "comment", "content": "..."}` messages
- Receiving broadcast messages
- Comments are saved to database
- Multiple clients receive broadcasts

❌ **Not Working (Expected):**
- Connection without token → Connection closed
- Connection with invalid token → Connection closed
- Connection to non-existent blog → Connection closed
- Empty content messages → Ignored
- Invalid message types → Ignored

## Verification

After sending a comment via WebSocket, verify it was saved:

**GET** `https://localhost/api/blogs/{blog_id}/comments`

You should see your comment in the list!

## Quick Test Checklist

- [ ] Get access token via login
- [ ] Get/create a blog ID
- [ ] Connect via WebSocket with token
- [ ] Send a comment message
- [ ] Receive broadcast response
- [ ] Verify comment in database
- [ ] Test with multiple clients (broadcasting)

