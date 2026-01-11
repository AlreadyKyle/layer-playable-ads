"""
Layer.ai Playable Studio - Streamlit Application

MVP v1.0 - AI-powered playable ad generation workflow.

3-Step Process:
1. Select Style - Choose from your Layer.ai trained styles
2. Generate Assets - Create hook, gameplay, and CTA assets
3. Export Playable - Build and download MRAID-compliant HTML5 playable
"""

import base64
from pathlib import Path
import tempfile

import streamlit as st

from src.layer_client import (
    LayerClientSync,
    StyleConfig,
    LayerAPIError,
)
from src.forge.asset_forger import (
    AssetGenerator,
    AssetType,
    AssetSet,
    ASSET_PRESETS,
)
from src.playable.assembler import (
    PlayableAssembler,
    PlayableConfig,
    PlayableMetadata,
    AdNetwork,
    NETWORK_SPECS,
    HOOK_DURATION_MS,
    GAMEPLAY_DURATION_MS,
    CTA_DURATION_MS,
)
from src.utils.helpers import validate_api_keys


# =============================================================================
# Page Configuration
# =============================================================================

st.set_page_config(
    page_title="Layer.ai Playable Studio",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Clean CSS
st.markdown("""
<style>
    .stApp { background-color: #0e1117; }
    .step-header {
        font-size: 1.4rem;
        font-weight: 600;
        color: #fafafa;
        margin-bottom: 1rem;
        padding: 0.5rem 0;
        border-bottom: 2px solid #ff4b4b;
    }
    .timing-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 16px;
        font-size: 0.8rem;
        margin: 2px;
        font-weight: 500;
    }
    .hook-badge { background-color: #ff6b6b; color: white; }
    .gameplay-badge { background-color: #4ecdc4; color: white; }
    .cta-badge { background-color: #45b7d1; color: white; }
    .network-badge {
        display: inline-block;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 0.75rem;
        margin: 2px;
        background-color: #2d3748;
        color: #a0aec0;
    }
    .network-badge.compatible {
        background-color: #276749;
        color: #9ae6b4;
    }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# Session State
# =============================================================================

def init_session_state():
    """Initialize session state variables."""
    defaults = {
        "current_step": 1,
        "layer_style_id": None,      # Selected Layer.ai style ID
        "layer_style_name": None,    # Style name for display
        "style_config": None,        # StyleConfig for prompt enhancement
        "asset_set": None,           # Generated assets
        "playable_html": None,       # Built playable HTML
        "playable_metadata": None,   # Playable metadata
        "workspace_info": None,      # Workspace credits info
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# =============================================================================
# Sidebar
# =============================================================================

def render_sidebar():
    """Render sidebar with status and workflow progress."""
    st.sidebar.title("🎮 Playable Studio")
    st.sidebar.caption("Layer.ai Playable Ad Generator")

    # API Status
    st.sidebar.markdown("---")
    st.sidebar.subheader("Status")

    key_status = validate_api_keys()
    all_keys_set = all(key_status.values())

    for key, is_set in key_status.items():
        icon = "✅" if is_set else "❌"
        name = key.replace("_", " ").title()
        st.sidebar.text(f"{icon} {name}")

    # Credits
    if all_keys_set:
        try:
            if st.session_state.workspace_info is None:
                client = LayerClientSync()
                st.session_state.workspace_info = client.get_workspace_info()
            info = st.session_state.workspace_info
            st.sidebar.metric("Credits", info.credits_available)
        except Exception:
            st.sidebar.text("Credits: Unable to fetch")

    # Workflow Progress
    st.sidebar.markdown("---")
    st.sidebar.subheader("Workflow")

    steps = [
        ("1. Select Style", 1),
        ("2. Generate Assets", 2),
        ("3. Export Playable", 3),
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
    st.sidebar.subheader("Ad Timing (3-15-5)")
    st.sidebar.markdown(f"""
    <span class="timing-badge hook-badge">Hook: {HOOK_DURATION_MS//1000}s</span>
    <span class="timing-badge gameplay-badge">Game: {GAMEPLAY_DURATION_MS//1000}s</span>
    <span class="timing-badge cta-badge">CTA: {CTA_DURATION_MS//1000}s</span>
    """, unsafe_allow_html=True)

    # Networks
    st.sidebar.markdown("---")
    st.sidebar.subheader("Export Networks")
    st.sidebar.caption("IronSource, Unity, AppLovin, Facebook, Google")


# =============================================================================
# Step 1: Select Style
# =============================================================================

def render_step_1():
    """Step 1: Select a Layer.ai style from the workspace."""
    st.markdown('<p class="step-header">Step 1: Select Layer.ai Style</p>', unsafe_allow_html=True)

    st.write("""
    Choose a trained style from your Layer.ai workspace. This style will be used
    to generate all playable ad assets with consistent visuals.
    """)

    st.info("""
    **Don't have a style yet?**
    Create one at [app.layer.ai](https://app.layer.ai) by uploading reference images
    and training a custom style. Only trained (COMPLETE) styles can be used here.
    """)

    # Fetch available styles
    st.subheader("🎨 Available Styles")

    available_styles = []
    fetch_error = None

    try:
        client = LayerClientSync()
        available_styles = client.list_styles(limit=50)
    except Exception as e:
        fetch_error = str(e)

    if fetch_error:
        st.error(f"Could not fetch styles: {fetch_error}")
        st.write("Check your API keys and try again.")

        # Manual fallback
        st.markdown("---")
        st.subheader("Manual Entry")
        manual_id = st.text_input(
            "Layer.ai Style ID",
            placeholder="Paste style ID from Layer.ai URL",
        )
        if manual_id and st.button("Use This Style", type="primary"):
            st.session_state.layer_style_id = manual_id
            st.session_state.layer_style_name = "Manual Style"
            st.session_state.style_config = StyleConfig(
                name="Manual Style",
                description="Manually entered style",
                style_keywords=[],
                negative_keywords=[],
            )
            st.session_state.current_step = 2
            st.rerun()
        return

    # Filter to COMPLETE styles only
    complete_styles = [s for s in available_styles if s.get("status") == "COMPLETE"]

    if not complete_styles:
        st.warning("""
        **No trained styles found in your workspace.**

        To create a style:
        1. Go to [app.layer.ai](https://app.layer.ai)
        2. Upload reference images for your game's visual style
        3. Train the style (wait for status: COMPLETE)
        4. Return here and refresh
        """)

        if st.button("🔄 Refresh Styles"):
            st.rerun()
        return

    st.success(f"Found {len(complete_styles)} trained styles")

    # Display styles as cards
    cols = st.columns(min(len(complete_styles), 3))

    for i, style in enumerate(complete_styles):
        with cols[i % 3]:
            style_id = style.get("id", "")
            style_name = style.get("name", "Unnamed Style")
            style_type = style.get("type", "Unknown")

            # Style card
            with st.container():
                st.markdown(f"### {style_name}")
                st.caption(f"Type: {style_type}")
                st.caption(f"ID: {style_id[:20]}...")

                if st.button(f"Select", key=f"select_{style_id}", type="secondary"):
                    st.session_state.layer_style_id = style_id
                    st.session_state.layer_style_name = style_name
                    st.session_state.style_config = StyleConfig(
                        name=style_name,
                        description=f"Layer.ai Style: {style_type}",
                        style_keywords=["game asset", "mobile game"],
                        negative_keywords=["blurry", "distorted"],
                    )
                    st.session_state.current_step = 2
                    st.rerun()

    # Manual fallback
    st.markdown("---")
    with st.expander("Or enter Style ID manually"):
        manual_id = st.text_input(
            "Style ID",
            placeholder="Paste style ID from Layer.ai URL",
            key="manual_style_input",
        )
        if manual_id:
            if st.button("Use Manual Style"):
                st.session_state.layer_style_id = manual_id
                st.session_state.layer_style_name = "Manual Style"
                st.session_state.style_config = StyleConfig(
                    name="Manual Style",
                    description="Manually entered style",
                    style_keywords=[],
                    negative_keywords=[],
                )
                st.session_state.current_step = 2
                st.rerun()


# =============================================================================
# Step 2: Generate Assets
# =============================================================================

def render_step_2():
    """Step 2: Generate playable ad assets."""
    st.markdown('<p class="step-header">Step 2: Generate Assets</p>', unsafe_allow_html=True)

    # Check requirements
    layer_style_id = st.session_state.layer_style_id
    layer_style_name = st.session_state.layer_style_name

    if not layer_style_id:
        st.error("No style selected. Please go back and select a style.")
        if st.button("← Back to Style Selection"):
            st.session_state.current_step = 1
            st.rerun()
        return

    # Show selected style
    st.success(f"**Style**: {layer_style_name} (`{layer_style_id[:20]}...`)")

    # Asset selection
    st.subheader("Select Assets to Generate")
    st.write("""
    Choose which assets to generate for your playable ad.
    Assets are organized by the 3-15-5 timing model.
    """)

    selected_types = []

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**🎣 Hook (3s)**")
        st.caption("Grab attention immediately")

        if st.checkbox("Character", value=True, key="asset_hook_char"):
            selected_types.append(AssetType.HOOK_CHARACTER)
        if st.checkbox("Item/Treasure", value=True, key="asset_hook_item"):
            selected_types.append(AssetType.HOOK_ITEM)

    with col2:
        st.markdown("**🎮 Gameplay (15s)**")
        st.caption("Core interactive loop")

        if st.checkbox("Background", value=True, key="asset_game_bg"):
            selected_types.append(AssetType.GAMEPLAY_BACKGROUND)
        if st.checkbox("Collectible", value=True, key="asset_game_collect"):
            selected_types.append(AssetType.GAMEPLAY_COLLECTIBLE)
        if st.checkbox("Element", value=False, key="asset_game_elem"):
            selected_types.append(AssetType.GAMEPLAY_ELEMENT)

    with col3:
        st.markdown("**📲 CTA (5s)**")
        st.caption("Drive installs")

        if st.checkbox("Button", value=True, key="asset_cta_btn"):
            selected_types.append(AssetType.CTA_BUTTON)
        if st.checkbox("Banner", value=False, key="asset_cta_banner"):
            selected_types.append(AssetType.CTA_BANNER)

    st.write(f"**Selected**: {len(selected_types)} assets")

    # Navigation
    st.markdown("---")
    col1, col2 = st.columns([1, 2])

    with col1:
        if st.button("← Back to Style Selection"):
            st.session_state.current_step = 1
            st.rerun()

    with col2:
        generate_disabled = len(selected_types) == 0

        if st.button(
            f"⚡ Generate {len(selected_types)} Assets",
            type="primary",
            disabled=generate_disabled
        ):
            with st.spinner("Generating assets with Layer.ai..."):
                try:
                    generator = AssetGenerator()
                    generator.set_style_id(layer_style_id)

                    if st.session_state.style_config:
                        generator.set_style(st.session_state.style_config)

                    progress = st.progress(0)
                    status = st.empty()

                    asset_set = AssetSet(style=st.session_state.style_config)

                    for i, asset_type in enumerate(selected_types):
                        preset = ASSET_PRESETS[asset_type]
                        status.text(f"Generating {preset.name}...")

                        asset = generator.generate_from_preset(asset_type)
                        asset_set.assets.append(asset)
                        asset_set.total_generation_time += asset.generation_time

                        progress.progress((i + 1) / len(selected_types))

                    asset_set.reference_image_id = generator._reference_image_id

                    st.session_state.asset_set = asset_set
                    st.session_state.current_step = 3
                    st.success(f"Generated {len(asset_set.assets)} assets!")
                    st.rerun()

                except LayerAPIError as e:
                    st.error(f"Layer.ai API Error: {str(e)}")
                except Exception as e:
                    st.error(f"Generation failed: {str(e)}")


# =============================================================================
# Step 3: Export Playable
# =============================================================================

def render_step_3():
    """Step 3: Assemble and export playable ad."""
    st.markdown('<p class="step-header">Step 3: Export Playable Ad</p>', unsafe_allow_html=True)

    asset_set = st.session_state.asset_set

    if not asset_set or not asset_set.assets:
        st.warning("No assets generated. Please go back and generate assets.")
        if st.button("← Back to Generate Assets"):
            st.session_state.current_step = 2
            st.rerun()
        return

    # Asset Preview
    st.subheader("Generated Assets")

    cols = st.columns(min(len(asset_set.assets), 4))
    for i, asset in enumerate(asset_set.assets):
        with cols[i % len(cols)]:
            if asset.image_url:
                st.image(asset.image_url, caption=asset.asset_type.value, width=120)

    st.caption(f"Total generation time: {asset_set.total_generation_time:.1f}s")

    # Playable Settings
    st.markdown("---")
    st.subheader("Playable Settings")

    col1, col2 = st.columns(2)

    with col1:
        game_name = st.text_input("Game Name", "My Awesome Game")
        hook_text = st.text_input("Hook Text", "Tap to Play!")
        cta_text = st.text_input("CTA Text", "Download FREE")

    with col2:
        store_url_ios = st.text_input(
            "App Store URL (iOS)",
            "https://apps.apple.com/app/id123456789",
        )
        store_url_android = st.text_input(
            "Play Store URL (Android)",
            "https://play.google.com/store/apps/details?id=com.example.game",
        )
        bg_color = st.color_picker("Background Color", "#1a1a2e")

    # Canvas Size
    st.markdown("---")
    st.subheader("Canvas Size")

    size_preset = st.radio(
        "Size Preset",
        options=["Portrait (320x480)", "Square (320x320)", "Landscape (480x320)", "Custom"],
        horizontal=True,
    )

    if size_preset == "Portrait (320x480)":
        width, height = 320, 480
    elif size_preset == "Square (320x320)":
        width, height = 320, 320
    elif size_preset == "Landscape (480x320)":
        width, height = 480, 320
    else:
        c1, c2 = st.columns(2)
        with c1:
            width = st.number_input("Width", 200, 1080, 320)
        with c2:
            height = st.number_input("Height", 200, 1920, 480)

    # Export Networks
    st.markdown("---")
    st.subheader("Export Networks")

    network_cols = st.columns(5)
    selected_networks = []

    network_options = [
        (AdNetwork.IRONSOURCE, "IronSource"),
        (AdNetwork.UNITY, "Unity Ads"),
        (AdNetwork.APPLOVIN, "AppLovin"),
        (AdNetwork.FACEBOOK, "Facebook"),
        (AdNetwork.GOOGLE, "Google Ads"),
    ]

    for i, (network, name) in enumerate(network_options):
        with network_cols[i]:
            if st.checkbox(name, value=(i < 3), key=f"export_net_{network.value}"):
                selected_networks.append(network)

    # Build Button
    st.markdown("---")
    col1, col2 = st.columns([1, 2])

    with col1:
        if st.button("← Back to Generate Assets"):
            st.session_state.current_step = 2
            st.rerun()

    with col2:
        if st.button("🎬 Build Playable", type="primary"):
            with st.spinner("Building playable ad..."):
                try:
                    assembler = PlayableAssembler()

                    # Prepare assets
                    prepared = assembler.prepare_asset_set(asset_set)

                    # Configure
                    config = PlayableConfig(
                        title=game_name,
                        width=int(width),
                        height=int(height),
                        background_color=bg_color,
                        store_url_ios=store_url_ios,
                        store_url_android=store_url_android,
                        hook_text=hook_text,
                        cta_text=cta_text,
                        game_name=game_name,
                    )

                    # Assemble
                    html, metadata = assembler.assemble(prepared, config)

                    st.session_state.playable_html = html
                    st.session_state.playable_metadata = metadata

                    st.success("Playable built successfully!")

                except Exception as e:
                    st.error(f"Build failed: {str(e)}")

    # Results
    if st.session_state.playable_html:
        metadata: PlayableMetadata = st.session_state.playable_metadata
        html = st.session_state.playable_html

        st.markdown("---")
        st.subheader("✅ Playable Ready")

        # Metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("File Size", metadata.file_size_formatted)
        with col2:
            st.metric("Assets", metadata.asset_count)
        with col3:
            st.metric("Duration", f"{metadata.duration_ms // 1000}s")
        with col4:
            st.metric("Networks", len(metadata.networks_compatible))

        # Compatible networks
        st.write("**Compatible Networks:**")
        network_html = ""
        for network_name in metadata.networks_compatible:
            network_html += f'<span class="network-badge compatible">{network_name}</span>'
        st.markdown(network_html, unsafe_allow_html=True)

        # Downloads
        st.markdown("---")
        st.subheader("Download")

        col1, col2 = st.columns(2)

        with col1:
            st.download_button(
                label="📥 Download index.html",
                data=html,
                file_name="index.html",
                mime="text/html",
            )

        with col2:
            if st.button("📦 Export for All Networks"):
                with tempfile.TemporaryDirectory() as tmpdir:
                    assembler = PlayableAssembler()
                    results = assembler.export_all_networks(
                        html,
                        Path(tmpdir),
                        selected_networks,
                    )

                    st.write("**Export Results:**")
                    for network, result in results.items():
                        if result.success:
                            st.success(f"✅ {network.value}: {result.file_size_formatted}")
                        else:
                            st.error(f"❌ {network.value}: {result.error_message}")

        # Preview
        st.markdown("---")
        if st.checkbox("Show Preview", key="preview_playable"):
            st.subheader("Preview")
            b64 = base64.b64encode(html.encode()).decode()
            st.markdown(f"""
            <iframe
                src="data:text/html;base64,{b64}"
                width="340"
                height="500"
                style="border: 2px solid #333; border-radius: 8px;"
            ></iframe>
            """, unsafe_allow_html=True)

        # Start Over
        st.markdown("---")
        if st.button("🔄 Start New Playable"):
            # Reset state
            st.session_state.current_step = 1
            st.session_state.layer_style_id = None
            st.session_state.layer_style_name = None
            st.session_state.asset_set = None
            st.session_state.playable_html = None
            st.session_state.playable_metadata = None
            st.rerun()


# =============================================================================
# Main Application
# =============================================================================

def main():
    """Main application entry point."""
    init_session_state()
    render_sidebar()

    st.title("Layer.ai Playable Studio")
    st.caption("Generate AI-powered playable ads for mobile games")

    # Check API keys
    keys = validate_api_keys()
    if not all(keys.values()):
        st.error("⚠️ Missing API keys. Please configure your environment.")
        st.markdown("""
        **Required keys:**
        - `LAYER_API_KEY` - Your Layer.ai API key
        - `LAYER_WORKSPACE_ID` - Your Layer.ai workspace ID
        - `ANTHROPIC_API_KEY` - Your Anthropic API key (for future features)

        **For Streamlit Cloud:** Add these in Settings → Secrets

        **For local development:** Create a `.env` file
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


if __name__ == "__main__":
    main()
