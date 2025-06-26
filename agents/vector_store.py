import os
import pickle

VECTOR_STORE_PATH = "./data/vector_store.pkl"

def load_vector_store():
    if not os.path.exists(VECTOR_STORE_PATH):
        return {}
    with open(VECTOR_STORE_PATH, "rb") as f:
        return pickle.load(f)

def save_vector_store(store):
    with open(VECTOR_STORE_PATH, "wb") as f:
        pickle.dump(store, f)

def clear_vector_store():
    if os.path.exists(VECTOR_STORE_PATH):
        os.remove(VECTOR_STORE_PATH)
