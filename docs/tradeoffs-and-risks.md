# Tradeoffs And Risks

## Figma Plugin Over Web App

The workflow belongs where designers already work. A Figma plugin can read selection context and apply outputs directly. A web app would be easier to build but would lose the strongest product value: editing the canvas without switching tools.

## Backend-Owned Model Calls

The plugin never owns provider credentials or final policy. Backend-owned calls make tenant access, brand profile selection, cost attribution, and audit records enforceable.

## Deterministic Local Providers

The local prototype uses deterministic providers so it can run for free and be verified repeatedly. The tradeoff is that it demonstrates integration shape, not live model quality.

## Async Image Jobs

Image generation is asynchronous because production image work can be slow, rate-limited, or policy-gated. The local prototype keeps this shape even though the placeholder returns quickly.

## Main Risks

- Poor generated output quality. Mitigation: golden samples, prompt evaluation, feedback taxonomy, and reviewed profile versions.
- Cross-tenant leakage. Mitigation: backend-side tenant checks on every operation and audit tests.
- Cost surprises. Mitigation: usage events, quotas, and cost reporting from day 1.
- Figma platform edge cases. Mitigation: fixture coverage for unsupported, locked, hidden, mixed-style, and image-fill layers.
- Overbuilt MVP. Mitigation: strict cut order and pilot-first rollout.
