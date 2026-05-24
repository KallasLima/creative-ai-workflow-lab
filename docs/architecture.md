# Architecture

This document expands the production architecture summarized in [Reviewer Architecture Plan](reviewer-architecture-plan.md). The local prototype demonstrates the boundaries, but the architecture below is the production implementation shape.

## Recommended Stack

| Layer | Recommendation | Why This Way |
| --- | --- | --- |
| Figma plugin | TypeScript, Figma Plugin API, HTML/CSS UI, OpenAPI-generated API client | Figma plugins run in a JavaScript sandbox. TypeScript gives safer layer parsing and keeps plugin/backend contracts typed. |
| Backend API | Python 3.12, FastAPI, Pydantic, SQLAlchemy or SQLModel, Alembic | The workflow is API-heavy, model-provider-heavy, and document-extraction-heavy. Python has strong AI/PDF tooling; FastAPI gives typed OpenAPI contracts quickly for 2 engineers. |
| Workers | Python worker processes using the same service modules as the API | Image generation, PDF extraction, model evaluation, and retries need the same brand policy and provider gateway code as the API. |
| Database | Postgres | Tenant, user, brand, profile, operation, usage, apply, audit, quota, and provider metadata need relational consistency and reporting queries. |
| Queue | Redis-backed queue for MVP, managed queue later if cloud platform supports it cleanly | MVP needs async jobs and retries without overbuilding. The abstraction should allow moving to SQS, Cloud Tasks, Pub/Sub, or another managed queue later. |
| Object storage | S3-compatible bucket or cloud-native equivalent | Generated images, source guidelines, and optional reference assets should not live in Postgres. |
| Auth | OIDC for MVP, SAML/SCIM added for enterprise rollout | OIDC is the fastest secure pilot path. SAML and provisioning matter for enterprise customers later. |
| Observability | OpenTelemetry traces, structured JSON logs, metrics, alerts | Provider latency, queue age, usage writes, audit writes, and tenant-boundary failures need operational visibility. |
| Contracts | OpenAPI as source of truth, generated TypeScript client for plugin | This keeps 2 engineers from hand-maintaining request/response shapes in 2 languages. |
| Deployment | Containerized API and workers behind HTTPS, managed Postgres, managed Redis/queue, managed object storage | Keeps MVP deployable without hand-managed infrastructure and leaves a path to scale. |

The local prototype uses Python/FastAPI, SQLite, and deterministic providers because it must run locally and free. Production keeps Python/FastAPI for the backend, but replaces SQLite with Postgres, local placeholder storage with object storage, deterministic providers with approved model providers, and local auth with OIDC/SAML-backed plugin sessions.

## System Boundary

The product has 3 major surfaces:

- **Figma plugin:** designer interaction, selected-layer context, preview, apply actions, and lightweight status UI.
- **Workflow backend:** session exchange, tenant and brand policy, brand profiles, model gateway, image jobs, usage, cost, audit, reporting, and operational controls.
- **Provider and storage layer:** text/image model providers, queue workers, Postgres, object storage, and observability.

The plugin is deliberately thin. It does not enforce final authorization, store provider keys, own prompt templates, persist brand policy, calculate billable usage, or decide provider routing. It reads the Figma selection, sends the minimum layer context needed for a request, previews backend-approved results, applies the designer's chosen result, and records the apply event.

## Core Flow

1. A designer selects supported text and image-fill layers in Figma.
2. The plugin starts a backend-owned OIDC/PKCE handoff and receives a short-lived plugin session.
3. The plugin sends selected layer metadata, text, target locales, image dimensions, file key, page/node ids, and request idempotency key to the backend.
4. The backend resolves the session to `tenant_id`, `user_id`, roles, and allowed Figma workspace/file claims.
5. The backend validates tenant, brand, user role, quota, feature flag, operation type, locale, layer type, and approved profile version.
6. Copy and localization requests go through the model gateway with the approved brand profile, glossary, locale rules, structured output schema, and prompt template version.
7. Image replacement requests create asynchronous image jobs with policy checks, provider routing, queue state, tenant-scoped asset storage, and retry metadata.
8. The plugin previews output and applies only the chosen result back to Figma.
9. The backend records generation, usage, cost, apply, and audit events. Generated-but-not-applied output remains visible in usage but does not count as adopted output.

For the sequence diagram, see [Production Data Flow](reviewer-architecture-plan.md#3-production-data-flow-localize-copy-and-replace-images).

## Multi-Tenancy: How It Works

The product should use a shared application and shared database with strict tenant scoping, not one deployment per customer. Separate deployments would slow onboarding and make shared provider governance harder. The shared model is safe only if tenant isolation is enforced at every layer.

### Tenant Identity Model

Core relational objects:

| Entity | Key Fields | Purpose |
| --- | --- | --- |
| `tenants` | `tenant_id`, name, status, plan, data retention policy | Customer workspace boundary. |
| `users` | `user_id`, external subject, email, status | Human identity after OIDC/SAML login. |
| `tenant_memberships` | `tenant_id`, `user_id`, role, status | User access to one tenant. |
| `figma_workspaces` | `tenant_id`, Figma team/workspace id | Connects Figma context to tenant policy. |
| `brands` | `tenant_id`, `brand_id`, name, active profile version | Brand boundary within tenant. |
| `brand_profiles` | `tenant_id`, `brand_id`, `profile_version_id`, status, version | Approved generation context. |
| `operations` | `tenant_id`, `brand_id`, `user_id`, operation type, status | Generation request record. |
| `usage_events` | `tenant_id`, `brand_id`, `user_id`, provider, cost, units | Cost and adoption reporting. |
| `audit_events` | `tenant_id`, actor, action, object type/id, metadata | Compliance and investigation trail. |
| `assets` | `tenant_id`, `brand_id`, asset id, storage key, policy metadata | Generated images and uploaded guideline assets. |

Every table that contains customer data includes `tenant_id`. Brand-scoped tables include both `tenant_id` and `brand_id` to avoid relying on globally unique brand ids. Joins always include tenant predicates, for example `WHERE tenant_id = :session_tenant_id AND brand_id = :requested_brand_id`.

### Tenant Enforcement Points

1. **Session creation:** OIDC/SAML login resolves identity into tenant memberships. The plugin token receives tenant and role claims, but the backend still reloads permissions on every request.
2. **Request validation:** Every route accepts or derives `tenant_id`. The backend compares it to the authenticated session and rejects mismatches before business logic runs.
3. **Repository layer:** Data access functions require `tenant_id` as an explicit parameter. There should be no repository method such as `get_brand(brand_id)` without tenant scope.
4. **Database constraints:** Foreign keys include tenant scope where practical. Indexes use tenant-leading keys such as `(tenant_id, brand_id, profile_version_id)`.
5. **Object storage:** Keys are tenant scoped: `tenants/{tenant_id}/brands/{brand_id}/assets/{asset_id}/original.png`. Signed URLs are generated only after a tenant authorization check.
6. **Queue payloads:** Jobs carry `tenant_id`, `brand_id`, `user_id`, and `operation_id`. Workers re-check tenant/brand/profile state before calling a provider.
7. **Provider gateway:** Provider calls receive tenant, brand, profile, operation, and policy metadata for logging, cost attribution, and routing. Provider credentials are never tenant-provided in MVP unless an enterprise tenant explicitly brings its own key later.
8. **Reporting:** Reports aggregate within one tenant by default. Cross-tenant internal reports require an internal admin role and should never expose source prompts or assets unless explicitly permitted.

### Why Shared DB With Tenant Scope

This is the right MVP and Beta choice because it supports several companies without duplicating infrastructure. It also lets the team compare provider cost, latency, and quality across tenants while keeping customer data partitioned by access control. The trade-off is that tenant scoping must be boringly consistent. To reduce human error, tenant checks belong in reusable dependencies/middleware, repository signatures, tests, and database indexes, not in scattered route code.

### Tenant Failure Modes

Release should be blocked if any of these are true:

- a route can read or mutate a brand without `tenant_id`,
- an object-storage key omits tenant scope,
- a queue job can run without tenant and brand ids,
- a report can aggregate across tenants without internal admin permission,
- a provider request log stores raw prompts without tenant-scoped retention controls,
- audit events omit tenant id, actor, object type, or action.

## Auth And Plugin Session Exchange

Figma plugins cannot safely hold long-lived provider credentials or enterprise identity tokens. The plugin should use a browser-based auth handoff:

1. Plugin calls `POST /auth/plugin/start` with plugin version, contract version, local nonce, and PKCE code challenge.
2. Backend creates an auth request and returns a browser URL.
3. User completes OIDC login in the browser. Enterprise rollout can add SAML through the identity provider while keeping the plugin contract unchanged.
4. Backend validates identity, Figma workspace mapping, tenant membership, and role.
5. Plugin calls `POST /auth/plugin/exchange` with nonce, state, and PKCE verifier.
6. Backend returns a short-lived plugin access token, for example 30-60 minutes, scoped to tenant, user, roles, and allowed operations.
7. Refresh requires another backend-validated exchange or silent browser session check; provider keys never leave the backend.

This is more work than hardcoded plugin auth, but it prevents the most damaging shortcut: a plugin with durable provider credentials and no revocation path.

## Brand Profile Lifecycle

Brand profiles are backend-owned product objects, not Figma styles. A Figma style can help with typography or colors, but it cannot represent tone, banned claims, locale rules, safety constraints, provider routing, retention policy, or approval status.

Lifecycle:

1. A brand owner uploads guidelines as PDFs/docs or enters structured notes.
2. A backend extraction job creates a draft profile: tone, glossary, forbidden terms, locale rules, visual notes, example prompts, and risk flags.
3. A human reviewer approves, edits, or rejects the draft.
4. Only approved profile versions can be used at runtime.
5. Generation requests store `profile_version_id` and `prompt_template_version_id` so output can be reproduced or audited later.
6. New profile versions do not rewrite historical operations. Rollback means switching the brand's active profile pointer.

This is important because without versioned profile ids, the team cannot answer “which brand rules produced this output?” after a customer challenges a generated line or image.

## Model Gateway

The model gateway is an internal service boundary, not necessarily a separate microservice on day 1. It should be a backend module with a clear interface:

```text
generate_copy(tenant_id, brand_id, profile_version_id, prompt_template_version_id, layer_context, locale_context) -> structured candidates
generate_image(operation_id, profile_version_id, provider_policy, dimensions, prompt, optional_reference_asset_id) -> asset candidate
evaluate_samples(provider_id, model_id, sample_set_id) -> quality score
```

The gateway owns:

- provider-specific request/response normalization,
- model and prompt version metadata,
- retries and fallback rules,
- safety and rights metadata,
- cost estimate normalization,
- latency/error metrics,
- golden-sample evaluation,
- provider allow/deny policy per tenant or brand.

The plugin never knows whether the backend used one provider, another provider, or a fallback. This keeps provider changes from requiring plugin releases.

## Image Generation Governance

Image generation is higher risk than text because it can create assets that look final, include rights-sensitive material, or accidentally reuse a protected mark. The MVP should allow image placeholders or ideation assets only.

Production flow:

1. API validates layer type and dimensions before queueing.
2. Policy check blocks public figures, protected marks, publication-ready claims, sensitive claims, and unsupported reference assets.
3. Accepted requests create an `image_jobs` row with state `queued`.
4. Worker reloads tenant, brand, profile, provider policy, quota, and prompt metadata.
5. Worker calls the model gateway and stores the result in tenant-scoped object storage.
6. Worker records usage, cost, policy metadata, provider metadata, and audit event.
7. Plugin previews the asset from a short-lived signed URL.
8. Designer applies the asset to Figma.
9. Plugin records the apply event. This is the adoption signal.

Reference images should not be arbitrary uploads in MVP. If added later, they should come from a governed brand asset library with rights metadata, consent, expiration, provider allow/deny routing, retention policy, and tenant-scoped storage. Candidate APIs could include Nano Banana 2/Gemini 3.1 Flash Image or GPT-Image-2 if those names and terms are approved at implementation time.

## Usage, Cost, And Audit

Usage and audit are not logs. They are product data.

Minimum usage event fields:

- `usage_event_id`
- `tenant_id`
- `brand_id`
- `user_id`
- `operation_id`
- `operation_type`
- `provider_id`
- `model_id`
- input/output units or image count
- estimated cost
- created timestamp

Minimum audit event fields:

- `audit_event_id`
- `tenant_id`
- actor user or system id
- action, such as `copy.generated`, `image.policy_blocked`, `profile.approved`, `output.applied`
- object type and id
- request id/correlation id
- metadata hash or redacted metadata
- created timestamp

Usage writes should happen in the same transactional boundary as operation state changes when possible. If a provider call succeeds but usage write fails, the operation should be marked `usage_write_failed` and alerted. Silent cost loss is unacceptable because cost attribution is a core requirement.

## Backend Responsibilities

- OIDC/PKCE plugin session exchange and later SAML/SCIM enterprise expansion.
- Tenant, brand, user, role, locale, quota, and feature-flag authorization.
- Approved brand profile lookup for prompt context.
- Brand guideline ingestion into draft profile versions.
- Human approval, versioning, and rollback for brand profiles.
- Model gateway abstraction for copy, localization, and image providers.
- Async image job orchestration, retries, provider policy checks, and asset metadata.
- Usage and cost metering by user, tenant, brand, operation, provider, and applied output.
- Audit records for generation, apply events, policy blocks, profile changes, and admin actions.
- Reporting endpoints for workflow health, adoption, unit economics, and operational review.

## Production Components

| Component | Role |
| --- | --- |
| Figma plugin | Reads selection, previews output, applies selected copy or image fills, records apply events. |
| API service | Owns auth, contracts, policy checks, profile lookup, model orchestration, usage, and audit writes. |
| Postgres | Stores tenants, users, memberships, brands, profiles, operations, usage, apply events, audit events, quotas, and provider metadata. |
| Object storage | Stores uploaded brand materials, generated image assets, and optional approved reference assets under tenant-scoped keys. |
| Queue workers | Process image jobs, PDF/profile extraction, provider retries, quality evaluation, and slow model work. |
| Model gateway | Routes to approved text/image providers, records model metadata, applies policy and fallback rules. |
| Observability | Tracks health, latency, provider errors, queue age, image completion, cost anomalies, and audit write failures. |

## Availability And Release Shape

The production target is 99% availability for the MVP workflow and a release process that can ship or roll back a change in less than 12 hours.

The architecture supports that target by:

- keeping the plugin thin and backward-compatible,
- versioning backend API contracts,
- releasing risky behavior behind feature flags,
- keeping image/PDF/provider work asynchronous,
- preserving previous backend images for rollback,
- monitoring health, provider error rates, queue age, apply-event write success, and usage-report freshness.

The backend should expose at least:

- `/health/live`: process is alive,
- `/health/ready`: dependencies are reachable,
- `/contracts/version`: plugin-compatible contract versions,
- synthetic checks for auth exchange, profile lookup, queue enqueue, and usage/audit write paths.

Tenant isolation failures, provider credential exposure, missing usage writes, missing audit writes, and broken rollback path should block release.

## Scaling Path

For 100+ concurrent users across multiple tenants:

- API services scale horizontally behind a load balancer because session state is stored in signed tokens plus backend session records, not process memory.
- Postgres uses tenant-leading indexes such as `(tenant_id, brand_id)`, `(tenant_id, user_id)`, `(tenant_id, created_at)`, and `(tenant_id, operation_type, created_at)`.
- Queue workers scale separately from the API. Image jobs and PDF extraction have separate queues by Beta if image traffic starts starving profile ingestion.
- Object storage keeps generated images and brand materials out of the relational database.
- Provider quotas and backpressure prevent 1 tenant or brand from consuming all capacity.
- Plugin/backend contract versioning reduces rollout risk across multiple customer workspaces.

The production roadmap and effort model are detailed in [Reviewer Architecture Plan](reviewer-architecture-plan.md#5-phased-roadmap).
