"""
Vision Module - Competitor Spy & Style Intelligence

Uses Claude vision to analyze game screenshots and extract Style Recipes.
"""

from .competitor_spy import CompetitorSpy, AnalysisResult
from src.layer_client import StyleRecipe

__all__ = ["CompetitorSpy", "AnalysisResult", "StyleRecipe"]
