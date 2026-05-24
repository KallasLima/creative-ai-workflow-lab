# Delivery Plan

This plan assumes 2 full-stack engineers using modern AI-assisted development tools for scaffolding, fixtures, tests, documentation, and review support. Human engineers retain ownership of architecture, security, integration, and release decisions.

## Weeks 1-2

- Lock API contracts for selection, generation, localization, image jobs, apply events, and reporting.
- Build the Figma plugin shell and local backend session exchange.
- Add deterministic fixtures and contract tests.
- Prove one end-to-end local flow.

## Weeks 3-4

- Add brand profile storage, PDF ingestion, profile review states, and prompt versioning.
- Build copy and localization flows against the provider gateway.
- Add usage, cost, and audit records.

## Weeks 5-6

- Add asynchronous image placeholder jobs.
- Add private asset metadata and safe preview/apply behavior.
- Expand Figma edge-case coverage for locked, hidden, unsupported, and mixed-style layers.

## Weeks 7-8

- Harden auth, tenant isolation, quotas, monitoring, and retry behavior.
- Add pilot reporting and operational runbooks.
- Run security and privacy review.

## Weeks 9-10

- Pilot with a small group.
- Validate quality, latency, adoption, apply rate, and unit economics.
- Fix expansion blockers or cut scope before broader rollout.

## Cut Order

Cut admin polish, advanced analytics, self-service tenant onboarding, and image breadth before cutting auth, tenant isolation, usage metering, audit trails, or profile governance.
