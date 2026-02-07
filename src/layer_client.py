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
    RetryError,
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


@dataclass
class StyleRecipe:
    """
    Style Recipe extracted from competitor analysis.

    Contains structured style information for Layer.ai asset generation.
    Maps to the PRD's StyleRecipe schema (FR-A4).
    """
    style_name: str
    prefix: list[str] = field(default_factory=list)
    technical: list[str] = field(default_factory=list)
    negative: list[str] = field(default_factory=list)
    palette_primary: str = "#000000"
    palette_accent: str = "#FFFFFF"
    reference_image_id: Optional[str] = None

    def to_style_config(self) -> "StyleConfig":
        """Convert StyleRecipe to StyleConfig for generation."""
        return StyleConfig(
            name=self.style_name,
            description=f"Style: {self.style_name}",
            style_keywords=self.prefix + self.technical,
            negative_keywords=self.negative,
            reference_image_id=self.reference_image_id,
        )

    def to_dict(self) -> dict:
        """Convert to dictionary matching PRD schema."""
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
    def from_dict(cls, data: dict) -> "StyleRecipe":
        """Create StyleRecipe from dictionary."""
        palette = data.get("palette", {})
        return cls(
            style_name=data.get("styleName", "Unknown Style"),
            prefix=data.get("prefix", []),
            technical=data.get("technical", []),
            negative=data.get("negative", []),
            palette_primary=palette.get("primary", "#000000"),
            palette_accent=palette.get("accent", "#FFFFFF"),
            reference_image_id=data.get("referenceImageId"),
        )


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


def _extract_error_message(error: Exception) -> str:
    """Extract a clean error message from various exception types."""
    original_error = error

    # Handle tenacity RetryError - unwrap to get the actual error
    if isinstance(error, RetryError):
        try:
            if error.last_attempt:
                exc = error.last_attempt.exception()
                if exc:
                    error = exc
        except Exception as unwrap_err:
            logger.debug("Could not unwrap RetryError", error=str(unwrap_err))

    # Handle httpx HTTPStatusError
    if isinstance(error, httpx.HTTPStatusError):
        status = error.response.status_code
        # Try to get response body for more details
        try:
            body = error.response.text[:200] if error.response.text else ""
        except Exception:
            body = ""

        if status == 401:
            return f"Authentication failed (HTTP 401) - check your LAYER_API_KEY. {body}"
        elif status == 403:
            return f"Access forbidden (HTTP 403) - check API key permissions. {body}"
        elif status == 404:
            return f"API endpoint not found (HTTP 404) - check LAYER_API_URL. {body}"
        elif status == 429:
            return "Rate limited (HTTP 429) - too many requests, please wait"
        elif status >= 500:
            return f"Layer.ai server error (HTTP {status}) - try again later"
        else:
            return f"HTTP error {status}: {body if body else 'Unknown error'}"

    # Handle connection errors
    if isinstance(error, httpx.ConnectError):
        return "Cannot connect to Layer.ai API - check your internet connection"

    if isinstance(error, httpx.TimeoutException):
        return "Request timed out - Layer.ai API is slow or unavailable"

    # Default: return string representation but clean it up
    msg = str(error)
    # Remove ugly Future/state info from tenacity errors but try to extract HTTP status
    if "Future at" in msg and "state=" in msg:
        # Try to find HTTP status code in the message
        if "HTTPStatusError" in msg:
            if "401" in msg:
                return "Authentication failed (HTTP 401) - verify your LAYER_API_KEY is correct"
            elif "403" in msg:
                return "Access forbidden (HTTP 403) - API key may not have workspace access"
            elif "404" in msg:
                return "API not found (HTTP 404) - check LAYER_API_URL setting"
            else:
                # Extract HTTP status code more precisely (look for "status_code" or HTTP pattern)
                import re
                # Look for patterns like "status_code=400" or "HTTP/1.1 400" or "Client error '400"
                match = re.search(r'(?:status_code[=:]?\s*|HTTP/\d\.\d\s+|error\s+[\'"]?)(\d{3})', msg)
                if match:
                    code = match.group(1)
                    # Only use if it looks like a valid HTTP status code (4xx or 5xx for errors)
                    if code.startswith(('4', '5')):
                        return f"API request failed (HTTP {code}) - check API credentials"
        return "API request failed after multiple retries - check your API credentials"

    # If it's a GraphQL error, try to extract the message
    if "API error:" in msg:
        return msg

    return msg


# =============================================================================
# GraphQL Operations
# =============================================================================

# Layer.ai GraphQL API - validated against actual schema
# API endpoint: api.app.layer.ai

QUERIES = {
    "get_workspace_usage": """
        query GetWorkspaceUsage($input: GetWorkspaceUsageInput!) {
            getWorkspaceUsage(input: $input) {
                __typename
                ... on WorkspaceUsage {
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

    "get_inferences_by_id": """
        query GetInferencesById($input: GetInferencesByIdInput!) {
            getInferencesById(input: $input) {
                __typename
                ... on InferencesResult {
                    inferences {
                        id
                        status
                        errorCode
                        files {
                            id
                            status
                            url
                        }
                    }
                }
                ... on Error {
                    code
                    message
                }
            }
        }
    """,

    "get_style_by_id": """
        query GetStyleById($input: GetStyleByIdInput!) {
            getStyleById(input: $input) {
                __typename
                ... on Style {
                    id
                    name
                    status
                    type
                }
                ... on Error {
                    code
                    message
                }
            }
        }
    """,

    "list_styles": """
        query ListStyles($input: ListStylesInput!) {
            listStyles(input: $input) {
                __typename
                ... on StylesConnection {
                    edges {
                        node {
                            id
                            name
                            status
                            type
                        }
                    }
                }
                ... on Error {
                    code
                    message
                }
            }
        }
    """,
}

MUTATIONS = {
    "generate_images": """
        mutation GenerateImages($input: GenerateImagesInput!) {
            generateImages(input: $input) {
                __typename
                ... on Inference {
                    id
                    status
                    files {
                        id
                        status
                        url
                    }
                }
                ... on Error {
                    type
                    code
                    message
                }
            }
        }
    """,

    "create_style": """
        mutation CreateStyle($input: CreateStyleInput!) {
            createStyle(input: $input) {
                __typename
                ... on Style {
                    id
                    name
                    status
                }
                ... on Error {
                    code
                    message
                }
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
        timeout: Optional[float] = None,
    ):
        settings = get_settings()
        self.api_url = api_url or settings.layer_api_url
        self.api_key = api_key or settings.layer_api_key
        self.workspace_id = workspace_id or settings.layer_workspace_id
        self.timeout = timeout or 60.0  # Default 60s, but can be overridden

        self._client: Optional[httpx.AsyncClient] = None
        self._logger = logger.bind(component="LayerClient")

    async def __aenter__(self) -> "LayerClient":
        # Layer.ai uses Bearer token authentication with Personal Access Tokens
        self._client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "x-api-key": self.api_key,  # Fallback header some APIs use
                "Content-Type": "application/json",
            },
            timeout=self.timeout,
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
            clean_msg = _extract_error_message(e)
            self._logger.error("Request timeout", error=clean_msg)
            raise LayerAPIError(f"Request timeout: {clean_msg}")
        except httpx.RequestError as e:
            clean_msg = _extract_error_message(e)
            self._logger.error("Request failed", error=clean_msg)
            raise LayerAPIError(f"Request failed: {clean_msg}")

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
            # GetWorkspaceUsageInput requires workspaceId and filtering fields
            # filtering is required but can be empty array to get all usage
            data = await self._execute(
                QUERIES["get_workspace_usage"],
                {
                    "input": {
                        "workspaceId": self.workspace_id,
                        "filtering": [],
                    }
                },
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
            self._logger.warning(
                "Failed to get workspace info, blocking operations for safety",
                error=str(e),
                error_type=type(e).__name__,
            )
            return WorkspaceInfo(
                workspace_id=self.workspace_id,
                credits_available=0,
                has_access=False,
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
        style_id: str,
        style: Optional[StyleConfig] = None,
        reference_image_id: Optional[str] = None,
    ) -> GeneratedImage:
        """
        Generate an image using Layer.ai.

        Args:
            prompt: Text description of the image to generate
            style_id: REQUIRED Layer.ai style ID
            style: Optional style configuration for prompt enhancement
            reference_image_id: Optional reference image for style consistency

        Returns:
            GeneratedImage with result or status
        """
        if not style_id:
            raise LayerAPIError("style_id is required for image generation")

        # Build full prompt with style keywords if provided
        full_prompt = prompt
        if style:
            full_prompt = style.to_prompt_prefix() + prompt

        self._logger.info(
            "Starting image generation",
            prompt_preview=full_prompt[:80],
            style_id=style_id,
        )

        # Build input for Layer.ai API - styleId is REQUIRED
        input_data: dict[str, Any] = {
            "workspaceId": self.workspace_id,
            "styleId": style_id,
            "prompt": full_prompt,
        }

        try:
            data = await self._execute(
                MUTATIONS["generate_images"],
                {"input": input_data},
            )

            result = data.get("generateImages", {})

            # Check for error response
            if result.get("__typename") == "Error":
                error_msg = result.get("message", "Unknown error")
                raise LayerAPIError(f"Generation failed: {error_msg}")

            # Extract inference data
            inference_id = result.get("id")
            status_str = result.get("status", "PENDING")
            files = result.get("files", [])

            # Map Layer.ai status to internal status
            # API uses: IN_PROGRESS, COMPLETE, FAILED, CANCELLED, DELETED
            status_map = {
                "IN_PROGRESS": GenerationStatus.PROCESSING,
                "COMPLETE": GenerationStatus.COMPLETED,
                "FAILED": GenerationStatus.FAILED,
                "CANCELLED": GenerationStatus.FAILED,
                "DELETED": GenerationStatus.FAILED,
            }
            status = status_map.get(status_str, GenerationStatus.PROCESSING)

            # Extract image URL from files if available
            image_url = None
            image_id = None
            if files:
                first_file = files[0]
                image_id = first_file.get("id")
                image_url = first_file.get("url")

            self._logger.info("Generation started", inference_id=inference_id, status=status_str)

            return GeneratedImage(
                task_id=inference_id or "",
                status=status,
                image_url=image_url,
                image_id=image_id,
                prompt=full_prompt,
            )

        except LayerAPIError:
            raise
        except Exception as e:
            clean_msg = _extract_error_message(e)
            self._logger.error("Generation failed", error=clean_msg)
            raise LayerAPIError(f"Generation failed: {clean_msg}")

    async def get_generation_status(self, inference_id: str) -> GeneratedImage:
        """Get current status of a generation task."""
        try:
            data = await self._execute(
                QUERIES["get_inferences_by_id"],
                {"input": {"inferenceIds": [inference_id]}},
            )

            result = data.get("getInferencesById", {})

            # Check for error response
            if result.get("__typename") == "Error":
                error_msg = result.get("message", "Unknown error")
                return GeneratedImage(
                    task_id=inference_id,
                    status=GenerationStatus.FAILED,
                    error_message=error_msg,
                )

            # Get first inference from result
            inferences = result.get("inferences", [])
            if not inferences:
                return GeneratedImage(
                    task_id=inference_id,
                    status=GenerationStatus.PROCESSING,
                )

            inference = inferences[0]
            status_str = inference.get("status", "PENDING")
            error_code = inference.get("errorCode")
            files = inference.get("files", [])

            # Map Layer.ai status to our status
            # API uses: IN_PROGRESS, COMPLETE, FAILED, CANCELLED, DELETED
            status_map = {
                "IN_PROGRESS": GenerationStatus.PROCESSING,
                "COMPLETE": GenerationStatus.COMPLETED,
                "FAILED": GenerationStatus.FAILED,
                "CANCELLED": GenerationStatus.FAILED,
                "DELETED": GenerationStatus.FAILED,
            }
            status = status_map.get(status_str, GenerationStatus.PROCESSING)

            # Extract image URL from files
            image_url = None
            image_id = None
            if files:
                first_file = files[0]
                image_id = first_file.get("id")
                file_status = first_file.get("status")
                image_url = first_file.get("url")

                # If file is completed, mark as completed
                # API uses "COMPLETE" not "COMPLETED"
                if file_status == "COMPLETE" and image_url:
                    status = GenerationStatus.COMPLETED

            return GeneratedImage(
                task_id=inference_id,
                status=status,
                image_url=image_url,
                image_id=image_id,
                error_message=error_code,
            )
        except LayerAPIError:
            raise
        except Exception as e:
            # If we can't get status, return processing
            return GeneratedImage(
                task_id=inference_id,
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
        style_id: str,
        style: Optional[StyleConfig] = None,
        reference_image_id: Optional[str] = None,
    ) -> GeneratedImage:
        """Generate an image and wait for completion."""
        initial_result = await self.generate_image(prompt, style_id, style, reference_image_id)

        # If already completed (image URL present), return immediately
        if initial_result.status == GenerationStatus.COMPLETED and initial_result.image_url:
            return initial_result

        # Otherwise poll for completion
        if not initial_result.task_id:
            raise LayerAPIError("Generation failed: no inference ID returned")

        result = await self.poll_generation(initial_result.task_id)
        result.prompt = prompt
        return result

    # =========================================================================
    # Image Operations
    # =========================================================================

    async def get_image(self, image_id: str) -> dict[str, Any]:
        """Get image details by ID.

        Note: Not yet implemented - requires Layer.ai image query schema.
        """
        raise NotImplementedError(
            "get_image() requires a 'get_image' query to be defined in QUERIES. "
            "Add the appropriate Layer.ai GraphQL query before using this method."
        )

    async def download_image(self, image_url: str) -> bytes:
        """Download image bytes from URL."""
        client = self._ensure_client()
        response = await client.get(image_url, follow_redirects=True)
        response.raise_for_status()
        return response.content

    # =========================================================================
    # Style Operations (Module B - FR-B1 to FR-B4)
    # =========================================================================

    async def create_style(self, recipe: "StyleRecipe") -> str:
        """
        Create a new style in Layer.ai from a StyleRecipe.

        Args:
            recipe: StyleRecipe containing style parameters

        Returns:
            Style ID of the created style
        """
        self._logger.info("Creating style", style_name=recipe.style_name)

        input_data = {
            "workspaceId": self.workspace_id,
            "name": recipe.style_name,
            "prefix": recipe.prefix,
            "technical": recipe.technical,
            "negative": recipe.negative,
        }

        try:
            data = await self._execute(
                MUTATIONS["create_style"],
                {"input": input_data},
            )

            style_id = data.get("createStyle", {}).get("id")
            if not style_id:
                raise LayerAPIError("Failed to create style: no ID returned")

            self._logger.info("Style created", style_id=style_id)
            return style_id

        except LayerAPIError:
            raise
        except Exception as e:
            self._logger.error("Style creation failed", error=str(e))
            raise LayerAPIError(f"Style creation failed: {str(e)}")

    async def get_style(self, style_id: str) -> dict[str, Any]:
        """
        Get style details by ID.

        Args:
            style_id: Style ID to retrieve

        Returns:
            Style data dictionary
        """
        self._logger.info("Fetching style", style_id=style_id)

        try:
            data = await self._execute(
                QUERIES["get_style_by_id"],
                {"input": {"styleId": style_id}},
            )
            result = data.get("getStyleById", {})
            if result.get("__typename") == "Error":
                error_msg = result.get("message", "Unknown error")
                raise LayerAPIError(f"Failed to get style: {error_msg}")
            return result
        except LayerAPIError:
            raise
        except Exception as e:
            self._logger.error("Failed to fetch style", error=str(e))
            raise LayerAPIError(f"Failed to fetch style: {str(e)}")

    async def list_styles(
        self,
        limit: int = 20,
        status_filter: Optional[list[str]] = None,
    ) -> list[dict[str, Any]]:
        """
        List styles accessible to the authenticated user.

        Args:
            limit: Maximum number of styles to return
            status_filter: Optional list of status values to filter by (e.g., ["COMPLETE"])

        Returns:
            List of style dicts with id, name, status, type
        """
        self._logger.info("Listing styles", limit=limit, workspace_id=self.workspace_id)

        try:
            # ListStylesInput fields: topics, isFeatured, status, visibility, after, before, first, last
            input_data: dict[str, Any] = {"first": limit}
            if status_filter:
                input_data["status"] = status_filter

            data = await self._execute(
                QUERIES["list_styles"],
                {"input": input_data},
            )

            result = data.get("listStyles", {})

            if result.get("__typename") == "Error":
                error_msg = result.get("message", "Unknown error")
                raise LayerAPIError(f"Failed to list styles: {error_msg}")

            # Extract styles from Relay-style edges/node structure
            edges = result.get("edges", [])
            styles = [edge.get("node") for edge in edges if edge.get("node")]
            self._logger.info("Styles listed", count=len(styles))
            return styles

        except LayerAPIError:
            raise
        except Exception as e:
            self._logger.error("Failed to list styles", error=str(e))
            raise LayerAPIError(f"Failed to list styles: {str(e)}")

    def get_style_dashboard_url(self, style_id: str) -> str:
        """
        Generate Layer.ai dashboard URL for a style.

        Args:
            style_id: Style ID

        Returns:
            Dashboard URL for manual tweaking
        """
        # Extract base URL from API URL
        base_url = self.api_url.replace("/v1/graphql", "").replace("/graphql", "").replace("api.", "")
        return f"{base_url}/workspace/{self.workspace_id}/styles/{style_id}"


# =============================================================================
# Sync Wrapper for Streamlit
# =============================================================================


class LayerClientSync:
    """Synchronous wrapper for LayerClient (for Streamlit compatibility).

    Uses a persistent event loop and shared async client to avoid
    creating a new event loop and HTTP connection per API call.
    """

    def __init__(
        self,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        workspace_id: Optional[str] = None,
        timeout: Optional[float] = None,
    ):
        self._api_url = api_url
        self._api_key = api_key
        self._workspace_id = workspace_id
        self._timeout = timeout
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._client: Optional[LayerClient] = None

    def _ensure_loop(self) -> asyncio.AbstractEventLoop:
        """Get or create a persistent event loop."""
        if self._loop is None or self._loop.is_closed():
            self._loop = asyncio.new_event_loop()
        return self._loop

    def _ensure_client(self) -> LayerClient:
        """Get or create a persistent async client."""
        if self._client is None:
            loop = self._ensure_loop()
            self._client = LayerClient(
                api_url=self._api_url,
                api_key=self._api_key,
                workspace_id=self._workspace_id,
                timeout=self._timeout,
            )
            loop.run_until_complete(self._client.__aenter__())
        return self._client

    def _run(self, coro):
        """Run coroutine synchronously using the persistent event loop."""
        return self._ensure_loop().run_until_complete(coro)

    def close(self):
        """Close the async client and event loop."""
        if self._client is not None:
            try:
                loop = self._ensure_loop()
                loop.run_until_complete(self._client.__aexit__(None, None, None))
            except Exception:
                pass
            self._client = None
        if self._loop is not None and not self._loop.is_closed():
            self._loop.close()
            self._loop = None

    def __del__(self):
        """Cleanup on garbage collection."""
        try:
            self.close()
        except Exception:
            pass

    def get_workspace_info(self) -> WorkspaceInfo:
        """Get workspace info synchronously."""
        client = self._ensure_client()
        return self._run(client.get_workspace_info())

    def check_credits(self) -> WorkspaceInfo:
        """Check credits synchronously."""
        client = self._ensure_client()
        return self._run(client.check_credits())

    def generate_with_polling(
        self,
        prompt: str,
        style_id: str,
        style: Optional[StyleConfig] = None,
        reference_image_id: Optional[str] = None,
    ) -> GeneratedImage:
        """Generate image and wait for completion."""
        client = self._ensure_client()
        return self._run(
            client.generate_with_polling(prompt, style_id, style, reference_image_id)
        )

    def download_image(self, image_url: str) -> bytes:
        """Download image bytes."""
        client = self._ensure_client()
        return self._run(client.download_image(image_url))

    # =========================================================================
    # Style Operations (sync wrappers)
    # =========================================================================

    def create_style(self, recipe: "StyleRecipe") -> str:
        """Create a style in Layer.ai synchronously."""
        client = self._ensure_client()
        return self._run(client.create_style(recipe))

    def get_style(self, style_id: str) -> dict[str, Any]:
        """Get style by ID synchronously."""
        client = self._ensure_client()
        return self._run(client.get_style(style_id))

    def list_styles(
        self,
        limit: int = 20,
        status_filter: Optional[list[str]] = None,
    ) -> list[dict[str, Any]]:
        """List workspace styles synchronously."""
        client = self._ensure_client()
        return self._run(client.list_styles(limit, status_filter))

    def get_style_dashboard_url(self, style_id: str) -> str:
        """Get dashboard URL for a style."""
        settings = get_settings()
        api_url = self._api_url or settings.layer_api_url
        workspace_id = self._workspace_id or settings.layer_workspace_id
        base_url = api_url.replace("/v1/graphql", "").replace("/graphql", "").replace("api.", "")
        return f"{base_url}/workspace/{workspace_id}/styles/{style_id}"


# =============================================================================
# Exports
# =============================================================================

def extract_error_message(error: Exception) -> str:
    """Extract a clean, user-friendly error message from an exception.

    Public wrapper around _extract_error_message for use in other modules.
    """
    return _extract_error_message(error)


__all__ = [
    "LayerClient",
    "LayerClientSync",
    "GeneratedImage",
    "GenerationStatus",
    "WorkspaceInfo",
    "StyleConfig",
    "StyleRecipe",
    "LayerAPIError",
    "InsufficientCreditsError",
    "GenerationTimeoutError",
    "AuthenticationError",
    "QUERIES",
    "MUTATIONS",
    "extract_error_message",
]
