# Backend

FastAPI backend for the local creative AI workflow slice. It owns the trust boundary: session exchange, tenant and brand policy, PDF extraction, profile versioning, model orchestration, quality checks, image jobs, metering, audit records, and reporting.

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
