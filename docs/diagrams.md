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

## Tenant Enforcement Path

```mermaid
flowchart TD
  Request["Plugin request"] --> Session["Resolve plugin token"]
  Session --> Claims["tenant_id, user_id, roles, figma workspace claims"]
  Claims --> RouteGuard["Route guard checks requested tenant"]
  RouteGuard --> Repo["Repository methods require tenant_id"]
  Repo --> DB[("Postgres rows include tenant_id")]
  RouteGuard --> Queue["Queue job carries tenant_id + brand_id + operation_id"]
  Queue --> Worker["Worker revalidates tenant, brand, profile, quota"]
  Worker --> Provider["Provider gateway call"]
  Worker --> Storage["Object key: tenants/{tenant_id}/brands/{brand_id}/..."]
  Storage --> SignedUrl["Signed URL only after tenant access check"]
```

## Production Data Model Sketch

```mermaid
erDiagram
  TENANTS ||--o{ TENANT_MEMBERSHIPS : has
  USERS ||--o{ TENANT_MEMBERSHIPS : joins
  TENANTS ||--o{ FIGMA_WORKSPACES : maps
  TENANTS ||--o{ BRANDS : owns
  BRANDS ||--o{ BRAND_PROFILES : versions
  TENANTS ||--o{ OPERATIONS : scopes
  BRANDS ||--o{ OPERATIONS : scopes
  OPERATIONS ||--o{ USAGE_EVENTS : records
  OPERATIONS ||--o{ APPLY_EVENTS : adopted_by
  OPERATIONS ||--o{ IMAGE_JOBS : may_create
  IMAGE_JOBS ||--o| ASSETS : produces
  TENANTS ||--o{ AUDIT_EVENTS : records
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

The important implementation detail is that workers do not trust queued payloads. They reload tenant, brand, profile, quota, and provider policy before calling the model gateway.

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

Only `Approved Profile Version` can be used at runtime. Draft profile output from extraction is not generation context until a human reviewer approves it.
