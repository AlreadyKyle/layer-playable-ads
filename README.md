# Layer.ai Playable Studio (LPS)

**Intelligence → Playable Ad Automation Platform**

LPS transforms competitor game analysis into production-ready HTML5 playable ads using Layer.ai's style system and AI-powered vision analysis.

---

## Overview

```
Screenshot → Style Recipe → Forged Assets → Playable Ad
  (Input)     (Vision AI)    (Layer.ai)     (Phaser.js)
```

LPS provides a 4-step wizard that:

1. **Style Intel** - Analyzes competitor screenshots using Claude Vision
2. **Style Lock** - Creates reusable styles in Layer.ai
3. **Variant Forge** - Generates consistent asset variants
4. **Export** - Assembles MRAID 3.0 compliant playable ads

---

## Quick Start

### Option 1: Mac Desktop (Recommended for Development!)

**Use Claude Code desktop app + GitHub Desktop on your Mac**

1. **Clone with GitHub Desktop**
   - Install [GitHub Desktop](https://desktop.github.com/)
   - Clone this repository
   - Switch to `main` branch

2. **Set Up Python**
   ```bash
   cd layer-playable-ads
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Configure API Keys**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

4. **Launch the App**
   ```bash
   ./start.sh
   ```

5. **Open in Claude Code**
   - Install [Claude Code desktop app](https://claude.ai/download)
   - Open the project folder
   - Start developing with AI assistance!

**[📖 Full Mac Desktop Workflow Guide](docs/desktop_workflow.md)**

---

### Option 2: GitHub Codespaces (No Local Setup!)

**Run entirely in your browser - zero installation required!**

1. **Open in Codespaces**
   - Click the green **Code** button on GitHub
   - Select **Codespaces** tab
   - Click **Create codespace on main**

   Or use this badge: [![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://github.com/codespaces/new?hide_repo_select=true&ref=main)

2. **Configure API Keys**
   - Once Codespaces loads, create your `.env` file:
   ```bash
   cp .env.example .env
   ```
   - Edit `.env` with your API keys (see [Configuration](#configuration) below)

3. **Launch the App**
   ```bash
   ./start.sh
   ```
   - Codespaces will automatically forward port 8501
   - Click the notification to open the app in your browser

**That's it!** The app runs in the cloud, accessible from any device with a browser.

**[📖 Full Web Workflow Guide](docs/web_workflow.md)**

---

### Option 3: Manual Local Installation

**Prerequisites:**
- Python 3.11+
- Layer.ai API access
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
```

**Run:**

```bash
./start.sh
# Or manually: streamlit run src/app.py
```

Open http://localhost:8501 in your browser.

---

### Configuration

Required environment variables (edit `.env`):

```bash
LAYER_API_KEY=your_layer_api_key          # From Layer.ai dashboard
LAYER_WORKSPACE_ID=your_workspace_id      # From Layer.ai dashboard
ANTHROPIC_API_KEY=your_anthropic_api_key  # From console.anthropic.com
```

**Getting API Keys:**
- **Layer.ai**: [app.layer.ai](https://app.layer.ai) → Settings → API Keys
- **Anthropic**: [console.anthropic.com](https://console.anthropic.com) → API Keys

---

## Features

### Vision Intelligence (Module A)

- Analyze game screenshots via Claude Vision
- Extract structured Style Recipes
- Support for App Store page analysis
- Color palette extraction

### Automated Workflow (Module B)

- Create styles via Layer.ai GraphQL API
- Deep links to Layer.ai dashboard
- Style versioning and tracking

### Smart Forge (Module C)

- Credit guard (blocks if < 50 credits)
- Reference image consistency
- UA-optimized presets:
  - Hook assets (characters, items)
  - Gameplay assets (backgrounds, elements)
  - CTA assets (buttons, banners)
- Exponential backoff polling

### Playable Assembly (Module D)

- Phaser.js 3.70 game engine
- MRAID 3.0 compliance
- Responsive canvas scaling
- Embedded Base64 assets
- Single-file export (< 5MB)

---

## Playable Timing Model

All generated playables follow the UA methodology:

| Phase | Duration | Purpose |
|-------|----------|---------|
| Hook | 3 seconds | Grab attention |
| Gameplay | 15 seconds | Engage user |
| CTA | 5 seconds | Convert to install |

**Total: 23 seconds**

---

## Project Structure

```
layer-playable-ads/
├── src/
│   ├── app.py              # Streamlit UI
│   ├── layer_client.py     # GraphQL client
│   ├── vision/             # Competitor analysis
│   ├── workflow/           # Style management
│   ├── forge/              # Asset generation
│   ├── playable/           # Playable assembly
│   └── utils/              # Shared utilities
├── docs/
│   ├── product_requirements.md
│   ├── technical_design.md
│   └── architecture.md
├── tests/
└── claude.md               # Development guidelines
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [Mac Desktop Workflow Guide](docs/desktop_workflow.md) | **Complete guide for Mac + Claude Code + GitHub Desktop** |
| [Web Workflow Guide](docs/web_workflow.md) | **Complete guide for GitHub Codespaces workflow** |
| [Product Requirements](docs/product_requirements.md) | PRD with user stories and constraints |
| [Technical Design](docs/technical_design.md) | Implementation details and APIs |
| [Architecture](docs/architecture.md) | System diagrams and decisions |
| [Claude.md](claude.md) | Development guidelines and schemas |

---

## API Reference

### Layer.ai GraphQL

```python
from src.layer_client import LayerClientSync, StyleRecipe

client = LayerClientSync()

# Check credits
credits = client.get_workspace_credits()

# Create style
recipe = StyleRecipe(
    style_name="My Style",
    prefix=["cartoon", "vibrant"],
    technical=["cel-shaded"],
    negative=["realistic"],
    palette_primary="#FF6B6B",
    palette_accent="#4ECDC4",
)
style_id = client.create_style(recipe)

# Forge asset
result = client.forge_with_polling(
    style_id=style_id,
    prompt="game character, dynamic pose",
)
```

### Vision Analysis

```python
from src.vision import CompetitorSpy

spy = CompetitorSpy()
result = spy.analyze_screenshots(["screenshot.png"])

print(result.recipe.style_name)
print(result.genre)
print(result.key_visual_elements)
```

### Playable Assembly

```python
from src.playable import PlayableAssembler, PlayableConfig

assembler = PlayableAssembler()

# Prepare assets
prepared = assembler.prepare_assets_from_set(forged_assets)

# Configure
config = PlayableConfig(
    title="My Playable",
    store_url="https://apps.apple.com/app/...",
)

# Assemble
html, metadata = assembler.assemble(prepared, config)

# Export
assembler.export(html, Path("output/index.html"))
```

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

### Type Checking

```bash
mypy src/
```

---

## Constraints

- **Export Size**: < 5 MB (single index.html)
- **Image Dimensions**: Max 512px
- **Minimum Credits**: 50 required to forge
- **MRAID Version**: 3.0
- **Python Version**: 3.11+

---

## Roadmap

### MVP (Current)

- [x] Vision-based style extraction
- [x] Layer.ai style creation
- [x] Asset forging with presets
- [x] Playable assembly
- [x] Single-file export

### Future

- [ ] Batch playable generation
- [ ] Style template library
- [ ] A/B variant management
- [ ] Analytics integration
- [ ] Multi-workspace support

---

## License

MIT License - See LICENSE file for details.

---

## Contributing

This is a prototype project. For contributions:

1. Create a feature branch
2. Follow guidelines in `claude.md`
3. Update documentation as needed
4. Submit pull request

---

## Support

For issues and questions:
- Check existing documentation
- Review `claude.md` for development guidelines
- Open a GitHub issue
