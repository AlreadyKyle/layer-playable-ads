"""Pydantic models for API request/response types."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ── Enums ──


class MechanicTypeEnum(str, Enum):
    MATCH3 = "match3"
    RUNNER = "runner"
    TAPPER = "tapper"
    MERGER = "merger"
    PUZZLE = "puzzle"
    SHOOTER = "shooter"
    UNKNOWN = "unknown"


class ConfidenceLevelEnum(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# ── Nested Models ──


class VisualStyleSchema(BaseModel):
    art_type: str
    color_palette: list[str]
    theme: str
    mood: str


class AssetNeedSchema(BaseModel):
    key: str
    description: str
    game_specific_prompt: str


class GameAnalysisSchema(BaseModel):
    game_name: str
    publisher: Optional[str] = None
    mechanic_type: MechanicTypeEnum
    mechanic_confidence: float
    mechanic_reasoning: str
    visual_style: VisualStyleSchema
    assets_needed: list[AssetNeedSchema]
    recommended_template: str
    template_config: dict
    core_loop_description: str
    hook_suggestion: str
    cta_suggestion: str
    confidence_level: ConfidenceLevelEnum
    raw_analysis: dict = Field(default_factory=dict)


class GeneratedAssetSchema(BaseModel):
    key: str
    prompt: str
    image_url: Optional[str] = None
    base64_data: Optional[str] = None
    generation_time: float = 0.0
    width: int = 0
    height: int = 0
    error: Optional[str] = None
    is_valid: bool = False


class GeneratedAssetSetSchema(BaseModel):
    game_name: str
    mechanic_type: MechanicTypeEnum
    assets: dict[str, GeneratedAssetSchema] = Field(default_factory=dict)
    total_generation_time: float = 0.0
    style_id: str = ""
    valid_count: int = 0


class PlayableConfigSchema(BaseModel):
    game_name: str = "My Game"
    title: str = "Playable Ad"
    store_url: str = "https://example.com"
    store_url_ios: str = ""
    store_url_android: str = ""
    width: int = 320
    height: int = 480
    background_color: str = "#1a1a2e"
    hook_text: str = "Tap to Play!"
    cta_text: str = "Download FREE"
    sound_enabled: bool = True


class PlayableResultSchema(BaseModel):
    html: str
    file_size_bytes: int
    file_size_formatted: str
    file_size_mb: float
    mechanic_type: MechanicTypeEnum
    assets_embedded: int
    is_valid: bool
    validation_errors: list[str] = Field(default_factory=list)


# ── Request Models ──


class AnalyzeRequest(BaseModel):
    """Used for JSON-based analysis (screenshots as base64)."""
    screenshots_base64: list[str]
    game_name: Optional[str] = None


class GenerateAssetsRequest(BaseModel):
    analysis: GameAnalysisSchema
    style_id: str


class BuildPlayableRequest(BaseModel):
    analysis: GameAnalysisSchema
    assets: GeneratedAssetSetSchema
    config: PlayableConfigSchema = Field(default_factory=PlayableConfigSchema)


class DemoRequest(BaseModel):
    mechanic_type: MechanicTypeEnum = MechanicTypeEnum.MATCH3
    game_name: str = "Demo Game"


# ── Response Models ──


class HealthResponse(BaseModel):
    status: str = "ok"
    api_keys: dict[str, bool] = Field(default_factory=dict)


class WorkspaceResponse(BaseModel):
    workspace_id: Optional[str] = None
    credits_available: Optional[int] = None
    has_access: Optional[bool] = None
    error: Optional[str] = None


class StyleSchema(BaseModel):
    id: str
    name: str
    status: str
    type: Optional[str] = None


class StylesResponse(BaseModel):
    styles: list[StyleSchema] = Field(default_factory=list)
    error: Optional[str] = None


class TemplateInfoSchema(BaseModel):
    mechanic_type: MechanicTypeEnum
    name: str
    description: str
    example_games: list[str]
    required_assets: list[AssetNeedSchema]


class TemplatesResponse(BaseModel):
    templates: list[TemplateInfoSchema] = Field(default_factory=list)
