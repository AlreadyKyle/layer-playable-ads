"""
Playable Factory - Unified pipeline for creating playable ads.

This module provides a single entry point that combines:
- Game analysis (Claude Vision)
- Asset generation (Layer.ai)
- Template selection and assembly
- Sound effects integration
- Export to various formats

Usage:
    factory = PlayableFactory()

    # From screenshots
    result = factory.create_from_screenshots(
        screenshots=[...],
        style_id="layer_style_id",
        store_url="https://..."
    )

    # Save the result
    result.save("output/playable.html")
    result.save_zip("output/playable.zip")
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Callable
import zipfile

from src.analysis import GameAnalyzerSync, GameAnalysis
from src.generation import GameAssetGenerator, GeneratedAssetSet, DynamicGameGenerator
from src.assembly import PlayableBuilder, PlayableConfig, PlayableResult
from src.templates import MechanicType, TEMPLATE_REGISTRY


@dataclass
class FactoryConfig:
    """Configuration for the playable factory."""

    # Store URLs
    store_url: str = ""
    store_url_ios: str = ""
    store_url_android: str = ""

    # Display
    width: int = 320
    height: int = 480
    background_color: str = "#1a1a2e"

    # Text (can be auto-filled from analysis)
    hook_text: Optional[str] = None
    cta_text: Optional[str] = None

    # Features
    sound_enabled: bool = True
    use_dynamic_generation: bool = False  # Use Claude to generate custom game code

    # Layer.ai
    style_id: Optional[str] = None


@dataclass
class PlayableOutput:
    """Final output from the factory."""

    html: str
    file_size_bytes: int
    mechanic_type: MechanicType
    game_name: str
    assets_count: int
    is_valid: bool
    validation_errors: list[str] = field(default_factory=list)

    # Intermediate results
    analysis: Optional[GameAnalysis] = None
    assets: Optional[GeneratedAssetSet] = None

    @property
    def file_size_mb(self) -> float:
        """File size in MB."""
        return self.file_size_bytes / (1024 * 1024)

    @property
    def file_size_formatted(self) -> str:
        """Human-readable file size."""
        if self.file_size_mb >= 1:
            return f"{self.file_size_mb:.2f} MB"
        return f"{self.file_size_bytes / 1024:.1f} KB"

    def is_network_compatible(self, max_size_mb: float = 5.0) -> bool:
        """Check if size is within network limits."""
        return self.file_size_mb <= max_size_mb

    def save(self, path: str | Path) -> None:
        """Save as HTML file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.html)

    def save_zip(self, path: str | Path) -> None:
        """Save as ZIP file (for Google Ads)."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("index.html", self.html)


class PlayableFactory:
    """
    Unified factory for creating playable ads.

    Orchestrates the complete pipeline:
    1. Analyze game screenshots (Claude Vision)
    2. Generate game-specific assets (Layer.ai)
    3. Select and configure template (Phaser.js)
    4. Assemble and validate output

    Example:
        factory = PlayableFactory()

        # Full pipeline
        result = factory.create_from_screenshots(
            screenshots=["screenshot1.png", "screenshot2.png"],
            style_id="abc123",
            store_url="https://apps.apple.com/app/id123"
        )

        # Check result
        if result.is_valid:
            result.save("playable.html")
            result.save_zip("playable.zip")
            print(f"Created {result.mechanic_type.value} playable: {result.file_size_formatted}")
    """

    def __init__(
        self,
        anthropic_api_key: Optional[str] = None,
        layer_api_key: Optional[str] = None,
    ):
        """Initialize the factory.

        Args:
            anthropic_api_key: Anthropic API key (uses env var if not provided)
            layer_api_key: Layer.ai API key (uses env var if not provided)
        """
        self._analyzer = GameAnalyzerSync(api_key=anthropic_api_key)
        self._builder = PlayableBuilder()
        self._dynamic_generator = DynamicGameGenerator(api_key=anthropic_api_key)

    def create_from_screenshots(
        self,
        screenshots: list[bytes | str | Path],
        style_id: str,
        store_url: str = "",
        config: Optional[FactoryConfig] = None,
        game_name_hint: Optional[str] = None,
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
    ) -> PlayableOutput:
        """Create a playable ad from game screenshots.

        This is the main entry point that runs the complete pipeline.

        Args:
            screenshots: List of screenshot images (bytes, file paths)
            style_id: Layer.ai style ID for asset generation
            store_url: Primary app store URL
            config: Optional configuration overrides
            game_name_hint: Optional hint about the game name
            progress_callback: Optional callback(step_name, current, total)

        Returns:
            PlayableOutput with the assembled playable
        """
        config = config or FactoryConfig()
        config.style_id = style_id
        config.store_url = store_url or config.store_url

        # Progress tracking
        def progress(step: str, current: int = 1, total: int = 1):
            if progress_callback:
                progress_callback(step, current, total)

        # Step 1: Analyze game
        progress("Analyzing game...", 1, 4)
        analysis = self._analyzer.analyze_screenshots(screenshots, game_name_hint)

        # Step 2: Generate assets
        progress("Generating assets...", 2, 4)
        asset_generator = GameAssetGenerator()
        assets = asset_generator.generate_for_game(
            analysis=analysis,
            style_id=style_id,
            progress_callback=lambda c, t, n: progress(f"Generating {n}...", c, t),
        )

        # Step 3: Build playable
        progress("Assembling playable...", 3, 4)
        playable_config = PlayableConfig(
            game_name=analysis.game_name,
            title=analysis.game_name,
            store_url=config.store_url,
            store_url_ios=config.store_url_ios,
            store_url_android=config.store_url_android,
            width=config.width,
            height=config.height,
            background_color=config.background_color,
            hook_text=config.hook_text or analysis.hook_suggestion,
            cta_text=config.cta_text or analysis.cta_suggestion,
            sound_enabled=config.sound_enabled,
        )

        if config.use_dynamic_generation:
            # Use Claude to generate custom game code
            generated = self._dynamic_generator.generate_game(analysis)
            # TODO: Merge with assets
            result = PlayableResult(
                html=generated.html,
                file_size_bytes=len(generated.html.encode()),
                mechanic_type=analysis.mechanic_type,
                assets_embedded=0,
                is_valid=True,
            )
        else:
            # Use template-based assembly
            result = self._builder.build(analysis, assets, playable_config)

        # Step 4: Package output
        progress("Finalizing...", 4, 4)

        return PlayableOutput(
            html=result.html,
            file_size_bytes=result.file_size_bytes,
            mechanic_type=result.mechanic_type,
            game_name=analysis.game_name,
            assets_count=result.assets_embedded,
            is_valid=result.is_valid,
            validation_errors=result.validation_errors,
            analysis=analysis,
            assets=assets,
        )

    def create_from_analysis(
        self,
        analysis: GameAnalysis,
        style_id: str,
        config: Optional[FactoryConfig] = None,
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
    ) -> PlayableOutput:
        """Create a playable from pre-existing game analysis.

        Use this when you've already analyzed the game and want to
        regenerate assets or try different settings.

        Args:
            analysis: Pre-existing GameAnalysis
            style_id: Layer.ai style ID
            config: Optional configuration
            progress_callback: Optional progress callback

        Returns:
            PlayableOutput
        """
        config = config or FactoryConfig()
        config.style_id = style_id

        def progress(step: str, current: int = 1, total: int = 1):
            if progress_callback:
                progress_callback(step, current, total)

        # Generate assets
        progress("Generating assets...", 1, 2)
        asset_generator = GameAssetGenerator()
        assets = asset_generator.generate_for_game(analysis, style_id)

        # Build playable
        progress("Assembling playable...", 2, 2)
        playable_config = PlayableConfig(
            game_name=analysis.game_name,
            title=analysis.game_name,
            store_url=config.store_url,
            store_url_ios=config.store_url_ios,
            store_url_android=config.store_url_android,
            width=config.width,
            height=config.height,
            background_color=config.background_color,
            hook_text=config.hook_text or analysis.hook_suggestion,
            cta_text=config.cta_text or analysis.cta_suggestion,
            sound_enabled=config.sound_enabled,
        )

        result = self._builder.build(analysis, assets, playable_config)

        return PlayableOutput(
            html=result.html,
            file_size_bytes=result.file_size_bytes,
            mechanic_type=result.mechanic_type,
            game_name=analysis.game_name,
            assets_count=result.assets_embedded,
            is_valid=result.is_valid,
            validation_errors=result.validation_errors,
            analysis=analysis,
            assets=assets,
        )

    def create_demo(
        self,
        mechanic_type: MechanicType = MechanicType.MATCH3,
        game_name: str = "Demo Game",
    ) -> PlayableOutput:
        """Create a demo playable without API calls.

        Uses fallback graphics (colored shapes) instead of
        Layer.ai generated assets. Useful for testing.

        Args:
            mechanic_type: Type of game mechanic
            game_name: Name for the demo

        Returns:
            PlayableOutput with demo playable
        """
        from src.templates.registry import get_template

        template = get_template(mechanic_type)
        if not template:
            template = TEMPLATE_REGISTRY[MechanicType.TAPPER]
            mechanic_type = MechanicType.TAPPER

        # Create empty asset set (templates have fallback graphics)
        assets = GeneratedAssetSet(
            game_name=game_name,
            mechanic_type=mechanic_type,
            style_id="demo",
        )

        # Create minimal analysis
        from src.analysis.game_analyzer import VisualStyle

        analysis = GameAnalysis(
            game_name=game_name,
            publisher="Demo",
            mechanic_type=mechanic_type,
            mechanic_confidence=1.0,
            mechanic_reasoning="Demo mode",
            visual_style=VisualStyle(
                art_type="cartoon",
                color_palette=["#FF6B6B", "#4ECDC4", "#FFE66D", "#95E1D3"],
                theme="casual",
                mood="playful",
            ),
            assets_needed=[],
            recommended_template=mechanic_type.value,
            template_config={},
            core_loop_description=f"Demo {mechanic_type.value} game",
            hook_suggestion="Tap to Play!",
            cta_suggestion="Download FREE",
        )

        # Build playable
        config = PlayableConfig(
            game_name=game_name,
            title=game_name,
            store_url="https://example.com",
            sound_enabled=True,
        )

        result = self._builder.build(analysis, assets, config)

        return PlayableOutput(
            html=result.html,
            file_size_bytes=result.file_size_bytes,
            mechanic_type=mechanic_type,
            game_name=game_name,
            assets_count=0,
            is_valid=result.is_valid,
            validation_errors=result.validation_errors,
            analysis=analysis,
            assets=assets,
        )


# Convenience function for quick usage
def create_playable(
    screenshots: list[bytes | str | Path],
    style_id: str,
    store_url: str,
    **kwargs,
) -> PlayableOutput:
    """Convenience function to create a playable ad.

    Args:
        screenshots: Game screenshot files or bytes
        style_id: Layer.ai style ID
        store_url: App store URL
        **kwargs: Additional config options

    Returns:
        PlayableOutput
    """
    factory = PlayableFactory()
    config = FactoryConfig(
        store_url=store_url,
        **{k: v for k, v in kwargs.items() if hasattr(FactoryConfig, k)}
    )
    return factory.create_from_screenshots(
        screenshots=screenshots,
        style_id=style_id,
        config=config,
    )
