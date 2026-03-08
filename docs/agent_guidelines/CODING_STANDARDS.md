# Coding Standards

## General principles
- Prefer explicit over implicit
- One function = one responsibility
- Errors must be handled — never swallowed silently
- No magic numbers or magic strings — use `config.settings` for thresholds

## Naming conventions

### Backend (Python)
| Type | Convention | Example |
|---|---|---|
| Variables/functions | snake_case | `get_subscriber_by_email()` |
| Classes | PascalCase | `KingTideEvent` |
| Constants | UPPER_SNAKE_CASE | `KING_TIDE_THRESHOLD` |
| Files | snake_case | `king_tide_detector.py` |

### Frontend (TypeScript/React)
| Type | Convention | Example |
|---|---|---|
| Variables/functions | camelCase | `fetchTideData()` |
| Components | PascalCase | `SubscribeForm` |
| Constants | UPPER_SNAKE_CASE | `API_BASE_URL` |
| Component files | PascalCase | `TideChart.tsx` |
| Utility files | camelCase | `api.ts` |

## File organisation
```
backend/
  app/
    routers/       # FastAPI route handlers (thin — delegate to services)
    services/      # Business logic and external API calls
    models/        # SQLAlchemy ORM models
    schemas/       # Pydantic request/response models
    config.py      # Pydantic Settings (all env vars)
    database.py    # SQLAlchemy engine and session
    main.py        # FastAPI app entrypoint
  tests/           # pytest tests mirroring app/ structure
  alembic/         # Database migrations

frontend/
  src/
    components/    # Reusable React components
    pages/         # Page-level components (one per route)
    services/      # API client modules
    types/         # TypeScript type definitions
    styles/        # CSS/Tailwind styles
```

## Testing rules

### Backend (pytest)
- Tests use SQLite in-memory via `conftest.py` fixtures (`test_db`, `client`)
- Mock external services (NOAA, Resend, Twilio) with `unittest.mock`
- Test files: `backend/tests/test_*.py`
- Run: `cd backend && pytest tests/ -v`

### Frontend (vitest)
- Uses jsdom environment with Testing Library for React components
- Test files: `frontend/src/**/__tests__/*.test.tsx`
- Run: `cd frontend && npx vitest run`

### Both
- Every new function needs at least one test
- Cover: happy path + at least one error/edge case
- No mocking the module under test

## Linting
- **Backend:** `ruff check backend/` (lint), `ruff format backend/` (format)
- **Frontend:** `npm run lint` from `frontend/` (ESLint)

## Error handling
- Backend: raise `fastapi.HTTPException` for API errors
- Backend: Pydantic validates request schemas automatically
- Frontend: axios interceptors or try/catch for API calls

## Dependencies
- Backend: `backend/requirements.txt` — do not add new packages without asking
- Frontend: `frontend/package.json` — do not add new packages without asking
- Prefer existing packages already in the dependency files

## What to avoid
- Do not use PostgreSQL-specific column types (use `sqlalchemy.Uuid`, not `postgresql.UUID`)
- Do not add co-authored-by lines in commits
- Do not import from `app.database` in tests — use `conftest.py` fixtures
- Do not add business logic to routers — delegate to services
