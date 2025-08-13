import re
import aiofiles
import os
from fastapi import UploadFile, HTTPException
import logging
from gemini_model import gemini_generate


logger = logging.getLogger("app_logger")

ALLOWED_FILE_TYPES = os.getenv("ALLOWED_FILE_TYPES", "image/png,image/jpeg").split(",")


def sanitize_input(text: str) -> str:
    clean = re.sub(r"[^\x20-\x7E\n\r\t]", "", text)
    return clean[:500].strip()

def sanitize_filename(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]", "_", os.path.basename(name))

async def save_upload_file(upload_file: UploadFile, destination: str):
    async with aiofiles.open(destination, 'wb') as out_file:
        while content := await upload_file.read(1024):
            await out_file.write(content)
    logger.info(f"Saved file: {destination}")

def validate_upload_file(upload_file: UploadFile):
    if upload_file.content_type not in ALLOWED_FILE_TYPES:
        raise HTTPException(400, detail=f"Unsupported file type: {upload_file.content_type}")

