"""
Storage Service

Decouples file storage management (saving, reading, unlinking) from business logic.
Supports user-isolated directory structures: `./uploads/{user_id}/{resume_uuid}.pdf`.
"""

import os
import shutil
import logging
import uuid
from pathlib import Path
from fastapi import UploadFile

logger = logging.getLogger(__name__)

BASE_UPLOAD_DIR = Path("uploads")


class StorageService:
    """
    Service encapsulating file storage operations.
    """

    @staticmethod
    async def save_resume_file(user_id: uuid.UUID, file: UploadFile) -> str:
        """
        Saves uploaded file to a user-isolated folder under `./uploads/{user_id}/`.
        Generates a unique UUID filename while preserving file extension.

        Returns:
            Relative file path string on disk.
        """
        user_dir = BASE_UPLOAD_DIR / str(user_id)
        user_dir.mkdir(parents=True, exist_ok=True)

        original_ext = Path(file.filename or "").suffix or ".pdf"
        unique_filename = f"{uuid.uuid4()}{original_ext}"
        destination = user_dir / unique_filename

        with open(destination, "wb") as out_file:
            shutil.copyfileobj(file.file, out_file)

        logger.info(f"Saved uploaded resume to {destination}")
        return str(destination).replace("\\", "/")

    @staticmethod
    def delete_file(file_path: str) -> bool:
        """
        Safely deletes file from disk if it exists.
        """
        if not file_path:
            return False

        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
                logger.info(f"Deleted file from disk: {file_path}")
                return True
            else:
                logger.warning(f"File not found on disk for deletion: {file_path}")
        except Exception as exc:
            logger.error(f"Failed to delete file '{file_path}': {exc}")

        return False
