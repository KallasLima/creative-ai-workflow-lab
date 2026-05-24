# Demo Evidence Checklist

Use this checklist after a practice run to confirm the demo is ready.

## Runtime

- [ ] `project/poc/scripts/verify-all.sh` passes.
- [ ] Figma Desktop imports `project/figma-plugin/manifest.json`.
- [ ] `project/poc/scripts/run-demo.sh` starts backend and browser fallback harness when the automated path is needed.
- [ ] Browser fallback harness opens at `http://localhost:5173`.
- [ ] Backend health works at `http://127.0.0.1:8000/health`.
- [ ] `Ctrl-C` stops the launcher cleanly.
- [ ] `project/poc/demo/demo-run-log-template.md` is filled in for the practice run.

## Visible Product Proof In Figma

- [ ] Plugin sees selected Figma layers.
- [ ] Plugin pairs with the local backend.
- [ ] Plugin generates copy from selected text layers.
- [ ] Plugin can apply generated/localized copy back to a text layer.
- [ ] Plugin creates a mocked 1024 x 1024 image placeholder job.
- [ ] Plugin applies the mocked placeholder to a fill-capable layer.
- [ ] Plugin records apply events with the backend.

## Fallback Harness Proof

- [ ] Transport badge shows real backend mode.
- [ ] Session user shows `Maya Chen`.
- [ ] Brand shows `Nova Athletics`.
- [ ] Profile shows `profile_nova_v3`.
- [ ] Selection shows `sel_spring_launch`.
- [ ] Selection includes 2 text layers and 1 image-fill layer.
- [ ] Copy output shows `operationId`.
- [ ] Copy output shows `usageEventId`.
- [ ] Localization shows all 8 locales.
- [ ] Image job shows queued, running, completed.
- [ ] Asset metadata shows `1024 x 1024`.
- [ ] Asset metadata shows `placeholderOnly: true`.
- [ ] Apply action creates `applyEventId`.
- [ ] Apply action creates `auditEventId`.
- [ ] Report shows operation count and estimated cost.

## Architecture Proof

- [ ] Can explain why the plugin stays thin.
- [ ] Can explain why backend owns policy and metering.
- [ ] Can explain why brand profiles are approved runtime artifacts.
- [ ] Can explain why images are async.
- [ ] Can explain what maps from local POC to production.
- [ ] Can point to the written run log instead of relying on memory.
