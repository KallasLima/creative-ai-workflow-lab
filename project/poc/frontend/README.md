# Creative AI Workflow Slice Browser Harness

This is the local fallback browser harness for the runnable architecture slice.

It is not the primary designer UX. The canonical designer workflow proof is the real local Figma development plugin in `project/figma-plugin/`. This Vite + React + TypeScript harness remains because it provides deterministic automated checks for the same backend contract:

- mock plugin sign-in for offline fallback,
- seeded Figma-shaped layer fixtures,
- brand profile visibility,
- copy generation variants,
- 8-locale localization,
- async image placeholder job,
- apply event,
- usage and audit reporting,
- visible mock vs real backend transport state.

## Run

```sh
cd project/poc/frontend
npm ci
npm run dev
```

Open `http://localhost:5173`.

## Backend Integration

By default the harness runs in deterministic mock mode.

To use the local backend:

```sh
cd project/poc/frontend
VITE_API_BASE_URL=http://localhost:8000 npm run dev
```

All backend calls go through `src/api/client.ts`. If `VITE_API_BASE_URL` is absent or unreachable, the harness falls back to mock mode.

When the backend probe fails, the UI stays live in mock mode and shows the failure banner instead of hiding the transport problem.

The client preserves:

- `contractVersion: "2026-05-poc"`
- `pluginVersion: "0.1.0"`
- `Authorization: Bearer demo_plugin_session`
- `Idempotency-Key` on model-backed write routes
- `clientRequestId` on write operations

## Verify

```sh
cd project/poc/frontend
npm ci
npm run build
npm run smoke
```
