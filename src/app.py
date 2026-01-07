"""
Layer.ai Playable Studio - Streamlit Application

MVP v1.0 - Simplified playable ad generation workflow.

3-Step Process:
1. Configure Style - Set up visual style for asset generation
2. Generate Assets - Create game assets using Layer.ai
3. Export Playable - Build and download for ad networks
"""

import base64
from pathlib import Path
from typing import Optional
import tempfile

import streamlit as st

from src.layer_client import (
    LayerClientSync,
    StyleConfig,
    WorkspaceInfo,
    LayerAPIError,
)
from src.forge.asset_forger import (
    AssetGenerator,
    AssetType,
    AssetCategory,
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
from src.utils.helpers import get_settings, validate_api_keys, format_file_size


# =============================================================================
# Page Configuration
# =============================================================================

st.set_page_config(
    page_title="Layer.ai Playable Studio",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Clean, modern CSS
st.markdown("""
<style>
    .stApp {
        background-color: #0e1117;
    }
    .step-header {
        font-size: 1.4rem;
        font-weight: 600;
        color: #fafafa;
        margin-bottom: 1rem;
        padding: 0.5rem 0;
        border-bottom: 2px solid #ff4b4b;
    }
    .info-card {
        background-color: #1e2128;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
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
        "style_config": None,
        "asset_set": None,
        "playable_html": None,
        "playable_metadata": None,
        "workspace_info": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_session_state()


# =============================================================================
# Sidebar
# =============================================================================

def render_sidebar():
    """Render sidebar with status and info."""
    st.sidebar.title("🎮 Playable Studio")
    st.sidebar.caption("Layer.ai + AI-Powered Playable Ads")

    # API Status
    st.sidebar.markdown("---")
    st.sidebar.subheader("Status")

    key_status = validate_api_keys()
    all_keys_set = all(key_status.values())

    for key, is_set in key_status.items():
        icon = "✅" if is_set else "❌"
        name = key.replace("_", " ").title()
        st.sidebar.text(f"{icon} {name}")

    # Credits display
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
        ("1. Style Config", 1),
        ("2. Generate Assets", 2),
        ("3. Export", 3),
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
    st.sidebar.subheader("Ad Timing (UA Model)")
    st.sidebar.markdown(f"""
    <span class="timing-badge hook-badge">Hook: {HOOK_DURATION_MS//1000}s</span>
    <span class="timing-badge gameplay-badge">Game: {GAMEPLAY_DURATION_MS//1000}s</span>
    <span class="timing-badge cta-badge">CTA: {CTA_DURATION_MS//1000}s</span>
    """, unsafe_allow_html=True)

    # Supported Networks
    st.sidebar.markdown("---")
    st.sidebar.subheader("Export Networks")
    networks = ["IronSource", "Unity", "AppLovin", "Facebook", "Google"]
    st.sidebar.caption(", ".join(networks))


# =============================================================================
# Step 1: Style Configuration
# =============================================================================

def render_step_1():
    """Step 1: Configure visual style."""
    st.markdown('<p class="step-header">Step 1: Configure Style</p>', unsafe_allow_html=True)

    st.write("""
    Define the visual style for your playable ad assets. This ensures all generated
    assets have a consistent look and feel.
    """)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Style Settings")

        style_name = st.text_input(
            "Style Name",
            value="Casual Game Style",
            help="A name to identify this style"
        )

        game_genre = st.selectbox(
            "Game Genre",
            options=[
                "Casual/Puzzle",
                "Match-3",
                "Idle/Clicker",
                "Action/Arcade",
                "Strategy",
                "RPG/Adventure",
                "Sports",
                "Other"
            ],
            help="Select the genre that best matches your game"
        )

        art_style = st.selectbox(
            "Art Style",
            options=[
                "Cartoon/Stylized",
                "2D Flat",
                "2.5D Isometric",
                "Pixel Art",
                "Realistic",
                "Minimalist",
            ],
            help="Visual art direction for assets"
        )

    with col2:
        st.subheader("Style Keywords")

        # Pre-populate based on selections
        default_keywords = {
            "Casual/Puzzle": ["vibrant colors", "friendly", "clean design"],
            "Match-3": ["colorful", "glossy", "candy-like"],
            "Idle/Clicker": ["satisfying", "progress indicators", "numbers"],
            "Action/Arcade": ["dynamic", "energetic", "bold"],
            "Strategy": ["detailed", "tactical", "icons"],
            "RPG/Adventure": ["fantasy", "epic", "atmospheric"],
            "Sports": ["athletic", "dynamic", "realistic"],
            "Other": ["game asset", "mobile game"],
        }

        style_keywords = st.text_area(
            "Style Keywords (comma-separated)",
            value=", ".join(default_keywords.get(game_genre, [])),
            help="Keywords to guide asset generation"
        )

        negative_keywords = st.text_area(
            "Avoid Keywords (comma-separated)",
            value="realistic, photographic, dark, gloomy, violent",
            help="Keywords to avoid in generation"
        )

    st.markdown("---")

    # Preview style config
    st.subheader("Style Preview")

    keywords_list = [k.strip() for k in style_keywords.split(",") if k.strip()]
    negative_list = [k.strip() for k in negative_keywords.split(",") if k.strip()]

    preview_config = {
        "name": style_name,
        "genre": game_genre,
        "art_style": art_style,
        "keywords": keywords_list,
        "negative": negative_list,
    }

    col1, col2 = st.columns(2)
    with col1:
        st.json(preview_config)

    with col2:
        st.info(f"""
        **Prompt Prefix**: {', '.join(keywords_list[:5])}...

        **Will Avoid**: {', '.join(negative_list[:3])}...
        """)

    # Navigation
    st.markdown("---")

    if st.button("Continue to Asset Generation →", type="primary"):
        # Create style config
        style = StyleConfig(
            name=style_name,
            description=f"{game_genre} - {art_style}",
            style_keywords=keywords_list,
            negative_keywords=negative_list,
        )

        st.session_state.style_config = style
        st.session_state.current_step = 2
        st.rerun()


# =============================================================================
# Step 2: Generate Assets
# =============================================================================

def render_step_2():
    """Step 2: Generate game assets."""
    st.markdown('<p class="step-header">Step 2: Generate Assets</p>', unsafe_allow_html=True)

    style: StyleConfig = st.session_state.style_config

    if not style:
        st.warning("Please configure a style first.")
        if st.button("← Back to Style Config"):
            st.session_state.current_step = 1
            st.rerun()
        return

    st.info(f"**Style**: {style.name} | Keywords: {', '.join(style.style_keywords[:3])}...")

    # Asset selection
    st.subheader("Select Assets to Generate")

    st.write("""
    Choose which assets to generate for your playable ad.
    More assets = richer experience but longer generation time.
    """)

    col1, col2, col3 = st.columns(3)

    selected_types = []

    with col1:
        st.markdown("**🎣 Hook (3s)**")
        st.caption("Grab attention")

        if st.checkbox("Character", value=True, key="hook_char"):
            selected_types.append(AssetType.HOOK_CHARACTER)
        if st.checkbox("Item/Treasure", value=True, key="hook_item"):
            selected_types.append(AssetType.HOOK_ITEM)

    with col2:
        st.markdown("**🎮 Gameplay (15s)**")
        st.caption("Core loop")

        if st.checkbox("Background", value=True, key="game_bg"):
            selected_types.append(AssetType.GAMEPLAY_BACKGROUND)
        if st.checkbox("Collectible", value=True, key="game_collect"):
            selected_types.append(AssetType.GAMEPLAY_COLLECTIBLE)
        if st.checkbox("Element", value=False, key="game_elem"):
            selected_types.append(AssetType.GAMEPLAY_ELEMENT)

    with col3:
        st.markdown("**📲 CTA (5s)**")
        st.caption("Convert users")

        if st.checkbox("Button", value=True, key="cta_btn"):
            selected_types.append(AssetType.CTA_BUTTON)
        if st.checkbox("Banner", value=False, key="cta_banner"):
            selected_types.append(AssetType.CTA_BANNER)

    st.write(f"**Selected**: {len(selected_types)} assets")

    # Quick presets
    st.markdown("---")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("Minimal (4 assets)"):
            st.session_state.hook_char = True
            st.session_state.hook_item = False
            st.session_state.game_bg = True
            st.session_state.game_collect = True
            st.session_state.game_elem = False
            st.session_state.cta_btn = True
            st.session_state.cta_banner = False
            st.rerun()

    with col2:
        if st.button("Standard (6 assets)"):
            st.session_state.hook_char = True
            st.session_state.hook_item = True
            st.session_state.game_bg = True
            st.session_state.game_collect = True
            st.session_state.game_elem = False
            st.session_state.cta_btn = True
            st.session_state.cta_banner = True
            st.rerun()

    with col3:
        if st.button("Full (7 assets)"):
            st.session_state.hook_char = True
            st.session_state.hook_item = True
            st.session_state.game_bg = True
            st.session_state.game_collect = True
            st.session_state.game_elem = True
            st.session_state.cta_btn = True
            st.session_state.cta_banner = True
            st.rerun()

    # Navigation
    st.markdown("---")
    col1, col2 = st.columns([1, 2])

    with col1:
        if st.button("← Back"):
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
                    generator.set_style(style)

                    progress = st.progress(0)
                    status = st.empty()

                    asset_set = AssetSet(style=style)

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
    """Step 3: Assemble and export playable."""
    st.markdown('<p class="step-header">Step 3: Export Playable Ad</p>', unsafe_allow_html=True)

    asset_set: AssetSet = st.session_state.asset_set

    if not asset_set or not asset_set.assets:
        st.warning("No assets generated. Please go back and generate assets.")
        if st.button("← Back to Generate"):
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

    # Playable Configuration
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

    # Canvas size
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
        col1, col2 = st.columns(2)
        with col1:
            width = st.number_input("Width", 200, 1080, 320)
        with col2:
            height = st.number_input("Height", 200, 1920, 480)

    # Export Networks
    st.markdown("---")
    st.subheader("Export Networks")

    st.write("Select which ad networks to export for:")

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
            if st.checkbox(name, value=(i < 3), key=f"net_{network.value}"):
                selected_networks.append(network)

    # Show network specs
    with st.expander("Network Specifications"):
        for network in selected_networks:
            spec = NETWORK_SPECS[network]
            st.markdown(f"""
            **{spec.name}**
            - Max Size: {spec.max_size_mb} MB
            - Format: {spec.format.upper()}
            - MRAID: {"Required" if spec.requires_mraid else "Optional"}
            - Notes: {spec.notes or "None"}
            """)

    # Build and Export
    st.markdown("---")
    col1, col2 = st.columns([1, 2])

    with col1:
        if st.button("← Back"):
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

    # Show results
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
            # Single HTML download
            st.download_button(
                label="📥 Download index.html",
                data=html,
                file_name="index.html",
                mime="text/html",
            )

        with col2:
            # Multi-network export
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
        if st.checkbox("Show Preview", key="show_preview"):
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

        # Validation
        with st.expander("Validation Details"):
            assembler = PlayableAssembler()
            for network in selected_networks[:3]:
                validation = assembler.validate_for_network(html, network)
                st.write(f"**{network.value}**")

                for check, passed in validation.items():
                    icon = "✅" if passed else "❌"
                    st.text(f"  {icon} {check}")


# =============================================================================
# Main Application
# =============================================================================

def main():
    """Main application entry point."""
    render_sidebar()

    st.title("Layer.ai Playable Studio")
    st.caption("Generate AI-powered playable ads for mobile games")

    # Check API keys
    keys = validate_api_keys()
    if not all(keys.values()):
        st.error("⚠️ Missing API keys. Please configure your .env file.")
        st.markdown("""
        **Required keys:**
        - `LAYER_API_KEY` - Your Layer.ai API key
        - `LAYER_WORKSPACE_ID` - Your Layer.ai workspace ID
        - `ANTHROPIC_API_KEY` - Your Anthropic API key

        Copy `.env.example` to `.env` and fill in your values.
        """)

        with st.expander("Setup Instructions"):
            st.code("""
# 1. Copy the example file
cp .env.example .env

# 2. Edit .env with your keys
LAYER_API_KEY=your_layer_key_here
LAYER_WORKSPACE_ID=your_workspace_id_here
ANTHROPIC_API_KEY=your_anthropic_key_here

# 3. Restart the app
streamlit run src/app.py
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
