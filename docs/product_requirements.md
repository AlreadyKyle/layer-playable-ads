# Product Requirements Document (PRD)
## Layer.ai Playable Studio (LPS)

**Version**: 0.1.0
**Status**: MVP / Prototype
**Last Updated**: 2025-01-06

---

## Executive Summary

Layer.ai Playable Studio (LPS) is an "Intelligence → Playable Ad" automation platform that transforms competitor analysis into production-ready HTML5 playable ads. By leveraging Layer.ai's GraphQL API and AI-powered vision analysis, LPS enables UA managers to generate high-performing playable ads in minutes instead of days.

---

## Problem Statement

### Current Pain Points

1. **Manual Style Extraction**: UA teams manually analyze competitor games to understand visual styles, a time-consuming and inconsistent process.

2. **Template Limitations**: Existing playable ad tools rely on rigid templates that produce generic-looking ads.

3. **Prompt Engineering Overhead**: AI-powered alternatives require extensive prompt crafting for each asset.

4. **Inconsistent Output**: Without systematic style management, generated assets lack visual coherence.

5. **Technical Barrier**: Creating MRAID-compliant playable ads requires specialized development skills.

### Market Opportunity

The mobile UA market is projected to exceed $120B by 2026. Playable ads consistently outperform static and video ads, with:
- 32% higher CTR than video ads
- 47% higher CVR than interstitials
- Lower CPI due to higher engagement

---

## Solution Overview

LPS addresses these challenges through a 3-step workflow:

```
Select Style → Generate Assets → Export Playable
 (Layer.ai)      (Layer.ai)       (Phaser.js)
```

**Note**: Layer.ai requires pre-trained styles (LoRAs/checkpoints) for image generation.
Users must create and train styles in Layer.ai before using this app.

### Core Value Proposition

| For | LPS Provides |
|-----|--------------|
| UA Managers | One-click playable generation from competitor analysis |
| Creative Teams | Consistent visual style across all ad variants |
| Performance Teams | A/B testable playable variants at scale |
| Engineering | Zero-code playable ad creation |

---

## Target Users

### Primary Persona: Senior UA Manager

- **Name**: Alex Chen
- **Role**: Senior UA Manager at mobile gaming studio
- **Goals**:
  - Launch new playable ad variants quickly
  - Maintain visual consistency with game brand
  - Demonstrate ROI to leadership
- **Pain Points**:
  - Creative bottleneck for new playable ads
  - Inconsistent quality from external vendors
  - Long turnaround times (2-3 weeks per playable)

### Demo Scenario

Alex is preparing a demo for the CRO to show how Layer.ai can modernize the playable ad workflow. They need to:
1. Analyze a top competitor's visual style
2. Generate matching assets using Layer.ai
3. Produce a working playable ad
4. Complete all of this in under 30 minutes

---

## Functional Requirements

### Module A: Competitor Spy (Vision Intelligence)

**FR-A1**: Accept game screenshots (PNG, JPG, WebP) as input
**FR-A2**: Accept App Store URLs with page screenshots
**FR-A3**: Extract structured Style Recipe using Claude Vision
**FR-A4**: Output JSON format with: styleName, prefix[], technical[], negative[], palette

**Style Recipe Schema**:
```json
{
  "styleName": "Bright Casual Match-3",
  "prefix": ["cartoon", "vibrant", "2D flat"],
  "technical": ["cel-shaded", "soft shadows", "clean lines"],
  "negative": ["realistic", "dark", "photographic"],
  "palette": {
    "primary": "#FF6B6B",
    "accent": "#4ECDC4"
  },
  "referenceImageId": null
}
```

### Module B: Automated Layer Workflow

**FR-B1**: Create styles via Layer.ai `createStyle` mutation
**FR-B2**: Store and track `styleId` for subsequent operations
**FR-B3**: Generate deep links to Layer.ai dashboard for manual tweaking
**FR-B4**: Support style listing and retrieval

### Module C: Smart Forge & Credit Guard

**FR-C1**: Query workspace credits before any forge operation
**FR-C2**: Block generation if credits < 50 (configurable threshold)
**FR-C3**: Set `referenceImageId` from first generated asset
**FR-C4**: Propagate `referenceImageId` to all subsequent variants
**FR-C5**: Poll `forgeTaskStatus` with exponential backoff (max 60s)
**FR-C6**: Provide UA-specific presets for common asset types:
  - Hook assets (character, item)
  - Gameplay assets (background, elements)
  - CTA assets (button, banner)

### Module D: Playable Assembler

**FR-D1**: Generate Phaser.js-based playable ads
**FR-D2**: Implement responsive canvas scaling
**FR-D3**: Support MRAID 3.0 specification
**FR-D4**: Implement timing model:
  - Hook: 3 seconds
  - Core Loop: 15 seconds
  - CTA: 5 seconds
**FR-D5**: Compress images via Pillow (max 512px dimension)
**FR-D6**: Embed all assets as Base64 data URIs
**FR-D7**: Export single `index.html` file
**FR-D8**: Validate export is < 5MB

---

## Non-Functional Requirements

### Performance

- **NFR-P1**: Style extraction completes in < 30 seconds
- **NFR-P2**: Individual forge operations complete in < 60 seconds
- **NFR-P3**: Full pipeline (analysis → playable) completes in < 10 minutes

### Security

- **NFR-S1**: API keys stored in environment variables, never in code
- **NFR-S2**: No PII collected or stored
- **NFR-S3**: All API calls use HTTPS

### Scalability

- **NFR-SC1**: Designed for single-user demo usage (not production scale)
- **NFR-SC2**: Stateless operations enable future horizontal scaling

### Compatibility

- **NFR-C1**: Generated playables work on iOS Safari 14+
- **NFR-C2**: Generated playables work on Chrome Mobile 90+
- **NFR-C3**: MRAID 3.0 compliant for ad network distribution

---

## User Interface

### Wizard Flow (3 Steps)

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Select Style   │ -> │ Generate Assets │ -> │ Export Playable │
│                 │    │                 │    │                 │
│ • Pick from     │    │ • Select presets│    │ • Configure ad  │
│   Layer.ai      │    │ • Generate      │    │ • Download HTML │
│   workspace     │    │   images        │    │ • Preview       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

**Prerequisite**: Users must have trained styles in their Layer.ai workspace.

### UI Principles

1. **Clarity over Polish**: Enterprise-dark theme, minimal distractions
2. **Progress Visibility**: Clear workflow steps and status indicators
3. **Error Transparency**: Clear error messages with actionable guidance
4. **Deep Links**: Layer.ai dashboard links for advanced users

---

## Success Metrics

### MVP Success Criteria

| Metric | Target |
|--------|--------|
| End-to-end completion | < 10 minutes |
| Playable file size | < 5 MB |
| Style extraction accuracy | Subjective demo approval |
| Asset visual consistency | All variants match reference |
| Playable functionality | Runs on mobile browsers |

### Future KPIs (Post-MVP)

- Time to first playable (TTFP)
- Playable CTR vs. baseline
- User retention in wizard flow
- Credit efficiency (assets per credit)

---

## Constraints

### Technical Constraints

- Single `index.html` export (no external dependencies at runtime)
- Maximum playable size: 5MB
- Maximum image dimension: 512px
- Layer.ai API rate limits apply

### Business Constraints

- Prototype/demo quality (not production-hardened)
- Single workspace support
- No user authentication (demo mode)
- Minimum 50 credits required to operate

### Timeline Constraints

- MVP delivery for Layer.ai team demo
- Focus on quality over feature breadth

---

## Out of Scope (MVP)

- Multi-workspace support
- User authentication/authorization
- Playable analytics integration
- Template library management
- Batch playable generation
- A/B test variant management
- Real-time collaboration
- Version control for styles

---

## Dependencies

### External Services

| Service | Purpose | Status |
|---------|---------|--------|
| Layer.ai GraphQL API | Style/forge operations | Required |
| Anthropic Claude API | Vision analysis | Required |
| Phaser.js CDN | Game engine runtime | Optional fallback |

### Development Dependencies

See `requirements.txt` for full list. Key dependencies:
- Python 3.11+
- Streamlit
- httpx
- anthropic
- Pillow
- pydantic

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Layer.ai API changes | High | Version-pin client, abstract API layer |
| Claude vision inaccuracy | Medium | Allow manual recipe editing |
| Credit exhaustion mid-flow | Medium | Pre-check credits, clear warnings |
| File size exceeds limit | Medium | Image compression, asset pruning |
| MRAID compatibility issues | Low | Test on major ad networks |

---

## Appendix

### A. Competitive Analysis

| Competitor | Approach | LPS Differentiation |
|------------|----------|---------------------|
| sett.ai | Prompt-heavy AI generation | Systematic style extraction |
| Playable Factory | Template-based | Dynamic style adaptation |
| GameByte.ai | Text-to-game | Visual intelligence input |
| Craftsman+ | Templated engine | Layer.ai consistency system |

### B. MRAID 3.0 Requirements

- `mraid.open()` for store redirects
- State change detection (`loading` → `ready`)
- Viewport handling for responsive design

### C. UA Playable Timing Model

```
|<-------- 23 seconds total -------->|
|  3s   |      15s         |   5s   |
| HOOK  |    CORE LOOP     |  CTA   |
| Grab  |    Engage        | Convert|
```

This timing model is **non-negotiable** and must be:
- Designed into the playable structure
- Reflected in all metadata
- Used to inform variant logic
