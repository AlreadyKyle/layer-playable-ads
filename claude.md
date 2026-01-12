# Claude.md - LPS Development Guidelines

This document defines constraints, schemas, and repository etiquette for Claude Code when working on the Layer.ai Playable Studio (LPS) project.

---

## Quick Reference

### Running the App
```bash
# Local development
streamlit run src/app.py
# Opens at http://localhost:8501

# Run tests
pytest tests/ -v

# Test Layer.ai API connection
python scripts/test_layer_api.py
```

### Key Files to Know
| File | Purpose |
|------|---------|
| `src/app.py` | Streamlit web UI (4-step wizard) |
| `src/playable_factory.py` | Unified pipeline orchestrator |
| `src/layer_client.py` | Layer.ai GraphQL API client |
| `src/generation/game_asset_generator.py` | Asset generation with retry |
| `src/templates/registry.py` | Game mechanic templates |
| `docs/IMPLEMENTATION_PLAN.md` | Current work plan |

---

## Project Overview

**Name**: Layer.ai Playable Studio (LPS)
**Version**: 2.1
**Purpose**: AI-powered playable ad generation using Layer.ai + Claude Vision
**Stage**: Active Development

### v2.0 Architecture
- **4-Step Wizard**: Upload Screenshots → Analyze Game → Generate Assets → Export
- **Claude Vision Analysis**: Automatically detects game mechanic type (match-3, runner, tapper)
- **Template-Based Games**: Phaser.js templates for each mechanic type
- **Demo Mode**: Full playable generation without API keys (fallback graphics)
- **Professional Fallbacks**: Gem-style graphics when Layer.ai assets fail

### Architecture Reality
**IMPORTANT**: Layer.ai requires pre-trained styles. Generation uses a `styleId` from the user's Layer.ai workspace. If assets fail, the system uses professional-looking fallback graphics.

### Known Issues
1. **Layer.ai "pixel wizards" error** - Some styles have generation restrictions
2. **Base model (MODEL_URL) styles** may have content filters
3. **Solution**: Use custom-trained styles (LAYER_TRAINED_CHECKPOINT)

---

## Development Workflows

LPS supports multiple development workflows to suit different preferences:

### 1. Mac Desktop Workflow (Recommended for Development)

**Tools:**
- Claude Code desktop app (AI-assisted development)
- GitHub Desktop (visual git management)
- Local Python environment

**Best for:**
- Active development and feature work
- AI-assisted coding with Claude Code
- Full IDE experience
- Offline capability

**Guide:** [docs/desktop_workflow.md](docs/desktop_workflow.md)

### 2. Web Workflow (GitHub Codespaces)

**Tools:**
- Browser-based VS Code
- Cloud Python environment
- GitHub integration

**Best for:**
- Quick demos and testing
- No local setup required
- Working from any device
- Collaborative development

**Guide:** [docs/web_workflow.md](docs/web_workflow.md)

### 3. Manual Local Setup

**Tools:**
- Any text editor or IDE
- Command-line git
- Local Python environment

**Best for:**
- Custom development environments
- Advanced users
- Specific IDE preferences

**Guide:** See [README.md](README.md#option-3-manual-local-installation)

---

## Git Branch Strategy

- **Main branch:** `main` (default production branch)
- **Feature branches:** `feature/description` or `claude/description-xxxxx`
- **All development should target the `main` branch**

---

## Hard Constraints (Non-Negotiable)

### 1. Playable Export Requirements

```
┌────────────────────────────────────────┐
│        EXPORT CONSTRAINTS              │
├────────────────────────────────────────┤
│ Format:      Single index.html         │
│ Max Size:    < 5 MB                    │
│ Max Image:   512px (width or height)   │
│ MRAID:       3.0 compliant             │
│ Runtime:     Self-contained (no fetch) │
└────────────────────────────────────────┘
```

### 2. Timing Model (UA Methodology)

```
│<────────── 23 seconds total ──────────>│
│   3s    │        15s        │    5s    │
│  HOOK   │     GAMEPLAY      │   CTA    │
│  Grab   │      Engage       │ Convert  │
```

These timings are **non-negotiable** and must be:
- Designed into playable structure
- Reflected in all metadata
- Used to inform variant logic

### 3. Credit Guard

```python
# NEVER start forge operations without credit check
MIN_CREDITS_REQUIRED = 50

if workspace_credits.available < MIN_CREDITS_REQUIRED:
    raise InsufficientCreditsError("Block generation")
```

### 4. Visual Consistency

```python
# First asset sets the reference
if session.reference_image_id is None:
    session.reference_image_id = first_forged_asset.image_id

# All subsequent forges MUST use the reference
forge(reference_image_id=session.reference_image_id)
```

---

## Data Schemas

### StyleRecipe (Core Schema)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "StyleRecipe",
  "type": "object",
  "required": ["styleName", "prefix", "technical", "negative", "palette"],
  "properties": {
    "styleName": {
      "type": "string",
      "description": "Human-readable style name",
      "example": "Bright Casual Match-3"
    },
    "prefix": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Style prefix terms for prompts",
      "example": ["cartoon", "vibrant", "2D flat"]
    },
    "technical": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Technical rendering specifications",
      "example": ["cel-shaded", "soft shadows", "clean lines"]
    },
    "negative": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Terms to avoid in generation",
      "example": ["realistic", "dark", "photographic"]
    },
    "palette": {
      "type": "object",
      "required": ["primary", "accent"],
      "properties": {
        "primary": {
          "type": "string",
          "pattern": "^#[0-9A-Fa-f]{6}$",
          "example": "#FF6B6B"
        },
        "accent": {
          "type": "string",
          "pattern": "^#[0-9A-Fa-f]{6}$",
          "example": "#4ECDC4"
        }
      }
    },
    "referenceImageId": {
      "type": ["string", "null"],
      "description": "Layer.ai image ID for consistency"
    }
  }
}
```

### PlayableConfig

```json
{
  "title": "PlayableConfig",
  "type": "object",
  "properties": {
    "title": { "type": "string", "default": "Playable Ad" },
    "width": { "type": "integer", "default": 320 },
    "height": { "type": "integer", "default": 480 },
    "background_color": { "type": "string", "default": "#000000" },
    "store_url": { "type": "string", "format": "uri" },
    "hook_text": { "type": "string", "default": "Play Now!" },
    "cta_text": { "type": "string", "default": "Install Free" },
    "analytics_id": { "type": ["string", "null"] }
  }
}
```

### UA Presets

```python
UA_PRESETS = {
    # Hook assets (3-second intro)
    "hook_character": {
        "category": "hook",
        "prompts": ["expressive game character, dynamic pose, eye-catching"]
    },
    "hook_item": {
        "category": "hook",
        "prompts": ["shiny treasure chest, glowing, magical particles"]
    },

    # Gameplay assets (15-second core loop)
    "gameplay_background": {
        "category": "gameplay",
        "prompts": ["game level background, vibrant colors, depth layers"]
    },
    "gameplay_element": {
        "category": "gameplay",
        "prompts": ["collectible gem, faceted crystal, glowing"]
    },

    # CTA assets (5-second call to action)
    "cta_button": {
        "category": "cta",
        "prompts": ["play now button, glossy, green gradient"]
    },
    "cta_banner": {
        "category": "cta",
        "prompts": ["game logo banner, premium quality"]
    }
}
```

---

## Repository Structure

```
layer-playable-ads/
├── .env.example          # Environment template (COPY to .env)
├── .gitignore
├── README.md
├── requirements.txt
├── pyproject.toml
├── claude.md             # This file
│
├── docs/                 # Documentation
│   ├── IMPLEMENTATION_PLAN.md  # Current work plan
│   ├── architecture.md         # System design
│   ├── layer_api_reference.md  # API documentation
│   └── ...
│
├── scripts/              # Utility scripts
│   └── test_layer_api.py      # API diagnostics
│
├── src/
│   ├── app.py                  # Streamlit 4-step wizard
│   ├── playable_factory.py     # Unified pipeline orchestrator
│   ├── layer_client.py         # Layer.ai GraphQL client
│   │
│   ├── analysis/               # Claude Vision game analysis
│   │   └── game_analyzer.py    # Mechanic detection, style extraction
│   │
│   ├── generation/             # Asset generation
│   │   ├── game_asset_generator.py  # Layer.ai with retry
│   │   ├── dynamic_game_generator.py  # (experimental)
│   │   └── sound_generator.py  # Procedural audio
│   │
│   ├── assembly/               # Playable HTML5 assembly
│   │   └── builder.py          # Template injection, optimization
│   │
│   ├── templates/              # Game mechanic templates
│   │   ├── registry.py         # MechanicType enum, registration
│   │   ├── match3/template.html
│   │   ├── runner/template.html
│   │   └── tapper/template.html
│   │
│   └── utils/
│       └── helpers.py          # Settings, logging, validation
│
└── tests/
    ├── test_e2e.py            # End-to-end tests (demo mode)
    ├── test_layer_client.py   # API client tests
    └── ...
```

### Key Classes (v2.0)

| Class | Location | Purpose |
|-------|----------|---------|
| `PlayableFactory` | `playable_factory.py` | Main pipeline orchestrator |
| `LayerClientSync` | `layer_client.py` | Layer.ai API with sync wrapper |
| `GameAnalyzer` | `analysis/game_analyzer.py` | Claude Vision game analysis |
| `GameAssetGenerator` | `generation/game_asset_generator.py` | Asset generation with retry |
| `PlayableBuilder` | `assembly/builder.py` | Build HTML5 playables |
| `MechanicType` | `templates/registry.py` | Enum: MATCH3, RUNNER, TAPPER |
| `StyleValidation` | `generation/game_asset_generator.py` | Style validation before generation |

---

## Development Rules

### Code Style

1. **Python 3.11+** - Use modern features (type hints, `|` union, etc.)
2. **Async by default** - Use async for I/O operations
3. **Dataclasses for models** - Prefer dataclasses over dicts
4. **Structured logging** - Use structlog with context
5. **Explicit imports** - No star imports

### Error Handling

```python
# DO: Use custom exceptions
raise InsufficientCreditsError(f"Need {required}, have {available}")

# DO: Log with context
logger.error("Forge failed", task_id=task_id, error=str(e))

# DON'T: Silently swallow errors
try:
    risky_operation()
except Exception:
    pass  # NEVER do this
```

### API Mocking

When Layer.ai API is unavailable:

```python
# DO: Mock clearly with obvious markers
class MockLayerClient:
    def forge(self, ...):
        logger.warning("MOCK: Using mock forge response")
        return ForgeResult(
            task_id="mock-task-id",
            status=ForgeTaskStatus.COMPLETED,
            image_url="https://placehold.co/512x512/png?text=MOCK",
        )
```

### Documentation Updates

When making changes, update these docs as needed:
- `changelog.md` - Version changes
- `project_tracker.md` - Task completion
- `feature_backlog.md` - New ideas/issues

---

## Environment Variables

### Required (App Will Not Start Without)

```bash
LAYER_API_KEY=your_layer_api_key_here
LAYER_WORKSPACE_ID=your_workspace_id_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

### Optional (Have Defaults)

```bash
LAYER_API_URL=https://api.app.layer.ai/v1/graphql
CLAUDE_MODEL=claude-sonnet-4-20250514
DEBUG=false
LOG_LEVEL=INFO
FORGE_POLL_TIMEOUT=60
MIN_CREDITS_REQUIRED=50
MAX_PLAYABLE_SIZE_MB=5.0
MAX_IMAGE_DIMENSION=512
```

---

## Layer.ai API Reference

**IMPORTANT**: See [docs/layer_api_reference.md](docs/layer_api_reference.md) for complete API documentation.

### Critical Knowledge

1. **Styles are trained ML models** - You cannot generate with just text prompts
2. **`styleId` is REQUIRED** for `generateImages` mutation
3. **Only COMPLETE styles work** - Check `status` before using a style
4. **Status enum values**: `IN_PROGRESS`, `COMPLETE`, `FAILED`, `CANCELLED`, `DELETED`

### Key Queries

```graphql
# List available styles (only use COMPLETE ones)
query ListStyles($input: ListStylesInput!) {
    listStyles(input: $input) {
        __typename
        ... on StylesResult {
            styles { id name status type }
        }
        ... on Error { code message }
    }
}

# Poll generation status
query GetInferencesById($input: GetInferencesByIdInput!) {
    getInferencesById(input: $input) {
        __typename
        ... on InferencesResult {
            inferences { id status errorCode files { id status url } }
        }
        ... on Error { code message }
    }
}
```

### Key Mutations

```graphql
# Generate images (styleId is REQUIRED)
mutation GenerateImages($input: GenerateImagesInput!) {
    generateImages(input: $input) {
        __typename
        ... on Inference {
            id
            status
            files { id status url }
        }
        ... on Error { type code message }
    }
}
```

### GenerateImagesInput (Correct Structure)

```json
{
    "input": {
        "workspaceId": "workspace-id",
        "styleId": "style-id",       // REQUIRED
        "prompt": "generation prompt" // At top level, NOT in parameters
    }
}
```

---

## Testing Checklist

Before committing:

- [ ] All API keys removed from code
- [ ] `.env` is not committed
- [ ] Playable exports validate < 5MB
- [ ] Timing model preserved (3-15-5)
- [ ] Credit check happens before forge
- [ ] Reference image propagates to variants
- [ ] MRAID detection present in output
- [ ] No hardcoded URLs (use env vars)

---

## Common Patterns

### Async to Sync Wrapper

```python
def sync_method(self, *args, **kwargs):
    return asyncio.run(self._async_method(*args, **kwargs))
```

### Retry with Backoff

```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(httpx.HTTPStatusError),
)
async def api_call(self):
    ...
```

### Session State Pattern (Streamlit)

```python
if "key" not in st.session_state:
    st.session_state.key = default_value
```

---

## Competitive Context

When making product decisions, remember competitors:

| Competitor | Approach | Our Differentiation |
|------------|----------|---------------------|
| sett.ai | Prompt-heavy | Systematic style extraction |
| Playable Factory | Templates | Dynamic style adaptation |
| GameByte.ai | Text-to-game | Visual intelligence input |
| Craftsman+ | Templated engine | Layer.ai consistency |

**Strategic Direction**: Avoid template-only or prompt-only approaches. Lean into Layer.ai's style system, consistency, and GraphQL automation.

---

## Troubleshooting

### Layer.ai Asset Generation Fails

**Error: "Oops! Our pixel wizards need a moment..."**

1. **Check style type**: Run `python scripts/test_layer_api.py`
   - `MODEL_URL` styles (base models) often have restrictions
   - Prefer `LAYER_TRAINED_CHECKPOINT` styles

2. **Simplify prompts**: The system auto-retries with simpler prompts
   - First try: Game-specific prompt from analysis
   - Retry: Simple generic prompt like "red gemstone"

3. **Check credits**: Ensure workspace has sufficient credits

4. **Use demo mode**: If assets keep failing, the system uses professional fallback graphics

### Playable Doesn't Work

1. **Check browser console**: Open DevTools → Console for JavaScript errors
2. **Verify Phaser loaded**: Look for `Phaser.Game` in HTML
3. **Test template**: Run `pytest tests/test_e2e.py -v`

### API Connection Issues

```bash
# Run diagnostics
python scripts/test_layer_api.py

# Check environment
cat .env | grep -E "^(LAYER|ANTHROPIC)"
```

### Common Fixes

| Issue | Solution |
|-------|----------|
| All tiles same color | Fixed in v2.1 - update template |
| Game stuck on hook | Fixed error handling in Match3Scene |
| Style not found | Verify style ID and status is COMPLETE |
| HTTP 403 | Check API key permissions and workspace ID |

---

## Contact & Resources

- **Implementation Plan**: `docs/IMPLEMENTATION_PLAN.md`
- **Layer.ai API Reference**: `docs/layer_api_reference.md`
- **Phaser.js Docs**: https://phaser.io/docs
- **MRAID 3.0 Spec**: https://www.iab.com/guidelines/mraid/
- **Anthropic Docs**: https://docs.anthropic.com
