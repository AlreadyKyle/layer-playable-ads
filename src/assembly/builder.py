"""
Playable Builder - Assembles final playable ads from templates and assets.

This module:
- Loads the appropriate game template based on mechanic type
- Injects generated assets as base64 data URIs
- Configures game parameters from analysis
- Validates size and compliance
"""

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from src.analysis.game_analyzer import GameAnalysis
from src.generation.game_asset_generator import GeneratedAssetSet
from src.generation.sound_generator import PROCEDURAL_SOUNDS_JS
from src.templates.registry import MechanicType, TEMPLATE_REGISTRY, get_template


# Phaser.js CDN (will be inlined for production)
PHASER_CDN = '<script src="https://cdn.jsdelivr.net/npm/phaser@3.70.0/dist/phaser.min.js"></script>'

# Sound effects script (procedural Web Audio API sounds)
SOUND_FX_SCRIPT = f'<script>\n{PROCEDURAL_SOUNDS_JS}\n</script>'

# Timing constants (milliseconds)
HOOK_DURATION_MS = 3000
GAMEPLAY_DURATION_MS = 15000
CTA_DURATION_MS = 5000


@dataclass
class PlayableConfig:
    """Configuration for playable ad assembly."""

    # Basic info
    game_name: str = "My Game"
    title: str = "Playable Ad"

    # Store URLs
    store_url: str = "https://example.com"
    store_url_ios: str = ""
    store_url_android: str = ""

    # Timing (milliseconds)
    hook_duration: int = HOOK_DURATION_MS
    gameplay_duration: int = GAMEPLAY_DURATION_MS
    cta_duration: int = CTA_DURATION_MS

    # Display
    width: int = 320
    height: int = 480
    background_color: str = "#1a1a2e"

    # Text
    hook_text: str = "Tap to Play!"
    cta_text: str = "Download FREE"

    # Sound
    sound_enabled: bool = True


@dataclass
class PlayableResult:
    """Result of playable assembly."""

    html: str
    file_size_bytes: int
    mechanic_type: MechanicType
    assets_embedded: int
    is_valid: bool
    validation_errors: list[str] = field(default_factory=list)

    @property
    def file_size_kb(self) -> float:
        """File size in KB."""
        return self.file_size_bytes / 1024

    @property
    def file_size_mb(self) -> float:
        """File size in MB."""
        return self.file_size_bytes / (1024 * 1024)

    @property
    def file_size_formatted(self) -> str:
        """Human-readable file size."""
        if self.file_size_mb >= 1:
            return f"{self.file_size_mb:.2f} MB"
        return f"{self.file_size_kb:.1f} KB"

    def is_network_compatible(self, max_size_mb: float = 5.0) -> bool:
        """Check if size is within network limits."""
        return self.file_size_mb <= max_size_mb


class PlayableBuilder:
    """Builds playable ads from templates and assets."""

    MAX_SIZE_MB = 5.0  # Most networks allow 5MB

    def __init__(self):
        """Initialize the builder."""
        self.templates_dir = Path(__file__).parent.parent / "templates"

    def build(
        self,
        analysis: GameAnalysis,
        assets: GeneratedAssetSet,
        config: Optional[PlayableConfig] = None,
    ) -> PlayableResult:
        """Build a playable ad from analysis and assets.

        Args:
            analysis: GameAnalysis from game analyzer
            assets: GeneratedAssetSet from asset generator
            config: Optional configuration overrides

        Returns:
            PlayableResult with assembled HTML
        """
        # Get template
        template_info = get_template(analysis.mechanic_type)
        if not template_info:
            # Fall back to tapper
            template_info = TEMPLATE_REGISTRY[MechanicType.TAPPER]

        # Load template HTML
        template_path = template_info.get_template_path()
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")

        template_html = template_path.read_text(encoding="utf-8")

        # Merge config with analysis suggestions
        final_config = self._merge_config(analysis, config)

        # Merge template config with analysis
        template_config = {**template_info.get_default_config(), **analysis.template_config}

        # Build asset manifest
        asset_manifest = assets.get_asset_manifest()

        # Prepare substitutions
        substitutions = self._build_substitutions(
            config=final_config,
            template_config=template_config,
            asset_manifest=asset_manifest,
        )

        # Perform substitution
        html = self._substitute_template(template_html, substitutions)

        # Validate
        errors = self._validate(html)

        # Calculate size
        size_bytes = len(html.encode("utf-8"))

        return PlayableResult(
            html=html,
            file_size_bytes=size_bytes,
            mechanic_type=analysis.mechanic_type,
            assets_embedded=len(asset_manifest),
            is_valid=len(errors) == 0,
            validation_errors=errors,
        )

    def build_from_template(
        self,
        mechanic_type: MechanicType,
        assets: GeneratedAssetSet,
        config: PlayableConfig,
        template_config: Optional[dict] = None,
    ) -> PlayableResult:
        """Build a playable ad directly from a mechanic type.

        This is a convenience wrapper around build() for when you don't
        have a GameAnalysis object.

        Args:
            mechanic_type: The game mechanic type
            assets: GeneratedAssetSet from asset generator
            config: Playable configuration
            template_config: Optional template-specific config

        Returns:
            PlayableResult with assembled HTML
        """
        from src.analysis.game_analyzer import GameAnalysis, VisualStyle

        # Create a minimal GameAnalysis to delegate to build()
        analysis = GameAnalysis(
            game_name=config.game_name,
            publisher=None,
            mechanic_type=mechanic_type,
            mechanic_confidence=1.0,
            mechanic_reasoning="Direct template build",
            visual_style=VisualStyle(
                art_type="cartoon",
                color_palette=["#FF6B6B", "#4ECDC4"],
                theme="casual",
                mood="playful",
            ),
            assets_needed=[],
            recommended_template=mechanic_type.value,
            template_config=template_config or {},
            core_loop_description="",
            hook_suggestion=config.hook_text,
            cta_suggestion=config.cta_text,
        )
        return self.build(analysis, assets, config)

    def _merge_config(
        self,
        analysis: GameAnalysis,
        config: Optional[PlayableConfig],
    ) -> PlayableConfig:
        """Merge analysis suggestions with user config."""
        if config:
            return PlayableConfig(
                game_name=config.game_name or analysis.game_name,
                title=config.title or analysis.game_name,
                store_url=config.store_url,
                store_url_ios=config.store_url_ios,
                store_url_android=config.store_url_android,
                hook_duration=config.hook_duration,
                gameplay_duration=config.gameplay_duration,
                cta_duration=config.cta_duration,
                width=config.width,
                height=config.height,
                background_color=config.background_color,
                hook_text=config.hook_text or analysis.hook_suggestion,
                cta_text=config.cta_text or analysis.cta_suggestion,
            )
        else:
            return PlayableConfig(
                game_name=analysis.game_name,
                title=analysis.game_name,
                hook_text=analysis.hook_suggestion,
                cta_text=analysis.cta_suggestion,
            )

    def _build_substitutions(
        self,
        config: PlayableConfig,
        template_config: dict,
        asset_manifest: dict[str, str],
    ) -> dict[str, str]:
        """Build substitution dictionary for template."""
        subs = {
            # Basic config
            "TITLE": config.title,
            "GAME_NAME": config.game_name,
            "BACKGROUND_COLOR": config.background_color,
            "WIDTH": str(config.width),
            "HEIGHT": str(config.height),

            # Store URLs
            "STORE_URL": config.store_url or config.store_url_ios or config.store_url_android,
            "STORE_URL_IOS": config.store_url_ios or config.store_url,
            "STORE_URL_ANDROID": config.store_url_android or config.store_url,

            # Timing
            "HOOK_DURATION": str(config.hook_duration),
            "GAMEPLAY_DURATION": str(config.gameplay_duration),
            "CTA_DURATION": str(config.cta_duration),

            # Text
            "HOOK_TEXT": config.hook_text,
            "CTA_TEXT": config.cta_text,

            # Assets
            "ASSET_MANIFEST": json.dumps(asset_manifest),

            # Phaser script + Sound effects
            "PHASER_SCRIPT": PHASER_CDN + ("\n" + SOUND_FX_SCRIPT if config.sound_enabled else ""),
        }

        # Add template-specific config
        for key, value in template_config.items():
            subs[key.upper()] = str(value) if not isinstance(value, str) else value

        return subs

    def _substitute_template(self, template_html: str, subs: dict[str, str]) -> str:
        """Perform template substitution using ${VAR} style placeholders."""
        result = template_html
        for key, value in subs.items():
            result = result.replace(f"${{{key}}}", value)
        return result

    def _validate(self, html: str) -> list[str]:
        """Validate the assembled playable."""
        errors = []

        # Check size
        size_mb = len(html.encode("utf-8")) / (1024 * 1024)
        if size_mb > self.MAX_SIZE_MB:
            errors.append(f"File size {size_mb:.2f}MB exceeds {self.MAX_SIZE_MB}MB limit")

        # Check for required elements
        if "openStoreUrl" not in html:
            errors.append("Missing openStoreUrl function")

        # Check for known template placeholders that should have been replaced
        known_placeholders = [
            "${TITLE}", "${GAME_NAME}", "${STORE_URL}", "${ASSET_MANIFEST}",
            "${PHASER_SCRIPT}", "${HOOK_TEXT}", "${CTA_TEXT}", "${BACKGROUND_COLOR}",
            "${HOOK_DURATION}", "${GAMEPLAY_DURATION}", "${CTA_DURATION}",
        ]
        remaining = [p for p in known_placeholders if p in html]
        if remaining:
            errors.append(f"Unsubstituted template variables found: {remaining}")

        # Check that asset manifest doesn't contain external URLs (XSS prevention)
        asset_section = re.search(r"var\s+ASSETS\s*=\s*(\{.*?\});", html, re.DOTALL)
        if asset_section:
            asset_json = asset_section.group(1)
            if re.search(r"https?://", asset_json):
                errors.append("Asset manifest contains external URLs (expected data URIs only)")

        return errors

    def export_html(self, result: PlayableResult, output_path: Path) -> None:
        """Export playable to HTML file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(result.html, encoding="utf-8")

    def export_zip(self, result: PlayableResult, output_path: Path) -> None:
        """Export playable as ZIP (for Google Ads)."""
        import zipfile

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("index.html", result.html)
