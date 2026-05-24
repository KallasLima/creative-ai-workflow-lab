export const CONTRACT_VERSION = "2026-05-poc";
export const PLUGIN_VERSION = "0.1.0";

export type ApiMode = "mock" | "real";

export type SessionUser = {
  userId: string;
  displayName: string;
};

export type Session = {
  accessToken: string;
  expiresAt: string;
};

export type AuthStartResponse = {
  requestId: string;
  browserUrl: string;
  expiresAt: string;
  pollAfterMs: number;
};

export type AuthExchangeResponse = {
  session: Session;
  user: SessionUser;
};

export type ContextResponse = {
  tenant: { tenantId: string; name: string };
  user: SessionUser & { role: string };
  brands: Array<{ brandId: string; name: string; activeProfileId: string }>;
  featureFlags: Record<string, boolean>;
};

export type BrandProfile = {
  profileId: string;
  brandId: string;
  status: string;
  version: number;
  sourceGuidelineId: string;
  tone: string[];
  bannedPhrases: string[];
  updatedAt: string;
};

export type TextLayer = {
  layerId: string;
  type: "text";
  name: string;
  text: string;
  style: { fontSize: number; maxCharacters: number };
};

export type ImageLayer = {
  layerId: string;
  type: "imageFill";
  name: string;
  dimensions: { width: number; height: number };
};

export type SelectionLayer = TextLayer | ImageLayer;

export type SelectionResponse = {
  fileId: string;
  pageId: string;
  selectionId: string;
  layers: SelectionLayer[];
};

export type CopyGenerateRequest = {
  clientRequestId: string;
  contractVersion: typeof CONTRACT_VERSION;
  pluginVersion: typeof PLUGIN_VERSION;
  tenantId: string;
  brandId: string;
  profileId: string;
  campaign: string;
  channel: string;
  variantCount: number;
  layers: Array<{ layerId: string; text: string }>;
};

export type CopyGenerateResponse = {
  operationId: string;
  requestId: string;
  profileVersion: string;
  model: string;
  latencyMs: number;
  results: Array<{
    layerId: string;
    variants: Array<{ variantId: string; text: string; score: number }>;
  }>;
  usageEventId: string;
};

export type LocalizationRequest = {
  clientRequestId: string;
  contractVersion: typeof CONTRACT_VERSION;
  pluginVersion: typeof PLUGIN_VERSION;
  tenantId: string;
  brandId: string;
  profileId: string;
  channel: string;
  locales: string[];
  layers: Array<{ layerId: string; text: string }>;
};

export type LocalizationResponse = {
  operationId: string;
  requestId: string;
  results: Array<{
    layerId: string;
    localizations: Array<{ locale: string; text: string; warning: string | null }>;
  }>;
  usageEventId: string;
};

export type ImageJobStatus = "queued" | "running" | "completed" | "failed";

export type ImageJobRequest = {
  clientRequestId: string;
  contractVersion: typeof CONTRACT_VERSION;
  pluginVersion: typeof PLUGIN_VERSION;
  tenantId: string;
  brandId: string;
  profileId: string;
  channel: string;
  layer: ImageLayer;
  prompt: string;
};

export type ImageJobCreateResponse = {
  jobId: string;
  status: ImageJobStatus;
  pollAfterMs: number;
};

export type ImageAsset = {
  assetId: string;
  url: string;
  width: number;
  height: number;
  placeholderOnly: boolean;
  rightsStatus?: "ideation_only";
  safetyStatus?: "passed" | "requires_review";
  policyChecks?: string[];
};

export type ImageJobResponse = {
  jobId: string;
  status: ImageJobStatus;
  asset?: ImageAsset;
  usageEventId?: string;
};

export type ApplyEventRequest = {
  operationId: string;
  appliedBy: string;
  appliedItems: Array<{ layerId: string; outputId: string; outputType: "copy" | "image" }>;
};

export type ApplyEventResponse = {
  applyEventId: string;
  auditEventId: string;
  status: string;
};

export type UsageReport = {
  summary: {
    totalOperations: number;
    totalEstimatedCostUsd: number;
    copyOperations: number;
    localizationOperations: number;
    imageJobs: number;
    applyEvents: number;
  };
  byUser: Array<{
    userId: string;
    displayName: string;
    operations: number;
    estimatedCostUsd: number;
  }>;
  recentAuditEvents: Array<{
    auditEventId: string;
    type: string;
    operationId?: string;
    usageEventId?: string;
    createdAt: string;
  }>;
};
