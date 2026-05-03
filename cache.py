"""Cache configuration for Google libraries."""

import os
from pathlib import Path


class GoogleLibrariesCache:
    """Configurable cache paths for Google libraries."""

    def __init__(self, base: Path | None = None) -> None:
        if base is None:
            base = Path()
        self.base = base
        self.directory_gcp_secret = base / ".gcp"
        self.path_credentials = self.directory_gcp_secret / "credentials.json"
        self.path_token = self.directory_gcp_secret / "token.json"
        self.directory_google_drive = base / ".google-drive-cache"

    def save_credentials(self, json_str: str) -> None:
        self.directory_gcp_secret.mkdir(parents=True, exist_ok=True)
        self.path_credentials.write_text(json_str)

    def save_application_credentials(self, json_str: str) -> None:
        path_application_credentials = Path(os.environ["GOOGLE_APPLICATION_CREDENTIALS"])
        path_application_credentials.parent.mkdir(parents=True, exist_ok=True)
        path_application_credentials.write_text(json_str, encoding="utf-8")
