import sys
import os
from pathlib import Path

# Fix path
server_dir = Path(__file__).parent / "server"
sys.path.append(str(server_dir.absolute()))

print(f"Python: {sys.executable}")
print(f"CWD: {os.getcwd()}")
print(f"Server Dir: {server_dir}")

try:
    print("\n[1] Testing Imports...")
    from server.utils.document_utils import clean_text
    from server.utils.vector_store import get_vector_store
    print("Imports OK")
except Exception as e:
    print(f"Imports Failed: {e}")

try:
    print("\n[2] Testing Vector Store (ChromaDB)...")
    vs = get_vector_store()
    print(f"Vector Store OK. Collection: {vs.collection.name}")
except Exception as e:
    print(f"Vector Store Failed: {e}")

try:
    print("\n[3] Testing Ollama Connection...")
    import ollama
    models = ollama.list()
    print(f"Ollama OK. Available models: {[m['name'] for m in models.get('models', [])]}")
except Exception as e:
    print(f"Ollama Failed: {e}")

print("\n--- Diagnostics Complete ---")
