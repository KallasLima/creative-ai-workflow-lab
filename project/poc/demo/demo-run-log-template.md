# Demo Run Log Template

Use this after a practice run or walkthrough to capture what was actually proven.

## Run Metadata

- Date:
- Mode:
  - [ ] Real backend
  - [ ] Mock fallback
- Launcher used:
  - [ ] `project/poc/scripts/run-demo.sh`
  - [ ] `project/poc/scripts/run-dev.sh`
- Backend URL:
- Frontend URL:

## Start Proof

- [ ] Backend health returned `ok`.
- [ ] Frontend rendered at `http://127.0.0.1:5173`.
- [ ] Demo launcher printed the canonical checklist and evidence template paths.

## Live Demo Proof

- [ ] Session user: `Maya Chen`
- [ ] Brand: `Nova Athletics`
- [ ] Profile: `profile_nova_v3`
- [ ] Selection: `sel_spring_launch`
- [ ] Text layers: 2
- [ ] Image-fill layers: 1
- [ ] Copy `operationId`:
- [ ] Copy `usageEventId`:
- [ ] Localization locales visible:
- [ ] Image job reached `completed`
- [ ] Asset metadata showed `1024 x 1024`
- [ ] Asset metadata showed `placeholderOnly: true`
- [ ] Apply event `applyEventId`:
- [ ] Audit event `auditEventId`:
- [ ] Report showed usage/cost evidence

## Cleanup Proof

- [ ] `Ctrl-C` stopped the launcher cleanly.
- [ ] No listeners remained on ports `8000` or `5173`.
- [ ] `project/poc` has no generated `node_modules`, `dist`, `.venv`, `.data`, `__pycache__`, or `.pytest_cache` directories.

## Notes

- Issues found:
- Fixes made:
- Remaining risks:
