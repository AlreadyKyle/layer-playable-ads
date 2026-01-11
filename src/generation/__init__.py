"""
Asset Generation Module - Layer.ai powered asset generation.

This module provides:
- GameAssetGenerator: Generates game-specific assets based on analysis
- Leverages Layer.ai API for consistent style generation
"""

from .game_asset_generator import (
    GameAssetGenerator,
    GeneratedAssetSet,
)

__all__ = [
    "GameAssetGenerator",
    "GeneratedAssetSet",
]
