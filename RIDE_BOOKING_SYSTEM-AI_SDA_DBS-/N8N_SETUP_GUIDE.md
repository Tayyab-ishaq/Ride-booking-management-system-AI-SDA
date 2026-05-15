# N8N Integration Setup Guide for Ride Management System

## Overview
This guide covers integrating **n8n** (workflow automation) into your Ride Booking System to send automated email notifications when rides are completed (status = "completed" AND payment status = "completed").

---

## Part 1: N8N Installation & Setup

### Option 1: Docker (Recommended for Development)

#### Prerequisites:
- Docker & Docker Compose installed

#### Steps:

1. **Create Docker Compose file** in your project root:

```yaml
version: '3.8'

services:
  n8n:
    image: n8nio/n8n:latest
    ports:
      - "5678:5678"
    environment:
      - N8N_HOST=localhost
      - N8N_PORT=5678
      - N8N_PROTOCOL=http
      - N8N_WEBHOOK_URL=http://localhost:5678
      - N8N_EMAIL_MODE=smtp
      - N8N_SMTP_HOST=${SMTP_HOST}
      - N8N_SMTP_PORT=${SMTP_PORT}
      - N8N_SMTP_USER=${SMTP_USER}
      - N8N_SMTP_PASS=${SMTP_PASS}
      - N8N_SMTP_SENDER=${SMTP_SENDER}
      - POSTGRES_DB=n8n
      - POSTGRES_USER=${N8N_DB_USER}
      - POSTGRES_PASSWORD=${N8N_DB_PASSWORD}
      - DB_TYPE=postgresdb
      - DB_POSTGRESDB_HOST=n8n_postgres
      - DB_POSTGRESDB_PORT=5432
      - DB_POSTGRESDB_DATABASE=n8n
      - DB_POSTGRESDB_USER=${N8N_DB_USER}
      - DB_POSTGRESDB_PASSWORD=${N8N_DB_PASSWORD}
    volumes:
      - n8n_data:/home/node/.n8n
    depends_on:
      - n8n_postgres
    networks:
      - n8n_network

  n8n_postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=n8n
      - POSTGRES_USER=${N8N_DB_USER}
      - POSTGRES_PASSWORD=${N8N_DB_PASSWORD}
    volumes:
      - n8n_postgres_data:/var/lib/postgresql/data
    networks:
      - n8n_network

volumes:
  n8n_data:
  n8n_postgres_data:

networks:
  n8n_network:
```

2. **Update your .env file** with:

```bash
# N8N Configuration
N8N_DB_USER=n8n_user
N8N_DB_PASSWORD=your_secure_password

# Email Configuration (Gmail, Sendgrid, etc.)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-app-password
SMTP_SENDER=noreply@yourrides.com
```

3. **Start N8N**:

```bash
docker-compose up -d
```

4. **Access N8N UI**: http://localhost:5678

---

### Option 2: Self-Hosted (Linux/Ubuntu)

```bash
# Install Node.js (v18+)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install n8n globally
sudo npm install -g n8n

# Start n8n
n8n start
```

---

### Option 3: Cloud (n8n Cloud)
- Visit: https://app.n8n.cloud
- Sign up and create account
- No installation needed, but requires internet

---

## Part 2: PostgreSQL Connection Setup

### Connect N8N to Your Ride Management Database

1. **In N8N UI → Credentials** (top left)
2. **Click "Create New Credential"**
3. **Search for "PostgreSQL"**
4. **Fill in connection details**:
   - Host: `your_db_host` (e.g., `localhost`)
   - Port: `5432`
   - Database: `your_database_name`
   - User: `your_db_user`
   - Password: `your_db_password`
   - SSL: Toggle based on your setup

5. **Test Connection** → Save

---

## Part 3: Email Configuration

### Gmail Setup (Recommended)

1. **Enable 2-Step Verification** in your Google Account
2. **Generate App Password**:
   - Go to: https://myaccount.google.com/apppasswords
   - Select "Mail" and "Windows Computer"
   - Copy the 16-character password
   - Use this as `SMTP_PASS` in .env

3. **In N8N → Credentials**:
   - Search for "Gmail"
   - Use OAuth2 or Service Account
   - Authorize N8N to send emails

### Alternative: SendGrid

1. **Create SendGrid Account**: https://sendgrid.com
2. **Generate API Key**
3. **In N8N → Credentials**:
   - Search for "SendGrid"
   - Enter API Key

---

## Part 4: FastAPI Webhook Integration

### Add Webhook Endpoint to Your FastAPI App

Create file: `api/endpoints/integrations/n8n_webhooks.py`

```python
from __future__ import annotations

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from core.security import create_access_token
from app.config import get_settings

router = APIRouter()


class RideCompletionPayload(BaseModel):
    """Payload sent from N8N when ride is completed"""
    ride_id: str
    rider_id: str
    driver_id: str
    rider_email: str
    driver_email: str
    driver_name: str
    rider_name: str
    amount: float
    origin: str
    destination: str
    ride_type: str


@router.post(
    "/n8n/ride-completion-webhook",
    status_code=status.HTTP_200_OK,
    summary="Webhook for ride completion notifications"
)
async def ride_completion_webhook(
    payload: RideCompletionPayload,
    settings: any = Depends(get_settings)
) -> dict:
    """
    This webhook is called by N8N when a ride is completed and payment is confirmed.
    N8N uses this to trigger email notifications.
    """
    try:
        # Validate the ride_id format
        UUID(payload.ride_id)
        
        # Log the event
        print(f"Ride Completion Event: {payload.ride_id}")
        
        # N8N will handle email sending
        return {
            "status": "success",
            "message": "Ride completion event received",
            "ride_id": payload.ride_id
        }
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ride_id format"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
```

### Register the Router in `api/router.py`

```python
from api.endpoints.integrations.n8n_webhooks import router as n8n_webhook_router

# Add this to your router includes:
api_router.include_router(n8n_webhook_router, tags=["N8N Integration"])
```

---

## Part 5: Database Queries for N8N

N8N needs to query your database to get ride & user details when sending emails.

### SQL Query in N8N (PostgreSQL node):

```sql
SELECT 
    r.id as ride_id,
    r.rider_id,
    r.driver_id,
    r.origin,
    r.destination,
    r.ride_type,
    r.fare,
    r.status,
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

---

## Part 6: N8N Workflow Setup

### Workflow 1: Send Email on Ride Completion

#### Step 1: Webhook Trigger
1. **Create New Workflow**
2. **Add Node → Webhooks → Webhook**
   - Authentication: None (or API Key if needed)
   - HTTP Method: POST
   - Copy the webhook URL

#### Step 2: Database Query
1. **Add Node → PostgreSQL**
   - Credential: Your ride_management database
   - Use the SQL query from Part 5
   - Parameters: Use webhook body data

#### Step 3: Email to Rider
1. **Add Node → Gmail / SendGrid / Email**
   - To: `{{ $node["PostgreSQL"].data["rider_email"] }}`
   - Subject: "Your Ride Completed - {{ $node["PostgreSQL"].data["ride_id"] }}"
   - Body:
   ```
   Hi {{ $node["PostgreSQL"].data["rider_name"] }},
   
   Your ride has been completed!
   
   Trip Details:
   - From: {{ $node["PostgreSQL"].data["origin"] }}
   - To: {{ $node["PostgreSQL"].data["destination"] }}
   - Amount: ${{ $node["PostgreSQL"].data["fare"] }}
   - Driver: {{ $node["PostgreSQL"].data["driver_name"] }}
   
   Thank you for using our service!
   ```

#### Step 4: Email to Driver
1. **Add Node → Gmail / SendGrid / Email**
   - To: `{{ $node["PostgreSQL"].data["driver_email"] }}`
   - Subject: "Ride Completed - Payment Confirmed"
   - Body:
   ```
   Hi {{ $node["PostgreSQL"].data["driver_name"] }},
   
   You have successfully completed a ride!
   
   Trip Details:
   - From: {{ $node["PostgreSQL"].data["origin"] }}
   - To: {{ $node["PostgreSQL"].data["destination"] }}
   - Amount Earned: ${{ $node["PostgreSQL"].data["fare"] }}
   - Rider: {{ $node["PostgreSQL"].data["rider_name"] }}
   
   Payment has been processed.
   ```

#### Step 5: Log Response
1. **Add Node → Return Response**
   - Body:
   ```json
   {
     "status": "success",
     "message": "Emails sent successfully",
     "ride_id": "{{ $node['Webhook'].data['ride_id'] }}"
   }
   ```

---

## Part 7: Integration with Your Confirm Payment Endpoint

### Update `api/endpoints/payments/confirm_payment.py`

Add n8n webhook trigger after payment confirmation:

```python
import httpx
from app.config import get_settings

@router.post(
    "/confirm",
    response_model=ConfirmPaymentResponse,
    status_code=status.HTTP_200_OK,
    summary="Confirm a payment",
)
async def confirm_payment(
    payload: ConfirmPaymentRequest,
    user_id: UUID = Depends(get_current_user_id),
    service: PaymentConfirmService = Depends(get_payment_confirm_service),
) -> ConfirmPaymentResponse:
    try:
        payment = await service.confirm_payment(
            payment_id=payload.payment_id,
            user_id=user_id,
            transaction_id=payload.transaction_id,
        )
        
        # WebSocket notification
        await ws_hub.emit_to_rider(
            payment.user_id,
            "payment_done",
            {
                "payment_id": str(payment.id),
                "ride_id": str(payment.ride_id),
                "status": payment.status.value,
                "amount": str(payment.amount),
            },
        )
        
        # Trigger N8N workflow for email notification
        try:
            settings = get_settings()
            async with httpx.AsyncClient() as client:
                await client.post(
                    "http://localhost:5678/webhook/ride-completion",  # Your N8N webhook URL
                    json={
                        "ride_id": str(payment.ride_id),
                        "payment_id": str(payment.id),
                        "status": payment.status.value,
                        "amount": str(payment.amount),
                        "timestamp": payment.updated_at.isoformat()
                    },
                    timeout=10.0
                )
        except Exception as e:
            print(f"N8N webhook call failed: {e}")
            # Don't fail payment confirmation if webhook fails
        
        return ConfirmPaymentResponse.model_validate(payment)
    except Exception as exc:
        raise_payment_http_exception(exc)
```

---

## Part 8: Testing the Integration

### Test Steps:

1. **Start Your FastAPI Server**:
   ```bash
   python -m uvicorn app.main:app --reload
   ```

2. **Start N8N**:
   ```bash
   docker-compose up -d
   # or
   n8n start
   ```

3. **Copy N8N Webhook URL** from your workflow

4. **Update the webhook URL** in `confirm_payment.py`

5. **Create a Test Workflow** in N8N:
   - Test manually with dummy data
   - Verify database connection works
   - Check email credentials

6. **Complete a Ride**:
   - Create ride → Accept → Mark as completed
   - Confirm payment
   - Check your email for notifications

---

## Part 9: Environment Variables Checklist

Add to your `.env`:

```bash
# N8N Database
N8N_DB_USER=n8n_user
N8N_DB_PASSWORD=secure_password

# Email SMTP
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASS=app-password
SMTP_SENDER=noreply@yourrides.com

# N8N Webhook (your FastAPI server)
N8N_WEBHOOK_BASE_URL=http://localhost:8000/api

# External N8N URL (for receiving webhooks from N8N)
N8N_WEBHOOK_URL=http://localhost:5678/webhook/ride-completion
```

---

## Part 10: Production Deployment

### Docker Production Setup

```yaml
version: '3.8'

services:
  n8n:
    image: n8nio/n8n:latest
    environment:
      - N8N_HOST=your-domain.com
      - N8N_PORT=443
      - N8N_PROTOCOL=https
      - N8N_WEBHOOK_URL=https://your-domain.com
      # ... other vars
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.n8n.rule=Host(`n8n.your-domain.com`)"
    networks:
      - reverse-proxy

  # Add Traefik reverse proxy for HTTPS
  traefik:
    image: traefik:v3.0
    ports:
      - "443:443"
    # ... configuration
```

### Security Best Practices:

1. **Use HTTPS** for all webhooks
2. **Add API Key authentication** to webhook endpoints
3. **Whitelist N8N IP** addresses
4. **Use environment variables** for all secrets
5. **Enable N8N authentication** (UI login)
6. **Rate limit** webhook endpoints
7. **Add error logging** and monitoring

---

## Part 11: Troubleshooting

| Issue | Solution |
|-------|----------|
| **N8N can't connect to DB** | Check credentials, verify firewall rules, ensure PostgreSQL is running |
| **Emails not sending** | Verify SMTP credentials, check spam folder, enable "Less secure apps" (Gmail) |
| **Webhook not firing** | Check webhook URL is correct, verify FastAPI is running, check N8N logs |
| **Database query error** | Test SQL query in pgAdmin first, verify column names |
| **CORS issues** | Add N8N URL to FastAPI CORS allowed origins |

---

## Summary

✅ **Installation**: Docker or self-hosted n8n
✅ **Database Connection**: PostgreSQL integration
✅ **Email Setup**: Gmail or SendGrid
✅ **Webhooks**: FastAPI endpoint for N8N
✅ **Workflow**: Automated emails on ride completion
✅ **Testing**: Local testing workflow
✅ **Production**: HTTPS, security, monitoring

---

## Next Steps:
1. Choose installation method
2. Set up database connection
3. Configure email service
4. Create N8N workflow
5. Test end-to-end
6. Deploy to production
