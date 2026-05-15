# API Testing Guide - JSON Request Bodies

## 1. REGISTER - Create a new user account
**Endpoint:** `POST /api/auth/register`
**Headers:** `Content-Type: application/json`

### Example JSON:
```json
{
  "full_name": "John Doe",
  "email": "johnd@example.com",
  "password": "securePassword123",
  "confirm_password": "securePassword123",
  "role": "rider"
}
```

**Alternative (using first_name and last_name):**
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "email": "john@example.com",
  "password": "securePassword123",
  "confirm_password": "securePassword123",
  "role": "rider"
}
```

**Response (Example):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "full_name": "John Doe",
  "email": "john@example.com",
  "role": "rider",
  "created_at": "2026-05-08T12:00:00Z",
  "updated_at": "2026-05-08T12:00:00Z"
}
```

---

## 2. LOGIN - Get access and refresh tokens
**Endpoint:** `POST /api/auth/login`
**Headers:** `Content-Type: application/json`

### Example JSON:
```json
{
  "email": "john@example.com",
  "password": "securePassword123"
}
```

**Response (Example):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**⚠️ Important:** Save the `access_token` - you'll need it for all subsequent requests.

---

## 3. CREATE RIDE - Request a ride before matching
**Endpoint:** `POST /api/rides/create`
**Headers:**
- `Content-Type: application/json`
- `Authorization: Bearer {access_token}`

### Example JSON:
```json
{
  "origin": "123 Main Street, Downtown",
  "destination": "456 Park Avenue, Uptown"
}
```

**Response (Example):**
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440111",
  "rider_id": "550e8400-e29b-41d4-a716-446655440000",
  "driver_id": null,
  "status": "requested",
  "origin": "123 Main Street, Downtown",
  "destination": "456 Park Avenue, Uptown",
  "fare": null,
  "created_at": "2026-05-08T12:05:00Z",
  "updated_at": "2026-05-08T12:05:00Z"
}
```

**Save the `id` from the response - you'll need it for matching!**

---

## 4. MATCHING - Find and assign a driver
**Endpoint:** `POST /api/matching/find`
**Headers:**
- `Content-Type: application/json`
- `Authorization: Bearer {access_token}`

### Example JSON:
```json
{
  "ride_id": "660e8400-e29b-41d4-a716-446655440111"
}
```

**Response (Example - if successful):**
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440111",
  "rider_id": "550e8400-e29b-41d4-a716-446655440000",
  "driver_id": "770e8400-e29b-41d4-a716-446655440222",
  "status": "accepted",
  "origin": "123 Main Street, Downtown",
  "destination": "456 Park Avenue, Uptown",
  "fare": null,
  "created_at": "2026-05-08T12:05:00Z",
  "updated_at": "2026-05-08T12:05:30Z"
}
```

---

## Testing Steps in Order

1. **Register a rider account** (POST /api/auth/register)
2. **Register a driver account** (POST /api/auth/register with `"role": "driver"`)
3. **Login as rider** (POST /api/auth/login) → Save access_token
4. **Create a ride** (POST /api/rides/create) → Save ride_id
5. **Match for a driver** (POST /api/matching/find) → Use ride_id

---

## Why "Unauthorized Access" Error?

The matching API requires authentication. Make sure:

✅ You've logged in and have an `access_token`
✅ Your Authorization header is formatted correctly:
   ```
   Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   ```
✅ The token is still valid (tokens expire after 60 minutes by default)

---

## Postman/Curl Examples

### Register (curl):
```bash
curl -X POST http://127.0.0.1:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "John Doe",
    "email": "john@example.com",
    "password": "securePassword123",
    "confirm_password": "securePassword123",
    "role": "rider"
  }'
```

### Login (curl):
```bash
curl -X POST http://127.0.0.1:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "securePassword123"
  }'
```

### Create Ride (curl):
```bash
curl -X POST http://127.0.0.1:8000/api/rides/create \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE" \
  -d '{
    "origin": "123 Main Street, Downtown",
    "destination": "456 Park Avenue, Uptown"
  }'
```

### Matching (curl):
```bash
curl -X POST http://127.0.0.1:8000/api/matching/find \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE" \
  -d '{
    "ride_id": "RIDE_ID_FROM_CREATE_RESPONSE"
  }'
```
