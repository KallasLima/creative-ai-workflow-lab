# Delivery Plan

This document expands the roadmap in [Reviewer Architecture Plan](reviewer-architecture-plan.md#5-phased-roadmap). It is a production delivery plan for the deployed product, not a plan for the local prototype.

## Team Model

The MVP is sized for 2 full-stack engineers over 10 weeks, with AI coding agents such as Codex or Claude Code used to accelerate scaffolding, fixtures, tests, documentation, and review loops.

- Engineer 1: Figma plugin UX, selected-layer handling, auth handoff UI, API client, preview/apply states, plugin packaging, Figma edge cases.
- Engineer 2: deployed backend, SSO/session exchange, tenant and brand policy, brand profile ingestion, model gateway, image jobs, usage/cost/audit, deployment, monitoring.
- Shared: contracts, data model, security review, release gates, pilot metrics, quality evaluation, incident runbooks.

## MVP: Weeks 1-10

### Weeks 1-2: Contracts And Skeleton

- Lock API contracts for auth/session exchange, selection, copy, localization, image jobs, apply events, usage reports, and errors.
- Build the Figma plugin shell and backend session handoff.
- Create the deployed backend skeleton with health checks, logging, and environment configuration.
- Add contract tests and deterministic fixtures.

### Weeks 3-4: Brand Profiles And Text Workflows

- Add tenant, brand, user, role, and profile tables.
- Add brand guideline ingestion from PDFs/docs into draft profile versions.
- Add human profile approval, active-profile lookup, and rollback basics.
- Implement copy generation and localization through the model gateway.
- Record usage, model metadata, estimated cost, and audit rows.

### Weeks 5-6: Image Jobs And Apply Events

- Add asynchronous image jobs, provider policy checks, queue workers, retries, and job states.
- Store image assets in tenant-scoped object storage.
- Record apply events after Figma canvas changes.
- Add image safety, rights metadata, and policy-block handling.

### Weeks 7-8: Governance And Operations

- Harden SSO/session exchange, tenant isolation, quotas, feature flags, and provider routing.
- Add monitoring for latency, provider errors, queue age, image completion, usage writes, and audit writes.
- Add pilot reporting for adoption, apply rate, cost per applied output, and quality review.
- Run security and privacy review.

### Weeks 9-10: Pilot Readiness

- Pilot with a small group of designers and customer brands.
- Validate copy quality, localization quality, latency, adoption, apply rate, unit economics, and operational alerts.
- Fix expansion blockers or cut scope before broader rollout.
- Document rollback, provider outage, bad-output, tenant-access, and image-job failure runbooks.

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
