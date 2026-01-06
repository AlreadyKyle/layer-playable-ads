"""
Style Manager - Automated Layer.ai Workflow Module

Manages the lifecycle of styles in Layer.ai including creation,
retrieval, and dashboard deep linking.
"""

from dataclasses import dataclass
from typing import Any, Optional

import structlog

from src.layer_client import LayerClient, LayerClientSync, StyleRecipe

logger = structlog.get_logger()


@dataclass
class ManagedStyle:
    """A style being managed in Layer.ai."""

    style_id: str
    name: str
    dashboard_url: str
    recipe: StyleRecipe
    layer_data: dict


class StyleManager:
    """
    Manages style creation and retrieval in Layer.ai.

    Provides a high-level interface for the style workflow.
    """

    def __init__(self, client: Optional[LayerClientSync] = None):
        """
        Initialize StyleManager.

        Args:
            client: LayerClientSync instance (creates new if not provided)
        """
        self._client = client or LayerClientSync()
        self._logger = logger.bind(component="StyleManager")
        self._active_styles: dict[str, ManagedStyle] = {}

    def create_style_from_recipe(self, recipe: StyleRecipe) -> ManagedStyle:
        """
        Create a new style in Layer.ai from a StyleRecipe.

        Args:
            recipe: StyleRecipe containing style parameters

        Returns:
            ManagedStyle with ID and dashboard URL
        """
        self._logger.info("Creating style from recipe", style_name=recipe.style_name)

        # Create style via API
        style_id = self._client.create_style(recipe)

        # Get the created style data
        layer_data = self._client.get_style(style_id)

        # Build dashboard URL
        dashboard_url = self._client.get_style_dashboard_url(style_id)

        managed = ManagedStyle(
            style_id=style_id,
            name=recipe.style_name,
            dashboard_url=dashboard_url,
            recipe=recipe,
            layer_data=layer_data,
        )

        # Track locally
        self._active_styles[style_id] = managed

        self._logger.info(
            "Style created successfully",
            style_id=style_id,
            dashboard_url=dashboard_url,
        )

        return managed

    def get_style(self, style_id: str) -> Optional[ManagedStyle]:
        """
        Get a managed style by ID.

        Checks local cache first, then fetches from API if not found.

        Args:
            style_id: Style ID

        Returns:
            ManagedStyle or None if not found
        """
        # Check cache
        if style_id in self._active_styles:
            return self._active_styles[style_id]

        # Fetch from API
        try:
            layer_data = self._client.get_style(style_id)
            if not layer_data:
                return None

            # Reconstruct recipe from layer data
            recipe = StyleRecipe(
                style_name=layer_data.get("name", "Unknown"),
                prefix=layer_data.get("prefix", []),
                technical=layer_data.get("technical", []),
                negative=layer_data.get("negative", []),
            )

            managed = ManagedStyle(
                style_id=style_id,
                name=recipe.style_name,
                dashboard_url=self._client.get_style_dashboard_url(style_id),
                recipe=recipe,
                layer_data=layer_data,
            )

            self._active_styles[style_id] = managed
            return managed

        except Exception as e:
            self._logger.error("Failed to fetch style", style_id=style_id, error=str(e))
            return None

    def list_workspace_styles(
        self, limit: int = 20, offset: int = 0
    ) -> list[dict[str, Any]]:
        """
        List all styles in the workspace.

        Args:
            limit: Maximum styles to return
            offset: Pagination offset

        Returns:
            List of style summary dicts
        """
        styles, total = self._client.list_styles(limit=limit, offset=offset)

        self._logger.info(
            "Listed workspace styles",
            returned=len(styles),
            total=total,
        )

        return styles

    def get_dashboard_url(self, style_id: str) -> str:
        """
        Get the Layer.ai dashboard URL for a style.

        Args:
            style_id: Style ID

        Returns:
            Dashboard URL for manual tweaking
        """
        return self._client.get_style_dashboard_url(style_id)

    @property
    def active_style_count(self) -> int:
        """Number of locally tracked styles."""
        return len(self._active_styles)

    def clear_cache(self) -> None:
        """Clear the local style cache."""
        self._active_styles.clear()
        self._logger.info("Style cache cleared")


__all__ = ["StyleManager", "ManagedStyle"]
