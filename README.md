# Layer.ai Playable Studio v2.0

**Game-Specific Playable Ad Generator**

Transform any mobile game into a game-specific HTML5 playable ad using AI-powered analysis and Layer.ai asset generation.

---

## Overview

```
Upload Screenshots → AI Analysis → Generate Assets → Export Playable
    (1-5 images)      (Claude Vision)   (Layer.ai)      (Phaser.js)
```

LPS v2.0 creates **game-specific** playable ads, not generic templates:

1. **Upload Game Screenshots** - 1-5 screenshots from any mobile game
2. **AI Game Analysis** - Claude Vision detects game mechanics and visual style
3. **Asset Generation** - Layer.ai creates game-specific art assets
4. **Export Playable** - MRAID 3.0 compliant HTML5 playable with actual gameplay

**Supported Game Mechanics:**
- Match-3 (Candy Crush, Royal Match, etc.)
- Runner (Subway Surfers, Temple Run, etc.)
- Tapper/Idle (Cookie Clicker, Idle Heroes, etc.)
- Merger (Merge Dragons, etc.) - coming soon
- Puzzle (Tetris, etc.) - coming soon
- Shooter - coming soon

---

## Quick Start

### Option 1: Demo Mode (No API Keys Required)

Test the output without any API keys:

1. Launch the app (see installation below)
2. Use the **Quick Demo** section in the sidebar
3. Select a game type and click "Generate Demo"
4. Download and test the playable HTML

### Option 2: Full Workflow

**Prerequisites:**
- Python 3.11+
- Layer.ai API access with trained styles
- Anthropic Claude API access

**Installation:**

```bash
# Clone the repository
git clone https://github.com/AlreadyKyle/layer-playable-ads.git
cd layer-playable-ads

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure API keys
cp .env.example .env
# Edit .env with your API keys
```

**Run:**

```bash
./start.sh
# Or: streamlit run src/app.py
```

Open http://localhost:8501 in your browser.

---

## Configuration

Required environment variables (edit `.env`):

```bash
LAYER_API_KEY=your_layer_api_key          # From Layer.ai dashboard
LAYER_WORKSPACE_ID=your_workspace_id      # From Layer.ai dashboard
ANTHROPIC_API_KEY=your_anthropic_api_key  # From console.anthropic.com
```

**Getting API Keys:**
- **Layer.ai**: [app.layer.ai](https://app.layer.ai) → Settings → API Keys
- **Anthropic**: [console.anthropic.com](https://console.anthropic.com) → API Keys

**Important**: Layer.ai requires pre-trained styles. Create and train styles in your Layer.ai workspace before using the full workflow.

---

## Features

### AI Game Analysis (Claude Vision)

- Automatic game mechanic detection (match-3, runner, tapper, etc.)
- Visual style extraction (art type, colors, theme, mood)
- Game-specific asset identification
- Hook and CTA text suggestions
- Confidence scoring

### Asset Generation (Layer.ai)

- Game-specific prompts based on analysis
- Style-consistent asset generation
- Automatic image optimization for size limits
- Base64 embedding for single-file output

### Template-Based Playables (Phaser.js)

Each game mechanic has a dedicated Phaser.js template:

| Mechanic | Description | Example Games |
|----------|-------------|---------------|
| Match-3 | Grid-based tile matching | Candy Crush, Royal Match |
| Runner | Lane-based endless running | Subway Surfers, Temple Run |
| Tapper | Tap/click accumulation | Cookie Clicker, Idle Heroes |

Templates include:
- 3-15-5 timing (3s hook, 15s gameplay, 5s CTA)
- Touch-optimized controls
- Procedural sound effects (Web Audio API)
- Fallback graphics for demo mode
- MRAID 3.0 compliance

### Export & Compatibility

- Single HTML file (< 5MB)
- Compatible networks: Google Ads, Unity, IronSource, AppLovin
- Facebook-compatible when < 2MB
- ZIP export for Google Ads

---

## Project Structure

```
layer-playable-ads/
├── src/
│   ├── app.py                  # Streamlit UI (4-step wizard)
│   ├── playable_factory.py     # Unified pipeline
│   ├── analysis/               # Claude Vision game analysis
│   │   ├── game_analyzer.py    # Main analyzer
│   │   └── models.py           # Data models
│   ├── generation/             # Asset generation
│   │   ├── game_asset_generator.py  # Layer.ai integration
│   │   ├── dynamic_game_generator.py # Claude code generation
│   │   └── sound_generator.py  # Web Audio API sounds
│   ├── assembly/               # Playable assembly
│   │   └── builder.py          # Template + assets → HTML
│   ├── templates/              # Phaser.js game templates
│   │   ├── registry.py         # Template registry
│   │   ├── match3/template.html
│   │   ├── runner/template.html
│   │   └── tapper/template.html
│   ├── layer_client.py         # Layer.ai GraphQL client
│   └── utils/                  # Shared utilities
├── docs/
│   ├── PRD.md                  # Product requirements
│   ├── REFACTOR_PLAN.md        # Architecture design
│   └── ...
└── tests/
```

---

## API Reference

### PlayableFactory (Recommended)

The unified pipeline for creating playable ads:

```python
from src.playable_factory import PlayableFactory, FactoryConfig

factory = PlayableFactory()

# From screenshots (full pipeline)
result = factory.create_from_screenshots(
    screenshots=["screenshot1.png", "screenshot2.png"],
    style_id="your-layer-style-id",
    store_url="https://apps.apple.com/app/id123"
)

if result.is_valid:
    result.save("playable.html")
    result.save_zip("playable.zip")
    print(f"Created {result.mechanic_type.value} playable: {result.file_size_formatted}")

# Demo mode (no API calls)
demo = factory.create_demo(mechanic_type=MechanicType.MATCH3)
demo.save("demo.html")
```

### Individual Components

```python
# Game Analysis
from src.analysis import GameAnalyzerSync

analyzer = GameAnalyzerSync()
analysis = analyzer.analyze_screenshots(["game.png"])
print(f"Detected: {analysis.mechanic_type.value}")
print(f"Style: {analysis.visual_style.art_type}")

# Asset Generation
from src.generation import GameAssetGenerator

generator = GameAssetGenerator()
assets = generator.generate_for_game(
    analysis=analysis,
    style_id="your-style-id"
)

# Assembly
from src.assembly import PlayableBuilder, PlayableConfig

builder = PlayableBuilder()
result = builder.build(analysis, assets, PlayableConfig(
    game_name="My Game",
    store_url="https://..."
))
```

---

## Playable Timing Model

All playables follow the proven 3-15-5 UA methodology:

| Phase | Duration | Purpose |
|-------|----------|---------|
| Hook | 3 seconds | Grab attention, show game title |
| Gameplay | 15 seconds | Interactive demo of core mechanic |
| CTA | 5 seconds | Score display, download button |

**Total: 23 seconds**

---

## Development

### Running Tests

```bash
pytest tests/ -v --cov=src
```

### Code Formatting

```bash
black src/ tests/
ruff check src/ tests/
```

### Adding New Game Mechanics

1. Create template in `src/templates/{mechanic}/template.html`
2. Register in `src/templates/registry.py`
3. Add mechanic instructions in `src/generation/dynamic_game_generator.py`
4. Test with demo mode

---

## Deployment Options

### Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Deploy from GitHub repository
3. Configure secrets in dashboard

### GitHub Codespaces

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://github.com/codespaces/new?hide_repo_select=true&ref=main)

---

## Constraints

- **Export Size**: < 5 MB (single index.html)
- **Image Dimensions**: Max 512px (for size optimization)
- **MRAID Version**: 3.0
- **Python Version**: 3.11+
- **Layer.ai**: Requires trained styles

---

## Roadmap

### v2.0 (Current)

- [x] Claude Vision game analysis
- [x] Game-specific templates (match-3, runner, tapper)
- [x] Unified PlayableFactory pipeline
- [x] Procedural sound effects
- [x] Demo mode without API keys
- [x] MRAID 3.0 compliance

### Future

- [ ] More game mechanics (merger, puzzle, shooter)
- [ ] Dynamic game generation with Claude
- [ ] Batch processing
- [ ] A/B variant management
- [ ] Analytics integration

---

## License

MIT License - See LICENSE file for details.

---

## Support

For issues and questions:
- Check documentation in `docs/`
- Review development guidelines in `claude.md`
- Open a GitHub issue
