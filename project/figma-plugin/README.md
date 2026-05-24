# Figma Development Plugin

This folder contains the local Figma development plugin for Creative AI Workflow Lab. It is imported directly from `manifest.json` and needs no build step.

The plugin demonstrates:

- current selection scanning,
- local demo fixture creation,
- backend pairing,
- copy and localization requests,
- image placeholder job requests,
- text and image-fill apply actions,
- backend apply-event recording after canvas changes.

## Files

- `manifest.json`: Figma development-plugin manifest.
- `src/main.js`: main-thread bridge for Figma canvas access and apply operations.
- `src/ui.html`: iframe UI that calls the local backend.

## Local Run

1. Start the backend with `project/poc/scripts/run-demo.sh`.
2. Open Figma Desktop.
3. Use **Plugins > Development > Import plugin from manifest**.
4. Select `project/figma-plugin/manifest.json`.
5. Run **Creative AI Workflow Lab**.
6. Click **Create demo selection** to create 2 text layers and 1 fill-capable 1024 x 1024 rectangle.
7. Pair with the backend.
8. Generate copy, localize copy, create an image placeholder, and apply outputs back to the canvas.

The local development plugin uses `devAllowedDomains` for `http://localhost:8000`; production `allowedDomains` intentionally stays `["none"]` because this package is meant for local development only.

## Boundaries

- This is a local development plugin, not a published Figma Community plugin.
- The plugin can be imported and exercised on a free personal Figma account, but it is not packaged for external distribution.
- Image output is deterministic placeholder generation with `placeholderOnly: true`.
- The browser harness under `project/poc/frontend` is fallback automation support, not the primary product surface.
