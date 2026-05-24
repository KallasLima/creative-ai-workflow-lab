# Architecture

This document expands the production architecture summarized in [Reviewer Architecture Plan](reviewer-architecture-plan.md). The local prototype demonstrates these boundaries, but the architecture below is for the deployed product.

## System Boundary

The product has 3 major surfaces:

- **Figma plugin:** designer interaction, selected-layer context, preview, apply actions, and lightweight status UI.
- **Workflow backend:** SSO/session exchange, tenant and brand policy, brand profiles, model gateway, image jobs, usage, cost, audit, reporting, and operational controls.
- **Provider and storage layer:** text/image model providers, queue workers, Postgres, object storage, and observability.

The plugin must stay thin. Provider credentials, tenant isolation, brand rules, prompt templates, cost attribution, and audit records belong on the backend.

## Core Flow

1. A designer selects supported text and image-fill layers in Figma.
2. The plugin starts a backend-owned SSO/OAuth handoff and receives a short-lived plugin session.
3. The plugin sends selected layer metadata, text, target locales, and image dimensions to the backend.
4. The backend validates tenant, brand, user role, quota, feature flag, operation type, and approved profile.
5. Copy and localization requests go through the model gateway with the approved brand profile, glossary, locale rules, and structured output schema.
6. Image replacement requests create asynchronous image jobs with policy checks, provider routing, and tenant-scoped asset storage.
7. The plugin previews output and applies only the chosen result back to Figma.
8. The backend records generation, usage, cost, apply, and audit events.

For the sequence diagram, see [Production Data Flow](reviewer-architecture-plan.md#3-production-data-flow-localize-copy-and-replace-images).

## Backend Responsibilities

- SSO/OAuth or PKCE-style plugin session exchange.
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
| Figma plugin | Reads selection, previews output, applies selected copy or image fills. |
| API service | Owns auth, contracts, policy checks, profile lookup, model orchestration, usage, and audit writes. |
| Postgres | Stores tenants, users, brands, profiles, operations, usage, apply events, audit events, quotas, and provider metadata. |
| Object storage | Stores uploaded brand materials, generated image assets, and optional approved reference assets. |
| Queue workers | Process image jobs, PDF/profile extraction, provider retries, and slow model work. |
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

Tenant isolation failures, provider credential exposure, missing usage writes, and missing audit writes should block release.

## Scaling Path

For 100+ concurrent users across multiple tenants:

- API services scale horizontally behind a load balancer.
- Postgres uses tenant-aware indexes for user/brand/reporting queries.
- Queue workers scale separately from the API for image and extraction jobs.
- Object storage keeps generated images and brand materials out of the relational database.
- Provider quotas and backpressure prevent 1 tenant or brand from consuming all capacity.
- Plugin/backend contract versioning reduces rollout risk across multiple customer workspaces.

The production roadmap and effort model are detailed in [Reviewer Architecture Plan](reviewer-architecture-plan.md#5-phased-roadmap).
