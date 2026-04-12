# Backend

This backend is a FastAPI scaffold for Maya Portfolio Manager.

## Structure

- `app/main.py` - FastAPI application entrypoint
- `app/api/v1/` - API routing and endpoint modules
- `app/core/` - configuration and shared core setup
- `app/db/` - database base class and session scaffolding
- `app/models/` - future ORM models
- `app/schemas/` - future request and response schemas
- `app/services/domain/` - future domain services
- `tests/` - backend test suite

## Current Status

Only a basic `/health` endpoint is implemented. No authentication, business logic, or legacy Flask porting has been added yet.

## Run Locally

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Copy `.env.example` to `.env` if you want to customize settings.
4. Start the development server:

```bash
uvicorn app.main:app --reload
```

5. Open `http://127.0.0.1:8000/health`

## Run Tests

```bash
pytest
```
