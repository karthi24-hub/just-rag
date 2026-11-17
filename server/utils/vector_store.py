import chromadb
from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer
import os
from pathlib import Path
from typing import List, Dict, Any

class VectorStore:
    def __init__(self, persist_directory: str = None):
        if persist_directory is None:
            # Default to absolute path relative to this file
            persist_directory = str(Path(__file__).parent.parent.parent / "data" / "chroma_db")
        self.persist_directory = persist_directory
        os.makedirs(os.path.dirname(self.persist_directory), exist_ok=True)
        self.client = chromadb.PersistentClient(path=persist_directory)
        # Using a reliable local embedding model
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
        self.collection = self.client.get_or_create_collection(
            name="knowledge_base",
            embedding_function=self.embedding_function
        )

    def add_documents(self, texts: List[str], metadatas: List[Dict[str, Any]], ids: List[str]):
        self.collection.add(
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )

    def query(self, query_text: str, n_results: int = 5) -> Dict[str, Any]:
        return self.collection.query(
            query_texts=[query_text],
            n_results=n_results
        )

    def delete_collection(self):
        self.client.delete_collection("knowledge_base")
        self.collection = self.client.get_or_create_collection(
            name="knowledge_base",
            embedding_function=self.embedding_function
        )

def get_vector_store():
    return VectorStore()
