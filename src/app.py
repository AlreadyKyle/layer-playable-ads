"""
Layer.ai Playable Studio v2.0 - Game-Specific Playable Ad Generator

New Workflow:
1. Input Game - Upload screenshots or enter App Store URL
2. Analyze & Review - Claude Vision extracts mechanics and style
3. Generate Assets - Layer.ai creates game-specific art
4. Export Playable - Build and download MRAID-compliant HTML5 playable
"""

import sys
from pathlib import Path

# Ensure project root is on sys.path so `from src.xxx` imports work
# regardless of how the app is launched (streamlit run, start.sh, IDE, etc.)
_project_root = str(Path(__file__).resolve().parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import base64
import tempfile
from typing import Optional

import streamlit as st

from src.analysis.game_analyzer import GameAnalyzerSync, GameAnalysis
from src.generation.game_asset_generator import GameAssetGenerator, GeneratedAssetSet
from src.assembly.builder import PlayableBuilder, PlayableConfig, PlayableResult
from src.layer_client import LayerClientSync, LayerAPIError, extract_error_message
from src.templates.registry import MechanicType, TEMPLATE_REGISTRY, list_available_mechanics
from src.utils.helpers import validate_api_keys, get_settings
from src.ui_components import (
    glass_card, step_header, metric_card, confidence_badge, color_palette,
    asset_preview_card, network_badges, success_banner, empty_state,
    sidebar_progress, api_status_row, credits_display, phone_preview,
    gradient_divider, styled_pill, onboarding_card,
)


# =============================================================================
# Cached Functions
# =============================================================================

@st.cache_data(ttl=300, show_spinner="Connecting to Layer.ai...")
def fetch_workspace_info() -> Optional[dict]:
    """Fetch workspace info with caching."""
    try:
        settings = get_settings()
        client = LayerClientSync(timeout=float(settings.api_fetch_timeout))
        info = client.get_workspace_info()
        return {
            "workspace_id": info.workspace_id,
            "credits_available": info.credits_available,
            "has_access": info.has_access,
        }
    except Exception as e:
        return {"error": extract_error_message(e)}


@st.cache_data(ttl=60, show_spinner="Loading styles...")
def fetch_styles(limit: int = 50) -> dict:
    """Fetch Layer.ai styles with caching."""
    try:
        settings = get_settings()
        client = LayerClientSync(timeout=float(settings.api_fetch_timeout))
        styles = client.list_styles(limit=limit)
        return {"styles": styles, "error": None}
    except Exception as e:
        return {"styles": [], "error": extract_error_message(e)}


# =============================================================================
# Page Config
# =============================================================================

st.set_page_config(
    page_title="Playable Ad Generator",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    /* ── Design Tokens ── */
    :root {
        --bg-primary: #0e1117;
        --bg-secondary: #161b22;
        --accent: #FF4B4B;
        --accent-secondary: #6366f1;
        --color-success: #48bb78;
        --color-warning: #ecc94b;
        --color-error: #f56565;
        --text-primary: #f0f0f0;
        --text-secondary: #a0aec0;
        --text-muted: #636e7b;
        --glass-bg: rgba(255,255,255,0.03);
        --glass-border: rgba(255,255,255,0.07);
        --radius-sm: 6px;
        --radius-md: 10px;
        --radius-lg: 14px;
        --blur: 16px;
        --shadow-lg: 0 8px 32px rgba(0,0,0,0.25);
        --transition: 0.25s ease;
    }

    /* ── Google Font ── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    /* ── Global ── */
    .stApp {
        background-color: var(--bg-primary);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }
    header[data-testid="stHeader"] { background: transparent !important; }
    footer { display: none !important; }
    .stApp > header { backdrop-filter: blur(12px); }

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #12151c 0%, #0d1017 100%) !important;
        border-right: 1px solid var(--glass-border) !important;
    }
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stMarkdown span {
        font-family: 'Inter', sans-serif;
    }

    /* ── Keyframes ── */
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(12px); }
        to { opacity: 1; transform: translateY(0); }
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    @keyframes shimmer {
        0% { background-position: -200% 0; }
        100% { background-position: 200% 0; }
    }

    .animate-fade-in {
        animation: fadeInUp 0.4s ease both;
    }

    /* ── Glass Card Hover ── */
    .glass-card:hover {
        border-color: rgba(255,255,255,0.12) !important;
    }

    /* ── Streamlit Button Override ── */
    .stButton > button {
        transition: all var(--transition);
        border-radius: var(--radius-md) !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important;
    }
    .stButton > button:hover {
        box-shadow: 0 0 20px rgba(255,75,75,0.2);
        transform: translateY(-1px);
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, var(--accent), #e03e3e) !important;
        border: none !important;
    }

    /* ── Divider Override ── */
    hr {
        border-color: var(--glass-border) !important;
        opacity: 0.5;
    }

    /* ── Gradient Title ── */
    .gradient-title {
        background: linear-gradient(135deg, var(--accent), var(--accent-secondary));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 800;
        font-size: 2rem;
        line-height: 1.2;
    }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# Session State
# =============================================================================

def init_session_state():
    """Initialize session state."""
    defaults = {
        "current_step": 1,
        "screenshots": [],  # Uploaded screenshot bytes
        "game_analysis": None,  # GameAnalysis result
        "selected_mechanic": None,  # User-confirmed mechanic type
        "layer_style_id": None,  # Selected Layer.ai style
        "generated_assets": None,  # GeneratedAssetSet
        "playable_result": None,  # PlayableResult
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# =============================================================================
# Sidebar
# =============================================================================

def render_sidebar():
    """Render sidebar with status and progress."""
    # Brand mark
    st.sidebar.markdown("""
    <div style="padding:8px 0 4px 0;">
        <span style="
            font-size:1.6rem;font-weight:800;
            background:linear-gradient(135deg, #FF4B4B, #6366f1);
            -webkit-background-clip:text;-webkit-text-fill-color:transparent;
            background-clip:text;
        ">LPS</span>
        <div style="font-size:0.7rem;text-transform:uppercase;letter-spacing:0.1em;
                     color:#636e7b;margin-top:2px;">Playable Studio</div>
    </div>
    """, unsafe_allow_html=True)

    # API Status
    st.sidebar.markdown(gradient_divider(), unsafe_allow_html=True)
    st.sidebar.markdown('<div style="font-size:0.72rem;text-transform:uppercase;letter-spacing:0.08em;color:#636e7b;margin-bottom:8px;">API Status</div>', unsafe_allow_html=True)

    key_status = validate_api_keys()
    all_keys_set = all(key_status.values())

    key_labels = {
        "layer_api_key": "Layer.ai API",
        "layer_workspace_id": "Workspace ID",
        "anthropic_api_key": "Anthropic API",
    }
    for key, is_set in key_status.items():
        name = key_labels.get(key, key.replace("_", " ").title())
        st.sidebar.markdown(api_status_row(name, is_set), unsafe_allow_html=True)

    if all_keys_set:
        info = fetch_workspace_info()
        if info and "error" not in info:
            if info.get("has_access") is False:
                st.sidebar.warning("Could not verify credits")
            else:
                st.sidebar.markdown(credits_display(info.get("credits_available", "?")), unsafe_allow_html=True)

    # Workflow Progress
    st.sidebar.markdown(gradient_divider(), unsafe_allow_html=True)
    st.sidebar.markdown('<div style="font-size:0.72rem;text-transform:uppercase;letter-spacing:0.08em;color:#636e7b;margin-bottom:8px;">Workflow</div>', unsafe_allow_html=True)
    st.sidebar.markdown(sidebar_progress(st.session_state.current_step), unsafe_allow_html=True)

    # Supported Games
    st.sidebar.markdown(gradient_divider(), unsafe_allow_html=True)
    st.sidebar.markdown('<div style="font-size:0.72rem;text-transform:uppercase;letter-spacing:0.08em;color:#636e7b;margin-bottom:8px;">Supported Games</div>', unsafe_allow_html=True)

    pills_html = ""
    for mechanic in list_available_mechanics():
        template = TEMPLATE_REGISTRY[mechanic]
        pills_html += styled_pill(template.name)
    st.sidebar.markdown(f'<div style="display:flex;flex-wrap:wrap;gap:4px;">{pills_html}</div>', unsafe_allow_html=True)

    # Demo Mode
    st.sidebar.markdown(gradient_divider(), unsafe_allow_html=True)
    st.sidebar.markdown(glass_card(
        title="Quick Demo",
        icon="&#9889;",
        content='<div style="font-size:0.78rem;color:var(--text-muted);margin-bottom:8px;">No API keys needed</div>',
    ), unsafe_allow_html=True)

    demo_type = st.sidebar.selectbox(
        "Game Type",
        options=["match3", "runner", "tapper"],
        format_func=lambda x: {"match3": "Match-3", "runner": "Runner", "tapper": "Tapper"}[x],
        key="demo_type_select",
    )

    if st.sidebar.button("Generate Demo", type="primary", key="demo_btn"):
        from src.playable_factory import PlayableFactory
        factory = PlayableFactory()
        demo_result = factory.create_demo(
            mechanic_type=MechanicType(demo_type),
            game_name=f"Demo {demo_type.title()}"
        )
        st.session_state.playable_result = demo_result
        st.session_state.current_step = 4
        st.rerun()


# =============================================================================
# Step 1: Input Game
# =============================================================================

def render_step_1():
    """Step 1: Input game screenshots."""
    st.markdown(step_header(1, "Input Your Game"), unsafe_allow_html=True)

    # Upload hint card
    st.markdown(glass_card(
        icon="&#128247;",
        title="Upload Screenshots",
        content="""
        <div style="font-size:0.88rem;color:var(--text-secondary);line-height:1.6;">
            Upload 1-5 screenshots from the game you want to create a playable ad for.<br>
            <span style="color:var(--text-muted);font-size:0.8rem;">Supported: PNG, JPG &middot; Shows core gameplay</span>
        </div>
        """,
    ), unsafe_allow_html=True)

    # Screenshot upload
    uploaded_files = st.file_uploader(
        "Upload Game Screenshots",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True,
        help="Upload 1-5 screenshots showing the core gameplay",
    )

    if uploaded_files:
        # Display previews
        cols = st.columns(min(len(uploaded_files), 5))
        for i, file in enumerate(uploaded_files[:5]):
            with cols[i]:
                st.image(file, caption=f"Screenshot {i+1}", width=150)

        # Optional game name hint
        game_name = st.text_input(
            "Game Name (optional)",
            placeholder="e.g., Candy Crush, Subway Surfers",
            help="Helps improve analysis accuracy",
        )

        st.session_state.screenshots = [f.read() for f in uploaded_files[:5]]
        # Reset file position
        for f in uploaded_files:
            f.seek(0)

        if st.button("Analyze Game", type="primary"):
            with st.spinner("Analyzing game with Claude Vision..."):
                try:
                    analyzer = GameAnalyzerSync()
                    analysis = analyzer.analyze_screenshots(
                        st.session_state.screenshots,
                        game_name_hint=game_name if game_name else None,
                    )
                    st.session_state.game_analysis = analysis
                    st.session_state.current_step = 2
                    st.rerun()
                except Exception as e:
                    st.error(f"Analysis failed: {str(e)}")
    else:
        st.markdown(empty_state(
            title="Upload Game Screenshots",
            message="Add 1-5 screenshots showing core gameplay to get started. The AI will analyze mechanics, style, and colors.",
            icon="&#127918;",
        ), unsafe_allow_html=True)


# =============================================================================
# Step 2: Analyze & Review
# =============================================================================

def render_step_2():
    """Step 2: Review and confirm analysis."""
    st.markdown(step_header(2, "Review Analysis"), unsafe_allow_html=True)

    analysis: GameAnalysis = st.session_state.game_analysis

    if not analysis:
        st.warning("No analysis available. Please go back and upload screenshots.")
        if st.button("Back"):
            st.session_state.current_step = 1
            st.rerun()
        return

    # Game info
    col1, col2 = st.columns([2, 1])

    with col1:
        # Game Identity glass card
        publisher_html = f'<div style="font-size:0.8rem;color:var(--text-muted);margin-top:2px;">by {analysis.publisher}</div>' if analysis.publisher else ""
        badge_html = confidence_badge(
            analysis.mechanic_type.value.upper(),
            analysis.mechanic_confidence,
            analysis.confidence_level.value,
        )
        reasoning_html = f'<div style="font-size:0.88rem;color:var(--text-secondary);margin-top:10px;"><strong>Why:</strong> {analysis.mechanic_reasoning}</div>'

        st.markdown(glass_card(
            title="Game Identity",
            icon="&#127918;",
            content=f"""
            <div style="font-size:1.2rem;font-weight:700;color:var(--text-primary);">{analysis.game_name}</div>
            {publisher_html}
            <div style="margin-top:12px;">{badge_html}</div>
            {reasoning_html}
            """,
        ), unsafe_allow_html=True)

        # Core loop
        st.markdown(glass_card(
            title="Core Game Loop",
            icon="&#128260;",
            content=f'<div style="font-size:0.9rem;color:var(--text-secondary);line-height:1.6;">{analysis.core_loop_description}</div>',
        ), unsafe_allow_html=True)

    with col2:
        # Visual Style glass card
        palette_html = color_palette(analysis.visual_style.color_palette[:6])
        st.markdown(glass_card(
            title="Visual Style",
            icon="&#127912;",
            content=f"""
            <div style="font-size:0.88rem;color:var(--text-secondary);line-height:1.8;">
                <strong>Art:</strong> {analysis.visual_style.art_type}<br>
                <strong>Theme:</strong> {analysis.visual_style.theme}<br>
                <strong>Mood:</strong> {analysis.visual_style.mood}
            </div>
            <div style="margin-top:12px;">
                <div style="font-size:0.78rem;font-weight:600;color:var(--text-muted);margin-bottom:6px;">COLOR PALETTE</div>
                {palette_html}
            </div>
            """,
        ), unsafe_allow_html=True)

    # Allow override of mechanic type
    st.markdown(gradient_divider(), unsafe_allow_html=True)

    mechanic_options = [m.value for m in list_available_mechanics()]
    current_index = mechanic_options.index(analysis.mechanic_type.value) if analysis.mechanic_type.value in mechanic_options else 0

    selected = st.selectbox(
        "Confirm Game Type",
        options=mechanic_options,
        index=current_index,
        format_func=lambda x: TEMPLATE_REGISTRY[MechanicType(x)].name,
    )

    st.session_state.selected_mechanic = MechanicType(selected)

    # Show template info in glass card with accent
    template = TEMPLATE_REGISTRY[st.session_state.selected_mechanic]
    with st.expander("Template Details"):
        examples = ", ".join(template.example_games)
        assets_html = ""
        for asset in template.required_assets:
            assets_html += f'<div style="font-size:0.85rem;color:var(--text-secondary);padding:3px 0;">&bull; <strong>{asset.key}</strong>: {asset.description}</div>'

        st.markdown(glass_card(
            content=f"""
            <div style="font-size:0.9rem;color:var(--text-secondary);line-height:1.6;">
                <strong>Template:</strong> {template.name}<br>
                <strong>Description:</strong> {template.description}<br>
                <strong>Example Games:</strong> {examples}
            </div>
            <div style="margin-top:12px;">
                <div style="font-size:0.78rem;font-weight:600;color:var(--text-muted);margin-bottom:6px;">REQUIRED ASSETS</div>
                {assets_html}
            </div>
            """,
            accent="var(--accent-secondary)",
        ), unsafe_allow_html=True)

    # Assets needed
    st.markdown(gradient_divider(), unsafe_allow_html=True)

    if analysis.assets_needed:
        assets_content = ""
        for asset in analysis.assets_needed:
            assets_content += f"""
            <div style="
                display:flex;align-items:center;gap:10px;
                padding:8px 12px;margin:4px 0;
                background:rgba(255,255,255,0.02);
                border-radius:var(--radius-sm);
                border-left:2px solid var(--accent);
            ">
                <span style="font-size:0.85rem;color:var(--text-primary);font-weight:600;">{asset.key}</span>
                <span style="font-size:0.8rem;color:var(--text-muted);">{asset.description}</span>
            </div>"""
        st.markdown(glass_card(
            title="Assets to Generate",
            icon="&#128444;",
            content=assets_content,
        ), unsafe_allow_html=True)
    else:
        st.markdown(glass_card(
            title="Assets to Generate",
            icon="&#128444;",
            content='<div style="font-size:0.85rem;color:var(--text-muted);">Using default asset prompts for this template</div>',
            accent="var(--accent-secondary)",
        ), unsafe_allow_html=True)

    # Navigation
    st.markdown(gradient_divider(), unsafe_allow_html=True)
    col1, col2 = st.columns([1, 2])

    with col1:
        if st.button("Back to Screenshots"):
            st.session_state.current_step = 1
            st.rerun()

    with col2:
        if st.button("Continue to Asset Generation", type="primary"):
            st.session_state.current_step = 3
            st.rerun()


# =============================================================================
# Step 3: Generate Assets
# =============================================================================

def render_step_3():
    """Step 3: Generate assets with Layer.ai."""
    st.markdown(step_header(3, "Generate Assets"), unsafe_allow_html=True)

    analysis: GameAnalysis = st.session_state.game_analysis
    mechanic_type = st.session_state.selected_mechanic or analysis.mechanic_type

    # Style selection in glass card
    st.markdown(glass_card(
        title="Layer.ai Style",
        icon="&#127912;",
        content='<div style="font-size:0.82rem;color:var(--text-muted);margin-bottom:4px;">Choose a trained style from your workspace to generate assets.</div>',
    ), unsafe_allow_html=True)

    styles_data = fetch_styles(limit=50)
    available_styles = styles_data.get("styles", [])
    fetch_error = styles_data.get("error")

    if fetch_error:
        st.error(f"Could not fetch styles: {fetch_error}")
        manual_id = st.text_input("Enter Style ID manually")
        if manual_id:
            st.session_state.layer_style_id = manual_id
    elif not available_styles:
        st.warning("No trained styles found. Please create one at app.layer.ai")
        manual_id = st.text_input("Enter Style ID manually")
        if manual_id:
            st.session_state.layer_style_id = manual_id
    else:
        complete_styles = [s for s in available_styles if s.get("status") == "COMPLETE"]

        if complete_styles:
            style_options = {s["name"]: s["id"] for s in complete_styles}
            selected_name = st.selectbox(
                "Available Styles",
                options=list(style_options.keys()),
            )
            st.session_state.layer_style_id = style_options[selected_name]
        else:
            st.warning("No completed styles found")

    # Show what will be generated as styled cards
    st.markdown(gradient_divider(), unsafe_allow_html=True)

    template = TEMPLATE_REGISTRY[mechanic_type]
    required_assets = [a for a in template.required_assets if a.required]

    assets_content = ""
    for asset in required_assets:
        assets_content += f"""
        <div style="
            display:flex;align-items:center;gap:10px;
            padding:10px 14px;margin:4px 0;
            background:rgba(255,255,255,0.02);
            border-radius:var(--radius-sm);
            border-left:2px solid var(--accent);
        ">
            <span style="font-size:0.85rem;color:var(--text-primary);font-weight:600;">{asset.key}</span>
            <span style="font-size:0.8rem;color:var(--text-muted);">{asset.description}</span>
        </div>"""

    st.markdown(glass_card(
        title=f"Assets to Generate ({len(required_assets)})",
        icon="&#128444;",
        content=assets_content,
    ), unsafe_allow_html=True)

    # Navigation
    st.markdown(gradient_divider(), unsafe_allow_html=True)
    col1, col2 = st.columns([1, 2])

    with col1:
        if st.button("Back to Analysis"):
            st.session_state.current_step = 2
            st.rerun()

    with col2:
        can_generate = st.session_state.layer_style_id is not None

        if st.button("Generate Assets", type="primary", disabled=not can_generate):
            with st.spinner("Generating assets with Layer.ai..."):
                try:
                    generator = GameAssetGenerator()

                    # Progress display
                    progress = st.progress(0)
                    status = st.empty()

                    def progress_callback(current, total, name):
                        progress.progress(current / total)
                        status.text(f"Generating {name}...")

                    asset_set = generator.generate_for_game(
                        analysis=analysis,
                        style_id=st.session_state.layer_style_id,
                        progress_callback=progress_callback,
                    )

                    st.session_state.generated_assets = asset_set
                    st.session_state.current_step = 4
                    st.markdown(success_banner(
                        f"Generated {asset_set.valid_count} assets!",
                        "Proceeding to export...",
                    ), unsafe_allow_html=True)
                    st.rerun()

                except LayerAPIError as e:
                    st.error(f"Layer.ai Error: {str(e)}")
                except Exception as e:
                    st.error(f"Generation failed: {str(e)}")


# =============================================================================
# Step 4: Export Playable
# =============================================================================

def render_step_4():
    """Step 4: Export playable ad."""
    st.markdown(step_header(4, "Export Playable Ad"), unsafe_allow_html=True)

    # Check if we're in demo mode (playable_result exists but no assets)
    is_demo_mode = st.session_state.playable_result is not None and st.session_state.generated_assets is None

    analysis: GameAnalysis = st.session_state.game_analysis
    assets: GeneratedAssetSet = st.session_state.generated_assets

    if is_demo_mode:
        # Skip asset section for demo mode
        mechanic_type = st.session_state.playable_result.mechanic_type
    elif not assets:
        st.warning("No assets generated. Please go back.")
        if st.button("Back"):
            st.session_state.current_step = 3
            st.rerun()
        return
    else:
        mechanic_type = st.session_state.selected_mechanic or analysis.mechanic_type

    # Asset preview (skip in demo mode)
    if not is_demo_mode and assets:
        # Build asset preview cards
        preview_cards = ""
        for key, asset in assets.assets.items():
            preview_cards += asset_preview_card(
                key=key,
                image_url=asset.image_url if asset.is_valid else "",
                is_valid=asset.is_valid,
                error=asset.error or "",
            )

        st.markdown(glass_card(
            title=f"Generated Assets &middot; {assets.total_generation_time:.1f}s",
            icon="&#128444;",
            content=f'<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(120px,1fr));gap:8px;">{preview_cards}</div>',
        ), unsafe_allow_html=True)

        # Still show actual images via Streamlit for clickability
        cols = st.columns(min(len(assets.assets), 5))
        for i, (key, asset) in enumerate(assets.assets.items()):
            with cols[i % len(cols)]:
                if asset.is_valid and asset.image_url:
                    st.image(asset.image_url, caption=key, width=100)

    elif is_demo_mode:
        st.markdown(glass_card(
            title="Demo Mode",
            icon="&#127918;",
            content='<div style="font-size:0.85rem;color:var(--text-muted);">Using fallback graphics (colored shapes)</div>',
            accent="var(--accent-secondary)",
        ), unsafe_allow_html=True)

    # Configuration (skip build options in demo mode - already built)
    if not is_demo_mode:
        st.markdown(gradient_divider(), unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            st.markdown(glass_card(
                title="Game Info",
                icon="&#127918;",
                content="",
            ), unsafe_allow_html=True)
            game_name = st.text_input("Game Name", value=analysis.game_name if analysis else "My Game")
            hook_text = st.text_input("Hook Text", value=analysis.hook_suggestion if analysis else "Tap to Play!")
            cta_text = st.text_input("CTA Text", value=analysis.cta_suggestion if analysis else "Download FREE")

        with col2:
            st.markdown(glass_card(
                title="Technical",
                icon="&#9881;",
                content="",
            ), unsafe_allow_html=True)
            store_url_ios = st.text_input("App Store URL (iOS)", value="https://apps.apple.com/app/id123456789")
            store_url_android = st.text_input("Play Store URL (Android)", value="https://play.google.com/store/apps/details?id=com.example.game")
            bg_color = st.color_picker("Background Color", value="#1a1a2e")

        # Size preset
        size_preset = st.radio(
            "Canvas Size",
            options=["Portrait (320x480)", "Square (320x320)", "Landscape (480x320)"],
            horizontal=True,
        )

        if size_preset == "Portrait (320x480)":
            width, height = 320, 480
        elif size_preset == "Square (320x320)":
            width, height = 320, 320
        else:
            width, height = 480, 320

        # Build button
        st.markdown(gradient_divider(), unsafe_allow_html=True)
        col1, col2 = st.columns([1, 2])

        with col1:
            if st.button("Back to Assets"):
                st.session_state.current_step = 3
                st.rerun()

        with col2:
            if st.button("Build Playable", type="primary"):
                with st.spinner("Building playable ad..."):
                    try:
                        config = PlayableConfig(
                            game_name=game_name,
                            title=game_name,
                            store_url=store_url_ios or store_url_android,
                            store_url_ios=store_url_ios,
                            store_url_android=store_url_android,
                            width=width,
                            height=height,
                            background_color=bg_color,
                            hook_text=hook_text,
                            cta_text=cta_text,
                        )

                        builder = PlayableBuilder()
                        result = builder.build(analysis, assets, config)

                        st.session_state.playable_result = result
                        st.markdown(success_banner("Playable built successfully!"), unsafe_allow_html=True)

                    except Exception as e:
                        st.error(f"Build failed: {str(e)}")

    # Results
    if st.session_state.playable_result:
        result: PlayableResult = st.session_state.playable_result

        st.markdown(gradient_divider(), unsafe_allow_html=True)
        st.markdown(success_banner(
            "Playable Ready",
            "Your ad is built and ready for download.",
        ), unsafe_allow_html=True)

        # Metrics as custom cards
        size_status = "success" if result.file_size_mb <= 5 else "error"
        valid_status = "success" if result.is_valid else "warning"

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(metric_card("File Size", result.file_size_formatted, status=size_status), unsafe_allow_html=True)
        with col2:
            st.markdown(metric_card("Assets", str(result.assets_embedded)), unsafe_allow_html=True)
        with col3:
            st.markdown(metric_card("Mechanic", result.mechanic_type.value), unsafe_allow_html=True)
        with col4:
            status_val = "Valid" if result.is_valid else "Issues"
            st.markdown(metric_card("Status", status_val, status=valid_status), unsafe_allow_html=True)

        if result.validation_errors:
            for error in result.validation_errors:
                st.warning(error)

        # Network compatibility badges
        st.markdown(glass_card(
            title="Network Compatibility",
            icon="&#127760;",
            content=network_badges([], file_size_mb=result.file_size_mb),
        ), unsafe_allow_html=True)

        # Downloads
        st.markdown(gradient_divider(), unsafe_allow_html=True)

        st.markdown(glass_card(
            title="Download",
            icon="&#128229;",
            content="""
            <div style="font-size:0.82rem;color:var(--text-muted);margin-bottom:4px;">
                Single self-contained HTML file &middot; MRAID 3.0 compliant
            </div>
            """,
            accent="var(--color-success)",
        ), unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            st.download_button(
                label="Download index.html",
                data=result.html,
                file_name="index.html",
                mime="text/html",
            )

        with col2:
            # Create ZIP
            import io
            import zipfile

            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
                zf.writestr("index.html", result.html)
            zip_data = zip_buffer.getvalue()

            st.download_button(
                label="Download ZIP (Google Ads)",
                data=zip_data,
                file_name="playable_ad.zip",
                mime="application/zip",
            )

        # Preview in phone mockup
        st.markdown(gradient_divider(), unsafe_allow_html=True)
        if st.checkbox("Show Preview"):
            b64 = base64.b64encode(result.html.encode()).decode()
            st.markdown(phone_preview(b64, width=320, height=480), unsafe_allow_html=True)

        # Start over
        st.markdown(gradient_divider(), unsafe_allow_html=True)
        if st.button("Create Another Playable"):
            for key in ["screenshots", "game_analysis", "selected_mechanic",
                       "layer_style_id", "generated_assets", "playable_result"]:
                st.session_state[key] = None if key != "screenshots" else []
            st.session_state.current_step = 1
            st.rerun()


# =============================================================================
# Main
# =============================================================================

def main():
    """Main application entry point."""
    init_session_state()
    render_sidebar()

    # Gradient title
    st.markdown("""
    <div class="animate-fade-in">
        <span class="gradient-title">Playable Ad Generator</span>
        <div style="font-size:0.88rem;color:var(--text-muted);margin-top:4px;">
            Create game-specific playable ads using AI
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown(gradient_divider(), unsafe_allow_html=True)

    # Check if we're in demo mode (step 4 with playable result but no assets)
    is_demo_mode = (
        st.session_state.current_step == 4
        and st.session_state.playable_result is not None
        and st.session_state.generated_assets is None
    )

    # Check API keys (skip if in demo mode)
    if not is_demo_mode:
        keys = validate_api_keys()
        if not all(keys.values()):
            st.markdown(onboarding_card(), unsafe_allow_html=True)
            return

    # Render current step
    step = st.session_state.current_step

    if step == 1:
        render_step_1()
    elif step == 2:
        render_step_2()
    elif step == 3:
        render_step_3()
    elif step == 4:
        render_step_4()


if __name__ == "__main__":
    main()
