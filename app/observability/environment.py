"""Environment helper utilities."""

from app.config.settings import Settings


def is_development(settings: Settings | None) -> bool:
    """Check if the current environment is development."""
    return settings is not None and settings.environment.lower() == "development"
