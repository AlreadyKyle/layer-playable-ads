"""
Asset Generator for Playable Ads

Generates game assets optimized for mobile playable ads using Layer.ai.
Follows the 3-15-5 timing model (Hook-Gameplay-CTA).

MVP v1.0 - Simplified asset generation with preset templates.
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum

import structlog

from src.layer_client import (
    LayerClientSync,
    GeneratedImage,
    StyleConfig,
    WorkspaceInfo,
    InsufficientCreditsError,
)

logger = structlog.get_logger()


# =============================================================================
# Asset Types and Categories
# =============================================================================


class AssetCategory(str, Enum):
    """Categories for playable ad assets based on timing model."""
    HOOK = "hook"           # 3-second attention grabber
    GAMEPLAY = "gameplay"   # 15-second core loop
    CTA = "cta"            # 5-second call to action


class AssetType(str, Enum):
    """Specific asset types for playable ads."""
    # Hook assets
    HOOK_CHARACTER = "hook_character"
    HOOK_ITEM = "hook_item"
    HOOK_BACKGROUND = "hook_background"

    # Gameplay assets
    GAMEPLAY_BACKGROUND = "gameplay_background"
    GAMEPLAY_ELEMENT = "gameplay_element"
    GAMEPLAY_COLLECTIBLE = "gameplay_collectible"
    GAMEPLAY_OBSTACLE = "gameplay_obstacle"

    # CTA assets
    CTA_BUTTON = "cta_button"
    CTA_BANNER = "cta_banner"
    CTA_ICON = "cta_icon"


# =============================================================================
# Asset Presets
# =============================================================================


@dataclass
class AssetPreset:
    """Preset configuration for generating specific asset types."""
    asset_type: AssetType
    category: AssetCategory
    name: str
    description: str
    prompts: list[str]  # Multiple prompts for variety
    default_style_keywords: list[str] = field(default_factory=list)

    def get_prompt(self, index: int = 0) -> str:
        """Get a prompt by index (wraps around)."""
        return self.prompts[index % len(self.prompts)]


# Standard presets optimized for top mobile games
ASSET_PRESETS: dict[AssetType, AssetPreset] = {
    # Hook assets (grab attention in 3 seconds)
    AssetType.HOOK_CHARACTER: AssetPreset(
        asset_type=AssetType.HOOK_CHARACTER,
        category=AssetCategory.HOOK,
        name="Hook Character",
        description="Eye-catching character for the 3-second hook",
        prompts=[
            "expressive cartoon game character, dynamic excited pose, arms raised celebrating, centered composition, vibrant colors, clean edges, mobile game style",
            "cute game mascot character, happy surprised expression, looking at viewer, bright colorful, game asset sprite",
            "stylized hero character, action pose, glowing effects, mobile game art style, transparent background",
        ],
        default_style_keywords=["cartoon", "vibrant", "game asset", "clean edges"],
    ),

    AssetType.HOOK_ITEM: AssetPreset(
        asset_type=AssetType.HOOK_ITEM,
        category=AssetCategory.HOOK,
        name="Hook Item",
        description="Attention-grabbing collectible or treasure",
        prompts=[
            "shiny treasure chest overflowing with gold, magical glow, sparkle particles, game asset, vibrant colors",
            "golden coin with sparkles, premium game currency, glossy metallic, clean game sprite",
            "mystery gift box with glowing question mark, magical particles, exciting, mobile game style",
        ],
        default_style_keywords=["shiny", "glowing", "game asset", "vibrant"],
    ),

    AssetType.HOOK_BACKGROUND: AssetPreset(
        asset_type=AssetType.HOOK_BACKGROUND,
        category=AssetCategory.HOOK,
        name="Hook Background",
        description="Vibrant background for hook sequence",
        prompts=[
            "vibrant game background, colorful gradient, abstract shapes, mobile game style, 16:9 ratio",
            "magical sparkle background, bright colors, particle effects, game UI backdrop",
            "exciting burst background, radial gradient, celebration confetti, mobile game",
        ],
        default_style_keywords=["vibrant", "colorful", "background", "mobile game"],
    ),

    # Gameplay assets (15-second core loop)
    AssetType.GAMEPLAY_BACKGROUND: AssetPreset(
        asset_type=AssetType.GAMEPLAY_BACKGROUND,
        category=AssetCategory.GAMEPLAY,
        name="Gameplay Background",
        description="Background for the core gameplay loop",
        prompts=[
            "colorful game level background, parallax layers, depth, no characters, vibrant mobile game environment",
            "fantasy game world backdrop, atmospheric lighting, detailed scenery, game level art",
            "casual game background, bright cheerful colors, simple clean design, mobile game style",
        ],
        default_style_keywords=["background", "game level", "parallax", "vibrant"],
    ),

    AssetType.GAMEPLAY_ELEMENT: AssetPreset(
        asset_type=AssetType.GAMEPLAY_ELEMENT,
        category=AssetCategory.GAMEPLAY,
        name="Gameplay Element",
        description="Interactive game elements",
        prompts=[
            "game platform block, clean edges, tileable, cartoon style, mobile game asset",
            "game UI element, rounded corners, glossy, casual game style, clean sprite",
            "interactive game button, 3D effect, colorful, mobile game UI asset",
        ],
        default_style_keywords=["game asset", "clean edges", "sprite", "mobile game"],
    ),

    AssetType.GAMEPLAY_COLLECTIBLE: AssetPreset(
        asset_type=AssetType.GAMEPLAY_COLLECTIBLE,
        category=AssetCategory.GAMEPLAY,
        name="Gameplay Collectible",
        description="Items players can collect during gameplay",
        prompts=[
            "glowing gem collectible, faceted crystal, sparkle effect, game pickup sprite",
            "golden star collectible, shiny metallic, game reward, clean sprite style",
            "colorful candy collectible, glossy, match-3 game style, vibrant game asset",
        ],
        default_style_keywords=["collectible", "glowing", "game sprite", "clean"],
    ),

    AssetType.GAMEPLAY_OBSTACLE: AssetPreset(
        asset_type=AssetType.GAMEPLAY_OBSTACLE,
        category=AssetCategory.GAMEPLAY,
        name="Gameplay Obstacle",
        description="Obstacles or enemies in gameplay",
        prompts=[
            "game obstacle spike, dangerous looking, cartoon style, game hazard sprite",
            "cute enemy character, mischievous expression, bouncy, mobile game style",
            "game barrier block, warning colors, clean edges, mobile game asset",
        ],
        default_style_keywords=["game obstacle", "sprite", "clean edges", "mobile game"],
    ),

    # CTA assets (5-second call to action)
    AssetType.CTA_BUTTON: AssetPreset(
        asset_type=AssetType.CTA_BUTTON,
        category=AssetCategory.CTA,
        name="CTA Button",
        description="Call-to-action button",
        prompts=[
            "play now button, glossy green gradient, rounded corners, 3D depth effect, game UI",
            "download button, app store style, prominent, clean modern design",
            "install free button, action oriented, finger tap indicator, bright green",
        ],
        default_style_keywords=["button", "UI", "glossy", "call to action"],
    ),

    AssetType.CTA_BANNER: AssetPreset(
        asset_type=AssetType.CTA_BANNER,
        category=AssetCategory.CTA,
        name="CTA Banner",
        description="End card banner for app install",
        prompts=[
            "game logo banner, premium quality, brand style, clean professional design",
            "download now banner, urgent style, attention grabbing, game promotion",
            "limited time offer badge, exclusive golden, premium game marketing",
        ],
        default_style_keywords=["banner", "professional", "game marketing", "clean"],
    ),

    AssetType.CTA_ICON: AssetPreset(
        asset_type=AssetType.CTA_ICON,
        category=AssetCategory.CTA,
        name="CTA Icon",
        description="App icon for end card",
        prompts=[
            "mobile game app icon, rounded square, vibrant colors, professional design",
            "game logo icon, clean modern style, recognizable, app store ready",
            "casual game icon, friendly character, bright colors, mobile app style",
        ],
        default_style_keywords=["app icon", "rounded", "vibrant", "professional"],
    ),
}


# =============================================================================
# Generated Asset
# =============================================================================


@dataclass
class GeneratedAsset:
    """A generated game asset."""
    asset_type: AssetType
    category: AssetCategory
    image_url: str
    image_id: Optional[str] = None
    prompt: str = ""
    generation_time: float = 0.0

    @property
    def key(self) -> str:
        """Unique key for this asset (for Phaser loading)."""
        return f"{self.category.value}_{self.asset_type.value}"


@dataclass
class AssetSet:
    """A complete set of assets for a playable ad."""
    assets: list[GeneratedAsset] = field(default_factory=list)
    style: Optional[StyleConfig] = None
    reference_image_id: Optional[str] = None
    total_generation_time: float = 0.0

    def get_by_category(self, category: AssetCategory) -> list[GeneratedAsset]:
        """Get all assets in a category."""
        return [a for a in self.assets if a.category == category]

    def get_by_type(self, asset_type: AssetType) -> Optional[GeneratedAsset]:
        """Get asset by type (returns first match)."""
        for asset in self.assets:
            if asset.asset_type == asset_type:
                return asset
        return None

    @property
    def hook_assets(self) -> list[GeneratedAsset]:
        return self.get_by_category(AssetCategory.HOOK)

    @property
    def gameplay_assets(self) -> list[GeneratedAsset]:
        return self.get_by_category(AssetCategory.GAMEPLAY)

    @property
    def cta_assets(self) -> list[GeneratedAsset]:
        return self.get_by_category(AssetCategory.CTA)

    @property
    def asset_count(self) -> int:
        return len(self.assets)


# =============================================================================
# Asset Generator
# =============================================================================


class AssetGenerator:
    """
    Generates game assets for playable ads using Layer.ai.

    Features:
    - Pre-defined presets optimized for mobile playable ads
    - Style consistency via reference images
    - Credit checking before generation
    - Support for custom prompts
    """

    def __init__(self, client: Optional[LayerClientSync] = None):
        self._client = client or LayerClientSync()
        self._logger = logger.bind(component="AssetGenerator")
        self._current_style: Optional[StyleConfig] = None
        self._reference_image_id: Optional[str] = None

    def set_style(self, style: StyleConfig) -> None:
        """Set the style configuration for consistent generation."""
        self._current_style = style
        self._logger.info("Style set", style_name=style.name)

    def set_reference_image(self, image_id: str) -> None:
        """Set reference image for visual consistency."""
        self._reference_image_id = image_id
        self._logger.info("Reference image set", image_id=image_id)

    def check_credits(self) -> WorkspaceInfo:
        """Check if workspace has sufficient credits."""
        return self._client.check_credits()

    def generate_from_preset(
        self,
        asset_type: AssetType,
        prompt_index: int = 0,
        custom_style: Optional[StyleConfig] = None,
    ) -> GeneratedAsset:
        """
        Generate an asset using a preset configuration.

        Args:
            asset_type: Type of asset to generate
            prompt_index: Which prompt variant to use (0, 1, 2...)
            custom_style: Override the current style

        Returns:
            GeneratedAsset with image URL and metadata
        """
        if asset_type not in ASSET_PRESETS:
            raise ValueError(f"Unknown asset type: {asset_type}")

        preset = ASSET_PRESETS[asset_type]
        prompt = preset.get_prompt(prompt_index)

        return self.generate_custom(
            prompt=prompt,
            asset_type=asset_type,
            category=preset.category,
            custom_style=custom_style,
        )

    def generate_custom(
        self,
        prompt: str,
        asset_type: AssetType = AssetType.GAMEPLAY_ELEMENT,
        category: AssetCategory = AssetCategory.GAMEPLAY,
        custom_style: Optional[StyleConfig] = None,
    ) -> GeneratedAsset:
        """
        Generate an asset with a custom prompt.

        Args:
            prompt: Custom generation prompt
            asset_type: Type classification for the asset
            category: Category (hook/gameplay/cta)
            custom_style: Override the current style

        Returns:
            GeneratedAsset with image URL and metadata
        """
        style = custom_style or self._current_style

        self._logger.info(
            "Generating asset",
            asset_type=asset_type.value,
            category=category.value,
            prompt_preview=prompt[:50],
        )

        # Generate with Layer.ai
        result: GeneratedImage = self._client.generate_with_polling(
            prompt=prompt,
            style=style,
            reference_image_id=self._reference_image_id,
        )

        asset = GeneratedAsset(
            asset_type=asset_type,
            category=category,
            image_url=result.image_url or "",
            image_id=result.image_id,
            prompt=prompt,
            generation_time=result.duration_seconds,
        )

        # Set reference from first generation for consistency
        if self._reference_image_id is None and result.image_id:
            self._reference_image_id = result.image_id
            self._logger.info("Reference image auto-set", image_id=result.image_id)

        self._logger.info(
            "Asset generated",
            asset_type=asset_type.value,
            duration=f"{result.duration_seconds:.1f}s",
        )

        return asset

    def generate_minimal_set(self) -> AssetSet:
        """
        Generate a minimal asset set for a playable ad.

        Includes:
        - 1 hook character
        - 1 gameplay background
        - 1 gameplay collectible
        - 1 CTA button

        Returns:
            AssetSet with 4 essential assets
        """
        self._logger.info("Generating minimal asset set")

        asset_set = AssetSet(style=self._current_style)

        types_to_generate = [
            AssetType.HOOK_CHARACTER,
            AssetType.GAMEPLAY_BACKGROUND,
            AssetType.GAMEPLAY_COLLECTIBLE,
            AssetType.CTA_BUTTON,
        ]

        for asset_type in types_to_generate:
            try:
                asset = self.generate_from_preset(asset_type)
                asset_set.assets.append(asset)
                asset_set.total_generation_time += asset.generation_time
            except InsufficientCreditsError:
                self._logger.warning("Insufficient credits, stopping generation")
                break
            except Exception as e:
                self._logger.error(f"Failed to generate {asset_type}", error=str(e))

        asset_set.reference_image_id = self._reference_image_id

        self._logger.info(
            "Minimal set complete",
            asset_count=asset_set.asset_count,
            total_time=f"{asset_set.total_generation_time:.1f}s",
        )

        return asset_set

    def generate_standard_set(self) -> AssetSet:
        """
        Generate a standard asset set for a playable ad.

        Includes:
        - 2 hook assets (character + item)
        - 3 gameplay assets (background + collectible + element)
        - 2 CTA assets (button + banner)

        Returns:
            AssetSet with 7 standard assets
        """
        self._logger.info("Generating standard asset set")

        asset_set = AssetSet(style=self._current_style)

        types_to_generate = [
            # Hook (2)
            AssetType.HOOK_CHARACTER,
            AssetType.HOOK_ITEM,
            # Gameplay (3)
            AssetType.GAMEPLAY_BACKGROUND,
            AssetType.GAMEPLAY_COLLECTIBLE,
            AssetType.GAMEPLAY_ELEMENT,
            # CTA (2)
            AssetType.CTA_BUTTON,
            AssetType.CTA_BANNER,
        ]

        for asset_type in types_to_generate:
            try:
                asset = self.generate_from_preset(asset_type)
                asset_set.assets.append(asset)
                asset_set.total_generation_time += asset.generation_time
            except InsufficientCreditsError:
                self._logger.warning("Insufficient credits, stopping generation")
                break
            except Exception as e:
                self._logger.error(f"Failed to generate {asset_type}", error=str(e))

        asset_set.reference_image_id = self._reference_image_id

        self._logger.info(
            "Standard set complete",
            asset_count=asset_set.asset_count,
            total_time=f"{asset_set.total_generation_time:.1f}s",
        )

        return asset_set

    def generate_custom_set(
        self,
        asset_types: list[AssetType],
    ) -> AssetSet:
        """
        Generate a custom selection of assets.

        Args:
            asset_types: List of asset types to generate

        Returns:
            AssetSet with requested assets
        """
        self._logger.info("Generating custom asset set", count=len(asset_types))

        asset_set = AssetSet(style=self._current_style)

        for asset_type in asset_types:
            try:
                asset = self.generate_from_preset(asset_type)
                asset_set.assets.append(asset)
                asset_set.total_generation_time += asset.generation_time
            except InsufficientCreditsError:
                self._logger.warning("Insufficient credits, stopping generation")
                break
            except Exception as e:
                self._logger.error(f"Failed to generate {asset_type}", error=str(e))

        asset_set.reference_image_id = self._reference_image_id

        return asset_set

    @property
    def available_presets(self) -> dict[AssetType, AssetPreset]:
        """Get all available asset presets."""
        return ASSET_PRESETS.copy()

    def reset(self) -> None:
        """Reset generator state (style and reference image)."""
        self._current_style = None
        self._reference_image_id = None
        self._logger.info("Generator reset")


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "AssetGenerator",
    "AssetCategory",
    "AssetType",
    "AssetPreset",
    "GeneratedAsset",
    "AssetSet",
    "ASSET_PRESETS",
]
