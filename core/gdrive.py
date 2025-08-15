"""Utilities for uploading and downloading CSV files to Google Drive."""

from __future__ import annotations

import io
from typing import Optional

import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload

from .gdrive_config import CREDENTIALS_FILE, FOLDER_ID

SCOPES = ["https://www.googleapis.com/auth/drive.file"]


def _drive_service():
    creds = service_account.Credentials.from_service_account_file(
        CREDENTIALS_FILE, scopes=SCOPES
    )
    return build("drive", "v3", credentials=creds)


def upload_df(df: pd.DataFrame, filename: str) -> Optional[str]:
    """Upload a DataFrame as CSV to Google Drive.

    Returns the file ID if successful.
    """
    service = _drive_service()
    file_metadata = {"name": filename}
    if FOLDER_ID:
        file_metadata["parents"] = [FOLDER_ID]
    stream = io.BytesIO(df.to_csv(index=False).encode("utf-8"))
    media = MediaIoBaseUpload(stream, mimetype="text/csv")
    file = (
        service.files()
        .create(body=file_metadata, media_body=media, fields="id")
        .execute()
    )
    return file.get("id")


def download_df(filename: str) -> Optional[pd.DataFrame]:
    """Download a CSV from Google Drive into a DataFrame.

    Looks for a file with the given name inside the configured folder.
    Returns ``None`` if the file is not found.
    """
    service = _drive_service()
    query = f"name='{filename}'"
    if FOLDER_ID:
        query += f" and '{FOLDER_ID}' in parents"
    results = (
        service.files()
        .list(q=query, spaces="drive", fields="files(id,name)", pageSize=1)
        .execute()
    )
    items = results.get("files", [])
    if not items:
        return None
    file_id = items[0]["id"]
    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    fh.seek(0)
    return pd.read_csv(fh)
