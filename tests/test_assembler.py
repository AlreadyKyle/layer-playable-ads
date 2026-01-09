"""
Tests for Playable Assembler

Basic test coverage for playable assembly functionality.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from src.playable.assembler import (
    PlayableAssembler,
    PlayableConfig,
    PlayableMetadata,
    PlayableAsset,
    AdNetwork,
    NETWORK_SPECS,
    HOOK_DURATION_MS,
    GAMEPLAY_DURATION_MS,
    CTA_DURATION_MS,
    TOTAL_DURATION_MS,
)


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
        assert TOTAL_DURATION_MS == 23000
        assert TOTAL_DURATION_MS == HOOK_DURATION_MS + GAMEPLAY_DURATION_MS + CTA_DURATION_MS


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

    def test_custom_config(self):
        """Test custom PlayableConfig values."""
        config = PlayableConfig(
            title="My Game",
            width=480,
            height=320,
            background_color="#000000",
            store_url_ios="https://apps.apple.com/test",
            hook_text="Play Now!",
            cta_text="Download",
        )

        assert config.title == "My Game"
        assert config.width == 480
        assert config.height == 320
        assert config.hook_text == "Play Now!"


# =============================================================================
# PlayableMetadata Tests
# =============================================================================


class TestPlayableMetadata:
    """Tests for PlayableMetadata dataclass."""

    def test_file_size_formatted_bytes(self):
        """Test file size formatting for bytes."""
        metadata = PlayableMetadata(
            title="Test",
            file_size_bytes=500,
            asset_count=1,
            networks_compatible=["IronSource"],
        )

        assert "B" in metadata.file_size_formatted

    def test_file_size_formatted_kb(self):
        """Test file size formatting for KB."""
        metadata = PlayableMetadata(
            title="Test",
            file_size_bytes=5000,
            asset_count=1,
            networks_compatible=["IronSource"],
        )

        formatted = metadata.file_size_formatted
        assert "KB" in formatted

    def test_file_size_formatted_mb(self):
        """Test file size formatting for MB."""
        metadata = PlayableMetadata(
            title="Test",
            file_size_bytes=2_000_000,
            asset_count=1,
            networks_compatible=["IronSource"],
        )

        formatted = metadata.file_size_formatted
        assert "MB" in formatted

    def test_default_duration(self):
        """Test default duration is 23000ms."""
        metadata = PlayableMetadata(
            title="Test",
            file_size_bytes=1000,
            asset_count=1,
            networks_compatible=[],
        )

        assert metadata.duration_ms == 23000

    def test_mraid_version(self):
        """Test default MRAID version is 3.0."""
        metadata = PlayableMetadata(
            title="Test",
            file_size_bytes=1000,
            asset_count=1,
            networks_compatible=[],
        )

        assert metadata.mraid_version == "3.0"


# =============================================================================
# AdNetwork Tests
# =============================================================================


class TestAdNetwork:
    """Tests for AdNetwork enum and specs."""

    def test_network_values(self):
        """Test all network enum values exist."""
        assert AdNetwork.IRONSOURCE == "ironsource"
        assert AdNetwork.UNITY == "unity"
        assert AdNetwork.APPLOVIN == "applovin"
        assert AdNetwork.FACEBOOK == "facebook"
        assert AdNetwork.GOOGLE == "google"
        assert AdNetwork.MINTEGRAL == "mintegral"
        assert AdNetwork.VUNGLE == "vungle"
        assert AdNetwork.TIKTOK == "tiktok"
        assert AdNetwork.GENERIC == "generic"

    def test_network_specs_exist(self):
        """Test all networks have specs."""
        for network in AdNetwork:
            assert network in NETWORK_SPECS

    def test_ironsource_spec(self):
        """Test IronSource network spec."""
        spec = NETWORK_SPECS[AdNetwork.IRONSOURCE]

        assert spec.name == "IronSource"
        assert spec.max_size_mb == 5.0
        assert spec.format == "html"
        assert spec.requires_mraid is True

    def test_facebook_spec(self):
        """Test Facebook network spec (stricter size limit)."""
        spec = NETWORK_SPECS[AdNetwork.FACEBOOK]

        assert spec.name == "Facebook"
        assert spec.max_size_mb == 2.0  # Stricter limit
        assert spec.format == "html"

    def test_google_spec(self):
        """Test Google network spec (ZIP format)."""
        spec = NETWORK_SPECS[AdNetwork.GOOGLE]

        assert spec.name == "Google Ads"
        assert spec.format == "zip"


# =============================================================================
# PlayableAsset Tests
# =============================================================================


class TestPlayableAsset:
    """Tests for PlayableAsset dataclass."""

    def test_create_asset(self):
        """Test creating a PlayableAsset."""
        asset = PlayableAsset(
            name="test_asset",
            data_uri="data:image/png;base64,ABC123",
            original_size=1000,
            processed_size=800,
            width=512,
            height=512,
        )

        assert asset.name == "test_asset"
        assert asset.data_uri.startswith("data:image/png;base64,")
        assert asset.processed_size < asset.original_size


# =============================================================================
# PlayableAssembler Tests
# =============================================================================


class TestPlayableAssembler:
    """Tests for PlayableAssembler class."""

    def test_assembler_initialization(self):
        """Test PlayableAssembler initialization."""
        assembler = PlayableAssembler()
        assert assembler is not None

    def test_validate_for_network_size_check(self):
        """Test network validation includes size check."""
        assembler = PlayableAssembler()

        # Small HTML should pass IronSource (5MB limit)
        small_html = "<html><body>Test</body></html>"
        validation = assembler.validate_for_network(small_html, AdNetwork.IRONSOURCE)

        assert "size_ok" in validation
        assert validation["size_ok"] is True

    def test_validate_for_network_mraid_check(self):
        """Test network validation includes MRAID check."""
        assembler = PlayableAssembler()

        # HTML without MRAID
        html_no_mraid = "<html><body>Test</body></html>"
        validation = assembler.validate_for_network(html_no_mraid, AdNetwork.IRONSOURCE)

        assert "has_mraid" in validation

    def test_validate_for_network_store_url_check(self):
        """Test network validation includes store URL check."""
        assembler = PlayableAssembler()

        html_with_store = "<html><body>https://apps.apple.com/test</body></html>"
        validation = assembler.validate_for_network(html_with_store, AdNetwork.UNITY)

        assert "has_store_url" in validation


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
