import {
  Activity,
  BadgeCheck,
  CheckCircle2,
  CircleDollarSign,
  AlertTriangle,
  FileText,
  Image,
  Layers3,
  Loader2,
  Play,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import type { ReactNode } from "react";
import { useEffect, useMemo, useState } from "react";
import { ApiClient, ApiRuntime, createApiClient } from "./api/client";
import {
  ApplyEventResponse,
  BrandProfile,
  ContextResponse,
  CopyGenerateResponse,
  ImageAsset,
  ImageJobResponse,
  LocalizationResponse,
  SelectionLayer,
  SelectionResponse,
  Session,
  SessionUser,
  UsageReport,
} from "./api/types";
import { locales } from "./mocks/data";
import { buildDemoProofSummary } from "./lib/demo-proof";

type Tab = "copy" | "localization" | "image" | "report";
type RunState = "idle" | "running" | "ready" | "error";
type UiError = {
  scope: "session" | "copy" | "localization" | "image" | "apply" | "report" | "bootstrap";
  message: string;
  detail: string;
  recoverable: boolean;
};

const campaign = "Spring Launch";
const channel = "mobile";
const imagePrompt = "Lightweight running shoe on a bright spring track";

function textLayers(selection?: SelectionResponse) {
  return selection?.layers.filter((layer): layer is Extract<SelectionLayer, { type: "text" }> => layer.type === "text") ?? [];
}

function imageLayers(selection?: SelectionResponse) {
  return selection?.layers.filter((layer): layer is Extract<SelectionLayer, { type: "imageFill" }> => layer.type === "imageFill") ?? [];
}

function StatusPill({ tone = "neutral", children }: { tone?: "neutral" | "good" | "warn" | "info"; children: ReactNode }) {
  return <span className={`status status-${tone}`}>{children}</span>;
}

function Metric({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function ProofCard({
  label,
  value,
  detail,
  tone = "neutral",
}: {
  label: string;
  value: string;
  detail: string;
  tone?: "neutral" | "good" | "warn" | "info";
}) {
  return (
    <article className={`proof-card proof-card-${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{detail}</small>
    </article>
  );
}

function NoticeBanner({
  tone = "info",
  title,
  body,
  action,
}: {
  tone?: "info" | "warn" | "good";
  title: string;
  body: string;
  action?: ReactNode;
}) {
  return (
    <div className={`notice-banner notice-${tone}`} role="status" aria-live="polite">
      <div>
        <strong>{title}</strong>
        <p>{body}</p>
      </div>
      {action ? <div className="notice-action">{action}</div> : null}
    </div>
  );
}

function DemoSequence({ signedIn, copyReady, localizationReady, imageReady, applyReady }: {
  signedIn: boolean;
  copyReady: boolean;
  localizationReady: boolean;
  imageReady: boolean;
  applyReady: boolean;
}) {
  const steps = [
    ["1", "Sign in", signedIn],
    ["2", "Generate copy", copyReady],
    ["3", "Localize", localizationReady],
    ["4", "Image job", imageReady],
    ["5", "Apply + report", applyReady],
  ] as const;

  return (
    <section className="demo-sequence" aria-label="Demo sequence">
      <div>
        <strong>3-5 minute demo path</strong>
        <span>Follow the demo path from session to report.</span>
      </div>
      <ol>
        {steps.map(([number, label, done]) => (
          <li className={done ? "done" : ""} key={label}>
            <span>{number}</span>
            {label}
          </li>
        ))}
      </ol>
    </section>
  );
}

function SectionTitle({ icon, title, detail }: { icon: ReactNode; title: string; detail?: string }) {
  return (
    <div className="section-title">
      <span className="section-icon">{icon}</span>
      <div>
        <h2>{title}</h2>
        {detail ? <p>{detail}</p> : null}
      </div>
    </div>
  );
}

function describeError(
  scope: UiError["scope"],
  error: unknown,
  fallbackMessage: string,
  recoverable = true,
): UiError {
  return {
    scope,
    message: fallbackMessage,
    detail: error instanceof Error ? error.message : String(error ?? "Unknown error"),
    recoverable,
  };
}

function SelectionPanel({ selection }: { selection?: SelectionResponse }) {
  const texts = textLayers(selection);
  const images = imageLayers(selection);
  const unsupported = Math.max(0, (selection?.layers.length ?? 0) - texts.length - images.length);

  return (
    <section className="panel selection-panel">
      <SectionTitle icon={<Layers3 size={16} />} title="Selection" detail={selection?.selectionId ?? "No selection loaded"} />
      <div className="selection-stats">
        <Metric label="Text" value={texts.length} />
        <Metric label="Fill" value={images.length} />
        <Metric label="Ignored" value={unsupported} />
      </div>
      <div className="selection-rail">
        <StatusPill tone={texts.length >= 2 ? "good" : "warn"}>{texts.length >= 2 ? "Copy ready" : "Need 2 text layers"}</StatusPill>
        <StatusPill tone={images.length >= 1 ? "good" : "warn"}>{images.length >= 1 ? "Image ready" : "Need 1 image-fill layer"}</StatusPill>
        <StatusPill tone={unsupported > 0 ? "warn" : "info"}>{unsupported > 0 ? `${unsupported} ignored` : "No unsupported layers"}</StatusPill>
      </div>
      <div className="layer-list">
        {selection?.layers.map((layer) => (
          <div className="layer-row" key={layer.layerId}>
            <span className={`layer-kind ${layer.type === "text" ? "text-kind" : "image-kind"}`}>
              {layer.type === "text" ? <FileText size={14} /> : <Image size={14} />}
            </span>
            <div>
              <strong>{layer.name}</strong>
              <small>{layer.layerId}</small>
            </div>
            <span className="layer-meta">
              {layer.type === "text" ? `${layer.style.maxCharacters} chars` : `${layer.dimensions.width} x ${layer.dimensions.height}`}
            </span>
          </div>
        ))}
      </div>
    </section>
  );
}

function ContextPanel({ context, profile }: { context?: ContextResponse; profile?: BrandProfile }) {
  const brand = context?.brands[0];

  return (
    <section className="panel">
      <SectionTitle icon={<ShieldCheck size={16} />} title="Context" detail={brand?.name ?? "Sign in to load brand access"} />
      <div className="context-grid">
        <Metric label="Brand" value={brand?.name ?? "-"} />
        <Metric label="Profile" value={profile?.profileId ?? brand?.activeProfileId ?? "-"} />
        <Metric label="Campaign" value={campaign} />
        <Metric label="Channel" value={channel} />
      </div>
      <div className="profile-strip">
        <StatusPill tone={profile?.status === "approved" ? "good" : "warn"}>{profile?.status ?? "pending"}</StatusPill>
        <StatusPill tone="info">{context?.user.role ?? "designer"}</StatusPill>
        <span>{profile ? `v${profile.version}` : "version pending"}</span>
        <span>{profile ? profile.tone.join(" / ") : "Waiting for approved profile"}</span>
      </div>
    </section>
  );
}

function CopyTab({
  copy,
  state,
  selection,
  onGenerate,
  onApply,
  applyState,
  statusMessage,
  error,
  canGenerate,
}: {
  copy?: CopyGenerateResponse;
  state: RunState;
  selection?: SelectionResponse;
  onGenerate: () => void;
  onApply: (outputId: string, layerId: string) => void;
  applyState: RunState;
  statusMessage: string;
  error?: UiError;
  canGenerate: boolean;
}) {
  const layerNames = new Map(textLayers(selection).map((layer) => [layer.layerId, layer.name]));

  return (
    <div className="tab-body">
      <div className="action-bar">
        <div>
          <h3>Copy variants</h3>
          <p>3 bounded options per selected text layer.</p>
          <small className="status-note">{statusMessage}</small>
        </div>
        <button className="primary" onClick={onGenerate} disabled={!canGenerate || state === "running"}>
          {state === "running" ? <Loader2 className="spin" size={16} /> : <Sparkles size={16} />}
          Generate copy
        </button>
      </div>

      {error ? <NoticeBanner tone="warn" title={error.message} body={error.detail} /> : null}

      {copy ? (
        <>
          <div className="trace-line">
            <StatusPill tone="info">operationId {copy.operationId}</StatusPill>
            <StatusPill tone="info">usageEventId {copy.usageEventId}</StatusPill>
            <StatusPill tone="good">{copy.latencyMs} ms</StatusPill>
          </div>
          <div className="result-list">
            {copy.results.map((result) => (
              <div className="result-group" key={result.layerId}>
                <div className="result-heading">
                  <strong>{layerNames.get(result.layerId) ?? result.layerId}</strong>
                  <small>{result.layerId}</small>
                </div>
                {result.variants.map((variant) => (
                  <button className="variant-row" key={variant.variantId} onClick={() => onApply(variant.variantId, result.layerId)}>
                    <span>{variant.text}</span>
                    <small>{variant.variantId} / {Math.round(variant.score * 100)}%</small>
                  </button>
                ))}
              </div>
            ))}
          </div>
          <div className="helper-line">
            <CheckCircle2 size={15} />
            Click any variant to record an apply event. Current apply state: {applyState}.
          </div>
        </>
      ) : (
        <div className="empty-state">Generate copy to show variants, operation id, and usage event id.</div>
      )}
    </div>
  );
}

function LocalizationTab({
  localization,
  state,
  selection,
  onLocalize,
  onApply,
  applyState,
  statusMessage,
  error,
  canLocalize,
}: {
  localization?: LocalizationResponse;
  state: RunState;
  selection?: SelectionResponse;
  onLocalize: () => void;
  onApply: (outputId: string, layerId: string, operationId: string) => void;
  applyState: RunState;
  statusMessage: string;
  error?: UiError;
  canLocalize: boolean;
}) {
  const layerNames = new Map(textLayers(selection).map((layer) => [layer.layerId, layer.name]));

  return (
    <div className="tab-body">
      <div className="action-bar">
        <div>
          <h3>Localization</h3>
          <p>All 8 target locales stay visible.</p>
          <small className="status-note">{statusMessage}</small>
        </div>
        <button className="primary" onClick={onLocalize} disabled={!canLocalize || state === "running"}>
          {state === "running" ? <Loader2 className="spin" size={16} /> : <Activity size={16} />}
          Localize
        </button>
      </div>
      {error ? <NoticeBanner tone="warn" title={error.message} body={error.detail} /> : null}
      <div className="locale-strip">
        {locales.map((locale) => <span key={locale}>{locale}</span>)}
      </div>
      {localization ? (
        <>
          <div className="trace-line">
            <StatusPill tone="info">operationId {localization.operationId}</StatusPill>
            <StatusPill tone="info">usageEventId {localization.usageEventId}</StatusPill>
          </div>
          <div className="locale-matrix">
            {localization.results.map((result) => (
              <div className="locale-group" key={result.layerId}>
                <div className="result-heading">
                  <strong>{layerNames.get(result.layerId) ?? result.layerId}</strong>
                  <small>{result.layerId}</small>
                </div>
                <div className="locale-grid">
                  {result.localizations.map((item) => (
                    <div className="locale-cell" key={`${result.layerId}-${item.locale}`}>
                      <strong>{item.locale}</strong>
                      <span>{item.text}</span>
                      <button
                        className="secondary locale-apply"
                        onClick={() => onApply(`locale_${item.locale}`, result.layerId, localization.operationId)}
                        disabled={applyState === "running"}
                      >
                        Apply {item.locale}
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
          <div className="helper-line">
            <CheckCircle2 size={15} />
            Apply a localized value to record the localization operation in the audit trail. Current apply state: {applyState}.
          </div>
        </>
      ) : (
        <div className="empty-state">Run localization to fill the matrix for fr-FR, de-DE, es-ES, pt-BR, it-IT, nl-NL, ja-JP, and ko-KR.</div>
      )}
    </div>
  );
}

function PlaceholderPreview({ asset }: { asset?: ImageAsset }) {
  return (
    <div className={`asset-preview ${asset ? "" : "asset-preview-pending"}`} aria-label="1024 x 1024 placeholder asset preview">
      <div className="asset-mark">NA</div>
      <div>
        <strong>{asset?.assetId ?? "asset pending"}</strong>
        <span>{asset ? `${asset.width} x ${asset.height}` : "Run the image job to verify 1024 x 1024"}</span>
        <span>{asset ? `placeholderOnly: ${String(asset.placeholderOnly)}` : "placeholder metadata pending"}</span>
      </div>
    </div>
  );
}

function OperationEmptyState({
  backendIsReachable,
  signInLabel,
}: {
  backendIsReachable: boolean;
  signInLabel: string;
}) {
  return (
    <div className="operation-empty">
      <div>
        <StatusPill tone={backendIsReachable ? "good" : "warn"}>
          {backendIsReachable ? "Real backend ready" : "Mock fallback ready"}
        </StatusPill>
        <h3>Start with {signInLabel}</h3>
        <p>
          The demo loads a Figma-like selection, approved brand profile, operation controls,
          and traceable usage records after the session exchange.
        </p>
      </div>
      <ol>
        <li>Load `sel_spring_launch` with 2 text layers and 1 image-fill layer.</li>
        <li>Generate copy, localize 8 locales, create an async image placeholder.</li>
        <li>Apply an output and show usage, cost, apply, and audit evidence.</li>
      </ol>
    </div>
  );
}

function ImageTab({
  imageJob,
  state,
  onCreateImage,
  onApplyImage,
  statusMessage,
  error,
  canCreate,
}: {
  imageJob?: ImageJobResponse;
  state: RunState;
  onCreateImage: () => void;
  onApplyImage: () => void;
  statusMessage: string;
  error?: UiError;
  canCreate: boolean;
}) {
  const progress = imageJob?.status ?? "idle";

  return (
    <div className="tab-body">
      <div className="action-bar">
        <div>
          <h3>Image placeholder</h3>
          <p>{imagePrompt}</p>
          <small className="status-note">{statusMessage}</small>
        </div>
        <button className="primary" onClick={onCreateImage} disabled={!canCreate || state === "running"}>
          {state === "running" ? <Loader2 className="spin" size={16} /> : <Image size={16} />}
          Create image placeholder
        </button>
      </div>
      {error ? <NoticeBanner tone="warn" title={error.message} body={error.detail} /> : null}
      <div className="job-track">
        {["queued", "running", "completed"].map((step) => (
          <span className={progress === step || (step === "queued" && progress !== "idle") || (step === "running" && progress === "completed") ? "active" : ""} key={step}>
            {step}
          </span>
        ))}
      </div>
      <PlaceholderPreview asset={imageJob?.asset} />
      {imageJob ? (
        <div className="trace-line">
          <StatusPill tone="info">jobId {imageJob.jobId}</StatusPill>
          <StatusPill tone={imageJob.status === "completed" ? "good" : "warn"}>{imageJob.status}</StatusPill>
          {imageJob.usageEventId ? <StatusPill tone="info">usageEventId {imageJob.usageEventId}</StatusPill> : null}
        </div>
      ) : null}
      <button className="secondary" onClick={onApplyImage} disabled={!imageJob?.asset}>
        Apply image output
      </button>
    </div>
  );
}

function ReportTab({ report, apply }: { report?: UsageReport; apply?: ApplyEventResponse }) {
  return (
    <div className="tab-body">
      <div className="report-grid">
        <Metric label="Operations" value={report?.summary.totalOperations ?? 0} />
        <Metric label="Cost" value={`$${(report?.summary.totalEstimatedCostUsd ?? 0).toFixed(3)}`} />
        <Metric label="Copy" value={report?.summary.copyOperations ?? 0} />
        <Metric label="Locales" value={report?.summary.localizationOperations ?? 0} />
        <Metric label="Images" value={report?.summary.imageJobs ?? 0} />
        <Metric label="Applies" value={report?.summary.applyEvents ?? 0} />
      </div>
      {apply ? (
        <div className="trace-line">
          <StatusPill tone="good">applyEventId {apply.applyEventId}</StatusPill>
          <StatusPill tone="good">auditEventId {apply.auditEventId}</StatusPill>
        </div>
      ) : null}
      <div className="report-rail">
        <div>
          <strong>Why this matters</strong>
          <p>Every visible action creates traceable usage and audit records so the design workflow can scale beyond a toy demo.</p>
        </div>
        <div>
          <strong>What to defend</strong>
          <p>SQLite maps to Postgres, mock provider maps to a model gateway, and polling maps to queue workers without changing the frontend contract.</p>
        </div>
      </div>
      <div className="audit-list">
        {(report?.recentAuditEvents ?? []).map((event) => (
          <div className="audit-row" key={event.auditEventId}>
            <span>{event.type}</span>
            <strong>{event.auditEventId}</strong>
            <small>{event.usageEventId ?? event.operationId}</small>
          </div>
        ))}
      </div>
    </div>
  );
}

function ScaleReadinessPanel({
  summary,
}: {
  summary: ReturnType<typeof buildDemoProofSummary>;
}) {
  return (
    <aside className="panel scale-panel">
      <SectionTitle icon={<CircleDollarSign size={16} />} title="Scale Readiness" detail="Local prototype to production path" />
      <div className="proof-stack">
        <ProofCard {...summary.runtimeCard} />
        <ProofCard {...summary.selectionCard} />
        <ProofCard {...summary.profileCard} />
        <ProofCard {...summary.assetCard} />
        <ProofCard {...summary.traceCard} />
        <ProofCard {...summary.scaleCard} />
      </div>
      <div className="scale-list">
        <div><strong>Persistence</strong><span>SQLite locally, Postgres for tenant data and usage records.</span></div>
        <div><strong>Model</strong><span>Mock provider locally, model gateway for licensed GPT-4o-equivalent calls.</span></div>
        <div><strong>Async</strong><span>Local job polling, queue workers for image and PDF work.</span></div>
        <div><strong>Audit</strong><span>operationId, usageEventId, applyEventId, auditEventId are first-class.</span></div>
      </div>
      <div className="gate-list">
        {summary.readinessGates.map((gate) => (
          <div className={`gate-row ${gate.passed ? "gate-pass" : "gate-fail"}`} key={gate.label}>
            <strong>{gate.label}</strong>
            <span>{gate.detail}</span>
          </div>
        ))}
      </div>
    </aside>
  );
}

export function App() {
  const [client, setClient] = useState<ApiClient>();
  const [session, setSession] = useState<Session>();
  const [user, setUser] = useState<SessionUser>();
  const [context, setContext] = useState<ContextResponse>();
  const [profile, setProfile] = useState<BrandProfile>();
  const [selection, setSelection] = useState<SelectionResponse>();
  const [report, setReport] = useState<UsageReport>();
  const [copy, setCopy] = useState<CopyGenerateResponse>();
  const [localization, setLocalization] = useState<LocalizationResponse>();
  const [imageJob, setImageJob] = useState<ImageJobResponse>();
  const [apply, setApply] = useState<ApplyEventResponse>();
  const [activeTab, setActiveTab] = useState<Tab>("copy");
  const [signInState, setSignInState] = useState<RunState>("idle");
  const [copyState, setCopyState] = useState<RunState>("idle");
  const [locState, setLocState] = useState<RunState>("idle");
  const [imageState, setImageState] = useState<RunState>("idle");
  const [applyState, setApplyState] = useState<RunState>("idle");
  const [lastError, setLastError] = useState<UiError>();

  useEffect(() => {
    createApiClient()
      .then((loadedClient) => {
        setClient(loadedClient);
        setLastError(undefined);
      })
      .catch((error) => {
        setLastError(describeError("bootstrap", error, "Frontend bootstrap failed", false));
      });
  }, []);

  const selectedTextLayers = useMemo(() => textLayers(selection), [selection]);
  const selectedImageLayer = useMemo(() => imageLayers(selection)[0], [selection]);
  const activeBrand = context?.brands[0];
  const token = session?.accessToken;
  const runtime = client?.runtime;
  const proofSummary = useMemo(
    () =>
      buildDemoProofSummary({
        runtime,
        selection,
        profile,
        copy,
        localization,
        imageJob,
        apply,
        report,
      }),
    [runtime, selection, profile, copy, localization, imageJob, apply, report],
  );
  const backendIsReachable = runtime?.probeState === "reachable";
  const backendIsUnreachable = runtime?.probeState === "unreachable";

  async function refreshReport() {
    if (!client) return;
    try {
      setLastError(undefined);
      setReport(await client.getUsageReport(token));
    } catch (error) {
      setLastError(describeError("report", error, "Usage report refresh failed"));
    }
  }

  async function signIn() {
    if (!client) return;
    setSignInState("running");
    try {
      setLastError(undefined);
      const auth = await client.startAuth();
      const exchanged = await client.exchangeAuth(auth.requestId);
      setSession(exchanged.session);
      setUser(exchanged.user);
      const loadedContext = await client.getContext(exchanged.session.accessToken);
      setContext(loadedContext);
      const brand = loadedContext.brands[0];
      const [loadedProfile, loadedSelection, loadedReport] = await Promise.all([
        client.getBrandProfile(loadedContext.tenant.tenantId, brand.brandId, brand.activeProfileId, exchanged.session.accessToken),
        client.getSelection(exchanged.session.accessToken),
        client.getUsageReport(exchanged.session.accessToken),
      ]);
      setProfile(loadedProfile);
      setSelection(loadedSelection);
      setReport(loadedReport);
      setSignInState("ready");
    } catch (error) {
      setSignInState("error");
      setLastError(describeError("session", error, "Sign-in flow failed"));
    }
  }

  async function generateCopy() {
    if (!client || !context || !activeBrand) return;
    setCopyState("running");
    try {
      setLastError(undefined);
      const response = await client.generateCopy({
        tenantId: context.tenant.tenantId,
        brandId: activeBrand.brandId,
        profileId: activeBrand.activeProfileId,
        campaign,
        channel,
        variantCount: 3,
        layers: selectedTextLayers.map((layer) => ({ layerId: layer.layerId, text: layer.text })),
      }, token);
      setCopy(response);
      setCopyState("ready");
      await refreshReport();
    } catch (error) {
      setCopyState("error");
      setLastError(describeError("copy", error, "Copy generation failed"));
    }
  }

  async function localizeCopy() {
    if (!client || !context || !activeBrand) return;
    setLocState("running");
    try {
      setLastError(undefined);
      const response = await client.localizeCopy({
        tenantId: context.tenant.tenantId,
        brandId: activeBrand.brandId,
        profileId: activeBrand.activeProfileId,
        channel,
        locales,
        layers: selectedTextLayers.map((layer) => ({ layerId: layer.layerId, text: layer.text })),
      }, token);
      setLocalization(response);
      setLocState("ready");
      await refreshReport();
    } catch (error) {
      setLocState("error");
      setLastError(describeError("localization", error, "Localization failed"));
    }
  }

  async function createImage() {
    if (!client || !context || !activeBrand || !selectedImageLayer) return;
    setImageState("running");
    try {
      setLastError(undefined);
      const created = await client.createImageJob({
        tenantId: context.tenant.tenantId,
        brandId: activeBrand.brandId,
        profileId: activeBrand.activeProfileId,
        channel,
        layer: selectedImageLayer,
        prompt: imagePrompt,
      }, token);
      setImageJob({ jobId: created.jobId, status: created.status });

      let latest: ImageJobResponse = { jobId: created.jobId, status: created.status };
      for (let index = 0; index < 3; index += 1) {
        await new Promise((resolve) => window.setTimeout(resolve, created.pollAfterMs));
        latest = await client.getImageJob(created.jobId, token);
        setImageJob(latest);
        if (latest.status === "completed" || latest.status === "failed") break;
      }
      setImageState(latest.status === "completed" ? "ready" : "error");
      await refreshReport();
    } catch (error) {
      setImageState("error");
      setLastError(describeError("image", error, "Image job failed"));
    }
  }

  async function applyOutput(outputId: string, layerId: string, outputType: "copy" | "image" = "copy", operationIdOverride?: string) {
    if (!client || !user) return;
    setApplyState("running");
    try {
      setLastError(undefined);
      const operationId = operationIdOverride ?? (outputType === "image" ? imageJob?.jobId ?? "job_img_001" : copy?.operationId ?? "op_copy_001");
      const response = await client.recordApplyEvent({
        operationId,
        appliedBy: user.userId,
        appliedItems: [{ layerId, outputId, outputType }],
      }, token);
      setApply(response);
      setApplyState("ready");
      await refreshReport();
    } catch (error) {
      setApplyState("error");
      setLastError(describeError("apply", error, "Apply event failed"));
    }
  }

  const signedIn = Boolean(session && user);
  const selectedTextCount = selectedTextLayers.length;
  const selectedImageCount = selectedImageLayer ? 1 : 0;
  const primaryError: UiError | undefined = lastError ?? (backendIsUnreachable
    ? {
        scope: "bootstrap",
        message: "Backend probe failed, running mock fallback",
        detail: `The app could not reach ${runtime?.baseUrl ?? "the configured backend"} so it stayed live on deterministic fixtures.`,
        recoverable: true,
      }
    : undefined);
  const signInLabel = backendIsReachable ? "Backend sign-in" : "Mock sign-in";
  const copyStatusMessage = !signedIn
    ? "Sign in to unlock the demo flow."
    : selectedTextCount > 0
      ? `${selectedTextCount} text layers are ready to generate.`
      : "No text layers are available for copy generation.";
  const locStatusMessage = !signedIn
    ? "Sign in to unlock localization."
    : selectedTextCount > 0
      ? "Localization keeps all 8 target locales visible."
      : "No text layers are available for localization.";
  const imageStatusMessage = !signedIn
    ? "Sign in to unlock image placeholder jobs."
    : selectedImageCount > 0
      ? "The image job remains asynchronous so progress stays honest."
      : "No image-fill layer is selected for placeholder generation.";

  return (
    <main className="app-shell">
      <div className="plugin-shell">
        <header className="topbar">
          <div>
            <h1>Creative AI Workflow Slice</h1>
            <p>Figma-like plugin panel for Nova Athletics.</p>
            <div className="topbar-meta">
              <StatusPill tone={backendIsReachable ? "good" : backendIsUnreachable ? "warn" : "info"}>{runtime?.label ?? "Loading transport"}</StatusPill>
              <StatusPill tone={signedIn ? "good" : "neutral"}>{signedIn ? user?.displayName : "Signed out"}</StatusPill>
              <StatusPill tone="info">contractVersion 2026-05-poc</StatusPill>
              <StatusPill tone="info">pluginVersion 0.1.0</StatusPill>
            </div>
          </div>
          <div className="session-box">
            <StatusPill tone={backendIsReachable ? "good" : backendIsUnreachable ? "warn" : "neutral"}>{backendIsReachable ? "Real backend mode" : backendIsUnreachable ? "Mock fallback active" : client?.modeLabel ?? "Loading client"}</StatusPill>
            <StatusPill tone={signedIn ? "good" : "neutral"}>{signedIn ? user?.displayName : "Signed out"}</StatusPill>
          </div>
        </header>

        {primaryError ? <NoticeBanner tone={primaryError.recoverable ? "warn" : "info"} title={primaryError.message} body={primaryError.detail} /> : null}

        <section className="proof-strip" aria-label="Workflow summary">
          <ProofCard {...proofSummary.runtimeCard} />
          <ProofCard {...proofSummary.selectionCard} />
          <ProofCard {...proofSummary.profileCard} />
          <ProofCard {...proofSummary.assetCard} />
        </section>

        <DemoSequence
          signedIn={signedIn}
          copyReady={Boolean(copy)}
          localizationReady={Boolean(localization)}
          imageReady={imageJob?.status === "completed"}
          applyReady={Boolean(apply)}
        />

        <div className="workspace">
          <div className="left-rail">
            <section className="panel signin-panel">
              <SectionTitle
                icon={<BadgeCheck size={16} />}
                title="Session"
                detail={signedIn ? "Backend-issued plugin session" : backendIsReachable ? "Backend browser pairing" : "Mock browser pairing"}
              />
              <button className="primary full" onClick={signIn} disabled={!client || signInState === "running"}>
                {signInState === "running" ? <Loader2 className="spin" size={16} /> : <Play size={16} />}
                {signInLabel}
              </button>
              {session ? <small className="token-line">Session token issued by backend (redacted)</small> : null}
              <div className="session-rail">
                <StatusPill tone={backendIsReachable ? "good" : backendIsUnreachable ? "warn" : "info"}>{runtime?.label ?? "Loading transport"}</StatusPill>
                <small>{runtime?.detail ?? "Waiting for backend probe"}</small>
              </div>
            </section>
            <SelectionPanel selection={selection} />
            <ContextPanel context={context} profile={profile} />
          </div>

          <section className="panel operation-panel">
            <div className="tabs" role="tablist" aria-label="Operation tabs">
              {[
                ["copy", "Copy"],
                ["localization", "Localization"],
                ["image", "Image"],
                ["report", "Report"],
              ].map(([tab, label]) => (
                <button className={activeTab === tab ? "active" : ""} key={tab} onClick={() => setActiveTab(tab as Tab)}>
                  {label}
                </button>
              ))}
            </div>
            {!signedIn ? <OperationEmptyState backendIsReachable={backendIsReachable} signInLabel={signInLabel} /> : null}
            {signedIn && activeTab === "copy" ? (
              <CopyTab
                copy={copy}
                state={copyState}
                selection={selection}
                onGenerate={generateCopy}
                onApply={applyOutput}
                applyState={applyState}
                statusMessage={copyStatusMessage}
                error={lastError?.scope === "copy" ? lastError : undefined}
                canGenerate={selectedTextCount > 0 && Boolean(context && activeBrand)}
              />
            ) : null}
            {signedIn && activeTab === "localization" ? (
              <LocalizationTab
                localization={localization}
                state={locState}
                selection={selection}
                onLocalize={localizeCopy}
                onApply={(outputId, layerId, operationId) => applyOutput(outputId, layerId, "copy", operationId)}
                applyState={applyState}
                statusMessage={locStatusMessage}
                error={lastError?.scope === "localization" ? lastError : undefined}
                canLocalize={selectedTextCount > 0 && Boolean(context && activeBrand)}
              />
            ) : null}
            {signedIn && activeTab === "image" ? (
              <ImageTab
                imageJob={imageJob}
                state={imageState}
                onCreateImage={createImage}
                onApplyImage={() => applyOutput(imageJob?.asset?.assetId ?? "asset_img_001", selectedImageLayer?.layerId ?? "img_hero", "image")}
                statusMessage={imageStatusMessage}
                error={lastError?.scope === "image" ? lastError : undefined}
                canCreate={Boolean(selectedImageLayer && context && activeBrand)}
              />
            ) : null}
            {signedIn && activeTab === "report" ? <ReportTab report={report} apply={apply} /> : null}
          </section>

          <ScaleReadinessPanel summary={proofSummary} />
        </div>
      </div>
    </main>
  );
}
