"""
Shared utilities and configuration for LPS.

Supports both local development (.env) and Streamlit Cloud (st.secrets).
"""

import os
import functools
from pathlib import Path
from typing import Optional

import structlog
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Get the project root directory (parent of src/)
PROJECT_ROOT = Path(__file__).parent.parent.parent
ENV_FILE = PROJECT_ROOT / ".env"


def _load_streamlit_secrets_to_env():
    """
    Load Streamlit Cloud secrets into environment variables.
    This allows the same Settings class to work in both local and cloud environments.
    """
    try:
        import streamlit as st
        if hasattr(st, 'secrets') and len(st.secrets) > 0:
            for key, value in st.secrets.items():
                # Only set if not already in environment (allow local override)
                if key.upper() not in os.environ:
                    os.environ[key.upper()] = str(value)
    except Exception:
        # Not running in Streamlit context, or secrets not available
        pass


# Load Streamlit secrets first (if available)
_load_streamlit_secrets_to_env()

# Then load .env file (local development)
# Use override=True to ensure .env values take precedence over secrets
if ENV_FILE.exists():
    load_dotenv(ENV_FILE, override=True)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Layer.ai API
    layer_api_url: str = Field(
        default="https://api.app.layer.ai/v1/graphql",
        description="Layer.ai GraphQL endpoint",
    )
    layer_api_key: str = Field(
        default="",
        description="Layer.ai API key",
    )
    layer_workspace_id: str = Field(
        default="",
        description="Layer.ai workspace ID",
    )

    # Anthropic Claude
    anthropic_api_key: str = Field(
        default="",
        description="Anthropic API key for Claude",
    )
    claude_model: str = Field(
        default="claude-sonnet-4-20250514",
        description="Claude model for vision analysis",
    )

    # Optional: Supabase
    supabase_url: Optional[str] = Field(
        default=None,
        description="Supabase project URL",
    )
    supabase_key: Optional[str] = Field(
        default=None,
        description="Supabase anon key",
    )

    # Development
    debug: bool = Field(
        default=False,
        description="Enable debug mode",
    )
    log_level: str = Field(
        default="INFO",
        description="Logging level",
    )

    # Forge settings
    forge_poll_timeout: int = Field(
        default=60,
        description="Max seconds to poll forge task status",
    )
    min_credits_required: int = Field(
        default=50,
        description="Minimum credits required to start forging",
    )

    # Playable constraints
    max_playable_size_mb: float = Field(
        default=5.0,
        description="Maximum playable file size in MB",
    )
    max_image_dimension: int = Field(
        default=512,
        description="Maximum image dimension in pixels",
    )


@functools.lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()


def setup_logging(level: Optional[str] = None) -> structlog.BoundLogger:
    """
    Configure structured logging for the application.

    Args:
        level: Override log level (default: from settings)

    Returns:
        Configured logger instance
    """
    settings = get_settings()
    log_level = level or settings.log_level

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.dev.ConsoleRenderer(colors=True),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    return structlog.get_logger()


def validate_api_keys() -> dict[str, bool]:
    """
    Validate that required API keys are configured.

    Returns:
        Dict mapping key names to whether they are set
    """
    settings = get_settings()
    return {
        "layer_api_key": bool(settings.layer_api_key),
        "layer_workspace_id": bool(settings.layer_workspace_id),
        "anthropic_api_key": bool(settings.anthropic_api_key),
    }


def format_file_size(size_bytes: int) -> str:
    """Format byte size to human readable string."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"
