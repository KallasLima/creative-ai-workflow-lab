# Runnable PoC Demo Checklist

Fallback checklist for direct local browser checks at `http://localhost:5173`.

For a real-backend review, prefer the canonical local path:

```sh
project/poc/scripts/run-demo.sh
```

Then use `project/poc/demo/demo-quickstart.md`.

## Startup

- [ ] Run `project/poc/scripts/run-demo.sh` for the canonical demo, or `project/poc/scripts/run-dev.sh` only for mock fallback checks.
- [ ] Confirm the UI labels either `Local mock mode`, `Mock fallback active`, or `Real backend mode at http://localhost:8000`.
- [ ] Click `Backend sign-in` in the canonical real-backend demo, or `Mock sign-in` only during fallback checks.
- [ ] Confirm session user is `Maya Chen`.
- [ ] Confirm the top proof strip shows transport, selection, profile, and asset proof cards.

## Plugin Workflow

- [ ] Confirm selection id `sel_spring_launch`.
- [ ] Confirm 2 text layers and 1 image-fill layer.
- [ ] Confirm brand `Nova Athletics`.
- [ ] Confirm profile `profile_nova_v3`.
- [ ] Confirm campaign `Spring Launch`.
- [ ] Confirm channel `mobile`.
- [ ] Click `Generate copy`.
- [ ] Confirm 3 variants appear for each text layer.
- [ ] Confirm `operationId op_copy_001`.
- [ ] Confirm `usageEventId usage_copy_001`.
- [ ] Click `Localization`.
- [ ] Click `Localize`.
- [ ] Confirm all 8 locales are visible: `fr-FR`, `de-DE`, `es-ES`, `pt-BR`, `it-IT`, `nl-NL`, `ja-JP`, `ko-KR`.
- [ ] Click `Image`.
- [ ] Click `Create image placeholder`.
- [ ] Confirm job states progress through queued, running, completed.
- [ ] Confirm asset metadata shows `1024 x 1024`.
- [ ] Confirm `placeholderOnly: true`.
- [ ] Apply 1 copy output or image output.
- [ ] Click `Report`.
- [ ] Confirm an `applyEventId` is visible.
- [ ] Confirm an `auditEventId` is visible.
- [ ] Confirm operation count, estimated cost, usage event ids, and audit events are visible.
- [ ] Confirm the proof gates show the selection, profile, localization, image, trace, and scale path as satisfied.

## Close

- [ ] Point to the scale panel: SQLite/Postgres, mock provider/model gateway, local job/queue worker.
- [ ] Explain that the browser harness stays usable in mock mode, but the real Figma plugin plus backend is the canonical workflow proof.
- [ ] Say this is a runnable architecture slice, not a production MVP, and that it proves the risky seams rather than only a happy-path UI.
- [ ] Fill `project/poc/demo/demo-run-log-template.md` if this was a practice or handoff run.
