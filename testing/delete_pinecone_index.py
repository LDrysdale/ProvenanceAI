import pinecone
import os

pinecone.init(api_key=os.getenv("PINECONE_API_KEY"), environment=os.getenv("PINECONE_ENV"))
pinecone.delete_index("developer-quickstart-py")  # old 1024-dim index