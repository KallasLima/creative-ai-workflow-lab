# Demo Guide

Use this guide to run the local prototype without reading the whole repository.

## Start

```sh
project/poc/scripts/run-demo.sh
```

Open:

```text
http://localhost:5173
```

The launcher starts the backend on `http://127.0.0.1:8000` and the browser harness on `http://127.0.0.1:5173` with `VITE_API_BASE_URL` pointed at the backend. Stop both with `Ctrl-C`.

## Browser Harness Flow

1. Confirm the transport badge says `Real backend mode`.
2. Click `Backend sign-in`.
3. Confirm `Maya Chen`, `Nova Athletics`, and `profile_nova_v3`.
4. Confirm selection `sel_spring_launch` has 2 text layers and 1 image-fill layer.
5. Generate copy and verify `operationId` plus `usageEventId`.
6. Run localization and verify all 8 locales are visible.
7. Create the image placeholder and verify queued, running, completed states.
8. Verify the asset is `1024 x 1024` and `placeholderOnly: true`.
9. Apply copy, localized copy, or image output.
10. Open Report and verify operation count, estimated cost, apply event, and audit event.

## Figma Plugin Flow

1. Start the backend.
2. Import `project/figma-plugin/manifest.json` in Figma Desktop as a development plugin.
3. Run **Creative AI Workflow Lab**.
4. Click **Create demo selection**.
5. Pair with the backend.
6. Generate copy, localize copy, create an image placeholder, and apply outputs to the canvas.

## What This Demonstrates

- The plugin remains thin and canvas-focused.
- The backend owns auth, policy, profile context, model calls, usage, cost, and audit records.
- Image work is asynchronous and tracked as an asset/job lifecycle.
- Apply events are explicit, so generated output is not treated as used until it is actually applied.
