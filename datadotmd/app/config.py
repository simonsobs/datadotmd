"""Configuration for the DataDotMD application using pydantic-settings."""

from pathlib import Path
from urllib.parse import urlparse
from pydantic_settings import BaseSettings, SettingsConfigDict
import notifiers


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application settings
    app_name: str = "DataDotMD"
    root_directory_name: str = "Root"
    app_base_url: str = "http://localhost:8000"
    debug: bool = False

    # Data directory settings
    data_root: Path = Path("data")

    # Database settings
    database_url: str = "sqlite:///./datadotmd.db"

    # Pagination settings
    items_per_page: int = 10

    # Auto-scan settings
    enable_auto_scan: bool = False
    auto_scan_interval_minutes: int = 60

    # Notifications -- Note you need to set the NOTIFIERS_X environment variables
    # to give the correct credentials.
    notifier_name: str = "mock"

    @property
    def notifier(self):
        """Get the configured notifier instance."""
        if self.notifier_name == "mock":

            class MockNotifier:
                def notify(self, *args, **kwargs):
                    print(f"Mock notification: args={args}, kwargs={kwargs}")

            return MockNotifier()
        return notifiers.get_notifier(self.notifier_name)

    def get_root_path(self) -> str:
        """Extract root path from app_base_url.

        Examples:
            http://localhost:8000 -> ""
            http://example.com/datadotmd -> "/datadotmd"
            http://example.com/api/v1/datadotmd -> "/api/v1/datadotmd"
        """
        parsed = urlparse(self.app_base_url)
        path = parsed.path.rstrip("/")
        return path


settings = Settings()
