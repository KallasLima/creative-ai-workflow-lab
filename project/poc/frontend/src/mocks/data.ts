import {
  AuthExchangeResponse,
  AuthStartResponse,
  BrandProfile,
  ContextResponse,
  CopyGenerateResponse,
  ImageJobResponse,
  LocalizationResponse,
  SelectionResponse,
  UsageReport,
} from "../api/types";

export const locales = ["fr-FR", "de-DE", "es-ES", "pt-BR", "it-IT", "nl-NL", "ja-JP", "ko-KR"];

export const authStart: AuthStartResponse = {
  requestId: "auth_req_demo",
  browserUrl: "http://localhost:5173/mock-auth/auth_req_demo",
  expiresAt: "2026-05-23T23:59:00Z",
  pollAfterMs: 500,
};

export const authExchange: AuthExchangeResponse = {
  session: {
    accessToken: "demo_plugin_session",
    expiresAt: "2026-05-24T00:59:00Z",
  },
  user: {
    userId: "usr_maya",
    displayName: "Maya Chen",
  },
};

export const context: ContextResponse = {
  tenant: { tenantId: "tenant_designtechco", name: "DesignTechCo" },
  user: { userId: "usr_maya", displayName: "Maya Chen", role: "designer" },
  brands: [{ brandId: "brand_nova", name: "Nova Athletics", activeProfileId: "profile_nova_v3" }],
  featureFlags: {
    imagePlaceholders: true,
    pdfIngestion: true,
    usageReporting: true,
  },
};

export const profile: BrandProfile = {
  profileId: "profile_nova_v3",
  brandId: "brand_nova",
  status: "approved",
  version: 3,
  sourceGuidelineId: "guide_nova_001",
  tone: ["energetic", "clear", "performance-led"],
  bannedPhrases: ["cheap", "miracle"],
  updatedAt: "2026-05-23T12:00:00Z",
};

export const selection: SelectionResponse = {
  fileId: "fig_demo_campaign",
  pageId: "page_mobile_ads",
  selectionId: "sel_spring_launch",
  layers: [
    {
      layerId: "txt_headline",
      type: "text",
      name: "Headline",
      text: "Run further with gear built for spring.",
      style: { fontSize: 42, maxCharacters: 72 },
    },
    {
      layerId: "txt_cta",
      type: "text",
      name: "CTA",
      text: "Shop the drop",
      style: { fontSize: 18, maxCharacters: 28 },
    },
    {
      layerId: "img_hero",
      type: "imageFill",
      name: "Hero Product Placeholder",
      dimensions: { width: 1024, height: 1024 },
    },
  ],
};

export const copyResponse: CopyGenerateResponse = {
  operationId: "op_copy_001",
  requestId: "req_copy_001",
  profileVersion: "profile_nova_v3",
  model: "mock-gpt-4o-equivalent",
  latencyMs: 420,
  results: [
    {
      layerId: "txt_headline",
      variants: [
        { variantId: "v1", text: "Spring miles start with gear that keeps up.", score: 0.91 },
        { variantId: "v2", text: "Built for longer runs and brighter days.", score: 0.88 },
        { variantId: "v3", text: "Your spring run kit, ready for every mile.", score: 0.86 },
      ],
    },
    {
      layerId: "txt_cta",
      variants: [
        { variantId: "v1", text: "Shop spring gear", score: 0.92 },
        { variantId: "v2", text: "Start the run", score: 0.89 },
        { variantId: "v3", text: "See the drop", score: 0.87 },
      ],
    },
  ],
  usageEventId: "usage_copy_001",
};

export const localizationResponse: LocalizationResponse = {
  operationId: "op_loc_001",
  requestId: "req_loc_001",
  results: [
    {
      layerId: "txt_headline",
      localizations: [
        { locale: "fr-FR", text: "Les kilometres du printemps commencent ici.", warning: null },
        { locale: "de-DE", text: "Fruehlingskilometer beginnen mit Ausruestung, die mithalt.", warning: null },
        { locale: "es-ES", text: "Tus kilometros de primavera empiezan con equipo que responde.", warning: null },
        { locale: "pt-BR", text: "A corrida de primavera comeca com equipamento que acompanha.", warning: null },
        { locale: "it-IT", text: "I chilometri di primavera iniziano con gear che tiene il passo.", warning: null },
        { locale: "nl-NL", text: "Lentekilometers beginnen met gear dat bijblijft.", warning: null },
        { locale: "ja-JP", text: "春のランを支えるギアで、もっと遠くへ。", warning: null },
        { locale: "ko-KR", text: "봄 러닝을 끝까지 받쳐 주는 기어.", warning: null },
      ],
    },
    {
      layerId: "txt_cta",
      localizations: [
        { locale: "fr-FR", text: "Decouvrir la collection", warning: null },
        { locale: "de-DE", text: "Kollektion shoppen", warning: null },
        { locale: "es-ES", text: "Comprar la coleccion", warning: null },
        { locale: "pt-BR", text: "Comprar a colecao", warning: null },
        { locale: "it-IT", text: "Scopri la collezione", warning: null },
        { locale: "nl-NL", text: "Shop de collectie", warning: null },
        { locale: "ja-JP", text: "コレクションを見る", warning: null },
        { locale: "ko-KR", text: "컬렉션 쇼핑하기", warning: null },
      ],
    },
  ],
  usageEventId: "usage_loc_001",
};

export const imageJobQueued: ImageJobResponse = {
  jobId: "job_img_001",
  status: "queued",
};

export const imageJobRunning: ImageJobResponse = {
  jobId: "job_img_001",
  status: "running",
};

export const imageJobCompleted: ImageJobResponse = {
  jobId: "job_img_001",
  status: "completed",
  asset: {
    assetId: "asset_img_001",
    url: "mock://asset_img_001.png",
    width: 1024,
    height: 1024,
    placeholderOnly: true,
    rightsStatus: "ideation_only",
    safetyStatus: "passed",
    policyChecks: ["placeholder_only", "ideation_only", "no_public_figure", "no_protected_mark", "no_final_asset_claim"],
  },
  usageEventId: "usage_img_001",
};

export const emptyReport: UsageReport = {
  summary: {
    totalOperations: 0,
    totalEstimatedCostUsd: 0,
    copyOperations: 0,
    localizationOperations: 0,
    imageJobs: 0,
    applyEvents: 0,
  },
  byUser: [{ userId: "usr_maya", displayName: "Maya Chen", operations: 0, estimatedCostUsd: 0 }],
  recentAuditEvents: [],
};

export const completeReport: UsageReport = {
  summary: {
    totalOperations: 6,
    totalEstimatedCostUsd: 0.036,
    copyOperations: 1,
    localizationOperations: 1,
    imageJobs: 1,
    applyEvents: 3,
  },
  byUser: [{ userId: "usr_maya", displayName: "Maya Chen", operations: 6, estimatedCostUsd: 0.036 }],
  recentAuditEvents: [
    {
      auditEventId: "audit_copy_001",
      type: "copy.generated",
      operationId: "op_copy_001",
      usageEventId: "usage_copy_001",
      createdAt: "2026-05-23T12:01:00Z",
    },
    {
      auditEventId: "audit_loc_001",
      type: "copy.localized",
      operationId: "op_loc_001",
      usageEventId: "usage_loc_001",
      createdAt: "2026-05-23T12:02:00Z",
    },
    {
      auditEventId: "audit_img_001",
      type: "image.placeholder_completed",
      operationId: "job_img_001",
      usageEventId: "usage_img_001",
      createdAt: "2026-05-23T12:03:00Z",
    },
    {
      auditEventId: "audit_apply_001",
      type: "apply_recorded",
      operationId: "op_copy_001",
      createdAt: "2026-05-23T12:04:00Z",
    },
    {
      auditEventId: "audit_apply_002",
      type: "apply_recorded",
      operationId: "op_loc_001",
      createdAt: "2026-05-23T12:05:00Z",
    },
    {
      auditEventId: "audit_apply_003",
      type: "apply_recorded",
      operationId: "job_img_001",
      createdAt: "2026-05-23T12:06:00Z",
    },
  ],
};
