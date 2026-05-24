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

The local proof uses FastAPI, SQLite, and deterministic providers. A production version would keep the same boundaries while replacing local components with managed equivalents:

- SQLite to Postgres.
- Local file assets to private object storage.
- Deterministic provider to a model gateway.
- Local polling to queue workers.
- Local auth fixtures to OAuth or SSO-backed plugin sessions.

The key design choice is that generated content never bypasses backend policy, metering, or audit controls.
