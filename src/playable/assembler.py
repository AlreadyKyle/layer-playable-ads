"""
Playable Ad Assembler

Creates MRAID 3.0 compliant HTML5 playable ads with multi-network export support.
Exports optimized for: IronSource, Unity Ads, AppLovin, Facebook, Google Ads, and more.

MVP v1.0 - Industry-standard playable ad generation.
"""

import base64
import io
import json
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from string import Template
from typing import Optional
from enum import Enum

import httpx
import structlog
from PIL import Image

from src.forge.asset_forger import GeneratedAsset, AssetSet, AssetCategory
from src.utils.helpers import format_file_size, get_settings

logger = structlog.get_logger()


# =============================================================================
# Constants - Industry Standard Timing
# =============================================================================

# Playable ad timing (UA methodology - non-negotiable)
HOOK_DURATION_MS = 3000       # 3-second hook
GAMEPLAY_DURATION_MS = 15000  # 15-second gameplay
CTA_DURATION_MS = 5000        # 5-second CTA
TOTAL_DURATION_MS = HOOK_DURATION_MS + GAMEPLAY_DURATION_MS + CTA_DURATION_MS

# Asset constraints
MAX_IMAGE_DIMENSION = 512
SUPPORTED_FORMATS = {"png", "jpg", "jpeg", "webp", "gif"}


# =============================================================================
# Ad Network Specifications
# =============================================================================


class AdNetwork(str, Enum):
    """Supported ad networks for export."""
    IRONSOURCE = "ironsource"
    UNITY = "unity"
    APPLOVIN = "applovin"
    FACEBOOK = "facebook"
    GOOGLE = "google"
    MINTEGRAL = "mintegral"
    VUNGLE = "vungle"
    TIKTOK = "tiktok"
    GENERIC = "generic"  # Universal format


@dataclass
class NetworkSpec:
    """Specification for an ad network's playable requirements."""
    network: AdNetwork
    name: str
    max_size_mb: float
    format: str  # "html" or "zip"
    main_file_name: str
    requires_mraid: bool = True
    notes: str = ""


# Network specifications based on industry standards
NETWORK_SPECS: dict[AdNetwork, NetworkSpec] = {
    AdNetwork.IRONSOURCE: NetworkSpec(
        network=AdNetwork.IRONSOURCE,
        name="IronSource",
        max_size_mb=5.0,
        format="html",
        main_file_name="index.html",
        requires_mraid=True,
        notes="Single inline HTML file required",
    ),
    AdNetwork.UNITY: NetworkSpec(
        network=AdNetwork.UNITY,
        name="Unity Ads",
        max_size_mb=5.0,
        format="html",
        main_file_name="index.html",
        requires_mraid=True,
        notes="Must include App Store/Play Store URLs",
    ),
    AdNetwork.APPLOVIN: NetworkSpec(
        network=AdNetwork.APPLOVIN,
        name="AppLovin",
        max_size_mb=5.0,
        format="html",
        main_file_name="index.html",
        requires_mraid=True,
        notes="External requests require pre-approval",
    ),
    AdNetwork.FACEBOOK: NetworkSpec(
        network=AdNetwork.FACEBOOK,
        name="Facebook",
        max_size_mb=2.0,  # 2MB for HTML, 5MB for zip
        format="html",
        main_file_name="index.html",
        requires_mraid=False,
        notes="Stricter size limit for HTML format",
    ),
    AdNetwork.GOOGLE: NetworkSpec(
        network=AdNetwork.GOOGLE,
        name="Google Ads",
        max_size_mb=5.0,
        format="zip",
        main_file_name="index.html",
        requires_mraid=False,
        notes="Must be zipped before upload",
    ),
    AdNetwork.MINTEGRAL: NetworkSpec(
        network=AdNetwork.MINTEGRAL,
        name="Mintegral",
        max_size_mb=5.0,
        format="html",
        main_file_name="index.html",
        requires_mraid=True,
    ),
    AdNetwork.VUNGLE: NetworkSpec(
        network=AdNetwork.VUNGLE,
        name="Vungle",
        max_size_mb=5.0,
        format="html",
        main_file_name="ad.html",  # Vungle uses ad.html
        requires_mraid=True,
        notes="Main file must be named ad.html",
    ),
    AdNetwork.TIKTOK: NetworkSpec(
        network=AdNetwork.TIKTOK,
        name="TikTok",
        max_size_mb=5.0,
        format="zip",
        main_file_name="index.html",
        requires_mraid=True,
        notes="Requires config.json with orientation/language",
    ),
    AdNetwork.GENERIC: NetworkSpec(
        network=AdNetwork.GENERIC,
        name="Generic/Universal",
        max_size_mb=5.0,
        format="html",
        main_file_name="index.html",
        requires_mraid=True,
        notes="Works with most networks",
    ),
}


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class PlayableAsset:
    """An asset prepared for embedding in a playable."""
    key: str  # Phaser asset key
    data_uri: str  # Base64 data URI
    width: int
    height: int
    category: str = "general"
    original_url: Optional[str] = None


@dataclass
class PlayableConfig:
    """Configuration for a playable ad."""
    title: str = "Playable Ad"
    width: int = 320
    height: int = 480
    background_color: str = "#1a1a2e"
    store_url_ios: str = ""
    store_url_android: str = ""
    hook_text: str = "Tap to Play!"
    cta_text: str = "Download FREE"
    game_name: str = "My Game"

    @property
    def store_url(self) -> str:
        """Get primary store URL (iOS preferred for demos)."""
        return self.store_url_ios or self.store_url_android or "https://apps.apple.com"


@dataclass
class PlayableMetadata:
    """Metadata about a generated playable."""
    title: str
    file_size_bytes: int
    asset_count: int
    networks_compatible: list[str] = field(default_factory=list)
    duration_ms: int = TOTAL_DURATION_MS
    mraid_version: str = "3.0"
    timing: dict = field(default_factory=lambda: {
        "hook_ms": HOOK_DURATION_MS,
        "gameplay_ms": GAMEPLAY_DURATION_MS,
        "cta_ms": CTA_DURATION_MS,
    })

    @property
    def file_size_formatted(self) -> str:
        return format_file_size(self.file_size_bytes)

    @property
    def file_size_mb(self) -> float:
        return self.file_size_bytes / (1024 * 1024)


@dataclass
class ExportResult:
    """Result of exporting a playable ad."""
    network: AdNetwork
    success: bool
    file_path: Optional[Path] = None
    file_size_bytes: int = 0
    error_message: Optional[str] = None

    @property
    def file_size_formatted(self) -> str:
        return format_file_size(self.file_size_bytes)


# =============================================================================
# Playable Assembler
# =============================================================================


class PlayableAssembler:
    """
    Assembles playable ads from generated assets.

    Creates MRAID 3.0 compliant HTML5 playables with:
    - 3-15-5 timing model (Hook-Gameplay-CTA)
    - Embedded base64 assets for single-file export
    - Multi-network export support
    - Phaser.js for game logic
    """

    def __init__(self):
        self._logger = logger.bind(component="PlayableAssembler")
        self._template_path = Path(__file__).parent / "templates" / "phaser_base.html"
        self._prepared_assets: list[PlayableAsset] = []

    def _download_image_sync(self, url: str) -> bytes:
        """Download image from URL."""
        with httpx.Client(timeout=30.0) as client:
            response = client.get(url, follow_redirects=True)
            response.raise_for_status()
            return response.content

    def _process_image(
        self,
        image_data: bytes,
        max_dimension: Optional[int] = None,
    ) -> tuple[bytes, int, int, str]:
        """Process image: resize if needed and compress."""
        settings = get_settings()
        max_dim = max_dimension or settings.max_image_dimension

        img = Image.open(io.BytesIO(image_data))

        # Determine output format
        if img.mode in ("RGBA", "P"):
            output_format = "PNG"
            mime_type = "image/png"
        else:
            output_format = "JPEG"
            mime_type = "image/jpeg"

        # Resize if exceeds max dimension
        if img.width > max_dim or img.height > max_dim:
            ratio = min(max_dim / img.width, max_dim / img.height)
            new_size = (int(img.width * ratio), int(img.height * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)

        # Save to bytes with compression
        buffer = io.BytesIO()
        if output_format == "JPEG":
            img = img.convert("RGB")
            img.save(buffer, format="JPEG", quality=80, optimize=True)
        else:
            img.save(buffer, format="PNG", optimize=True)

        return buffer.getvalue(), img.width, img.height, mime_type

    def prepare_asset(
        self,
        asset: GeneratedAsset,
        key: Optional[str] = None,
    ) -> PlayableAsset:
        """Prepare a generated asset for embedding."""
        asset_key = key or asset.key

        self._logger.info("Preparing asset", key=asset_key)

        # Download image
        image_data = self._download_image_sync(asset.image_url)

        # Process (resize, compress)
        processed, width, height, mime_type = self._process_image(image_data)

        # Convert to data URI
        b64 = base64.standard_b64encode(processed).decode("utf-8")
        data_uri = f"data:{mime_type};base64,{b64}"

        playable_asset = PlayableAsset(
            key=asset_key,
            data_uri=data_uri,
            width=width,
            height=height,
            category=asset.category.value,
            original_url=asset.image_url,
        )

        self._prepared_assets.append(playable_asset)

        self._logger.info(
            "Asset prepared",
            key=asset_key,
            dimensions=f"{width}x{height}",
            size=format_file_size(len(processed)),
        )

        return playable_asset

    def prepare_asset_set(self, asset_set: AssetSet) -> list[PlayableAsset]:
        """Prepare all assets from an asset set."""
        prepared = []

        for i, asset in enumerate(asset_set.assets):
            key = f"{asset.category.value}_{i}"
            prepared.append(self.prepare_asset(asset, key))

        return prepared

    def _load_template(self) -> str:
        """Load the Phaser.js HTML template."""
        if not self._template_path.exists():
            raise FileNotFoundError(f"Template not found: {self._template_path}")
        return self._template_path.read_text()

    def _generate_asset_loader_js(self, assets: list[PlayableAsset]) -> str:
        """Generate Phaser asset loader JavaScript."""
        lines = []
        for asset in assets:
            lines.append(f"        this.load.image('{asset.key}', '{asset.data_uri}');")
        return "\n".join(lines)

    def _generate_asset_manifest(self, assets: list[PlayableAsset]) -> str:
        """Generate asset manifest as JSON."""
        manifest = {
            asset.key: {
                "width": asset.width,
                "height": asset.height,
                "category": asset.category,
            }
            for asset in assets
        }
        return json.dumps(manifest, indent=2)

    def assemble(
        self,
        assets: list[PlayableAsset],
        config: PlayableConfig,
    ) -> tuple[str, PlayableMetadata]:
        """
        Assemble a complete playable ad.

        Args:
            assets: List of prepared PlayableAssets
            config: PlayableConfig with settings

        Returns:
            Tuple of (html_content, metadata)
        """
        self._logger.info(
            "Assembling playable",
            title=config.title,
            asset_count=len(assets),
        )

        # Load template
        template_str = self._load_template()
        template = Template(template_str)

        # Generate JavaScript for asset loading
        asset_loader = self._generate_asset_loader_js(assets)
        asset_manifest = self._generate_asset_manifest(assets)

        # Substitute template variables
        html = template.safe_substitute(
            TITLE=config.title,
            WIDTH=config.width,
            HEIGHT=config.height,
            BACKGROUND_COLOR=config.background_color,
            STORE_URL=config.store_url,
            HOOK_TEXT=config.hook_text,
            CTA_TEXT=config.cta_text,
            HOOK_DURATION=HOOK_DURATION_MS,
            GAMEPLAY_DURATION=GAMEPLAY_DURATION_MS,
            CTA_DURATION=CTA_DURATION_MS,
            ASSET_LOADER=asset_loader,
            ASSET_MANIFEST=asset_manifest,
            ANALYTICS_ID="",
        )

        # Check compatibility with networks
        file_size = len(html.encode("utf-8"))
        compatible_networks = []

        for network, spec in NETWORK_SPECS.items():
            max_bytes = int(spec.max_size_mb * 1024 * 1024)
            if file_size <= max_bytes:
                compatible_networks.append(spec.name)

        metadata = PlayableMetadata(
            title=config.title,
            file_size_bytes=file_size,
            asset_count=len(assets),
            networks_compatible=compatible_networks,
        )

        self._logger.info(
            "Playable assembled",
            file_size=metadata.file_size_formatted,
            compatible_networks=len(compatible_networks),
        )

        return html, metadata

    def export_for_network(
        self,
        html: str,
        network: AdNetwork,
        output_dir: Path,
        config: Optional[PlayableConfig] = None,
    ) -> ExportResult:
        """
        Export playable for a specific ad network.

        Args:
            html: Assembled HTML content
            network: Target ad network
            output_dir: Directory for output files
            config: Optional config for network-specific settings

        Returns:
            ExportResult with success/failure info
        """
        spec = NETWORK_SPECS.get(network, NETWORK_SPECS[AdNetwork.GENERIC])

        self._logger.info(
            "Exporting for network",
            network=spec.name,
            format=spec.format,
        )

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            if spec.format == "html":
                # Single HTML file
                file_path = output_dir / spec.main_file_name
                file_path.write_text(html, encoding="utf-8")
                file_size = file_path.stat().st_size

            elif spec.format == "zip":
                # Create zip with HTML and any required files
                zip_path = output_dir / f"{network.value}_playable.zip"

                with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                    zf.writestr(spec.main_file_name, html)

                    # Add network-specific files
                    if network == AdNetwork.TIKTOK:
                        # TikTok requires config.json
                        tiktok_config = json.dumps({
                            "playable_orientation": "portrait",
                            "playable_languages": ["en"],
                        })
                        zf.writestr("config.json", tiktok_config)

                file_path = zip_path
                file_size = zip_path.stat().st_size

            else:
                raise ValueError(f"Unknown format: {spec.format}")

            # Validate size
            max_bytes = int(spec.max_size_mb * 1024 * 1024)
            if file_size > max_bytes:
                return ExportResult(
                    network=network,
                    success=False,
                    file_path=file_path,
                    file_size_bytes=file_size,
                    error_message=f"File size {format_file_size(file_size)} exceeds {spec.max_size_mb}MB limit",
                )

            self._logger.info(
                "Export successful",
                network=spec.name,
                file_size=format_file_size(file_size),
            )

            return ExportResult(
                network=network,
                success=True,
                file_path=file_path,
                file_size_bytes=file_size,
            )

        except Exception as e:
            self._logger.error("Export failed", network=spec.name, error=str(e))
            return ExportResult(
                network=network,
                success=False,
                error_message=str(e),
            )

    def export_all_networks(
        self,
        html: str,
        output_dir: Path,
        networks: Optional[list[AdNetwork]] = None,
    ) -> dict[AdNetwork, ExportResult]:
        """
        Export playable for multiple ad networks.

        Args:
            html: Assembled HTML content
            output_dir: Base directory for output
            networks: List of networks (default: all)

        Returns:
            Dict mapping network to ExportResult
        """
        if networks is None:
            # Default to most common networks
            networks = [
                AdNetwork.IRONSOURCE,
                AdNetwork.UNITY,
                AdNetwork.APPLOVIN,
                AdNetwork.FACEBOOK,
                AdNetwork.GOOGLE,
            ]

        results = {}
        for network in networks:
            network_dir = output_dir / network.value
            results[network] = self.export_for_network(html, network, network_dir)

        return results

    def validate_for_network(
        self,
        html: str,
        network: AdNetwork,
    ) -> dict[str, bool]:
        """
        Validate a playable for a specific network.

        Returns:
            Dict of validation checks and their results
        """
        spec = NETWORK_SPECS.get(network, NETWORK_SPECS[AdNetwork.GENERIC])
        file_size = len(html.encode("utf-8"))
        max_bytes = int(spec.max_size_mb * 1024 * 1024)

        results = {
            "size_valid": file_size <= max_bytes,
            "has_doctype": "<!DOCTYPE html>" in html,
            "has_viewport": "viewport" in html.lower(),
            "has_hook_timing": str(HOOK_DURATION_MS) in html,
            "has_gameplay_timing": str(GAMEPLAY_DURATION_MS) in html,
            "has_cta_timing": str(CTA_DURATION_MS) in html,
        }

        if spec.requires_mraid:
            results["has_mraid"] = "mraid" in html.lower()

        results["has_store_redirect"] = "openStoreUrl" in html or "store" in html.lower()
        results["all_valid"] = all(results.values())

        return results

    def clear_prepared_assets(self) -> None:
        """Clear the list of prepared assets."""
        self._prepared_assets.clear()

    @property
    def prepared_asset_count(self) -> int:
        """Number of prepared assets."""
        return len(self._prepared_assets)


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "PlayableAssembler",
    "PlayableAsset",
    "PlayableConfig",
    "PlayableMetadata",
    "ExportResult",
    "AdNetwork",
    "NetworkSpec",
    "NETWORK_SPECS",
    "HOOK_DURATION_MS",
    "GAMEPLAY_DURATION_MS",
    "CTA_DURATION_MS",
    "TOTAL_DURATION_MS",
]
