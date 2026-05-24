import {
  ApplyEventRequest,
  ApplyEventResponse,
  AuthExchangeResponse,
  AuthStartResponse,
  BrandProfile,
  ContextResponse,
  CopyGenerateRequest,
  CopyGenerateResponse,
  ImageJobCreateResponse,
  ImageJobRequest,
  ImageJobResponse,
  LocalizationRequest,
  LocalizationResponse,
  SelectionResponse,
  UsageReport,
} from "./types";
import {
  authExchange,
  authStart,
  completeReport,
  context,
  copyResponse,
  emptyReport,
  imageJobCompleted,
  imageJobQueued,
  imageJobRunning,
  localizationResponse,
  profile,
  selection,
} from "../mocks/data";

type ClientOptions = {
  baseUrl?: string;
};

type RequestOptions = {
  idempotencyKey?: string;
  accessToken?: string;
};

export type BackendProbeState = "not-configured" | "reachable" | "unreachable";

export type ApiRuntime = {
  baseUrl?: string;
  probeState: BackendProbeState;
  label: string;
  detail: string;
};

type CopyInput = Omit<CopyGenerateRequest, "clientRequestId" | "contractVersion" | "pluginVersion">;
type LocalizationInput = Omit<LocalizationRequest, "clientRequestId" | "contractVersion" | "pluginVersion">;
type ImageInput = Omit<ImageJobRequest, "clientRequestId" | "contractVersion" | "pluginVersion">;

const clientRequestId = (prefix: string) => `${prefix}_${Date.now().toString(36)}`;

const delay = (ms: number) => new Promise((resolve) => window.setTimeout(resolve, ms));

async function requestJson<T>(
  baseUrl: string,
  path: string,
  init: RequestInit = {},
  options: RequestOptions = {},
): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set("Accept", "application/json");
  if (init.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  if (options.accessToken) {
    headers.set("Authorization", `Bearer ${options.accessToken}`);
  }
  if (options.idempotencyKey) {
    headers.set("Idempotency-Key", options.idempotencyKey);
  }

  const response = await fetch(`${baseUrl}${path}`, { ...init, headers });
  if (!response.ok) {
    throw new Error(`${init.method ?? "GET"} ${path} failed with ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export interface ApiClient {
  mode: "mock" | "real";
  modeLabel: string;
  runtime: ApiRuntime;
  startAuth(): Promise<AuthStartResponse>;
  exchangeAuth(requestId?: string): Promise<AuthExchangeResponse>;
  getContext(accessToken?: string): Promise<ContextResponse>;
  getBrandProfile(tenantId: string, brandId: string, profileId: string, accessToken?: string): Promise<BrandProfile>;
  getSelection(accessToken?: string): Promise<SelectionResponse>;
  generateCopy(request: CopyInput, accessToken?: string): Promise<CopyGenerateResponse>;
  localizeCopy(request: LocalizationInput, accessToken?: string): Promise<LocalizationResponse>;
  createImageJob(request: ImageInput, accessToken?: string): Promise<ImageJobCreateResponse>;
  getImageJob(jobId: string, accessToken?: string): Promise<ImageJobResponse>;
  recordApplyEvent(request: ApplyEventRequest, accessToken?: string): Promise<ApplyEventResponse>;
  getUsageReport(accessToken?: string): Promise<UsageReport>;
}

class MockWorkflowClient {
  readonly mode = "mock" as const;
  readonly modeLabel: string;
  readonly runtime: ApiRuntime;
  private report: UsageReport;
  private jobPolls = 0;
  private applyCount = 0;

  constructor(runtime: ApiRuntime = {
    probeState: "not-configured",
    label: "Local mock mode",
    detail: "Deterministic fixtures only",
  }) {
    this.runtime = runtime;
    this.modeLabel = runtime.label;
    this.report = emptyReport;
  }

  async startAuth(): Promise<AuthStartResponse> {
    await delay(180);
    return authStart;
  }

  async exchangeAuth(_requestId = "auth_req_demo"): Promise<AuthExchangeResponse> {
    await delay(220);
    return authExchange;
  }

  async getContext(_accessToken?: string): Promise<ContextResponse> {
    await delay(160);
    return context;
  }

  async getBrandProfile(
    _tenantId = "tenant_designtechco",
    _brandId = "brand_nova",
    _profileId = "profile_nova_v3",
    _accessToken?: string,
  ): Promise<BrandProfile> {
    await delay(120);
    return profile;
  }

  async getSelection(_accessToken?: string): Promise<SelectionResponse> {
    await delay(120);
    return selection;
  }

  async generateCopy(_request: CopyInput, _accessToken?: string): Promise<CopyGenerateResponse> {
    await delay(420);
    this.report = {
      ...this.report,
      summary: {
        ...this.report.summary,
        totalOperations: Math.max(this.report.summary.totalOperations, 1),
        totalEstimatedCostUsd: Math.max(this.report.summary.totalEstimatedCostUsd, 0.009),
        copyOperations: 1,
      },
      byUser: [{ userId: "usr_maya", displayName: "Maya Chen", operations: 1, estimatedCostUsd: 0.009 }],
      recentAuditEvents: completeReport.recentAuditEvents.slice(0, 1),
    };
    return copyResponse;
  }

  async localizeCopy(_request: LocalizationInput, _accessToken?: string): Promise<LocalizationResponse> {
    await delay(500);
    this.report = {
      ...this.report,
      summary: {
        ...this.report.summary,
        totalOperations: Math.max(this.report.summary.totalOperations, 2),
        totalEstimatedCostUsd: Math.max(this.report.summary.totalEstimatedCostUsd, 0.018),
        localizationOperations: 1,
      },
      byUser: [{ userId: "usr_maya", displayName: "Maya Chen", operations: 2, estimatedCostUsd: 0.018 }],
      recentAuditEvents: completeReport.recentAuditEvents.slice(0, 2),
    };
    return localizationResponse;
  }

  async createImageJob(_request: ImageInput, _accessToken?: string): Promise<ImageJobCreateResponse> {
    this.jobPolls = 0;
    await delay(220);
    return { jobId: "job_img_001", status: "queued", pollAfterMs: 700 };
  }

  async getImageJob(_jobId = "job_img_001", _accessToken?: string): Promise<ImageJobResponse> {
    await delay(360);
    this.jobPolls += 1;
    if (this.jobPolls === 1) {
      return imageJobQueued;
    }
    if (this.jobPolls === 2) {
      return imageJobRunning;
    }
    this.report = {
      ...this.report,
      summary: {
        ...this.report.summary,
        totalOperations: Math.max(this.report.summary.totalOperations, 3),
        totalEstimatedCostUsd: Math.max(this.report.summary.totalEstimatedCostUsd, 0.031),
        imageJobs: 1,
      },
      byUser: [{ userId: "usr_maya", displayName: "Maya Chen", operations: 3, estimatedCostUsd: 0.031 }],
      recentAuditEvents: completeReport.recentAuditEvents.slice(0, 3),
    };
    return imageJobCompleted;
  }

  async recordApplyEvent(request: ApplyEventRequest, _accessToken?: string): Promise<ApplyEventResponse> {
    await delay(180);
    this.applyCount += 1;
    const applyEventId = `apply_${String(this.applyCount).padStart(3, "0")}`;
    const auditEventId = `audit_apply_${String(this.applyCount).padStart(3, "0")}`;
    const auditEvent = {
      auditEventId,
      type: "apply_recorded",
      operationId: request.operationId,
      createdAt: "2026-05-23T12:04:00Z",
    };
    const recentAuditEvents = [
      ...completeReport.recentAuditEvents.filter((event) => !event.auditEventId.startsWith("audit_apply_")),
      ...Array.from({ length: this.applyCount }, (_, index) => ({
        ...auditEvent,
        auditEventId: `audit_apply_${String(index + 1).padStart(3, "0")}`,
        operationId: index + 1 === this.applyCount ? request.operationId : index === 0 ? "op_copy_001" : index === 1 ? "op_loc_001" : "job_img_001",
      })),
    ];
    this.report = {
      ...this.report,
      summary: {
        ...this.report.summary,
        applyEvents: this.applyCount,
        totalOperations: Math.max(this.report.summary.copyOperations + this.report.summary.localizationOperations + this.report.summary.imageJobs + this.applyCount, this.report.summary.totalOperations),
        totalEstimatedCostUsd: Math.max(this.report.summary.totalEstimatedCostUsd, 0.036),
      },
      byUser: [{
        userId: "usr_maya",
        displayName: "Maya Chen",
        operations: this.report.summary.copyOperations + this.report.summary.localizationOperations + this.report.summary.imageJobs + this.applyCount,
        estimatedCostUsd: Math.max(this.report.summary.totalEstimatedCostUsd, 0.036),
      }],
      recentAuditEvents,
    };
    return { applyEventId, auditEventId, status: "recorded" };
  }

  async getUsageReport(_accessToken?: string): Promise<UsageReport> {
    await delay(140);
    return this.report;
  }
}

class RealWorkflowClient {
  readonly mode = "real" as const;
  readonly modeLabel = "Real backend mode";
  readonly runtime: ApiRuntime;

  constructor(private readonly baseUrl: string, private accessToken?: string) {
    this.runtime = {
      baseUrl,
      probeState: "reachable",
      label: `Real backend mode at ${baseUrl}`,
      detail: "Backend probe succeeded and the app is using live transport.",
    };
  }

  async startAuth(): Promise<AuthStartResponse> {
    return requestJson<AuthStartResponse>(
      this.baseUrl,
      "/auth/plugin/start",
      {
        method: "POST",
        body: JSON.stringify({
          contractVersion: "2026-05-poc",
          pluginVersion: "0.1.0",
          localNonce: "demo_nonce",
        }),
      },
    );
  }

  async exchangeAuth(requestId = "auth_req_demo", localNonce = "demo_nonce"): Promise<AuthExchangeResponse> {
    const response = await requestJson<AuthExchangeResponse>(
      this.baseUrl,
      "/auth/plugin/exchange",
      {
        method: "POST",
        body: JSON.stringify({
          requestId,
          localNonce,
          contractVersion: "2026-05-poc",
          pluginVersion: "0.1.0",
        }),
      },
    );
    this.accessToken = response.session.accessToken;
    return response;
  }

  async getContext(accessToken = this.accessToken): Promise<ContextResponse> {
    return requestJson<ContextResponse>(this.baseUrl, "/me/context", {}, { accessToken });
  }

  async getBrandProfile(
    tenantId = "tenant_designtechco",
    brandId = "brand_nova",
    profileId = "profile_nova_v3",
    accessToken = this.accessToken,
  ): Promise<BrandProfile> {
    return requestJson<BrandProfile>(
      this.baseUrl,
      `/tenants/${tenantId}/brands/${brandId}/profiles/${profileId}`,
      {},
      { accessToken },
    );
  }

  async getSelection(accessToken = this.accessToken): Promise<SelectionResponse> {
    return requestJson<SelectionResponse>(
      this.baseUrl,
      "/fixtures/figma-selection",
      {},
      { accessToken },
    );
  }

  async generateCopy(request: CopyInput, accessToken = this.accessToken): Promise<CopyGenerateResponse> {
    const payload: CopyGenerateRequest = {
      clientRequestId: clientRequestId("client_copy"),
      contractVersion: "2026-05-poc",
      pluginVersion: "0.1.0",
      ...request,
    };
    return requestJson<CopyGenerateResponse>(
      this.baseUrl,
      "/plugin/copy/generate",
      { method: "POST", body: JSON.stringify(payload) },
      { accessToken, idempotencyKey: payload.clientRequestId },
    );
  }

  async localizeCopy(request: LocalizationInput, accessToken = this.accessToken): Promise<LocalizationResponse> {
    const payload: LocalizationRequest = {
      clientRequestId: clientRequestId("client_loc"),
      contractVersion: "2026-05-poc",
      pluginVersion: "0.1.0",
      ...request,
    };
    return requestJson<LocalizationResponse>(
      this.baseUrl,
      "/plugin/copy/localize",
      { method: "POST", body: JSON.stringify(payload) },
      { accessToken, idempotencyKey: payload.clientRequestId },
    );
  }

  async createImageJob(request: ImageInput, accessToken = this.accessToken): Promise<ImageJobCreateResponse> {
    const payload: ImageJobRequest = {
      clientRequestId: clientRequestId("client_img"),
      contractVersion: "2026-05-poc",
      pluginVersion: "0.1.0",
      ...request,
    };
    return requestJson<ImageJobCreateResponse>(
      this.baseUrl,
      "/plugin/images/jobs",
      { method: "POST", body: JSON.stringify(payload) },
      { accessToken, idempotencyKey: payload.clientRequestId },
    );
  }

  async getImageJob(jobId: string, accessToken = this.accessToken): Promise<ImageJobResponse> {
    return requestJson<ImageJobResponse>(
      this.baseUrl,
      `/plugin/images/jobs/${jobId}`,
      {},
      { accessToken },
    );
  }

  async recordApplyEvent(request: ApplyEventRequest, accessToken = this.accessToken): Promise<ApplyEventResponse> {
    return requestJson<ApplyEventResponse>(
      this.baseUrl,
      "/plugin/apply-events",
      { method: "POST", body: JSON.stringify(request) },
      { accessToken, idempotencyKey: `apply_${request.operationId}` },
    );
  }

  async getUsageReport(accessToken = this.accessToken): Promise<UsageReport> {
    return requestJson<UsageReport>(this.baseUrl, "/reports/usage", {}, { accessToken });
  }
}

export type WorkflowClient = ApiClient;

export function createWorkflowClient(options: ClientOptions = {}): WorkflowClient {
  const baseUrl = options.baseUrl ?? import.meta.env.VITE_API_BASE_URL;
  if (!baseUrl) {
    return new MockWorkflowClient();
  }
  return new RealWorkflowClient(baseUrl.replace(/\/$/, ""));
}

async function probeBackend(baseUrl: string): Promise<boolean> {
  try {
    const response = await fetch(`${baseUrl.replace(/\/$/, "")}/health`, { method: "GET" });
    return response.ok;
  } catch {
    return false;
  }
}

export async function createReachableWorkflowClient(): Promise<WorkflowClient> {
  const baseUrl = import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "");
  if (!baseUrl) {
    return new MockWorkflowClient();
  }

  if (await probeBackend(baseUrl)) {
    return new RealWorkflowClient(baseUrl);
  }

  return new MockWorkflowClient({
    baseUrl,
    probeState: "unreachable",
    label: "Local mock mode",
    detail: `Backend probe failed for ${baseUrl}. The demo stays live on deterministic fixtures.`,
  });
}

export async function createApiClient(): Promise<ApiClient> {
  return createReachableWorkflowClient();
}
