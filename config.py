import os

class Config:
    UPLOAD_FOLDER = "uploads"
    SAVED_FOLDER = "saved_audios"
    MAX_COUNT_LENGTH = 30 * 1024 * 1024

    FREESOUND_API_KEY = os.getenv(
        "FREESOUND_API_KEY",
    )