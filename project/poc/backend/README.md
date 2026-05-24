# Backend

FastAPI backend for the local creative AI workflow slice. It owns the trust boundary: session exchange, tenant and brand policy, PDF extraction, profile versioning, model orchestration, quality checks, image jobs, metering, audit records, and reporting.

## Structure

The backend is intentionally organized like a small production service rather than a single-script demo:

```text
app/
  main.py              ASGI entrypoint
  factory.py           FastAPI app factory, middleware, exception handlers
  api/
    router.py          Router composition
    routes/            Endpoint groups by product capability
  core/                Config constants, auth/session helpers, error envelope
  domain/              Pure policy rules, such as image-prompt governance
  providers/           Model/provider gateway adapters
  services/            Use-case orchestration and persistence coordination
  db.py                SQLite schema and seed data for the local slice
  png.py               Deterministic placeholder asset generation
```

The local implementation still uses SQLite and deterministic providers, but the code boundaries mirror the target architecture: API routes stay thin, services own use cases, domain modules own policy, provider adapters isolate model behavior, and the database module owns local persistence setup.

The production recommendation keeps Python/FastAPI for the backend because the product depends on model-provider orchestration, PDF extraction, structured validation, background workers, and fast OpenAPI generation. Production replaces SQLite with Postgres, local deterministic providers with approved model providers, local auth with OIDC/SAML-backed sessions, and local placeholder assets with tenant-scoped object storage.

## Start

```sh
cd project/poc/backend
python -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

OpenAPI docs are available at:

```text
http://localhost:8000/docs
```

The default SQLite database is `project/poc/backend/.data/poc.sqlite`. Set `POC_DB_PATH` to use another local database.

## Verify

Targeted backend verification:

```sh
project/poc/scripts/verify-api.sh
```

All-up verification, including fallback browser-harness install/build and a real-backend smoke:

```sh
project/poc/scripts/verify-all.sh
```

Backend tests only:

```sh
cd project/poc/backend
python -m pytest
```
