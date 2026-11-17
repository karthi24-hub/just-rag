import sys
import os
from pathlib import Path
import logging

# [New] CRITICAL: Setup logging first thing
# Use a path that is GUARANTEED to be writable in a local setup
log_path = Path(__file__).parent.parent / "server_debug.log"
logging.basicConfig(
    filename=str(log_path.absolute()),
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logging.info(f"Process starting. Python: {sys.executable}")
logging.info(f"CWD: {os.getcwd()}")

try:
    from typing import List, Dict, Any, Optional

    # Add the server directory to sys.path to handle utility imports
    server_dir = str(Path(__file__).parent.absolute())
    sys.path.append(server_dir)
    logging.info(f"Added {server_dir} to sys.path")

    logging.info("Importing mcp...")
    from mcp.server.fastmcp import FastMCP
    
    # Initialize FastMCP server immediately to respond to handshake
    mcp = FastMCP("Universal AI Knowledge Assistant")
    logging.info("FastMCP object created.")

    # Lazy loading containers
    _vector_store = None
    _text_splitter = None

    def get_lazy_vector_store():
        global _vector_store
        if _vector_store is None:
            logging.info("Lazy loading vector store...")
            from utils.vector_store import get_vector_store
            _vector_store = get_vector_store()
        return _vector_store

    def get_lazy_text_splitter():
        global _text_splitter
        if _text_splitter is None:
            logging.info("Lazy loading text splitter...")
            from langchain_text_splitters import RecursiveCharacterTextSplitter
            _text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=100,
                length_function=len,
            )
        return _text_splitter

    logging.info("Server logic ready for lazy initialization.")
except Exception as e:
    logging.error(f"FATAL ERROR DURING STARTUP: {e}", exc_info=True)
    sys.stderr.write(f"FATAL ERROR: {e}\n")
    sys.exit(1)

@mcp.tool()
async def ping() -> str:
    """Simple ping tool to verify connection."""
    return "pong"

@mcp.tool()
async def read_file(file_path: str) -> str:
    """Reads and extracts text from a supported file format."""
    try:
        from utils.document_utils import extract_text, clean_text
        text = extract_text(file_path)
        return clean_text(text)
    except Exception as e:
        return f"Error reading file: {str(e)}"

@mcp.tool()
async def process_document(text: str, filename: str) -> List[Dict[str, Any]]:
    """Cleans, structures, and chunks document content."""
    splitter = get_lazy_text_splitter()
    chunks = splitter.split_text(text)
    processed_chunks = []
    for i, chunk in enumerate(chunks):
        processed_chunks.append({
            "content": chunk,
            "metadata": {
                "source": filename,
                "chunk_index": i,
                "length": len(chunk)
            },
            "id": f"{filename}_{i}"
        })
    return processed_chunks

@mcp.tool()
async def generate_embeddings(text_chunks: List[str]) -> List[List[float]]:
    """Generates local embeddings for a list of text chunks."""
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("all-MiniLM-L6-v2")
        embeddings = model.encode(text_chunks).tolist()
        return embeddings
    except Exception as e:
        return [f"Error generating embeddings: {str(e)}"]

@mcp.tool()
async def store_vectors(chunks: List[Dict[str, Any]]) -> str:
    """Stores chunks and their embeddings in ChromaDB."""
    try:
        vs = get_lazy_vector_store()
        texts = [c["content"] for c in chunks]
        metadatas = [c["metadata"] for c in chunks]
        ids = [c["id"] for c in chunks]
        vs.add_documents(texts, metadatas, ids)
        return f"Successfully stored {len(chunks)} chunks in vector database."
    except Exception as e:
        return f"Error storing vectors: {str(e)}"

@mcp.tool()
async def retrieve_context(query: str, n_results: int = 5) -> str:
    """Finds relevant context from the vector database for a given query."""
    try:
        vs = get_lazy_vector_store()
        results = vs.query(query, n_results=n_results)
        context_parts = []
        for i, doc in enumerate(results["documents"][0]):
            metadata = results["metadatas"][0][i]
            context_parts.append(f"Source: {metadata['source']}\nContent: {doc}")
        return "\n\n---\n\n".join(context_parts)
    except Exception as e:
        return f"Error retrieving context: {str(e)}"

@mcp.tool()
async def generate_ai_answer(prompt: str, context: str, model: str = "llama3") -> Dict[str, Any]:
    """Generates an AI answer grounded in the provided context using Ollama."""
    import ollama
    full_prompt = f"""
    You are a professional AI Knowledge Assistant. Use the following context to answer the user's question.
    If the answer is not in the context, say that you don't know based on the provided documents.
    Do not use any external knowledge.
    
    Context:
    {context}
    
    Question: {prompt}
    
    Answer:
    """
    try:
        if os.getenv("OLLAMA_HOST"):
             os.environ["OLLAMA_HOST"] = os.getenv("OLLAMA_HOST")
        
        response = ollama.generate(model=model, prompt=full_prompt)
        return {
            "answer": response["response"],
            "model": model,
            "context_used": context
        }
    except Exception as e:
        return {"error": f"Error generating answer with Ollama: {str(e)}"}

@mcp.tool()
async def summarize_document(text: str, filename: str, model: str = "llama3") -> str:
    """Generates a concise summary of the document."""
    prompt = f"Summarize the following document titled '{filename}':\n\n{text[:10000]}" # Limit text for summary
    try:
        response = ollama.generate(model=model, prompt=prompt)
        return response["response"]
    except Exception as e:
        return f"Error summarizing document: {str(e)}"

@mcp.tool()
async def extract_insights(text: str, filename: str, model: str = "llama3") -> str:
    """Extracts key insights and bullet points from the document."""
    prompt = f"Extract 5-10 key insights and important bullet points from the document '{filename}':\n\n{text[:10000]}"
    try:
        response = ollama.generate(model=model, prompt=prompt)
        return response["response"]
    except Exception as e:
        return f"Error extracting insights: {str(e)}"

@mcp.tool()
async def generate_educational_content(text: str, content_type: str, model: str = "llama3") -> str:
    """Generates FAQs, Flashcards, or Study Notes based on the content_type."""
    prompts = {
        "faq": "Generate 5 frequently asked questions and answers based on this content:\n\n",
        "flashcards": "Generate 10 flashcard pairs (Question/Answer) based on this content:\n\n",
        "notes": "Generate structured study notes and a deep-dive outline based on this content:\n\n"
    }
    prompt = prompts.get(content_type, "summarize") + text[:10000]
    try:
        response = ollama.generate(model=model, prompt=prompt)
        return response["response"]
    except Exception as e:
        return f"Error generating {content_type}: {str(e)}"

@mcp.tool()
async def compare_documents(texts: List[str], filenames: List[str], model: str = "llama3") -> str:
    """Compares two or more documents and highlights differences and similarities."""
    combined_input = ""
    for name, text in zip(filenames, texts):
        combined_input += f"Document: {name}\nContent Preview: {text[:5000]}\n\n"
    
    prompt = f"Compare the following documents and highlight key similarities, differences, and unique points in each:\n\n{combined_input}"
    try:
        response = ollama.generate(model=model, prompt=prompt)
        return response["response"]
    except Exception as e:
        return f"Error comparing documents: {str(e)}"

@mcp.tool()
async def get_citations(ai_response: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extracts source references and citations from the AI response and context."""
    context = ai_response.get("context_used", "")
    citations = []
    # Simple extraction logic: find source headers in context
    if "Source:" in context:
        parts = context.split("---")
        for part in parts:
            if "Source:" in part:
                source_line = part.strip().split("\n")[0]
                source_name = source_line.replace("Source: ", "").strip()
                content_preview = part.strip().split("\n")[1].replace("Content: ", "")[:100] + "..."
                citations.append({
                    "source": source_name,
                    "preview": content_preview
                })
    return citations

if __name__ == "__main__":
    mcp.run()
