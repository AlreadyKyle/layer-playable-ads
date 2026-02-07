"""
Layer.ai Playable Studio v2.0 - Game-Specific Playable Ad Generator

New Workflow:
1. Input Game - Upload screenshots or enter App Store URL
2. Analyze & Review - Claude Vision extracts mechanics and style
3. Generate Assets - Layer.ai creates game-specific art
4. Export Playable - Build and download MRAID-compliant HTML5 playable
"""

import base64
from pathlib import Path
import tempfile
from typing import Optional

import streamlit as st

from src.analysis.game_analyzer import GameAnalyzerSync, GameAnalysis
from src.generation.game_asset_generator import GameAssetGenerator, GeneratedAssetSet
from src.assembly.builder import PlayableBuilder, PlayableConfig, PlayableResult
from src.layer_client import LayerClientSync, LayerAPIError, extract_error_message
from src.templates.registry import MechanicType, TEMPLATE_REGISTRY, list_available_mechanics
from src.utils.helpers import validate_api_keys, get_settings


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
    .stApp { background-color: #0e1117; }
    .step-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #fafafa;
        margin-bottom: 1rem;
        padding: 0.5rem 0;
        border-bottom: 2px solid #ff4b4b;
    }
    .mechanic-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 16px;
        font-size: 0.9rem;
        font-weight: 500;
        margin: 4px;
    }
    .high-confidence { background-color: #276749; color: #9ae6b4; }
    .medium-confidence { background-color: #744210; color: #fbd38d; }
    .low-confidence { background-color: #742a2a; color: #feb2b2; }
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
    st.sidebar.title("🎮 Playable Generator")
    st.sidebar.caption("AI-Powered Game Ad Creation")

    # API Status
    st.sidebar.markdown("---")
    st.sidebar.subheader("API Status")

    key_status = validate_api_keys()
    all_keys_set = all(key_status.values())

    for key, is_set in key_status.items():
        icon = "✅" if is_set else "❌"
        name = key.replace("_", " ").title()
        st.sidebar.text(f"{icon} {name}")

    if all_keys_set:
        info = fetch_workspace_info()
        if info and "error" not in info:
            if info.get("has_access") is False:
                st.sidebar.warning("Could not verify credits — generation blocked for safety")
            else:
                st.sidebar.metric("Layer.ai Credits", info.get("credits_available", "?"))

    # Workflow Progress
    st.sidebar.markdown("---")
    st.sidebar.subheader("Workflow")

    steps = [
        ("1. Input Game", 1),
        ("2. Analyze & Review", 2),
        ("3. Generate Assets", 3),
        ("4. Export Playable", 4),
    ]

    for label, step_num in steps:
        if st.session_state.current_step == step_num:
            st.sidebar.markdown(f"**→ {label}**")
        elif st.session_state.current_step > step_num:
            st.sidebar.markdown(f"✅ {label}")
        else:
            st.sidebar.markdown(f"○ {label}")

    # Supported Games
    st.sidebar.markdown("---")
    st.sidebar.subheader("Supported Game Types")
    for mechanic in list_available_mechanics():
        template = TEMPLATE_REGISTRY[mechanic]
        st.sidebar.text(f"• {template.name}")

    # Demo Mode
    st.sidebar.markdown("---")
    st.sidebar.subheader("Quick Demo")
    st.sidebar.caption("Test without API keys")

    demo_type = st.sidebar.selectbox(
        "Game Type",
        options=["match3", "runner", "tapper"],
        format_func=lambda x: {"match3": "Match-3", "runner": "Runner", "tapper": "Tapper"}[x],
        key="demo_type_select",
    )

    if st.sidebar.button("🎮 Generate Demo", key="demo_btn"):
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
    st.markdown('<p class="step-header">Step 1: Input Your Game</p>', unsafe_allow_html=True)

    st.write("""
    Upload 1-5 screenshots from the game you want to create a playable ad for.
    The AI will analyze the game mechanics and visual style.
    """)

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

        if st.button("🔍 Analyze Game", type="primary"):
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
        st.info("👆 Upload game screenshots to begin")


# =============================================================================
# Step 2: Analyze & Review
# =============================================================================

def render_step_2():
    """Step 2: Review and confirm analysis."""
    st.markdown('<p class="step-header">Step 2: Review Analysis</p>', unsafe_allow_html=True)

    analysis: GameAnalysis = st.session_state.game_analysis

    if not analysis:
        st.warning("No analysis available. Please go back and upload screenshots.")
        if st.button("← Back"):
            st.session_state.current_step = 1
            st.rerun()
        return

    # Game info
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader(f"🎮 {analysis.game_name}")
        if analysis.publisher:
            st.caption(f"by {analysis.publisher}")

        # Mechanic type with confidence
        confidence_class = {
            "high": "high-confidence",
            "medium": "medium-confidence",
            "low": "low-confidence",
        }.get(analysis.confidence_level.value, "medium-confidence")

        st.markdown(f"""
        <span class="mechanic-badge {confidence_class}">
            {analysis.mechanic_type.value.upper()} ({int(analysis.mechanic_confidence * 100)}% confident)
        </span>
        """, unsafe_allow_html=True)

        st.write(f"**Why:** {analysis.mechanic_reasoning}")

        # Core loop
        st.markdown("---")
        st.subheader("Core Game Loop")
        st.write(analysis.core_loop_description)

    with col2:
        # Visual style
        st.subheader("Visual Style")
        st.write(f"**Art:** {analysis.visual_style.art_type}")
        st.write(f"**Theme:** {analysis.visual_style.theme}")
        st.write(f"**Mood:** {analysis.visual_style.mood}")

        # Color palette
        st.write("**Colors:**")
        color_html = ""
        for color in analysis.visual_style.color_palette[:6]:
            color_html += f'<span style="background-color:{color}; padding: 5px 15px; margin: 2px; border-radius: 4px;">&nbsp;</span>'
        st.markdown(color_html, unsafe_allow_html=True)

    # Allow override of mechanic type
    st.markdown("---")
    st.subheader("Confirm Game Type")

    mechanic_options = [m.value for m in list_available_mechanics()]
    current_index = mechanic_options.index(analysis.mechanic_type.value) if analysis.mechanic_type.value in mechanic_options else 0

    selected = st.selectbox(
        "Game Mechanic Type",
        options=mechanic_options,
        index=current_index,
        format_func=lambda x: TEMPLATE_REGISTRY[MechanicType(x)].name,
    )

    st.session_state.selected_mechanic = MechanicType(selected)

    # Show template info
    template = TEMPLATE_REGISTRY[st.session_state.selected_mechanic]
    with st.expander("Template Details"):
        st.write(f"**Template:** {template.name}")
        st.write(f"**Description:** {template.description}")
        st.write(f"**Example Games:** {', '.join(template.example_games)}")
        st.write("**Required Assets:**")
        for asset in template.required_assets:
            st.write(f"  • {asset.key}: {asset.description}")

    # Assets needed
    st.markdown("---")
    st.subheader("Assets to Generate")

    if analysis.assets_needed:
        for asset in analysis.assets_needed:
            st.write(f"• **{asset.key}**: {asset.description}")
    else:
        st.info("Using default asset prompts for this template")

    # Navigation
    st.markdown("---")
    col1, col2 = st.columns([1, 2])

    with col1:
        if st.button("← Back to Screenshots"):
            st.session_state.current_step = 1
            st.rerun()

    with col2:
        if st.button("Continue to Asset Generation →", type="primary"):
            st.session_state.current_step = 3
            st.rerun()


# =============================================================================
# Step 3: Generate Assets
# =============================================================================

def render_step_3():
    """Step 3: Generate assets with Layer.ai."""
    st.markdown('<p class="step-header">Step 3: Generate Assets</p>', unsafe_allow_html=True)

    analysis: GameAnalysis = st.session_state.game_analysis
    mechanic_type = st.session_state.selected_mechanic or analysis.mechanic_type

    # Style selection
    st.subheader("Select Layer.ai Style")
    st.write("Choose a trained style from your Layer.ai workspace to generate assets.")

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

    # Show what will be generated
    st.markdown("---")
    st.subheader("Assets to Generate")

    template = TEMPLATE_REGISTRY[mechanic_type]
    for asset in template.required_assets:
        if asset.required:
            st.write(f"• **{asset.key}**: {asset.description}")

    # Navigation
    st.markdown("---")
    col1, col2 = st.columns([1, 2])

    with col1:
        if st.button("← Back to Analysis"):
            st.session_state.current_step = 2
            st.rerun()

    with col2:
        can_generate = st.session_state.layer_style_id is not None

        if st.button("⚡ Generate Assets", type="primary", disabled=not can_generate):
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
                    st.success(f"Generated {asset_set.valid_count} assets!")
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
    st.markdown('<p class="step-header">Step 4: Export Playable Ad</p>', unsafe_allow_html=True)

    # Check if we're in demo mode (playable_result exists but no assets)
    is_demo_mode = st.session_state.playable_result is not None and st.session_state.generated_assets is None

    analysis: GameAnalysis = st.session_state.game_analysis
    assets: GeneratedAssetSet = st.session_state.generated_assets

    if is_demo_mode:
        # Skip asset section for demo mode
        mechanic_type = st.session_state.playable_result.mechanic_type
    elif not assets:
        st.warning("No assets generated. Please go back.")
        if st.button("← Back"):
            st.session_state.current_step = 3
            st.rerun()
        return
    else:
        mechanic_type = st.session_state.selected_mechanic or analysis.mechanic_type

    # Asset preview (skip in demo mode)
    if not is_demo_mode and assets:
        st.subheader("Generated Assets")
        cols = st.columns(min(len(assets.assets), 5))
        for i, (key, asset) in enumerate(assets.assets.items()):
            with cols[i % len(cols)]:
                if asset.is_valid and asset.image_url:
                    st.image(asset.image_url, caption=key, width=100)
                else:
                    st.write(f"❌ {key}")
                    if asset.error:
                        st.caption(asset.error[:50])

        st.caption(f"Generation time: {assets.total_generation_time:.1f}s")
    elif is_demo_mode:
        st.info("🎮 **Demo Mode** - Using fallback graphics (colored shapes)")

    # Configuration (skip build options in demo mode - already built)
    if not is_demo_mode:
        st.markdown("---")
        st.subheader("Playable Settings")

        col1, col2 = st.columns(2)

        with col1:
            game_name = st.text_input("Game Name", value=analysis.game_name if analysis else "My Game")
            hook_text = st.text_input("Hook Text", value=analysis.hook_suggestion if analysis else "Tap to Play!")
            cta_text = st.text_input("CTA Text", value=analysis.cta_suggestion if analysis else "Download FREE")

        with col2:
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
        st.markdown("---")
        col1, col2 = st.columns([1, 2])

        with col1:
            if st.button("← Back to Assets"):
                st.session_state.current_step = 3
                st.rerun()

        with col2:
            if st.button("🎬 Build Playable", type="primary"):
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
                        st.success("Playable built successfully!")

                    except Exception as e:
                        st.error(f"Build failed: {str(e)}")

    # Results
    if st.session_state.playable_result:
        result: PlayableResult = st.session_state.playable_result

        st.markdown("---")
        st.subheader("✅ Playable Ready")

        # Metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("File Size", result.file_size_formatted)
        with col2:
            st.metric("Assets", result.assets_embedded)
        with col3:
            st.metric("Mechanic", result.mechanic_type.value)
        with col4:
            status = "✅ Valid" if result.is_valid else "⚠️ Issues"
            st.metric("Status", status)

        if result.validation_errors:
            for error in result.validation_errors:
                st.warning(error)

        # Network compatibility
        networks = ["Google Ads", "Unity", "IronSource", "AppLovin"]
        if result.file_size_mb <= 2:
            networks.append("Facebook")

        st.write("**Compatible Networks:** " + ", ".join(networks))

        # Downloads
        st.markdown("---")
        st.subheader("Download")

        col1, col2 = st.columns(2)

        with col1:
            st.download_button(
                label="📥 Download index.html",
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
                label="📦 Download ZIP (Google Ads)",
                data=zip_data,
                file_name="playable_ad.zip",
                mime="application/zip",
            )

        # Preview
        st.markdown("---")
        if st.checkbox("Show Preview"):
            st.subheader("Preview")
            b64 = base64.b64encode(result.html.encode()).decode()
            st.markdown(f"""
            <iframe
                src="data:text/html;base64,{b64}"
                width="340"
                height="500"
                style="border: 2px solid #333; border-radius: 8px;"
            ></iframe>
            """, unsafe_allow_html=True)

        # Start over
        st.markdown("---")
        if st.button("🔄 Create Another Playable"):
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

    st.title("🎮 Playable Ad Generator")
    st.caption("Create game-specific playable ads using AI")

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
            st.warning("⚠️ Missing API keys. Use Demo Mode in sidebar to test without keys.")
            st.markdown("""
            **Required keys for full workflow:**
            - `LAYER_API_KEY` - Your Layer.ai API key
            - `LAYER_WORKSPACE_ID` - Your Layer.ai workspace ID
            - `ANTHROPIC_API_KEY` - Your Anthropic API key

            Create a `.env` file or add to Streamlit secrets.

            **Or try Demo Mode** in the sidebar to see the playable output without API keys.
            """)
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
