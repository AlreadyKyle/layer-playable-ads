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

# Lazy imports — submodules are loaded on first access, not at package init.
# This avoids cascading import failures when heavy dependencies (httpx,
# anthropic, etc.) are missing from the active Python environment.


def __getattr__(name: str):
    """Lazy-load public symbols on first access."""
    _import_map = {
        "LayerClientSync": ("src.layer_client", "LayerClientSync"),
        "LayerClient": ("src.layer_client", "LayerClient"),
        "GameAnalyzer": ("src.analysis", "GameAnalyzer"),
        "GameAnalyzerSync": ("src.analysis", "GameAnalyzerSync"),
        "GameAnalysis": ("src.analysis", "GameAnalysis"),
        "GameAssetGenerator": ("src.generation", "GameAssetGenerator"),
        "DynamicGameGenerator": ("src.generation", "DynamicGameGenerator"),
        "SoundGenerator": ("src.generation", "SoundGenerator"),
        "PlayableBuilder": ("src.assembly", "PlayableBuilder"),
        "PlayableConfig": ("src.assembly", "PlayableConfig"),
        "MechanicType": ("src.templates", "MechanicType"),
        "TEMPLATE_REGISTRY": ("src.templates", "TEMPLATE_REGISTRY"),
        "PlayableFactory": ("src.playable_factory", "PlayableFactory"),
        "PlayableOutput": ("src.playable_factory", "PlayableOutput"),
        "create_playable": ("src.playable_factory", "create_playable"),
    }
    if name in _import_map:
        module_path, attr = _import_map[name]
        import importlib
        mod = importlib.import_module(module_path)
        return getattr(mod, attr)
    raise AttributeError(f"module 'src' has no attribute {name!r}")


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
