# King Tide Alerts

Get notified before king tides flood the Bay Trail through Sausalito. Free email and SMS alerts so you can plan your bike commute.

## How it works

1. Subscribe with your email or phone number
2. We check NOAA tide predictions daily at 6 AM Pacific
3. When a king tide is forecasted (> 1.0 ft above MHHW at the Golden Gate), you get alerted:
   - **7 days before** — heads up to plan ahead
   - **48 hours before** — reminder to take an alternate route

## Tech stack

- **Backend:** FastAPI, SQLAlchemy, PostgreSQL, APScheduler
- **Frontend:** React, TypeScript, Vite, Recharts
- **Integrations:** NOAA CO-OPS API, Resend (email), Twilio (SMS), Stripe (donations)
- **Deployment:** Railway

## Project structure

```
king-tide-alerts/
├── backend/          # FastAPI API + background scheduler
│   ├── app/
│   │   ├── models/   # SQLAlchemy models
│   │   ├── routers/  # API endpoints
│   │   ├── schemas/  # Pydantic request/response models
│   │   ├── services/ # NOAA client, notifications, scheduler
│   │   └── utils/    # Email templates
│   ├── alembic/      # Database migrations
│   └── tests/
└── frontend/         # React SPA
    └── src/
        ├── components/
        ├── pages/
        └── services/
```

## Local development

### Prerequisites

- Python 3.11+
- Node 18+
- PostgreSQL

### Backend

```bash
cd backend
createdb king_tide_alerts
cp .env.example .env
# Edit .env with your DATABASE_URL

pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

API runs at http://localhost:8000

### Frontend

```bash
cd frontend
echo "VITE_API_URL=http://localhost:8000" > .env
npm install
npm run dev
```

App runs at http://localhost:5173

## Running tests

```bash
# Backend (20 tests, 81% coverage)
cd backend
pytest tests/ -v

# Frontend (14 tests)
cd frontend
npx vitest run
```

## Linting

```bash
# Backend
cd backend
ruff check .
mypy app/ --ignore-missing-imports

# Frontend
cd frontend
npx eslint src/
npx tsc --noEmit
```

## Deployment (Railway)

The project deploys as three Railway services:

| Service | Root directory | Description |
|---------|---------------|-------------|
| PostgreSQL | — | Railway managed database |
| Backend | `/backend` | Dockerfile builds Python, runs migrations, starts uvicorn |
| Frontend | `/frontend` | Multi-stage Dockerfile: node build → nginx |

### Backend environment variables

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string (from Railway Postgres) |
| `RESEND_API_KEY` | Resend API key for email |
| `TWILIO_ACCOUNT_SID` | Twilio account SID for SMS |
| `TWILIO_AUTH_TOKEN` | Twilio auth token |
| `TWILIO_PHONE_NUMBER` | Twilio phone number |
| `STRIPE_API_KEY` | Stripe secret key |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook signing secret |
| `APP_URL` | Frontend URL (for confirmation/unsubscribe links) |
| `NOAA_STATION_ID` | NOAA station (default: `9414290` — Golden Gate) |
| `KING_TIDE_THRESHOLD` | Height in ft above MHHW (default: `1.0`) |
| `ENVIRONMENT` | Set to `production` to enable the scheduler |

### Frontend environment variables

| Variable | Description |
|----------|-------------|
| `VITE_API_URL` | Backend API URL |

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Health check |
| POST | `/api/subscribe` | Create a new subscriber |
| GET | `/api/confirm/{token}` | Confirm subscription |
| GET | `/api/unsubscribe/{token}` | Unsubscribe |
| GET | `/api/tides/upcoming?days=14` | Tide predictions with king tide flags |
| POST | `/api/stripe/create-checkout-session` | Start a donation checkout |
| POST | `/api/stripe/webhook` | Stripe webhook handler |

## Data source

Tide predictions come from the [NOAA CO-OPS API](https://tidesandcurrents.noaa.gov/api/) — free, public, no auth required. The primary station is San Francisco / Golden Gate (`9414290`), using the MHHW datum so positive values indicate height above normal high tide.
