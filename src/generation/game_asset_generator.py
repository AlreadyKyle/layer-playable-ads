"""
Game Asset Generator - Generates game-specific assets using Layer.ai.

This module takes game analysis results and generates assets
tailored to the specific game's visual style and template requirements.
"""

import base64
import time
from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path
from typing import Optional

import httpx
import structlog
from PIL import Image

from src.layer_client import LayerClientSync, GeneratedImage, LayerAPIError
from src.analysis.game_analyzer import GameAnalysis, AssetNeed, VisualStyle
from src.templates.registry import MechanicType, TEMPLATE_REGISTRY, AssetRequirement

logger = structlog.get_logger()


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
    style_warnings: list[str] = field(default_factory=list)

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

    @property
    def failed_assets(self) -> list[GeneratedAsset]:
        """Get list of failed assets."""
        return [a for a in self.assets.values() if not a.is_valid]


@dataclass
class StyleValidation:
    """Result of style validation check."""
    style_id: str
    is_valid: bool
    style_name: str = ""
    style_type: str = ""
    style_status: str = ""
    warnings: list[str] = field(default_factory=list)
    error: Optional[str] = None


class GameAssetGenerator:
    """Generates game-specific assets using Layer.ai."""

    MAX_IMAGE_DIMENSION = 512
    JPEG_QUALITY = 85

    # Simple, safe prompts that are unlikely to trigger content filters
    SIMPLE_PROMPTS = {
        "tile_1": "red gemstone",
        "tile_2": "blue crystal",
        "tile_3": "green emerald",
        "tile_4": "yellow diamond",
        "tile_5": "purple amethyst",
        "tile_6": "orange citrine",
        "background": "colorful gradient background",
        "player": "simple character sprite",
        "obstacle": "wooden crate",
        "collectible": "golden coin",
        "target": "round target",
    }

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
        self._logger = logger.bind(component="GameAssetGenerator")

    def validate_style(self, style_id: str) -> StyleValidation:
        """Validate a style before using it for generation.

        Args:
            style_id: Layer.ai style ID to validate

        Returns:
            StyleValidation with status and any warnings
        """
        self._logger.info("Validating style", style_id=style_id)

        try:
            style = self.client.get_style(style_id)

            if not style:
                return StyleValidation(
                    style_id=style_id,
                    is_valid=False,
                    error="Style not found"
                )

            style_name = style.get("name", "Unknown")
            style_type = style.get("type", "Unknown")
            style_status = style.get("status", "Unknown")

            warnings = []

            # Check status
            if style_status != "COMPLETE":
                return StyleValidation(
                    style_id=style_id,
                    is_valid=False,
                    style_name=style_name,
                    style_type=style_type,
                    style_status=style_status,
                    error=f"Style status is {style_status}, must be COMPLETE"
                )

            # Warn about base model styles
            if style_type == "MODEL_URL":
                warnings.append(
                    "This is a base model (MODEL_URL) style. "
                    "Custom-trained styles (LAYER_TRAINED_CHECKPOINT) are more reliable."
                )

            self._logger.info(
                "Style validated",
                style_id=style_id,
                style_name=style_name,
                style_type=style_type,
                warnings=warnings
            )

            return StyleValidation(
                style_id=style_id,
                is_valid=True,
                style_name=style_name,
                style_type=style_type,
                style_status=style_status,
                warnings=warnings
            )

        except LayerAPIError as e:
            self._logger.error("Style validation failed", error=str(e))
            return StyleValidation(
                style_id=style_id,
                is_valid=False,
                error=str(e)
            )
        except Exception as e:
            self._logger.error("Unexpected error validating style", error=str(e))
            return StyleValidation(
                style_id=style_id,
                is_valid=False,
                error=f"Validation error: {str(e)}"
            )

    def generate_for_game(
        self,
        analysis: GameAnalysis,
        style_id: str,
        progress_callback: Optional[callable] = None,
        validate_style: bool = True,
    ) -> GeneratedAssetSet:
        """Generate all assets needed for a game's playable ad.

        Args:
            analysis: GameAnalysis from game analyzer
            style_id: Layer.ai style ID to use
            progress_callback: Optional callback(current, total, asset_name)
            validate_style: Whether to validate style before generation

        Returns:
            GeneratedAssetSet with all generated assets
        """
        self._logger.info(
            "Starting asset generation",
            game_name=analysis.game_name,
            mechanic_type=analysis.mechanic_type.value,
            style_id=style_id
        )

        # Initialize result set
        result = GeneratedAssetSet(
            game_name=analysis.game_name,
            mechanic_type=analysis.mechanic_type,
            style_id=style_id,
        )

        # Validate style first
        if validate_style:
            validation = self.validate_style(style_id)
            if not validation.is_valid:
                self._logger.error("Style validation failed", error=validation.error)
                # Return empty result with error info
                result.style_warnings = [f"Style validation failed: {validation.error}"]
                return result
            result.style_warnings = validation.warnings

        # Get template requirements
        template = TEMPLATE_REGISTRY.get(analysis.mechanic_type)
        if not template:
            # Fall back to tapper if unknown
            self._logger.warning(
                "Unknown mechanic type, falling back to tapper",
                mechanic_type=analysis.mechanic_type.value
            )
            template = TEMPLATE_REGISTRY[MechanicType.TAPPER]

        # Merge template requirements with game-specific needs
        asset_requirements = self._merge_requirements(
            template.required_assets,
            analysis.assets_needed,
            analysis.visual_style,
        )

        self._logger.info(
            "Asset requirements determined",
            asset_count=len(asset_requirements),
            asset_keys=list(asset_requirements.keys())
        )

        # Generate each asset
        total = len(asset_requirements)
        for i, (key, prompt) in enumerate(asset_requirements.items()):
            if progress_callback:
                progress_callback(i + 1, total, key)

            self._logger.info(
                "Generating asset",
                key=key,
                prompt=prompt[:50] + "..." if len(prompt) > 50 else prompt,
                progress=f"{i + 1}/{total}"
            )

            try:
                asset = self._generate_asset_with_retry(key, prompt, style_id)
                result.assets[key] = asset
                result.total_generation_time += asset.generation_time

                if asset.is_valid:
                    self._logger.info(
                        "Asset generated successfully",
                        key=key,
                        generation_time=f"{asset.generation_time:.1f}s"
                    )
                else:
                    self._logger.warning(
                        "Asset generation failed",
                        key=key,
                        error=asset.error
                    )

            except Exception as e:
                self._logger.error(
                    "Asset generation exception",
                    key=key,
                    error=str(e)
                )
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

        # Log summary
        self._logger.info(
            "Asset generation complete",
            total_assets=len(result.assets),
            valid_assets=result.valid_count,
            failed_assets=len(result.failed_assets),
            total_time=f"{result.total_generation_time:.1f}s"
        )

        return result

    def _generate_asset_with_retry(
        self,
        key: str,
        prompt: str,
        style_id: str,
        max_retries: int = 2,
    ) -> GeneratedAsset:
        """Generate asset with retry using simplified prompts on failure."""
        last_error = None

        for attempt in range(max_retries + 1):
            # Use original prompt first, then simplify
            if attempt == 0:
                current_prompt = prompt
            else:
                # Try a simpler prompt on retry
                simple_prompt = self.SIMPLE_PROMPTS.get(key, "simple object")
                current_prompt = simple_prompt
                self._logger.info(
                    "Retrying with simplified prompt",
                    key=key,
                    attempt=attempt + 1,
                    prompt=current_prompt
                )

            try:
                asset = self._generate_asset(key, current_prompt, style_id)
                if asset.is_valid:
                    return asset
                last_error = asset.error
            except Exception as e:
                last_error = str(e)

            # Wait before retry
            if attempt < max_retries:
                time.sleep(2 * (attempt + 1))

        # All retries failed
        return GeneratedAsset(
            key=key,
            prompt=prompt,
            image_url=None,
            image_data=None,
            base64_data=None,
            generation_time=0,
            error=f"All attempts failed: {last_error}",
        )

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

            # Keep prompts simple to avoid content filtering
            # Layer.ai styles already encode the visual style, so don't overload the prompt
            if req.transparency:
                prompt = f"{base_prompt}, isolated on white background"
            else:
                prompt = base_prompt

            result[req.key] = prompt

        return result

    def _generate_asset(
        self,
        key: str,
        prompt: str,
        style_id: str,
    ) -> GeneratedAsset:
        """Generate a single asset."""
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
