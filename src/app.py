"""
Layer.ai Playable Studio - Streamlit Application

Main entry point for the LPS web interface.
Implements a wizard-style UI for playable ad generation.
"""

import base64
from pathlib import Path
from typing import Optional

import streamlit as st

from src.layer_client import LayerClientSync, StyleRecipe
from src.utils.helpers import get_settings, validate_api_keys
from src.vision.competitor_spy import CompetitorSpy, AnalysisResult
from src.workflow.style_manager import StyleManager, ManagedStyle
from src.forge.asset_forger import AssetForger, ForgeSession, UA_PRESETS
from src.playable.assembler import (
    PlayableAssembler,
    PlayableConfig,
    PlayableMetadata,
    HOOK_DURATION_MS,
    GAMEPLAY_DURATION_MS,
    CTA_DURATION_MS,
)


# =============================================================================
# Page Configuration
# =============================================================================

st.set_page_config(
    page_title="Layer.ai Playable Studio",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Enterprise dark theme CSS
st.markdown("""
<style>
    .stApp {
        background-color: #0e1117;
    }
    .step-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #fafafa;
        margin-bottom: 1rem;
        padding: 0.5rem;
        border-left: 4px solid #ff4b4b;
    }
    .status-card {
        background-color: #1e2128;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #ff4b4b;
    }
    .timing-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 16px;
        font-size: 0.875rem;
        margin: 4px;
    }
    .hook-badge { background-color: #ff6b6b; color: white; }
    .gameplay-badge { background-color: #4ecdc4; color: white; }
    .cta-badge { background-color: #45b7d1; color: white; }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# Session State Initialization
# =============================================================================

def init_session_state():
    """Initialize session state variables."""
    defaults = {
        "current_step": 1,
        "analysis_result": None,
        "style_recipe": None,
        "managed_style": None,
        "forge_session": None,
        "forged_assets": None,
        "playable_html": None,
        "playable_metadata": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_session_state()


# =============================================================================
# Sidebar
# =============================================================================

def render_sidebar():
    """Render the sidebar with status and navigation."""
    st.sidebar.title("🎮 Playable Studio")
    st.sidebar.caption("Layer.ai Intelligence → Playable")

    # API Status
    st.sidebar.markdown("---")
    st.sidebar.subheader("API Status")

    key_status = validate_api_keys()
    for key, is_set in key_status.items():
        icon = "✅" if is_set else "❌"
        name = key.replace("_", " ").title()
        st.sidebar.text(f"{icon} {name}")

    # Workflow Progress
    st.sidebar.markdown("---")
    st.sidebar.subheader("Workflow")

    steps = [
        ("1. Style Intel", 1),
        ("2. Style Lock", 2),
        ("3. Variant Forge", 3),
        ("4. Export", 4),
    ]

    for label, step_num in steps:
        if st.session_state.current_step == step_num:
            st.sidebar.markdown(f"**→ {label}**")
        elif st.session_state.current_step > step_num:
            st.sidebar.markdown(f"✅ {label}")
        else:
            st.sidebar.markdown(f"○ {label}")

    # Timing Reference
    st.sidebar.markdown("---")
    st.sidebar.subheader("Ad Timing")
    st.sidebar.markdown(f"""
    <span class="timing-badge hook-badge">Hook: {HOOK_DURATION_MS/1000}s</span>
    <span class="timing-badge gameplay-badge">Loop: {GAMEPLAY_DURATION_MS/1000}s</span>
    <span class="timing-badge cta-badge">CTA: {CTA_DURATION_MS/1000}s</span>
    """, unsafe_allow_html=True)

    # Credits (if connected)
    if all(key_status.values()):
        try:
            client = LayerClientSync()
            credits = client.get_workspace_credits()
            st.sidebar.markdown("---")
            st.sidebar.metric("Credits Available", credits.available)
            if not credits.is_sufficient:
                st.sidebar.warning("⚠️ Low credits!")
        except Exception:
            pass


# =============================================================================
# Step 1: Style Intelligence
# =============================================================================

def render_step_1():
    """Step 1: Analyze competitor and extract style."""
    st.markdown('<p class="step-header">Step 1: Style Intelligence</p>', unsafe_allow_html=True)

    st.write("""
    Upload exactly 3 competitor screenshots to extract a visual style recipe using AI vision analysis.
    """)

    st.subheader("📸 Upload 3 Screenshots")
    uploaded_files = st.file_uploader(
        "Upload exactly 3 game screenshots",
        type=["png", "jpg", "jpeg", "webp"],
        accept_multiple_files=True,
        key="screenshot_upload",
        help="Upload 3 screenshots from the competitor game for best style analysis results"
    )

    if uploaded_files:
        if len(uploaded_files) != 3:
            st.warning(f"⚠️ Please upload exactly 3 screenshots (currently {len(uploaded_files)} uploaded)")
        else:
            st.success("✅ 3 screenshots uploaded")

        cols = st.columns(min(len(uploaded_files), 3))
        for idx, f in enumerate(uploaded_files[:3]):
            with cols[idx]:
                st.image(f, caption=f"Screenshot {idx + 1}", use_container_width=True)

    # Additional context
    context = st.text_area(
        "Additional Context (optional)",
        placeholder="e.g., 'Match-3 puzzle game with fantasy theme'",
        key="analysis_context",
    )

    # Analyze button
    if st.button("🔍 Analyze & Extract Style", type="primary"):
        if not uploaded_files or len(uploaded_files) != 3:
            st.error("Please upload exactly 3 screenshots to proceed")
            return

        with st.spinner("Analyzing visual style with Claude Vision..."):
            try:
                spy = CompetitorSpy()

                # Save uploaded files temporarily
                temp_paths = []
                for f in uploaded_files:
                    temp_path = Path(f"/tmp/{f.name}")
                    temp_path.write_bytes(f.read())
                    temp_paths.append(temp_path)

                result = spy.analyze_screenshots(temp_paths, context)

                st.session_state.analysis_result = result
                st.session_state.style_recipe = result.recipe
                st.session_state.current_step = 2
                st.rerun()

            except Exception as e:
                st.error(f"Analysis failed: {str(e)}")


# =============================================================================
# Step 2: Style Lock
# =============================================================================

def render_step_2():
    """Step 2: Review and lock the style recipe."""
    st.markdown('<p class="step-header">Step 2: Style Lock</p>', unsafe_allow_html=True)

    result: AnalysisResult = st.session_state.analysis_result
    recipe: StyleRecipe = st.session_state.style_recipe

    if not result or not recipe:
        st.warning("No analysis result. Go back to Step 1.")
        if st.button("← Back to Step 1"):
            st.session_state.current_step = 1
            st.rerun()
        return

    # Analysis summary
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📊 Analysis Results")
        st.markdown(f"""
        - **Genre**: {result.genre}
        - **Art Style**: {result.art_style}
        - **Target Audience**: {result.target_audience}
        - **Key Elements**: {', '.join(result.key_visual_elements[:5])}
        """)

    with col2:
        st.subheader("🎨 Color Palette")
        col2a, col2b = st.columns(2)
        with col2a:
            st.color_picker("Primary", recipe.palette_primary, key="primary_color", disabled=True)
        with col2b:
            st.color_picker("Accent", recipe.palette_accent, key="accent_color", disabled=True)

    # Editable recipe
    st.subheader("✏️ Style Recipe")

    edited_name = st.text_input("Style Name", recipe.style_name, key="edit_name")
    edited_prefix = st.text_area(
        "Prefix Terms (comma-separated)",
        ", ".join(recipe.prefix),
        key="edit_prefix",
    )
    edited_technical = st.text_area(
        "Technical Terms (comma-separated)",
        ", ".join(recipe.technical),
        key="edit_technical",
    )
    edited_negative = st.text_area(
        "Negative Terms (comma-separated)",
        ", ".join(recipe.negative),
        key="edit_negative",
    )

    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        if st.button("← Back"):
            st.session_state.current_step = 1
            st.rerun()

    with col2:
        if st.button("🔄 Reset"):
            st.session_state.style_recipe = st.session_state.analysis_result.recipe
            st.rerun()

    with col3:
        if st.button("🔒 Lock Style & Create in Layer.ai", type="primary"):
            # Update recipe with edits
            recipe.style_name = edited_name
            recipe.prefix = [t.strip() for t in edited_prefix.split(",") if t.strip()]
            recipe.technical = [t.strip() for t in edited_technical.split(",") if t.strip()]
            recipe.negative = [t.strip() for t in edited_negative.split(",") if t.strip()]

            with st.spinner("Creating style in Layer.ai..."):
                try:
                    manager = StyleManager()
                    managed = manager.create_style_from_recipe(recipe)
                    st.session_state.managed_style = managed
                    st.session_state.current_step = 3
                    st.success("✅ Style created successfully in Layer.ai!")
                    st.rerun()
                except Exception as e:
                    error_msg = str(e)
                    st.error(f"❌ Failed to create style in Layer.ai")

                    # Show detailed error information
                    with st.expander("Error Details"):
                        st.code(error_msg)
                        st.markdown("""
                        **Common causes:**
                        - Layer.ai API temporarily unavailable (try again in a moment)
                        - Invalid API credentials
                        - Network connectivity issues
                        - Rate limiting

                        **Troubleshooting:**
                        1. Check your API keys in the sidebar
                        2. Verify your workspace ID is correct
                        3. Try again in a few seconds
                        4. Check the Layer.ai dashboard at https://app.layer.ai
                        """)


# =============================================================================
# Step 3: Variant Forge
# =============================================================================

def render_step_3():
    """Step 3: Forge asset variants."""
    st.markdown('<p class="step-header">Step 3: Variant Forge</p>', unsafe_allow_html=True)

    managed: ManagedStyle = st.session_state.managed_style

    if not managed:
        st.warning("No style locked. Go back to Step 2.")
        if st.button("← Back to Step 2"):
            st.session_state.current_step = 2
            st.rerun()
        return

    # Style info
    st.info(f"**Style**: {managed.name} | [Open in Layer.ai Dashboard]({managed.dashboard_url})")

    # Preset selection
    st.subheader("🎯 UA Presets")
    st.write("Select which asset types to generate for your playable ad:")

    col1, col2, col3 = st.columns(3)

    selected_presets = []

    with col1:
        st.markdown("**🎣 Hook (3s)**")
        if st.checkbox("Character", value=True, key="preset_hook_char"):
            selected_presets.append("hook_character")
        if st.checkbox("Item/Collectible", value=True, key="preset_hook_item"):
            selected_presets.append("hook_item")

    with col2:
        st.markdown("**🎮 Gameplay (15s)**")
        if st.checkbox("Background", value=True, key="preset_gameplay_bg"):
            selected_presets.append("gameplay_background")
        if st.checkbox("Game Elements", value=True, key="preset_gameplay_elem"):
            selected_presets.append("gameplay_element")

    with col3:
        st.markdown("**📲 CTA (5s)**")
        if st.checkbox("Button", value=True, key="preset_cta_btn"):
            selected_presets.append("cta_button")
        if st.checkbox("Banner", value=True, key="preset_cta_banner"):
            selected_presets.append("cta_banner")

    st.write(f"**Selected**: {len(selected_presets)} presets")

    col1, col2 = st.columns([1, 2])

    with col1:
        if st.button("← Back"):
            st.session_state.current_step = 2
            st.rerun()

    with col2:
        if st.button("⚡ Forge Assets", type="primary", disabled=len(selected_presets) == 0):
            with st.spinner("Forging assets (this may take a few minutes)..."):
                try:
                    forger = AssetForger()
                    session = forger.start_session(managed.style_id)

                    progress = st.progress(0)
                    status = st.empty()

                    forged = []
                    for i, preset in enumerate(selected_presets):
                        status.text(f"Forging {preset}...")
                        asset = forger.forge_from_preset(preset)
                        forged.append(asset)
                        progress.progress((i + 1) / len(selected_presets))

                    st.session_state.forge_session = forger.end_session()
                    st.session_state.forged_assets = forged
                    st.session_state.current_step = 4
                    st.rerun()

                except Exception as e:
                    st.error(f"Forge failed: {str(e)}")


# =============================================================================
# Step 4: Export & Preview
# =============================================================================

def render_step_4():
    """Step 4: Assemble and export playable."""
    st.markdown('<p class="step-header">Step 4: Export & Preview</p>', unsafe_allow_html=True)

    session: ForgeSession = st.session_state.forge_session
    forged = st.session_state.forged_assets

    if not session or not forged:
        st.warning("No forged assets. Go back to Step 3.")
        if st.button("← Back to Step 3"):
            st.session_state.current_step = 3
            st.rerun()
        return

    # Asset summary
    st.subheader("📦 Forged Assets")
    cols = st.columns(min(len(forged), 4))
    for i, asset in enumerate(forged):
        with cols[i % len(cols)]:
            if asset.image_url:
                st.image(asset.image_url, caption=asset.preset_name, width=150)
            st.caption(f"Category: {asset.category}")

    # Playable configuration
    st.subheader("⚙️ Playable Settings")

    col1, col2 = st.columns(2)

    with col1:
        title = st.text_input("Ad Title", "My Playable Ad", key="playable_title")
        store_url = st.text_input(
            "App Store URL",
            "https://apps.apple.com",
            key="store_url",
        )
        hook_text = st.text_input("Hook Text", "Play Now!", key="hook_text")
        cta_text = st.text_input("CTA Text", "Get it FREE!", key="cta_text")

    with col2:
        width = st.number_input("Width", 320, 1080, 320, key="canvas_width")
        height = st.number_input("Height", 480, 1920, 480, key="canvas_height")
        bg_color = st.color_picker("Background Color", "#1a1a2e", key="bg_color")

    col1, col2 = st.columns([1, 2])

    with col1:
        if st.button("← Back"):
            st.session_state.current_step = 3
            st.rerun()

    with col2:
        if st.button("🎬 Assemble Playable", type="primary"):
            with st.spinner("Assembling playable ad..."):
                try:
                    assembler = PlayableAssembler()

                    # Group forged assets by category
                    asset_set = {"hook": [], "gameplay": [], "cta": []}
                    for asset in forged:
                        if asset.category in asset_set:
                            asset_set[asset.category].append(asset)

                    # Prepare assets
                    prepared = assembler.prepare_assets_from_set(asset_set)

                    # Configure
                    config = PlayableConfig(
                        title=title,
                        width=int(width),
                        height=int(height),
                        background_color=bg_color,
                        store_url=store_url,
                        hook_text=hook_text,
                        cta_text=cta_text,
                    )

                    # Assemble
                    html, metadata = assembler.assemble(prepared, config)

                    st.session_state.playable_html = html
                    st.session_state.playable_metadata = metadata

                    st.success("Playable assembled successfully!")

                except Exception as e:
                    st.error(f"Assembly failed: {str(e)}")

    # Show results if assembled
    if st.session_state.playable_html:
        metadata: PlayableMetadata = st.session_state.playable_metadata
        html = st.session_state.playable_html

        st.markdown("---")
        st.subheader("✅ Playable Ready")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("File Size", metadata.file_size_formatted)
        with col2:
            st.metric("Assets", metadata.asset_count)
        with col3:
            valid = "✅ Valid" if metadata.is_valid_size else "❌ Too Large"
            st.metric("Size Check", valid)

        # Download button
        st.download_button(
            label="📥 Download index.html",
            data=html,
            file_name="index.html",
            mime="text/html",
        )

        # Preview (iframe)
        if st.checkbox("Show Preview", key="show_preview"):
            b64 = base64.b64encode(html.encode()).decode()
            st.markdown(f"""
            <iframe
                src="data:text/html;base64,{b64}"
                width="340"
                height="500"
                style="border: 2px solid #333; border-radius: 8px;"
            ></iframe>
            """, unsafe_allow_html=True)


# =============================================================================
# Main Application
# =============================================================================

def main():
    """Main application entry point."""
    render_sidebar()

    st.title("Layer.ai Playable Studio")
    st.caption("Intelligence → Playable Ad Pipeline")

    # Check API keys
    keys = validate_api_keys()
    if not all(keys.values()):
        st.error("⚠️ Missing API keys. Please configure your .env file.")
        st.markdown("""
        Required keys:
        - `LAYER_API_KEY` - Your Layer.ai API key
        - `LAYER_WORKSPACE_ID` - Your Layer.ai workspace ID
        - `ANTHROPIC_API_KEY` - Your Anthropic API key for Claude

        Copy `.env.example` to `.env` and fill in your values.
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
