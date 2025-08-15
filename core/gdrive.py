"""Utilities for uploading and downloading CSV files to Google Drive."""

from __future__ import annotations

import io
from typing import Optional

import pandas as pd
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import os
from .gdrive_config import FOLDER_ID, TOKEN_FILE, CLIENT_SECRET

SCOPES = ["https://www.googleapis.com/auth/drive.file"]


def _drive_service():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
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
