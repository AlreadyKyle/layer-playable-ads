# Layer.ai Playable Studio (LPS)

**Intelligence → Playable Ad Automation Platform**

LPS transforms competitor game analysis into production-ready HTML5 playable ads using Layer.ai's style system and AI-powered vision analysis.

---

## Overview

```
Select Style → Generate Assets → Export Playable
 (Layer.ai)      (Layer.ai)       (Phaser.js)
```

LPS provides a 3-step wizard:

1. **Select Style** - Choose a trained style from your Layer.ai workspace
2. **Generate Assets** - Create hook, gameplay, and CTA assets using Layer.ai
3. **Export Playable** - Assemble MRAID 3.0 compliant HTML5 playable ads

**Important**: Layer.ai requires pre-trained styles (LoRAs/checkpoints). You must create and train styles in your Layer.ai workspace before using this app.

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

**Automated Git Scripts Included:**
- `./sync.sh` - Fetch and pull latest changes
- `./save.sh "message"` - Quick commit and push
- `./git-status.sh` - Comprehensive status check

**[📖 Full Mac Desktop Workflow Guide](docs/desktop_workflow.md)**

---

### Option 2: Streamlit Cloud (Easiest Cloud Testing!)

**Deploy and test instantly - no local setup required!**

1. **Deploy to Streamlit Cloud**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Sign in with GitHub
   - Click **New app**
   - Select this repository (`AlreadyKyle/layer-playable-ads`)
   - Main file: `streamlit_app.py`
   - Click **Deploy**

2. **Configure Secrets** (in Streamlit Cloud dashboard)
   - Go to your app settings (gear icon)
   - Click **Secrets**
   - Add your API keys in TOML format:
   ```toml
   LAYER_API_KEY = "your_layer_api_key_here"
   LAYER_WORKSPACE_ID = "your_workspace_id_here"
   ANTHROPIC_API_KEY = "your_anthropic_api_key_here"
   ```
   - Click **Save**

3. **Test Your App**
   - Your app is live at `https://your-app-name.streamlit.app`
   - Share the URL with anyone for testing
   - Changes pushed to GitHub auto-deploy!

**Benefits:**
- Free hosting for public repos
- Auto-deploy on git push
- Shareable URL for testing
- No server management

---

### Option 3: GitHub Codespaces (Development Environment)

**Full development environment in your browser!**

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

### Option 4: Manual Local Installation

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

### Style Selection

- Browse trained styles from your Layer.ai workspace
- Filter by status (only COMPLETE styles can be used)
- Manual style ID entry as fallback
- Deep links to Layer.ai dashboard

### Asset Generation

- Credit guard (blocks if < 50 credits)
- Reference image consistency across all assets
- UA-optimized presets organized by timing:
  - **Hook (3s)**: Characters, items - grab attention
  - **Gameplay (15s)**: Backgrounds, collectibles - engage user
  - **CTA (5s)**: Buttons, banners - drive installs
- Exponential backoff polling for generation status

### Playable Assembly

- Phaser.js 3.70 game engine
- MRAID 3.0 compliance for ad networks
- Responsive canvas scaling
- Embedded Base64 assets (no external dependencies)
- Single-file HTML export (< 5MB)
- Multi-network export (IronSource, Unity, AppLovin, Facebook, Google)

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
from src.layer_client import LayerClientSync

client = LayerClientSync()

# Get workspace info (includes credits)
info = client.get_workspace_info()
print(f"Credits: {info.credits_available}")

# List available styles (only COMPLETE styles can be used)
styles = client.list_styles(limit=50)
for style in styles:
    if style["status"] == "COMPLETE":
        print(f"{style['name']}: {style['id']}")

# Generate image with a trained style (styleId is REQUIRED)
result = client.generate_with_polling(
    prompt="game character, dynamic pose",
    style_id="your-trained-style-id",
)
print(f"Generated: {result.image_url}")
```

### Playable Assembly

```python
from src.playable import PlayableAssembler, PlayableConfig

assembler = PlayableAssembler()

# Prepare assets from generated asset set
prepared = assembler.prepare_asset_set(asset_set)

# Configure
config = PlayableConfig(
    title="My Playable",
    store_url_ios="https://apps.apple.com/app/...",
    store_url_android="https://play.google.com/store/apps/...",
)

# Assemble
html, metadata = assembler.assemble(prepared, config)
print(f"Size: {metadata.file_size_formatted}")
```

For complete API documentation, see [docs/layer_api_reference.md](docs/layer_api_reference.md).

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

- [x] Style selection from Layer.ai workspace
- [x] Asset generation with trained styles
- [x] UA-optimized presets (3-15-5 timing)
- [x] Playable assembly with Phaser.js
- [x] Multi-network export
- [x] Single-file HTML export

### Future

- [ ] Vision-based style analysis (Claude Vision)
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
