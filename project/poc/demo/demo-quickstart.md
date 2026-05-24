# Demo Quickstart

Use this when live Figma is unavailable or you need a deterministic automated fallback harness. The canonical designer workflow is the real local Figma development plugin in `project/figma-plugin/`.

## Start

```sh
project/poc/scripts/run-demo.sh
```

Open:

```text
http://localhost:5173
```

The launcher starts the backend on `http://127.0.0.1:8000` and the browser harness on `http://127.0.0.1:5173` with `VITE_API_BASE_URL` set to the backend.

Stop both with `Ctrl-C`.

## 5-Minute Fallback Harness Flow

1. Confirm the transport badge says `Real backend mode`.
2. Click `Backend sign-in`.
3. Confirm `Maya Chen`, `Nova Athletics`, `brand_nova`, `profile_nova_v3`, approved profile status, `Spring Launch`, and `mobile`.
4. Confirm selection `sel_spring_launch`: 2 text layers and 1 image-fill layer.
5. Click `Generate copy`; verify `operationId` and `usageEventId`.
6. Click `Localization`; verify all 8 locales.
7. Click `Image`; verify queued, running, and completed states.
8. Verify `1024 x 1024` and `placeholderOnly: true`.
9. Apply one output.
10. Open `Report`; verify operation count, estimated cost, apply event, and audit event.

## Closing Line

This is not a production MVP or the main product surface. It is a runnable fallback demonstration of the boundaries: plugin workflow, backend policy, profile versioning, model boundary, async jobs, usage metering, and auditability.
