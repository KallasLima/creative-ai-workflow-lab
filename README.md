# Creative AI Workflow Lab

Creative AI Workflow Lab is a local prototype for an AI-assisted design workflow. It shows how a Figma development plugin can call a backend-owned workflow for copy generation, localization, image placeholder creation, usage metering, and audit records.

The project is intentionally local-first. The model and image outputs are deterministic fixtures, while the backend, persistence, API contracts, Figma plugin bridge, browser fallback harness, and verification scripts are executable.

This is best read as a runnable architecture slice: it proves the workflow seams that are expensive to retrofit later, especially backend-owned policy, profile context, async asset jobs, usage metering, and explicit apply/audit records.

## What It Demonstrates

- A Figma development plugin that reads selected layers, previews generated outputs, and applies copy or image fills.
- A FastAPI backend that owns auth/session exchange, tenant and brand policy, prompt/profile context, model orchestration, PDF extraction, image job lifecycle, usage metering, and audit trails.
- A browser fallback harness for running the same workflow without Figma during local verification.
- A deployable backend shape with a Dockerfile, compose file, health check, and persistent data path.
- A 10-week delivery plan and architecture notes for turning the local proof into a production-grade workflow.

## Project Map

| Path | Purpose |
| --- | --- |
| `project/figma-plugin/` | Figma development plugin package. |
| `project/poc/backend/` | FastAPI backend with SQLite persistence and tests. |
| `project/poc/frontend/` | Browser fallback harness for the same backend workflow. |
| `project/poc/contracts/` | API and payload contracts shared by plugin and backend. |
| `project/poc/fixtures/` | Deterministic fixtures for brand, selection, quality, and reports. |
| `project/poc/scripts/` | Local run and verification scripts. |
| `project/deployment/` | Container-shaped backend deployment proof. |
| `docs/` | Architecture, trade-off, and delivery notes. |

## Run The Local Proof

Requirements:

- Python 3.11+
- Node.js 20+
- npm
- Google Chrome for the visual smoke test

Run the full verifier:

```sh
project/poc/scripts/verify-all.sh
```

Start the local backend and browser fallback harness:

```sh
project/poc/scripts/run-demo.sh
```

Then open:

```text
http://127.0.0.1:5173
```

## Run The Figma Development Plugin

1. Start the local demo with `project/poc/scripts/run-demo.sh`.
2. Open Figma Desktop.
3. Import `project/figma-plugin/manifest.json` as a development plugin.
4. Run `Creative AI Workflow Lab`.
5. Use `Create local proof selection`, then pair with the local backend and run copy, localization, and image placeholder actions.

The plugin is configured for local development only and talks to `http://localhost:8000`.

## What Is Mocked

- Model output is deterministic and fixture-backed.
- Image generation returns a 1024 x 1024 placeholder asset rather than calling a paid image model.
- Auth is local and deterministic, but it preserves the backend-owned session and token shape.
- SQLite stands in for a production relational database.

## Documentation

- [Architecture](docs/architecture.md)
- [Diagrams](docs/diagrams.md)
- [Delivery Plan](docs/delivery-plan.md)
- [Tradeoffs And Risks](docs/tradeoffs-and-risks.md)
- [Runnable Local Proof](docs/runnable-local-proof.md)
