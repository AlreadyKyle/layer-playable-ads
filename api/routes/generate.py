"""Asset generation route."""

from fastapi import APIRouter

from api.schemas import (
    GenerateAssetsRequest,
    GeneratedAssetSetSchema,
    GeneratedAssetSchema,
    MechanicTypeEnum,
)
from src.analysis.game_analyzer import GameAnalysis, VisualStyle, AssetNeed
from src.generation.game_asset_generator import GameAssetGenerator
from src.templates.registry import MechanicType

router = APIRouter()


def _schema_to_analysis(data) -> GameAnalysis:
    """Convert API schema back to GameAnalysis dataclass."""
    return GameAnalysis(
        game_name=data.game_name,
        publisher=data.publisher,
        mechanic_type=MechanicType(data.mechanic_type.value),
        mechanic_confidence=data.mechanic_confidence,
        mechanic_reasoning=data.mechanic_reasoning,
        visual_style=VisualStyle(
            art_type=data.visual_style.art_type,
            color_palette=data.visual_style.color_palette,
            theme=data.visual_style.theme,
            mood=data.visual_style.mood,
        ),
        assets_needed=[
            AssetNeed(
                key=a.key,
                description=a.description,
                game_specific_prompt=a.game_specific_prompt,
            )
            for a in data.assets_needed
        ],
        recommended_template=data.recommended_template,
        template_config=data.template_config,
        core_loop_description=data.core_loop_description,
        hook_suggestion=data.hook_suggestion,
        cta_suggestion=data.cta_suggestion,
        raw_analysis=data.raw_analysis,
    )


@router.post("/generate-assets", response_model=GeneratedAssetSetSchema)
def generate_assets(req: GenerateAssetsRequest):
    analysis = _schema_to_analysis(req.analysis)
    generator = GameAssetGenerator()
    asset_set = generator.generate_for_game(
        analysis=analysis,
        style_id=req.style_id,
    )
    return GeneratedAssetSetSchema(
        game_name=asset_set.game_name,
        mechanic_type=MechanicTypeEnum(asset_set.mechanic_type.value),
        assets={
            key: GeneratedAssetSchema(
                key=a.key,
                prompt=a.prompt,
                image_url=a.image_url,
                base64_data=a.base64_data,
                generation_time=a.generation_time,
                width=a.width,
                height=a.height,
                error=a.error,
                is_valid=a.is_valid,
            )
            for key, a in asset_set.assets.items()
        },
        total_generation_time=asset_set.total_generation_time,
        style_id=asset_set.style_id,
        valid_count=asset_set.valid_count,
    )
