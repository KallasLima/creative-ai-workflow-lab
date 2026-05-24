export const CONTRACT_VERSION = "2026-05-poc";
export const PLUGIN_VERSION = "0.1.0";
export const DEMO_ACCESS_TOKEN = "demo_plugin_session";

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
  requestId: string;
  session: Session;
  user: SessionUser;
};

export type ContextResponse = {
  requestId: string;
  tenant: { tenantId: string; name: string };
  user: SessionUser & { role: string };
  brands: Array<{ brandId: string; name: string; activeProfileId: string }>;
  tenants: Array<{
    tenantId: string;
    name: string;
    brands: Array<{
      brandId: string;
      name: string;
      activeProfileVersionId: string;
      enabledOperations: string[];
    }>;
  }>;
  featureFlags: {
    imagePlaceholders: boolean;
    pdfIngestion: boolean;
    usageReporting: boolean;
  };
  limits: {
    maxTextLayersPerRequest: number;
    maxLocalesPerRequest: number;
    maxImageJobsPerUser: number;
  };
};

export type BrandProfile = {
  requestId: string;
  profileVersionId: string;
  profileId: string;
  brandId: string;
  status: string;
  confidence: string;
  version: number;
  sourceGuidelineId: string;
  sourceGuidelineIds: string[];
  profile: {
    tone: string[];
    bannedPhrases: string[];
    localeNotes: Record<string, string[]>;
    visualNotes: string[];
  };
  reviewNotes: Array<{ severity: string; message: string }>;
  tone: string[];
  bannedPhrases: string[];
  updatedAt: string;
};

export type ProfileListResponse = {
  requestId: string;
  brandId: string;
  profiles: Array<{
    profileVersionId: string;
    status: string;
    confidence: string;
    version: number;
    sourceGuidelineIds: string[];
    isActive: boolean;
  }>;
};

export type ProfileApproveRequest = {
  approved: boolean;
  makeActive: boolean;
  reviewComment?: string | null;
};

export type ProfileApproveResponse = {
  requestId: string;
  profileVersionId: string;
  status: string;
  previousActiveProfileVersionId: string | null;
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
  requestId: string;
  operationId: string;
  status: "completed";
  profileVersion: string;
  brandProfileVersionId: string;
  promptTemplateVersionId: string;
  model: "mock-gpt-4o-equivalent";
  latencyMs: number;
  results: Array<{
    layerId: string;
    variants: Array<{ variantId: string; text: string; score: number }>;
  }>;
  usageEventId: string;
  usage: {
    usageEventId: string;
    estimatedCostUsd: string;
    latencyMs: number;
    modelProvider: string;
    modelName: string;
  };
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
  requestId: string;
  operationId: string;
  status: "completed";
  brandProfileVersionId: string;
  promptTemplateVersionId: string;
  results: Array<{
    layerId: string;
    localizations: Array<{ locale: string; text: string; warning: string | null }>;
  }>;
  usageEventId: string;
  usage: {
    usageEventId: string;
    estimatedCostUsd: string;
    latencyMs: number;
  };
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
  requestId: string;
  jobId: string;
  status: ImageJobStatus;
  pollAfterMs: number;
};

export type ImageAsset = {
  assetId: string;
  url: string;
  previewUrl?: string;
  width: number;
  height: number;
  placeholderOnly: boolean;
  rightsStatus: "ideation_only";
  safetyStatus: "passed" | "requires_review";
  policyChecks: Array<
    | "placeholder_only"
    | "ideation_only"
    | "no_public_figure"
    | "no_protected_mark"
    | "no_final_asset_claim"
  >;
  contentType?: string;
};

export type ImageJobResponse = {
  requestId: string;
  jobId: string;
  status: ImageJobStatus;
  asset?: ImageAsset;
  usageEventId?: string;
  usage?: {
    usageEventId: string;
    estimatedCostUsd: string;
  };
};

export type ApplyEventRequest = {
  operationId: string;
  appliedBy: string;
  appliedItems: Array<{ layerId: string; outputId: string; outputType: "copy" | "image" }>;
};

export type ApplyEventResponse = {
  requestId: string;
  applyEventId: string;
  auditEventId: string;
  status: "recorded";
};

export type ModelQualityCheck = {
  name: string;
  passed: boolean;
  missingTerms?: string[];
  bannedPhrasesFound?: string[];
  overLimitLocales?: string[];
  expected?: number;
  actual?: number;
  characters?: number;
};

export type ModelQualityResult = {
  sampleId: string;
  operationType: "copy" | "localization";
  score: number;
  passed: boolean;
  checks: ModelQualityCheck[];
  outputPreview: string;
};

export type ModelQualityGateResponse = {
  requestId: string;
  qualityRunId: string;
  provider: string;
  model: string;
  threshold: number;
  score: number;
  passed: boolean;
  sampleCount: number;
  results: ModelQualityResult[];
  qualityGate: {
    goldenSampleSet: string;
    proves: string;
    doesNotProve: string;
  };
};

export type UsageGroup = {
  userId: string;
  brandId: string;
  operationType: string;
  operationCount: number;
  estimatedCostUsd: number;
};

export type UsageReport = {
  requestId: string;
  summary: {
    operationCount: number;
    appliedCount: number;
    estimatedCostUsd: number;
    medianTextLatencyMs: number;
    imageJobFailureRate: number;
    totalOperations: number;
    totalEstimatedCostUsd: number;
    copyOperations: number;
    localizationOperations: number;
    imageJobs: number;
    applyEvents: number;
  };
  groups: UsageGroup[];
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
