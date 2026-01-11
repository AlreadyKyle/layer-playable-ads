"""
Game Analysis Module - Claude Vision powered game analysis.

This module provides:
- GameAnalyzer: Analyzes game screenshots to extract mechanics and style
- GameAnalysis: Structured analysis result with mechanic type and assets
"""

from .game_analyzer import (
    GameAnalyzer,
    GameAnalyzerSync,
    GameAnalysis,
    VisualStyle,
    AssetNeed,
)
from .models import (
    AnalysisResult,
    ConfidenceLevel,
)

__all__ = [
    "GameAnalyzer",
    "GameAnalyzerSync",
    "GameAnalysis",
    "VisualStyle",
    "AssetNeed",
    "AnalysisResult",
    "ConfidenceLevel",
]
