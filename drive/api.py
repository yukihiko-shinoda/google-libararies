"""The API about Google Drive."""

import io
from logging import getLogger
from pathlib import Path
from typing import TYPE_CHECKING
from typing import ClassVar

import google.auth
from google.auth.credentials import Credentials
from google.auth.exceptions import DefaultCredentialsError
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

from googlelibraries.credentials_manager import CredentialsManager

if TYPE_CHECKING:
    from collections.abc import Generator

    from googleapiclient._apis.drive.v3.resources import DriveResource
    from googleapiclient._apis.drive.v3.schemas import File


class CredentialsFactory:
    """Creates Google API credentials, preferring application default credentials."""

    # If modifying these scopes, delete the file token.json.
    SCOPES: ClassVar = [
        "https://www.googleapis.com/auth/drive.metadata.readonly",
        "https://www.googleapis.com/auth/drive.readonly",
    ]

    @classmethod
    def create(cls, path_to_credentials: Path | None = None, path_to_token: Path | None = None) -> Credentials:
        """Create credentials, falling back to a file-based token if defaults are unavailable."""
        try:
            return google.auth.default()[0]
        except DefaultCredentialsError:
            if not path_to_credentials or not path_to_token:
                raise
        # For backward compatibility, the credentials are created by the credentials manager if the default credentials cannot be loaded.
        return CredentialsManager(
            cls.SCOPES,
            is_inside_of_container=True,
            path_to_credentials=path_to_credentials,
            path_to_token=path_to_token,
        ).create()


class GoogleDrive:
    """The Google Drive API."""

    def __init__(
        self,
        path_to_credentials: Path | None = None,
        path_to_token: Path | None = None,
    ) -> None:
        self.logger = getLogger(__name__)
        credentials = CredentialsFactory.create(path_to_credentials, path_to_token)
        service: DriveResource = build("drive", "v3", credentials=credentials)
        # Reason: pylint: disable-next=no-member
        self.resource = service.files()

    def get_folder(self, folder_name: str) -> str | None:
        """Gets the folder id by name.

        Args:
            folder_name (str): The name of the folder.
        """
        query = f"mimeType = 'application/vnd.google-apps.folder' and name = '{folder_name}'"
        fields = "nextPageToken, files(id, name)"
        response = self.resource.list(q=query, pageSize=100, fields=fields).execute()
        # this gives us a list of all folders with that name
        files = response.get("files", [])
        # however, we know there is only 1 folder with that name, so we just get the id of the 1st item in the list
        return files[0].get("id")

    def get_files(self) -> list["File"]:
        """Gets the files in the root folder.

        Returns: The list of files.
        """
        response = self.resource.list(pageSize=10, fields="nextPageToken, files(id, name)").execute()
        return response.get("files", [])

    def get_files_in_folder(self, folder_name: str, file_name_contains: str) -> "Generator[File]":
        """Gets the files in the folder.

        Args:
            folder_name: The name of the folder.
            file_name_contains: The name of the file.
        """
        folder_id = self.get_folder(folder_name)
        page_token: str | None = ""
        query = f"'{folder_id}' in parents and name contains '{file_name_contains}'"
        fields = "nextPageToken, files(id, name)"
        while page_token is not None:
            response = self.resource.list(
                q=query,
                orderBy="name desc",
                pageSize=100,
                fields=fields,
                pageToken=page_token,
            ).execute()
            yield from response.get("files", [])
            page_token = response.get("nextPageToken")

    def download_file(self, file_id: str, path_export: Path) -> None:
        """Downloads the file.

        Args:
            file_id: The id of the file.
            path_export: The path to export the file.
        """
        request = self.resource.get_media(fileId=file_id)
        file = io.BytesIO()
        downloader = MediaIoBaseDownload(file, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            self.logger.debug("Download %d.", int(status.progress() * 100))
        path_export.write_bytes(file.getvalue())
