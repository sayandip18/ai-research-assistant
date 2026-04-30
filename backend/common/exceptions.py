from __future__ import annotations


class AppError(Exception):
    """Base class for all application errors."""


class NotFoundError(AppError):
    """Resource does not exist or the requesting user lacks access."""


class ValidationError(AppError):
    """Business rule violation (distinct from Pydantic validation)."""


class AuthenticationError(AppError):
    """Missing or invalid credentials."""


class AuthorizationError(AppError):
    """Authenticated but not permitted."""


class IngestionError(AppError):
    """Document parsing or embedding failure."""


class AgentStepLimitError(AppError):
    """Agent hit MAX_AGENT_STEPS."""


class ExternalServiceError(AppError):
    """OpenAI, Tavily, or S3 call failed after retries."""
