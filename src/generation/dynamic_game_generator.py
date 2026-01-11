"""
Dynamic Game Generator - Uses Claude to generate custom Phaser.js game code.

This module generates game code dynamically based on game analysis,
rather than relying on static templates. This allows for:
- More game mechanic types without manual template creation
- Customization based on specific game analysis
- Dynamic difficulty and parameter adjustment
"""

from dataclasses import dataclass
from typing import Optional

import anthropic

from src.analysis.game_analyzer import GameAnalysis
from src.templates.registry import MechanicType, TEMPLATE_REGISTRY


@dataclass
class GeneratedGame:
    """Result of dynamic game generation."""

    html: str
    mechanic_type: MechanicType
    generation_notes: str
    confidence: float


class DynamicGameGenerator:
    """Generates custom Phaser.js games using Claude."""

    GENERATION_PROMPT = """You are an expert HTML5 game developer specializing in playable ads.

Generate a COMPLETE, SELF-CONTAINED Phaser.js 3.70 game based on this game analysis.

## Game Analysis
- Game Name: {game_name}
- Mechanic Type: {mechanic_type}
- Core Loop: {core_loop}
- Visual Style: {art_type}, {theme} theme, {mood} mood
- Color Palette: {colors}

## REQUIREMENTS (CRITICAL)

1. **Single HTML File**: All code must be in ONE index.html file
2. **Phaser 3.70**: Use CDN: https://cdn.jsdelivr.net/npm/phaser@3.70.0/dist/phaser.min.js
3. **3-15-5 Timing**:
   - Hook Scene: 3 seconds (attention grabber)
   - Gameplay Scene: 15 seconds (core mechanic demo)
   - CTA Scene: 5 seconds (install button)
4. **Asset Placeholders**: Use these exact placeholder keys in CONFIG:
   {asset_keys}
5. **MRAID Support**: Include openStoreUrl() function that uses mraid.open()
6. **Mobile Optimized**: Touch controls, 320x480 default size, Scale.FIT

## Template Structure

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>${{TITLE}}</title>
    <style>
        * {{ margin: 0; padding: 0; }}
        html, body {{ width: 100%; height: 100%; overflow: hidden; background: ${{BACKGROUND_COLOR}}; }}
        #game-container {{ width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; }}
    </style>
</head>
<body>
    <div id="game-container"></div>
    <script src="https://cdn.jsdelivr.net/npm/phaser@3.70.0/dist/phaser.min.js"></script>
    <script>
        // CONFIG object (will be injected by assembler)
        var CONFIG = {{
            storeUrl: '${{STORE_URL}}',
            gameName: '${{GAME_NAME}}',
            hookText: '${{HOOK_TEXT}}',
            ctaText: '${{CTA_TEXT}}',
            hookDuration: ${{HOOK_DURATION}},
            gameplayDuration: ${{GAMEPLAY_DURATION}},
            ctaDuration: ${{CTA_DURATION}}
        }};

        // ASSETS manifest (Base64 data URIs injected by assembler)
        var ASSETS = ${{ASSET_MANIFEST}};

        // MRAID handler
        var mraid = window.mraid || null;
        function openStoreUrl() {{
            if (mraid && mraid.open) mraid.open(CONFIG.storeUrl);
            else window.open(CONFIG.storeUrl, '_blank');
        }}

        // YOUR GAME CODE HERE
        // Include: BootScene, HookScene, GameplayScene, CTAScene
        // Implement the {mechanic_type} mechanic
    </script>
</body>
</html>
```

## Core Mechanic Implementation for {mechanic_type}

{mechanic_instructions}

## Output Format

Return ONLY the complete HTML code, no markdown, no explanations.
The code must be immediately runnable in a browser.
"""

    MECHANIC_INSTRUCTIONS = {
        MechanicType.MATCH3: """
For MATCH-3:
- Create a grid of tiles (7x9 default)
- Use tile_1, tile_2, tile_3, tile_4 asset keys
- Implement swap logic: tap two adjacent tiles to swap
- Detect matches of 3+ same tiles in row/column
- Clear matches with animation, drop new tiles
- Track and display score
- Show tutorial hint "Swap to match 3!"
""",
        MechanicType.RUNNER: """
For RUNNER:
- Create 3 lanes (left, center, right)
- Player character runs forward automatically
- Use player, obstacle, collectible, background asset keys
- Swipe left/right to change lanes
- Tap to jump over obstacles
- Spawn obstacles and collectibles from top
- Track score for collected items and avoided obstacles
- Show tutorial "Swipe to dodge, tap to jump!"
""",
        MechanicType.TAPPER: """
For TAPPER/IDLE:
- Large tappable target in center
- Use target, bonus, background asset keys
- Each tap increases score
- Fast tapping builds multiplier (x1 to x5)
- Multiplier decays if not tapping
- Spawn bonus items that give extra points
- Show big score counter with K/M formatting
- Tutorial: "Tap fast for combo!"
""",
        MechanicType.MERGER: """
For MERGER:
- Grid of items (4x4 or 5x5)
- Use item_1, item_2, item_3, background asset keys
- Drag items onto same-type items to merge
- Merged items upgrade to next level
- New items spawn in empty spaces
- Track score based on merge level
- Tutorial: "Drag to merge!"
""",
        MechanicType.PUZZLE: """
For PUZZLE:
- Falling block puzzle (Tetris-style simplified)
- Use block_1, block_2, block_3, background asset keys
- Blocks fall from top
- Tap left/right side to move block
- Tap center to rotate
- Clear complete rows
- Track score and lines cleared
- Tutorial: "Tap to move, fill rows!"
""",
        MechanicType.SHOOTER: """
For SHOOTER:
- Player at bottom, targets above
- Use player, projectile, target, background asset keys
- Tap to shoot projectile upward
- Projectiles destroy targets on hit
- Targets may move or be stationary
- Track score for hits
- Tutorial: "Tap to shoot!"
""",
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-20250514",
    ):
        """Initialize the generator."""
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    def generate_game(
        self,
        analysis: GameAnalysis,
        custom_instructions: Optional[str] = None,
    ) -> GeneratedGame:
        """Generate a complete Phaser.js game based on analysis.

        Args:
            analysis: GameAnalysis from game analyzer
            custom_instructions: Optional additional instructions

        Returns:
            GeneratedGame with complete HTML code
        """
        # Get mechanic-specific instructions
        mechanic_instructions = self.MECHANIC_INSTRUCTIONS.get(
            analysis.mechanic_type,
            self.MECHANIC_INSTRUCTIONS[MechanicType.TAPPER]  # Default fallback
        )

        if custom_instructions:
            mechanic_instructions += f"\n\nAdditional Requirements:\n{custom_instructions}"

        # Get asset keys for this mechanic
        template = TEMPLATE_REGISTRY.get(analysis.mechanic_type)
        if template:
            asset_keys = ", ".join([a.key for a in template.required_assets])
        else:
            asset_keys = "background, target, bonus"

        # Build prompt
        prompt = self.GENERATION_PROMPT.format(
            game_name=analysis.game_name,
            mechanic_type=analysis.mechanic_type.value.upper(),
            core_loop=analysis.core_loop_description,
            art_type=analysis.visual_style.art_type,
            theme=analysis.visual_style.theme,
            mood=analysis.visual_style.mood,
            colors=", ".join(analysis.visual_style.color_palette),
            asset_keys=asset_keys,
            mechanic_instructions=mechanic_instructions,
        )

        # Generate with Claude
        message = self.client.messages.create(
            model=self.model,
            max_tokens=8000,
            messages=[
                {"role": "user", "content": prompt}
            ],
        )

        html = message.content[0].text

        # Clean up if wrapped in markdown
        if html.startswith("```html"):
            html = html[7:]
        if html.startswith("```"):
            html = html[3:]
        if html.endswith("```"):
            html = html[:-3]
        html = html.strip()

        return GeneratedGame(
            html=html,
            mechanic_type=analysis.mechanic_type,
            generation_notes=f"Generated {analysis.mechanic_type.value} game for {analysis.game_name}",
            confidence=0.8,
        )

    def generate_custom_mechanic(
        self,
        description: str,
        game_name: str = "Custom Game",
        asset_keys: Optional[list[str]] = None,
    ) -> GeneratedGame:
        """Generate a game for a custom/unsupported mechanic type.

        Args:
            description: Detailed description of the game mechanic
            game_name: Name for the game
            asset_keys: List of asset keys to use

        Returns:
            GeneratedGame with complete HTML code
        """
        if asset_keys is None:
            asset_keys = ["player", "target", "background", "collectible"]

        custom_prompt = f"""You are an expert HTML5 game developer.

Generate a COMPLETE Phaser.js 3.70 playable ad game with this mechanic:

## Game Description
{description}

## Requirements
- Single HTML file, self-contained
- Phaser 3.70 from CDN
- 3-15-5 timing: 3s hook, 15s gameplay, 5s CTA
- Mobile touch controls
- MRAID support for store URLs
- Asset keys: {', '.join(asset_keys)}
- Use ${{PLACEHOLDER}} syntax for config injection

## Config Object Structure
```javascript
var CONFIG = {{
    storeUrl: '${{STORE_URL}}',
    gameName: '${{GAME_NAME}}',
    hookText: '${{HOOK_TEXT}}',
    ctaText: '${{CTA_TEXT}}',
    hookDuration: ${{HOOK_DURATION}},
    gameplayDuration: ${{GAMEPLAY_DURATION}},
    ctaDuration: ${{CTA_DURATION}}
}};
var ASSETS = ${{ASSET_MANIFEST}};
```

Output ONLY the complete HTML code, no explanations.
"""

        message = self.client.messages.create(
            model=self.model,
            max_tokens=8000,
            messages=[
                {"role": "user", "content": custom_prompt}
            ],
        )

        html = message.content[0].text
        if html.startswith("```"):
            html = html.split("```")[1]
            if html.startswith("html"):
                html = html[4:]
        html = html.strip()

        return GeneratedGame(
            html=html,
            mechanic_type=MechanicType.UNKNOWN,
            generation_notes=f"Custom mechanic: {description[:100]}...",
            confidence=0.6,
        )
