from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from .core.config import CONTRACT_VERSION, DEMO_CODE_CHALLENGE, DEMO_CODE_VERIFIER, PLUGIN_VERSION


class AuthStartRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    pluginVersion: str = PLUGIN_VERSION
    contractVersion: str = CONTRACT_VERSION
    localNonce: str = "demo_nonce"
    state: str = "state_demo"
    codeChallenge: str = DEMO_CODE_CHALLENGE
    codeChallengeMethod: Literal["S256"] = "S256"
    figmaUserHint: str | None = None


class AuthExchangeRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    requestId: str
    localNonce: str
    state: str = "state_demo"
    codeVerifier: str = DEMO_CODE_VERIFIER
    pluginVersion: str = PLUGIN_VERSION
    contractVersion: str = CONTRACT_VERSION


class LayerText(BaseModel):
    model_config = ConfigDict(extra="ignore")
    layerId: str
    text: str


class CopyGenerateRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    clientRequestId: str = Field(min_length=1)
    contractVersion: str
    pluginVersion: str
    tenantId: str
    brandId: str
    profileId: str
    campaign: str
    channel: str
    variantCount: int = Field(default=3, ge=1, le=3)
    layers: list[LayerText] = Field(min_length=1)


class LocalizationRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    clientRequestId: str = Field(min_length=1)
    contractVersion: str
    pluginVersion: str
    tenantId: str
    brandId: str
    profileId: str
    channel: str
    locales: list[str] = Field(min_length=1, max_length=8)
    layers: list[LayerText] = Field(min_length=1)


class ImageDimensions(BaseModel):
    model_config = ConfigDict(extra="ignore")
    width: int
    height: int


class ImageLayer(BaseModel):
    model_config = ConfigDict(extra="ignore")
    layerId: str
    name: str
    type: Literal["imageFill"] = "imageFill"
    dimensions: ImageDimensions


class ImageJobRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    clientRequestId: str = Field(min_length=1)
    contractVersion: str
    pluginVersion: str
    tenantId: str
    brandId: str
    profileId: str
    channel: str
    layer: ImageLayer
    prompt: str


class AppliedItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    layerId: str
    outputId: str
    outputType: Literal["copy", "image"]


class ApplyEventRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    operationId: str
    appliedBy: str
    appliedItems: list[AppliedItem] = Field(min_length=1)
    generationRequestId: str | None = None
    appliedAt: str | None = None
    figmaFileKey: str | None = None
    skippedItems: list[dict[str, Any]] = Field(default_factory=list)


class ApproveProfileRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    approved: bool = True
    makeActive: bool = True
    reviewComment: str | None = None


class TenantCreateRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    tenantId: str = Field(pattern=r"^tenant_[a-z0-9_]+$")
    name: str = Field(min_length=2)


class BrandCreateRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    brandId: str = Field(pattern=r"^brand_[a-z0-9_]+$")
    name: str = Field(min_length=2)

