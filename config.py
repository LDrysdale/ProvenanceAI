# config.py

import os
from dotenv import load_dotenv
import sys
import logging



load_dotenv()

def get_env(key: str, default=None, required=False, cast=str):
    value = os.getenv(key, default)
    if required and value is None:
        raise ValueError(f"Missing required environment variable: {key}")
    try:
        return cast(value)
    except Exception as e:
        raise ValueError(f"Invalid type for {key}: {e}")

# Core behavior
USE_LOCAL_DATA = get_env("USE_LOCAL_DATA", default="1", cast=int)  # 1 = use mock_users.json, 0 = Firebase

# Rate limiting
RATE_LIMIT = get_env("RATE_LIMIT", default="5/minute")

# CORS
ALLOWED_ORIGINS = get_env("ALLOWED_ORIGINS", default="http://localhost:5173").split(",")

# Upload limits
MAX_FILE_SIZE_MB = get_env("MAX_FILE_SIZE_MB", default="5", cast=int)
MAX_FILE_SIZE = MAX_FILE_SIZE_MB * 1024 * 1024  # bytes

ALLOWED_FILE_TYPES = get_env("ALLOWED_FILE_TYPES", default="image/png,image/jpeg").split(",")

# Firebase path
FIREBASE_CREDENTIALS_PATH = get_env("FIREBASE_CREDENTIALS_PATH", default="credentials/firebase-adminsdk.json")

# Paths
MOCK_USERS_FILE = get_env("MOCK_USERS_FILE", default="tests/datasets/mock_users.json")

# Model settings
MODEL_PATH = get_env("MODEL_PATH", default="mistral-7b-instruct-v0.1.Q2_K.gguf")
VECTOR_STORE_DIR = get_env("VECTOR_STORE_DIR", default="./data/vector_store")



# Optional: configure basic logging if used outside FastAPI context
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

REQUIRED_ENV_VARS = [
    "RATE_LIMIT",
    "ALLOWED_ORIGINS",
    "MAX_FILE_SIZE_MB",
    "ALLOWED_FILE_TYPES",
    "FIREBASE_CREDENTIALS_PATH",
    "MODEL_PATH",
]

missing_vars = [var for var in REQUIRED_ENV_VARS if os.getenv(var) is None]

if missing_vars:
    logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
    sys.exit(1)  # Prevent the app from starting






