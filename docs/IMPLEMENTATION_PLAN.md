# Layer.ai Playable Ads - Comprehensive Implementation Plan

**Created**: 2025-01-12
**Status**: Active Development
**Version**: 2.1 (Post-Audit)

---

## Executive Summary

This document outlines a systematic plan to fix the Layer.ai Playable Studio application. The two major issues are:

1. **Layer.ai asset generation fails** with "Oops! Our pixel wizards need a moment..." error
2. **Fallback graphics look unprofessional** (colored circles instead of game-quality assets)

This plan breaks down the work into testable phases that can be executed incrementally.

---

## Root Cause Analysis

### Issue 1: Layer.ai Asset Generation Failure

**Symptoms:**
- API returns "Oops! Our pixel wizards need a moment to recharge"
- Occurs consistently across different prompts
- Affects all asset types (tiles, backgrounds)

**Potential Causes (in order of likelihood):**

1. **Style Compatibility Issue**
   - Using base `MODEL_URL` style types (e.g., "Trellis 2") instead of custom-trained styles
   - Base models may have usage restrictions or content moderation
   - Documentation says: "Prefer custom trained styles - MODEL_URL types are base models and may have restrictions"

2. **Content Moderation/Filtering**
   - Prompts may trigger content filters
   - Even simple prompts like "colorful gem" may be rejected by certain styles

3. **Rate Limiting**
   - Too many concurrent requests
   - Workspace may be at rate limit threshold

4. **Credit/Entitlement Issues**
   - Workspace may have depleted credits
   - Style may require specific entitlements

5. **Style Not COMPLETE**
   - Style status must be "COMPLETE" for generation
   - Training/incomplete styles will fail

### Issue 2: Poor Fallback Graphics

**Symptoms:**
- When Layer.ai assets fail, game shows basic colored circles
- Visual quality is extremely low
- Does not represent actual game aesthetics

**Root Cause:**
- Fallback graphics were implemented as minimal placeholders
- No attempt to match game visual style
- `createTileSprite()` in match3/template.html uses simple `Phaser.add.circle()`

---

## Implementation Phases

### Phase 1: Diagnostics & Bug Fixes (Critical)

**Goal:** Understand exactly why Layer.ai is failing and fix known bugs.

#### 1.1 Fix Missing GraphQL Query Bug
- **File:** `src/layer_client.py:789-795`
- **Issue:** `get_image()` method calls `QUERIES["get_image"]` which doesn't exist
- **Fix:** Add query to QUERIES dict or remove unused method
- **Test:** Unit test for `get_image()` method

#### 1.2 Add Layer.ai Diagnostic Endpoint
- Create `/test-layer-api` debug page in Streamlit
- Show: workspace credits, style list, style details
- Test generation with minimal prompt
- Log full error responses

#### 1.3 Style Validation
- Before generation, verify style:
  - Exists and is accessible
  - Status is "COMPLETE"
  - Type is compatible (prefer LAYER_TRAINED_CHECKPOINT)
- Show warnings for MODEL_URL styles

#### 1.4 Enhanced Error Logging
- Log full API request/response for failed generations
- Include: prompt, style_id, error code, error message
- Add structured logging for debugging

**Test Checkpoint:** Can view Layer.ai workspace status and styles in debug UI

---

### Phase 2: Layer.ai Generation Reliability

**Goal:** Make asset generation work consistently.

#### 2.1 Prompt Engineering
- **Simplify prompts** - Keep under 20 words
- **Remove style modifiers** - Layer.ai style already encodes visual style
- **Use neutral subjects** - Avoid anything that could trigger filters
- **Test prompts:**
  - `"simple red gemstone"`
  - `"blue circle shape"`
  - `"green square tile"`

#### 2.2 Style Selection Strategy
```
Priority Order:
1. User's custom-trained style (LAYER_TRAINED_CHECKPOINT)
2. Public/featured styles with COMPLETE status
3. MODEL_URL base models (with warning)
```

#### 2.3 Retry Logic with Backoff
- Current: 3 retries with exponential backoff
- Add: Different prompts on retry (simplify further)
- Add: Alternative style fallback

#### 2.4 Generation Queue
- Don't generate all assets simultaneously
- Sequential generation with delay between requests
- Reduces rate limit risk

**Test Checkpoint:** Successfully generate at least 1 image with Layer.ai

---

### Phase 3: Professional Fallback Assets

**Goal:** When Layer.ai fails, game still looks professional.

#### 3.1 SVG-Based Fallback Assets
Create embedded SVG assets for each game type:

**Match-3 Tiles:**
```javascript
const FALLBACK_TILES = [
  // Red gem with gradient and shine
  `<svg>...</svg>`,
  // Blue gem
  `<svg>...</svg>`,
  // ... 6 total
];
```

**Runner Assets:**
- Player character (simple stick figure or robot)
- Obstacle (spike/barrier)
- Collectible (coin/star)

**Tapper Assets:**
- Main tap target
- Particles/effects

#### 3.2 CSS-Based Fallback Alternative
For maximum compatibility:
```javascript
// Create tile with CSS gradients
function createCSSFallbackTile(type) {
  const gradients = [
    'radial-gradient(circle, #ff6b6b 0%, #c92a2a 100%)',
    'radial-gradient(circle, #4ecdc4 0%, #087f5b 100%)',
    // ...
  ];
  // Return styled div/canvas
}
```

#### 3.3 Template Updates
- Update match3/template.html `createTileSprite()` method
- Use SVG data URIs for fallback tiles
- Add subtle animations (pulse, glow) to improve feel

**Test Checkpoint:** Demo mode produces professional-looking game

---

### Phase 4: Improved User Experience

**Goal:** Users understand what's happening and can recover from errors.

#### 4.1 Progress Feedback
- Show which asset is being generated
- Display "Attempting with simplified prompt..." on retry
- Show "Using fallback assets" message clearly

#### 4.2 Asset Preview
- Show generated assets before building playable
- Allow retry individual failed assets
- Option to use fallback for specific assets

#### 4.3 Error Recovery
- If all assets fail, offer demo mode
- Clear explanation of what went wrong
- Link to Layer.ai dashboard for style debugging

**Test Checkpoint:** User can complete workflow even when some assets fail

---

### Phase 5: Testing Infrastructure

**Goal:** Catch regressions before they reach production.

#### 5.1 API Mock Tests
```python
# tests/test_layer_client_mock.py
@pytest.fixture
def mock_layer_response():
    return {"generateImages": {"id": "test-123", "status": "IN_PROGRESS"}}

def test_generation_handles_error(mock_layer_response, mocker):
    mocker.patch('httpx.AsyncClient.post', return_value=mock_error_response)
    # Assert proper error handling
```

#### 5.2 Integration Test Script
```bash
# scripts/test_layer_integration.sh
# 1. Check workspace credits
# 2. List available styles
# 3. Test generation with simple prompt
# 4. Verify image download
```

#### 5.3 Visual Regression Tests
- Screenshot comparison for demo playables
- Verify fallback assets render correctly
- Test across all game templates

**Test Checkpoint:** CI passes with mocked API tests

---

### Phase 6: Documentation & Best Practices

**Goal:** Make the project maintainable and self-documenting.

#### 6.1 CLAUDE.md Updates
- Project structure overview
- Common issues and solutions
- Testing commands
- Deployment checklist

#### 6.2 Layer.ai API Reference Updates
- Document common error codes
- Add troubleshooting section
- Include working example prompts

#### 6.3 README Updates
- Quick start guide
- Demo mode instructions
- API key setup guide

**Test Checkpoint:** New developer can set up and run project

---

## Detailed Task Breakdown

### Critical Path (Must Complete)

| # | Task | File(s) | Est. Time | Dependencies |
|---|------|---------|-----------|--------------|
| 1 | Fix missing GraphQL query | layer_client.py | 15 min | None |
| 2 | Add style validation | layer_client.py | 30 min | None |
| 3 | Simplify generation prompts | game_asset_generator.py | 30 min | None |
| 4 | Create SVG fallback tiles | match3/template.html | 1 hour | None |
| 5 | Add diagnostic logging | layer_client.py | 30 min | #2 |
| 6 | Test Layer.ai with simple prompts | Manual testing | 30 min | #1, #2, #3 |

### High Priority

| # | Task | File(s) | Est. Time | Dependencies |
|---|------|---------|-----------|--------------|
| 7 | Add debug page to Streamlit | app.py | 1 hour | #5 |
| 8 | Implement retry with prompt simplification | game_asset_generator.py | 45 min | #3 |
| 9 | Update runner template fallbacks | runner/template.html | 45 min | #4 |
| 10 | Update tapper template fallbacks | tapper/template.html | 45 min | #4 |
| 11 | Add mocked API tests | tests/test_layer_mock.py | 1 hour | None |

### Medium Priority

| # | Task | File(s) | Est. Time | Dependencies |
|---|------|---------|-----------|--------------|
| 12 | Asset preview in UI | app.py | 1.5 hours | #6 |
| 13 | Sequential generation queue | game_asset_generator.py | 1 hour | #8 |
| 14 | Enhanced error messages | layer_client.py | 30 min | #5 |
| 15 | Update CLAUDE.md | CLAUDE.md | 30 min | None |
| 16 | Update README | README.md | 30 min | None |

---

## Testing Strategy

### Manual Test Script

After each change, run this test sequence:

```bash
# 1. Run unit tests
pytest tests/ -v

# 2. Test demo mode (no API)
python -c "
from src.playable_factory import PlayableFactory
from src.templates.registry import MechanicType
factory = PlayableFactory()
result = factory.create_demo(MechanicType.MATCH3, 'Test Game')
result.save('test_demo.html')
print(f'Demo created: {result.file_size_bytes} bytes')
"

# 3. Verify HTML is valid
python -c "
with open('test_demo.html') as f:
    html = f.read()
assert 'Phaser.Game' in html
assert 'Match3Scene' in html
print('HTML structure valid')
"

# 4. Test Layer.ai (requires API keys)
python scripts/test_layer_api.py
```

### Automated Test Coverage

| Component | Current | Target |
|-----------|---------|--------|
| layer_client.py | 20% | 80% |
| game_asset_generator.py | 0% | 60% |
| builder.py | 40% | 70% |
| Templates | 30% | 50% |

---

## Recommended Claude Code Plugins

Based on this project's needs:

1. **None required** - Standard Claude Code tools are sufficient
   - File read/write
   - Git operations
   - Bash for testing
   - Web search for API debugging

2. **Helpful for debugging:**
   - Use `WebFetch` to test Layer.ai API endpoints directly
   - Use `Bash` to run Python test scripts

---

## Success Criteria

### Minimum Viable Fix
- [ ] Demo mode produces professional-looking playables
- [ ] Layer.ai errors are clearly communicated to users
- [ ] At least one template works with fallback assets

### Full Resolution
- [ ] Layer.ai asset generation works > 80% of the time
- [ ] All three templates have professional fallback assets
- [ ] Comprehensive test coverage for API client
- [ ] Documentation is complete and accurate

---

## Next Steps

1. **Immediate:** Fix the GraphQL query bug
2. **Today:** Add diagnostic logging and test Layer.ai
3. **This Week:** Implement SVG fallback assets
4. **Ongoing:** Improve test coverage and documentation

---

## Appendix: Layer.ai Error Reference

| Error Message | Likely Cause | Solution |
|---------------|--------------|----------|
| "Oops! Our pixel wizards need a moment..." | Rate limit, style issue, or content filter | Wait, try different style, simplify prompt |
| "At least one style must be provided" | Missing styleId | Always include styleId in request |
| "Cannot query field 'X'" | GraphQL schema mismatch | Update query to match API schema |
| HTTP 401 | Invalid API key | Regenerate API key from dashboard |
| HTTP 403 | Workspace access denied | Check workspace ID and permissions |

---

*This plan will be updated as implementation progresses.*
