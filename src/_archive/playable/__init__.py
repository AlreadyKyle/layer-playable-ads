"""
Playable Module - HTML5 Playable Ad Assembly

Creates MRAID 3.0 compliant playable ads with multi-network export support.
"""

from src.playable.assembler import (
    PlayableAssembler,
    PlayableAsset,
    PlayableConfig,
    PlayableMetadata,
    ExportResult,
    AdNetwork,
    NetworkSpec,
    NETWORK_SPECS,
    HOOK_DURATION_MS,
    GAMEPLAY_DURATION_MS,
    CTA_DURATION_MS,
    TOTAL_DURATION_MS,
)

__all__ = [
    "PlayableAssembler",
    "PlayableAsset",
    "PlayableConfig",
    "PlayableMetadata",
    "ExportResult",
    "AdNetwork",
    "NetworkSpec",
    "NETWORK_SPECS",
    "HOOK_DURATION_MS",
    "GAMEPLAY_DURATION_MS",
    "CTA_DURATION_MS",
    "TOTAL_DURATION_MS",
]
