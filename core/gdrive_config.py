"""Configuration for Google Drive integration."""
from core.utils import load_config

app_config = load_config()

# Path to service account credentials JSON file
TOKEN_FILE = app_config.get("GDRIVE_TOKEN_FILE", "gdrive_credentials.json")
CLIENT_SECRET = app_config.get("GDRIVE_CLIENT_SECRET", "gdrive_credentials.json")

# Folder ID in Google Drive where CSV files are stored
FOLDER_ID = app_config.get("GDRIVE_FOLDER_ID", "")
