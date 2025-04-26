"""Credential manager.

see: https://developers.google.com/calendar/api/quickstart/python
"""

from pathlib import Path

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from googlelibraries import DIRECTORY_GCP_SECRET
from googlelibraries.token_manager import TokenManager


class CredentialsManager:
    """Credential manager."""

    PATH_TO_CREDENTIALS = DIRECTORY_GCP_SECRET / "credentials.json"

    def __init__(
        self,
        scopes: list[str],
        *,
        path_to_credentials: Path | None = None,
        path_to_token: Path | None = None,
        is_inside_of_container: bool = False,
    ) -> None:
        self.token_manager = TokenManager(scopes, path_to_token=path_to_token)
        self.scopes = scopes
        # Reason: This code is expected to run in Docker container.
        self.bind_addr = "0.0.0.0" if is_inside_of_container else None  # noqa: S104  # nosec: B104
        self.path_to_credentials = path_to_credentials if path_to_credentials else self.PATH_TO_CREDENTIALS

    def create(self) -> Credentials:
        """Creates credentials.

        The file token.json stores the user's access and refresh tokens, and is created automatically when the
        authorization flow completes for the first time.
        """
        credentials = self.token_manager.load_credentials()
        return credentials if credentials else self.login()

    def login(self) -> Credentials:
        """If there are no (valid) credentials available, let the user log in."""
        flow = InstalledAppFlow.from_client_secrets_file(self.path_to_credentials, self.scopes)
        # Reason: This code is expected to run in Docker container.
        credentials: Credentials = flow.run_local_server(
            port=8000,
            bind_addr=self.bind_addr,
            open_browser=False,
        )
        self.token_manager.save(credentials)
        return credentials
