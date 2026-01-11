# Playable Ad Generator - Complete Refactor Plan

## Executive Summary

This document outlines a complete architectural refactor to transform the current prototype into a system that can actually generate game-specific playable ads. The current implementation has a fundamental disconnect between goals and execution that requires rebuilding core components.

---

## Current State vs. Desired State

### What Exists Now

```
Current Flow:
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│  1. User selects pre-trained Layer.ai style                        │
│                    ↓                                                │
│  2. System generates generic assets (character, background, etc.)  │
│                    ↓                                                │
│  3. Assets injected into SINGLE generic Phaser template            │
│                    ↓                                                │
│  4. Output: "Tap to collect circles" game for ALL games            │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**Problems:**
1. No game input - user selects a "style" not a "game"
2. No game analysis - mechanics are never identified
3. Single template - same "tap collectibles" output regardless of game type
4. No gameplay matching - a match-3 game gets the same output as a runner

### What We Need

```
Desired Flow:
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│  1. User inputs game (App Store URL or screenshots)                 │
│                    ↓                                                │
│  2. Claude Vision analyzes game:                                    │
│     - Core mechanic type (match-3, runner, puzzle, etc.)            │
│     - Visual style (cartoon, realistic, pixel art)                  │
│     - Key game elements (characters, items, UI patterns)            │
│                    ↓                                                │
│  3. System selects appropriate GAME TEMPLATE from library           │
│     - match3_template.html for match-3 games                        │
│     - runner_template.html for endless runners                      │
│     - tapper_template.html for idle/clicker games                   │
│     - etc.                                                          │
│                    ↓                                                │
│  4. Layer.ai generates game-specific assets based on analysis       │
│                    ↓                                                │
│  5. Assets + config injected into selected template                 │
│                    ↓                                                │
│  6. Output: Game-specific playable ad that mimics the core mechanic │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Core Architecture Components

### Component 1: Game Input & Analysis

**Purpose:** Take a game as input and extract everything needed to build a playable ad.

**Input Options:**
- App Store URL (scrape screenshots + metadata)
- Direct screenshot upload (1-5 screenshots)
- Game name + platform (use search to find)

**Output (GameAnalysis):**
```json
{
  "game_name": "Candy Crush Saga",
  "platform": "iOS",
  "publisher": "King",
  "mechanic_type": "match-3",
  "mechanic_details": {
    "grid_size": "9x9",
    "match_minimum": 3,
    "direction": "adjacent",
    "special_items": ["striped", "wrapped", "color_bomb"]
  },
  "visual_style": {
    "art_type": "cartoon_2d",
    "color_palette": ["#FF6B6B", "#4ECDC4", "#FFE66D", "#95E1D3"],
    "theme": "candy_fantasy"
  },
  "assets_needed": [
    {"type": "tile_red", "description": "Red candy piece, round, glossy"},
    {"type": "tile_blue", "description": "Blue candy piece, round, glossy"},
    {"type": "tile_green", "description": "Green candy piece, round, glossy"},
    {"type": "tile_yellow", "description": "Yellow candy piece, round, glossy"},
    {"type": "background", "description": "Candy kingdom background, colorful"}
  ],
  "recommended_template": "match3"
}
```

### Component 2: Game Template Library

**Purpose:** A collection of pre-built Phaser.js templates, each implementing a different core game mechanic.

**Templates Needed (Priority Order):**

| Template | Game Types | Core Interaction |
|----------|-----------|------------------|
| `match3.html` | Candy Crush, Bejeweled, Puzzle | Swap adjacent tiles to match 3+ |
| `runner.html` | Subway Surfers, Temple Run | Swipe to change lanes, tap to jump |
| `tapper.html` | Cookie Clicker, idle games | Tap rapidly to accumulate |
| `merger.html` | Merge Dragons, 2048 | Drag items together to merge |
| `puzzle.html` | Block puzzles, Tetris-style | Drag/rotate to fit pieces |
| `shooter.html` | Angry Birds, physics shooters | Aim and release projectile |

**Each template includes:**
- Configurable parameters (speed, difficulty, colors)
- Asset injection points (sprites, backgrounds)
- 3-15-5 timing model (Hook → Gameplay → CTA)
- MRAID compliance
- Base64 asset embedding

### Component 3: Asset Generation Pipeline

**Purpose:** Generate game-specific assets using Layer.ai, guided by the game analysis.

**Process:**
1. Receive `assets_needed` from GameAnalysis
2. For each asset:
   - Build prompt from description + visual_style
   - Check if user has appropriate Layer.ai style
   - Generate with Layer.ai API
   - Download and compress for size limits
3. Return asset set mapped to template requirements

**Key Difference from Current:**
- Assets are game-specific, not generic categories
- Prompts are built from game analysis, not hardcoded presets
- Asset types match template requirements (e.g., match-3 needs tile sprites)

### Component 4: Template Assembly Engine

**Purpose:** Combine the selected template, generated assets, and game config into a final playable.

**Process:**
1. Load template matching `recommended_template`
2. Inject Base64-encoded assets at designated points
3. Configure game parameters from `mechanic_details`
4. Apply visual styling from `visual_style`
5. Validate size constraints (< 5MB)
6. Export for target ad networks

---

## Detailed Implementation Plan

### Phase 1: Game Analysis Pipeline (Foundation)

**Goal:** Build the Claude Vision-powered game analysis system.

**Files to Create/Modify:**
```
src/
├── analysis/
│   ├── __init__.py
│   ├── game_analyzer.py      # Main analysis orchestrator
│   ├── screenshot_fetcher.py # Fetch from App Store URLs
│   ├── mechanic_classifier.py # Identify game type
│   └── style_extractor.py    # Extract visual style
```

**Key Classes:**

```python
# game_analyzer.py
@dataclass
class GameAnalysis:
    game_name: str
    platform: str
    mechanic_type: MechanicType  # Enum: MATCH3, RUNNER, TAPPER, etc.
    mechanic_details: dict
    visual_style: VisualStyle
    assets_needed: list[AssetRequirement]
    recommended_template: str
    confidence_score: float

class GameAnalyzer:
    def __init__(self, anthropic_client):
        self.client = anthropic_client

    async def analyze_from_screenshots(
        self,
        screenshots: list[bytes],
        game_name: Optional[str] = None
    ) -> GameAnalysis:
        """Analyze game from screenshots using Claude Vision."""

    async def analyze_from_app_store(
        self,
        url: str
    ) -> GameAnalysis:
        """Fetch screenshots from App Store and analyze."""
```

**Claude Vision Prompt (Mechanic Classification):**
```
You are a mobile game analyst. Analyze these screenshots and identify:

1. GAME TYPE: Choose ONE from:
   - MATCH3: Games where you match 3+ similar items (Candy Crush, Bejeweled)
   - RUNNER: Endless runner games (Subway Surfers, Temple Run)
   - TAPPER: Idle/clicker games (Cookie Clicker, Idle Miner)
   - MERGER: Games where you combine items (Merge Dragons, 2048)
   - PUZZLE: Block/shape puzzles (Tetris, Block Blast)
   - SHOOTER: Aim and shoot physics (Angry Birds)
   - OTHER: Describe if none match

2. CORE MECHANIC: Describe the single most important player action

3. VISUAL STYLE: Art direction, colors, theme

4. KEY ASSETS: List 5-8 specific visual elements needed to recreate this game's look

Respond in JSON format.
```

### Phase 2: Template Library (Core Mechanics)

**Goal:** Create 4-6 Phaser.js templates implementing different game mechanics.

**Files to Create:**
```
src/templates/
├── __init__.py
├── base_template.py          # Shared template logic
├── match3_template.html      # Match-3 mechanics
├── runner_template.html      # Endless runner
├── tapper_template.html      # Idle clicker
├── merger_template.html      # Merge mechanic
└── template_config.py        # Template registry
```

**Template Structure (Example: match3_template.html):**

```html
<!DOCTYPE html>
<html>
<head>
    <!-- Standard MRAID setup -->
</head>
<body>
    <script src="phaser.min.js"></script>
    <script>
        // CONFIGURABLE PARAMETERS (injected by assembler)
        const CONFIG = {
            gridWidth: ${GRID_WIDTH},      // e.g., 7
            gridHeight: ${GRID_HEIGHT},    // e.g., 9
            tileTypes: ${TILE_TYPES},      // e.g., 4
            matchMinimum: ${MATCH_MIN},    // e.g., 3
            backgroundColor: '${BG_COLOR}',
            assets: ${ASSET_MANIFEST}       // Base64 tiles
        };

        // HOOK SCENE (3 seconds)
        class HookScene extends Phaser.Scene {
            create() {
                // Show game title, animated tiles falling
                // "Tap to Play!" prompt
            }
        }

        // GAMEPLAY SCENE (15 seconds)
        class GameplayScene extends Phaser.Scene {
            create() {
                // Build grid
                // Handle swipe/tap to swap tiles
                // Detect and clear matches
                // Drop new tiles
                // Score tracking
            }

            handleSwap(tile1, tile2) {
                // Actual match-3 logic
            }

            checkMatches() {
                // Find and clear matches
            }
        }

        // CTA SCENE (5 seconds)
        class CTAScene extends Phaser.Scene {
            create() {
                // Show score, "Great Job!"
                // Install button with MRAID
            }
        }
    </script>
</body>
</html>
```

**Template Registry:**

```python
# template_config.py
TEMPLATE_REGISTRY = {
    MechanicType.MATCH3: {
        "template": "match3_template.html",
        "required_assets": ["tile_1", "tile_2", "tile_3", "tile_4", "background"],
        "config_schema": {
            "grid_width": {"type": "int", "default": 7, "min": 5, "max": 9},
            "grid_height": {"type": "int", "default": 9, "min": 7, "max": 12},
            "tile_types": {"type": "int", "default": 4, "min": 3, "max": 6},
        }
    },
    MechanicType.RUNNER: {
        "template": "runner_template.html",
        "required_assets": ["player", "obstacle", "collectible", "background"],
        "config_schema": {
            "lanes": {"type": "int", "default": 3},
            "speed": {"type": "float", "default": 5.0},
        }
    },
    # ... etc
}
```

### Phase 3: Asset Generation Refactor

**Goal:** Generate assets based on game analysis, not generic categories.

**Changes to `asset_forger.py`:**

```python
class GameAssetGenerator:
    """Generate assets specific to analyzed game."""

    def __init__(self, layer_client: LayerClient):
        self.client = layer_client

    async def generate_for_game(
        self,
        analysis: GameAnalysis,
        style_id: str
    ) -> dict[str, GeneratedAsset]:
        """Generate all assets needed for a game's template."""

        template_info = TEMPLATE_REGISTRY[analysis.mechanic_type]
        required_assets = template_info["required_assets"]

        generated = {}
        for asset_key in required_assets:
            # Find matching requirement from analysis
            requirement = self._find_requirement(
                asset_key,
                analysis.assets_needed
            )

            # Build prompt from requirement + visual style
            prompt = self._build_prompt(requirement, analysis.visual_style)

            # Generate with Layer.ai
            result = await self.client.generate_with_polling(
                prompt=prompt,
                style_id=style_id
            )

            generated[asset_key] = result

        return generated
```

### Phase 4: Assembly System Update

**Goal:** Select template based on game type and assemble with generated assets.

```python
class PlayableBuilder:
    """Build playable ads from analysis + assets."""

    def __init__(self):
        self.templates = self._load_templates()

    def build(
        self,
        analysis: GameAnalysis,
        assets: dict[str, GeneratedAsset],
        config: PlayableConfig
    ) -> tuple[str, PlayableMetadata]:
        """Build complete playable from game analysis and assets."""

        # 1. Select template
        template = self.templates[analysis.mechanic_type]

        # 2. Prepare assets (Base64 encode)
        asset_manifest = self._prepare_assets(assets)

        # 3. Build config from analysis
        game_config = self._build_game_config(analysis)

        # 4. Inject into template
        html = template.render(
            assets=asset_manifest,
            config=game_config,
            store_urls=config.store_urls,
            timing={
                "hook": 3000,
                "gameplay": 15000,
                "cta": 5000
            }
        )

        # 5. Validate and return
        return self._validate_and_package(html)
```

### Phase 5: New UI Workflow

**Goal:** Redesign Streamlit UI around game input, not style selection.

**New Flow:**
```
┌─────────────────────────────────────────────────────────────────────┐
│ Step 1: Enter Game                                                  │
│ ┌──────────────────────────────────────────────────────────────┐    │
│ │ Enter App Store URL or upload screenshots                   │    │
│ │ [https://apps.apple.com/app/candy-crush-saga/id553834731]   │    │
│ │                                                              │    │
│ │ OR                                                           │    │
│ │                                                              │    │
│ │ [Upload Screenshots] (up to 5 images)                        │    │
│ └──────────────────────────────────────────────────────────────┘    │
│                                                                     │
│ [Analyze Game] →                                                    │
└─────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│ Step 2: Review Analysis                                             │
│ ┌──────────────────────────────────────────────────────────────┐    │
│ │ Game: Candy Crush Saga                                       │    │
│ │ Type: MATCH-3 (95% confidence)                               │    │
│ │ Template: match3_template                                    │    │
│ │                                                              │    │
│ │ Visual Style:                                                │    │
│ │ - Cartoon 2D                                                 │    │
│ │ - Vibrant colors: 🔴🔵🟢🟡                                    │    │
│ │                                                              │    │
│ │ Assets to Generate:                                          │    │
│ │ ☑ Red candy tile                                             │    │
│ │ ☑ Blue candy tile                                            │    │
│ │ ☑ Green candy tile                                           │    │
│ │ ☑ Yellow candy tile                                          │    │
│ │ ☑ Background                                                 │    │
│ └──────────────────────────────────────────────────────────────┘    │
│                                                                     │
│ Select Layer.ai Style: [Dropdown of trained styles]                 │
│                                                                     │
│ [Generate Assets] →                                                 │
└─────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│ Step 3: Preview & Export                                            │
│ ┌──────────────────────────────────────────────────────────────┐    │
│ │ [Live Playable Preview]                                      │    │
│ │                                                              │    │
│ │ ┌──────────────────────────────────┐                         │    │
│ │ │        CANDY CRUSH STYLE         │                         │    │
│ │ │        ┌───┬───┬───┬───┐         │                         │    │
│ │ │        │ 🔴│ 🔵│ 🔴│ 🟢│         │                         │    │
│ │ │        ├───┼───┼───┼───┤         │                         │    │
│ │ │        │ 🟡│ 🔴│ 🔵│ 🔴│         │                         │    │
│ │ │        └───┴───┴───┴───┘         │                         │    │
│ │ │                                  │                         │    │
│ │ │         Tap to Swap!             │                         │    │
│ │ └──────────────────────────────────┘                         │    │
│ └──────────────────────────────────────────────────────────────┘    │
│                                                                     │
│ [Download index.html]  [Export for All Networks]                    │
└─────────────────────────────────────────────────────────────────────┘
```

---

## File Structure After Refactor

```
layer-playable-ads/
├── src/
│   ├── app.py                    # Redesigned Streamlit UI
│   │
│   ├── analysis/                 # NEW: Game analysis
│   │   ├── __init__.py
│   │   ├── game_analyzer.py      # Main orchestrator
│   │   ├── screenshot_fetcher.py # App Store scraping
│   │   ├── mechanic_classifier.py# Game type detection
│   │   └── models.py             # GameAnalysis, MechanicType, etc.
│   │
│   ├── templates/                # NEW: Template library
│   │   ├── __init__.py
│   │   ├── base.py               # Base template class
│   │   ├── registry.py           # Template registry
│   │   ├── match3.html           # Match-3 template
│   │   ├── runner.html           # Runner template
│   │   ├── tapper.html           # Tapper template
│   │   ├── merger.html           # Merger template
│   │   └── puzzle.html           # Puzzle template
│   │
│   ├── generation/               # REFACTORED: Asset generation
│   │   ├── __init__.py
│   │   ├── game_asset_generator.py # Game-specific generation
│   │   └── layer_client.py       # Moved from src/
│   │
│   ├── assembly/                 # REFACTORED: Playable assembly
│   │   ├── __init__.py
│   │   ├── builder.py            # Template + assets → playable
│   │   └── exporter.py           # Multi-network export
│   │
│   └── utils/
│       ├── __init__.py
│       └── helpers.py            # Settings, logging
│
├── docs/
│   ├── REFACTOR_PLAN.md          # This document
│   ├── PRD.md                    # Rewritten PRD
│   ├── architecture.md           # Updated architecture
│   └── templates.md              # Template documentation
│
└── tests/
    ├── test_analyzer.py
    ├── test_templates.py
    └── test_builder.py
```

---

## Critical Success Factors

### 1. Template Quality

The templates are the heart of this system. Each template must:
- Implement a believable, fun core mechanic
- Be configurable (grid size, speed, colors)
- Work within 5MB size limit
- Follow 3-15-5 timing model
- Be MRAID 3.0 compliant

**Recommendation:** Start with 3 templates (match3, runner, tapper) and expand.

### 2. Analysis Accuracy

Claude Vision must reliably classify games. Key strategies:
- Use multiple screenshots for better context
- Have Claude explain its reasoning
- Allow user to override classification
- Build confidence scoring

### 3. Layer.ai Style Requirement

**Important limitation:** Layer.ai requires pre-trained styles. Users must:
1. Train a style on Layer.ai using game screenshots
2. Use that style ID in this app

**Mitigation:**
- Guide users through style training
- Support manual style ID entry
- Consider pre-training common styles (cartoon, realistic, pixel art)

### 4. Asset Quality

Generated assets must fit the template requirements:
- Correct dimensions for grid tiles
- Transparent backgrounds for sprites
- Consistent visual style across assets

---

## Implementation Priority

| Priority | Component | Effort | Impact |
|----------|-----------|--------|--------|
| P0 | Match-3 Template | High | Critical - proves concept |
| P0 | Game Analyzer | Medium | Critical - enables workflow |
| P1 | Runner Template | Medium | High - second most common |
| P1 | New UI Workflow | Medium | High - user experience |
| P2 | Tapper Template | Low | Medium - simple mechanic |
| P2 | Merger Template | Medium | Medium - popular genre |
| P3 | Puzzle Template | Medium | Low - less common |

---

## Success Metrics

After refactor, the system should:

1. **Accept a game as input** - Not a style
2. **Correctly classify 80%+ of games** - Into appropriate template category
3. **Generate game-specific playables** - Match-3 games get match-3 mechanics
4. **Produce working HTML5 ads** - Playable in browser, < 5MB
5. **Export to major networks** - Google, Unity, IronSource, etc.

---

## Next Steps

1. **Write the new PRD** - Align documentation with this plan
2. **Create Match-3 Template** - First working template
3. **Build Game Analyzer** - Claude Vision integration
4. **Refactor UI** - New 3-step workflow
5. **Test End-to-End** - Analyze → Generate → Export
6. **Expand Templates** - Add runner, tapper, etc.

---

## Appendix: Why This Will Work

### Layer.ai's Role

Layer.ai is an **image generation** service, not a game engine. Its role is:
- Generate consistent visual assets (characters, tiles, backgrounds)
- Apply trained art styles to prompts
- Produce game-ready PNG/JPEG images

It cannot generate game code or mechanics. That's what the template library is for.

### Claude Vision's Role

Claude Vision is a **visual analysis** service. Its role is:
- Classify game mechanics from screenshots
- Extract visual style information
- Identify key game elements

It cannot generate playable code either. But it can tell us WHICH template to use.

### The Template Library

This is the key innovation. Pre-built templates that:
- Implement actual game mechanics in Phaser.js
- Are configurable for different games
- Accept generated assets for visual styling

**The templates are the "game engine" - Layer.ai provides the art, Claude provides the intelligence to select and configure.**

This architecture is feasible because:
1. Game mechanics are finite - there are only ~10-15 common types
2. Phaser.js is battle-tested for HTML5 games
3. Templates can be highly configurable
4. The combination creates believable, game-specific playables
