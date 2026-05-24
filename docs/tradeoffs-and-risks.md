# Tradeoffs And Risks

This document expands the trade-off matrix in [Reviewer Architecture Plan](reviewer-architecture-plan.md#4-technology-choices-and-trade-offs).

## Figma Plugin Over Web App

The workflow belongs where designers already work. A Figma plugin can read selection context and apply outputs directly to the canvas. A standalone web app would be easier to build, but it would lose the strongest product value: editing Figma designs without switching tools.

Mitigation: keep the plugin thin and put auth, policy, provider calls, metering, audit, and persistence in the backend.

## Backend-Owned Model Calls

The plugin should never own provider credentials or enforce final policy locally. Backend-owned model calls make tenant access, brand profile selection, cost attribution, quotas, provider routing, and audit records enforceable.

Trade-off: the backend is more complex than a plugin-only implementation.

Mitigation: start with narrow contracts and a model gateway; avoid leaking provider-specific logic into the plugin.

## Approved Brand Profiles

Brand guidelines are often messy PDFs, decks, docs, websites, and informal rules. The product should convert them into reviewed, versioned brand profiles before they affect generation.

Trade-off: human approval slows onboarding.

Mitigation: use draft profile extraction to speed setup, but require approval before runtime use. Track profile versions and support rollback.

## Reference Images For Image Generation

Reference images can make output more brand-specific by preserving product shape, palette, composition, logo placement, or campaign style. Candidate provider APIs could include Nano Banana 2, the popular name for Google's Gemini 3.1 Flash Image model, or GPT-Image-2 from OpenAI, assuming those names and terms are approved at implementation time.

Trade-off: reference images introduce rights, consent, privacy, retention, tenant-isolation, provider-training, and brand-safety risk. They also increase cost, latency, and review burden.

Mitigation: keep arbitrary reference-image upload out of MVP. Start with approved visual notes and selected-layer context. Add reference images later only through a governed brand asset library with consent metadata, retention rules, provider allow/deny routing, and tenant-scoped storage.

## Async Image Jobs

Image generation is slower and riskier than text. It can be rate-limited, policy-gated, or expensive, and it often needs retries and asset storage.

Trade-off: designers wait for images.

Mitigation: keep copy/localization synchronous, make image jobs asynchronous, show clear job states, and notify when results are ready.

## Production Model Providers

Production providers are needed to validate output quality with customer brands and designers.

Trade-off: provider behavior can drift, costs can spike, and latency can vary.

Mitigation: route all provider calls through the model gateway, record model metadata, run golden-sample evaluation, track provider cost and latency, and maintain fallback options.

## Main Risks

| Risk | Mitigation |
| --- | --- |
| Poor generated output quality | Golden samples, prompt evaluation, feedback taxonomy, reviewed profile versions, and rollback. |
| Cross-tenant leakage | Backend tenant checks on every route, tenant-scoped storage, audit tests, and security review. |
| Cost surprises | Usage events, quotas, provider routing, cost-per-applied-output reporting. |
| Figma platform edge cases | Support a narrow set of layer types first; clearly reject unsupported layers. |
| Provider latency hurts UX | Keep text fast, make image generation async, monitor provider latency and queue age. |
| Overbuilt MVP | Cut breadth before cutting auth, tenant isolation, usage, audit, or profile governance. |
