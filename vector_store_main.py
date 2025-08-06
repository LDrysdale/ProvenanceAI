import os
import shutil
import logging
from langchain_community.vectorstores import FAISS

logger = logging.getLogger("app_logger")
VECTOR_STORE_DIR = "./data/vector_store"

def persist_vector_store(vector_store):
    if vector_store:
        try:
            vector_store.save_local(VECTOR_STORE_DIR)
            logger.info("Vector store persisted.")
        except Exception as e:
            logger.error(f"Persist error: {e}")

def load_vector_store(embedder):
    try:
        vector_store = FAISS.load_local(VECTOR_STORE_DIR, embedder)
        logger.info("Vector store loaded.")
        return vector_store
    except Exception as e:
        logger.warning("No vector store found or failed to load.")
        return None

def delete_vector_store():
    try:
        if os.path.exists(VECTOR_STORE_DIR):
            shutil.rmtree(VECTOR_STORE_DIR)
        os.makedirs(VECTOR_STORE_DIR, exist_ok=True)
        logger.info("Vector store reset.")
    except Exception as e:
        logger.error(f"Failed to delete vector store: {e}")