# Deployment Proof

This folder is the production-shape deployment proof for the local POC backend.

It does not require a paid cloud account. It proves the deployable unit that a free container host, internal platform, or later managed environment can run:

- pinned Python runtime,
- dependency install from `requirements.txt`,
- app copy without local virtual environments or build artifacts,
- persistent SQLite volume for the POC,
- `/health` healthcheck,
- container port mapping for the API boundary.

## Verify

```sh
scripts/verify-deployment-proof.sh
```

To prove the backend entrypoint, health check, and persisted state behavior without a cloud account or local Docker daemon, run:

```sh
scripts/verify-deployment-runtime-smoke.sh
```

The runtime smoke starts the same FastAPI app with deployed-style `POC_DB_PATH`, runs the API verifier against that runtime, and confirms tenant, model-quality, and usage records were written to the mounted-data analogue.

If Docker is available, the same files can be run with:

```sh
docker compose -f project/deployment/docker-compose.yml up --build
```
