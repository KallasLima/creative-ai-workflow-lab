import type {
  ApplyEventResponse,
  BrandProfile,
  CopyGenerateResponse,
  ImageJobResponse,
  LocalizationResponse,
  SelectionResponse,
  UsageReport,
} from "../api/types";
import type { ApiRuntime } from "../api/client";

export type ProofTone = "neutral" | "good" | "warn" | "info";

export type ProofCard = {
  label: string;
  value: string;
  detail: string;
  tone: ProofTone;
};

export type ProofGate = {
  label: string;
  detail: string;
  passed: boolean;
};

export type DemoProofSummary = {
  runtimeCard: ProofCard;
  selectionCard: ProofCard;
  profileCard: ProofCard;
  traceCard: ProofCard;
  scaleCard: ProofCard;
  assetCard: ProofCard;
  readinessGates: ProofGate[];
};

function countSelection(selection?: SelectionResponse) {
  const layers = selection?.layers ?? [];
  const textCount = layers.filter((layer) => layer.type === "text").length;
  const imageCount = layers.filter((layer) => layer.type === "imageFill").length;
  const unsupportedCount = Math.max(0, layers.length - textCount - imageCount);
  return { textCount, imageCount, unsupportedCount };
}

function buildTraceValue(copy?: CopyGenerateResponse, localization?: LocalizationResponse, imageJob?: ImageJobResponse, apply?: ApplyEventResponse) {
  const items = [copy?.operationId, localization?.operationId, imageJob?.jobId, apply?.applyEventId].filter(Boolean);
  return items.length ? items.join(" · ") : "Awaiting generated traces";
}

function buildTraceDetail(copy?: CopyGenerateResponse, localization?: LocalizationResponse, imageJob?: ImageJobResponse, apply?: ApplyEventResponse) {
  const items = [copy?.usageEventId, localization?.usageEventId, imageJob?.usageEventId, apply?.auditEventId].filter(Boolean);
  return items.length ? items.join(" · ") : "operationId / usageEventId / applyEventId / auditEventId";
}

export function buildDemoProofSummary(input: {
  runtime?: ApiRuntime;
  selection?: SelectionResponse;
  profile?: BrandProfile;
  copy?: CopyGenerateResponse;
  localization?: LocalizationResponse;
  imageJob?: ImageJobResponse;
  apply?: ApplyEventResponse;
  report?: UsageReport;
}): DemoProofSummary {
  const { textCount, imageCount, unsupportedCount } = countSelection(input.selection);
  const runtime = input.runtime;
  const modeTone: ProofTone = runtime?.probeState === "reachable" ? "good" : runtime?.probeState === "unreachable" ? "warn" : "neutral";
  const asset = input.imageJob?.asset;
  const assetValue = asset ? `${asset.width} x ${asset.height}` : "Awaiting image job";
  const assetDetail = asset ? `placeholderOnly: ${String(asset.placeholderOnly)} · ${asset.assetId}` : "Create the placeholder before claiming metadata";
  const readinessGates: ProofGate[] = [
    {
      label: "Selection",
      detail: "2 text layers and 1 image-fill layer are visible",
      passed: textCount >= 2 && imageCount >= 1,
    },
    {
      label: "Profile",
      detail: "profile_nova_v3 is approved and brand-scoped",
      passed: input.profile?.profileId === "profile_nova_v3" && input.profile?.status === "approved",
    },
    {
      label: "Localization",
      detail: "The 8 required locales are visible in the matrix",
      passed: (input.localization?.results[0]?.localizations.length ?? 0) === 8,
    },
    {
      label: "Image",
      detail: "The placeholder remains 1024 x 1024 and placeholderOnly",
      passed: Boolean(asset) && asset?.width === 1024 && asset?.height === 1024 && asset?.placeholderOnly === true,
    },
    {
      label: "Trace",
      detail: "operation, usage, apply, and audit ids stay visible",
      passed: Boolean(input.copy?.operationId && input.copy?.usageEventId && input.apply?.applyEventId && input.apply?.auditEventId),
    },
    {
      label: "Scale path",
      detail: "SQLite, mock provider, and queue-worker path is explicit",
      passed: true,
    },
  ];

  return {
    runtimeCard: {
      label: runtime?.label ?? "Loading client",
      value: runtime?.probeState === "reachable" ? "Real backend" : runtime?.probeState === "unreachable" ? "Mock fallback" : "Mock mode",
      detail: runtime?.detail ?? "Waiting for client bootstrap",
      tone: modeTone,
    },
    selectionCard: {
      label: input.selection?.selectionId ?? "Selection",
      value: `${textCount} text / ${imageCount} image-fill / ${unsupportedCount} ignored`,
      detail: input.selection ? `${input.selection.fileId} · ${input.selection.pageId}` : "Waiting for selection fixture",
      tone: textCount >= 2 && imageCount >= 1 ? "good" : "warn",
    },
    profileCard: {
      label: input.profile?.profileId ?? "Brand profile",
      value: `${input.profile?.status ?? "pending"} v${input.profile?.version ?? 0}`,
      detail: input.profile ? `Brand ${input.profile.brandId} · ${input.profile.tone.join(" / ")}` : "Waiting for approved brand profile",
      tone: input.profile?.status === "approved" ? "good" : "warn",
    },
    traceCard: {
      label: "Trace IDs",
      value: buildTraceValue(input.copy, input.localization, input.imageJob, input.apply),
      detail: buildTraceDetail(input.copy, input.localization, input.imageJob, input.apply),
      tone: input.copy?.operationId && input.apply?.applyEventId ? "good" : "info",
    },
    scaleCard: {
      label: "Local to production",
      value: "SQLite -> Postgres",
      detail: "Mock provider -> model gateway · polling -> queue workers",
      tone: "info",
    },
    assetCard: {
      label: asset?.assetId ?? "Asset pending",
      value: assetValue,
      detail: assetDetail,
      tone: asset?.placeholderOnly ? "good" : "neutral",
    },
    readinessGates,
  };
}
