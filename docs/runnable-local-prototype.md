# Runnable Local Prototype

This document explains the local prototype that supports [Reviewer Architecture Plan](reviewer-architecture-plan.md). The prototype is evidence for the architecture boundaries; it is not the production delivery plan.

The local prototype has 3 layers:

- Figma development plugin.
- FastAPI backend with SQLite persistence.
- Browser fallback harness for repeatable verification.

## What It Demonstrates

- Plugin-shaped selection, preview, and apply flow.
- Backend-owned policy and brand profile lookup.
- Model-gateway-shaped copy and localization calls.
- Async image job lifecycle.
- Usage and audit records.
- Local verification scripts.

## What It Does Not Prove

- Production model quality.
- Enterprise SSO integration.
- Cloud reliability.
- Provider image quality.
- Long-term multi-tenant operations.

Those belong in the production roadmap in [Reviewer Architecture Plan](reviewer-architecture-plan.md#5-phased-roadmap).

## Full Verification

```sh
project/poc/scripts/verify-all.sh
```

This runs backend tests, starts the backend, verifies API contracts, runs the latency benchmark, installs and builds the frontend harness, runs a backend-connected smoke test, and runs a browser visual smoke test.

## Manual Demo

```sh
project/poc/scripts/run-demo.sh
```

Then open `http://127.0.0.1:5173` for the browser fallback harness.

For Figma:

1. Import `project/figma-plugin/manifest.json` as a development plugin.
2. Run `Creative AI Workflow Lab`.
3. Create the demo selection.
4. Pair with the backend.
5. Generate copy, localize text, create an image placeholder, apply outputs, and inspect usage reporting.

## Expected Evidence

- Copy generation records operation, usage, and apply events.
- Localization records operation, usage, and apply events.
- Image placeholder generation records job, asset, usage, and apply events.
- The report shows operation count, estimated cost, image jobs, applies, and audit rows.
