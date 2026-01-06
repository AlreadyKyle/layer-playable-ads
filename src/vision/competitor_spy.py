"""
Competitor Spy - Vision Intelligence Module

Analyzes competitor games via screenshots or App Store pages to extract
visual style recipes using Claude's vision capabilities.
"""

import base64
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Union

import httpx
import structlog
from anthropic import Anthropic

from src.layer_client import StyleRecipe
from src.utils.helpers import get_settings

logger = structlog.get_logger()


# =============================================================================
# Constants
# =============================================================================

STYLE_EXTRACTION_PROMPT = """You are an expert game art director and UA (User Acquisition) specialist.

Analyze the provided game screenshot(s) and extract a comprehensive visual style recipe that can be used to generate consistent game assets.

Focus on:
1. **Art Style**: Is it 2D/3D, cartoon/realistic, pixel art, vector, etc.?
2. **Color Palette**: Identify the dominant primary and accent colors
3. **Visual Elements**: Characters, environments, UI elements, effects
4. **Mood/Tone**: Bright/dark, playful/serious, casual/hardcore
5. **Technical Style**: Rendering techniques, shading style, outline presence

Output a JSON object with this EXACT structure:
{
    "styleName": "A descriptive name for this style (e.g., 'Bright Casual Match-3')",
    "prefix": ["list", "of", "style", "prefix", "terms"],
    "technical": ["rendering", "quality", "technical", "terms"],
    "negative": ["things", "to", "avoid", "in", "generation"],
    "palette": {
        "primary": "#HEX_COLOR",
        "accent": "#HEX_COLOR"
    },
    "referenceImageId": null,
    "analysis": {
        "genre": "detected game genre",
        "artStyle": "primary art style classification",
        "targetAudience": "casual/midcore/hardcore",
        "keyVisualElements": ["list", "of", "key", "elements"],
        "moodDescriptors": ["mood", "descriptors"]
    }
}

The prefix array should contain style descriptors that will be prepended to generation prompts.
The technical array should contain quality and rendering specifications.
The negative array should contain things to avoid in generated images.

Be specific and actionable. These will be used to drive AI image generation for playable ads."""


APP_STORE_EXTRACTION_PROMPT = """You are analyzing an App Store page for a mobile game.

Extract visual style information from the screenshots and app icon visible on this page.
Focus on the game's art direction, color palette, and visual identity.

Output a JSON object with this EXACT structure:
{
    "styleName": "A descriptive name for this style",
    "prefix": ["list", "of", "style", "prefix", "terms"],
    "technical": ["rendering", "quality", "technical", "terms"],
    "negative": ["things", "to", "avoid", "in", "generation"],
    "palette": {
        "primary": "#HEX_COLOR",
        "accent": "#HEX_COLOR"
    },
    "referenceImageId": null,
    "analysis": {
        "appName": "detected app name",
        "genre": "detected game genre",
        "artStyle": "primary art style classification",
        "targetAudience": "casual/midcore/hardcore",
        "keyVisualElements": ["list", "of", "key", "elements"],
        "moodDescriptors": ["mood", "descriptors"]
    }
}

Be specific and actionable for AI image generation purposes."""


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class AnalysisResult:
    """Result of competitor analysis."""

    recipe: StyleRecipe
    genre: str = "unknown"
    art_style: str = "unknown"
    target_audience: str = "casual"
    key_visual_elements: list[str] = field(default_factory=list)
    mood_descriptors: list[str] = field(default_factory=list)
    raw_analysis: dict = field(default_factory=dict)
    source_type: str = "screenshot"  # "screenshot" or "appstore"


# =============================================================================
# Competitor Spy
# =============================================================================


class CompetitorSpy:
    """
    Vision-based competitor analysis for style extraction.

    Uses Claude's vision capabilities to analyze game screenshots
    and extract reusable style recipes.
    """

    def __init__(
        self,
        anthropic_api_key: Optional[str] = None,
        model: Optional[str] = None,
    ):
        """
        Initialize CompetitorSpy.

        Args:
            anthropic_api_key: Anthropic API key (default: from settings)
            model: Claude model to use (default: from settings)
        """
        settings = get_settings()
        self.api_key = anthropic_api_key or settings.anthropic_api_key
        self.model = model or settings.claude_model

        if not self.api_key:
            raise ValueError(
                "Anthropic API key required. Set ANTHROPIC_API_KEY in .env"
            )

        self._client = Anthropic(api_key=self.api_key)
        self._logger = logger.bind(component="CompetitorSpy")

    def _encode_image(self, image_path: Union[str, Path]) -> tuple[str, str]:
        """
        Encode image file to base64.

        Args:
            image_path: Path to image file

        Returns:
            Tuple of (base64_data, media_type)
        """
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {path}")

        # Determine media type
        suffix = path.suffix.lower()
        media_types = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".webp": "image/webp",
        }
        media_type = media_types.get(suffix, "image/png")

        # Read and encode
        with open(path, "rb") as f:
            data = base64.standard_b64encode(f.read()).decode("utf-8")

        return data, media_type

    async def _fetch_image_from_url(self, url: str) -> tuple[str, str]:
        """
        Fetch and encode image from URL.

        Args:
            url: Image URL

        Returns:
            Tuple of (base64_data, media_type)
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(url, follow_redirects=True)
            response.raise_for_status()

            content_type = response.headers.get("content-type", "image/png")
            media_type = content_type.split(";")[0].strip()

            data = base64.standard_b64encode(response.content).decode("utf-8")
            return data, media_type

    def _parse_json_response(self, text: str) -> dict:
        """
        Parse JSON from Claude's response, handling markdown code blocks.

        Args:
            text: Raw response text

        Returns:
            Parsed JSON dict
        """
        # Try to extract JSON from markdown code block
        json_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
        if json_match:
            text = json_match.group(1)

        # Clean up common issues
        text = text.strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            self._logger.error("Failed to parse JSON response", error=str(e))
            raise ValueError(f"Failed to parse style recipe: {e}")

    def _build_analysis_result(self, data: dict, source_type: str) -> AnalysisResult:
        """
        Build AnalysisResult from parsed response data.

        Args:
            data: Parsed JSON response
            source_type: Source type ("screenshot" or "appstore")

        Returns:
            AnalysisResult with StyleRecipe
        """
        analysis = data.get("analysis", {})

        recipe = StyleRecipe(
            style_name=data.get("styleName", "Extracted Style"),
            prefix=data.get("prefix", []),
            technical=data.get("technical", []),
            negative=data.get("negative", []),
            palette_primary=data.get("palette", {}).get("primary", "#000000"),
            palette_accent=data.get("palette", {}).get("accent", "#FFFFFF"),
            reference_image_id=data.get("referenceImageId"),
        )

        return AnalysisResult(
            recipe=recipe,
            genre=analysis.get("genre", "unknown"),
            art_style=analysis.get("artStyle", "unknown"),
            target_audience=analysis.get("targetAudience", "casual"),
            key_visual_elements=analysis.get("keyVisualElements", []),
            mood_descriptors=analysis.get("moodDescriptors", []),
            raw_analysis=data,
            source_type=source_type,
        )

    def analyze_screenshots(
        self,
        image_paths: list[Union[str, Path]],
        additional_context: Optional[str] = None,
    ) -> AnalysisResult:
        """
        Analyze game screenshots to extract style recipe.

        Args:
            image_paths: List of paths to screenshot images
            additional_context: Optional context about the game

        Returns:
            AnalysisResult containing StyleRecipe and metadata
        """
        self._logger.info(
            "Analyzing screenshots",
            count=len(image_paths),
        )

        # Build message content with images
        content = []

        for path in image_paths:
            data, media_type = self._encode_image(path)
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": media_type,
                    "data": data,
                },
            })

        # Add the analysis prompt
        prompt = STYLE_EXTRACTION_PROMPT
        if additional_context:
            prompt += f"\n\nAdditional context: {additional_context}"

        content.append({
            "type": "text",
            "text": prompt,
        })

        # Call Claude
        response = self._client.messages.create(
            model=self.model,
            max_tokens=2000,
            messages=[{"role": "user", "content": content}],
        )

        # Parse response
        response_text = response.content[0].text
        data = self._parse_json_response(response_text)

        result = self._build_analysis_result(data, "screenshot")

        self._logger.info(
            "Screenshot analysis complete",
            style_name=result.recipe.style_name,
            genre=result.genre,
        )

        return result

    def analyze_screenshot(
        self,
        image_path: Union[str, Path],
        additional_context: Optional[str] = None,
    ) -> AnalysisResult:
        """
        Analyze a single screenshot.

        Convenience method that wraps analyze_screenshots.
        """
        return self.analyze_screenshots([image_path], additional_context)

    def analyze_app_store_url(
        self,
        url: str,
        screenshot_image: Optional[Union[str, Path, bytes]] = None,
    ) -> AnalysisResult:
        """
        Analyze an App Store page to extract style recipe.

        Note: Since we can't directly fetch App Store pages in vision,
        this method requires a screenshot of the App Store page to be provided.

        Args:
            url: App Store URL (for context/logging)
            screenshot_image: Screenshot of the App Store page

        Returns:
            AnalysisResult containing StyleRecipe and metadata
        """
        self._logger.info("Analyzing App Store page", url=url)

        if screenshot_image is None:
            raise ValueError(
                "screenshot_image required: provide a screenshot of the App Store page"
            )

        content = []

        # Handle different input types
        if isinstance(screenshot_image, bytes):
            data = base64.standard_b64encode(screenshot_image).decode("utf-8")
            media_type = "image/png"
        elif isinstance(screenshot_image, (str, Path)):
            data, media_type = self._encode_image(screenshot_image)
        else:
            raise ValueError(f"Invalid screenshot_image type: {type(screenshot_image)}")

        content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": media_type,
                "data": data,
            },
        })

        content.append({
            "type": "text",
            "text": f"App Store URL: {url}\n\n{APP_STORE_EXTRACTION_PROMPT}",
        })

        # Call Claude
        response = self._client.messages.create(
            model=self.model,
            max_tokens=2000,
            messages=[{"role": "user", "content": content}],
        )

        # Parse response
        response_text = response.content[0].text
        data = self._parse_json_response(response_text)

        result = self._build_analysis_result(data, "appstore")

        self._logger.info(
            "App Store analysis complete",
            style_name=result.recipe.style_name,
            app_name=data.get("analysis", {}).get("appName", "unknown"),
        )

        return result


# =============================================================================
# Export
# =============================================================================

__all__ = ["CompetitorSpy", "AnalysisResult", "StyleRecipe"]
