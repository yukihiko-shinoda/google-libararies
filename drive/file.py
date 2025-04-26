"""The module for files of Google Drive."""

from logging import getLogger
from pathlib import Path
from typing import TYPE_CHECKING

from googlelibraries.drive.api import GoogleDrive

if TYPE_CHECKING:
    from collections.abc import Generator

    from googleapiclient._apis.drive.v3.schemas import File as FileSchema


class File:
    """The file of Google Drive."""

    def __init__(self, drive: GoogleDrive, directory_cache: Path, folder_name: str, file_name_contains: str) -> None:
        self.logger = getLogger(__name__)
        self.drive = drive
        self.directory_cache = directory_cache
        self.folder_name = folder_name
        self.file_name_contains = file_name_contains
        self.file: File | None = None

    def get_first(self) -> Path:
        return self.get(1).__next__()

    def get(self, number: int) -> "Generator[Path]":
        files = self.drive.get_files_in_folder(self.folder_name, self.file_name_contains)
        for _ in range(number):
            yield from self._get(files)

    def _get(self, files: "Generator[FileSchema]") -> "Generator[Path]":
        try:
            file = next(files)
        except StopIteration:
            self.logger.warning("No more files found in folder: %s", self.folder_name)
        else:
            yield self.ensure_file_downloaded(file)

    def ensure_file_downloaded(self, file: "FileSchema") -> Path:
        file_name = file["name"]
        file_id = file["id"]
        self.logger.debug("%s (%s)", file_name, file_id)
        path_download = self.directory_cache / file_name
        self.download_if_not_exists(file_id, path_download)
        return path_download

    def download_if_not_exists(self, file_id: str, path_download: Path) -> None:
        if path_download.exists():
            self.logger.debug("File already exists: %s", path_download)
            return
        self.drive.download_file(file_id, path_download)


class FileFactory:
    def __init__(self, directory_cache: Path) -> None:
        self.directory_cache = directory_cache
        self.drive = GoogleDrive()

    def create(self, folder_name: str, file_name_contains: str) -> File:
        return File(self.drive, self.directory_cache, folder_name, file_name_contains)
