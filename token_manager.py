"""Token manager."""

from pathlib import Path

from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

from googlelibraries import DIRECTORY_GCP_SECRET


class TokenManager:
    """Token manager."""

    PATH_TO_TOKEN = DIRECTORY_GCP_SECRET / "token.json"

    def __init__(self, scopes: list[str], *, path_to_token: Path | None = None) -> None:
        self.scopes = scopes
        self.path_to_token = self.PATH_TO_TOKEN if path_to_token is None else path_to_token

    def load_credentials(self) -> Credentials | None:
        """Loads token."""
        if not self.path_to_token.exists():
            return None
        # Reason: The google-auth-oauthlib's issue.
        credentials: Credentials = Credentials.from_authorized_user_file(  # type: ignore[no-untyped-call]
            self.path_to_token,
            self.scopes,
        )
        if credentials.valid:
            return credentials
        if credentials.expired and credentials.refresh_token:
            return self.refresh(credentials)
        return None

    def refresh(self, credentials: Credentials) -> Credentials | None:
        """Refreshes the credentials."""
        # Reason: The google-auth-oauthlib's issue.
        try:
            credentials.refresh(Request())  # type: ignore[no-untyped-call]
        except RefreshError as error:
            message = "('invalid_grant: Bad Request', {'error': 'invalid_grant', 'error_description': 'Bad Request'})"
            if str(error) == message:
                return None
        self.save(credentials)
        return credentials

    def save(self, credentials: Credentials) -> None:
        """Save the credentials for the next run."""
        # Reason: The google-auth-oauthlib's issue.
        self.path_to_token.write_text(credentials.to_json())  # type: ignore[no-untyped-call]
