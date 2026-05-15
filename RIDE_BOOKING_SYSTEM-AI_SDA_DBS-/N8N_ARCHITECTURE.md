# N8N Integration Architecture

## Flow Diagram

```mermaid
graph TD
    A["Rider App"] -->|Complete Ride| B["FastAPI Backend"]
    C["Driver App"] -->|Confirm Location| B
    
    B -->|Update Ride Status| D["PostgreSQL DB"]
    D -->|Store| E["Rides Table"]
    D -->|Store| F["Drivers Table"]
    D -->|Store| G["Users Table"]
    
    B -->|Complete Payment| H["Payment Service"]
    H -->|Update Payment Status| D
    H -->|Trigger Webhook| I["N8N Webhook Endpoint"]
    
    I -->|POST Request| J["N8N Workflow Engine"]
    
    J -->|Query Data| K["PostgreSQL Connection"]
    K -->|Fetch Ride Details| D
    
    J -->|Send Email| L["Gmail/SendGrid"]
    L -->|Email Notification| M["Rider Email"]
    L -->|Email Notification| N["Driver Email"]
    
    J -->|Log Event| O["N8N Database"]
    
    M -->|Delivery Status| P["Email Client"]
    N -->|Delivery Status| Q["Email Client"]
    
    style B fill:#4A90E2
    style J fill:#FF6B6B
    style D fill:#2ECB71
    style L fill:#FFD93D
```

## System Architecture

```mermaid
architecture-diagram
    component User["User Clients"] {
        service Rider["Rider App"]
        service Driver["Driver App"]
    }
    
    component Backend["FastAPI Backend"] {
        service API["REST API"]
        service WebSocket["WebSocket"]
        service Payment["Payment Handler"]
        service Webhook["N8N Webhook Endpoint"]
    }
    
    component Automation["N8N Automation Server"] {
        service Workflows["Workflows Engine"]
        service DB_Connector["PostgreSQL Connector"]
        service Email_Connector["Email Connector"]
    }
    
    component Storage["Data Storage"] {
        service RideDB["PostgreSQL Database"]
        service N8NDB["N8N Database"]
    }
    
    component Communication["External Services"] {
        service SMTP["Gmail/SendGrid"]
        service EmailInbox["User Inboxes"]
    }
    
    User -->|API Requests| Backend
    Backend -->|SQL Queries| RideDB
    Payment -->|Webhook POST| Webhook
    Webhook -->|HTTP POST| Workflows
    Workflows -->|SQL Query| DB_Connector
    DB_Connector -->|Connect| RideDB
    Workflows -->|Send Email| Email_Connector
    Email_Connector -->|SMTP Protocol| SMTP
    SMTP -->|Email Delivery| EmailInbox
    Workflows -->|Store Logs| N8NDB
```

## Data Flow Sequence

```mermaid
sequenceDiagram
    participant Rider as Rider App
    participant Driver as Driver App
    participant API as FastAPI API
    participant DB as PostgreSQL
    participant Payment as Payment Service
    participant N8N as N8N Workflow
    participant Email as Email Service
    
    Rider->>API: Complete Ride
    API->>DB: UPDATE rides status = 'completed'
    Driver->>API: Confirm Payment
    API->>Payment: Confirm Payment Transaction
    Payment->>DB: UPDATE payment status = 'completed'
    Payment->>N8N: POST /webhook/ride-completion
    
    N8N->>N8N: Parse webhook payload
    N8N->>DB: SELECT * FROM rides WHERE id = $1
    DB-->>N8N: Return ride + user details
    
    N8N->>Email: Send email to Rider
    N8N->>Email: Send email to Driver
    
    Email-->>Rider: Ride completion email
    Email-->>Driver: Payment received email
    
    N8N-->>Payment: Return 200 OK
    Payment-->>API: Success
    API-->>Driver: Payment Confirmed
```

## Component Communication

### 1. **Ride Completion Flow**
```
Rider marks ride complete
    ↓
FastAPI updates ride status → DB
    ↓
Driver confirms payment
    ↓
FastAPI confirm_payment endpoint
    ↓
Payment status → 'completed' in DB
    ↓
HTTP POST to N8N webhook
    ↓
N8N triggers workflow
```

### 2. **N8N Internal Flow**
```
Webhook Trigger (receives payload)
    ↓
PostgreSQL Node (queries ride details)
    ↓
Email Node 1 (sends to rider)
    ↓
Email Node 2 (sends to driver)
    ↓
Response Node (confirms success)
```

### 3. **Database Query Structure**
```
rides table
    ├─ id
    ├─ rider_id → users
    ├─ driver_id → drivers
    ├─ status ('completed')
    ├─ origin
    ├─ destination
    └─ fare
    
payments table
    ├─ id
    ├─ ride_id → rides
    ├─ status ('completed')
    └─ amount
    
users table
    ├─ id
    ├─ email
    └─ first_name
```

## Deployment Architecture

```mermaid
graph TB
    subgraph "Your Infrastructure"
        FastAPI["FastAPI Server<br/>:8000"]
        PostgreSQL["PostgreSQL<br/>:5432"]
    end
    
    subgraph "N8N Infrastructure"
        N8N["N8N Server<br/>:5678"]
        N8N_DB["N8N Database<br/>PostgreSQL"]
    end
    
    subgraph "External Services"
        Gmail["Gmail SMTP"]
        SendGrid["SendGrid API"]
    end
    
    FastAPI -->|TCP 5432| PostgreSQL
    FastAPI -->|HTTP POST| N8N
    N8N -->|TCP 5432| PostgreSQL
    N8N -->|TCP 5432| N8N_DB
    N8N -->|SMTP 587| Gmail
    N8N -->|HTTPS API| SendGrid
    
    style FastAPI fill:#4A90E2
    style N8N fill:#FF6B6B
    style PostgreSQL fill:#2ECB71
```

## Port Mapping

| Service | Port | Protocol | Purpose |
|---------|------|----------|---------|
| FastAPI | 8000 | HTTP | REST API server |
| PostgreSQL | 5432 | TCP | Database |
| N8N UI | 5678 | HTTP | Workflow editor |
| SMTP (Gmail) | 587 | SMTP | Email sending |
| SMTP (Gmail) | 465 | SMTPS | Email sending (TLS) |
| SendGrid | 443 | HTTPS | API calls |

## Security Boundaries

```
┌─────────────────────────────────────────────┐
│           Public Internet                    │
│   (Rider/Driver Apps, Email Clients)        │
└────────────────┬────────────────────────────┘
                 │ HTTPS
         ┌───────▼────────┐
         │  Your Firewall  │
         └───────┬────────┘
                 │ HTTP (Internal)
    ┌────────────┴──────────────┐
    │                           │
┌───▼────────┐          ┌──────▼───┐
│ FastAPI    │◄────────►│PostgreSQL │
│ :8000      │          │ :5432     │
└───┬────────┘          └───────────┘
    │ HTTP POST
    │ (to N8N)
    │
    │ ┌──────────────────────────────┐
    │ │  N8N Automation Layer        │
    │ │  (Can be separate server)    │
    │ │                              │
    └─►│ ├─ Workflow Engine          │
        │ ├─ PostgreSQL Connector    │
        │ ├─ Email Connector         │
        │ └─ Webhook Handler         │
        │                            │
        └───────────┬────────────────┘
                    │ SMTP/HTTPS
        ┌───────────▼──────────────┐
        │  External Services       │
        │ ├─ Gmail                 │
        │ ├─ SendGrid              │
        │ └─ Other APIs            │
        └──────────────────────────┘
```

## Error Handling & Retry Logic

```mermaid
graph TD
    A["Payment Confirmed"] -->B{"N8N Webhook\nReachable?"}
    B -->|Yes| C["N8N Processes"]
    B -->|No| D["Retry Queue"]
    D -->|Max 3 retries| E{"Success?"}
    E -->|Yes| C
    E -->|No| F["Log Error & Alert"]
    C --> G{"DB Query\nSuccessful?"}
    G -->|Yes| H["Send Emails"]
    G -->|No| I["Rollback & Log"]
    H --> J{"Email\nSent?"}
    J -->|Yes| K["Log Success"]
    J -->|No| L["Retry with Exponential Backoff"]
    K --> M["Update Status"]
    L --> M
```

## Monitoring Points

1. **N8N Workflow Logs**: Check execution history
2. **PostgreSQL Slow Queries**: Monitor query performance
3. **Email Delivery**: Track bounces & failures
4. **Webhook Latency**: Monitor response times
5. **Error Rates**: Alert on failures
