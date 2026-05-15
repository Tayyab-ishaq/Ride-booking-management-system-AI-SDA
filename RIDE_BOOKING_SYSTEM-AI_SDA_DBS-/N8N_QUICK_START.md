# N8N Integration - Quick Start Checklist

## Phase 1: Pre-Setup (Day 1)

### Email Service Setup
- [ ] **Gmail**:
  - [ ] Enable 2-Step Verification: https://myaccount.google.com/security
  - [ ] Generate App Password: https://myaccount.google.com/apppasswords
  - [ ] Save password to `.env` as `SMTP_PASS`
  - [ ] Note: Gmail will be in `.env` with `SMTP_USER=your-email@gmail.com`

- [ ] **Alternative - SendGrid** (if preferred):
  - [ ] Create account: https://sendgrid.com
  - [ ] Generate API Key
  - [ ] Save to `.env` as `SENDGRID_API_KEY`

### Environment Variables
- [ ] Create/update `.env` file:
```bash
# Database Connection (for N8N to use)
N8N_DB_USER=n8n_user
N8N_DB_PASSWORD=your_secure_password_here

# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASS=xxxxxxxxxxxxxxxxxxx  # 16-char app password
SMTP_SENDER=noreply@yourrides.com

# FastAPI Server
FASTAPI_HOST=localhost
FASTAPI_PORT=8000
```

---

## Phase 2: N8N Installation (Day 1-2)

### Option A: Docker (Recommended)
- [ ] Install Docker Desktop: https://www.docker.com/products/docker-desktop
- [ ] Copy `docker-compose.yml` to project root (from N8N_SETUP_GUIDE.md)
- [ ] Update `.env` with database credentials
- [ ] Run: `docker-compose up -d`
- [ ] Access UI: http://localhost:5678
- [ ] Set up N8N admin account (email/password)

### Option B: Self-Hosted
- [ ] Install Node.js v18+: https://nodejs.org
- [ ] Run: `npm install -g n8n`
- [ ] Run: `n8n start`
- [ ] Access UI: http://localhost:5678

### Verification
- [ ] N8N UI loads at http://localhost:5678
- [ ] Can log in to N8N dashboard
- [ ] N8N backend is running

---

## Phase 3: Database Connection (Day 2)

### Configure N8N → PostgreSQL Connection
- [ ] In N8N UI, go to **Credentials** (gear icon)
- [ ] Click **"Create new credential"**
- [ ] Search for **"PostgreSQL"**
- [ ] Fill in your database details:
  - Host: `localhost` (or your DB host)
  - Port: `5432`
  - Database: `your_database_name`
  - User: `your_db_user`
  - Password: `your_db_password`
  - SSL: `false` (unless required)
- [ ] Click **"Test connection"** - should pass
- [ ] Save credential

### Verification
- [ ] Connection test passes
- [ ] Can query database from N8N

---

## Phase 4: Email Configuration (Day 2)

### Configure N8N Email Credential
- [ ] In N8N UI, go to **Credentials**
- [ ] Click **"Create new credential"**
- [ ] Search for **"Gmail"** (or "SendGrid" if using that)

**For Gmail:**
- [ ] Select **"OAuth2"** or **"SMTP"**
- [ ] If SMTP:
  - Host: `smtp.gmail.com`
  - Port: `587`
  - User: `your-email@gmail.com`
  - Password: `your-app-password`
  - TLS: `true`
- [ ] Click **"Test connection"** - should pass
- [ ] Save credential

**For SendGrid:**
- [ ] Select authentication type
- [ ] Paste your SendGrid API Key
- [ ] Test connection
- [ ] Save credential

### Verification
- [ ] Email credential test passes
- [ ] SMTP connection established

---

## Phase 5: FastAPI Webhook Setup (Day 2-3)

### Create N8N Webhook Endpoint
- [ ] Copy `n8n_webhooks.py` to `api/endpoints/integrations/`
- [ ] Create `api/endpoints/integrations/__init__.py` (empty file)
- [ ] Update `api/router.py`:

```python
from api.endpoints.integrations.n8n_webhooks import router as n8n_router

# In the router includes section:
api_router.include_router(n8n_router, tags=["N8N Integration"])
```

- [ ] Test FastAPI starts: `python -m uvicorn app.main:app --reload`
- [ ] Verify endpoint: `curl http://localhost:8000/api/n8n/test`
- [ ] Should return: `{"status": "ok", ...}`

### Verification
- [ ] FastAPI server starts without errors
- [ ] Webhook endpoint responds to test request
- [ ] No import errors

---

## Phase 6: Update Payment Confirmation (Day 3)

### Integrate N8N Webhook Call
- [ ] Install httpx: `pip install httpx`
- [ ] Update `api/endpoints/payments/confirm_payment.py`
- [ ] Add n8n webhook trigger (see N8N_SETUP_GUIDE.md Part 7)
- [ ] Test payment confirmation flow

### Verification
- [ ] Payment confirmation works
- [ ] FastAPI doesn't crash if N8N webhook fails
- [ ] Error handling is in place

---

## Phase 7: Create N8N Workflow (Day 3-4)

### Create Base Workflow
- [ ] Go to N8N UI → **Workflows**
- [ ] Create **New Workflow**
- [ ] Name it: `"Ride Completion Email Notifications"`
- [ ] Save workflow

### Add Webhook Trigger
- [ ] Add **Webhooks** node
- [ ] Select **Webhook** trigger
- [ ] HTTP Method: `POST`
- [ ] **Copy the webhook URL** (you'll need this)
- [ ] Authentication: Leave as None (or add API key if desired)

### Add Database Query Node
- [ ] Add **PostgreSQL** node
- [ ] Select credential: Your ride_management database
- [ ] Query type: **Execute Query**
- [ ] SQL Query (from Part 5 of setup guide):
```sql
SELECT 
    r.id as ride_id,
    r.rider_id,
    r.driver_id,
    r.origin,
    r.destination,
    r.ride_type,
    r.fare,
    rr.email as rider_email,
    rr.first_name as rider_name,
    d.email as driver_email,
    d.first_name as driver_name,
    p.status as payment_status,
    p.amount
FROM rides r
JOIN users rr ON r.rider_id = rr.id
JOIN drivers d ON r.driver_id = d.id
JOIN payments p ON r.id = p.ride_id
WHERE r.id = $1
    AND r.status = 'completed'
    AND p.status = 'completed'
LIMIT 1;
```
- [ ] Parameters: `{{ $node["Webhook"].data["ride_id"] }}`

### Add Email to Rider
- [ ] Add **Gmail** (or SendGrid) node
- [ ] Select credential: Your Gmail credential
- [ ] To: `{{ $node["PostgreSQL"].data["rider_email"] }}`
- [ ] Subject: `Your Ride Completed - #{{ $node["PostgreSQL"].data["ride_id"].substring(0, 8) }}`
- [ ] Body:
```
Hi {{ $node["PostgreSQL"].data["rider_name"] }},

Your ride has been completed!

📍 Trip Details:
From: {{ $node["PostgreSQL"].data["origin"] }}
To: {{ $node["PostgreSQL"].data["destination"] }}
Amount: ${{ $node["PostgreSQL"].data["fare"] }}
Driver: {{ $node["PostgreSQL"].data["driver_name"] }}

Thank you for using our ride service!

Best regards,
Ride Management Team
```

### Add Email to Driver
- [ ] Add another **Gmail** (or SendGrid) node
- [ ] To: `{{ $node["PostgreSQL"].data["driver_email"] }}`
- [ ] Subject: `Ride Completed - Payment Confirmed`
- [ ] Body:
```
Hi {{ $node["PostgreSQL"].data["driver_name"] }},

You have successfully completed a ride!

📍 Trip Details:
From: {{ $node["PostgreSQL"].data["origin"] }}
To: {{ $node["PostgreSQL"].data["destination"] }}
Amount Earned: ${{ $node["PostgreSQL"].data["fare"] }}
Rider: {{ $node["PostgreSQL"].data["rider_name"] }}

Payment has been processed to your account.

Best regards,
Ride Management Team
```

### Add Response Node
- [ ] Add **Return** node
- [ ] Response Body:
```json
{
  "status": "success",
  "message": "Emails sent successfully",
  "ride_id": "{{ $node['Webhook'].data['ride_id'] }}"
}
```

### Verification
- [ ] All nodes connected properly
- [ ] Workflow saves without errors
- [ ] No red error indicators

---

## Phase 8: Test N8N Workflow (Day 4)

### Manual Test
- [ ] Open N8N workflow
- [ ] Click **"Test Webhook"** (Webhook node settings)
- [ ] Send test payload:
```json
{
  "ride_id": "550e8400-e29b-41d4-a716-446655440000"
}
```
- [ ] Check if PostgreSQL connects
- [ ] Check if query returns data
- [ ] Verify emails are "sent" (check N8N logs)

### Fix Issues
- [ ] If PostgreSQL fails: Check credentials, verify database is running
- [ ] If query fails: Test SQL in pgAdmin separately
- [ ] If email fails: Verify SMTP credentials, check spam folder

### Test from FastAPI
- [ ] Update webhook URL in `confirm_payment.py`
- [ ] Create a test ride through your app
- [ ] Accept the ride as driver
- [ ] Mark ride as completed
- [ ] Confirm payment
- [ ] Check N8N workflow executed
- [ ] Check emails received

### Verification
- [ ] Workflow executes successfully
- [ ] All nodes complete without errors
- [ ] Emails appear in test inboxes (may be in spam)
- [ ] Response is returned to FastAPI

---

## Phase 9: Production Deployment (Day 5+)

### Before Production
- [ ] All tests pass
- [ ] Error handling implemented
- [ ] Logging is configured
- [ ] Security reviewed

### Production Checklist
- [ ] [ ] Update webhook URL to production domain
- [ ] [ ] Use production database credentials
- [ ] [ ] Enable HTTPS for all endpoints
- [ ] [ ] Add API key authentication to webhooks
- [ ] [ ] Configure N8N with production settings
- [ ] [ ] Set up monitoring & alerting
- [ ] [ ] Enable N8N UI authentication
- [ ] [ ] Set resource limits on N8N containers
- [ ] [ ] Configure backups for N8N database
- [ ] [ ] Add error notifications (Slack, email)

---

## Troubleshooting Checklist

### N8N Won't Start
- [ ] Check Docker is running
- [ ] Check ports 5678 not already in use: `netstat -ano | findstr 5678`
- [ ] Check Docker logs: `docker logs n8n`
- [ ] Verify `.env` variables are set correctly

### Can't Connect to PostgreSQL
- [ ] Ping database: `psql -h localhost -U user -d dbname`
- [ ] Verify credentials in N8N match your database
- [ ] Check PostgreSQL is running
- [ ] Check firewall rules
- [ ] Verify IP addresses if not localhost

### Emails Not Sending
- [ ] Check SMTP credentials are correct
- [ ] Try sending test email from N8N UI
- [ ] Check spam/junk folder
- [ ] Verify Gmail app password (not regular password)
- [ ] Check SendGrid API key if using that

### Webhook Not Firing
- [ ] Verify webhook URL in FastAPI code matches N8N
- [ ] Check FastAPI is running on correct port
- [ ] Test with: `curl -X POST http://localhost:8000/api/n8n/test`
- [ ] Check N8N workflow is activated (toggle in UI)
- [ ] Look at N8N execution logs

### Database Query Returns No Data
- [ ] Test SQL query separately in pgAdmin
- [ ] Verify table names are correct (case-sensitive)
- [ ] Check sample data exists in database
- [ ] Verify column names match
- [ ] Check WHERE conditions are logical

---

## Key Webhook URLs

### N8N Workflow Webhook
```
N8N UI → Your Workflow → Webhook Node
URL visible in: Webhook Node → Details
```
Copy this and use in FastAPI `confirm_payment.py`

### FastAPI N8N Webhook Endpoint
```
http://localhost:8000/api/n8n/ride-completion
```
Use this in N8N to test FastAPI connectivity

### FastAPI Test Endpoint
```
http://localhost:8000/api/n8n/test
```
Returns `{"status": "ok"}` if FastAPI is running

---

## Files to Modify/Create

| File | Action | Status |
|------|--------|--------|
| `.env` | Update with email/database creds | ⏳ |
| `docker-compose.yml` | Create from template | ⏳ |
| `api/endpoints/integrations/n8n_webhooks.py` | Copy provided file | ⏳ |
| `api/endpoints/integrations/__init__.py` | Create empty | ⏳ |
| `api/router.py` | Add n8n router include | ⏳ |
| `api/endpoints/payments/confirm_payment.py` | Add webhook call | ⏳ |
| `requirements.txt` | Add httpx if needed | ⏳ |

---

## Success Criteria

- [x] N8N installed and running
- [x] Database connection working
- [x] Email service configured
- [x] FastAPI webhook endpoint created
- [x] N8N workflow created
- [x] Emails sent on ride completion
- [x] No errors in logs
- [x] Response times acceptable
- [x] Emails delivered to users
- [x] Ready for production

---

## Next Steps After Setup

1. **Monitor**: Set up error logging and monitoring
2. **Enhance**: Add more notifications (SMS, push notifications)
3. **Personalize**: Customize email templates with your branding
4. **Automate**: Create more workflows (ride reminders, promotions, etc.)
5. **Scale**: Consider dedicated N8N infrastructure for production

---

## Support Resources

- **N8N Docs**: https://docs.n8n.io
- **N8N Community**: https://community.n8n.io
- **FastAPI Docs**: https://fastapi.tiangolo.com
- **PostgreSQL Docs**: https://www.postgresql.org/docs
- **Gmail Setup**: https://support.google.com/accounts/answer/185833
