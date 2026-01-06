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

### Prerequisites

- Python 3.11+
- Layer.ai API access
- Anthropic Claude API access

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/layer-playable-ads.git
cd layer-playable-ads

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your API keys
nano .env
```

Required environment variables:

```
LAYER_API_KEY=your_layer_api_key
LAYER_WORKSPACE_ID=your_workspace_id
ANTHROPIC_API_KEY=your_anthropic_api_key
```

### Run

```bash
streamlit run src/app.py
```

Open http://localhost:8501 in your browser.

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
