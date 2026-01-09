"""
Tests for Asset Forger

Basic test coverage for asset generation functionality.
"""

import pytest
from unittest.mock import Mock, patch

from src.forge.asset_forger import (
    AssetGenerator,
    AssetSet,
    GeneratedAsset,
    AssetType,
    AssetCategory,
    AssetPreset,
    ASSET_PRESETS,
)
from src.layer_client import StyleConfig


# =============================================================================
# AssetType Tests
# =============================================================================


class TestAssetType:
    """Tests for AssetType enum."""

    def test_hook_assets(self):
        """Test hook asset types exist."""
        assert AssetType.HOOK_CHARACTER is not None
        assert AssetType.HOOK_ITEM is not None
        assert AssetType.HOOK_BACKGROUND is not None

    def test_gameplay_assets(self):
        """Test gameplay asset types exist."""
        assert AssetType.GAMEPLAY_BACKGROUND is not None
        assert AssetType.GAMEPLAY_ELEMENT is not None
        assert AssetType.GAMEPLAY_COLLECTIBLE is not None
        assert AssetType.GAMEPLAY_OBSTACLE is not None

    def test_cta_assets(self):
        """Test CTA asset types exist."""
        assert AssetType.CTA_BUTTON is not None
        assert AssetType.CTA_BANNER is not None
        assert AssetType.CTA_ICON is not None


# =============================================================================
# AssetCategory Tests
# =============================================================================


class TestAssetCategory:
    """Tests for AssetCategory enum."""

    def test_category_values(self):
        """Test category enum values."""
        assert AssetCategory.HOOK == "hook"
        assert AssetCategory.GAMEPLAY == "gameplay"
        assert AssetCategory.CTA == "cta"


# =============================================================================
# AssetPreset Tests
# =============================================================================


class TestAssetPresets:
    """Tests for asset presets."""

    def test_all_asset_types_have_presets(self):
        """Test all AssetType values have corresponding presets."""
        for asset_type in AssetType:
            assert asset_type in ASSET_PRESETS, f"Missing preset for {asset_type}"

    def test_preset_has_required_fields(self):
        """Test presets have all required fields."""
        for asset_type, preset in ASSET_PRESETS.items():
            assert isinstance(preset, AssetPreset)
            assert preset.name is not None
            assert preset.category is not None
            assert len(preset.prompts) > 0

    def test_hook_character_preset(self):
        """Test HOOK_CHARACTER preset details."""
        preset = ASSET_PRESETS[AssetType.HOOK_CHARACTER]

        assert preset.name == "Character"
        assert preset.category == AssetCategory.HOOK
        assert any("character" in p.lower() for p in preset.prompts)

    def test_gameplay_background_preset(self):
        """Test GAMEPLAY_BACKGROUND preset details."""
        preset = ASSET_PRESETS[AssetType.GAMEPLAY_BACKGROUND]

        assert preset.name == "Background"
        assert preset.category == AssetCategory.GAMEPLAY
        assert any("background" in p.lower() for p in preset.prompts)

    def test_cta_button_preset(self):
        """Test CTA_BUTTON preset details."""
        preset = ASSET_PRESETS[AssetType.CTA_BUTTON]

        assert preset.name == "Button"
        assert preset.category == AssetCategory.CTA
        assert any("button" in p.lower() for p in preset.prompts)


# =============================================================================
# GeneratedAsset Tests
# =============================================================================


class TestGeneratedAsset:
    """Tests for GeneratedAsset dataclass."""

    def test_create_generated_asset(self):
        """Test creating a GeneratedAsset."""
        asset = GeneratedAsset(
            asset_type=AssetType.HOOK_CHARACTER,
            category=AssetCategory.HOOK,
            image_url="https://example.com/image.png",
            image_id="img-123",
            prompt="test prompt",
            generation_time=2.5,
        )

        assert asset.asset_type == AssetType.HOOK_CHARACTER
        assert asset.category == AssetCategory.HOOK
        assert asset.image_url == "https://example.com/image.png"
        assert asset.generation_time == 2.5


# =============================================================================
# AssetSet Tests
# =============================================================================


class TestAssetSet:
    """Tests for AssetSet dataclass."""

    def test_create_empty_asset_set(self):
        """Test creating an empty AssetSet."""
        style = StyleConfig(name="Test")
        asset_set = AssetSet(style=style)

        assert asset_set.style == style
        assert len(asset_set.assets) == 0
        assert asset_set.total_generation_time == 0.0

    def test_asset_set_with_assets(self):
        """Test AssetSet with assets."""
        style = StyleConfig(name="Test")
        asset_set = AssetSet(style=style)

        asset1 = GeneratedAsset(
            asset_type=AssetType.HOOK_CHARACTER,
            category=AssetCategory.HOOK,
            image_url="https://example.com/1.png",
            prompt="test",
            generation_time=2.0,
        )

        asset2 = GeneratedAsset(
            asset_type=AssetType.GAMEPLAY_BACKGROUND,
            category=AssetCategory.GAMEPLAY,
            image_url="https://example.com/2.png",
            prompt="test",
            generation_time=3.0,
        )

        asset_set.assets.append(asset1)
        asset_set.assets.append(asset2)
        asset_set.total_generation_time = 5.0

        assert len(asset_set.assets) == 2
        assert asset_set.total_generation_time == 5.0

    def test_asset_set_get_by_category(self):
        """Test filtering assets by category."""
        style = StyleConfig(name="Test")
        asset_set = AssetSet(style=style)

        hook_asset = GeneratedAsset(
            asset_type=AssetType.HOOK_CHARACTER,
            category=AssetCategory.HOOK,
            image_url="https://example.com/1.png",
            prompt="test",
            generation_time=1.0,
        )

        gameplay_asset = GeneratedAsset(
            asset_type=AssetType.GAMEPLAY_BACKGROUND,
            category=AssetCategory.GAMEPLAY,
            image_url="https://example.com/2.png",
            prompt="test",
            generation_time=1.0,
        )

        asset_set.assets.extend([hook_asset, gameplay_asset])

        hook_assets = asset_set.get_by_category(AssetCategory.HOOK)
        gameplay_assets = asset_set.get_by_category(AssetCategory.GAMEPLAY)

        assert len(hook_assets) == 1
        assert len(gameplay_assets) == 1
        assert hook_assets[0].category == AssetCategory.HOOK


# =============================================================================
# AssetGenerator Tests (Mocked)
# =============================================================================


class TestAssetGenerator:
    """Tests for AssetGenerator class."""

    @pytest.fixture
    def mock_layer_client(self):
        """Mock LayerClientSync for tests."""
        with patch("src.forge.asset_forger.LayerClientSync") as mock:
            mock_instance = Mock()
            mock_instance.check_credits.return_value = Mock(credits_available=100)
            mock.return_value = mock_instance
            yield mock_instance

    def test_generator_initialization(self, mock_layer_client):
        """Test AssetGenerator initialization."""
        generator = AssetGenerator()
        assert generator is not None

    def test_set_style(self, mock_layer_client):
        """Test setting style on generator."""
        generator = AssetGenerator()
        style = StyleConfig(
            name="Test Style",
            style_keywords=["cartoon", "vibrant"],
        )

        generator.set_style(style)

        assert generator._style == style


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
