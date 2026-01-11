"""
End-to-End Tests for Playable Ad Generator v2.0

These tests verify the complete pipeline works correctly.
Demo mode tests run without API keys.
Full pipeline tests require API keys (skip if not configured).
"""

import os
import sys
import tempfile
from pathlib import Path

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.playable_factory import PlayableFactory, PlayableOutput, FactoryConfig
from src.templates.registry import MechanicType, TEMPLATE_REGISTRY, get_template
from src.assembly.builder import PlayableBuilder, PlayableConfig, PlayableResult
from src.generation.game_asset_generator import GeneratedAssetSet
from src.generation.sound_generator import SoundGenerator, PROCEDURAL_SOUNDS_JS


# =============================================================================
# Demo Mode Tests (No API Keys Required)
# =============================================================================

class TestDemoMode:
    """Tests that run without API keys using fallback graphics."""

    def test_demo_match3(self):
        """Test demo mode creates valid match-3 playable."""
        factory = PlayableFactory()
        result = factory.create_demo(
            mechanic_type=MechanicType.MATCH3,
            game_name="Demo Match-3"
        )

        assert result is not None
        assert result.is_valid, f"Validation errors: {result.validation_errors}"
        assert result.mechanic_type == MechanicType.MATCH3
        assert result.game_name == "Demo Match-3"
        assert result.file_size_bytes > 0
        assert result.file_size_mb < 5.0  # Under size limit
        assert "Match3Scene" in result.html
        assert "openStoreUrl" in result.html

    def test_demo_runner(self):
        """Test demo mode creates valid runner playable."""
        factory = PlayableFactory()
        result = factory.create_demo(
            mechanic_type=MechanicType.RUNNER,
            game_name="Demo Runner"
        )

        assert result is not None
        assert result.is_valid
        assert result.mechanic_type == MechanicType.RUNNER
        assert "RunnerScene" in result.html

    def test_demo_tapper(self):
        """Test demo mode creates valid tapper playable."""
        factory = PlayableFactory()
        result = factory.create_demo(
            mechanic_type=MechanicType.TAPPER,
            game_name="Demo Tapper"
        )

        assert result is not None
        assert result.is_valid
        assert result.mechanic_type == MechanicType.TAPPER
        assert "TapperScene" in result.html

    def test_demo_save_html(self):
        """Test saving demo playable as HTML file."""
        factory = PlayableFactory()
        result = factory.create_demo(mechanic_type=MechanicType.MATCH3)

        with tempfile.TemporaryDirectory() as tmpdir:
            html_path = Path(tmpdir) / "test.html"
            result.save(html_path)

            assert html_path.exists()
            content = html_path.read_text()
            assert "<!DOCTYPE html>" in content
            assert "Phaser" in content

    def test_demo_save_zip(self):
        """Test saving demo playable as ZIP file."""
        factory = PlayableFactory()
        result = factory.create_demo(mechanic_type=MechanicType.RUNNER)

        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = Path(tmpdir) / "test.zip"
            result.save_zip(zip_path)

            assert zip_path.exists()
            assert zip_path.stat().st_size > 0

            # Verify ZIP contents
            import zipfile
            with zipfile.ZipFile(zip_path, 'r') as zf:
                assert "index.html" in zf.namelist()


# =============================================================================
# Template Registry Tests
# =============================================================================

class TestTemplateRegistry:
    """Tests for template registry functionality."""

    def test_all_mechanics_registered(self):
        """Verify all supported mechanics have templates."""
        supported = [MechanicType.MATCH3, MechanicType.RUNNER, MechanicType.TAPPER]
        for mechanic in supported:
            template = get_template(mechanic)
            assert template is not None, f"No template for {mechanic.value}"
            assert template.get_template_path().exists(), f"Template file missing for {mechanic.value}"

    def test_template_has_required_assets(self):
        """Verify templates define required assets."""
        for mechanic, template in TEMPLATE_REGISTRY.items():
            if mechanic == MechanicType.UNKNOWN:
                continue
            assert len(template.required_assets) > 0, f"{mechanic.value} has no required assets"

    def test_template_files_exist(self):
        """Verify all template HTML files exist."""
        for mechanic, template in TEMPLATE_REGISTRY.items():
            if mechanic == MechanicType.UNKNOWN:
                continue
            path = template.get_template_path()
            assert path.exists(), f"Template file missing: {path}"

    def test_template_has_phaser_config(self):
        """Verify templates contain Phaser configuration."""
        for mechanic, template in TEMPLATE_REGISTRY.items():
            if mechanic == MechanicType.UNKNOWN:
                continue
            path = template.get_template_path()
            content = path.read_text()
            assert "Phaser.Game" in content, f"{mechanic.value} missing Phaser.Game"
            assert "${PHASER_SCRIPT}" in content, f"{mechanic.value} missing PHASER_SCRIPT placeholder"


# =============================================================================
# Builder Tests
# =============================================================================

class TestPlayableBuilder:
    """Tests for playable assembly."""

    def test_build_with_empty_assets(self):
        """Test building with empty asset set (uses fallbacks)."""
        from src.analysis.game_analyzer import GameAnalysis, VisualStyle

        analysis = GameAnalysis(
            game_name="Test Game",
            publisher="Test",
            mechanic_type=MechanicType.MATCH3,
            mechanic_confidence=1.0,
            mechanic_reasoning="Test",
            visual_style=VisualStyle(
                art_type="cartoon",
                color_palette=["#FF0000", "#00FF00"],
                theme="casual",
                mood="playful",
            ),
            assets_needed=[],
            recommended_template="match3",
            template_config={},
            core_loop_description="Test game",
            hook_suggestion="Play Now!",
            cta_suggestion="Download!",
        )

        assets = GeneratedAssetSet(
            game_name="Test Game",
            mechanic_type=MechanicType.MATCH3,
            style_id="test",
        )

        config = PlayableConfig(
            game_name="Test Game",
            store_url="https://example.com",
        )

        builder = PlayableBuilder()
        result = builder.build(analysis, assets, config)

        assert result is not None
        assert result.file_size_bytes > 0
        assert "openStoreUrl" in result.html

    def test_config_substitution(self):
        """Test that config values are properly substituted."""
        from src.analysis.game_analyzer import GameAnalysis, VisualStyle

        analysis = GameAnalysis(
            game_name="Substitution Test",
            publisher="Test",
            mechanic_type=MechanicType.TAPPER,
            mechanic_confidence=1.0,
            mechanic_reasoning="Test",
            visual_style=VisualStyle(
                art_type="cartoon",
                color_palette=["#FF0000"],
                theme="casual",
                mood="playful",
            ),
            assets_needed=[],
            recommended_template="tapper",
            template_config={},
            core_loop_description="Test",
            hook_suggestion="Test Hook!",
            cta_suggestion="Test CTA!",
        )

        assets = GeneratedAssetSet(
            game_name="Substitution Test",
            mechanic_type=MechanicType.TAPPER,
            style_id="test",
        )

        config = PlayableConfig(
            game_name="Substitution Test",
            title="My Title",
            store_url="https://test.example.com",
            hook_text="Custom Hook",
            cta_text="Custom CTA",
            background_color="#123456",
        )

        builder = PlayableBuilder()
        result = builder.build(analysis, assets, config)

        # Check substitutions
        assert "My Title" in result.html
        assert "https://test.example.com" in result.html
        assert "Custom Hook" in result.html
        assert "Custom CTA" in result.html
        assert "#123456" in result.html

        # Verify no unsubstituted placeholders remain
        assert "${" not in result.html, "Unsubstituted placeholders found"


# =============================================================================
# Sound Generator Tests
# =============================================================================

class TestSoundGenerator:
    """Tests for procedural sound effects."""

    def test_procedural_sounds_script_exists(self):
        """Verify procedural sounds JavaScript is available."""
        assert PROCEDURAL_SOUNDS_JS is not None
        assert len(PROCEDURAL_SOUNDS_JS) > 100
        assert "SoundFX" in PROCEDURAL_SOUNDS_JS

    def test_sound_integration_for_mechanics(self):
        """Verify sound integrations exist for all mechanics."""
        generator = SoundGenerator()

        mechanics = ["match3", "runner", "tapper"]
        for mechanic in mechanics:
            integration = generator.get_sound_integration_for_mechanic(mechanic)
            assert integration is not None
            assert len(integration) > 0


# =============================================================================
# Network Compatibility Tests
# =============================================================================

class TestNetworkCompatibility:
    """Tests for ad network size limits."""

    def test_demo_under_5mb(self):
        """Verify demo playables are under 5MB limit."""
        factory = PlayableFactory()

        for mechanic in [MechanicType.MATCH3, MechanicType.RUNNER, MechanicType.TAPPER]:
            result = factory.create_demo(mechanic_type=mechanic)
            assert result.file_size_mb < 5.0, f"{mechanic.value} exceeds 5MB: {result.file_size_formatted}"

    def test_demo_under_2mb_for_facebook(self):
        """Verify demo playables could work with Facebook's 2MB limit."""
        factory = PlayableFactory()

        for mechanic in [MechanicType.MATCH3, MechanicType.RUNNER, MechanicType.TAPPER]:
            result = factory.create_demo(mechanic_type=mechanic)
            # Demo mode uses fallback graphics, should be well under 2MB
            assert result.file_size_mb < 2.0, f"{mechanic.value} exceeds 2MB: {result.file_size_formatted}"


# =============================================================================
# Full Pipeline Tests (Requires API Keys)
# =============================================================================

@pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY") or not os.getenv("LAYER_API_KEY"),
    reason="API keys not configured"
)
class TestFullPipeline:
    """Tests that require API keys."""

    def test_game_analysis(self):
        """Test Claude Vision game analysis with real screenshot."""
        # This would require a real screenshot
        pytest.skip("Requires sample screenshot")

    def test_asset_generation(self):
        """Test Layer.ai asset generation."""
        # This would require Layer.ai credits
        pytest.skip("Requires Layer.ai credits")


# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
