# Ride-booking-management-system-AI-SDA
Structure

The project keeps only app bootstrap files in app/:

app/__init__.py

app/main.py

app/config.py

app/dependencies.py

Feature and domain modules are top-level packages:

api/

core/

db/

exception/

models/

repositories/

schemas/

services/

utils/

tests/

Setup

Copy .env.example to .env and set DB_URL and JWT_SECRET.

Install dependencies with pip install -r requirements.txt.

Run the PostgreSQL migration in migrations/001_users.sql.

Start the API with uvicorn app.main:app --reload.

n8n Ranking Provider Setup

The matching service supports two ranking modes:

local: in-app scoring algorithm (default)

n8n: external webhook ranking with optional local fallback

Set these env vars:

RANKING_PROVIDER=n8n

N8N_RANKING_WEBHOOK_URL=http://localhost:5678/webhook/ride-ranking

N8N_RANKING_TIMEOUT_SECONDS=2.5

N8N_RANKING_FALLBACK_ENABLED=true

# Optional auth header if your webhook is protected:

# N8N_RANKING_AUTH_HEADER=Bearer your-token

If RANKING_PROVIDER=n8n but webhook URL is missing, the app uses local ranking.

Webhook Request Payload

The backend sends:

{
	"ride": {
		
		"id": "uuid",
		
		"pickup_latitude": 24.8607,
		
		"pickup_longitude": 67.0011,
		
		"origin": "Clifton",
		
		"destination": "Airport",
		
		"ride_type": "ridex"
	},
	
	"available_drivers": [
	
		{
		
			"id": "uuid",
			
			"full_name": "Driver Name",
			
			"email": "driver@example.com",
			
			"rating": 4.8,
			
			"total_rides": 320
		}
		
	]
}

Supported Webhook Responses

Option A (recommended):

{
	
	"ranked_drivers": [
	
		{ "driver_id": "uuid-1", "score": 96.4, "distance_km": 1.2 },
		
		{ "driver_id": "uuid-2", "score": 92.8, "distance_km": 2.0 }
	]
	
}

Option B:

{


	"ordered_driver_ids": ["uuid-1", "uuid-2", "uuid-3"]
}


If the webhook fails, times out, or returns invalid JSON format, the service falls back to local ranking when N8N_RANKING_FALLBACK_ENABLED=true.

Auth Routes

POST /api/auth/register

POST /api/auth/login

POST /api/auth/refresh

POST /api/auth/logout

GET /api/auth/me
