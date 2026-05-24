# Deployment Shape

This folder is a container-shaped deployment package for the local POC backend. It proves that the backend can run as a deployable unit, but it is not the full production infrastructure.

It does not require a paid cloud account. It demonstrates the deployable unit that a free container host, internal platform, or later managed environment can run:

- pinned Python runtime,
- dependency install from `requirements.txt`,
- app copy without local virtual environments or build artifacts,
- persistent SQLite volume for the POC,
- `/health` healthcheck,
- container port mapping for the API boundary.

The production architecture in `docs/architecture.md` keeps the same API/worker boundary but replaces this local container shape with managed Postgres, managed queue infrastructure, object storage, OIDC/SAML-backed auth, OpenTelemetry, and tenant-scoped deployment configuration.

## Verify

```sh
project/poc/scripts/verify-all.sh
```

The all-up verifier starts the same FastAPI app, runs the API verifier against it, confirms persisted tenant/model-quality/usage records, then runs the browser-harness build and real-backend smoke.

If Docker is available, the same files can be run with:

```sh
docker compose -f project/deployment/docker-compose.yml up --build
```

Then check:

```sh
curl http://127.0.0.1:8000/health
```
