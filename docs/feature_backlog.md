# Feature Backlog

## Layer.ai Playable Studio (LPS)

This document tracks features, enhancements, and technical debt for the LPS project.

---

## Prioritization Key

| Priority | Description |
|----------|-------------|
| P0 | Critical for MVP |
| P1 | Important, nice-to-have for demo |
| P2 | Future enhancement |
| P3 | Exploratory / research |

---

## MVP Features (P0)

### Core Pipeline

| ID | Feature | Status | Module | Notes |
|----|---------|--------|--------|-------|
| MVP-001 | Screenshot upload | ✅ Done | Vision | Multiple file support |
| MVP-002 | Claude Vision analysis | ✅ Done | Vision | Style extraction |
| MVP-003 | Style Recipe schema | ✅ Done | Vision | JSON output |
| MVP-004 | Layer.ai style creation | ✅ Done | Workflow | GraphQL mutation |
| MVP-005 | Credit checking | ✅ Done | Forge | Guard before forge |
| MVP-006 | Asset forging | ✅ Done | Forge | With polling |
| MVP-007 | Reference image consistency | ✅ Done | Forge | First asset sets ref |
| MVP-008 | Playable assembly | ✅ Done | Playable | Phaser.js template |
| MVP-009 | HTML export | ✅ Done | Playable | Single file < 5MB |
| MVP-010 | 4-step wizard UI | ✅ Done | UI | Streamlit |

### Validation

| ID | Feature | Status | Module | Notes |
|----|---------|--------|--------|-------|
| MVP-011 | Size validation | ✅ Done | Playable | < 5MB check |
| MVP-012 | MRAID detection | ✅ Done | Playable | In template |
| MVP-013 | Timing constants | ✅ Done | Playable | 3-15-5 model |
| MVP-014 | Image compression | ✅ Done | Playable | Pillow processing |

---

## Demo Enhancements (P1)

| ID | Feature | Status | Module | Notes |
|----|---------|--------|--------|-------|
| P1-001 | Loading spinners | ✅ Done | UI | For async ops |
| P1-002 | Progress indicators | ✅ Done | UI | Forge progress |
| P1-003 | Error messages | ⬜ Todo | All | User-friendly text |
| P1-004 | Dashboard deep links | ✅ Done | Workflow | Style editing |
| P1-005 | Preview iframe | ✅ Done | UI | In-browser preview |
| P1-006 | Credit display | ✅ Done | UI | Sidebar metric |
| P1-007 | Sample screenshots | ⬜ Todo | - | Demo assets |
| P1-008 | Quick demo mode | ⬜ Todo | UI | Pre-filled values |

---

## Future Features (P2)

### Multi-Asset Support

| ID | Feature | Priority | Module | Description |
|----|---------|----------|--------|-------------|
| P2-001 | Batch playable generation | P2 | Forge | Multiple playables at once |
| P2-002 | Variant management | P2 | Workflow | Track style variants |
| P2-003 | Asset library | P2 | Forge | Reuse forged assets |
| P2-004 | Template library | P2 | Playable | Saved configurations |

### Export Options

| ID | Feature | Priority | Module | Description |
|----|---------|----------|--------|-------------|
| P2-005 | MRAID 2.0 export | P2 | Playable | Legacy support |
| P2-006 | VAST export | P2 | Playable | Video ad spec |
| P2-007 | ZIP bundle export | P2 | Playable | With assets separate |
| P2-008 | CDN asset hosting | P2 | Playable | External assets option |

### Intelligence

| ID | Feature | Priority | Module | Description |
|----|---------|----------|--------|-------------|
| P2-009 | App Store URL fetch | P2 | Vision | Auto-fetch screenshots |
| P2-010 | Style comparison | P2 | Vision | Compare multiple games |
| P2-011 | Genre detection | P2 | Vision | Auto-categorization |
| P2-012 | Trend analysis | P2 | Vision | Popular style trends |

### Integration

| ID | Feature | Priority | Module | Description |
|----|---------|----------|--------|-------------|
| P2-013 | Analytics integration | P2 | Playable | Event tracking |
| P2-014 | A/B test framework | P2 | All | Variant testing |
| P2-015 | Webhook notifications | P2 | Core | Forge completion alerts |
| P2-016 | CI/CD pipeline | P2 | DevOps | Automated testing |

---

## Exploratory (P3)

| ID | Feature | Priority | Module | Description |
|----|---------|----------|--------|-------------|
| P3-001 | Multi-workspace | P3 | Core | Enterprise support |
| P3-002 | Team collaboration | P3 | Core | Shared styles |
| P3-003 | Custom game templates | P3 | Playable | Beyond simple collect |
| P3-004 | Sound effects | P3 | Playable | Audio integration |
| P3-005 | Physics gameplay | P3 | Playable | Advanced mechanics |
| P3-006 | GPT-4V support | P3 | Vision | Alternative vision |
| P3-007 | Gemini support | P3 | Vision | Alternative vision |
| P3-008 | Local LLM option | P3 | Vision | Privacy-first |

---

## Technical Debt

| ID | Issue | Priority | Module | Description |
|----|-------|----------|--------|-------------|
| TD-001 | Test coverage | P1 | All | Add unit tests |
| TD-002 | Type stubs | P2 | All | Complete type hints |
| TD-003 | Error handling | P1 | All | Consistent patterns |
| TD-004 | Logging audit | P2 | All | Ensure all paths logged |
| TD-005 | Config validation | P2 | Utils | Startup checks |
| TD-006 | API versioning | P3 | Client | GraphQL schema version |
| TD-007 | Retry refinement | P2 | Client | Better backoff strategy |
| TD-008 | Memory optimization | P3 | Playable | Large asset handling |

---

## Bug Tracking

| ID | Bug | Priority | Module | Status |
|----|-----|----------|--------|--------|
| - | No bugs reported yet | - | - | - |

---

## Completed Features

### v0.1.0

- [x] Project scaffolding
- [x] Layer.ai GraphQL client
- [x] Vision analysis module
- [x] Style management
- [x] Asset forging with presets
- [x] Playable assembly
- [x] Streamlit UI
- [x] Documentation suite

---

## Feature Request Template

When adding new features:

```markdown
### Feature: [Name]

**ID**: P[X]-[XXX]
**Priority**: P0/P1/P2/P3
**Module**: [Module name]

**Description**:
[Brief description of the feature]

**User Story**:
As a [user type], I want [goal] so that [benefit].

**Acceptance Criteria**:
- [ ] Criteria 1
- [ ] Criteria 2
- [ ] Criteria 3

**Technical Notes**:
[Any implementation considerations]

**Dependencies**:
[List any dependent features or external requirements]
```

---

## Voting / Prioritization

For team prioritization sessions:

| Feature | Votes | Final Priority |
|---------|-------|----------------|
| TBD | TBD | TBD |
