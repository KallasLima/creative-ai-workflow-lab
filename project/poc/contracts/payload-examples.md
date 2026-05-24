# Payload Examples

All model-backed write requests preserve `contractVersion: "2026-05-poc"` and `pluginVersion: "0.1.0"`, require `clientRequestId`, and accept `Idempotency-Key`.

## Auth Start

```json
{
  "requestId": "auth_req_demo",
  "browserUrl": "http://localhost:5173/mock-auth/auth_req_demo",
  "state": "state_demo",
  "codeChallengeMethod": "S256",
  "authorizationCodeIssued": true,
  "expiresAt": "2026-05-23T23:59:00Z",
  "pollAfterMs": 500
}
```

## Auth Exchange

```json
{
  "requestId": "auth_req_demo",
  "session": {
    "accessToken": "demo_plugin_session",
    "expiresAt": "2026-05-24T00:59:00Z",
    "tokenType": "Bearer"
  },
  "oauth": {
    "state": "state_demo",
    "pkceVerified": true,
    "idTokenIssued": true
  },
  "idToken": "header.payload.signature",
  "user": {
    "userId": "usr_maya",
    "displayName": "Maya Chen"
  }
}
```

## Context

```json
{
  "requestId": "req_context_001",
  "tenant": { "tenantId": "tenant_designtechco", "name": "DesignTechCo" },
  "user": { "userId": "usr_maya", "displayName": "Maya Chen", "role": "designer" },
  "brands": [
    { "brandId": "brand_nova", "name": "Nova Athletics", "activeProfileId": "profile_nova_v3" }
  ],
  "tenants": [
    {
      "tenantId": "tenant_designtechco",
      "name": "DesignTechCo",
      "brands": [
        {
          "brandId": "brand_nova",
          "name": "Nova Athletics",
          "activeProfileVersionId": "profile_nova_v3",
          "enabledOperations": ["copy_variants", "localize", "image_placeholder"]
        }
      ]
    }
  ],
  "featureFlags": {
    "imagePlaceholders": true,
    "pdfIngestion": true,
    "usageReporting": true
  },
  "limits": {
    "maxTextLayersPerRequest": 20,
    "maxLocalesPerRequest": 8,
    "maxImageJobsPerUser": 3
  }
}
```

## Admin Tenant List

```json
{
  "requestId": "req_admin_tenants_001",
  "tenants": [
    {
      "tenantId": "tenant_designtechco",
      "name": "DesignTechCo",
      "brands": [
        { "brandId": "brand_nova", "name": "Nova Athletics", "activeProfileId": "profile_nova_v3" }
      ],
      "users": [
        { "userId": "usr_maya", "displayName": "Maya Chen", "role": "designer" }
      ]
    }
  ]
}
```

## Admin Tenant And Brand Create

```json
{
  "tenantId": "tenant_pilotco",
  "name": "Pilot Co"
}
```

```json
{
  "brandId": "brand_stride",
  "name": "Stride Lab"
}
```

## PDF Guideline Upload Response

```json
{
  "requestId": "req_guideline_001",
  "guidelineId": "guide_nova_001",
  "profileId": "profile_nova_v3",
  "status": "approved",
  "extraction": {
    "extractor": "pypdf",
    "pageCount": 1,
    "lowConfidence": false
  }
}
```

## Profile List

```json
{
  "requestId": "req_profiles_list_001",
  "brandId": "brand_nova",
  "profiles": [
    {
      "profileVersionId": "profile_nova_v3",
      "status": "active",
      "confidence": "high",
      "version": 3,
      "sourceGuidelineIds": ["guide_nova_001"],
      "isActive": true
    }
  ]
}
```

## Profile Get

```json
{
  "requestId": "req_profile_001",
  "profileVersionId": "profile_nova_v3",
  "profileId": "profile_nova_v3",
  "brandId": "brand_nova",
  "status": "active",
  "confidence": "high",
  "version": 3,
  "sourceGuidelineId": "guide_nova_001",
  "sourceGuidelineIds": ["guide_nova_001"],
  "profile": {
    "tone": ["energetic", "clear", "performance-led"],
    "bannedPhrases": ["cheap", "miracle"],
    "localeNotes": {
      "fr-FR": ["Preserve concise CTA style across locales"]
    },
    "visualNotes": ["Use bright ecommerce lifestyle placeholder imagery."]
  },
  "reviewNotes": [],
  "tone": ["energetic", "clear", "performance-led"],
  "bannedPhrases": ["cheap", "miracle"],
  "updatedAt": "2026-05-23T12:00:00Z"
}
```

## Profile Approve

```json
{
  "approved": true,
  "makeActive": true,
  "reviewComment": "Approved for pilot copy and placeholder generation."
}
```

```json
{
  "requestId": "req_profile_approve_001",
  "profileVersionId": "profile_nova_v3",
  "status": "active",
  "previousActiveProfileVersionId": "profile_nova_v3"
}
```

## Copy Generation Request

```json
{
  "clientRequestId": "client_copy_001",
  "contractVersion": "2026-05-poc",
  "pluginVersion": "0.1.0",
  "tenantId": "tenant_designtechco",
  "brandId": "brand_nova",
  "profileId": "profile_nova_v3",
  "campaign": "Spring Launch",
  "channel": "mobile",
  "variantCount": 3,
  "layers": [
    { "layerId": "txt_headline", "text": "Run further with gear built for spring." },
    { "layerId": "txt_cta", "text": "Shop the drop" }
  ]
}
```

## Copy Generation Response

```json
{
  "requestId": "req_copy_001",
  "operationId": "op_copy_001",
  "status": "completed",
  "profileVersion": "profile_nova_v3",
  "brandProfileVersionId": "profile_nova_v3",
  "promptTemplateVersionId": "ptv_copy_04",
  "model": "mock-gpt-4o-equivalent",
  "latencyMs": 420,
  "results": [
    {
      "layerId": "txt_headline",
      "variants": [
        { "variantId": "v1", "text": "Spring miles start with gear that keeps up.", "score": 0.91 },
        { "variantId": "v2", "text": "Built for longer runs and brighter days.", "score": 0.88 },
        { "variantId": "v3", "text": "Your spring run kit, ready for every mile.", "score": 0.86 }
      ]
    }
  ],
  "usageEventId": "usage_copy_001",
  "usage": {
    "usageEventId": "usage_copy_001",
    "estimatedCostUsd": "0.012",
    "latencyMs": 420,
    "modelProvider": "mock-provider",
    "modelName": "mock-gpt-4o-equivalent"
  }
}
```

## Localization Request

```json
{
  "clientRequestId": "client_loc_001",
  "contractVersion": "2026-05-poc",
  "pluginVersion": "0.1.0",
  "tenantId": "tenant_designtechco",
  "brandId": "brand_nova",
  "profileId": "profile_nova_v3",
  "channel": "mobile",
  "locales": ["fr-FR", "de-DE", "es-ES", "pt-BR", "it-IT", "nl-NL", "ja-JP", "ko-KR"],
  "layers": [
    { "layerId": "txt_cta", "text": "Shop the drop" }
  ]
}
```

## Localization Response

```json
{
  "requestId": "req_loc_001",
  "operationId": "op_loc_001",
  "status": "completed",
  "brandProfileVersionId": "profile_nova_v3",
  "promptTemplateVersionId": "ptv_localize_04",
  "results": [
    {
      "layerId": "txt_cta",
      "localizations": [
        { "locale": "fr-FR", "text": "Découvrir la collection", "warning": null },
        { "locale": "de-DE", "text": "Kollektion shoppen", "warning": null },
        { "locale": "es-ES", "text": "Compra la colección", "warning": null },
        { "locale": "pt-BR", "text": "Compre a coleção", "warning": null },
        { "locale": "it-IT", "text": "Scopri la collezione", "warning": null },
        { "locale": "nl-NL", "text": "Shop de collectie", "warning": null },
        { "locale": "ja-JP", "text": "コレクションを見る", "warning": "Review character width for compact CTA buttons." },
        { "locale": "ko-KR", "text": "컬렉션 쇼핑하기", "warning": null }
      ]
    }
  ],
  "usageEventId": "usage_loc_001",
  "usage": {
    "usageEventId": "usage_loc_001",
    "estimatedCostUsd": "0.009",
    "latencyMs": 610
  }
}
```

## Image Job Request

```json
{
  "clientRequestId": "client_img_001",
  "contractVersion": "2026-05-poc",
  "pluginVersion": "0.1.0",
  "tenantId": "tenant_designtechco",
  "brandId": "brand_nova",
  "profileId": "profile_nova_v3",
  "channel": "mobile",
  "layer": {
    "layerId": "img_hero",
    "name": "Hero Product Placeholder",
    "type": "imageFill",
    "dimensions": { "width": 1024, "height": 1024 }
  },
  "prompt": "Lightweight running shoe on a bright spring track"
}
```

## Image Job Create Response

```json
{
  "requestId": "req_img_001",
  "jobId": "job_img_001",
  "status": "queued",
  "pollAfterMs": 1000
}
```

## Image Job Status Response

```json
{
  "requestId": "req_img_002",
  "jobId": "job_img_001",
  "status": "completed",
  "asset": {
    "assetId": "asset_img_001",
    "url": "http://localhost:8000/assets/asset_img_001.png",
    "previewUrl": "http://localhost:8000/assets/asset_img_001.png",
    "width": 1024,
    "height": 1024,
    "placeholderOnly": true,
    "rightsStatus": "ideation_only",
    "safetyStatus": "passed",
    "policyChecks": [
      "placeholder_only",
      "ideation_only",
      "no_public_figure",
      "no_protected_mark",
      "no_final_asset_claim"
    ],
    "contentType": "image/png"
  },
  "usageEventId": "usage_img_001",
  "usage": {
    "usageEventId": "usage_img_001",
    "estimatedCostUsd": "0.015"
  }
}
```

## Apply Event Response

```json
{
  "requestId": "req_apply_001",
  "applyEventId": "apply_001",
  "auditEventId": "audit_apply_001",
  "status": "recorded"
}
```

## Model Quality Gate Response

```json
{
  "requestId": "req_quality_001",
  "qualityRunId": "quality_run_001",
  "provider": "mock-provider",
  "model": "mock-gpt-4o-equivalent",
  "threshold": 0.9,
  "score": 1,
  "passed": true,
  "sampleCount": 3,
  "results": [
    {
      "sampleId": "golden_copy_headline_001",
      "operationType": "copy",
      "score": 1,
      "passed": true,
      "checks": [
        { "name": "schema_valid", "passed": true },
        { "name": "required_terms_present", "passed": true },
        { "name": "banned_phrases_absent", "passed": true },
        { "name": "max_length_respected", "passed": true }
      ],
      "outputPreview": "Spring miles start with gear that keeps up."
    }
  ],
  "qualityGate": {
    "goldenSampleSet": "project/poc/fixtures/golden-samples.json",
    "proves": "Executable provider-quality gate mechanics against local golden samples.",
    "doesNotProve": "Live paid or approved model-provider quality in a production environment."
  }
}
```

## Usage Report

```json
{
  "requestId": "req_usage_001",
  "summary": {
    "operationCount": 3,
    "appliedCount": 1,
    "estimatedCostUsd": 0.036,
    "medianTextLatencyMs": 610,
    "imageJobFailureRate": 0,
    "totalOperations": 4,
    "totalEstimatedCostUsd": 0.036,
    "copyOperations": 1,
    "localizationOperations": 1,
    "imageJobs": 1,
    "applyEvents": 1
  },
  "groups": [
    {
      "userId": "usr_maya",
      "brandId": "brand_nova",
      "operationType": "copy",
      "operationCount": 1,
      "estimatedCostUsd": 0.012
    },
    {
      "userId": "usr_maya",
      "brandId": "brand_nova",
      "operationType": "localization",
      "operationCount": 1,
      "estimatedCostUsd": 0.009
    },
    {
      "userId": "usr_maya",
      "brandId": "brand_nova",
      "operationType": "image",
      "operationCount": 1,
      "estimatedCostUsd": 0.015
    }
  ],
  "byUser": [
    { "userId": "usr_maya", "displayName": "Maya Chen", "operations": 3, "estimatedCostUsd": 0.036 }
  ],
  "recentAuditEvents": [
    {
      "auditEventId": "audit_apply_001",
      "type": "apply_recorded",
      "operationId": "op_copy_001",
      "createdAt": "2026-05-23T12:00:00Z"
    }
  ]
}
```
