"""
Tests for Game Asset Generator (v2.0)

Test coverage for asset generation functionality using
the v2.0 API (src.generation.game_asset_generator).
"""

import pytest
from unittest.mock import Mock, patch

from src.generation.game_asset_generator import (
    GameAssetGenerator,
    GeneratedAssetSet,
    GeneratedAsset,
)
from src.templates.registry import MechanicType, TEMPLATE_REGISTRY, AssetRequirement
from src.layer_client import StyleConfig
from src.analysis.game_analyzer import GameAnalysis, VisualStyle, AssetNeed


# =============================================================================
# GeneratedAsset Tests
# =============================================================================


class TestGeneratedAsset:
    """Tests for GeneratedAsset dataclass."""

    def test_create_valid_asset(self):
        """Test creating a valid GeneratedAsset."""
        asset = GeneratedAsset(
            key="tile_1",
            prompt="red candy piece",
            image_url="https://example.com/image.png",
            image_data=b"fake_image_data",
            base64_data="data:image/png;base64,abc123",
            generation_time=2.5,
            width=256,
            height=256,
        )

        assert asset.key == "tile_1"
        assert asset.prompt == "red candy piece"
        assert asset.image_url == "https://example.com/image.png"
        assert asset.generation_time == 2.5
        assert asset.is_valid is True
        assert asset.error is None

    def test_create_error_asset(self):
        """Test creating an asset with an error."""
        asset = GeneratedAsset(
            key="tile_1",
            prompt="red candy piece",
            image_url=None,
            image_data=None,
            base64_data=None,
            generation_time=0,
            error="Generation failed",
        )

        assert asset.is_valid is False
        assert asset.error == "Generation failed"


# =============================================================================
# GeneratedAssetSet Tests
# =============================================================================


class TestGeneratedAssetSet:
    """Tests for GeneratedAssetSet dataclass."""

    def test_create_empty_set(self):
        """Test creating an empty GeneratedAssetSet."""
        asset_set = GeneratedAssetSet(
            game_name="Test Game",
            mechanic_type=MechanicType.MATCH3,
            style_id="test-style",
        )

        assert asset_set.game_name == "Test Game"
        assert asset_set.mechanic_type == MechanicType.MATCH3
        assert len(asset_set.assets) == 0
        assert asset_set.total_generation_time == 0.0
        assert asset_set.valid_count == 0

    def test_asset_set_with_assets(self):
        """Test GeneratedAssetSet with valid and invalid assets."""
        asset_set = GeneratedAssetSet(
            game_name="Test Game",
            mechanic_type=MechanicType.MATCH3,
            style_id="test-style",
        )

        valid_asset = GeneratedAsset(
            key="tile_1",
            prompt="red candy",
            image_url="https://example.com/1.png",
            image_data=b"data",
            base64_data="data:image/png;base64,abc",
            generation_time=2.0,
        )

        error_asset = GeneratedAsset(
            key="tile_2",
            prompt="blue candy",
            image_url=None,
            image_data=None,
            base64_data=None,
            generation_time=0,
            error="Failed",
        )

        asset_set.assets["tile_1"] = valid_asset
        asset_set.assets["tile_2"] = error_asset
        asset_set.total_generation_time = 2.0

        assert len(asset_set.assets) == 2
        assert asset_set.valid_count == 1
        assert asset_set.all_valid is False

    def test_get_asset(self):
        """Test getting an asset by key."""
        asset_set = GeneratedAssetSet(
            game_name="Test",
            mechanic_type=MechanicType.TAPPER,
            style_id="test",
        )

        asset = GeneratedAsset(
            key="target",
            prompt="tappable circle",
            image_url="https://example.com/1.png",
            image_data=b"data",
            base64_data="data:image/png;base64,abc",
            generation_time=1.5,
        )
        asset_set.assets["target"] = asset

        assert asset_set.get_asset("target") is asset
        assert asset_set.get_asset("nonexistent") is None

    def test_get_asset_manifest(self):
        """Test asset manifest generation for template embedding."""
        asset_set = GeneratedAssetSet(
            game_name="Test",
            mechanic_type=MechanicType.MATCH3,
            style_id="test",
        )

        valid_asset = GeneratedAsset(
            key="tile_1",
            prompt="candy",
            image_url="https://example.com/1.png",
            image_data=b"data",
            base64_data="data:image/png;base64,abc",
            generation_time=1.0,
        )
        invalid_asset = GeneratedAsset(
            key="tile_2",
            prompt="candy",
            image_url=None,
            image_data=None,
            base64_data=None,
            generation_time=0,
            error="Failed",
        )

        asset_set.assets["tile_1"] = valid_asset
        asset_set.assets["tile_2"] = invalid_asset

        manifest = asset_set.get_asset_manifest()

        assert "tile_1" in manifest
        assert "tile_2" not in manifest
        assert manifest["tile_1"] == "data:image/png;base64,abc"


# =============================================================================
# Template Asset Requirements Tests
# =============================================================================


class TestTemplateAssetRequirements:
    """Tests for template asset requirements."""

    def test_all_registered_templates_have_assets(self):
        """Test that all registered templates define required assets."""
        for mechanic_type, template_info in TEMPLATE_REGISTRY.items():
            assert len(template_info.required_assets) > 0, (
                f"Template {mechanic_type.value} has no required assets"
            )

    def test_match3_template_requirements(self):
        """Test Match-3 template has expected asset keys."""
        template = TEMPLATE_REGISTRY.get(MechanicType.MATCH3)
        assert template is not None

        asset_keys = {a.key for a in template.required_assets}
        assert "tile_1" in asset_keys
        assert "background" in asset_keys

    def test_runner_template_requirements(self):
        """Test Runner template has expected asset keys."""
        template = TEMPLATE_REGISTRY.get(MechanicType.RUNNER)
        assert template is not None

        asset_keys = {a.key for a in template.required_assets}
        assert "player" in asset_keys
        assert "background" in asset_keys

    def test_tapper_template_requirements(self):
        """Test Tapper template has expected asset keys."""
        template = TEMPLATE_REGISTRY.get(MechanicType.TAPPER)
        assert template is not None

        asset_keys = {a.key for a in template.required_assets}
        assert "target" in asset_keys
        assert "background" in asset_keys


# =============================================================================
# GameAssetGenerator Tests (Mocked)
# =============================================================================


class TestGameAssetGenerator:
    """Tests for GameAssetGenerator class."""

    def test_generator_initialization(self):
        """Test GameAssetGenerator initialization with mock client."""
        mock_client = Mock()
        generator = GameAssetGenerator(layer_client=mock_client)

        assert generator is not None
        assert generator.client is mock_client
        assert generator.max_dimension == 512

    def test_generator_custom_dimension(self):
        """Test GameAssetGenerator with custom max dimension."""
        mock_client = Mock()
        generator = GameAssetGenerator(layer_client=mock_client, max_dimension=256)

        assert generator.max_dimension == 256

    def test_data_uri_png(self):
        """Test PNG data URI generation."""
        mock_client = Mock()
        generator = GameAssetGenerator(layer_client=mock_client)

        # PNG magic bytes
        png_data = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100
        uri = generator._to_data_uri(png_data)

        assert uri.startswith("data:image/png;base64,")

    def test_data_uri_jpeg(self):
        """Test JPEG data URI generation."""
        mock_client = Mock()
        generator = GameAssetGenerator(layer_client=mock_client)

        # JPEG magic bytes
        jpeg_data = b'\xff\xd8' + b'\x00' * 100
        uri = generator._to_data_uri(jpeg_data)

        assert uri.startswith("data:image/jpeg;base64,")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
