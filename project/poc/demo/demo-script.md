# 3-Minute Demo Script

## 0:00 - Frame

I built a small local runnable slice to prove the architecture's riskiest contracts. It is intentionally not a production MVP, and that is the point: it proves the seam between a real local Figma development plugin, the backend trust boundary, the brand profile, and the async image workflow without pretending the full platform already exists.

## 0:20 - Session And Selection

I start with backend-issued browser pairing, which represents the plugin receiving a short-lived session without owning credentials. In the canonical demo, the real local Figma plugin scans the selected layers and talks to the backend at `127.0.0.1:8000`. The browser harness is only there for automated fallback practice. After pairing, the flow uses Maya Chen, the Nova Athletics brand context, `profile_nova_v3`, and the selected Figma layers.

The selection contains 2 text layers and 1 fill-capable layer. That is the first architecture boundary: the plugin sends normalized design intent, not provider credentials or ungoverned prompts.

## 0:55 - Copy

In Copy, I generate 3 variants per selected text layer. The result shows `operationId`, `usageEventId`, model name, and latency. The point is not just that a model returned words. The point is that each output is tied to tenant, brand, profile version, campaign, channel, usage, and audit records, so the architecture can defend cost and governance later.

## 1:30 - Localization

In Localization, the same selected text becomes an 8-locale matrix: `fr-FR`, `de-DE`, `es-ES`, `pt-BR`, `it-IT`, `nl-NL`, `ja-JP`, and `ko-KR`. This demonstrates that localization is constrained writing inside existing design boxes, not generic translation outside the workflow. The matrix also makes overflow and completeness easy to audit during a live review.

## 2:05 - Image Placeholder

In Image, I start a placeholder job for the selected fill layer. It moves through queued, running, and completed. The completed asset is explicitly `1024 x 1024` and `placeholderOnly: true`, which keeps the workflow honest: it accelerates ideation without pretending to clear final rights or brand approval.

## 2:35 - Apply And Report

When I apply an output, the UI records `applyEventId` and `auditEventId`. The Report tab shows operation count, estimated cost, usage events, and recent audit events.

## 2:55 - Close

The scale panel is the bridge from local to production: SQLite maps to Postgres, the mock provider maps to a model gateway, and local polling maps to queue workers. The value of the slice is that the seams are executable: plugin workflow, backend policy, model gateway, usage records, async jobs, apply events, and reporting.

If someone asks why this is more than a toy, the answer is that the slice proves the architecture decisions that would be hardest to retrofit later: tenant-aware auth, governed brand profile versioning, async asset jobs, usage metering, traceable applies, and a path from local fixtures to live backend transport without changing the UI contract.
