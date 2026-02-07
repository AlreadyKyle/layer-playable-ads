"""
Tests for Playable Builder (v2.0)

Test coverage for playable assembly functionality using
the v2.0 builder API (src.assembly.builder).
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from src.assembly.builder import (
    PlayableBuilder,
    PlayableConfig,
    PlayableResult,
    HOOK_DURATION_MS,
    GAMEPLAY_DURATION_MS,
    CTA_DURATION_MS,
)
from src.templates.registry import MechanicType
from src.generation.game_asset_generator import GeneratedAssetSet
from src.analysis.game_analyzer import GameAnalysis, VisualStyle


# =============================================================================
# Timing Constants Tests
# =============================================================================


class TestTimingConstants:
    """Tests for timing constants (non-negotiable per PRD)."""

    def test_hook_duration(self):
        """Test hook duration is 3 seconds."""
        assert HOOK_DURATION_MS == 3000

    def test_gameplay_duration(self):
        """Test gameplay duration is 15 seconds."""
        assert GAMEPLAY_DURATION_MS == 15000

    def test_cta_duration(self):
        """Test CTA duration is 5 seconds."""
        assert CTA_DURATION_MS == 5000

    def test_total_duration(self):
        """Test total duration is 23 seconds."""
        total = HOOK_DURATION_MS + GAMEPLAY_DURATION_MS + CTA_DURATION_MS
        assert total == 23000


# =============================================================================
# PlayableConfig Tests
# =============================================================================


class TestPlayableConfig:
    """Tests for PlayableConfig dataclass."""

    def test_default_config(self):
        """Test default PlayableConfig values."""
        config = PlayableConfig()

        assert config.title == "Playable Ad"
        assert config.width == 320
        assert config.height == 480
        assert config.background_color == "#1a1a2e"
        assert config.game_name == "My Game"

    def test_custom_config(self):
        """Test custom PlayableConfig values."""
        config = PlayableConfig(
            game_name="My Game",
            title="Test Title",
            width=480,
            height=320,
            background_color="#000000",
            store_url="https://example.com",
            hook_text="Play Now!",
            cta_text="Download",
        )

        assert config.game_name == "My Game"
        assert config.title == "Test Title"
        assert config.width == 480
        assert config.height == 320
        assert config.hook_text == "Play Now!"
        assert config.cta_text == "Download"

    def test_timing_defaults(self):
        """Test default timing values match constants."""
        config = PlayableConfig()

        assert config.hook_duration == HOOK_DURATION_MS
        assert config.gameplay_duration == GAMEPLAY_DURATION_MS
        assert config.cta_duration == CTA_DURATION_MS


# =============================================================================
# PlayableResult Tests
# =============================================================================


class TestPlayableResult:
    """Tests for PlayableResult dataclass."""

    def test_file_size_kb(self):
        """Test file size in KB."""
        result = PlayableResult(
            html="x" * 2048,
            file_size_bytes=2048,
            mechanic_type=MechanicType.MATCH3,
            assets_embedded=0,
            is_valid=True,
        )

        assert result.file_size_kb == 2.0

    def test_file_size_mb(self):
        """Test file size in MB."""
        result = PlayableResult(
            html="x",
            file_size_bytes=2 * 1024 * 1024,
            mechanic_type=MechanicType.MATCH3,
            assets_embedded=0,
            is_valid=True,
        )

        assert result.file_size_mb == 2.0

    def test_file_size_formatted_kb(self):
        """Test file size formatting for KB."""
        result = PlayableResult(
            html="x",
            file_size_bytes=5000,
            mechanic_type=MechanicType.MATCH3,
            assets_embedded=0,
            is_valid=True,
        )

        assert "KB" in result.file_size_formatted

    def test_file_size_formatted_mb(self):
        """Test file size formatting for MB."""
        result = PlayableResult(
            html="x",
            file_size_bytes=2_000_000,
            mechanic_type=MechanicType.MATCH3,
            assets_embedded=0,
            is_valid=True,
        )

        assert "MB" in result.file_size_formatted

    def test_network_compatible(self):
        """Test network compatibility check."""
        small = PlayableResult(
            html="x",
            file_size_bytes=1_000_000,
            mechanic_type=MechanicType.MATCH3,
            assets_embedded=0,
            is_valid=True,
        )

        large = PlayableResult(
            html="x",
            file_size_bytes=6_000_000,
            mechanic_type=MechanicType.MATCH3,
            assets_embedded=0,
            is_valid=True,
        )

        assert small.is_network_compatible(5.0) is True
        assert large.is_network_compatible(5.0) is False

    def test_validation_errors(self):
        """Test result with validation errors."""
        result = PlayableResult(
            html="x",
            file_size_bytes=100,
            mechanic_type=MechanicType.MATCH3,
            assets_embedded=0,
            is_valid=False,
            validation_errors=["Missing openStoreUrl"],
        )

        assert not result.is_valid
        assert len(result.validation_errors) == 1


# =============================================================================
# PlayableBuilder Tests
# =============================================================================


def _make_analysis(mechanic_type=MechanicType.MATCH3, game_name="Test Game"):
    """Helper to create a GameAnalysis for testing."""
    return GameAnalysis(
        game_name=game_name,
        publisher="Test",
        mechanic_type=mechanic_type,
        mechanic_confidence=1.0,
        mechanic_reasoning="Test",
        visual_style=VisualStyle(
            art_type="cartoon",
            color_palette=["#FF0000", "#00FF00"],
            theme="casual",
            mood="playful",
        ),
        assets_needed=[],
        recommended_template=mechanic_type.value,
        template_config={},
        core_loop_description="Test game",
        hook_suggestion="Play Now!",
        cta_suggestion="Download!",
    )


def _make_assets(mechanic_type=MechanicType.MATCH3, game_name="Test Game"):
    """Helper to create an empty GeneratedAssetSet for testing."""
    return GeneratedAssetSet(
        game_name=game_name,
        mechanic_type=mechanic_type,
        style_id="test",
    )


class TestPlayableBuilder:
    """Tests for PlayableBuilder class."""

    def test_builder_initialization(self):
        """Test PlayableBuilder initialization."""
        builder = PlayableBuilder()
        assert builder is not None
        assert builder.templates_dir.exists()

    def test_build_produces_html(self):
        """Test that build produces HTML output."""
        builder = PlayableBuilder()
        analysis = _make_analysis()
        assets = _make_assets()
        config = PlayableConfig(game_name="Test Game", store_url="https://example.com")

        result = builder.build(analysis, assets, config)

        assert result is not None
        assert result.file_size_bytes > 0
        assert "openStoreUrl" in result.html

    def test_build_substitutes_config(self):
        """Test that config values are substituted into HTML."""
        builder = PlayableBuilder()
        analysis = _make_analysis()
        assets = _make_assets()
        config = PlayableConfig(
            game_name="Test Game",
            title="My Title",
            store_url="https://test.example.com",
            hook_text="Custom Hook",
            cta_text="Custom CTA",
            background_color="#123456",
        )

        result = builder.build(analysis, assets, config)

        assert "My Title" in result.html
        assert "https://test.example.com" in result.html
        assert "Custom Hook" in result.html
        assert "Custom CTA" in result.html
        assert "#123456" in result.html

    def test_build_no_unsubstituted_placeholders(self):
        """Test that no ${} placeholders remain after build."""
        builder = PlayableBuilder()
        analysis = _make_analysis()
        assets = _make_assets()
        config = PlayableConfig(game_name="Test", store_url="https://example.com")

        result = builder.build(analysis, assets, config)

        assert "${" not in result.html, "Unsubstituted placeholders found"

    def test_build_from_template(self):
        """Test building directly from mechanic type."""
        builder = PlayableBuilder()
        assets = _make_assets(mechanic_type=MechanicType.TAPPER)
        config = PlayableConfig(game_name="Tapper Test", store_url="https://example.com")

        result = builder.build_from_template(
            mechanic_type=MechanicType.TAPPER,
            assets=assets,
            config=config,
        )

        assert result is not None
        assert result.mechanic_type == MechanicType.TAPPER
        assert result.file_size_bytes > 0

    def test_validate_size_limit(self):
        """Test that oversized playables are flagged."""
        builder = PlayableBuilder()
        errors = builder._validate("x" * (6 * 1024 * 1024))  # 6MB

        assert any("exceeds" in e for e in errors)

    def test_validate_missing_store_url(self):
        """Test validation catches missing openStoreUrl."""
        builder = PlayableBuilder()
        errors = builder._validate("<html><body>No store url</body></html>")

        assert any("openStoreUrl" in e for e in errors)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
