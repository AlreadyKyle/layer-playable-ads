# Claude.md - LPS Development Guidelines

This document defines constraints, schemas, and repository etiquette for Claude Code when working on the Layer.ai Playable Studio (LPS) project.

---

## Project Overview

**Name**: Layer.ai Playable Studio (LPS)
**Version**: MVP v1.0
**Purpose**: AI-powered playable ad generation using Layer.ai
**Stage**: Production-ready MVP

### MVP v1.0 Features
- Style-based asset generation with Layer.ai
- 3-15-5 timing model (Hook-Gameplay-CTA)
- Multi-network export (IronSource, Unity, AppLovin, Facebook, Google)
- MRAID 3.0 compliant HTML5 output
- Industry-standard ad network specifications

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
├── CLAUDE.md             # This file
│
├── docs/                 # Documentation
│   └── ...
│
├── src/
│   ├── __init__.py       # Package init (v1.0.0)
│   ├── app.py            # Streamlit 3-step wizard
│   ├── layer_client.py   # Layer.ai API client
│   │
│   ├── forge/            # Asset generation
│   │   ├── __init__.py
│   │   └── asset_forger.py  # AssetGenerator, presets
│   │
│   ├── playable/         # Playable assembly
│   │   ├── __init__.py
│   │   ├── assembler.py  # PlayableAssembler, network exports
│   │   └── templates/
│   │       └── phaser_base.html
│   │
│   └── utils/
│       ├── __init__.py
│       └── helpers.py
│
└── tests/
    └── __init__.py
```

### Key Classes (MVP v1.0)

| Class | Location | Purpose |
|-------|----------|---------|
| `LayerClientSync` | `layer_client.py` | Layer.ai API with sync wrapper |
| `StyleConfig` | `layer_client.py` | Style keywords and negative prompts |
| `AssetGenerator` | `forge/asset_forger.py` | Generate assets from presets |
| `AssetType` | `forge/asset_forger.py` | Enum: HOOK_CHARACTER, GAMEPLAY_BACKGROUND, etc. |
| `PlayableAssembler` | `playable/assembler.py` | Build HTML5 playables |
| `AdNetwork` | `playable/assembler.py` | Enum: IRONSOURCE, UNITY, APPLOVIN, etc. |

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

## GraphQL Reference

### Workspace Credits Query

```graphql
query GetWorkspaceCredits($workspaceId: ID!) {
    workspace(id: $workspaceId) {
        credits {
            available
            used
            total
        }
    }
}
```

### Create Style Mutation

```graphql
mutation CreateStyle($input: CreateStyleInput!) {
    createStyle(input: $input) {
        id
        name
        prefix
        technical
        negative
    }
}
```

### Start Forge Mutation

```graphql
mutation StartForge($input: ForgeInput!) {
    forge(input: $input) {
        taskId
        status
    }
}
```

### Poll Forge Status Query

```graphql
query GetForgeTaskStatus($taskId: ID!) {
    forgeTask(id: $taskId) {
        id
        status
        result {
            imageUrl
            imageId
        }
        error {
            message
        }
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

## Contact & Resources

- **Layer.ai API Docs**: https://docs.layer.ai
- **Phaser.js Docs**: https://phaser.io/docs
- **MRAID 3.0 Spec**: https://www.iab.com/guidelines/mraid/
- **Anthropic Docs**: https://docs.anthropic.com
