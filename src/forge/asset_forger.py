"""
Asset Forger - Smart Forge Module with Credit Guard

Handles asset generation with credit checking, reference image consistency,
and automatic polling for completion.
"""

from dataclasses import dataclass, field
from typing import Optional

import structlog

from src.layer_client import (
    ForgeResult,
    InsufficientCreditsError,
    LayerClientSync,
    WorkspaceCredits,
)

logger = structlog.get_logger()


# =============================================================================
# UA Preset Definitions
# =============================================================================

@dataclass
class UAPreset:
    """
    UA (User Acquisition) preset for generating specific asset types.

    Each preset defines prompts optimized for a specific use case
    in playable ad creation.
    """

    name: str
    description: str
    prompts: list[str]
    category: str = "general"  # hook, gameplay, cta, character, environment


# Standard UA presets for playable ads
UA_PRESETS = {
    "hook_character": UAPreset(
        name="Hook Character",
        description="Eye-catching character for the 3-second hook",
        prompts=[
            "expressive game character, dynamic pose, eye-catching, centered composition",
            "excited character celebrating, arms raised, victory pose",
            "character with surprised expression, looking at viewer",
        ],
        category="hook",
    ),
    "hook_item": UAPreset(
        name="Hook Item",
        description="Attention-grabbing item or collectible",
        prompts=[
            "shiny treasure chest, glowing, magical particles",
            "golden coin with sparkles, premium game currency",
            "mystery box with question mark, glowing edges",
        ],
        category="hook",
    ),
    "gameplay_background": UAPreset(
        name="Gameplay Background",
        description="Background for the 15-second core loop",
        prompts=[
            "game level background, vibrant colors, depth layers",
            "colorful game environment, parallax ready, no characters",
            "fantasy game world backdrop, atmospheric lighting",
        ],
        category="gameplay",
    ),
    "gameplay_element": UAPreset(
        name="Gameplay Element",
        description="Interactive elements for core gameplay",
        prompts=[
            "game obstacle, clean edges, game-ready sprite",
            "collectible gem, faceted crystal, glowing",
            "power-up item, energy effect, pickup ready",
        ],
        category="gameplay",
    ),
    "cta_button": UAPreset(
        name="CTA Button",
        description="Call-to-action button elements",
        prompts=[
            "play now button, glossy, green gradient, rounded corners",
            "download button, app store style, prominent",
            "install game button, action oriented, finger tap indicator",
        ],
        category="cta",
    ),
    "cta_banner": UAPreset(
        name="CTA Banner",
        description="End card banner elements",
        prompts=[
            "game logo banner, premium quality, brand colors",
            "install now banner, urgent, attention grabbing",
            "limited time offer badge, exclusive, golden",
        ],
        category="cta",
    ),
}


# =============================================================================
# Asset Forger
# =============================================================================


@dataclass
class ForgedAsset:
    """A successfully forged asset."""

    asset_id: str
    image_id: str
    image_url: str
    prompt: str
    preset_name: Optional[str] = None
    category: str = "general"
    duration_seconds: float = 0.0


@dataclass
class ForgeSession:
    """Tracks a forge session with multiple assets."""

    style_id: str
    reference_image_id: Optional[str] = None
    assets: list[ForgedAsset] = field(default_factory=list)
    credits_used: int = 0
    credits_remaining: int = 0

    @property
    def asset_count(self) -> int:
        return len(self.assets)

    def get_assets_by_category(self, category: str) -> list[ForgedAsset]:
        return [a for a in self.assets if a.category == category]


class AssetForger:
    """
    Smart asset forging with credit guard and consistency management.

    Features:
    - Credit checking before forge operations
    - Reference image ID propagation for visual consistency
    - UA presets for common playable ad asset types
    - Session tracking for batch operations
    """

    def __init__(self, client: Optional[LayerClientSync] = None):
        """
        Initialize AssetForger.

        Args:
            client: LayerClientSync instance (creates new if not provided)
        """
        self._client = client or LayerClientSync()
        self._logger = logger.bind(component="AssetForger")
        self._current_session: Optional[ForgeSession] = None

    def check_credits(self) -> WorkspaceCredits:
        """
        Check workspace credit balance.

        Returns:
            WorkspaceCredits with current balance

        Raises:
            InsufficientCreditsError: If credits below threshold
        """
        credits = self._client.get_workspace_credits()

        self._logger.info(
            "Credit check",
            available=credits.available,
            sufficient=credits.is_sufficient,
        )

        if not credits.is_sufficient:
            raise InsufficientCreditsError(
                f"Insufficient credits: {credits.available} available"
            )

        return credits

    def start_session(
        self,
        style_id: str,
        reference_image_id: Optional[str] = None,
    ) -> ForgeSession:
        """
        Start a new forge session.

        A session tracks related assets generated together,
        ensuring visual consistency via reference image.

        Args:
            style_id: Layer.ai style ID to use
            reference_image_id: Optional reference image for consistency

        Returns:
            New ForgeSession
        """
        # Check credits first
        credits = self.check_credits()

        self._current_session = ForgeSession(
            style_id=style_id,
            reference_image_id=reference_image_id,
            credits_remaining=credits.available,
        )

        self._logger.info(
            "Forge session started",
            style_id=style_id,
            reference_image=reference_image_id,
            credits_available=credits.available,
        )

        return self._current_session

    def forge_asset(
        self,
        prompt: str,
        preset_name: Optional[str] = None,
        use_reference: bool = True,
    ) -> ForgedAsset:
        """
        Forge a single asset.

        Args:
            prompt: Generation prompt
            preset_name: Optional preset name for categorization
            use_reference: Whether to use session's reference image

        Returns:
            ForgedAsset with image URL and metadata

        Raises:
            RuntimeError: If no active session
            InsufficientCreditsError: If credits insufficient
        """
        if self._current_session is None:
            raise RuntimeError("No active session. Call start_session() first.")

        session = self._current_session

        # Determine reference image
        reference_id = session.reference_image_id if use_reference else None

        self._logger.info(
            "Forging asset",
            prompt_preview=prompt[:50],
            preset=preset_name,
            use_reference=bool(reference_id),
        )

        # Execute forge with polling
        result: ForgeResult = self._client.forge_with_polling(
            style_id=session.style_id,
            prompt=prompt,
            reference_image_id=reference_id,
        )

        # Determine category from preset
        category = "general"
        if preset_name and preset_name in UA_PRESETS:
            category = UA_PRESETS[preset_name].category

        # Create asset record
        asset = ForgedAsset(
            asset_id=result.task_id,
            image_id=result.image_id or "",
            image_url=result.image_url or "",
            prompt=prompt,
            preset_name=preset_name,
            category=category,
            duration_seconds=result.duration_seconds,
        )

        # Update session
        session.assets.append(asset)
        session.credits_used += 1
        session.credits_remaining -= 1

        # Set reference image from first asset if not already set
        if session.reference_image_id is None and result.image_id:
            session.reference_image_id = result.image_id
            self._logger.info(
                "Reference image set from first forge",
                reference_image_id=result.image_id,
            )

        self._logger.info(
            "Asset forged successfully",
            image_id=asset.image_id,
            duration=f"{asset.duration_seconds:.1f}s",
            session_total=session.asset_count,
        )

        return asset

    def forge_from_preset(
        self,
        preset_name: str,
        prompt_index: int = 0,
    ) -> ForgedAsset:
        """
        Forge an asset using a UA preset.

        Args:
            preset_name: Name of the UA preset
            prompt_index: Which prompt from the preset to use

        Returns:
            ForgedAsset

        Raises:
            ValueError: If preset not found
        """
        if preset_name not in UA_PRESETS:
            available = list(UA_PRESETS.keys())
            raise ValueError(
                f"Unknown preset '{preset_name}'. Available: {available}"
            )

        preset = UA_PRESETS[preset_name]
        prompt = preset.prompts[prompt_index % len(preset.prompts)]

        return self.forge_asset(prompt=prompt, preset_name=preset_name)

    def forge_preset_batch(
        self,
        preset_names: list[str],
    ) -> list[ForgedAsset]:
        """
        Forge multiple assets from a list of presets.

        Args:
            preset_names: List of preset names to forge

        Returns:
            List of ForgedAssets
        """
        assets = []
        for preset_name in preset_names:
            try:
                asset = self.forge_from_preset(preset_name)
                assets.append(asset)
            except InsufficientCreditsError:
                self._logger.warning(
                    "Stopping batch: insufficient credits",
                    completed=len(assets),
                    remaining=len(preset_names) - len(assets),
                )
                break
            except Exception as e:
                self._logger.error(
                    "Forge failed in batch",
                    preset=preset_name,
                    error=str(e),
                )
                # Continue with remaining presets

        return assets

    def forge_playable_asset_set(self) -> dict[str, list[ForgedAsset]]:
        """
        Forge a complete set of assets for a playable ad.

        Generates assets for:
        - Hook (3-second intro)
        - Gameplay (15-second core loop)
        - CTA (5-second call to action)

        Returns:
            Dict mapping category to list of assets
        """
        self._logger.info("Forging complete playable asset set")

        # Define the standard playable ad asset set
        preset_sequence = [
            "hook_character",
            "hook_item",
            "gameplay_background",
            "gameplay_element",
            "gameplay_element",
            "cta_button",
            "cta_banner",
        ]

        assets = self.forge_preset_batch(preset_sequence)

        # Group by category
        result = {
            "hook": [],
            "gameplay": [],
            "cta": [],
        }

        for asset in assets:
            if asset.category in result:
                result[asset.category].append(asset)

        self._logger.info(
            "Playable asset set complete",
            hook_count=len(result["hook"]),
            gameplay_count=len(result["gameplay"]),
            cta_count=len(result["cta"]),
        )

        return result

    @property
    def current_session(self) -> Optional[ForgeSession]:
        """Get the current forge session."""
        return self._current_session

    @property
    def available_presets(self) -> dict[str, UAPreset]:
        """Get all available UA presets."""
        return UA_PRESETS.copy()

    def end_session(self) -> Optional[ForgeSession]:
        """
        End the current session.

        Returns:
            The completed session, or None if no session active
        """
        session = self._current_session
        self._current_session = None

        if session:
            self._logger.info(
                "Forge session ended",
                total_assets=session.asset_count,
                credits_used=session.credits_used,
            )

        return session


__all__ = [
    "AssetForger",
    "ForgedAsset",
    "ForgeSession",
    "UAPreset",
    "UA_PRESETS",
]
