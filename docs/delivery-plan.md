# Delivery Plan

This document expands the roadmap in [Reviewer Architecture Plan](reviewer-architecture-plan.md#5-phased-roadmap). It is a production delivery plan for the deployed product, not a plan for the local prototype.

## Team Model

The MVP is sized for 2 full-stack engineers over 10 weeks, with AI coding agents such as Codex or Claude Code used to accelerate scaffolding, fixtures, tests, documentation, and review loops.

- Engineer 1: TypeScript Figma plugin UX, selected-layer handling, auth handoff UI, OpenAPI-generated API client, preview/apply states, plugin packaging, and Figma edge cases.
- Engineer 2: Python/FastAPI backend, OIDC/PKCE session exchange, Postgres tenant/brand policy, brand profile ingestion, model gateway, image jobs, usage/cost/audit, deployment, and monitoring.
- Shared: contracts, data model, security review, release gates, pilot metrics, quality evaluation, incident runbooks.

The team should keep OpenAPI as the contract source. Backend changes update the OpenAPI schema; the plugin consumes a generated TypeScript client. That avoids a 2-engineer team manually synchronizing payloads across Python and TypeScript.

## MVP: Weeks 1-10

### Weeks 1-2: Contracts And Skeleton

- Lock API contracts for auth/session exchange, selection, copy, localization, image jobs, apply events, usage reports, and errors.
- Build the TypeScript Figma plugin shell with selected-node parsing for text and image-fill nodes.
- Create the Python/FastAPI backend skeleton with app factory, route groups, service modules, error envelope, structured logging, and OpenAPI generation.
- Implement OIDC/PKCE-shaped plugin session handoff using a local/dev identity provider first, with the same route contract production will keep.
- Create the first Postgres migration set for `tenants`, `users`, `tenant_memberships`, `figma_workspaces`, `brands`, `brand_profiles`, `operations`, `usage_events`, `apply_events`, and `audit_events`.
- Add contract tests that fail if a route can access brand data without `tenant_id`.

### Weeks 3-4: Brand Profiles And Text Workflows

- Add repository functions that always require `tenant_id`; prohibit unscoped lookups in code review.
- Add brand guideline ingestion from PDFs/docs into draft profile versions.
- Add human profile approval, active-profile lookup, and rollback basics.
- Implement copy generation and localization through the model gateway.
- Record usage, model metadata, estimated cost, and audit rows.
- Add golden-sample evaluation for copy/localization with profile version and prompt template version recorded.

### Weeks 5-6: Image Jobs And Apply Events

- Add asynchronous image jobs, provider policy checks, queue workers, retries, and job states.
- Store image assets in tenant-scoped object storage keys: `tenants/{tenant_id}/brands/{brand_id}/assets/{asset_id}/...`.
- Record apply events after Figma canvas changes.
- Add image safety, rights metadata, and policy-block handling.
- Add worker-side revalidation so queued jobs cannot bypass tenant, brand, profile, quota, or provider policy checks.

### Weeks 7-8: Governance And Operations

- Harden SSO/session exchange, tenant isolation, quotas, feature flags, and provider routing.
- Add monitoring for latency, provider errors, queue age, image completion, usage writes, and audit writes.
- Add pilot reporting for adoption, apply rate, cost per applied output, and quality review.
- Run security and privacy review.
- Add synthetic checks for auth exchange, profile lookup, queue enqueue, provider mock/fallback, usage write, and audit write.

### Weeks 9-10: Pilot Readiness

- Pilot with a small group of designers and customer brands.
- Validate copy quality, localization quality, latency, adoption, apply rate, unit economics, and operational alerts.
- Fix expansion blockers or cut scope before broader rollout.
- Document rollback, provider outage, bad-output, tenant-access, and image-job failure runbooks.
- Freeze plugin/backend contract version for the pilot and keep the previous backend image deployable for rollback.

## Beta: Next 3 Months

- Expand to several teams or brands.
- Add better profile review UX, feedback capture, and profile rollback.
- Add quota controls and cost dashboards.
- Evaluate provider quality using pilot examples and designer feedback.
- Decide whether governed brand asset/reference-image libraries are worth adding.
- Tighten runbooks and support paths for production incidents.

## Full Rollout: 12+ Months

- Expand to a multi-tenant platform licensed to several companies.
- Support 100+ concurrent users through stateless APIs, queues, object storage, provider backpressure, and quotas.
- Add enterprise SSO, user provisioning, audit exports, retention policy, admin controls, and billing exports.
- Add provider allow/deny policies and optional governed reference-image workflows.
- Maintain versioned plugin/backend contracts to reduce rework across customer rollouts.

## Release And Availability Plan

- Deploy backend changes through container images with `/health`, smoke checks, and contract tests.
- Release plugin behavior behind backend feature flags when API behavior changes.
- Preserve previous backend images and old plugin-compatible contracts for rollback.
- Keep rollback under 12 hours for the MVP workflow.
- Treat tenant isolation failures, provider credential exposure, missing usage writes, and missing audit writes as release blockers.

Release gates:

- A request from tenant A cannot read, list, generate against, or apply output for tenant B.
- A provider call cannot run without operation id, tenant id, brand id, profile version id, and user id.
- A generated asset cannot be served unless the requesting session can access its tenant and brand.
- Every successful model operation creates usage and audit records.
- Every plugin apply action creates an apply event tied to the original operation.
- A rollback can disable the feature flag or redeploy the previous backend image without orphaning plugin clients.

## Cut Order

Cut these first:

- self-service tenant onboarding,
- advanced analytics,
- complex admin workflow polish,
- broad image styles,
- multiple image providers,
- polished billing UI,
- support for every Figma node type.

Do not cut:

- tenant isolation,
- provider credential protection,
- usage metering,
- audit trail,
- approved brand profile governance,
- apply-event tracking,
- SSO/session security,
- basic monitoring and rollback.
