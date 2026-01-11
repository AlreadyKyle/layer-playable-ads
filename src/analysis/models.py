"""
Data models for game analysis.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ConfidenceLevel(str, Enum):
    """Confidence level for analysis results."""

    HIGH = "high"  # 80%+ certainty
    MEDIUM = "medium"  # 50-80% certainty
    LOW = "low"  # Below 50% certainty


@dataclass
class AnalysisResult:
    """Base class for analysis results with confidence tracking."""

    confidence: ConfidenceLevel
    confidence_score: float  # 0.0 to 1.0
    reasoning: str = ""  # Explanation of the analysis

    def is_reliable(self) -> bool:
        """Check if the analysis is reliable enough to use."""
        return self.confidence_score >= 0.6
