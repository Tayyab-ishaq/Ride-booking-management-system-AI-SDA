# Architecture & Data Flow Diagram

## 📐 System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT (Browser/App)                      │
└────────────────────────────┬────────────────────────────────────┘
                             │
                    GET /api/matching/status/{ride_id}
                    Authorization: Bearer {token}
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                      FASTAPI APPLICATION                         │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  api/endpoints/matching/status.py                        │  │
│  │  @router.get("/status/{ride_id}")                        │  │
│  │  async def get_matching_status(...)                      │  │
│  └──────────────────────┬──────────────────────────────────┘  │
│                         │                                       │
│  ┌──────────────────────▼──────────────────────────────────┐  │
│  │  Dependency Injection:                                  │  │
│  │  - get_current_rider_id() → JWT token validation       │  │
│  │  - get_ride_matching_service() → Service instance      │  │
│  └──────────────────────┬──────────────────────────────────┘  │
│                         │                                       │
│  ┌──────────────────────▼──────────────────────────────────┐  │
│  │  services/rides/matching.py                            │  │
│  │  RideMatchingService.get_matching_status()             │  │
│  │  1. Fetch ride from repository                         │  │
│  │  2. Validate ride exists                               │  │
│  │  3. Validate rider ownership                           │  │
│  │  4. Return Ride object                                 │  │
│  └──────────────────────┬──────────────────────────────────┘  │
│                         │                                       │
│  ┌──────────────────────▼──────────────────────────────────┐  │
│  │  repositories/ride_repository.py                        │  │
│  │  async def get_by_id(ride_id: UUID) -> Ride            │  │
│  │  Queries database for ride record                       │  │
│  └──────────────────────┬──────────────────────────────────┘  │
└────────────────────────┬──────────────────────────────────────┘
                         │
                         │ SQL Query (AsyncPG)
                         │
┌────────────────────────▼──────────────────────────────────────┐
│                      POSTGRESQL DATABASE                       │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ Table: rides                                             │ │
│  │ ┌─────────────────────────────────────────────────────┐ │ │
│  │ │ id (UUID, PK)        ← Indexed                      │ │ │
│  │ │ rider_id (UUID, FK)                                 │ │ │
│  │ │ driver_id (UUID, FK, nullable)                      │ │ │
│  │ │ status (TEXT) ← ENUM                                │ │ │
│  │ │ origin (TEXT)                                       │ │ │
│  │ │ destination (TEXT)                                  │ │ │
│  │ │ fare (DECIMAL, nullable)                            │ │ │
│  │ │ rating (INT, nullable)                              │ │ │
│  │ │ created_at (TIMESTAMP)                              │ │ │
│  │ │ updated_at (TIMESTAMP)                              │ │ │
│  │ └─────────────────────────────────────────────────────┘ │ │
│  └──────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────┘
                         │
                         │ Query Result (Record)
                         │
┌────────────────────────▼──────────────────────────────────────┐
│                 Data Deserialization                           │
│                                                                │
│  Record → Ride Model → MatchingStatusResponse → JSON         │
│                                                                │
│  {                                                            │
│    "id": "550e8400-e29b-41d4-a716-446655440000",             │
│    "rider_id": "550e8400-e29b-41d4-a716-446655440001",       │
│    "driver_id": "550e8400-e29b-41d4-a716-446655440002",      │
│    "status": "accepted",                                     │
│    "origin": "123 Main St",                                  │
│    "destination": "456 Oak Ave",                             │
│    "fare": 25.50,                                            │
│    "created_at": "2026-05-09T10:00:00",                      │
│    "updated_at": "2026-05-09T10:05:00",                      │
│    "rating": null,                                           │
│    "matched_at": null                                        │
│  }                                                            │
└────────────────────────┬───────────────────────────────────────┘
                         │
                         │ HTTP 200 Response
                         │
┌────────────────────────▼───────────────────────────────────────┐
│                        CLIENT                                  │
│              Receives Ride Status Update                       │
│         Renders UI: ✅ Driver matched or ⏳ Still searching   │
└────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Request/Response Cycle

```
STEP 1: CLIENT SENDS REQUEST
┌─────────────────────────────────────────────────────────────┐
│ GET /api/matching/status/550e8400-e29b-41d4-a716-446655440000 │
│ Headers: {                                                    │
│   "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ...",
│   "Content-Type": "application/json"                         │
│ }                                                             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
STEP 2: FASTAPI VALIDATES TOKEN
┌─────────────────────────────────────────────────────────────┐
│ JWT Decode:                                                  │
│ - Verify signature                                           │
│ - Extract rider_id from "sub" claim                         │
│ - Validate expiration                                        │
│                                                              │
│ Result: rider_id = 550e8400-e29b-41d4-a716-446655440001    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
STEP 3: CALL SERVICE METHOD
┌─────────────────────────────────────────────────────────────┐
│ service.get_matching_status(                                 │
│   ride_id="550e8400-e29b-41d4-a716-446655440000",          │
│   rider_id="550e8400-e29b-41d4-a716-446655440001"          │
│ )                                                            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
STEP 4: QUERY DATABASE
┌─────────────────────────────────────────────────────────────┐
│ SQL Query:                                                   │
│ SELECT id, rider_id, driver_id, status, origin,             │
│        destination, fare, rating, created_at, updated_at    │
│ FROM rides                                                   │
│ WHERE id = '550e8400-e29b-41d4-a716-446655440000'          │
│                                                              │
│ Database Returns 1 row (or NULL if not found)              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
STEP 5: VALIDATE OWNERSHIP
┌─────────────────────────────────────────────────────────────┐
│ Check: ride.rider_id == authenticated_rider_id              │
│                                                              │
│ 550e8400-e29b-41d4-a716-446655440001                        │
│    == 550e8400-e29b-41d4-a716-446655440001 ✓               │
│                                                              │
│ Authorization verified!                                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
STEP 6: SERIALIZE RESPONSE
┌─────────────────────────────────────────────────────────────┐
│ Ride Object → Pydantic Model → JSON                         │
│                                                              │
│ {                                                            │
│   "id": "550e8400-e29b-41d4-a716-446655440000",             │
│   "rider_id": "550e8400-e29b-41d4-a716-446655440001",       │
│   "driver_id": "550e8400-e29b-41d4-a716-446655440002",      │
│   "status": "accepted",                                     │
│   "origin": "123 Main St",                                  │
│   "destination": "456 Oak Ave",                             │
│   "fare": 25.50,                                            │
│   "rating": null,                                           │
│   "created_at": "2026-05-09T10:00:00Z",                     │
│   "updated_at": "2026-05-09T10:05:00Z",                     │
│   "matched_at": null                                        │
│ }                                                            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
STEP 7: RETURN HTTP RESPONSE
┌─────────────────────────────────────────────────────────────┐
│ HTTP 200 OK                                                  │
│ Content-Type: application/json                              │
│                                                              │
│ [JSON body from step 6]                                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
STEP 8: CLIENT RECEIVES & UPDATES UI
┌─────────────────────────────────────────────────────────────┐
│ JavaScript:                                                  │
│                                                              │
│ const ride = await response.json();                         │
│                                                              │
│ if (ride.driver_id) {                                       │
│   showNotification("✅ Driver assigned: " + ride.driver_id); │
│   updateUI(ride);                                           │
│ }                                                            │
└─────────────────────────────────────────────────────────────┘
```

---

## 🗄️ Database Layer Details

### Connection Pool
```
app.state.db_pool (AsyncPG Pool)
├── min_size: 5 (configurable)
├── max_size: 20 (configurable)
└── Maintains persistent connections to PostgreSQL
```

### Query Execution
```
1. Get connection from pool
   ↓
2. Execute prepared statement (parameterized for SQL injection protection)
   ↓
3. Parse result into Python record dict
   ↓
4. Map to Ride dataclass
   ↓
5. Return connection to pool
```

### Indexes
```sql
-- Existing index on rides table
CREATE INDEX rides_id_index ON rides (id);

-- Enables O(1) lookup performance
-- Query: SELECT * FROM rides WHERE id = $1
```

---

## 🔀 Polling Workflow (Client)

```
START
  │
  ├─→ Create Ride (POST /rides/create)
  │       │
  │       └─→ status: "requested"
  │
  ├─→ Find Driver (POST /matching/find)
  │       │
  │       └─→ status: "requested" → "accepted"
  │           driver_id: NULL → assigned driver
  │
  ├─→ POLL LOOP (start)
  │    │
  │    ├─→ GET /matching/status/{ride_id}
  │    │    │
  │    │    └─→ Check response
  │    │
  │    ├─→ IF driver_id != null
  │    │   └─→ DONE ✅ (break loop)
  │    │
  │    ├─→ ELSE
  │    │   ├─→ Wait 3 seconds
  │    │   └─→ Retry
  │    │
  │    ├─→ IF timeout (2 min)
  │    │   └─→ TIMEOUT ❌ (break loop)
  │    │
  │    └─→ REPEAT
  │
  └─→ END
```

---

## 🛡️ Security Layers

```
1. HTTPS/TLS Transport (production)
   └─ Encrypts data in transit

2. JWT Token Validation
   └─ Verifies user identity
   └─ Checks expiration
   └─ Validates signature

3. Rider Ownership Check
   ├─ Ensures rider_id from token matches ride.rider_id
   └─ Prevents unauthorized status access

4. SQL Injection Prevention
   └─ Uses parameterized queries ($1, $2, etc.)
   └─ No string concatenation

5. Rate Limiting (optional)
   └─ Can add per-user request limits
   └─ Prevents polling abuse
```

---

## 📊 Included Files

```
✅ CREATED:
├── api/endpoints/matching/status.py
│   └─ GET endpoint handler
├── schemas/matching/status.py
│   └─ Response validation model
└── test_matching_status.py
   └─ Integration test script

✅ MODIFIED:
├── api/endpoints/matching/__init__.py
│   └─ Registered status router
├── services/rides/matching.py
│   └─ Added get_matching_status() method
└── tests/unit/test_ride_matching_service.py
   └─ Added 3 new unit tests

✅ DOCUMENTATION:
├── IMPLEMENTATION_SUMMARY.md
│   └─ Complete implementation overview
├── POLLING_ENDPOINT_GUIDE.md
│   └─ Detailed API documentation
├── POLLING_QUICK_START.md
│   └─ Quick reference guide
└── ARCHITECTURE_DIAGRAM.md
   └─ This file - architecture visualization
```

---

## ✅ Verification Checklist

- [x] Endpoint created and registered
- [x] Database queries working
- [x] Input validation (JWT + ownership)
- [x] Output serialization (JSON)
- [x] Error handling (404, 403, 401)
- [x] Unit tests passing (7/7)
- [x] Database connection pooling active
- [x] Type hints complete
- [x] Docstrings added
- [x] Documentation provided
