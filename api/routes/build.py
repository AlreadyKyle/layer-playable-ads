"""Playable build route."""

from fastapi import APIRouter

from api.schemas import (
    BuildPlayableRequest,
    PlayableResultSchema,
    MechanicTypeEnum,
)
from src.analysis.game_analyzer import GameAnalysis, VisualStyle, AssetNeed
from src.generation.game_asset_generator import GeneratedAssetSet, GeneratedAsset
from src.assembly.builder import PlayableBuilder, PlayableConfig
from src.templates.registry import MechanicType

router = APIRouter()


def _to_analysis(data) -> GameAnalysis:
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


def _to_asset_set(data) -> GeneratedAssetSet:
    asset_set = GeneratedAssetSet(
        game_name=data.game_name,
        mechanic_type=MechanicType(data.mechanic_type.value),
        style_id=data.style_id,
    )
    for key, a in data.assets.items():
        asset_set.assets[key] = GeneratedAsset(
            key=a.key,
            prompt=a.prompt,
            image_url=a.image_url,
            image_data=None,
            base64_data=a.base64_data,
            generation_time=a.generation_time,
            width=a.width,
            height=a.height,
            error=a.error,
        )
    return asset_set


@router.post("/build-playable", response_model=PlayableResultSchema)
def build_playable(req: BuildPlayableRequest):
    analysis = _to_analysis(req.analysis)
    assets = _to_asset_set(req.assets)
    config = PlayableConfig(
        game_name=req.config.game_name,
        title=req.config.title,
        store_url=req.config.store_url,
        store_url_ios=req.config.store_url_ios,
        store_url_android=req.config.store_url_android,
        width=req.config.width,
        height=req.config.height,
        background_color=req.config.background_color,
        hook_text=req.config.hook_text,
        cta_text=req.config.cta_text,
        sound_enabled=req.config.sound_enabled,
    )
    builder = PlayableBuilder()
    result = builder.build(analysis, assets, config)
    return PlayableResultSchema(
        html=result.html,
        file_size_bytes=result.file_size_bytes,
        file_size_formatted=result.file_size_formatted,
        file_size_mb=result.file_size_mb,
        mechanic_type=MechanicTypeEnum(result.mechanic_type.value),
        assets_embedded=result.assets_embedded,
        is_valid=result.is_valid,
        validation_errors=result.validation_errors,
    )
