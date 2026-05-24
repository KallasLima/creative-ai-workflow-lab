# Runnable Local Proof

The local proof has 3 layers:

- Figma development plugin.
- FastAPI backend with SQLite persistence.
- Browser fallback harness for repeatable verification.

## Full Verification

```sh
project/poc/scripts/verify-all.sh
```

This runs backend tests, starts the backend, verifies API contracts, installs and builds the frontend harness, runs a real-backend smoke test, and runs a browser visual smoke test.

## Manual Demo

```sh
project/poc/scripts/run-demo.sh
```

Then open `http://127.0.0.1:5173` for the browser fallback harness.

For Figma:

1. Import `project/figma-plugin/manifest.json` as a development plugin.
2. Run `Creative AI Workflow Lab`.
3. Create the local proof selection.
4. Pair with the backend.
5. Generate copy, localize text, create an image placeholder, apply outputs, and inspect usage reporting.

## Expected Proof

- Copy generation records operation, usage, and apply events.
- Localization records operation, usage, and apply events.
- Image placeholder generation records job, asset, usage, and apply events.
- The report shows operation count, estimated cost, image jobs, applies, and audit rows.
