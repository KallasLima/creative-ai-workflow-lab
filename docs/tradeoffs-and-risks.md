# Tradeoffs And Risks

This document expands the trade-off matrix in [Reviewer Architecture Plan](reviewer-architecture-plan.md#4-technology-choices-and-trade-offs).

## Figma Plugin Over Web App

The workflow belongs where designers already work. A Figma plugin can read selection context and apply outputs directly to the canvas. A standalone web app would be easier to build, but it would lose the strongest product value: editing Figma designs without switching tools.

Mitigation: keep the plugin thin and put auth, policy, provider calls, metering, audit, and persistence in the backend.

## Backend-Owned Model Calls

The plugin should never own provider credentials or enforce final policy locally. Backend-owned model calls make tenant access, brand profile selection, cost attribution, quotas, provider routing, and audit records enforceable.

Trade-off: the backend is more complex than a plugin-only implementation.

Mitigation: start with narrow contracts and a model gateway; avoid leaking provider-specific logic into the plugin.

Implementation detail: the plugin sends layer metadata and text, not provider prompts. The backend assembles prompts from approved profile version, prompt template version, locale rules, and provider policy. That is what makes provider changes and prompt fixes possible without publishing a new plugin.

## Python/FastAPI Backend Instead Of TypeScript Backend

Python/FastAPI is the recommended backend stack because the hard backend problems are model orchestration, PDF extraction, provider evaluation, background jobs, and typed API contracts. Python has better mature libraries for those tasks, and FastAPI/Pydantic generates OpenAPI schemas that the TypeScript plugin can consume.

Trade-off: the system uses TypeScript in the plugin and Python in the backend, so engineers must maintain cross-language contracts.

Mitigation: make OpenAPI the contract source. Add generated TypeScript client code, contract tests, and CI checks that fail when backend schema changes are not reflected in plugin types.

## Shared Multi-Tenant Database Instead Of Per-Tenant Deployments

A shared Postgres database with tenant-scoped rows is the recommended MVP/Beta model. Per-tenant deployments sound safer, but they multiply operational work, make provider governance harder, and are too slow for a 2-engineer 10-week MVP.

Trade-off: shared tenancy requires rigorous enforcement.

Mitigation: every customer-owned table includes `tenant_id`; brand-owned rows include `brand_id`; repository functions require tenant scope; object storage keys include tenant prefixes; queue payloads carry tenant and brand ids; audit tests prove tenant A cannot access tenant B.

## Redis Queue First Instead Of Full Event Platform

Redis-backed queues are enough for MVP image jobs, profile extraction, and provider retries. A full event streaming platform is premature unless the product needs high-volume integration events or replay across services.

Trade-off: Redis queues are less expressive than a mature event bus and need care around retries and dead-letter handling.

Mitigation: define a queue interface, explicit job states, retry count, next retry time, dead-letter reason, and operation id from day 1. Move to SQS, Cloud Tasks, Pub/Sub, or another managed queue later without changing plugin contracts.

## Approved Brand Profiles

Brand guidelines are often messy PDFs, decks, docs, websites, and informal rules. The product should convert them into reviewed, versioned brand profiles before they affect generation.

Trade-off: human approval slows onboarding.

Mitigation: use draft profile extraction to speed setup, but require approval before runtime use. Track profile versions and support rollback.

Implementation detail: runtime generation should never read “latest draft.” It reads a specific approved `profile_version_id` from the brand's active profile pointer. Historical operations keep their original profile version so generated output remains explainable.

## Reference Images For Image Generation

Reference images can make output more brand-specific by preserving product shape, palette, composition, logo placement, or campaign style. Candidate provider APIs could include Nano Banana 2, the popular name for Google's Gemini 3.1 Flash Image model, or GPT-Image-2 from OpenAI, assuming those names and terms are approved at implementation time.

Trade-off: reference images introduce rights, consent, privacy, retention, tenant-isolation, provider-training, and brand-safety risk. They also increase cost, latency, and review burden.

Mitigation: keep arbitrary reference-image upload out of MVP. Start with approved visual notes and selected-layer context. Add reference images later only through a governed brand asset library with consent metadata, retention rules, provider allow/deny routing, and tenant-scoped storage.

## Async Image Jobs

Image generation is slower and riskier than text. It can be rate-limited, policy-gated, or expensive, and it often needs retries and asset storage.

Trade-off: designers wait for images.

Mitigation: keep copy/localization synchronous, make image jobs asynchronous, show clear job states, and notify when results are ready.

Implementation detail: an image job moves through `submitted`, `policy_blocked`, `queued`, `running`, `completed`, `failed`, and `applied`. The worker revalidates tenant, brand, profile, quota, and provider policy before calling an image model. Completed assets are served through signed URLs after tenant access checks.

## Production Model Providers

Production providers are needed to validate output quality with customer brands and designers.

Trade-off: provider behavior can drift, costs can spike, and latency can vary.

Mitigation: route all provider calls through the model gateway, record model metadata, run golden-sample evaluation, track provider cost and latency, and maintain fallback options.

## Main Risks

| Risk | Mitigation |
| --- | --- |
| Poor generated output quality | Golden samples, prompt evaluation, feedback taxonomy, reviewed profile versions, and rollback. |
| Cross-tenant leakage | Backend tenant checks on every route, tenant-leading database indexes, tenant-scoped storage keys, worker-side revalidation, audit tests, and security review. |
| Cost surprises | Usage events, quotas, provider routing, cost-per-applied-output reporting. |
| Figma platform edge cases | Support a narrow set of layer types first; clearly reject unsupported layers. |
| Provider latency hurts UX | Keep text fast, make image generation async, monitor provider latency and queue age. |
| Overbuilt MVP | Cut breadth before cutting auth, tenant isolation, usage, audit, or profile governance. |
| Contract drift between plugin and backend | Use OpenAPI-generated TypeScript clients and contract tests as release gates. |
