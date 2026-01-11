# Product Requirements Document: Game-Specific Playable Ad Generator

**Version:** 2.0
**Status:** Active Development
**Last Updated:** January 2026

---

## 1. Product Vision

Create an application that takes a mobile game as input and generates a working, game-specific playable advertisement using Claude Vision for analysis and Layer.ai for asset generation.

### 1.1 The Problem

Playable ads (interactive HTML5 game demos) convert 3-7x better than video ads, but creating them requires:
- Game developers who understand the source game's mechanics
- Artists who can recreate the game's visual style
- Technical expertise in HTML5/Phaser.js and ad network compliance

This makes playable ads expensive and time-consuming to produce.

### 1.2 The Solution

An AI-powered pipeline that:
1. **Analyzes** any mobile game from screenshots or App Store URL
2. **Identifies** the core mechanic (match-3, runner, puzzle, etc.)
3. **Generates** matching art assets using Layer.ai
4. **Assembles** a working playable ad from pre-built game templates
5. **Exports** in ad network-compliant formats

---

## 2. User Workflow

### 2.1 Target User

A mobile game marketer or UA (User Acquisition) specialist who:
- Has access to game screenshots or App Store listing
- Has a Layer.ai subscription with trained styles
- Needs playable ads for various ad networks
- Is NOT a game developer or programmer

### 2.2 End-to-End Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│  USER INPUT                                                         │
│  ─────────                                                          │
│  • App Store URL (https://apps.apple.com/app/id...)                 │
│  • OR: Upload 1-5 game screenshots                                  │
│  • OR: Enter game name for search                                   │
│                                                                     │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│  STEP 1: GAME ANALYSIS (Claude Vision)                              │
│  ─────────────────────────────────────                              │
│  Automatic extraction of:                                           │
│  • Game name and publisher                                          │
│  • Core mechanic type (match-3, runner, tapper, etc.)               │
│  • Visual style (cartoon, realistic, pixel art)                     │
│  • Color palette                                                    │
│  • Key game elements (characters, tiles, obstacles)                 │
│  • Recommended template selection                                   │
│                                                                     │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│  STEP 2: USER REVIEW & CONFIGURATION                                │
│  ───────────────────────────────────                                │
│  User can:                                                          │
│  • Confirm or adjust detected game type                             │
│  • Select Layer.ai style for asset generation                       │
│  • Customize asset list if needed                                   │
│  • Set difficulty/speed parameters                                  │
│                                                                     │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│  STEP 3: ASSET GENERATION (Layer.ai)                                │
│  ───────────────────────────────────                                │
│  For each required asset:                                           │
│  • Build prompt from game analysis + visual style                   │
│  • Generate with selected Layer.ai style                            │
│  • Download and optimize (resize, compress)                         │
│  • Convert to Base64 for embedding                                  │
│                                                                     │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│  STEP 4: PLAYABLE ASSEMBLY                                          │
│  ────────────────────────────                                       │
│  • Select game template based on mechanic type                      │
│  • Inject generated assets                                          │
│  • Configure game parameters                                        │
│  • Apply 3-15-5 timing model                                        │
│  • Validate size (< 5MB)                                            │
│                                                                     │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│  STEP 5: PREVIEW & EXPORT                                           │
│  ────────────────────────────                                       │
│  • Live preview in browser                                          │
│  • Download single HTML file                                        │
│  • Export for specific networks:                                    │
│    - Google Ads (ZIP format)                                        │
│    - Unity Ads (MRAID compliant)                                    │
│    - IronSource                                                     │
│    - Facebook/Meta                                                  │
│    - AppLovin                                                       │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. Supported Game Types

The system supports the following core game mechanics. Each maps to a pre-built Phaser.js template.

| Mechanic Type | Example Games | Core Interaction | Template |
|---------------|---------------|------------------|----------|
| **Match-3** | Candy Crush, Bejeweled | Swap adjacent tiles to match 3+ | `match3.html` |
| **Runner** | Subway Surfers, Temple Run | Swipe lanes, tap to jump | `runner.html` |
| **Tapper/Idle** | Cookie Clicker, Idle Miner | Tap rapidly to accumulate | `tapper.html` |
| **Merger** | Merge Dragons, 2048 | Drag items together | `merger.html` |
| **Puzzle** | Tetris, Block Blast | Fit shapes together | `puzzle.html` |
| **Shooter** | Angry Birds | Aim and release | `shooter.html` |

### 3.1 Template Requirements

Each template must:
- Implement the core mechanic in Phaser.js
- Follow the 3-15-5 timing model (3s hook, 15s gameplay, 5s CTA)
- Accept configurable parameters (speed, difficulty, colors)
- Support asset injection via Base64 data URIs
- Be MRAID 3.0 compliant
- Fit within 5MB when assembled

---

## 4. Functional Requirements

### 4.1 Game Input (FR-INPUT)

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-INPUT-01 | Accept App Store URL and extract game screenshots | P0 |
| FR-INPUT-02 | Accept direct screenshot uploads (1-5 images) | P0 |
| FR-INPUT-03 | Accept game name and search for screenshots | P2 |
| FR-INPUT-04 | Support iOS App Store URLs | P0 |
| FR-INPUT-05 | Support Google Play Store URLs | P1 |

### 4.2 Game Analysis (FR-ANALYSIS)

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-ANALYSIS-01 | Detect game mechanic type with 80%+ accuracy | P0 |
| FR-ANALYSIS-02 | Extract visual style (art type, colors, theme) | P0 |
| FR-ANALYSIS-03 | Identify required assets for template | P0 |
| FR-ANALYSIS-04 | Provide confidence score for classification | P1 |
| FR-ANALYSIS-05 | Allow user override of detected type | P0 |
| FR-ANALYSIS-06 | Extract game name and publisher | P1 |

### 4.3 Asset Generation (FR-ASSETS)

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-ASSETS-01 | Generate assets matching template requirements | P0 |
| FR-ASSETS-02 | Use Layer.ai style selected by user | P0 |
| FR-ASSETS-03 | Build prompts from game analysis | P0 |
| FR-ASSETS-04 | Optimize images for size (< 512px, compressed) | P0 |
| FR-ASSETS-05 | Support transparency for sprites | P0 |
| FR-ASSETS-06 | Convert to Base64 for embedding | P0 |
| FR-ASSETS-07 | Show generation progress | P1 |
| FR-ASSETS-08 | Allow regeneration of individual assets | P2 |

### 4.4 Template Assembly (FR-ASSEMBLY)

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-ASSEMBLY-01 | Select template based on mechanic type | P0 |
| FR-ASSEMBLY-02 | Inject assets at designated placeholders | P0 |
| FR-ASSEMBLY-03 | Configure game parameters from analysis | P0 |
| FR-ASSEMBLY-04 | Apply 3-15-5 timing model | P0 |
| FR-ASSEMBLY-05 | Validate final size < 5MB | P0 |
| FR-ASSEMBLY-06 | Generate asset manifest for template | P0 |

### 4.5 Export (FR-EXPORT)

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-EXPORT-01 | Export single HTML file | P0 |
| FR-EXPORT-02 | Export Google Ads ZIP format | P0 |
| FR-EXPORT-03 | Include MRAID 3.0 handlers | P0 |
| FR-EXPORT-04 | Support store URL configuration (iOS/Android) | P0 |
| FR-EXPORT-05 | Multi-network batch export | P1 |
| FR-EXPORT-06 | Size validation per network | P1 |

### 4.6 Preview (FR-PREVIEW)

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-PREVIEW-01 | Render playable in iframe preview | P0 |
| FR-PREVIEW-02 | Show file size and network compatibility | P0 |
| FR-PREVIEW-03 | Allow replay of playable | P1 |

---

## 5. Non-Functional Requirements

### 5.1 Performance

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-PERF-01 | Game analysis completion | < 30 seconds |
| NFR-PERF-02 | Asset generation (per asset) | < 60 seconds |
| NFR-PERF-03 | Template assembly | < 5 seconds |
| NFR-PERF-04 | UI responsiveness | < 200ms |

### 5.2 Reliability

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-REL-01 | API error handling | Graceful with retry |
| NFR-REL-02 | Session state persistence | Survive page refresh |
| NFR-REL-03 | Partial failure recovery | Continue with available assets |

### 5.3 Ad Network Compliance

| Network | Format | Max Size | Requirements |
|---------|--------|----------|--------------|
| Google Ads | ZIP | 5 MB | ExitAPI for CTAs |
| Unity Ads | HTML | 5 MB | MRAID 3.0, single file |
| IronSource | HTML | 5 MB | MRAID 3.0 |
| Facebook | HTML | 2 MB | No external requests |
| AppLovin | HTML | 5 MB | MRAID 3.0 |

---

## 6. Technical Architecture

### 6.1 Component Diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│                         STREAMLIT UI                                 │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐     │
│  │   Input    │  │  Review    │  │  Generate  │  │   Export   │     │
│  │   Page     │  │   Page     │  │    Page    │  │    Page    │     │
│  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘     │
└────────┼───────────────┼───────────────┼───────────────┼────────────┘
         │               │               │               │
         ▼               ▼               ▼               ▼
┌──────────────────────────────────────────────────────────────────────┐
│                         CORE SERVICES                                │
│                                                                      │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐  │
│  │  GameAnalyzer   │    │ AssetGenerator  │    │ PlayableBuilder │  │
│  │                 │    │                 │    │                 │  │
│  │ • analyze()     │    │ • generate()    │    │ • build()       │  │
│  │ • classify()    │    │ • optimize()    │    │ • export()      │  │
│  └────────┬────────┘    └────────┬────────┘    └────────┬────────┘  │
│           │                      │                      │           │
└───────────┼──────────────────────┼──────────────────────┼───────────┘
            │                      │                      │
            ▼                      ▼                      ▼
┌───────────────────┐  ┌───────────────────┐  ┌───────────────────────┐
│   Claude Vision   │  │    Layer.ai API   │  │   Template Library    │
│   (Anthropic)     │  │   (GraphQL)       │  │   (Phaser.js HTML)    │
│                   │  │                   │  │                       │
│ • Screenshot      │  │ • Style lookup    │  │ • match3.html         │
│   analysis        │  │ • Image generate  │  │ • runner.html         │
│ • Mechanic        │  │ • Status polling  │  │ • tapper.html         │
│   classification  │  │                   │  │ • merger.html         │
└───────────────────┘  └───────────────────┘  └───────────────────────┘
```

### 6.2 Data Flow

```
Screenshot/URL
      │
      ▼
┌─────────────┐
│ GameAnalyzer│ ──────────────────────────────────┐
└─────────────┘                                   │
      │                                           │
      ▼                                           ▼
GameAnalysis {                             Template Selection
  mechanic_type: MATCH3                          │
  visual_style: {...}                            │
  assets_needed: [...]                           │
}                                                │
      │                                          │
      ▼                                          │
┌──────────────┐                                 │
│AssetGenerator│                                 │
└──────────────┘                                 │
      │                                          │
      ▼                                          │
Generated Assets {                               │
  tile_1: <base64>                               │
  tile_2: <base64>                               │
  background: <base64>                           │
}                                                │
      │                                          │
      └─────────────────────┬────────────────────┘
                            │
                            ▼
                   ┌─────────────────┐
                   │ PlayableBuilder │
                   └─────────────────┘
                            │
                            ▼
                   Assembled Playable
                   (index.html < 5MB)
```

### 6.3 Template Library Structure

```
src/templates/
├── base.py                 # Base template class
├── registry.py             # Template → mechanic mapping
│
├── match3/
│   ├── template.html       # Phaser.js match-3 game
│   ├── config.json         # Configurable parameters
│   └── assets.json         # Required asset definitions
│
├── runner/
│   ├── template.html       # Phaser.js runner game
│   ├── config.json
│   └── assets.json
│
├── tapper/
│   ├── template.html       # Phaser.js tapper game
│   ├── config.json
│   └── assets.json
│
└── shared/
    ├── phaser.min.js       # Phaser 3.70 (minified)
    ├── mraid.js            # MRAID 3.0 shim
    └── common.css          # Shared styles
```

---

## 7. User Interface Mockups

### 7.1 Step 1: Game Input

```
╔══════════════════════════════════════════════════════════════════════╗
║  🎮 PLAYABLE AD GENERATOR                                            ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                      ║
║  STEP 1: Enter Your Game                                             ║
║  ━━━━━━━━━━━━━━━━━━━━━━━                                              ║
║                                                                      ║
║  ┌────────────────────────────────────────────────────────────────┐  ║
║  │ App Store URL                                                  │  ║
║  │ ┌──────────────────────────────────────────────────────────┐   │  ║
║  │ │ https://apps.apple.com/app/candy-crush-saga/id553834731  │   │  ║
║  │ └──────────────────────────────────────────────────────────┘   │  ║
║  └────────────────────────────────────────────────────────────────┘  ║
║                                                                      ║
║                           ─── OR ───                                 ║
║                                                                      ║
║  ┌────────────────────────────────────────────────────────────────┐  ║
║  │ Upload Screenshots                                             │  ║
║  │ ┌──────────────────────────────────────────────────────────┐   │  ║
║  │ │  📷 Drop images here or click to upload                  │   │  ║
║  │ │     (1-5 screenshots, PNG/JPG)                           │   │  ║
║  │ └──────────────────────────────────────────────────────────┘   │  ║
║  └────────────────────────────────────────────────────────────────┘  ║
║                                                                      ║
║                      ╔════════════════════╗                          ║
║                      ║   Analyze Game →   ║                          ║
║                      ╚════════════════════╝                          ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
```

### 7.2 Step 2: Analysis Review

```
╔══════════════════════════════════════════════════════════════════════╗
║  🎮 PLAYABLE AD GENERATOR                                            ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                      ║
║  STEP 2: Review Analysis                                             ║
║  ━━━━━━━━━━━━━━━━━━━━━━━                                              ║
║                                                                      ║
║  ┌────────────────────────────────────────────────────────────────┐  ║
║  │ GAME DETECTED                                                  │  ║
║  │                                                                │  ║
║  │ 🎯 Candy Crush Saga                                            │  ║
║  │    by King                                                     │  ║
║  │                                                                │  ║
║  │ ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │  ║
║  │ │             │  │             │  │             │              │  ║
║  │ │ Screenshot1 │  │ Screenshot2 │  │ Screenshot3 │              │  ║
║  │ │             │  │             │  │             │              │  ║
║  │ └─────────────┘  └─────────────┘  └─────────────┘              │  ║
║  └────────────────────────────────────────────────────────────────┘  ║
║                                                                      ║
║  ┌───────────────────────────┐  ┌───────────────────────────────┐   ║
║  │ GAME TYPE                 │  │ VISUAL STYLE                  │   ║
║  │                           │  │                               │   ║
║  │ ◉ Match-3 (95%)           │  │ Art: Cartoon 2D               │   ║
║  │ ○ Runner                  │  │ Theme: Candy Fantasy          │   ║
║  │ ○ Tapper                  │  │                               │   ║
║  │ ○ Merger                  │  │ Colors:                       │   ║
║  │ ○ Puzzle                  │  │ 🔴 🔵 🟢 🟡 🟣 🟠              │   ║
║  └───────────────────────────┘  └───────────────────────────────┘   ║
║                                                                      ║
║  ┌────────────────────────────────────────────────────────────────┐  ║
║  │ ASSETS TO GENERATE                                             │  ║
║  │                                                                │  ║
║  │ ☑ Red candy tile     ☑ Background                             │  ║
║  │ ☑ Blue candy tile    ☑ Score UI                               │  ║
║  │ ☑ Green candy tile                                            │  ║
║  │ ☑ Yellow candy tile                                           │  ║
║  └────────────────────────────────────────────────────────────────┘  ║
║                                                                      ║
║  ┌────────────────────────────────────────────────────────────────┐  ║
║  │ Layer.ai Style                                                 │  ║
║  │ ▼ Candy Art Style (trained)                                    │  ║
║  └────────────────────────────────────────────────────────────────┘  ║
║                                                                      ║
║  ╔════════════════════╗                                              ║
║  ║ Generate Assets →  ║                                              ║
║  ╚════════════════════╝                                              ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
```

### 7.3 Step 3: Export

```
╔══════════════════════════════════════════════════════════════════════╗
║  🎮 PLAYABLE AD GENERATOR                                            ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                      ║
║  STEP 3: Preview & Export                                            ║
║  ━━━━━━━━━━━━━━━━━━━━━━━━                                             ║
║                                                                      ║
║  ┌────────────────────────┐  ┌────────────────────────────────────┐  ║
║  │                        │  │ GENERATED ASSETS                   │  ║
║  │   ┌──────────────┐     │  │                                    │  ║
║  │   │ LIVE PREVIEW │     │  │ 🔴 tile_red    🔵 tile_blue        │  ║
║  │   │              │     │  │ 🟢 tile_green  🟡 tile_yellow      │  ║
║  │   │  ┌──┬──┬──┐  │     │  │ 🎨 background                      │  ║
║  │   │  │🔴│🔵│🔴│  │     │  │                                    │  ║
║  │   │  ├──┼──┼──┤  │     │  ├────────────────────────────────────┤  ║
║  │   │  │🟡│🟢│🔵│  │     │  │ PLAYABLE INFO                      │  ║
║  │   │  └──┴──┴──┘  │     │  │                                    │  ║
║  │   │              │     │  │ Size: 1.8 MB ✓                     │  ║
║  │   │  Tap to Swap │     │  │ Duration: 23 seconds               │  ║
║  │   └──────────────┘     │  │ Template: match3.html              │  ║
║  │                        │  │                                    │  ║
║  │   [▶ Play Again]       │  │ Compatible Networks:               │  ║
║  │                        │  │ ✓ Google  ✓ Unity  ✓ IronSource   │  ║
║  └────────────────────────┘  │ ✓ AppLovin  ✓ Facebook            │  ║
║                              └────────────────────────────────────┘  ║
║                                                                      ║
║  ┌────────────────────────────────────────────────────────────────┐  ║
║  │ STORE URLs                                                     │  ║
║  │ iOS:     https://apps.apple.com/app/id553834731                │  ║
║  │ Android: https://play.google.com/store/apps/details?id=...     │  ║
║  └────────────────────────────────────────────────────────────────┘  ║
║                                                                      ║
║  ╔═══════════════════╗  ╔═══════════════════════╗                    ║
║  ║ Download HTML     ║  ║ Export All Networks   ║                    ║
║  ╚═══════════════════╝  ╚═══════════════════════╝                    ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
```

---

## 8. Success Criteria

### 8.1 MVP Success

The MVP is successful when a user can:

1. **Input a game** via App Store URL or screenshots
2. **Receive accurate analysis** of game type (80%+ accuracy on common types)
3. **Generate matching assets** using their Layer.ai style
4. **Download a working playable** that demonstrates the game's core mechanic
5. **Export for ad networks** in compliant formats

### 8.2 Quality Bar

| Metric | Target |
|--------|--------|
| Game classification accuracy | 80%+ on top 6 mechanic types |
| Playable interactivity | Core mechanic is demonstrable |
| File size compliance | 100% < 5MB (2MB for Facebook) |
| Ad network compatibility | Works on 4+ major networks |
| End-to-end time | < 5 minutes from input to export |

---

## 9. Limitations & Constraints

### 9.1 Layer.ai Dependency

**Constraint:** Layer.ai requires pre-trained styles. Users must:
1. Have an active Layer.ai subscription
2. Train a style using game screenshots BEFORE using this app
3. Wait for style training to complete (can take hours)

**Mitigation:**
- Clear documentation on style training
- Support for manual style ID entry
- Consider pre-training common art styles

### 9.2 Template Coverage

**Constraint:** Only games matching our template library can be processed.

**Current Templates:**
- Match-3 (Candy Crush, Bejeweled)
- Runner (Subway Surfers, Temple Run)
- Tapper (Cookie Clicker, idle games)
- Merger (2048, Merge Dragons)
- Puzzle (Tetris, block puzzles)
- Shooter (Angry Birds, physics games)

**Games NOT supported:**
- Complex RPGs
- Real-time strategy
- Sports simulations
- Multiplayer games
- Story-driven games

### 9.3 Asset Quality

**Constraint:** Generated assets depend on Layer.ai quality.

**Considerations:**
- Assets may not perfectly match source game
- Style training quality affects output
- Some prompts work better than others

---

## 10. Roadmap

### Phase 1: Core MVP (Current)

- [ ] Match-3 template with full gameplay
- [ ] Game analyzer with Claude Vision
- [ ] Layer.ai asset generation (game-specific)
- [ ] New Streamlit UI workflow
- [ ] Google Ads export

### Phase 2: Template Expansion

- [ ] Runner template
- [ ] Tapper template
- [ ] Merger template
- [ ] Multi-network export

### Phase 3: Enhancement

- [ ] Puzzle template
- [ ] Shooter template
- [ ] Asset regeneration
- [ ] A/B variant generation

### Phase 4: Scale

- [ ] Pre-trained style library
- [ ] Batch processing
- [ ] API access
- [ ] Team collaboration

---

## Appendix A: Glossary

| Term | Definition |
|------|------------|
| **Playable Ad** | Interactive HTML5 game demo used as advertisement |
| **MRAID** | Mobile Rich Media Ad Interface Definitions (industry standard) |
| **Core Loop** | The fundamental repeating gameplay mechanic |
| **3-15-5 Model** | 3s hook, 15s gameplay, 5s CTA timing structure |
| **CTA** | Call-to-Action (install button) |
| **Layer.ai** | AI image generation service with trainable styles |
| **Template** | Pre-built Phaser.js game implementing a specific mechanic |
