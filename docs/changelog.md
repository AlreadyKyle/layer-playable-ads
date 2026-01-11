# Changelog

All notable changes to Layer.ai Playable Studio (LPS) will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Planned
- Vision-based style analysis (Claude Vision)
- Batch playable generation
- Style template library
- Export format options (MRAID 2.0, VAST)

---

## [1.0.0] - 2025-01-11

### Changed

#### Architecture Redesign
- **BREAKING**: Simplified from 4-step to 3-step wizard
  - Removed Style Intel and Style Lock steps
  - Layer.ai requires pre-trained styles, not extracted recipes
  - New flow: Select Style → Generate Assets → Export Playable

#### Layer.ai Integration (`layer_client.py`)
- Fixed GraphQL schema to match actual API
- `styleId` is now REQUIRED for `generateImages` mutation
- Correct status enum values: `IN_PROGRESS`, `COMPLETE`, `FAILED`
- Use `url` field on File type (not `signedUrl` or `thumbnails.url`)
- `prompt` at top level of input (not nested in `parameters`)

#### Performance Improvements
- Added `@st.cache_data` for workspace info and styles fetch
- Configurable `api_fetch_timeout` (default 15s) for initial loads
- Show loading spinners during first API fetch

#### Streamlit UI (`app.py`)
- 3-step wizard:
  1. Select Style (choose from Layer.ai workspace)
  2. Generate Assets (hook, gameplay, CTA)
  3. Export Playable (multi-network, MRAID 3.0)
- Style selector showing only COMPLETE styles
- Manual style ID entry as fallback

### Added
- `docs/layer_api_reference.md` - Complete Layer.ai API documentation
- Multi-network export (IronSource, Unity, AppLovin, Facebook, Google)
- Configurable `api_fetch_timeout` environment variable

### Fixed
- App loading hang (pulsing skeleton) on startup
- GraphQL "Cannot query field 'url' on type 'FileThumbnails'" error
- GraphQL "At least one style must be provided" error
- Streamlit session state errors on widget interactions

---

## [0.1.0] - 2025-01-06

### Added

#### Core Infrastructure
- Project scaffolding with Python 3.11+ support
- Streamlit-based web interface with enterprise-dark theme
- pydantic-settings for type-safe configuration
- structlog for structured logging

#### Layer.ai Integration (`layer_client.py`)
- Async GraphQL client with retry logic
- Sync wrapper for Streamlit compatibility
- Workspace credit querying
- Style CRUD operations
- Forge task management with polling
- Dashboard deep linking

#### Vision Module (`vision/competitor_spy.py`)
- Claude Vision integration for screenshot analysis
- Style Recipe extraction with JSON schema
- Support for multiple screenshot input
- App Store page analysis capability
- Color palette detection

#### Workflow Module (`workflow/style_manager.py`)
- Style lifecycle management
- Local style caching
- Dashboard URL generation

#### Forge Module (`forge/asset_forger.py`)
- Credit guard (minimum 50 credits)
- Session-based forge tracking
- Reference image consistency propagation
- UA preset system:
  - hook_character
  - hook_item
  - gameplay_background
  - gameplay_element
  - cta_button
  - cta_banner
- Batch preset forging

#### Playable Module (`playable/assembler.py`)
- Phaser.js 3.70 template system
- MRAID 3.0 compliance
- Image processing pipeline (resize, compress)
- Base64 asset embedding
- Single-file HTML export
- Size validation (< 5MB)

#### Streamlit UI (`app.py`)
- 4-step wizard flow:
  1. Style Intel (upload/analyze)
  2. Style Lock (review/edit/create)
  3. Variant Forge (preset selection)
  4. Export (assembly/download/preview)
- Session state management
- Progress indicators
- API status sidebar

#### Documentation
- Product Requirements Document (PRD)
- Technical Design Document
- Architecture diagrams
- claude.md development guidelines
- README with quick start guide

### Technical Decisions
- Chose Streamlit over FastAPI+React for rapid prototyping
- Used httpx for async/sync HTTP client flexibility
- Phaser.js for proven MRAID compatibility
- Base64 embedding for single-file export requirement

---

## Version History

| Version | Date | Highlights |
|---------|------|------------|
| 1.0.0 | 2025-01-11 | Architecture redesign: 3-step wizard, Layer.ai API fixes |
| 0.1.0 | 2025-01-06 | Initial MVP scaffold |

---

## Migration Notes

### Upgrading to 0.1.0

This is the initial release. No migration required.

### Environment Variables

New in 0.1.0:
```bash
LAYER_API_KEY=required
LAYER_WORKSPACE_ID=required
ANTHROPIC_API_KEY=required
LAYER_API_URL=optional
CLAUDE_MODEL=optional
DEBUG=optional
LOG_LEVEL=optional
FORGE_POLL_TIMEOUT=optional
MIN_CREDITS_REQUIRED=optional
MAX_PLAYABLE_SIZE_MB=optional
MAX_IMAGE_DIMENSION=optional
```
