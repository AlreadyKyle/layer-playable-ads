"""
Game Analyzer - Uses Claude Vision to analyze game screenshots.

This module extracts:
- Game mechanic type (match-3, runner, tapper, etc.)
- Visual style (art type, colors, theme)
- Required assets for the playable ad
- Recommended template and configuration
"""

import base64
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import anthropic

from src.templates.registry import MechanicType, TEMPLATE_REGISTRY
from .models import ConfidenceLevel


@dataclass
class VisualStyle:
    """Visual style extracted from game screenshots."""

    art_type: str  # cartoon, realistic, pixel, minimalist, etc.
    color_palette: list[str]  # Hex colors
    theme: str  # fantasy, sci-fi, casual, etc.
    mood: str  # playful, intense, relaxing, etc.

    def to_prompt_prefix(self) -> str:
        """Convert style to prompt prefix for asset generation."""
        return f"{self.art_type} style, {self.theme} theme, {self.mood} mood"


@dataclass
class AssetNeed:
    """A specific asset needed for the playable ad."""

    key: str  # Template asset key (e.g., "tile_1", "player")
    description: str  # Detailed description for prompt
    game_specific_prompt: str  # Prompt based on game analysis


@dataclass
class GameAnalysis:
    """Complete analysis of a game from screenshots."""

    game_name: str
    publisher: Optional[str]
    mechanic_type: MechanicType
    mechanic_confidence: float  # 0.0 to 1.0
    mechanic_reasoning: str

    visual_style: VisualStyle
    assets_needed: list[AssetNeed]

    recommended_template: str  # Template key
    template_config: dict  # Suggested configuration

    core_loop_description: str  # How the game plays
    hook_suggestion: str  # Suggested hook text
    cta_suggestion: str  # Suggested CTA text

    raw_analysis: dict = field(default_factory=dict)  # Full Claude response

    @property
    def confidence_level(self) -> ConfidenceLevel:
        """Get confidence level enum."""
        if self.mechanic_confidence >= 0.8:
            return ConfidenceLevel.HIGH
        elif self.mechanic_confidence >= 0.5:
            return ConfidenceLevel.MEDIUM
        return ConfidenceLevel.LOW

    def is_supported(self) -> bool:
        """Check if the detected mechanic has a template."""
        return self.mechanic_type in TEMPLATE_REGISTRY


class GameAnalyzer:
    """Analyzes game screenshots using Claude Vision."""

    ANALYSIS_PROMPT = """You are a mobile game analyst and playable ad specialist.

Analyze these game screenshots and extract the following information:

1. GAME IDENTIFICATION
   - What is the name of this game (if visible)?
   - Who is the publisher (if visible)?

2. CORE MECHANIC CLASSIFICATION
   Choose ONE primary mechanic from:
   - MATCH3: Games where you match 3+ similar items by swapping (Candy Crush, Bejeweled)
   - RUNNER: Endless runner games with lane-switching/jumping (Subway Surfers, Temple Run)
   - TAPPER: Idle/clicker games where tapping accumulates resources (Cookie Clicker)
   - MERGER: Games where dragging items together creates new ones (2048, Merge Dragons)
   - PUZZLE: Block/shape fitting puzzles (Tetris, Block Blast)
   - SHOOTER: Aim and launch physics games (Angry Birds)
   - UNKNOWN: If none of the above fit

   Explain your reasoning for the classification.
   Rate your confidence from 0.0 to 1.0.

3. VISUAL STYLE
   - Art type: cartoon, realistic, pixel, minimalist, 3D, etc.
   - Color palette: List 4-6 dominant hex colors
   - Theme: fantasy, sci-fi, casual, medieval, modern, etc.
   - Mood: playful, intense, relaxing, competitive, etc.

4. CORE LOOP DESCRIPTION
   In 1-2 sentences, describe the primary player action and reward cycle.
   Focus on the SINGLE most important interaction.

5. ASSETS NEEDED
   Based on the mechanic type, list the specific assets needed for a playable ad.
   For each asset, provide a detailed visual description based on what you see.

   For MATCH3:
   - tile_1, tile_2, tile_3, tile_4: The matching pieces
   - background: The game background

   For RUNNER:
   - player: The main character
   - obstacle: Things to avoid
   - collectible: Items to collect
   - background: The environment

   For TAPPER:
   - target: The main tappable element
   - bonus: Bonus items that appear
   - background: The game background

6. PLAYABLE AD SUGGESTIONS
   - hook_text: A catchy 3-5 word hook (e.g., "Match the candies!")
   - cta_text: Call-to-action text (e.g., "Download FREE")
   - template_config: Any specific configuration (grid size, speed, etc.)

Respond in this exact JSON format:
```json
{
  "game_name": "Name or Unknown",
  "publisher": "Publisher or null",
  "mechanic_type": "MATCH3|RUNNER|TAPPER|MERGER|PUZZLE|SHOOTER|UNKNOWN",
  "mechanic_confidence": 0.0-1.0,
  "mechanic_reasoning": "Explanation of why this mechanic type",
  "visual_style": {
    "art_type": "cartoon",
    "color_palette": ["#FF6B6B", "#4ECDC4", "#FFE66D", "#95E1D3"],
    "theme": "fantasy",
    "mood": "playful"
  },
  "core_loop_description": "Player swaps adjacent tiles to match 3 or more.",
  "assets_needed": [
    {
      "key": "tile_1",
      "description": "Red round candy with glossy surface",
      "game_specific_prompt": "red candy piece, round, glossy, cartoon style, game asset"
    }
  ],
  "hook_suggestion": "Match the candies!",
  "cta_suggestion": "Download FREE",
  "template_config": {
    "GRID_WIDTH": 7,
    "GRID_HEIGHT": 9,
    "TILE_TYPES": 4
  }
}
```"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-20250514",
    ):
        """Initialize the game analyzer.

        Args:
            api_key: Anthropic API key. If None, uses ANTHROPIC_API_KEY env var.
            model: Claude model to use for analysis.
        """
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    def analyze_screenshots(
        self,
        screenshots: list[bytes | Path | str],
        game_name_hint: Optional[str] = None,
    ) -> GameAnalysis:
        """Analyze game screenshots to extract mechanics and style.

        Args:
            screenshots: List of screenshot images (bytes, file paths, or base64)
            game_name_hint: Optional hint about the game name

        Returns:
            GameAnalysis with complete game information
        """
        # Prepare images for Claude
        image_content = []
        for screenshot in screenshots:
            image_data = self._prepare_image(screenshot)
            image_content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": image_data,
                },
            })

        # Add hint if provided
        prompt = self.ANALYSIS_PROMPT
        if game_name_hint:
            prompt += f"\n\nHint: The game might be '{game_name_hint}'."

        # Call Claude Vision
        message = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            messages=[
                {
                    "role": "user",
                    "content": [
                        *image_content,
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
        )

        # Parse response
        response_text = message.content[0].text
        return self._parse_analysis(response_text)

    def analyze_from_files(
        self,
        file_paths: list[str | Path],
        game_name_hint: Optional[str] = None,
    ) -> GameAnalysis:
        """Analyze screenshots from file paths.

        Args:
            file_paths: Paths to screenshot image files
            game_name_hint: Optional hint about the game name

        Returns:
            GameAnalysis with complete game information
        """
        screenshots = []
        for path in file_paths:
            path = Path(path)
            if path.exists():
                screenshots.append(path.read_bytes())
            else:
                raise FileNotFoundError(f"Screenshot not found: {path}")

        return self.analyze_screenshots(screenshots, game_name_hint)

    def _prepare_image(self, image: bytes | Path | str) -> str:
        """Convert image to base64 string."""
        if isinstance(image, bytes):
            return base64.standard_b64encode(image).decode("utf-8")
        elif isinstance(image, Path):
            return base64.standard_b64encode(image.read_bytes()).decode("utf-8")
        elif isinstance(image, str):
            # Assume it's already base64 or a file path
            path = Path(image)
            if path.exists():
                return base64.standard_b64encode(path.read_bytes()).decode("utf-8")
            # Assume it's base64
            return image
        else:
            raise ValueError(f"Unsupported image type: {type(image)}")

    def _parse_analysis(self, response_text: str) -> GameAnalysis:
        """Parse Claude's JSON response into GameAnalysis."""
        # Extract JSON from response (handle markdown code blocks)
        json_str = response_text
        if "```json" in response_text:
            start = response_text.find("```json") + 7
            end = response_text.find("```", start)
            json_str = response_text[start:end].strip()
        elif "```" in response_text:
            start = response_text.find("```") + 3
            end = response_text.find("```", start)
            json_str = response_text[start:end].strip()

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            # Fallback: try to extract what we can
            return self._create_fallback_analysis(response_text, str(e))

        # Parse mechanic type
        mechanic_str = data.get("mechanic_type", "UNKNOWN")
        mechanic_type = MechanicType.from_string(mechanic_str)

        # Parse visual style
        style_data = data.get("visual_style", {})
        visual_style = VisualStyle(
            art_type=style_data.get("art_type", "cartoon"),
            color_palette=style_data.get("color_palette", ["#FF6B6B", "#4ECDC4"]),
            theme=style_data.get("theme", "casual"),
            mood=style_data.get("mood", "playful"),
        )

        # Parse assets needed
        assets_needed = []
        for asset_data in data.get("assets_needed", []):
            assets_needed.append(AssetNeed(
                key=asset_data.get("key", "unknown"),
                description=asset_data.get("description", ""),
                game_specific_prompt=asset_data.get("game_specific_prompt", ""),
            ))

        # Get template info for recommended config
        template = TEMPLATE_REGISTRY.get(mechanic_type)
        recommended_template = mechanic_type.value if template else "tapper"
        default_config = template.get_default_config() if template else {}

        # Merge with analyzed config
        template_config = {**default_config, **data.get("template_config", {})}

        return GameAnalysis(
            game_name=data.get("game_name", "Unknown Game"),
            publisher=data.get("publisher"),
            mechanic_type=mechanic_type,
            mechanic_confidence=data.get("mechanic_confidence", 0.5),
            mechanic_reasoning=data.get("mechanic_reasoning", ""),
            visual_style=visual_style,
            assets_needed=assets_needed,
            recommended_template=recommended_template,
            template_config=template_config,
            core_loop_description=data.get("core_loop_description", ""),
            hook_suggestion=data.get("hook_suggestion", "Tap to Play!"),
            cta_suggestion=data.get("cta_suggestion", "Download FREE"),
            raw_analysis=data,
        )

    def _create_fallback_analysis(self, response_text: str, error: str) -> GameAnalysis:
        """Create a fallback analysis when JSON parsing fails."""
        # Try to extract mechanic type from text
        mechanic_type = MechanicType.UNKNOWN
        for mtype in MechanicType:
            if mtype.value.upper() in response_text.upper():
                mechanic_type = mtype
                break

        return GameAnalysis(
            game_name="Unknown Game",
            publisher=None,
            mechanic_type=mechanic_type,
            mechanic_confidence=0.3,
            mechanic_reasoning=f"Fallback analysis due to parse error: {error}",
            visual_style=VisualStyle(
                art_type="cartoon",
                color_palette=["#FF6B6B", "#4ECDC4", "#FFE66D"],
                theme="casual",
                mood="playful",
            ),
            assets_needed=[],
            recommended_template=mechanic_type.value,
            template_config={},
            core_loop_description="Unable to parse core loop",
            hook_suggestion="Tap to Play!",
            cta_suggestion="Download FREE",
            raw_analysis={"error": error, "raw_response": response_text},
        )


class GameAnalyzerSync:
    """Synchronous wrapper for GameAnalyzer."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-20250514",
    ):
        self._analyzer = GameAnalyzer(api_key=api_key, model=model)

    def analyze_screenshots(
        self,
        screenshots: list[bytes | Path | str],
        game_name_hint: Optional[str] = None,
    ) -> GameAnalysis:
        """Analyze game screenshots (sync version)."""
        return self._analyzer.analyze_screenshots(screenshots, game_name_hint)

    def analyze_from_files(
        self,
        file_paths: list[str | Path],
        game_name_hint: Optional[str] = None,
    ) -> GameAnalysis:
        """Analyze screenshots from file paths (sync version)."""
        return self._analyzer.analyze_from_files(file_paths, game_name_hint)
