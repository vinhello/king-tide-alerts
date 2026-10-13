# King Tide Alerts

Get notified before high tides flood the Bay Trail through Sausalito. Free email and SMS alerts so you can plan your bike commute.

**Website:** [kingtidealert.com](https://kingtidealert.com)

## How it works

1. Subscribe with your email or phone number at [kingtidealert.com](https://kingtidealert.com)
2. We check NOAA tide predictions daily at 6 AM Pacific
3. When a high tide above 6.0 ft (MLLW) is forecasted at the San Francisco (Golden Gate) gauge, you get alerted:
   - **7 days before** — heads up to plan ahead
   - **48 hours before** — reminder to take an alternate route
4. Alerts include the predicted peak time, a flooding window (estimated ~2 hours before and after peak), and a disclaimer
5. Tides at or above 6.5 ft get a "king tide" callout

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
# Backend (89 tests)
cd backend
pytest tests/ -v

# Frontend (27 tests)
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
| `RESEND_WEBHOOK_SECRET` | Resend webhook signing secret (starts with `whsec_`). Enables `POST /api/webhooks/resend`, which records delivery outcomes and stops sending to an address after a hard bounce or spam complaint. Empty disables the endpoint. |
| `ADMIN_API_KEY` | API key for admin endpoints (e.g. test-alert) |
| `APP_URL` | Frontend URL (for confirmation/unsubscribe links) |
| `PUBLIC_API_URL` | This backend's public URL (no trailing slash). Enables RFC 8058 one-click unsubscribe headers on alert emails. Empty disables the one-click header. |
| `FEEDBACK_EMAIL` | Inbox that receives feedback form submissions (default: `info@kingtidealert.com`) |
| `HEALTHCHECK_PING_URL` | Optional. Ping URL of a [healthchecks.io](https://healthchecks.io) check. The daily job pings it on start, success and failure so a missed run triggers an email. Empty disables. |
| `NOAA_STATION_ID` | NOAA station (default: `9414290` — San Francisco, Golden Gate) |
| `KING_TIDE_THRESHOLD` | Alert threshold in MLLW ft (default: `6.0`) |
| `KING_TIDE_HEIGHT` | King tide label threshold in MLLW ft (default: `6.5`) |
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
| POST | `/api/feedback` | Send feedback from the website to the project inbox |
| GET | `/api/tides/upcoming?days=14` | Tide predictions with king tide flags |
| POST | `/api/stripe/create-checkout-session` | Start a donation checkout |
| POST | `/api/stripe/webhook` | Stripe webhook handler |
| POST | `/api/webhooks/resend` | Resend delivery webhook (delivered, delayed, bounced, complained) |

## Analytics

The site uses [Plausible](https://plausible.io) (cookieless, no personal data) via the script tag in `frontend/index.html`, with custom events for Subscribe, Confirm, Resend Confirmation, Calendar Download, Donate Click and Feedback Sent. Events are sent through `frontend/src/services/analytics.ts`, which is a no-op when the script is absent or blocked.

## Data source

Tide predictions come from the [NOAA CO-OPS API](https://tidesandcurrents.noaa.gov/api/) — free, public, no auth required. The station is San Francisco at the Golden Gate (`9414290`): the nearest gauge with live observations, and the reference Marin County and Caltrans use for flooding at Manzanita. Heights use the MLLW datum, so they represent feet above mean lower low water at that gauge.
