"""
Game Template Library for Playable Ad Generation.

This module provides pre-built Phaser.js templates for different game mechanics.
Each template implements a specific core gameplay loop that can be customized
with game-specific assets and configuration.
"""

from .registry import (
    MechanicType,
    TemplateInfo,
    TEMPLATE_REGISTRY,
    get_template,
    get_template_for_mechanic,
    list_available_mechanics,
)

__all__ = [
    "MechanicType",
    "TemplateInfo",
    "TEMPLATE_REGISTRY",
    "get_template",
    "get_template_for_mechanic",
    "list_available_mechanics",
]
