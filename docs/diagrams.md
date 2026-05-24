# Diagrams

These diagrams support [Reviewer Architecture Plan](reviewer-architecture-plan.md). They describe the production architecture; the local prototype is a small runnable slice of the same boundaries.

## System Context

```mermaid
flowchart LR
  Designer["Designer in Figma"] --> Plugin["Figma Plugin"]
  Plugin --> API["Deployed Workflow API"]
  API --> Auth["SSO / OAuth"]
  API --> Policy["Tenant + Brand Policy"]
  API --> Profile["Brand Profile Service"]
  API --> Gateway["Model Gateway"]
  API --> Queue["Image / Extraction Queues"]
  API --> DB[("Postgres")]
  API --> Storage["Object Storage"]
  API --> Reports["Usage, Cost, Audit Reports"]
  Gateway --> TextProvider["Text Model Provider"]
  Gateway --> ImageProvider["Image Model Provider"]
  Queue --> Gateway
  Queue --> Storage
```

## Production Runtime Flow

```mermaid
sequenceDiagram
  participant D as Designer
  participant P as Figma Plugin
  participant B as Backend API
  participant A as SSO/OAuth
  participant G as Model Gateway
  participant Q as Queue Worker
  participant S as Object Storage
  participant U as Usage/Audit

  D->>P: Select text and image layers
  P->>B: Start plugin session
  B->>A: Verify user and workspace claims
  A-->>B: Identity and access claims
  B-->>P: Short-lived plugin session
  P->>B: Request localization and image replacement
  B->>B: Validate tenant, brand, profile, quota, locale, layer type
  B->>G: Generate localized copy
  G-->>B: Structured copy candidates
  B->>U: Record generation usage and cost
  B-->>P: Return preview
  D->>P: Apply selected copy
  P->>B: Record apply event
  B->>U: Record apply audit
  P->>B: Create image job
  B->>Q: Enqueue provider-routed image job
  Q->>G: Call image provider
  Q->>S: Store tenant-scoped asset
  Q->>U: Record image usage, cost, policy metadata
  P->>B: Poll or subscribe to job status
  B-->>P: Return preview URL and metadata
  D->>P: Apply image fill
  P->>B: Record image apply event
```

## Image Job State

```mermaid
stateDiagram-v2
  [*] --> Submitted
  Submitted --> PolicyBlocked: rights/safety/provider policy fails
  Submitted --> Queued: accepted
  Queued --> Running
  Running --> Completed: asset stored
  Running --> Failed: provider error or timeout
  Failed --> Queued: retry allowed
  Completed --> Applied: designer applies asset
  PolicyBlocked --> [*]
  Applied --> [*]
```

## Brand Profile Lifecycle

```mermaid
flowchart TD
  Upload["Upload brand guideline PDF/doc"] --> Extract["Extract draft rules"]
  Extract --> Draft["Draft Brand Profile"]
  Draft --> Review["Human brand/admin review"]
  Review --> Approved["Approved Profile Version"]
  Approved --> Runtime["Runtime prompt context"]
  Approved --> Rollback["Rollback candidate"]
  Runtime --> Feedback["Designer feedback + quality review"]
  Feedback --> Draft
```
