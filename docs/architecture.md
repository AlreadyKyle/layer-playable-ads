# Architecture Document
## Layer.ai Playable Studio (LPS)

**Version**: 0.1.0
**Last Updated**: 2025-01-06

---

## 1. High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                              LPS Architecture                                 │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│    ┌─────────────────────────────────────────────────────────────────┐      │
│    │                    Presentation Layer                            │      │
│    │                                                                  │      │
│    │    ┌──────────────────────────────────────────────────────┐     │      │
│    │    │              Streamlit Web UI (app.py)                │     │      │
│    │    │                                                       │     │      │
│    │    │   ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐│     │      │
│    │    │   │ Step 1  │  │ Step 2  │  │ Step 3  │  │ Step 4  ││     │      │
│    │    │   │ Intel   │─▶│ Lock    │─▶│ Forge   │─▶│ Export  ││     │      │
│    │    │   └─────────┘  └─────────┘  └─────────┘  └─────────┘│     │      │
│    │    └──────────────────────────────────────────────────────┘     │      │
│    └─────────────────────────────────────────────────────────────────┘      │
│                                        │                                     │
│    ┌───────────────────────────────────┼─────────────────────────────┐      │
│    │                    Business Logic Layer                          │      │
│    │                                   │                              │      │
│    │    ┌──────────────┐    ┌─────────┴────────┐    ┌──────────────┐│      │
│    │    │    Vision    │    │     Workflow     │    │   Playable   ││      │
│    │    │    Module    │    │     Module       │    │   Module     ││      │
│    │    │              │    │                  │    │              ││      │
│    │    │ competitor_  │    │ style_manager.py │    │ assembler.py ││      │
│    │    │ spy.py       │    │                  │    │              ││      │
│    │    └──────┬───────┘    └────────┬─────────┘    └──────┬───────┘│      │
│    │           │                     │                      │        │      │
│    │           │            ┌────────┴─────────┐           │        │      │
│    │           │            │   Forge Module   │           │        │      │
│    │           │            │ asset_forger.py  │           │        │      │
│    │           │            └────────┬─────────┘           │        │      │
│    └───────────┼─────────────────────┼─────────────────────┼────────┘      │
│                │                     │                     │                │
│    ┌───────────┼─────────────────────┼─────────────────────┼────────┐      │
│    │           │      Integration Layer                    │        │      │
│    │           │                     │                     │        │      │
│    │           │            ┌────────┴─────────┐           │        │      │
│    │           │            │   Layer Client   │           │        │      │
│    │           │            │  layer_client.py │◀──────────┘        │      │
│    │           │            └────────┬─────────┘                    │      │
│    └───────────┼─────────────────────┼──────────────────────────────┘      │
│                │                     │                                      │
│    ┌───────────┼─────────────────────┼──────────────────────────────┐      │
│    │           │       External Services                            │      │
│    │           ▼                     ▼                              │      │
│    │    ┌──────────────┐    ┌───────────────┐                       │      │
│    │    │  Anthropic   │    │   Layer.ai    │                       │      │
│    │    │  Claude API  │    │  GraphQL API  │                       │      │
│    │    └──────────────┘    └───────────────┘                       │      │
│    └────────────────────────────────────────────────────────────────┘      │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Component Architecture

### 2.1 Module Dependency Graph

```
                    ┌─────────────────┐
                    │     app.py      │
                    │   (Streamlit)   │
                    └────────┬────────┘
                             │
           ┌─────────────────┼─────────────────┐
           │                 │                 │
           ▼                 ▼                 ▼
   ┌───────────────┐ ┌──────────────┐ ┌───────────────┐
   │ competitor_   │ │ style_       │ │ assembler.py  │
   │ spy.py        │ │ manager.py   │ │               │
   └───────┬───────┘ └──────┬───────┘ └───────┬───────┘
           │                │                 │
           │                ▼                 │
           │        ┌──────────────┐          │
           │        │ asset_       │          │
           │        │ forger.py    │          │
           │        └──────┬───────┘          │
           │               │                  │
           │               ▼                  │
           │        ┌──────────────┐          │
           └───────▶│ layer_       │◀─────────┘
                    │ client.py    │
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │ helpers  │ │ anthropic│ │  httpx   │
        │ .py      │ │ SDK      │ │          │
        └──────────┘ └──────────┘ └──────────┘
```

### 2.2 Data Flow Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ Screenshots │     │   Style     │     │   Forged    │     │  Playable   │
│   (Input)   │────▶│   Recipe    │────▶│   Assets    │────▶│   (Output)  │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
       │                   │                   │                   │
       ▼                   ▼                   ▼                   ▼
   ┌───────┐          ┌───────┐          ┌───────┐          ┌───────┐
   │ PNG   │          │ JSON  │          │ PNG   │          │ HTML  │
   │ JPG   │          │       │          │ JPG   │          │       │
   │ WebP  │          │ {     │          │ URLs  │          │ <5MB  │
   └───────┘          │  ...  │          └───────┘          └───────┘
                      │ }     │
                      └───────┘
```

---

## 3. Layer Architecture

### 3.1 Presentation Layer

**Technology**: Streamlit
**Responsibility**: User interface and interaction

```
src/app.py
├── Page Configuration
├── Session State Management
├── Sidebar (Status, Navigation)
├── Step 1: Style Intel (Upload, Analysis)
├── Step 2: Style Lock (Review, Edit, Create)
├── Step 3: Variant Forge (Preset Selection, Generation)
└── Step 4: Export (Assembly, Download, Preview)
```

**Key Patterns**:
- Wizard-style navigation via session state
- Form-based input collection
- Progress indicators for async operations
- Download buttons for exports

### 3.2 Business Logic Layer

**Technology**: Python modules
**Responsibility**: Core business operations

| Module | File | Responsibility |
|--------|------|----------------|
| Vision | `vision/competitor_spy.py` | AI-powered visual analysis |
| Workflow | `workflow/style_manager.py` | Style lifecycle management |
| Forge | `forge/asset_forger.py` | Asset generation with presets |
| Playable | `playable/assembler.py` | HTML5 playable assembly |

**Key Patterns**:
- Dataclass models for type safety
- Factory methods for complex object creation
- Session-based state tracking (ForgeSession)
- Template-based output generation

### 3.3 Integration Layer

**Technology**: httpx, anthropic SDK
**Responsibility**: External API communication

```
src/layer_client.py
├── LayerClient (Async)
│   ├── _execute() - GraphQL execution with retry
│   ├── Workspace operations
│   ├── Style operations
│   ├── Forge operations
│   └── Image operations
└── LayerClientSync (Sync wrapper for Streamlit)
```

**Key Patterns**:
- Async context manager (`async with`)
- Automatic retry with exponential backoff
- Sync wrapper for Streamlit compatibility
- Typed return values via dataclasses

### 3.4 Infrastructure Layer

**Technology**: pydantic-settings, structlog
**Responsibility**: Configuration and observability

```
src/utils/helpers.py
├── Settings (pydantic-settings)
│   └── Environment variable binding
├── get_settings() - Cached settings accessor
├── setup_logging() - Structured logging config
└── Utility functions
```

---

## 4. Cross-Cutting Concerns

### 4.1 Configuration Management

```
┌──────────────────────────────────────────┐
│              Configuration               │
├──────────────────────────────────────────┤
│  .env (secrets)                          │
│       │                                  │
│       ▼                                  │
│  Settings (pydantic-settings)            │
│       │                                  │
│       ▼                                  │
│  get_settings() (cached singleton)       │
│       │                                  │
│       ├──▶ LayerClient                   │
│       ├──▶ CompetitorSpy                 │
│       ├──▶ AssetForger                   │
│       └──▶ PlayableAssembler             │
└──────────────────────────────────────────┘
```

### 4.2 Error Handling

```
┌──────────────────────────────────────────┐
│            Error Hierarchy               │
├──────────────────────────────────────────┤
│                                          │
│  Exception                               │
│       │                                  │
│       └── LayerClientError               │
│               │                          │
│               ├── InsufficientCreditsError│
│               └── ForgeTimeoutError      │
│                                          │
│  Handling Strategy:                      │
│  ┌────────────┬────────────────────────┐│
│  │ Layer      │ Strategy               ││
│  ├────────────┼────────────────────────┤│
│  │ Integration│ Retry + raise          ││
│  │ Business   │ Log + transform        ││
│  │ Presentation│ Display to user       ││
│  └────────────┴────────────────────────┘│
└──────────────────────────────────────────┘
```

### 4.3 Logging Architecture

```
┌──────────────────────────────────────────┐
│           Structured Logging             │
├──────────────────────────────────────────┤
│                                          │
│  structlog.get_logger()                  │
│       │                                  │
│       ▼                                  │
│  logger.bind(component="ComponentName")  │
│       │                                  │
│       ▼                                  │
│  logger.info(                            │
│      "Event description",                │
│      key1=value1,                        │
│      key2=value2                         │
│  )                                       │
│       │                                  │
│       ▼                                  │
│  Console output (dev) / JSON (prod)      │
│                                          │
└──────────────────────────────────────────┘
```

---

## 5. State Management

### 5.1 Application State

```
┌──────────────────────────────────────────────────────────────┐
│                    Streamlit Session State                    │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────┐  ┌─────────────────┐                   │
│  │  current_step   │  │ analysis_result │                   │
│  │  (int: 1-4)     │  │ (AnalysisResult)│                   │
│  └─────────────────┘  └─────────────────┘                   │
│                                                              │
│  ┌─────────────────┐  ┌─────────────────┐                   │
│  │  style_recipe   │  │  managed_style  │                   │
│  │  (StyleRecipe)  │  │ (ManagedStyle)  │                   │
│  └─────────────────┘  └─────────────────┘                   │
│                                                              │
│  ┌─────────────────┐  ┌─────────────────┐                   │
│  │  forge_session  │  │  forged_assets  │                   │
│  │ (ForgeSession)  │  │ (list[Forged])  │                   │
│  └─────────────────┘  └─────────────────┘                   │
│                                                              │
│  ┌─────────────────┐  ┌─────────────────┐                   │
│  │  playable_html  │  │playable_metadata│                   │
│  │  (str)          │  │(PlayableMetadata)│                   │
│  └─────────────────┘  └─────────────────┘                   │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### 5.2 State Transitions

```
┌─────────┐    analyze    ┌─────────┐    create    ┌─────────┐
│ Step 1  │──────────────▶│ Step 2  │─────────────▶│ Step 3  │
│ (Intel) │               │ (Lock)  │              │ (Forge) │
└─────────┘               └─────────┘              └─────────┘
     │                         │                        │
     │                         │                        │
     ▼                         ▼                        ▼
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│analysis_    │         │managed_     │         │forge_       │
│result       │         │style        │         │session      │
│style_recipe │         │             │         │forged_assets│
└─────────────┘         └─────────────┘         └─────────────┘
                                                       │
                                                       │ assemble
                                                       ▼
                                                ┌─────────┐
                                                │ Step 4  │
                                                │(Export) │
                                                └─────────┘
                                                       │
                                                       ▼
                                                ┌─────────────┐
                                                │playable_    │
                                                │html         │
                                                │playable_    │
                                                │metadata     │
                                                └─────────────┘
```

---

## 6. Integration Architecture

### 6.1 Layer.ai GraphQL Integration

```
┌──────────────────────────────────────────────────────────────┐
│                  Layer.ai Integration                         │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                    LayerClient                       │    │
│  │                                                      │    │
│  │  ┌──────────────┐    ┌──────────────┐               │    │
│  │  │   Queries    │    │  Mutations   │               │    │
│  │  │              │    │              │               │    │
│  │  │• getCredits  │    │• createStyle │               │    │
│  │  │• getStyle    │    │• updateStyle │               │    │
│  │  │• listStyles  │    │• startForge  │               │    │
│  │  │• getForge    │    │• uploadImage │               │    │
│  │  │  TaskStatus  │    │              │               │    │
│  │  │• getImage    │    │              │               │    │
│  │  └──────────────┘    └──────────────┘               │    │
│  │                                                      │    │
│  │  ┌──────────────────────────────────────────────┐   │    │
│  │  │                 _execute()                    │   │    │
│  │  │                                               │   │    │
│  │  │  httpx.AsyncClient                           │   │    │
│  │  │       │                                       │   │    │
│  │  │       ▼                                       │   │    │
│  │  │  POST /graphql                               │   │    │
│  │  │       │                                       │   │    │
│  │  │       ▼                                       │   │    │
│  │  │  Retry (3x, exponential backoff)             │   │    │
│  │  │       │                                       │   │    │
│  │  │       ▼                                       │   │    │
│  │  │  Parse response / raise errors               │   │    │
│  │  └──────────────────────────────────────────────┘   │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### 6.2 Anthropic Claude Integration

```
┌──────────────────────────────────────────────────────────────┐
│                  Claude Vision Integration                    │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                 CompetitorSpy                        │    │
│  │                                                      │    │
│  │  Input Processing:                                   │    │
│  │  ┌────────────┐                                     │    │
│  │  │ Screenshot │──▶ Base64 encode ──▶ Message       │    │
│  │  │ (file/url) │                      content        │    │
│  │  └────────────┘                                     │    │
│  │                                                      │    │
│  │  API Call:                                          │    │
│  │  ┌────────────────────────────────────────────┐    │    │
│  │  │ anthropic.messages.create(                  │    │    │
│  │  │     model="claude-sonnet-4-20250514",       │    │    │
│  │  │     messages=[{                             │    │    │
│  │  │         "role": "user",                     │    │    │
│  │  │         "content": [image, prompt]          │    │    │
│  │  │     }]                                      │    │    │
│  │  │ )                                           │    │    │
│  │  └────────────────────────────────────────────┘    │    │
│  │                                                      │    │
│  │  Output Parsing:                                     │    │
│  │  ┌────────────┐                                     │    │
│  │  │ Response   │──▶ Extract JSON ──▶ StyleRecipe    │    │
│  │  │ text       │    from markdown                    │    │
│  │  └────────────┘                                     │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 7. Playable Output Architecture

### 7.1 HTML Structure

```
index.html
│
├── <head>
│   ├── Meta tags (viewport, mobile-web-app)
│   └── Embedded CSS (responsive, dark theme)
│
├── <body>
│   ├── <div id="game-container">
│   │
│   ├── <script> Phaser CDN
│   │
│   ├── <script> MRAID Handler
│   │   ├── mraid detection
│   │   ├── openStoreUrl()
│   │   └── timing constants
│   │
│   └── <script> Game Logic
│       ├── BootScene (asset loading)
│       ├── HookScene (3 seconds)
│       ├── GameplayScene (15 seconds)
│       └── CTAScene (5 seconds)
│
└── Base64 embedded assets (via data URIs)
```

### 7.2 Scene Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    Playable Scene Flow                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐ │
│  │  Boot   │───▶│  Hook   │───▶│Gameplay │───▶│   CTA   │ │
│  │  Scene  │    │  Scene  │    │  Scene  │    │  Scene  │ │
│  └─────────┘    └─────────┘    └─────────┘    └─────────┘ │
│       │              │              │              │       │
│       │              │              │              │       │
│       ▼              ▼              ▼              ▼       │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐ │
│  │ Load    │    │ Bounce  │    │ Collect │    │ Pulse   │ │
│  │ assets  │    │ anim    │    │ items   │    │ button  │ │
│  │         │    │ 3 sec   │    │ 15 sec  │    │ 5 sec   │ │
│  └─────────┘    └─────────┘    └─────────┘    └─────────┘ │
│                      │              │              │       │
│                      │              │              │       │
│                      └──────────────┴──────────────┘       │
│                                  │                         │
│                                  ▼                         │
│                           ┌───────────┐                    │
│                           │  mraid.   │                    │
│                           │  open()   │                    │
│                           │ (any tap) │                    │
│                           └───────────┘                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 8. Security Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    Security Boundaries                        │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                   Application                        │    │
│  │                                                      │    │
│  │  Secrets:                                           │    │
│  │  ┌────────────────────────────────────────────┐    │    │
│  │  │ .env (git-ignored)                          │    │    │
│  │  │   LAYER_API_KEY=***                         │    │    │
│  │  │   ANTHROPIC_API_KEY=***                     │    │    │
│  │  │   LAYER_WORKSPACE_ID=***                    │    │    │
│  │  └────────────────────────────────────────────┘    │    │
│  │                                                      │    │
│  │  Input Validation:                                   │    │
│  │  ┌────────────────────────────────────────────┐    │    │
│  │  │ • File type checking (png, jpg, webp)       │    │    │
│  │  │ • URL format validation                     │    │    │
│  │  │ • Size limits on uploads                    │    │    │
│  │  └────────────────────────────────────────────┘    │    │
│  │                                                      │    │
│  │  Output Sanitization:                               │    │
│  │  ┌────────────────────────────────────────────┐    │    │
│  │  │ • Template variable escaping                │    │    │
│  │  │ • Base64 encoding for assets                │    │    │
│  │  │ • No direct user input in HTML              │    │    │
│  │  └────────────────────────────────────────────┘    │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  External Communication:                                     │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                                                      │    │
│  │  ┌─────────┐         HTTPS          ┌─────────┐    │    │
│  │  │   LPS   │◀───────────────────────▶│Layer.ai │    │    │
│  │  │         │    Bearer Token Auth    │   API   │    │    │
│  │  └─────────┘                         └─────────┘    │    │
│  │                                                      │    │
│  │  ┌─────────┐         HTTPS          ┌─────────┐    │    │
│  │  │   LPS   │◀───────────────────────▶│Claude   │    │    │
│  │  │         │    API Key Header       │   API   │    │    │
│  │  └─────────┘                         └─────────┘    │    │
│  │                                                      │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 9. Decision Log

| Decision | Rationale | Alternatives Considered |
|----------|-----------|------------------------|
| Streamlit for UI | Rapid prototyping, Python-native, suitable for demo | FastAPI+React, Gradio |
| httpx over requests | Async support, modern API | aiohttp, requests |
| Phaser.js | Industry standard, MRAID compatible | PixiJS, vanilla Canvas |
| pydantic-settings | Type-safe config, env file support | python-dotenv alone |
| structlog | Structured logging, context binding | logging, loguru |
| Base64 embedding | Single-file export requirement | External asset URLs |
| Sync wrapper | Streamlit compatibility | Full async rewrite |

---

## 10. Future Architecture Considerations

### 10.1 Scaling Path

```
Current (MVP)              Future (Production)
─────────────              ───────────────────

Single-user        ──▶     Multi-tenant
Streamlit                  FastAPI + React

Session state      ──▶     Redis/PostgreSQL
In-memory                  Persistent store

Sync wrapper       ──▶     Full async
Blocking calls             Non-blocking

Local files        ──▶     Object storage
Temp directory             S3/GCS

No auth            ──▶     OAuth 2.0
Demo mode                  Enterprise SSO
```

### 10.2 Plugin Architecture (Future)

```
┌──────────────────────────────────────────┐
│            Plugin System (Future)         │
├──────────────────────────────────────────┤
│                                          │
│  Core ────────────────────────────────┐  │
│  │                                    │  │
│  │  ┌──────────────────────────────┐ │  │
│  │  │     Plugin Interface         │ │  │
│  │  └──────────────────────────────┘ │  │
│  │              │                    │  │
│  │    ┌─────────┴─────────┐         │  │
│  │    ▼                   ▼         │  │
│  │ ┌───────┐         ┌───────┐      │  │
│  │ │Vision │         │Export │      │  │
│  │ │Plugin │         │Plugin │      │  │
│  │ └───────┘         └───────┘      │  │
│  │    │                   │         │  │
│  │    ├── Claude          ├── MRAID │  │
│  │    ├── GPT-4V          ├── VAST  │  │
│  │    └── Gemini          └── HTML5 │  │
│  └────────────────────────────────────  │
│                                          │
└──────────────────────────────────────────┘
```
