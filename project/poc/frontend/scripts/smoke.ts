import { buildDemoProofSummary } from "../src/lib/demo-proof";
import {
  authExchange,
  authStart,
  completeReport,
  context,
  copyResponse,
  imageJobCompleted,
  localizationResponse,
  profile,
  selection,
} from "../src/mocks/data";
import { CONTRACT_VERSION, PLUGIN_VERSION } from "../src/api/types";

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) {
    throw new Error(message);
  }
}

const summary = buildDemoProofSummary({
  selection,
  profile,
  copy: copyResponse,
  localization: localizationResponse,
  imageJob: imageJobCompleted,
  apply: {
    applyEventId: "apply_003",
    auditEventId: "audit_apply_003",
    status: "recorded",
  },
  report: completeReport,
  runtime: {
    probeState: "not-configured",
    label: "Local mock mode",
    detail: "Deterministic fixtures only",
  },
});

const pendingSummary = buildDemoProofSummary({
  runtime: {
    probeState: "reachable",
    label: "Real backend mode at http://127.0.0.1:8000",
    detail: "Backend probe succeeded",
  },
});

assert(CONTRACT_VERSION === "2026-05-poc", "contractVersion must stay frozen");
assert(PLUGIN_VERSION === "0.1.0", "pluginVersion must stay frozen");
assert(authStart.requestId === "auth_req_demo", "auth start fixture must stay stable");
assert(authExchange.session.accessToken === "demo_plugin_session", "mock access token must stay stable");
assert(context.brands[0]?.name === "Nova Athletics", "brand fixture must stay stable");
assert(summary.selectionCard.value.includes("2 text"), "selection summary should prove the text layer count");
assert(summary.selectionCard.value.includes("1 image-fill"), "selection summary should prove the fill layer count");
assert(summary.profileCard.value.includes("approved"), "profile summary should show approved status");
assert(summary.assetCard.value === "1024 x 1024", "asset summary should prove placeholder dimensions");
assert(summary.assetCard.detail.includes("placeholderOnly: true"), "asset summary should prove placeholder-only status");
assert(pendingSummary.assetCard.value === "Awaiting image job", "pending asset summary must not claim dimensions before the image job");
assert(pendingSummary.assetCard.detail === "Create the placeholder before claiming metadata", "pending asset summary must not claim placeholder metadata early");
assert(pendingSummary.assetCard.detail.includes("before claiming metadata"), "pending asset summary must not claim placeholder metadata early");
assert(summary.traceCard.detail.includes("usage_copy_001"), "trace proof must include the copy usageEventId");
assert(summary.traceCard.detail.includes("usage_loc_001"), "trace proof must include the localization usageEventId");
assert(summary.traceCard.detail.includes("usage_img_001"), "trace proof must include the image usageEventId");
assert(completeReport.summary.totalOperations === 6, "usage report should prove the complete flow");
assert(completeReport.summary.applyEvents === 3, "usage report should prove all 3 apply events");
assert(copyResponse.results.every((result) => result.variants.length === 3), "copy response should expose 3 variants per layer");
assert(localizationResponse.results.every((result) => result.localizations.length === 8), "localization response should expose all 8 locales");
assert(imageJobCompleted.asset?.width === 1024 && imageJobCompleted.asset?.height === 1024, "image asset should stay 1024 x 1024");
assert(imageJobCompleted.asset?.placeholderOnly === true, "image asset should remain placeholderOnly");
assert(imageJobCompleted.asset?.rightsStatus === "ideation_only", "image asset should keep ideation-only rights status");
assert(imageJobCompleted.asset?.safetyStatus === "passed", "image asset should keep passed safety status");
assert(summary.readinessGates.every((gate) => gate.passed), "all readiness gates should pass on the frozen fixtures");

console.log("frontend-smoke: PASS");
