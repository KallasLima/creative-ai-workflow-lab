# Architecture

The system is a Figma-native creative workflow with a thin plugin and a backend trust boundary.

The plugin owns the designer interaction: selected layers, preview, apply, and local UI state. The backend owns policy and durable records: session validation, tenant and brand access, approved brand profiles, model calls, image jobs, usage, cost, and audit trails.

## Core Flow

1. A designer selects supported text and image-fill layers in Figma.
2. The plugin normalizes the selection and calls the backend.
3. The backend validates the session, tenant, brand, operation, and active profile.
4. Copy and localization return structured preview options.
5. Image placeholder creation runs as an asynchronous job.
6. The designer applies a chosen output.
7. The backend records operation, usage, apply, and audit events.

## Backend Responsibilities

- Session exchange and token validation.
- Tenant and brand authorization.
- Approved profile lookup for prompt context.
- Provider gateway abstraction for copy, localization, and image work.
- PDF extraction into reviewed brand profile drafts.
- Usage and cost metering.
- Audit records for generation and apply events.
- Reporting endpoints for workflow health and usage.

## Production Shape

The local prototype uses FastAPI, SQLite, and deterministic providers. A production version would keep the same boundaries while replacing local components with managed equivalents:

- SQLite to Postgres.
- Local file assets to private object storage.
- Deterministic provider to a model gateway.
- Local polling to queue workers.
- Local deterministic credentials to OAuth/PKCE or SSO-backed plugin sessions.

The key design choice is that generated content never bypasses backend policy, metering, or audit controls.

In production, the plugin would start a backend-owned OAuth/PKCE handoff, the browser would complete SSO, and the backend would exchange the verifier for a scoped plugin session. The local implementation keeps that same start/exchange/token boundary so the plugin never stores provider credentials and every model operation is tied back to a user, tenant, brand, and profile.

## Availability And Release Shape

The production target is 99% availability for the MVP workflow and a release process that can ship or roll back a change in less than 12 hours.

The architecture supports that target by keeping the plugin thin, backend APIs versioned, and long-running image work asynchronous. A normal release can deploy backend and plugin changes behind feature flags, verify `/health`, run contract smoke checks, and roll back by disabling the flag or redeploying the previous backend image. Generated assets, usage events, and audit records are durable backend data, so a plugin UI rollback does not erase operational evidence.

For scaling, stateless API instances sit behind a load balancer, Postgres owns transactional records, object storage owns generated assets and uploaded guidelines, and queue workers absorb image/PDF spikes. The local prototype keeps those boundaries explicit even though it runs on one machine.
