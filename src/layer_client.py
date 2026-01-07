"""
Layer.ai API Client

Simplified client for Layer.ai image generation API.
Uses GraphQL to generate game assets with style consistency.

MVP v1.0 - Focus on core image generation functionality.
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


class GenerationStatus(str, Enum):
    """Status values for generation tasks."""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


@dataclass
class GeneratedImage:
    """Result of an image generation operation."""
    task_id: str
    status: GenerationStatus
    image_url: Optional[str] = None
    image_id: Optional[str] = None
    error_message: Optional[str] = None
    duration_seconds: float = 0.0
    prompt: str = ""


@dataclass
class WorkspaceInfo:
    """Workspace information including credits."""
    workspace_id: str
    credits_available: int = 0
    has_access: bool = True

    @property
    def has_credits(self) -> bool:
        """Check if workspace has available credits."""
        settings = get_settings()
        return self.credits_available >= settings.min_credits_required


@dataclass
class StyleConfig:
    """Configuration for consistent style generation."""
    name: str
    description: str = ""
    style_keywords: list[str] = field(default_factory=list)
    negative_keywords: list[str] = field(default_factory=list)
    reference_image_id: Optional[str] = None

    def to_prompt_prefix(self) -> str:
        """Convert style config to prompt prefix."""
        if self.style_keywords:
            return ", ".join(self.style_keywords) + ", "
        return ""

    def to_negative_prompt(self) -> str:
        """Convert negative keywords to negative prompt string."""
        if self.negative_keywords:
            return ", ".join(self.negative_keywords)
        return ""


# =============================================================================
# Exceptions
# =============================================================================


class LayerAPIError(Exception):
    """Base exception for Layer API errors."""
    pass


class InsufficientCreditsError(LayerAPIError):
    """Raised when workspace has insufficient credits."""
    pass


class GenerationTimeoutError(LayerAPIError):
    """Raised when generation polling times out."""
    pass


class AuthenticationError(LayerAPIError):
    """Raised when API authentication fails."""
    pass


# =============================================================================
# GraphQL Operations
# =============================================================================

# Note: These queries are based on Layer.ai's GraphQL API.
# The actual schema may differ - these should be validated against the API sandbox.

QUERIES = {
    "get_workspace": """
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

    "get_generation_status": """
        query GetGenerationStatus($taskId: ID!) {
            generation(id: $taskId) {
                id
                status
                result {
                    imageUrl
                    imageId
                }
                error {
                    message
                }
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
            }
        }
    """,
}

MUTATIONS = {
    "generate_image": """
        mutation GenerateImage($input: GenerateInput!) {
            generate(input: $input) {
                taskId
                status
            }
        }
    """,
}


# =============================================================================
# Layer.ai API Client
# =============================================================================


class LayerClient:
    """
    Async client for Layer.ai image generation API.

    Usage:
        async with LayerClient() as client:
            info = await client.get_workspace_info()
            result = await client.generate_image("fantasy sword, game asset")
    """

    def __init__(
        self,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        workspace_id: Optional[str] = None,
    ):
        settings = get_settings()
        self.api_url = api_url or settings.layer_api_url
        self.api_key = api_key or settings.layer_api_key
        self.workspace_id = workspace_id or settings.layer_workspace_id

        self._client: Optional[httpx.AsyncClient] = None
        self._logger = logger.bind(component="LayerClient")

    async def __aenter__(self) -> "LayerClient":
        self._client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=60.0,
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    def _ensure_client(self) -> httpx.AsyncClient:
        if self._client is None:
            raise LayerAPIError(
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
        """Execute a GraphQL query or mutation."""
        client = self._ensure_client()

        payload = {"query": query}
        if variables:
            payload["variables"] = variables

        self._logger.debug("Executing GraphQL", query_preview=query[:80])

        try:
            response = await client.post(self.api_url, json=payload)

            # Check for auth errors
            if response.status_code == 401:
                raise AuthenticationError("Invalid API key or unauthorized access")
            if response.status_code == 403:
                raise AuthenticationError("Access forbidden - check API permissions")

            response.raise_for_status()

        except httpx.TimeoutException as e:
            self._logger.error("Request timeout", error=str(e))
            raise LayerAPIError(f"Request timeout: {str(e)}")
        except httpx.RequestError as e:
            self._logger.error("Request failed", error=str(e))
            raise LayerAPIError(f"Request failed: {str(e)}")

        result = response.json()

        if "errors" in result:
            error_msg = result["errors"][0].get("message", "Unknown GraphQL error")
            self._logger.error("GraphQL error", error=error_msg)
            raise LayerAPIError(f"API error: {error_msg}")

        return result.get("data", {})

    # =========================================================================
    # Workspace Operations
    # =========================================================================

    async def get_workspace_info(self) -> WorkspaceInfo:
        """Get workspace information including credit balance."""
        self._logger.info("Fetching workspace info", workspace_id=self.workspace_id)

        try:
            data = await self._execute(
                QUERIES["get_workspace"],
                {"workspaceId": self.workspace_id},
            )

            usage_data = data.get("getWorkspaceUsage", {})

            if usage_data.get("__typename") == "Error":
                error_msg = usage_data.get("message", "Unknown error")
                raise LayerAPIError(f"Failed to get workspace info: {error_msg}")

            entitlement = usage_data.get("entitlement", {})

            info = WorkspaceInfo(
                workspace_id=self.workspace_id,
                credits_available=int(entitlement.get("balance", 0)),
                has_access=entitlement.get("hasAccess", True),
            )

            self._logger.info(
                "Workspace info retrieved",
                credits=info.credits_available,
                has_credits=info.has_credits,
            )
            return info

        except LayerAPIError:
            raise
        except Exception as e:
            self._logger.warning("Failed to get workspace info, using defaults", error=str(e))
            return WorkspaceInfo(
                workspace_id=self.workspace_id,
                credits_available=100,  # Assume credits available
                has_access=True,
            )

    async def check_credits(self) -> WorkspaceInfo:
        """Check credits and raise if insufficient."""
        info = await self.get_workspace_info()
        if not info.has_credits:
            settings = get_settings()
            raise InsufficientCreditsError(
                f"Insufficient credits: {info.credits_available} available, "
                f"{settings.min_credits_required} required"
            )
        return info

    # =========================================================================
    # Image Generation
    # =========================================================================

    async def generate_image(
        self,
        prompt: str,
        style: Optional[StyleConfig] = None,
        reference_image_id: Optional[str] = None,
    ) -> str:
        """
        Start an image generation task.

        Args:
            prompt: Text description of the image to generate
            style: Optional style configuration for consistency
            reference_image_id: Optional reference image for style consistency

        Returns:
            Task ID for polling status
        """
        # Build full prompt with style
        full_prompt = prompt
        if style:
            full_prompt = style.to_prompt_prefix() + prompt

        self._logger.info(
            "Starting image generation",
            prompt_preview=full_prompt[:80],
            has_reference=bool(reference_image_id),
        )

        input_data = {
            "workspaceId": self.workspace_id,
            "prompt": full_prompt,
        }

        # Add negative prompt if style has one
        if style and style.to_negative_prompt():
            input_data["negativePrompt"] = style.to_negative_prompt()

        # Add reference image for style consistency
        ref_id = reference_image_id or (style.reference_image_id if style else None)
        if ref_id:
            input_data["referenceImageId"] = ref_id

        try:
            data = await self._execute(
                MUTATIONS["generate_image"],
                {"input": input_data},
            )

            task_id = data.get("generate", {}).get("taskId")
            if not task_id:
                raise LayerAPIError("Failed to start generation: no task ID returned")

            self._logger.info("Generation started", task_id=task_id)
            return task_id

        except LayerAPIError:
            raise
        except Exception as e:
            self._logger.error("Generation failed", error=str(e))
            raise LayerAPIError(f"Generation failed: {str(e)}")

    async def get_generation_status(self, task_id: str) -> GeneratedImage:
        """Get current status of a generation task."""
        try:
            data = await self._execute(
                QUERIES["get_generation_status"],
                {"taskId": task_id},
            )

            gen_data = data.get("generation", {})
            result_data = gen_data.get("result", {}) or {}
            error_data = gen_data.get("error", {}) or {}

            status_str = gen_data.get("status", "PENDING")
            try:
                status = GenerationStatus(status_str)
            except ValueError:
                status = GenerationStatus.PROCESSING

            return GeneratedImage(
                task_id=task_id,
                status=status,
                image_url=result_data.get("imageUrl"),
                image_id=result_data.get("imageId"),
                error_message=error_data.get("message"),
            )
        except LayerAPIError:
            raise
        except Exception as e:
            # If we can't get status, return processing
            return GeneratedImage(
                task_id=task_id,
                status=GenerationStatus.PROCESSING,
                error_message=str(e),
            )

    async def poll_generation(
        self,
        task_id: str,
        timeout_seconds: Optional[int] = None,
        poll_interval: float = 2.0,
    ) -> GeneratedImage:
        """Poll generation until complete."""
        settings = get_settings()
        timeout = timeout_seconds or settings.forge_poll_timeout
        start_time = time.time()
        current_interval = poll_interval

        self._logger.info("Polling generation", task_id=task_id, timeout=timeout)

        while True:
            elapsed = time.time() - start_time
            if elapsed > timeout:
                raise GenerationTimeoutError(
                    f"Generation {task_id} timed out after {timeout}s"
                )

            result = await self.get_generation_status(task_id)

            if result.status == GenerationStatus.COMPLETED:
                result.duration_seconds = elapsed
                self._logger.info(
                    "Generation completed",
                    task_id=task_id,
                    duration=f"{elapsed:.1f}s",
                )
                return result

            if result.status == GenerationStatus.FAILED:
                raise LayerAPIError(
                    f"Generation failed: {result.error_message or 'Unknown error'}"
                )

            self._logger.debug(
                "Generation in progress",
                task_id=task_id,
                elapsed=f"{elapsed:.1f}s",
            )

            await asyncio.sleep(current_interval)
            current_interval = min(current_interval * 1.5, 10.0)

    async def generate_with_polling(
        self,
        prompt: str,
        style: Optional[StyleConfig] = None,
        reference_image_id: Optional[str] = None,
    ) -> GeneratedImage:
        """Generate an image and wait for completion."""
        task_id = await self.generate_image(prompt, style, reference_image_id)
        result = await self.poll_generation(task_id)
        result.prompt = prompt
        return result

    # =========================================================================
    # Image Operations
    # =========================================================================

    async def get_image(self, image_id: str) -> dict[str, Any]:
        """Get image details by ID."""
        data = await self._execute(
            QUERIES["get_image"],
            {"imageId": image_id},
        )
        return data.get("image", {})

    async def download_image(self, image_url: str) -> bytes:
        """Download image bytes from URL."""
        client = self._ensure_client()
        response = await client.get(image_url, follow_redirects=True)
        response.raise_for_status()
        return response.content


# =============================================================================
# Sync Wrapper for Streamlit
# =============================================================================


class LayerClientSync:
    """Synchronous wrapper for LayerClient (for Streamlit compatibility)."""

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

    def get_workspace_info(self) -> WorkspaceInfo:
        """Get workspace info synchronously."""
        return self._run(self._execute_method("get_workspace_info"))

    def check_credits(self) -> WorkspaceInfo:
        """Check credits synchronously."""
        return self._run(self._execute_method("check_credits"))

    def generate_with_polling(
        self,
        prompt: str,
        style: Optional[StyleConfig] = None,
        reference_image_id: Optional[str] = None,
    ) -> GeneratedImage:
        """Generate image and wait for completion."""
        return self._run(
            self._execute_method(
                "generate_with_polling",
                prompt,
                style,
                reference_image_id,
            )
        )

    def download_image(self, image_url: str) -> bytes:
        """Download image bytes."""
        return self._run(self._execute_method("download_image", image_url))


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "LayerClient",
    "LayerClientSync",
    "GeneratedImage",
    "GenerationStatus",
    "WorkspaceInfo",
    "StyleConfig",
    "LayerAPIError",
    "InsufficientCreditsError",
    "GenerationTimeoutError",
    "AuthenticationError",
]
