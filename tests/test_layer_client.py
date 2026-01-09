"""
Tests for Layer.ai API Client

Basic test coverage for core functionality.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from dataclasses import asdict

from src.layer_client import (
    LayerClient,
    LayerClientSync,
    StyleConfig,
    StyleRecipe,
    WorkspaceInfo,
    GeneratedImage,
    GenerationStatus,
    LayerAPIError,
    InsufficientCreditsError,
)


# =============================================================================
# StyleConfig Tests
# =============================================================================


class TestStyleConfig:
    """Tests for StyleConfig dataclass."""

    def test_create_style_config(self):
        """Test creating a StyleConfig."""
        config = StyleConfig(
            name="Test Style",
            description="Test description",
            style_keywords=["cartoon", "vibrant"],
            negative_keywords=["dark", "realistic"],
        )

        assert config.name == "Test Style"
        assert config.description == "Test description"
        assert "cartoon" in config.style_keywords
        assert "dark" in config.negative_keywords

    def test_to_prompt_prefix(self):
        """Test prompt prefix generation."""
        config = StyleConfig(
            name="Test",
            style_keywords=["cartoon", "vibrant", "colorful"],
        )

        prefix = config.to_prompt_prefix()
        assert prefix == "cartoon, vibrant, colorful, "

    def test_to_prompt_prefix_empty(self):
        """Test prompt prefix with no keywords."""
        config = StyleConfig(name="Test")
        assert config.to_prompt_prefix() == ""

    def test_to_negative_prompt(self):
        """Test negative prompt generation."""
        config = StyleConfig(
            name="Test",
            negative_keywords=["dark", "realistic"],
        )

        negative = config.to_negative_prompt()
        assert negative == "dark, realistic"

    def test_to_negative_prompt_empty(self):
        """Test negative prompt with no keywords."""
        config = StyleConfig(name="Test")
        assert config.to_negative_prompt() == ""


# =============================================================================
# StyleRecipe Tests
# =============================================================================


class TestStyleRecipe:
    """Tests for StyleRecipe dataclass."""

    def test_create_style_recipe(self):
        """Test creating a StyleRecipe."""
        recipe = StyleRecipe(
            style_name="Casual Match-3",
            prefix=["cartoon", "2D"],
            technical=["cel-shaded", "clean lines"],
            negative=["realistic", "dark"],
            palette_primary="#FF6B6B",
            palette_accent="#4ECDC4",
        )

        assert recipe.style_name == "Casual Match-3"
        assert "cartoon" in recipe.prefix
        assert "cel-shaded" in recipe.technical
        assert recipe.palette_primary == "#FF6B6B"

    def test_to_style_config(self):
        """Test converting StyleRecipe to StyleConfig."""
        recipe = StyleRecipe(
            style_name="Test Style",
            prefix=["cartoon"],
            technical=["cel-shaded"],
            negative=["dark"],
        )

        config = recipe.to_style_config()

        assert isinstance(config, StyleConfig)
        assert config.name == "Test Style"
        assert "cartoon" in config.style_keywords
        assert "cel-shaded" in config.style_keywords
        assert "dark" in config.negative_keywords

    def test_to_dict(self):
        """Test converting StyleRecipe to dictionary."""
        recipe = StyleRecipe(
            style_name="Test",
            prefix=["a", "b"],
            technical=["c"],
            negative=["d"],
            palette_primary="#FF0000",
            palette_accent="#00FF00",
        )

        d = recipe.to_dict()

        assert d["styleName"] == "Test"
        assert d["prefix"] == ["a", "b"]
        assert d["technical"] == ["c"]
        assert d["negative"] == ["d"]
        assert d["palette"]["primary"] == "#FF0000"
        assert d["palette"]["accent"] == "#00FF00"

    def test_from_dict(self):
        """Test creating StyleRecipe from dictionary."""
        data = {
            "styleName": "From Dict",
            "prefix": ["x", "y"],
            "technical": ["z"],
            "negative": ["n"],
            "palette": {
                "primary": "#111111",
                "accent": "#222222",
            },
        }

        recipe = StyleRecipe.from_dict(data)

        assert recipe.style_name == "From Dict"
        assert recipe.prefix == ["x", "y"]
        assert recipe.palette_primary == "#111111"


# =============================================================================
# WorkspaceInfo Tests
# =============================================================================


class TestWorkspaceInfo:
    """Tests for WorkspaceInfo dataclass."""

    def test_has_credits_sufficient(self):
        """Test has_credits when credits are sufficient."""
        with patch("src.layer_client.get_settings") as mock_settings:
            mock_settings.return_value.min_credits_required = 50

            info = WorkspaceInfo(
                workspace_id="test",
                credits_available=100,
            )

            assert info.has_credits is True

    def test_has_credits_insufficient(self):
        """Test has_credits when credits are insufficient."""
        with patch("src.layer_client.get_settings") as mock_settings:
            mock_settings.return_value.min_credits_required = 50

            info = WorkspaceInfo(
                workspace_id="test",
                credits_available=30,
            )

            assert info.has_credits is False


# =============================================================================
# GeneratedImage Tests
# =============================================================================


class TestGeneratedImage:
    """Tests for GeneratedImage dataclass."""

    def test_create_generated_image(self):
        """Test creating a GeneratedImage."""
        image = GeneratedImage(
            task_id="task-123",
            status=GenerationStatus.COMPLETED,
            image_url="https://example.com/image.png",
            image_id="img-456",
        )

        assert image.task_id == "task-123"
        assert image.status == GenerationStatus.COMPLETED
        assert image.image_url == "https://example.com/image.png"

    def test_generation_status_values(self):
        """Test GenerationStatus enum values."""
        assert GenerationStatus.PENDING == "PENDING"
        assert GenerationStatus.PROCESSING == "PROCESSING"
        assert GenerationStatus.COMPLETED == "COMPLETED"
        assert GenerationStatus.FAILED == "FAILED"


# =============================================================================
# LayerClient Tests (Mocked)
# =============================================================================


class TestLayerClient:
    """Tests for LayerClient class."""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings for tests."""
        with patch("src.layer_client.get_settings") as mock:
            mock.return_value.layer_api_url = "https://api.test.com/graphql"
            mock.return_value.layer_api_key = "test-key"
            mock.return_value.layer_workspace_id = "test-workspace"
            mock.return_value.min_credits_required = 50
            mock.return_value.forge_poll_timeout = 60
            yield mock

    def test_client_initialization(self, mock_settings):
        """Test LayerClient initialization."""
        client = LayerClient()

        assert client.api_url == "https://api.test.com/graphql"
        assert client.api_key == "test-key"
        assert client.workspace_id == "test-workspace"

    def test_client_custom_params(self, mock_settings):
        """Test LayerClient with custom parameters."""
        client = LayerClient(
            api_url="https://custom.api.com",
            api_key="custom-key",
            workspace_id="custom-workspace",
        )

        assert client.api_url == "https://custom.api.com"
        assert client.api_key == "custom-key"
        assert client.workspace_id == "custom-workspace"


# =============================================================================
# Exception Tests
# =============================================================================


class TestExceptions:
    """Tests for custom exceptions."""

    def test_layer_api_error(self):
        """Test LayerAPIError."""
        error = LayerAPIError("Test error message")
        assert str(error) == "Test error message"

    def test_insufficient_credits_error(self):
        """Test InsufficientCreditsError."""
        error = InsufficientCreditsError("Not enough credits")
        assert str(error) == "Not enough credits"
        assert isinstance(error, LayerAPIError)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
