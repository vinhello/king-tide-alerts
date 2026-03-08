# Architecture Overview

## System overview
King Tide Alert monitors NOAA tide predictions for Sausalito (station 9414806) and sends email/SMS notifications to subscribers before high tides that may flood the Bay Trail bike path. It consists of a FastAPI backend and a React SPA frontend, deployed as separate services on Railway with a shared PostgreSQL database.

## Layer structure
```
HTTP Request → FastAPI Router → Service → SQLAlchemy Model → PostgreSQL
                                  ↓
                          External APIs (NOAA, Resend, Twilio, Stripe)
```

The frontend is a standalone React SPA that communicates with the backend via REST API.

## Key patterns
| Pattern | Where | Description |
|---|---|---|
| Router | `backend/app/routers/` | HTTP endpoint definitions, request validation via Pydantic schemas |
| Service | `backend/app/services/` | Business logic, external API calls, notification orchestration |
| Model | `backend/app/models/` | SQLAlchemy ORM models with cross-DB compatible types |
| Schema | `backend/app/schemas/` | Pydantic request/response models for API validation |
| Scheduler | `backend/app/services/scheduler.py` | APScheduler daily cron (6 AM Pacific) for tide checking |

## Important files / entrypoints
| File | Purpose |
|---|---|
| `backend/app/main.py` | FastAPI app init, CORS, router registration, scheduler lifecycle |
| `backend/app/config.py` | Pydantic Settings — all env vars and thresholds |
| `backend/app/database.py` | SQLAlchemy engine and session setup |
| `backend/app/services/king_tide_detector.py` | Core logic: fetch NOAA data, detect high tides, trigger alerts |
| `backend/app/services/noaa.py` | NOAA Tides & Currents API client |
| `backend/app/services/notification.py` | Email (Resend) and SMS (Twilio) sending |
| `backend/app/services/scheduler.py` | APScheduler configuration |
| `backend/app/routers/subscribers.py` | Subscribe, confirm, unsubscribe endpoints |
| `backend/app/routers/tides.py` | Tide data endpoint for frontend chart |
| `backend/app/routers/stripe.py` | Stripe checkout session and webhook |
| `frontend/src/App.tsx` | React router and page layout |
| `frontend/src/components/SubscribeForm.tsx` | Email/SMS subscription form with consent |
| `frontend/src/components/TideChart.tsx` | Recharts tide visualization |

## Database
Three models managed via Alembic migrations:

- **Subscriber** — email, phone, notification preference, confirmation/unsubscribe tokens
- **KingTideEvent** — detected high tide events with peak height and time
- **NotificationSent** — audit log of sent notifications (subscriber, event, channel, timing)

Conventions:
- Use `sqlalchemy.Uuid` (not `postgresql.UUID`) for cross-DB compatibility with SQLite tests
- Enum columns use `values_callable` to send lowercase values to PostgreSQL

## Authentication
- **No user authentication** — the app is a public notification service
- **Admin endpoints** protected by `ADMIN_API_KEY` header (`x-api-key`)
- **Subscriber actions** (confirm, unsubscribe) use per-subscriber `unsubscribe_token` in email/SMS links

## External services
| Service | Purpose | Config |
|---|---|---|
| NOAA Tides & Currents | Tide predictions for station 9414806 | `NOAA_STATION_ID` |
| Resend | Email notifications from `alert@alert.kingtidealert.com` | `RESEND_API_KEY` |
| Twilio | SMS notifications (pending A2P registration) | `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER` |
| Stripe | Donation checkout flow | `STRIPE_API_KEY`, `STRIPE_WEBHOOK_SECRET` |

## What to avoid
- Never query the database directly from routers — always go through services
- Never use PostgreSQL-specific column types — use cross-DB compatible equivalents
- Never hardcode station IDs or thresholds — use `config.settings`
- Never import from `app.database` in tests — use `conftest.py` fixtures (`test_db`, `client`)
