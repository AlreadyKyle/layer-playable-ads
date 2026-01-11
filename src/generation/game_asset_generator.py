"""
Game Asset Generator - Generates game-specific assets using Layer.ai.

This module takes game analysis results and generates assets
tailored to the specific game's visual style and template requirements.
"""

import base64
from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path
from typing import Optional

import httpx
from PIL import Image

from src.layer_client import LayerClientSync, GeneratedImage, LayerAPIError
from src.analysis.game_analyzer import GameAnalysis, AssetNeed, VisualStyle
from src.templates.registry import MechanicType, TEMPLATE_REGISTRY, AssetRequirement


@dataclass
class GeneratedAsset:
    """A generated asset with metadata."""

    key: str  # Asset key (e.g., "tile_1", "player")
    prompt: str  # Prompt used for generation
    image_url: Optional[str]  # Layer.ai URL
    image_data: Optional[bytes]  # Downloaded image data
    base64_data: Optional[str]  # Base64 encoded for embedding
    generation_time: float  # Time to generate in seconds
    width: int = 0
    height: int = 0
    error: Optional[str] = None

    @property
    def is_valid(self) -> bool:
        """Check if asset was successfully generated."""
        return self.image_data is not None and self.error is None


@dataclass
class GeneratedAssetSet:
    """Complete set of generated assets for a game."""

    game_name: str
    mechanic_type: MechanicType
    assets: dict[str, GeneratedAsset] = field(default_factory=dict)
    total_generation_time: float = 0.0
    style_id: str = ""

    def get_asset(self, key: str) -> Optional[GeneratedAsset]:
        """Get asset by key."""
        return self.assets.get(key)

    def get_asset_manifest(self) -> dict[str, str]:
        """Get manifest of asset keys to base64 data URIs."""
        manifest = {}
        for key, asset in self.assets.items():
            if asset.is_valid and asset.base64_data:
                manifest[key] = asset.base64_data
        return manifest

    @property
    def all_valid(self) -> bool:
        """Check if all assets are valid."""
        return all(a.is_valid for a in self.assets.values())

    @property
    def valid_count(self) -> int:
        """Count of valid assets."""
        return sum(1 for a in self.assets.values() if a.is_valid)


class GameAssetGenerator:
    """Generates game-specific assets using Layer.ai."""

    MAX_IMAGE_DIMENSION = 512
    JPEG_QUALITY = 85

    def __init__(
        self,
        layer_client: Optional[LayerClientSync] = None,
        max_dimension: int = 512,
    ):
        """Initialize the asset generator.

        Args:
            layer_client: Layer.ai client. Created if not provided.
            max_dimension: Max image dimension for optimization.
        """
        self.client = layer_client or LayerClientSync()
        self.max_dimension = max_dimension

    def generate_for_game(
        self,
        analysis: GameAnalysis,
        style_id: str,
        progress_callback: Optional[callable] = None,
    ) -> GeneratedAssetSet:
        """Generate all assets needed for a game's playable ad.

        Args:
            analysis: GameAnalysis from game analyzer
            style_id: Layer.ai style ID to use
            progress_callback: Optional callback(current, total, asset_name)

        Returns:
            GeneratedAssetSet with all generated assets
        """
        # Get template requirements
        template = TEMPLATE_REGISTRY.get(analysis.mechanic_type)
        if not template:
            # Fall back to tapper if unknown
            template = TEMPLATE_REGISTRY[MechanicType.TAPPER]

        # Merge template requirements with game-specific needs
        asset_requirements = self._merge_requirements(
            template.required_assets,
            analysis.assets_needed,
            analysis.visual_style,
        )

        # Initialize result set
        result = GeneratedAssetSet(
            game_name=analysis.game_name,
            mechanic_type=analysis.mechanic_type,
            style_id=style_id,
        )

        # Generate each asset
        total = len(asset_requirements)
        for i, (key, prompt) in enumerate(asset_requirements.items()):
            if progress_callback:
                progress_callback(i + 1, total, key)

            try:
                asset = self._generate_asset(key, prompt, style_id)
                result.assets[key] = asset
                result.total_generation_time += asset.generation_time
            except Exception as e:
                # Create error asset
                result.assets[key] = GeneratedAsset(
                    key=key,
                    prompt=prompt,
                    image_url=None,
                    image_data=None,
                    base64_data=None,
                    generation_time=0,
                    error=str(e),
                )

        return result

    def _merge_requirements(
        self,
        template_reqs: list[AssetRequirement],
        game_needs: list[AssetNeed],
        visual_style: VisualStyle,
    ) -> dict[str, str]:
        """Merge template requirements with game-specific prompts.

        Returns dict of asset_key -> prompt
        """
        result = {}

        # Create lookup for game-specific prompts
        game_prompts = {need.key: need.game_specific_prompt for need in game_needs}
        game_descriptions = {need.key: need.description for need in game_needs}

        # Style prefix for all prompts
        style_prefix = visual_style.to_prompt_prefix()

        for req in template_reqs:
            if not req.required:
                continue

            # Use game-specific prompt if available, otherwise default
            if req.key in game_prompts and game_prompts[req.key]:
                base_prompt = game_prompts[req.key]
            elif req.key in game_descriptions and game_descriptions[req.key]:
                base_prompt = game_descriptions[req.key]
            else:
                base_prompt = req.default_prompt

            # Add style and quality modifiers
            if req.transparency:
                prompt = f"{base_prompt}, {style_prefix}, transparent background, game asset, high quality"
            else:
                prompt = f"{base_prompt}, {style_prefix}, game background, high quality"

            result[req.key] = prompt

        return result

    def _generate_asset(
        self,
        key: str,
        prompt: str,
        style_id: str,
    ) -> GeneratedAsset:
        """Generate a single asset."""
        import time

        start_time = time.time()

        # Generate with Layer.ai
        result: GeneratedImage = self.client.generate_with_polling(
            prompt=prompt,
            style_id=style_id,
        )

        generation_time = time.time() - start_time

        if not result.image_url:
            return GeneratedAsset(
                key=key,
                prompt=prompt,
                image_url=None,
                image_data=None,
                base64_data=None,
                generation_time=generation_time,
                error=result.error_message or "No image URL returned",
            )

        # Download and optimize image
        try:
            image_data, width, height = self._download_and_optimize(result.image_url)
            base64_data = self._to_data_uri(image_data)

            return GeneratedAsset(
                key=key,
                prompt=prompt,
                image_url=result.image_url,
                image_data=image_data,
                base64_data=base64_data,
                generation_time=generation_time,
                width=width,
                height=height,
            )
        except Exception as e:
            return GeneratedAsset(
                key=key,
                prompt=prompt,
                image_url=result.image_url,
                image_data=None,
                base64_data=None,
                generation_time=generation_time,
                error=f"Download/optimize failed: {str(e)}",
            )

    def _download_and_optimize(
        self,
        url: str,
    ) -> tuple[bytes, int, int]:
        """Download image and optimize for playable ad size limits."""
        # Download
        response = httpx.get(url, timeout=30.0)
        response.raise_for_status()

        # Load with Pillow
        img = Image.open(BytesIO(response.content))

        # Convert to RGBA if needed (for transparency)
        if img.mode not in ("RGBA", "RGB"):
            img = img.convert("RGBA")

        # Resize if too large
        width, height = img.size
        if max(width, height) > self.max_dimension:
            ratio = self.max_dimension / max(width, height)
            new_size = (int(width * ratio), int(height * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
            width, height = img.size

        # Save optimized
        buffer = BytesIO()
        if img.mode == "RGBA":
            # PNG for transparency
            img.save(buffer, format="PNG", optimize=True)
        else:
            # JPEG for smaller size
            img.save(buffer, format="JPEG", quality=self.JPEG_QUALITY, optimize=True)

        return buffer.getvalue(), width, height

    def _to_data_uri(self, image_data: bytes) -> str:
        """Convert image bytes to data URI."""
        # Detect format from magic bytes
        if image_data[:8] == b'\x89PNG\r\n\x1a\n':
            mime_type = "image/png"
        elif image_data[:2] == b'\xff\xd8':
            mime_type = "image/jpeg"
        else:
            mime_type = "image/png"  # Default

        b64 = base64.standard_b64encode(image_data).decode("utf-8")
        return f"data:{mime_type};base64,{b64}"
