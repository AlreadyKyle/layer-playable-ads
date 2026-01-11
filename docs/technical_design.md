# Technical Design Document
## Layer.ai Playable Studio (LPS)

**Version**: 1.0.0
**Status**: MVP Implementation
**Last Updated**: 2025-01-11

---

## 1. System Overview

### 1.1 Architecture Summary

LPS follows a modular monolith architecture with four primary modules:

```
┌─────────────────────────────────────────────────────────────────┐
│                    Streamlit Web Interface                       │
│                         (src/app.py)                            │
└─────────────────────────────────────────────────────────────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        ▼                      ▼                      ▼
┌───────────────┐    ┌────────────────┐    ┌─────────────────┐
│  Vision       │    │   Workflow     │    │    Playable     │
│  Module       │    │   Module       │    │    Module       │
│               │    │                │    │                 │
│ competitor_   │    │ style_         │    │ assembler.py    │
│ spy.py        │    │ manager.py     │    │ templates/      │
└───────┬───────┘    └───────┬────────┘    └────────┬────────┘
        │                    │                      │
        │            ┌───────┴────────┐             │
        │            ▼                ▼             │
        │    ┌──────────────┐  ┌────────────┐      │
        │    │  Forge       │  │  Layer     │      │
        │    │  Module      │  │  Client    │◄─────┘
        │    │              │  │            │
        │    │ asset_       │  │ layer_     │
        │    │ forger.py    │  │ client.py  │
        │    └──────────────┘  └─────┬──────┘
        │                            │
        ▼                            ▼
┌───────────────┐           ┌───────────────┐
│   Anthropic   │           │   Layer.ai    │
│   Claude API  │           │  GraphQL API  │
└───────────────┘           └───────────────┘
```

### 1.2 Technology Stack

| Layer | Technology | Justification |
|-------|------------|---------------|
| Frontend | Streamlit | Rapid prototyping, Python-native |
| Backend | Python 3.11+ | Async support, type hints |
| HTTP Client | httpx | Async/sync dual support |
| AI/Vision | Anthropic Claude | Best-in-class vision analysis |
| Image Processing | Pillow | Standard Python imaging |
| Game Engine | Phaser.js 3.70 | Industry standard, MRAID compatible |
| Configuration | pydantic-settings | Type-safe env management |
| Logging | structlog | Structured, contextual logging |

---

## 2. Module Specifications

### 2.1 Layer Client (`src/layer_client.py`)

The central GraphQL client for all Layer.ai API interactions.

**IMPORTANT**: Layer.ai requires pre-trained styles. The `styleId` parameter is REQUIRED for image generation.

#### Class: `LayerClient`

```python
class LayerClient:
    """Async GraphQL client for Layer.ai API."""

    async def get_workspace_info() -> WorkspaceInfo
    async def check_credits() -> WorkspaceInfo
    async def list_styles(limit: int) -> list[dict]
    async def generate_image(prompt: str, style_id: str, ...) -> GeneratedImage
    async def get_generation_status(inference_id: str) -> GeneratedImage
    async def poll_generation(task_id: str, timeout: int) -> GeneratedImage
    async def generate_with_polling(prompt: str, style_id: str, ...) -> GeneratedImage
```

#### Class: `LayerClientSync`

Synchronous wrapper for Streamlit compatibility (uses `asyncio.run()`). Accepts optional `timeout` parameter for initial API fetches.

#### Key Data Classes

```python
@dataclass
class GeneratedImage:
    task_id: str
    status: GenerationStatus  # PENDING, PROCESSING, COMPLETED, FAILED
    image_url: Optional[str]
    image_id: Optional[str]
    error_message: Optional[str]
    duration_seconds: float
    prompt: str

@dataclass
class WorkspaceInfo:
    workspace_id: str
    credits_available: int
    has_access: bool

@dataclass
class StyleConfig:
    name: str
    description: str
    style_keywords: list[str]
    negative_keywords: list[str]
    reference_image_id: Optional[str]
```

#### Error Handling

Custom exceptions for API errors:
- `LayerAPIError`: Base exception
- `InsufficientCreditsError`: Credits below threshold
- `GenerationTimeoutError`: Polling timeout exceeded
- `AuthenticationError`: API key or access issues

#### Retry Logic

Uses `tenacity` for exponential backoff:
```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(httpx.HTTPStatusError),
)
async def _execute(self, query: str, variables: dict) -> dict:
    ...
```

### 2.2 Vision Module (`src/vision/competitor_spy.py`)

AI-powered visual analysis using Claude Vision.

#### Class: `CompetitorSpy`

```python
class CompetitorSpy:
    def analyze_screenshots(image_paths: list, context: str) -> AnalysisResult
    def analyze_screenshot(image_path: Path, context: str) -> AnalysisResult
    def analyze_app_store_url(url: str, screenshot: bytes) -> AnalysisResult
```

#### Vision Prompt Engineering

The style extraction prompt is carefully crafted to output structured JSON:

```
Focus on:
1. Art Style (2D/3D, cartoon/realistic, pixel art, etc.)
2. Color Palette (primary, accent hex values)
3. Visual Elements (characters, environments, UI)
4. Mood/Tone (bright/dark, playful/serious)
5. Technical Style (rendering, shading, outlines)
```

#### Output: `AnalysisResult`

```python
@dataclass
class AnalysisResult:
    recipe: StyleRecipe
    genre: str
    art_style: str
    target_audience: str
    key_visual_elements: list[str]
    mood_descriptors: list[str]
    raw_analysis: dict
    source_type: str  # "screenshot" or "appstore"
```

### 2.3 Workflow Module (`src/workflow/style_manager.py`)

High-level style lifecycle management.

#### Class: `StyleManager`

```python
class StyleManager:
    def create_style_from_recipe(recipe: StyleRecipe) -> ManagedStyle
    def get_style(style_id: str) -> Optional[ManagedStyle]
    def list_workspace_styles(limit: int, offset: int) -> list[dict]
    def get_dashboard_url(style_id: str) -> str
```

#### Dashboard Deep Linking

Generates URLs for manual style editing:
```
https://app.layer.ai/workspace/{workspace_id}/styles/{style_id}
```

### 2.4 Forge Module (`src/forge/asset_forger.py`)

Smart asset generation with credit guard and consistency tracking.

#### Class: `AssetForger`

```python
class AssetForger:
    def check_credits() -> WorkspaceCredits
    def start_session(style_id: str, reference_id: str) -> ForgeSession
    def forge_asset(prompt: str, preset_name: str) -> ForgedAsset
    def forge_from_preset(preset_name: str) -> ForgedAsset
    def forge_playable_asset_set() -> dict[str, list[ForgedAsset]]
    def end_session() -> ForgeSession
```

#### UA Presets

Pre-defined prompts optimized for playable ad assets:

| Preset | Category | Sample Prompt |
|--------|----------|---------------|
| hook_character | hook | "expressive game character, dynamic pose" |
| hook_item | hook | "shiny treasure chest, glowing, magical" |
| gameplay_background | gameplay | "game level background, vibrant colors" |
| gameplay_element | gameplay | "collectible gem, faceted crystal" |
| cta_button | cta | "play now button, glossy, green gradient" |
| cta_banner | cta | "game logo banner, premium quality" |

#### Reference Image Consistency

The first forged asset automatically sets `referenceImageId`:
```python
if session.reference_image_id is None and result.image_id:
    session.reference_image_id = result.image_id
```

All subsequent forges use this reference for visual consistency.

### 2.5 Playable Module (`src/playable/assembler.py`)

HTML5 playable ad assembly with MRAID 3.0 support.

#### Class: `PlayableAssembler`

```python
class PlayableAssembler:
    def prepare_asset(forged_asset: ForgedAsset, key: str) -> PlayableAsset
    def prepare_assets_from_set(asset_set: dict) -> list[PlayableAsset]
    def assemble(assets: list, config: PlayableConfig) -> tuple[str, PlayableMetadata]
    def export(html: str, output_path: Path) -> Path
    def validate_export(html: str) -> dict[str, bool]
```

#### Image Processing Pipeline

```
Download Image → Resize (max 512px) → Compress → Base64 Encode → Embed
```

Compression uses Pillow with:
- JPEG: quality=85, optimize=True
- PNG: optimize=True (for transparency)

#### Phaser.js Template Structure

```html
<!DOCTYPE html>
<html>
<head>
    <!-- Meta tags, styles -->
</head>
<body>
    <div id="game-container"></div>

    <!-- Phaser CDN -->
    <script src="phaser.min.js"></script>

    <!-- MRAID Handler -->
    <script>
        var mraid = window.mraid || null;
        function openStoreUrl() { ... }
    </script>

    <!-- Game Scenes -->
    <script>
        class BootScene { preload() { /* load base64 assets */ } }
        class HookScene { /* 3 second attention grabber */ }
        class GameplayScene { /* 15 second core loop */ }
        class CTAScene { /* 5 second call to action */ }
    </script>
</body>
</html>
```

#### Timing Constants

```python
HOOK_DURATION_MS = 3000      # 3 seconds
GAMEPLAY_DURATION_MS = 15000 # 15 seconds
CTA_DURATION_MS = 5000       # 5 seconds
TOTAL_DURATION_MS = 23000    # 23 seconds total
```

---

## 3. Data Flow

### 3.1 End-to-End Pipeline

```
[User Input]
     │
     ▼
[Screenshot Upload] ──────────────────────────────────────────┐
     │                                                        │
     ▼                                                        ▼
[CompetitorSpy.analyze_screenshots()]                    [Context]
     │                                                        │
     ├────────────────────┬───────────────────────────────────┘
     ▼                    │
[Claude Vision API]       │
     │                    │
     ▼                    │
[AnalysisResult]          │
     │                    │
     ▼                    │
[StyleRecipe] ◄───────────┘
     │
     ▼
[StyleManager.create_style_from_recipe()]
     │
     ▼
[Layer.ai createStyle mutation]
     │
     ▼
[ManagedStyle (styleId, dashboardUrl)]
     │
     ▼
[AssetForger.start_session(styleId)]
     │
     ▼
[Credit Check] ──── <50 ──► [ABORT with error]
     │
     │ ≥50
     ▼
[ForgeSession created]
     │
     ▼
[forge_from_preset("hook_character")]
     │
     ▼
[Layer.ai forge mutation]
     │
     ▼
[Poll forgeTaskStatus] ─── timeout ──► [ForgeTimeoutError]
     │
     │ COMPLETED
     ▼
[ForgedAsset (imageId, imageUrl)]
     │
     ├─── Set referenceImageId if first asset
     ▼
[Repeat for remaining presets]
     │
     ▼
[PlayableAssembler.prepare_assets_from_set()]
     │
     ▼
[Download, resize, compress, base64 encode]
     │
     ▼
[PlayableAssembler.assemble(assets, config)]
     │
     ▼
[Template substitution]
     │
     ▼
[Validate size < 5MB]
     │
     ▼
[Export index.html]
```

### 3.2 State Management

Streamlit session state tracks pipeline progress:

```python
session_state = {
    "current_step": 1,           # Wizard step (1-3)
    "layer_style_id": None,      # Selected Layer.ai style ID
    "layer_style_name": None,    # Style name for display
    "style_config": None,        # StyleConfig for prompt enhancement
    "asset_set": None,           # Generated assets (AssetSet)
    "workspace_info": None,      # WorkspaceInfo with credits
    "playable_html": None,       # Assembled HTML string
    "playable_metadata": None,   # PlayableMetadata
}
```

---

## 4. API Integration

### 4.1 Layer.ai GraphQL Schema (Subset)

For complete API documentation, see [layer_api_reference.md](layer_api_reference.md).

#### Queries

```graphql
# Get workspace credits
query GetWorkspaceUsage($input: GetWorkspaceUsageInput!) {
    getWorkspaceUsage(input: $input) {
        __typename
        ... on WorkspaceUsage {
            entitlement { balance, hasAccess }
        }
        ... on Error { code, message }
    }
}

# List available styles (only COMPLETE styles can be used)
query ListStyles($input: ListStylesInput!) {
    listStyles(input: $input) {
        __typename
        ... on StylesResult {
            styles { id, name, status, type }
        }
        ... on Error { code, message }
    }
}

# Poll generation status
query GetInferencesById($input: GetInferencesByIdInput!) {
    getInferencesById(input: $input) {
        __typename
        ... on InferencesResult {
            inferences { id, status, errorCode, files { id, status, url } }
        }
        ... on Error { code, message }
    }
}
```

#### Mutations

```graphql
# Generate images (styleId is REQUIRED)
mutation GenerateImages($input: GenerateImagesInput!) {
    generateImages(input: $input) {
        __typename
        ... on Inference {
            id
            status
            files { id, status, url }
        }
        ... on Error { type, code, message }
    }
}
```

**IMPORTANT**: The `styleId` field is REQUIRED even though the schema shows it as optional. The API returns "At least one style must be provided" without it.

### 4.2 Anthropic Claude API

Uses `anthropic` Python SDK for vision:

```python
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=2000,
    messages=[{
        "role": "user",
        "content": [
            {"type": "image", "source": {"type": "base64", ...}},
            {"type": "text", "text": STYLE_EXTRACTION_PROMPT}
        ]
    }]
)
```

---

## 5. Configuration

### 5.1 Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| LAYER_API_URL | No | https://api.app.layer.ai/v1/graphql | GraphQL endpoint |
| LAYER_API_KEY | Yes | - | Layer.ai API key |
| LAYER_WORKSPACE_ID | Yes | - | Workspace ID |
| ANTHROPIC_API_KEY | Yes | - | Claude API key (for future vision features) |
| CLAUDE_MODEL | No | claude-sonnet-4-20250514 | Vision model |
| DEBUG | No | false | Debug mode |
| LOG_LEVEL | No | INFO | Logging level |
| FORGE_POLL_TIMEOUT | No | 60 | Max generation poll seconds |
| API_FETCH_TIMEOUT | No | 15 | Max seconds for initial API fetches |
| MIN_CREDITS_REQUIRED | No | 50 | Credit threshold |
| MAX_PLAYABLE_SIZE_MB | No | 5.0 | Max export size |
| MAX_IMAGE_DIMENSION | No | 512 | Max image pixels |

### 5.2 Settings Class

```python
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
    )

    layer_api_url: str = "https://api.app.layer.ai/v1/graphql"
    layer_api_key: str
    layer_workspace_id: str
    anthropic_api_key: str
    # ... etc
```

---

## 6. Error Handling Strategy

### 6.1 Error Categories

| Category | Handling | User Feedback |
|----------|----------|---------------|
| Configuration | Fail fast at startup | Show required env vars |
| Network | Retry with backoff | Show retry progress |
| API Error | Log + surface to user | Show error message |
| Credit Insufficient | Block operation | Show credit warning |
| Timeout | Abort with context | Show timeout message |
| Validation | Block export | Show validation failures |

### 6.2 Logging Strategy

Structured logging with context:

```python
logger.info(
    "Forge completed",
    task_id=task_id,
    duration=f"{elapsed:.1f}s",
    image_id=result.image_id,
)
```

---

## 7. Testing Strategy

### 7.1 Test Categories

| Category | Location | Purpose |
|----------|----------|---------|
| Unit Tests | `tests/test_*.py` | Individual function testing |
| Integration | `tests/integration/` | API client testing |
| E2E | `tests/e2e/` | Full pipeline testing |

### 7.2 Mocking Strategy

- Mock `httpx.AsyncClient` for API tests
- Mock `anthropic.Anthropic` for vision tests
- Use fixtures for sample images and responses

---

## 8. Deployment

### 8.1 Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Run Streamlit
streamlit run src/app.py
```

### 8.2 Production Considerations (Future)

- Use `gunicorn` with `uvicorn` workers
- Configure Streamlit for multi-user access
- Add Redis for session caching
- Implement rate limiting

---

## 9. Security Considerations

### 9.1 Secrets Management

- API keys in environment variables only
- `.env` in `.gitignore`
- No secrets in logs or error messages

### 9.2 Input Validation

- File upload type checking
- URL format validation
- Size limits on uploads

### 9.3 Output Sanitization

- No user input directly in HTML templates
- Base64 encoding for all embedded content

---

## 10. Future Enhancements

### 10.1 Near-Term

- [ ] Vision-based style analysis (Claude Vision integration)
- [ ] Batch playable generation
- [ ] Style template library
- [ ] Enhanced error recovery
- [ ] Export to multiple formats (MRAID 2.0)

### 10.2 Long-Term

- [ ] Multi-workspace support
- [ ] Team collaboration features
- [ ] Analytics integration
- [ ] A/B testing framework
- [ ] CI/CD pipeline for playables
