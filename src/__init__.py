"""
Playable Ad Generator

AI-powered playable ad generation using:
- Claude Vision for game analysis
- Layer.ai for asset generation
- Phaser.js templates for game mechanics

MVP v2.0 Features:
- Game-specific playable ads (not generic)
- Automatic mechanic detection (match-3, runner, tapper, etc.)
- Dynamic game code generation
- Procedural sound effects
- Multi-network export (Google, Unity, IronSource, Facebook, AppLovin)
- MRAID 3.0 compliant HTML5 output
"""

__version__ = "2.0.0"
__app_name__ = "Playable Ad Generator"

# Core modules
from src.layer_client import LayerClientSync, LayerClient
from src.analysis import GameAnalyzer, GameAnalyzerSync, GameAnalysis
from src.generation import (
    GameAssetGenerator,
    DynamicGameGenerator,
    SoundGenerator,
)
from src.assembly import PlayableBuilder, PlayableConfig
from src.templates import MechanicType, TEMPLATE_REGISTRY
from src.playable_factory import PlayableFactory, PlayableOutput, create_playable

__all__ = [
    # Version
    "__version__",
    "__app_name__",
    # Factory (main entry point)
    "PlayableFactory",
    "PlayableOutput",
    "create_playable",
    # Layer.ai
    "LayerClientSync",
    "LayerClient",
    # Analysis
    "GameAnalyzer",
    "GameAnalyzerSync",
    "GameAnalysis",
    # Generation
    "GameAssetGenerator",
    "DynamicGameGenerator",
    "SoundGenerator",
    # Assembly
    "PlayableBuilder",
    "PlayableConfig",
    # Templates
    "MechanicType",
    "TEMPLATE_REGISTRY",
]
