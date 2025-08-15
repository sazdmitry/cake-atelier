"""Configuration for Google Drive integration."""

import os

# Path to service account credentials JSON file
CREDENTIALS_FILE = os.getenv("GDRIVE_CREDENTIALS_FILE", "gdrive_credentials.json")

# Folder ID in Google Drive where CSV files are stored
FOLDER_ID = os.getenv("GDRIVE_FOLDER_ID", "")
