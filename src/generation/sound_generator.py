"""
Sound Effect Integration - Free sound effects for playable ads.

This module provides integration with free sound effect sources:
- Pre-bundled minimal sound effects (Base64 encoded)
- Pixabay API (free, no key required for search)
- 8-bit procedural generation (Web Audio API based)

For MVP, we use pre-bundled minimal sounds to avoid external dependencies
and keep file sizes small.
"""

import base64
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class SoundType(str, Enum):
    """Common game sound effect types."""

    TAP = "tap"
    MATCH = "match"
    SCORE = "score"
    JUMP = "jump"
    COLLECT = "collect"
    FAIL = "fail"
    WIN = "win"
    WHOOSH = "whoosh"
    POP = "pop"
    DING = "ding"


@dataclass
class SoundEffect:
    """A sound effect with metadata."""

    type: SoundType
    name: str
    base64_data: str  # Base64 encoded audio
    format: str  # "wav" or "mp3"
    duration_ms: int

    @property
    def data_uri(self) -> str:
        """Get as data URI for embedding."""
        mime = "audio/wav" if self.format == "wav" else "audio/mpeg"
        return f"data:{mime};base64,{self.base64_data}"


# =============================================================================
# Pre-bundled Minimal Sound Effects (Procedurally Generated)
# =============================================================================
#
# These are tiny, procedurally generated sounds that work for any game.
# They're designed to be:
# - Very small (< 5KB each)
# - Universally applicable
# - No licensing concerns (generated, not recorded)
#
# In production, you'd generate these from Web Audio API or use a library.
# For now, we provide the JavaScript code to generate them client-side.

PROCEDURAL_SOUNDS_JS = """
// Procedural sound effect generator using Web Audio API
// Include this in your playable for dynamic sound effects

var SoundFX = (function() {
    var audioCtx = null;

    function getContext() {
        if (!audioCtx) {
            audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        }
        return audioCtx;
    }

    function playTone(frequency, duration, type, volume) {
        var ctx = getContext();
        var osc = ctx.createOscillator();
        var gain = ctx.createGain();

        osc.connect(gain);
        gain.connect(ctx.destination);

        osc.type = type || 'sine';
        osc.frequency.setValueAtTime(frequency, ctx.currentTime);

        gain.gain.setValueAtTime(volume || 0.3, ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + duration);

        osc.start(ctx.currentTime);
        osc.stop(ctx.currentTime + duration);
    }

    return {
        tap: function() {
            playTone(800, 0.1, 'sine', 0.2);
        },
        match: function() {
            playTone(523, 0.1, 'sine', 0.3);
            setTimeout(function() { playTone(659, 0.1, 'sine', 0.3); }, 100);
            setTimeout(function() { playTone(784, 0.15, 'sine', 0.3); }, 200);
        },
        score: function() {
            playTone(880, 0.15, 'sine', 0.25);
        },
        collect: function() {
            playTone(587, 0.08, 'square', 0.2);
            setTimeout(function() { playTone(784, 0.12, 'square', 0.2); }, 80);
        },
        jump: function() {
            var ctx = getContext();
            var osc = ctx.createOscillator();
            var gain = ctx.createGain();
            osc.connect(gain);
            gain.connect(ctx.destination);
            osc.type = 'sine';
            osc.frequency.setValueAtTime(300, ctx.currentTime);
            osc.frequency.exponentialRampToValueAtTime(600, ctx.currentTime + 0.1);
            gain.gain.setValueAtTime(0.2, ctx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.15);
            osc.start(ctx.currentTime);
            osc.stop(ctx.currentTime + 0.15);
        },
        fail: function() {
            playTone(200, 0.3, 'sawtooth', 0.2);
        },
        win: function() {
            playTone(523, 0.15, 'sine', 0.3);
            setTimeout(function() { playTone(659, 0.15, 'sine', 0.3); }, 150);
            setTimeout(function() { playTone(784, 0.15, 'sine', 0.3); }, 300);
            setTimeout(function() { playTone(1047, 0.3, 'sine', 0.3); }, 450);
        },
        pop: function() {
            var ctx = getContext();
            var osc = ctx.createOscillator();
            var gain = ctx.createGain();
            osc.connect(gain);
            gain.connect(ctx.destination);
            osc.type = 'sine';
            osc.frequency.setValueAtTime(400, ctx.currentTime);
            osc.frequency.exponentialRampToValueAtTime(100, ctx.currentTime + 0.1);
            gain.gain.setValueAtTime(0.3, ctx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.1);
            osc.start(ctx.currentTime);
            osc.stop(ctx.currentTime + 0.1);
        }
    };
})();
"""


class SoundGenerator:
    """Generates and manages sound effects for playable ads."""

    def __init__(self):
        """Initialize sound generator."""
        pass

    def get_procedural_sounds_script(self) -> str:
        """Get JavaScript for procedural sound effects.

        This returns a script that can be embedded in the playable
        to generate sounds using Web Audio API at runtime.
        No external files needed!

        Returns:
            JavaScript code string
        """
        return PROCEDURAL_SOUNDS_JS

    def get_sound_integration_for_mechanic(self, mechanic_type: str) -> dict:
        """Get recommended sound integration for a mechanic type.

        Returns:
            Dictionary mapping game events to SoundFX method calls
        """
        integrations = {
            "match3": {
                "on_tile_select": "SoundFX.tap()",
                "on_match": "SoundFX.match()",
                "on_score": "SoundFX.score()",
                "on_no_match": "SoundFX.pop()",
            },
            "runner": {
                "on_jump": "SoundFX.jump()",
                "on_collect": "SoundFX.collect()",
                "on_hit": "SoundFX.fail()",
                "on_score": "SoundFX.score()",
            },
            "tapper": {
                "on_tap": "SoundFX.tap()",
                "on_bonus": "SoundFX.collect()",
                "on_multiplier": "SoundFX.match()",
            },
            "merger": {
                "on_merge": "SoundFX.match()",
                "on_upgrade": "SoundFX.score()",
                "on_spawn": "SoundFX.pop()",
            },
            "puzzle": {
                "on_move": "SoundFX.tap()",
                "on_rotate": "SoundFX.pop()",
                "on_clear_row": "SoundFX.match()",
            },
            "shooter": {
                "on_shoot": "SoundFX.pop()",
                "on_hit": "SoundFX.match()",
                "on_miss": "SoundFX.fail()",
            },
        }

        return integrations.get(mechanic_type.lower(), integrations["tapper"])


# =============================================================================
# Pixabay Integration (Optional - requires network)
# =============================================================================

class PixabaySounds:
    """Integration with Pixabay free sound effects.

    Note: Pixabay sounds are royalty-free but require attribution
    unless you have a paid plan. For playable ads, procedural
    sounds are recommended to avoid licensing concerns.
    """

    SEARCH_URL = "https://pixabay.com/api/audio/"

    def __init__(self, api_key: Optional[str] = None):
        """Initialize Pixabay client.

        Args:
            api_key: Pixabay API key (free to obtain)
        """
        self.api_key = api_key

    def search_sounds(
        self,
        query: str,
        category: str = "sound_effects",
        per_page: int = 5,
    ) -> list[dict]:
        """Search for sound effects.

        Args:
            query: Search query
            category: "sound_effects" or "music"
            per_page: Number of results

        Returns:
            List of sound effect metadata
        """
        if not self.api_key:
            return []

        import httpx

        params = {
            "key": self.api_key,
            "q": query,
            "category": category,
            "per_page": per_page,
        }

        try:
            response = httpx.get(self.SEARCH_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data.get("hits", [])
        except Exception:
            return []
