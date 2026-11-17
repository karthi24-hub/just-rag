# Universal AI Knowledge Assistant

A production-ready, fully local AI assistant using MCP, RAG, Ollama, and Streamlit. Understand and answer questions from any document without requiring an API key.

## Features

- **Multi-format Support**: PDF, DOCX, TXT, CSV, XLSX, PPTX, MD.
- **Local RAG Pipeline**: Local embeddings and ChromaDB vector store.
- **MCP Architecture**: Modular tools for document processing and AI generation.
- **Advanced AI Tools**: Summarization, key insights, FAQ generation, flashcards, study notes, and document comparison.
- **Premium UI**: Modern ChatGPT-like interface with chat history, source citations, and dark mode.
- **Private & Local**: No data leaves your machine. Powered by Ollama.

## Prerequisites

1. **Ollama**: [Download and Install Ollama](https://ollama.com/).
2. **Models**: Pull your preferred model (e.g., `ollama pull llama3`).
3. **Python**: Version 3.10 or higher.

## Installation & Setup

1. **Clone the repository** (or navigate to the workspace).
2. **Setup with uv**:
   ```bash
   uv init
   uv add streamlit mcp ollama chromadb langchain-text-splitters pypdf python-docx pandas openpyxl python-pptx markdown sentence-transformers requests python-multipart Pillow fpdf2
   ```
3. **Run the Application**:
   ```bash
   uv run streamlit run app/app.py
   ```

## Docker Support

You can run the entire stack (excluding Ollama which should be running on the host) using Docker.

1. **Build and Run**:
   ```bash
   docker-compose up --build
   ```

## Usage

1. **Upload Documents**: Use the sidebar to drag and drop your files.
2. **Process**: Click "Process Files" to index them into the local vector DB.
3. **Chat**: Ask questions in the main chat interface.
4. **Advanced Actions**: Use the sidebar expanders for specific documents to generate summaries, FAQs, etc.
5. **Export**: Use the "Export Chat to PDF" button to save your session.
