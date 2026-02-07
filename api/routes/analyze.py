"""Game analysis route."""

from typing import Optional

from fastapi import APIRouter, File, Form, UploadFile

from api.schemas import GameAnalysisSchema, VisualStyleSchema, AssetNeedSchema, ConfidenceLevelEnum, MechanicTypeEnum
from src.analysis.game_analyzer import GameAnalyzerSync

router = APIRouter()


def _analysis_to_schema(analysis) -> GameAnalysisSchema:
    """Convert a GameAnalysis dataclass to Pydantic schema."""
    return GameAnalysisSchema(
        game_name=analysis.game_name,
        publisher=analysis.publisher,
        mechanic_type=MechanicTypeEnum(analysis.mechanic_type.value),
        mechanic_confidence=analysis.mechanic_confidence,
        mechanic_reasoning=analysis.mechanic_reasoning,
        visual_style=VisualStyleSchema(
            art_type=analysis.visual_style.art_type,
            color_palette=analysis.visual_style.color_palette,
            theme=analysis.visual_style.theme,
            mood=analysis.visual_style.mood,
        ),
        assets_needed=[
            AssetNeedSchema(
                key=a.key,
                description=a.description,
                game_specific_prompt=a.game_specific_prompt,
            )
            for a in analysis.assets_needed
        ],
        recommended_template=analysis.recommended_template,
        template_config=analysis.template_config,
        core_loop_description=analysis.core_loop_description,
        hook_suggestion=analysis.hook_suggestion,
        cta_suggestion=analysis.cta_suggestion,
        confidence_level=ConfidenceLevelEnum(analysis.confidence_level.value),
        raw_analysis=analysis.raw_analysis,
    )


@router.post("/analyze", response_model=GameAnalysisSchema)
async def analyze_game(
    screenshots: list[UploadFile] = File(...),
    game_name: Optional[str] = Form(None),
):
    screenshot_bytes = [await f.read() for f in screenshots]
    analyzer = GameAnalyzerSync()
    analysis = analyzer.analyze_screenshots(
        screenshot_bytes,
        game_name_hint=game_name,
    )
    return _analysis_to_schema(analysis)
