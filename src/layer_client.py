"""
Layer.ai GraphQL Client

Primary interface for all Layer.ai API interactions.
Handles authentication, style management, forge operations, and asset retrieval.
"""

import asyncio
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

import httpx
import structlog
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from src.utils.helpers import get_settings

logger = structlog.get_logger()


# =============================================================================
# Enums and Data Classes
# =============================================================================


class ForgeTaskStatus(str, Enum):
    """Status values for forge tasks."""

    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


@dataclass
class StyleRecipe:
    """
    Visual style recipe extracted from competitor analysis.

    This is the core data structure for style intelligence.
    """

    style_name: str
    prefix: list[str] = field(default_factory=list)
    technical: list[str] = field(default_factory=list)
    negative: list[str] = field(default_factory=list)
    palette_primary: str = "#000000"
    palette_accent: str = "#FFFFFF"
    reference_image_id: Optional[str] = None

    def to_layer_format(self) -> dict[str, Any]:
        """Convert to Layer.ai createStyle input format."""
        return {
            "name": self.style_name,
            "prefix": self.prefix,
            "technical": self.technical,
            "negative": self.negative,
            "palette": {
                "primary": self.palette_primary,
                "accent": self.palette_accent,
            },
        }

    def to_json(self) -> dict[str, Any]:
        """Convert to JSON-serializable dict (for export/storage)."""
        return {
            "styleName": self.style_name,
            "prefix": self.prefix,
            "technical": self.technical,
            "negative": self.negative,
            "palette": {
                "primary": self.palette_primary,
                "accent": self.palette_accent,
            },
            "referenceImageId": self.reference_image_id,
        }

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "StyleRecipe":
        """Create from JSON dict."""
        palette = data.get("palette", {})
        return cls(
            style_name=data.get("styleName", "Untitled Style"),
            prefix=data.get("prefix", []),
            technical=data.get("technical", []),
            negative=data.get("negative", []),
            palette_primary=palette.get("primary", "#000000"),
            palette_accent=palette.get("accent", "#FFFFFF"),
            reference_image_id=data.get("referenceImageId"),
        )


@dataclass
class ForgeResult:
    """Result of a forge operation."""

    task_id: str
    status: ForgeTaskStatus
    image_url: Optional[str] = None
    image_id: Optional[str] = None
    error_message: Optional[str] = None
    duration_seconds: float = 0.0


@dataclass
class WorkspaceCredits:
    """Workspace credit information."""

    available: int
    used: int
    total: int

    @property
    def is_sufficient(self) -> bool:
        """Check if credits exceed minimum threshold."""
        settings = get_settings()
        return self.available >= settings.min_credits_required


# =============================================================================
# GraphQL Queries and Mutations
# =============================================================================

QUERIES = {
    "get_workspace_credits": """
        query GetWorkspaceUsage($workspaceId: ID!) {
            getWorkspaceUsage(input: {workspaceId: $workspaceId, filtering: []}) {
                __typename
                ... on WorkspaceUsage {
                    workspaceId
                    entitlement {
                        balance
                        hasAccess
                    }
                }
                ... on Error {
                    code
                    message
                }
            }
        }
    """,
    "get_style": """
        query GetStyle($styleId: ID!) {
            style(id: $styleId) {
                id
                name
                prefix
                technical
                negative
                createdAt
                updatedAt
            }
        }
    """,
    "list_styles": """
        query ListStyles($workspaceId: ID!, $limit: Int, $offset: Int) {
            styles(workspaceId: $workspaceId, limit: $limit, offset: $offset) {
                items {
                    id
                    name
                    prefix
                    createdAt
                }
                totalCount
            }
        }
    """,
    "get_forge_task_status": """
        query GetForgeTaskStatus($taskId: ID!) {
            forgeTask(id: $taskId) {
                id
                status
                result {
                    imageUrl
                    imageId
                }
                error {
                    message
                }
                createdAt
                completedAt
            }
        }
    """,
    "get_image": """
        query GetImage($imageId: ID!) {
            image(id: $imageId) {
                id
                url
                width
                height
                format
            }
        }
    """,
}

MUTATIONS = {
    "create_style": """
        mutation CreateStyle($input: CreateStyleInput!) {
            createStyle(input: $input) {
                id
                name
                prefix
                technical
                negative
                createdAt
            }
        }
    """,
    "update_style": """
        mutation UpdateStyle($styleId: ID!, $input: UpdateStyleInput!) {
            updateStyle(id: $styleId, input: $input) {
                id
                name
                prefix
                technical
                negative
                updatedAt
            }
        }
    """,
    "start_forge": """
        mutation StartForge($input: ForgeInput!) {
            forge(input: $input) {
                taskId
                status
            }
        }
    """,
    "upload_image": """
        mutation UploadImage($input: UploadImageInput!) {
            uploadImage(input: $input) {
                id
                url
                uploadUrl
            }
        }
    """,
}


# =============================================================================
# Layer.ai GraphQL Client
# =============================================================================


class LayerClientError(Exception):
    """Base exception for Layer client errors."""

    pass


class InsufficientCreditsError(LayerClientError):
    """Raised when workspace has insufficient credits."""

    pass


class ForgeTimeoutError(LayerClientError):
    """Raised when forge polling times out."""

    pass


class LayerClient:
    """
    Async GraphQL client for Layer.ai API.

    Usage:
        async with LayerClient() as client:
            credits = await client.get_workspace_credits()
            style_id = await client.create_style(recipe)
    """

    def __init__(
        self,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        workspace_id: Optional[str] = None,
    ):
        """
        Initialize the Layer.ai client.

        Args:
            api_url: GraphQL endpoint (default: from settings)
            api_key: API key (default: from settings)
            workspace_id: Workspace ID (default: from settings)
        """
        settings = get_settings()
        self.api_url = api_url or settings.layer_api_url
        self.api_key = api_key or settings.layer_api_key
        self.workspace_id = workspace_id or settings.layer_workspace_id

        self._client: Optional[httpx.AsyncClient] = None
        self._logger = logger.bind(component="LayerClient")

    async def __aenter__(self) -> "LayerClient":
        """Async context manager entry."""
        self._client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()
            self._client = None

    def _ensure_client(self) -> httpx.AsyncClient:
        """Ensure HTTP client is initialized."""
        if self._client is None:
            raise LayerClientError(
                "Client not initialized. Use 'async with LayerClient() as client:'"
            )
        return self._client

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(httpx.HTTPStatusError),
    )
    async def _execute(
        self,
        query: str,
        variables: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Execute a GraphQL query or mutation.

        Args:
            query: GraphQL query/mutation string
            variables: Query variables

        Returns:
            Response data dict

        Raises:
            LayerClientError: On API errors
        """
        client = self._ensure_client()

        payload = {"query": query}
        if variables:
            payload["variables"] = variables

        self._logger.debug("Executing GraphQL", query_preview=query[:50])

        try:
            response = await client.post(self.api_url, json=payload)
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            self._logger.error(
                "HTTP error from Layer.ai API",
                status_code=e.response.status_code,
                response_text=e.response.text[:200],
            )
            raise
        except httpx.TimeoutException as e:
            self._logger.error("Request timeout", error=str(e))
            raise LayerClientError(f"Request timeout: {str(e)}")
        except httpx.RequestError as e:
            self._logger.error("Request failed", error=str(e))
            raise LayerClientError(f"Request failed: {str(e)}")

        result = response.json()

        if "errors" in result:
            error_msg = result["errors"][0].get("message", "Unknown GraphQL error")
            error_details = result["errors"][0].get("extensions", {})
            self._logger.error("GraphQL error", error=error_msg, details=error_details)
            raise LayerClientError(f"GraphQL error: {error_msg}")

        return result.get("data", {})

    # =========================================================================
    # Workspace Operations
    # =========================================================================

    async def get_workspace_credits(self) -> WorkspaceCredits:
        """
        Get current workspace credit balance.

        Returns:
            WorkspaceCredits with available, used, and total credits

        Raises:
            LayerClientError: On API error
        """
        self._logger.info("Fetching workspace credits", workspace_id=self.workspace_id)

        data = await self._execute(
            QUERIES["get_workspace_credits"],
            {"workspaceId": self.workspace_id},
        )

        usage_data = data.get("getWorkspaceUsage", {})

        # Handle error response
        if usage_data.get("__typename") == "Error":
            error_msg = usage_data.get("message", "Unknown error")
            raise LayerClientError(f"Failed to get workspace usage: {error_msg}")

        entitlement = usage_data.get("entitlement", {})
        balance = entitlement.get("balance", 0)

        # Layer.ai uses a balance system, treat balance as available credits
        credits = WorkspaceCredits(
            available=int(balance),
            used=0,  # Not provided by this API
            total=int(balance),  # Total is same as available since we don't have used
        )

        self._logger.info(
            "Credits retrieved",
            available=credits.available,
            sufficient=credits.is_sufficient,
        )
        return credits

    async def check_credits_or_raise(self) -> WorkspaceCredits:
        """
        Check credits and raise if insufficient.

        Returns:
            WorkspaceCredits if sufficient

        Raises:
            InsufficientCreditsError: If credits below threshold
        """
        credits = await self.get_workspace_credits()
        if not credits.is_sufficient:
            settings = get_settings()
            raise InsufficientCreditsError(
                f"Insufficient credits: {credits.available} available, "
                f"{settings.min_credits_required} required"
            )
        return credits

    # =========================================================================
    # Style Operations
    # =========================================================================

    async def create_style(self, recipe: StyleRecipe) -> str:
        """
        Create a new style from a StyleRecipe.

        Args:
            recipe: StyleRecipe containing style parameters

        Returns:
            Created style ID

        Raises:
            LayerClientError: On API error
        """
        self._logger.info("Creating style", style_name=recipe.style_name)

        input_data = {
            "workspaceId": self.workspace_id,
            **recipe.to_layer_format(),
        }

        data = await self._execute(
            MUTATIONS["create_style"],
            {"input": input_data},
        )

        style_id = data.get("createStyle", {}).get("id")
        if not style_id:
            raise LayerClientError("Failed to create style: no ID returned")

        self._logger.info("Style created", style_id=style_id)
        return style_id

    async def get_style(self, style_id: str) -> dict[str, Any]:
        """
        Get style details by ID.

        Args:
            style_id: Style ID

        Returns:
            Style data dict
        """
        data = await self._execute(
            QUERIES["get_style"],
            {"styleId": style_id},
        )
        return data.get("style", {})

    async def list_styles(
        self, limit: int = 20, offset: int = 0
    ) -> tuple[list[dict[str, Any]], int]:
        """
        List styles in the workspace.

        Args:
            limit: Max styles to return
            offset: Pagination offset

        Returns:
            Tuple of (style list, total count)
        """
        data = await self._execute(
            QUERIES["list_styles"],
            {
                "workspaceId": self.workspace_id,
                "limit": limit,
                "offset": offset,
            },
        )

        styles_data = data.get("styles", {})
        return (
            styles_data.get("items", []),
            styles_data.get("totalCount", 0),
        )

    def get_style_dashboard_url(self, style_id: str) -> str:
        """
        Generate deep link to style in Layer.ai dashboard.

        Args:
            style_id: Style ID

        Returns:
            Dashboard URL for manual tweaking
        """
        base_url = "https://app.layer.ai"
        return f"{base_url}/workspace/{self.workspace_id}/styles/{style_id}"

    # =========================================================================
    # Forge Operations
    # =========================================================================

    async def start_forge(
        self,
        style_id: str,
        prompt: str,
        reference_image_id: Optional[str] = None,
        count: int = 1,
    ) -> str:
        """
        Start a forge task to generate images.

        Args:
            style_id: Style to use
            prompt: Generation prompt
            reference_image_id: Optional reference image for consistency
            count: Number of images to generate

        Returns:
            Task ID for polling

        Raises:
            InsufficientCreditsError: If workspace lacks credits
            LayerClientError: On API error
        """
        # Credit guard
        await self.check_credits_or_raise()

        self._logger.info(
            "Starting forge",
            style_id=style_id,
            prompt_preview=prompt[:50],
            reference_image=reference_image_id,
        )

        input_data = {
            "workspaceId": self.workspace_id,
            "styleId": style_id,
            "prompt": prompt,
            "count": count,
        }

        if reference_image_id:
            input_data["referenceImageId"] = reference_image_id

        data = await self._execute(
            MUTATIONS["start_forge"],
            {"input": input_data},
        )

        task_id = data.get("forge", {}).get("taskId")
        if not task_id:
            raise LayerClientError("Failed to start forge: no task ID returned")

        self._logger.info("Forge started", task_id=task_id)
        return task_id

    async def get_forge_status(self, task_id: str) -> ForgeResult:
        """
        Get current status of a forge task.

        Args:
            task_id: Forge task ID

        Returns:
            ForgeResult with status and results
        """
        data = await self._execute(
            QUERIES["get_forge_task_status"],
            {"taskId": task_id},
        )

        task_data = data.get("forgeTask", {})
        result_data = task_data.get("result", {}) or {}
        error_data = task_data.get("error", {}) or {}

        return ForgeResult(
            task_id=task_id,
            status=ForgeTaskStatus(task_data.get("status", "PENDING")),
            image_url=result_data.get("imageUrl"),
            image_id=result_data.get("imageId"),
            error_message=error_data.get("message"),
        )

    async def poll_forge_until_complete(
        self,
        task_id: str,
        timeout_seconds: Optional[int] = None,
        poll_interval: float = 2.0,
    ) -> ForgeResult:
        """
        Poll forge task until completion with exponential backoff.

        Args:
            task_id: Forge task ID
            timeout_seconds: Max wait time (default: from settings)
            poll_interval: Initial poll interval in seconds

        Returns:
            Final ForgeResult

        Raises:
            ForgeTimeoutError: If polling times out
            LayerClientError: If forge fails
        """
        settings = get_settings()
        timeout = timeout_seconds or settings.forge_poll_timeout
        start_time = time.time()
        current_interval = poll_interval

        self._logger.info(
            "Polling forge task",
            task_id=task_id,
            timeout=timeout,
        )

        while True:
            elapsed = time.time() - start_time
            if elapsed > timeout:
                raise ForgeTimeoutError(
                    f"Forge task {task_id} timed out after {timeout}s"
                )

            result = await self.get_forge_status(task_id)

            if result.status == ForgeTaskStatus.COMPLETED:
                result.duration_seconds = elapsed
                self._logger.info(
                    "Forge completed",
                    task_id=task_id,
                    duration=f"{elapsed:.1f}s",
                    image_id=result.image_id,
                )
                return result

            if result.status == ForgeTaskStatus.FAILED:
                raise LayerClientError(
                    f"Forge task failed: {result.error_message or 'Unknown error'}"
                )

            self._logger.debug(
                "Forge in progress",
                task_id=task_id,
                status=result.status,
                elapsed=f"{elapsed:.1f}s",
            )

            await asyncio.sleep(current_interval)
            # Exponential backoff with cap
            current_interval = min(current_interval * 1.5, 10.0)

    async def forge_with_polling(
        self,
        style_id: str,
        prompt: str,
        reference_image_id: Optional[str] = None,
        count: int = 1,
    ) -> ForgeResult:
        """
        Convenience method: start forge and poll until complete.

        Args:
            style_id: Style to use
            prompt: Generation prompt
            reference_image_id: Optional reference image
            count: Number of images

        Returns:
            Completed ForgeResult with image URL/ID
        """
        task_id = await self.start_forge(
            style_id=style_id,
            prompt=prompt,
            reference_image_id=reference_image_id,
            count=count,
        )
        return await self.poll_forge_until_complete(task_id)

    # =========================================================================
    # Image Operations
    # =========================================================================

    async def get_image(self, image_id: str) -> dict[str, Any]:
        """
        Get image details by ID.

        Args:
            image_id: Image ID

        Returns:
            Image data including URL, dimensions, format
        """
        data = await self._execute(
            QUERIES["get_image"],
            {"imageId": image_id},
        )
        return data.get("image", {})

    async def download_image(self, image_url: str) -> bytes:
        """
        Download image bytes from URL.

        Args:
            image_url: Image URL

        Returns:
            Image bytes
        """
        client = self._ensure_client()
        response = await client.get(image_url)
        response.raise_for_status()
        return response.content


# =============================================================================
# Sync Wrapper (for Streamlit compatibility)
# =============================================================================


class LayerClientSync:
    """
    Synchronous wrapper for LayerClient.

    For use with Streamlit which doesn't play well with async.
    """

    def __init__(
        self,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        workspace_id: Optional[str] = None,
    ):
        self._api_url = api_url
        self._api_key = api_key
        self._workspace_id = workspace_id

    def _run(self, coro):
        """Run coroutine synchronously."""
        return asyncio.run(coro)

    async def _execute_method(self, method_name: str, *args, **kwargs):
        """Execute async method."""
        async with LayerClient(
            api_url=self._api_url,
            api_key=self._api_key,
            workspace_id=self._workspace_id,
        ) as client:
            method = getattr(client, method_name)
            return await method(*args, **kwargs)

    def get_workspace_credits(self) -> WorkspaceCredits:
        return self._run(self._execute_method("get_workspace_credits"))

    def create_style(self, recipe: StyleRecipe) -> str:
        return self._run(self._execute_method("create_style", recipe))

    def get_style(self, style_id: str) -> dict[str, Any]:
        return self._run(self._execute_method("get_style", style_id))

    def list_styles(
        self, limit: int = 20, offset: int = 0
    ) -> tuple[list[dict[str, Any]], int]:
        return self._run(self._execute_method("list_styles", limit, offset))

    def forge_with_polling(
        self,
        style_id: str,
        prompt: str,
        reference_image_id: Optional[str] = None,
        count: int = 1,
    ) -> ForgeResult:
        return self._run(
            self._execute_method(
                "forge_with_polling",
                style_id,
                prompt,
                reference_image_id,
                count,
            )
        )

    def get_style_dashboard_url(self, style_id: str) -> str:
        settings = get_settings()
        workspace_id = self._workspace_id or settings.layer_workspace_id
        return f"https://app.layer.ai/workspace/{workspace_id}/styles/{style_id}"
