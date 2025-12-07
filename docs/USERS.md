# Pre-seeded Users

The database has been seeded with the following users for testing:

## Admin User
- **Username:** `admin`
- **Email:** `admin@example.com`
- **Password:** `admin@1`
- **Role:** `admin`

## L1 Approver User
- **Username:** `approver`
- **Email:** `approver@example.com`
- **Password:** `approver@1`
- **Role:** `l1_approver`

## Regular Users
- **Username:** `user1` | **Email:** `user1@example.com` | **Password:** `user1@1` | **Role:** `user`
- **Username:** `user2` | **Email:** `user2@example.com` | **Password:** `user2@1` | **Role:** `user`
- **Username:** `user3` | **Email:** `user3@example.com` | **Password:** `user3@1` | **Role:** `user`
- **Username:** `user4` | **Email:** `user4@example.com` | **Password:** `user4@1` | **Role:** `user`
- **Username:** `user5` | **Email:** `user5@example.com` | **Password:** `user5@1` | **Role:** `user`

## Usage

You can use these credentials to:
1. **Login** via `/api/auth/login` endpoint
2. **Test different roles** and their permissions
3. **Test approval workflows** (admin/approver can approve blogs)
4. **Test blog creation** (users can create blogs)

## Re-seeding Users

To re-seed users (if you need to reset the database):

```bash
docker-compose exec api python /app/scripts/seed_users.py
```

**Note:** The script will skip users that already exist, so it's safe to run multiple times.

## Listing Users

To list all users in the database:

```bash
docker-compose exec api python /app/scripts/list_users.py
```

