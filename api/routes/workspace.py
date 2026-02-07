"""Workspace and styles routes."""

from fastapi import APIRouter

from api.schemas import (
    WorkspaceResponse,
    StylesResponse,
    StyleSchema,
    TemplatesResponse,
    TemplateInfoSchema,
    AssetNeedSchema,
    MechanicTypeEnum,
)
from src.layer_client import LayerClientSync, extract_error_message
from src.utils.helpers import get_settings
from src.templates.registry import TEMPLATE_REGISTRY, list_available_mechanics

router = APIRouter()


@router.get("/workspace", response_model=WorkspaceResponse)
def get_workspace():
    try:
        settings = get_settings()
        client = LayerClientSync(timeout=float(settings.api_fetch_timeout))
        info = client.get_workspace_info()
        return WorkspaceResponse(
            workspace_id=info.workspace_id,
            credits_available=info.credits_available,
            has_access=info.has_access,
        )
    except Exception as e:
        return WorkspaceResponse(error=extract_error_message(e))


@router.get("/styles", response_model=StylesResponse)
def get_styles(limit: int = 50):
    try:
        settings = get_settings()
        client = LayerClientSync(timeout=float(settings.api_fetch_timeout))
        styles = client.list_styles(limit=limit)
        return StylesResponse(
            styles=[
                StyleSchema(
                    id=s["id"],
                    name=s["name"],
                    status=s.get("status", "UNKNOWN"),
                    type=s.get("type"),
                )
                for s in styles
            ]
        )
    except Exception as e:
        return StylesResponse(error=extract_error_message(e))


@router.get("/templates", response_model=TemplatesResponse)
def get_templates():
    templates = []
    for mechanic in list_available_mechanics():
        info = TEMPLATE_REGISTRY[mechanic]
        templates.append(
            TemplateInfoSchema(
                mechanic_type=MechanicTypeEnum(mechanic.value),
                name=info.name,
                description=info.description,
                example_games=info.example_games,
                required_assets=[
                    AssetNeedSchema(
                        key=a.key,
                        description=a.description,
                        game_specific_prompt=a.default_prompt,
                    )
                    for a in info.required_assets
                ],
            )
        )
    return TemplatesResponse(templates=templates)
