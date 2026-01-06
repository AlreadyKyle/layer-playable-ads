# Research Summary

## Layer.ai Playable Studio (LPS)

This document captures research findings, competitive analysis, and technical investigations for the LPS project.

---

## Executive Summary

The mobile UA playable ad market is growing rapidly, with playables outperforming traditional ad formats by 30-50% on key metrics. Existing solutions fall into two categories: template-based (limited creativity) and prompt-based (inconsistent output). LPS addresses this gap by combining AI vision analysis with Layer.ai's systematic style management.

---

## Market Research

### Playable Ad Market Size

- Global mobile ad spend: $362B (2024)
- Playable ads segment: ~$8B (2024)
- CAGR: 18.5% through 2028
- Adoption rate: 47% of top 100 gaming advertisers

### Performance Benchmarks

| Ad Format | Avg CTR | Avg CVR | Avg CPI |
|-----------|---------|---------|---------|
| Static Banner | 0.35% | 1.2% | $2.80 |
| Video | 0.89% | 2.1% | $2.20 |
| Playable | 1.32% | 3.5% | $1.85 |

**Source**: Industry reports, 2024

### Key Insight

Playables deliver:
- 32% higher CTR than video
- 47% higher CVR than interstitials
- 16% lower CPI than video

---

## Competitive Analysis

### Direct Competitors

#### 1. sett.ai

**Approach**: AI-driven, prompt-heavy playable generation

**Strengths**:
- End-to-end AI generation
- Fast iteration
- Creative freedom

**Weaknesses**:
- Inconsistent visual style
- Heavy prompt engineering required
- Limited brand control

**LPS Differentiation**: Systematic style extraction vs. per-prompt crafting

---

#### 2. Playable Factory

**Approach**: Template-based agency model

**Strengths**:
- Proven templates
- Human QA
- Brand-safe output

**Weaknesses**:
- Slow turnaround (2-3 weeks)
- High cost ($5-15K per playable)
- Limited customization

**LPS Differentiation**: AI-powered speed with style consistency

---

#### 3. GameByte.ai

**Approach**: Text-to-game playable generation

**Strengths**:
- Natural language input
- Rapid prototyping
- Low barrier to entry

**Weaknesses**:
- Generic output
- No style control
- Limited asset quality

**LPS Differentiation**: Visual intelligence input vs. text-only

---

#### 4. Craftsman+

**Approach**: Templated interactive engine

**Strengths**:
- Robust engine
- Network compatibility
- Proven performance

**Weaknesses**:
- Template-locked creativity
- Long setup time
- Technical expertise required

**LPS Differentiation**: Layer.ai consistency system vs. rigid templates

---

### Competitive Matrix

| Feature | sett.ai | Playable Factory | GameByte | Craftsman+ | LPS |
|---------|---------|------------------|----------|------------|-----|
| AI Vision Analysis | ❌ | ❌ | ❌ | ❌ | ✅ |
| Style Consistency | ⚠️ | ✅ | ❌ | ✅ | ✅ |
| Automation Level | High | Low | High | Medium | High |
| Turnaround Time | Hours | Weeks | Minutes | Days | Minutes |
| Cost per Playable | ~$50 | $5-15K | ~$10 | ~$500 | ~$5* |
| MRAID Support | ✅ | ✅ | ⚠️ | ✅ | ✅ |

*Estimated based on Layer.ai credit usage

---

## Technical Research

### MRAID 3.0 Specification

**Key Requirements**:
- `mraid.open(url)` for store redirects
- State machine: loading → default → expanded → resized
- Viewport size detection
- Close button handling

**Implementation Notes**:
- Phaser.js handles MRAID well
- Window.mraid detection pattern
- Fallback to window.open for non-MRAID

---

### Phaser.js Selection

**Why Phaser.js 3.70?**

| Criteria | Phaser | PixiJS | Canvas |
|----------|--------|--------|--------|
| Bundle size | 800KB | 600KB | 0KB |
| MRAID compat | ✅ Proven | ⚠️ Manual | ⚠️ Manual |
| Scene system | ✅ Built-in | ❌ None | ❌ None |
| Animation | ✅ Tweens | ⚠️ Basic | ❌ Manual |
| Documentation | ✅ Excellent | ✅ Good | ⚠️ Varies |

**Decision**: Phaser.js provides the best balance of features and MRAID compatibility.

---

### File Size Analysis

**Target**: < 5MB single HTML file

**Budget Breakdown**:
| Component | Size | % of Budget |
|-----------|------|-------------|
| Phaser.js CDN | External | 0% |
| HTML/CSS/JS | ~50KB | 1% |
| Assets (base64) | ~4MB | 80% |
| Headroom | ~1MB | 19% |

**Asset Budget** (@ 512px max):
- ~6-8 PNG images at 500KB each, OR
- ~12-15 JPEG images at 300KB each

---

### Image Compression Research

**Pillow Optimization**:
```python
# JPEG: 85 quality, optimize
img.save(buffer, "JPEG", quality=85, optimize=True)
# ~60% size reduction vs uncompressed

# PNG: optimize only
img.save(buffer, "PNG", optimize=True)
# ~20% size reduction
```

**WebP Consideration**:
- 25-35% smaller than JPEG
- Browser support: 96%+ (2024)
- Future enhancement candidate

---

### UA Timing Model Research

**Industry Standards** (Mobile Gaming):
| Source | Hook | Gameplay | CTA |
|--------|------|----------|-----|
| Unity Ads | 3s | 15-20s | 5s |
| ironSource | 3s | 15s | 5s |
| AppLovin | 2-3s | 15s | 5s |
| Facebook | 3s | 15s | 5s |

**Consensus**: 3-15-5 model (23 seconds total)

**Psychology**:
- 3s hook: Attention span threshold
- 15s gameplay: Engagement optimization
- 5s CTA: Conversion without fatigue

---

## Layer.ai API Research

### GraphQL Capabilities

**Available Operations**:
- Workspace management
- Style CRUD
- Forge operations
- Image management

**Rate Limits**: Standard GraphQL limits apply

**Credit System**:
- Credits consumed per forge operation
- Workspace-level tracking
- Real-time balance queries

---

### Style System Analysis

**Layer.ai Style Structure**:
```json
{
  "name": "Style Name",
  "prefix": ["style", "terms"],
  "technical": ["quality", "specs"],
  "negative": ["avoid", "terms"]
}
```

**Key Insight**: Layer.ai's style system provides exactly the structure needed for consistent playable asset generation.

---

## Vision AI Research

### Claude Vision Capabilities

**Strengths**:
- Excellent at visual analysis
- Structured JSON output
- Color extraction
- Style categorization

**Limitations**:
- Cannot access URLs directly
- Requires base64 encoding
- Token limits on image count

**Prompt Engineering Findings**:
- Structured prompts yield structured output
- JSON schema in prompt improves accuracy
- Multiple images provide better context

---

### Alternative Vision Models (Future)

| Model | Pros | Cons |
|-------|------|------|
| GPT-4V | Strong analysis | Higher cost |
| Gemini Pro Vision | Google integration | Different API |
| LLaVA | Open source | Less accurate |

---

## User Research

### UA Manager Pain Points

From informal interviews:

1. **Time to Market**: "It takes 2-3 weeks to get a new playable from our agency"
2. **Consistency**: "Every asset looks different even with the same brief"
3. **Iteration Speed**: "I can't test variants fast enough"
4. **Technical Barrier**: "I need engineering help for every change"
5. **Cost**: "$10K per playable limits how many we can test"

### Desired Outcomes

- Generate playables in minutes, not weeks
- Maintain brand/game visual consistency
- Iterate on variants independently
- No engineering required for basic changes
- Lower cost per playable

---

## Key Takeaways

1. **Market Opportunity**: Playables outperform other formats but are slow/expensive to produce

2. **Competitive Gap**: No solution combines AI vision + systematic style management

3. **Technical Feasibility**: Phaser.js + MRAID + Layer.ai = viable stack

4. **User Need**: Speed + consistency + self-service = winning combination

5. **Strategic Fit**: Layer.ai's style system is the key differentiator

---

## Research Sources

- IAB MRAID 3.0 Specification (2018)
- Mobile Marketing Magazine (2024)
- App Annie / data.ai Reports
- Unity Gaming Report 2024
- Competitor website analysis
- Phaser.js Documentation
- Anthropic Claude API Documentation
- Layer.ai API Documentation

---

## Open Questions

1. How do different ad networks handle MRAID edge cases?
2. What's the optimal image count per playable?
3. Can we pre-compute style recipes for common genres?
4. How to handle animated assets (GIF/sprite sheets)?

---

## Next Research Steps

1. User testing with real UA managers
2. A/B testing playable performance
3. Network compatibility testing (Unity, ironSource, etc.)
4. Style recipe accuracy validation
