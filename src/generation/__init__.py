"""
Generation Module - AI-powered asset and game generation.

This module provides:
- GameAssetGenerator: Generates game-specific assets using Layer.ai
- DynamicGameGenerator: Generates Phaser.js game code using Claude
- SoundGenerator: Procedural sound effects for playable ads
"""

from .game_asset_generator import (
    GameAssetGenerator,
    GeneratedAssetSet,
)
from .dynamic_game_generator import (
    DynamicGameGenerator,
    GeneratedGame,
)
from .sound_generator import (
    SoundGenerator,
    SoundType,
    PROCEDURAL_SOUNDS_JS,
)

__all__ = [
    "GameAssetGenerator",
    "GeneratedAssetSet",
    "DynamicGameGenerator",
    "GeneratedGame",
    "SoundGenerator",
    "SoundType",
    "PROCEDURAL_SOUNDS_JS",
]
