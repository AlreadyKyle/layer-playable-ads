"""Demo playable route."""

from fastapi import APIRouter

from api.schemas import DemoRequest, PlayableResultSchema, MechanicTypeEnum
from src.playable_factory import PlayableFactory
from src.templates.registry import MechanicType

router = APIRouter()


@router.post("/demo", response_model=PlayableResultSchema)
def create_demo(req: DemoRequest):
    factory = PlayableFactory()
    output = factory.create_demo(
        mechanic_type=MechanicType(req.mechanic_type.value),
        game_name=req.game_name,
    )
    return PlayableResultSchema(
        html=output.html,
        file_size_bytes=output.file_size_bytes,
        file_size_formatted=output.file_size_formatted,
        file_size_mb=output.file_size_mb,
        mechanic_type=MechanicTypeEnum(output.mechanic_type.value),
        assets_embedded=output.assets_count,
        is_valid=output.is_valid,
        validation_errors=output.validation_errors,
    )
