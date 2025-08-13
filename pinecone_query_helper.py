# pinecone_query_helper.py
import os
import pinecone

# Load environment variables
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENV = os.getenv("PINECONE_ENV")

# Define new index name for 384-dim embeddings
PINECONE_INDEX_NAME = "developer-quickstart-py-384"

# Init Pinecone
pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENV)

# Create index if it doesn't exist
if PINECONE_INDEX_NAME not in pinecone.list_indexes():
    print(f"Creating index: {PINECONE_INDEX_NAME} (dimension=384)")
    pinecone.create_index(
        name=PINECONE_INDEX_NAME,
        dimension=384,  # match all-MiniLM-L6-v2 output
        metric="cosine"
    )
else:
    print(f"Index {PINECONE_INDEX_NAME} already exists.")

# Connect to index
index = pinecone.Index(PINECONE_INDEX_NAME)

print(f"Connected to index: {PINECONE_INDEX_NAME}")
