"""
Template Registry - Maps game mechanics to Phaser.js templates.

This module defines:
- MechanicType enum for supported game types
- TemplateInfo with configuration and asset requirements
- TEMPLATE_REGISTRY mapping mechanics to templates
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional


class MechanicType(str, Enum):
    """Supported game mechanic types."""

    MATCH3 = "match3"
    RUNNER = "runner"
    TAPPER = "tapper"
    MERGER = "merger"
    PUZZLE = "puzzle"
    SHOOTER = "shooter"
    UNKNOWN = "unknown"

    @classmethod
    def from_string(cls, value: str) -> "MechanicType":
        """Convert string to MechanicType, defaulting to UNKNOWN."""
        value_lower = value.lower().strip()
        for member in cls:
            if member.value == value_lower:
                return member
        # Try partial matching
        if "match" in value_lower or "3" in value_lower:
            return cls.MATCH3
        if "run" in value_lower or "endless" in value_lower:
            return cls.RUNNER
        if "tap" in value_lower or "click" in value_lower or "idle" in value_lower:
            return cls.TAPPER
        if "merge" in value_lower or "2048" in value_lower:
            return cls.MERGER
        if "puzzle" in value_lower or "tetris" in value_lower or "block" in value_lower:
            return cls.PUZZLE
        if "shoot" in value_lower or "angry" in value_lower or "aim" in value_lower:
            return cls.SHOOTER
        return cls.UNKNOWN


@dataclass
class AssetRequirement:
    """Definition of a required asset for a template."""

    key: str  # Asset key used in template (e.g., "tile_1", "player")
    description: str  # Human-readable description for prompts
    required: bool = True  # Whether the asset is required
    default_prompt: str = ""  # Default prompt if no game-specific prompt
    transparency: bool = True  # Whether asset needs transparent background
    max_size: int = 512  # Max dimension in pixels


@dataclass
class ConfigParameter:
    """Definition of a configurable parameter for a template."""

    key: str
    type: str  # "int", "float", "string", "color"
    default: any
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    description: str = ""


@dataclass
class TemplateInfo:
    """Complete information about a game template."""

    mechanic_type: MechanicType
    name: str
    description: str
    template_file: str  # Relative path from templates directory
    required_assets: list[AssetRequirement]
    config_parameters: list[ConfigParameter]
    example_games: list[str] = field(default_factory=list)

    def get_template_path(self) -> Path:
        """Get absolute path to template file."""
        templates_dir = Path(__file__).parent
        return templates_dir / self.template_file

    def get_asset_keys(self) -> list[str]:
        """Get list of required asset keys."""
        return [a.key for a in self.required_assets if a.required]

    def get_default_config(self) -> dict:
        """Get default configuration values."""
        return {p.key: p.default for p in self.config_parameters}


# =============================================================================
# Template Definitions
# =============================================================================

MATCH3_TEMPLATE = TemplateInfo(
    mechanic_type=MechanicType.MATCH3,
    name="Match-3 Puzzle",
    description="Swap adjacent tiles to match 3 or more of the same type",
    template_file="match3/template.html",
    example_games=["Candy Crush", "Bejeweled", "Gardenscapes", "Homescapes"],
    required_assets=[
        AssetRequirement(
            key="tile_1",
            description="First tile type (e.g., red gem, candy)",
            default_prompt="colorful gem game tile, round, glossy, cartoon style",
        ),
        AssetRequirement(
            key="tile_2",
            description="Second tile type (different color)",
            default_prompt="colorful gem game tile, round, glossy, cartoon style, blue",
        ),
        AssetRequirement(
            key="tile_3",
            description="Third tile type (different color)",
            default_prompt="colorful gem game tile, round, glossy, cartoon style, green",
        ),
        AssetRequirement(
            key="tile_4",
            description="Fourth tile type (different color)",
            default_prompt="colorful gem game tile, round, glossy, cartoon style, yellow",
        ),
        AssetRequirement(
            key="background",
            description="Game background",
            default_prompt="colorful game background, fantasy, vibrant",
            transparency=False,
        ),
    ],
    config_parameters=[
        ConfigParameter(
            key="GRID_WIDTH",
            type="int",
            default=7,
            min_value=5,
            max_value=9,
            description="Number of columns in the grid",
        ),
        ConfigParameter(
            key="GRID_HEIGHT",
            type="int",
            default=9,
            min_value=7,
            max_value=12,
            description="Number of rows in the grid",
        ),
        ConfigParameter(
            key="TILE_TYPES",
            type="int",
            default=4,
            min_value=3,
            max_value=6,
            description="Number of different tile types",
        ),
        ConfigParameter(
            key="MATCH_MINIMUM",
            type="int",
            default=3,
            min_value=3,
            max_value=4,
            description="Minimum tiles needed for a match",
        ),
    ],
)

RUNNER_TEMPLATE = TemplateInfo(
    mechanic_type=MechanicType.RUNNER,
    name="Endless Runner",
    description="Run, jump, and dodge obstacles in lanes",
    template_file="runner/template.html",
    example_games=["Subway Surfers", "Temple Run", "Sonic Dash", "Minion Rush"],
    required_assets=[
        AssetRequirement(
            key="player",
            description="Main player character (running pose)",
            default_prompt="cartoon game character, running pose, side view, mobile game style",
        ),
        AssetRequirement(
            key="obstacle",
            description="Obstacle to avoid",
            default_prompt="game obstacle, barrier, cartoon style, dangerous looking",
        ),
        AssetRequirement(
            key="collectible",
            description="Item to collect (coin, gem)",
            default_prompt="golden coin, shiny, game collectible, cartoon style",
        ),
        AssetRequirement(
            key="background",
            description="Scrolling background",
            default_prompt="endless runner game background, road or path, colorful",
            transparency=False,
        ),
    ],
    config_parameters=[
        ConfigParameter(
            key="LANES",
            type="int",
            default=3,
            min_value=2,
            max_value=5,
            description="Number of lanes",
        ),
        ConfigParameter(
            key="SPEED",
            type="float",
            default=5.0,
            min_value=3.0,
            max_value=10.0,
            description="Initial game speed",
        ),
        ConfigParameter(
            key="JUMP_HEIGHT",
            type="int",
            default=400,
            min_value=300,
            max_value=600,
            description="Jump velocity",
        ),
    ],
)

TAPPER_TEMPLATE = TemplateInfo(
    mechanic_type=MechanicType.TAPPER,
    name="Tapper / Idle Clicker",
    description="Tap rapidly to accumulate points with multipliers",
    template_file="tapper/template.html",
    example_games=["Cookie Clicker", "Idle Miner Tycoon", "Tap Titans", "AdVenture Capitalist"],
    required_assets=[
        AssetRequirement(
            key="target",
            description="Main tappable element (cookie, character, button)",
            default_prompt="large tappable game icon, cartoon style, inviting, colorful",
        ),
        AssetRequirement(
            key="bonus",
            description="Bonus item that appears",
            default_prompt="golden star, bonus icon, shiny, game reward",
            required=False,
        ),
        AssetRequirement(
            key="background",
            description="Game background",
            default_prompt="idle game background, colorful, appealing",
            transparency=False,
        ),
    ],
    config_parameters=[
        ConfigParameter(
            key="POINTS_PER_TAP",
            type="int",
            default=1,
            min_value=1,
            max_value=100,
            description="Base points per tap",
        ),
        ConfigParameter(
            key="BONUS_THRESHOLD",
            type="int",
            default=10,
            min_value=5,
            max_value=50,
            description="Taps needed for bonus",
        ),
    ],
)


# =============================================================================
# Template Registry
# =============================================================================

TEMPLATE_REGISTRY: dict[MechanicType, TemplateInfo] = {
    MechanicType.MATCH3: MATCH3_TEMPLATE,
    MechanicType.RUNNER: RUNNER_TEMPLATE,
    MechanicType.TAPPER: TAPPER_TEMPLATE,
}


def get_template(mechanic_type: MechanicType) -> Optional[TemplateInfo]:
    """Get template info for a mechanic type."""
    return TEMPLATE_REGISTRY.get(mechanic_type)


def get_template_for_mechanic(mechanic_name: str) -> Optional[TemplateInfo]:
    """Get template info from a mechanic name string."""
    mechanic_type = MechanicType.from_string(mechanic_name)
    return get_template(mechanic_type)


def list_available_mechanics() -> list[MechanicType]:
    """List all mechanics with available templates."""
    return list(TEMPLATE_REGISTRY.keys())


def get_mechanic_examples() -> dict[MechanicType, list[str]]:
    """Get example games for each mechanic type."""
    return {
        mechanic: info.example_games
        for mechanic, info in TEMPLATE_REGISTRY.items()
    }
