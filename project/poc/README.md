# Creative AI Workflow Slice

Local runnable prototype for a Figma-native creative AI workflow. It includes a backend, a Figma development plugin, and a browser fallback harness for deterministic verification.

## What Lives Here

- `backend/`: Python/FastAPI backend, SQLite persistence, layered API/core/domain/provider/service structure, PDF extraction, tenant and brand policy, deterministic model/image simulation, quality checks, usage reporting, and audit records.
- `frontend/`: Vite + React fallback browser harness for automated contract checks.
- `../figma-plugin/`: local Figma development plugin for the canonical designer workflow.
- `contracts/`: route and payload references.
- `fixtures/`: seeded selection, brand guideline sample, model-quality golden samples, and report fixtures.
- `scripts/`: backend verifier, all-up verifier, and real-backend smoke scripts.
- `demo/`: concise local demo guide.

## Backend Only

```sh
cd project/poc/backend
python -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

OpenAPI docs:

```text
http://localhost:8000/docs
```

Targeted backend verification:

```sh
project/poc/scripts/verify-api.sh
```

## Figma Plugin Demo

1. Start the backend with the backend-only command above or use `project/poc/scripts/run-demo.sh`.
2. Open Figma Desktop.
3. Import `project/figma-plugin/manifest.json` through **Plugins > Development > Import plugin from manifest**.
4. Run the plugin on a local file.
5. Create the demo selection.
6. Pair with the backend, generate copy/localization, create the image placeholder, apply outputs to canvas, and record apply events.

## Automated Browser Harness

Use this path for deterministic automated checks or when Figma is unavailable:

```sh
project/poc/scripts/run-demo.sh
```

Open `http://localhost:5173`, then follow `project/poc/demo/README.md`.

Stop with `Ctrl-C`.

Smoke launcher:

```sh
project/poc/scripts/run-demo.sh --smoke
```

## All-Up Verification

```sh
project/poc/scripts/verify-all.sh
```

The verifier runs backend tests, starts a local backend, verifies API contracts, installs and builds the fallback browser harness, runs a real-backend contract smoke, and runs a browser visual smoke test.

It also runs `project/poc/scripts/benchmark-latency.sh`, which samples copy generation, localization, and image-job creation and fails when median local round-trip latency reaches 2 seconds.

The POC intentionally does not implement production Postgres, managed queues, object storage, OIDC/SAML, or provider credentials. Those choices are specified in `docs/architecture.md`; this folder proves the API and workflow boundaries locally.
