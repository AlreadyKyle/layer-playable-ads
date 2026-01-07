"""
Playable Assembler - HTML5 Playable Ad Builder

Creates MRAID 3.0 compliant playable ads using Phaser.js with:
- 3-second hook animation
- 15-second core gameplay loop
- 5-second CTA sequence

Exports as single index.html < 5MB with all assets embedded.
"""

import base64
import io
import json
from dataclasses import dataclass, field
from pathlib import Path
from string import Template
from typing import Optional

import httpx
import structlog
from PIL import Image

from src.forge.asset_forger import ForgedAsset
from src.utils.helpers import format_file_size, get_settings

logger = structlog.get_logger()


# =============================================================================
# Constants
# =============================================================================

# Playable ad timing (non-negotiable per spec)
HOOK_DURATION_MS = 3000
GAMEPLAY_DURATION_MS = 15000
CTA_DURATION_MS = 5000
TOTAL_DURATION_MS = HOOK_DURATION_MS + GAMEPLAY_DURATION_MS + CTA_DURATION_MS

# Asset constraints
MAX_IMAGE_DIMENSION = 512
SUPPORTED_FORMATS = {"png", "jpg", "jpeg", "webp", "gif"}


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
    original_url: Optional[str] = None
    category: str = "general"


@dataclass
class PlayableConfig:
    """Configuration for a playable ad."""

    title: str = "Playable Ad"
    width: int = 320
    height: int = 480
    background_color: str = "#000000"
    hook_text: str = "Play Now!"
    cta_text: str = "Install Free"
    analytics_id: Optional[str] = None


@dataclass
class PlayableMetadata:
    """Metadata about a generated playable."""

    title: str
    file_size_bytes: int
    asset_count: int
    duration_ms: int = TOTAL_DURATION_MS
    mraid_version: str = "3.0"
    phaser_version: str = "3.70.0"
    timing: dict = field(default_factory=lambda: {
        "hook_ms": HOOK_DURATION_MS,
        "gameplay_ms": GAMEPLAY_DURATION_MS,
        "cta_ms": CTA_DURATION_MS,
    })

    @property
    def file_size_formatted(self) -> str:
        return format_file_size(self.file_size_bytes)

    @property
    def is_valid_size(self) -> bool:
        settings = get_settings()
        max_bytes = int(settings.max_playable_size_mb * 1024 * 1024)
        return self.file_size_bytes <= max_bytes


# =============================================================================
# Playable Assembler
# =============================================================================


class PlayableAssembler:
    """
    Assembles playable ads from forged assets.

    Creates MRAID 3.0 compliant HTML5 playables using Phaser.js.
    All assets are embedded as base64 for single-file export.
    """

    def __init__(self):
        """Initialize PlayableAssembler."""
        self._logger = logger.bind(component="PlayableAssembler")
        self._template_path = Path(__file__).parent / "templates" / "phaser_base.html"
        self._prepared_assets: list[PlayableAsset] = []

    async def _download_image(self, url: str) -> bytes:
        """Download image from URL."""
        async with httpx.AsyncClient() as client:
            response = await client.get(url, follow_redirects=True)
            response.raise_for_status()
            return response.content

    def _download_image_sync(self, url: str) -> bytes:
        """Download image from URL (sync version)."""
        with httpx.Client() as client:
            response = client.get(url, follow_redirects=True)
            response.raise_for_status()
            return response.content

    def _process_image(
        self,
        image_data: bytes,
        max_dimension: Optional[int] = None,
    ) -> tuple[bytes, int, int, str]:
        """
        Process image: resize if needed and compress.

        Args:
            image_data: Raw image bytes
            max_dimension: Max width/height (default: from settings)

        Returns:
            Tuple of (processed_bytes, width, height, format)
        """
        settings = get_settings()
        max_dim = max_dimension or settings.max_image_dimension

        img = Image.open(io.BytesIO(image_data))

        # Convert RGBA to RGB if needed for JPEG output
        if img.mode in ("RGBA", "P"):
            # Keep as PNG for transparency
            output_format = "PNG"
        else:
            output_format = "JPEG"

        # Resize if exceeds max dimension
        if img.width > max_dim or img.height > max_dim:
            ratio = min(max_dim / img.width, max_dim / img.height)
            new_size = (int(img.width * ratio), int(img.height * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
            self._logger.debug(
                "Image resized",
                original=(img.width, img.height),
                new=new_size,
            )

        # Save to bytes
        buffer = io.BytesIO()
        if output_format == "JPEG":
            img = img.convert("RGB")
            img.save(buffer, format="JPEG", quality=85, optimize=True)
            mime_type = "image/jpeg"
        else:
            img.save(buffer, format="PNG", optimize=True)
            mime_type = "image/png"

        return buffer.getvalue(), img.width, img.height, mime_type

    def prepare_asset(
        self,
        forged_asset: ForgedAsset,
        key: str,
    ) -> PlayableAsset:
        """
        Prepare a forged asset for embedding.

        Downloads, processes, and converts to base64 data URI.

        Args:
            forged_asset: ForgedAsset from the forge module
            key: Phaser asset key to use

        Returns:
            PlayableAsset ready for embedding
        """
        self._logger.info(
            "Preparing asset",
            key=key,
            url=forged_asset.image_url[:50] if forged_asset.image_url else "none",
        )

        # Download image
        image_data = self._download_image_sync(forged_asset.image_url)

        # Process (resize, compress)
        processed, width, height, mime_type = self._process_image(image_data)

        # Convert to data URI
        b64 = base64.standard_b64encode(processed).decode("utf-8")
        data_uri = f"data:{mime_type};base64,{b64}"

        asset = PlayableAsset(
            key=key,
            data_uri=data_uri,
            width=width,
            height=height,
            original_url=forged_asset.image_url,
            category=forged_asset.category,
        )

        self._prepared_assets.append(asset)

        self._logger.info(
            "Asset prepared",
            key=key,
            dimensions=f"{width}x{height}",
            data_size=format_file_size(len(processed)),
        )

        return asset

    def prepare_assets_from_set(
        self,
        asset_set: dict[str, list[ForgedAsset]],
    ) -> list[PlayableAsset]:
        """
        Prepare all assets from a forge asset set.

        Args:
            asset_set: Dict from AssetForger.forge_playable_asset_set()

        Returns:
            List of prepared PlayableAssets
        """
        prepared = []

        for category, assets in asset_set.items():
            for i, forged in enumerate(assets):
                key = f"{category}_{i}"
                prepared.append(self.prepare_asset(forged, key))

        return prepared

    def _load_template(self) -> str:
        """Load the Phaser.js HTML template."""
        if not self._template_path.exists():
            raise FileNotFoundError(
                f"Template not found: {self._template_path}"
            )
        return self._template_path.read_text()

    def _generate_asset_loader_js(self, assets: list[PlayableAsset]) -> str:
        """Generate Phaser asset loader JavaScript."""
        lines = []
        for asset in assets:
            lines.append(
                f"        this.load.image('{asset.key}', '{asset.data_uri}');"
            )
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
            STORE_URL="",  # App store URL removed - placeholder for ad network
            HOOK_TEXT=config.hook_text,
            CTA_TEXT=config.cta_text,
            HOOK_DURATION=HOOK_DURATION_MS,
            GAMEPLAY_DURATION=GAMEPLAY_DURATION_MS,
            CTA_DURATION=CTA_DURATION_MS,
            ASSET_LOADER=asset_loader,
            ASSET_MANIFEST=asset_manifest,
            ANALYTICS_ID=config.analytics_id or "",
        )

        # Calculate metadata
        file_size = len(html.encode("utf-8"))
        metadata = PlayableMetadata(
            title=config.title,
            file_size_bytes=file_size,
            asset_count=len(assets),
        )

        self._logger.info(
            "Playable assembled",
            file_size=metadata.file_size_formatted,
            valid_size=metadata.is_valid_size,
        )

        if not metadata.is_valid_size:
            self._logger.warning(
                "Playable exceeds size limit!",
                size=metadata.file_size_formatted,
                limit=f"{get_settings().max_playable_size_mb}MB",
            )

        return html, metadata

    def export(
        self,
        html: str,
        output_path: Path,
    ) -> Path:
        """
        Export playable HTML to file.

        Args:
            html: Assembled HTML content
            output_path: Output file path

        Returns:
            Path to exported file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        output_path.write_text(html, encoding="utf-8")

        self._logger.info(
            "Playable exported",
            path=str(output_path),
            size=format_file_size(output_path.stat().st_size),
        )

        return output_path

    def validate_export(self, html: str) -> dict[str, bool]:
        """
        Validate an exported playable.

        Checks:
        - File size < 5MB
        - Contains MRAID detection
        - Contains required timing constants
        - Has valid HTML structure

        Args:
            html: HTML content to validate

        Returns:
            Dict of validation results
        """
        settings = get_settings()
        max_bytes = int(settings.max_playable_size_mb * 1024 * 1024)
        size_bytes = len(html.encode("utf-8"))

        results = {
            "size_valid": size_bytes <= max_bytes,
            "has_mraid": "mraid" in html.lower(),
            "has_phaser": "Phaser" in html,
            "has_hook_timing": str(HOOK_DURATION_MS) in html,
            "has_gameplay_timing": str(GAMEPLAY_DURATION_MS) in html,
            "has_cta_timing": str(CTA_DURATION_MS) in html,
            "has_doctype": "<!DOCTYPE html>" in html,
            "has_store_redirect": "openStoreUrl" in html or "store" in html.lower(),
        }

        all_valid = all(results.values())
        results["all_valid"] = all_valid

        if not all_valid:
            failed = [k for k, v in results.items() if not v and k != "all_valid"]
            self._logger.warning("Validation failed", failed_checks=failed)
        else:
            self._logger.info("Validation passed")

        return results

    def clear_prepared_assets(self) -> None:
        """Clear the list of prepared assets."""
        self._prepared_assets.clear()

    @property
    def prepared_asset_count(self) -> int:
        """Number of prepared assets."""
        return len(self._prepared_assets)


__all__ = [
    "PlayableAssembler",
    "PlayableAsset",
    "PlayableConfig",
    "PlayableMetadata",
    "HOOK_DURATION_MS",
    "GAMEPLAY_DURATION_MS",
    "CTA_DURATION_MS",
    "TOTAL_DURATION_MS",
]
