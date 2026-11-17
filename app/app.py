import streamlit as st
import os
import tempfile
import asyncio
import json
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.session import ClientSession

# --- Page Config ---
st.set_page_config(
    page_title="Universal AI Knowledge Assistant",
    page_icon="🧠",
    layout="wide",
)

# --- Custom CSS ---
st.markdown("""
    <style>
    .main {
        background: #0e1117;
        color: #ffffff;
    }
    .stChatFloatingInputContainer {
        bottom: 20px;
    }
    .stChatMessage {
        background-color: #1e2227;
        border-radius: 15px;
        padding: 10px;
        margin-bottom: 10px;
        border: 1px solid #3e4451;
    }
    .source-panel {
        background-color: #161b22;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #30363d;
        font-size: 0.9rem;
    }
    .source-title {
        color: #58a6ff;
        font-weight: bold;
    }
    .stButton>button {
        border-radius: 20px;
        padding: 5px 20px;
        background-color: #238636;
        color: white;
        border: none;
    }
    </style>
""", unsafe_allow_html=True)

import sys
from pathlib import Path

# --- Page Config ---
# ... (existing imports)

# --- MCP Client Logic ---
async def call_mcp_tool(tool_name: str, arguments: dict):
    # This runs the MCP server locally using the current python interpreter
    # This ensures it has access to the same virtualenv dependencies
    import sys
    from pathlib import Path
    from mcp.client.stdio import stdio_client, StdioServerParameters
    from mcp.client.session import ClientSession

    server_script = Path(__file__).parent.parent / "server" / "mcp_server.py"
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[str(server_script.absolute())],
    )
    
    # Stateless: New process/session per call for maximum stability on Windows/Streamlit
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, arguments)
            return result.content[0].text

# Wrapper for streamlit
def run_mcp_tool_sync(tool_name: str, arguments: dict):
    import asyncio
    return asyncio.run(call_mcp_tool(tool_name, arguments))

# --- Sidebar ---
with st.sidebar:
    st.title("🧠 AI Knowledge Assistant")
    st.markdown("---")
    
    uploaded_files = st.file_uploader(
        "Upload Documents", 
        type=["pdf", "docx", "txt", "csv", "xlsx", "pptx", "md"], 
        accept_multiple_files=True
    )
    
    if st.button("Process Files") and uploaded_files:
        with st.spinner("Processing documents..."):
            for uploaded_file in uploaded_files:
                # Save to temp file
                with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{uploaded_file.name}") as tmp:
                    tmp.write(uploaded_file.getbuffer())
                    tmp_path = tmp.name
                
                # Flow: Read -> Process -> Store
                text = run_mcp_tool_sync("read_file", {"file_path": tmp_path})
                if not text.startswith("Error"):
                    # Store text for advanced actions
                    st.session_state.processed_docs.append(uploaded_file.name)
                    st.session_state.doc_text_store[uploaded_file.name] = text
                    
                    chunks_json = run_mcp_tool_sync("process_document", {"text": text, "filename": uploaded_file.name})
                    chunks = json.loads(chunks_json)
                    status = run_mcp_tool_sync("store_vectors", {"chunks": chunks})
                    st.success(f"Loaded: {uploaded_file.name}")
                else:
                    st.error(f"Error loading {uploaded_file.name}: {text}")
                
                os.remove(tmp_path)
            st.balloons()

    st.markdown("---")
    model_choice = st.selectbox("Select local AI model", ["llama3", "mistral", "gemma"])
    st.info("Ensure Ollama is running.")
    
    st.markdown("---")
    st.subheader("Advanced Actions")
    if "processed_docs" not in st.session_state:
        st.session_state.processed_docs = []

    for doc_name in st.session_state.processed_docs:
        with st.expander(f"Actions: {doc_name}"):
            action = st.radio(f"Select action for {doc_name}", ["Summarize", "Insights", "FAQ", "Flashcards", "Notes"], key=f"action_{doc_name}")
            if st.button(f"Run {action}", key=f"run_{doc_name}"):
                with st.spinner(f"Running {action}..."):
                    # First get text from file (we need to store it or re-read)
                    # For simplicity, we'll assume the text is small enough to store in state or we re-read from a known path
                    # Let's add a simple text store in session_state when processing
                    doc_text = st.session_state.doc_text_store.get(doc_name, "")
                    if action == "Summarize":
                        res = run_mcp_tool_sync("summarize_document", {"text": doc_text, "filename": doc_name, "model": model_choice})
                    elif action == "Insights":
                        res = run_mcp_tool_sync("extract_insights", {"text": doc_text, "filename": doc_name, "model": model_choice})
                    else:
                        type_map = {"FAQ": "faq", "Flashcards": "flashcards", "Notes": "notes"}
                        res = run_mcp_tool_sync("generate_educational_content", {"text": doc_text, "content_type": type_map[action], "model": model_choice})
                    
                    st.session_state.messages.append({"role": "assistant", "content": f"### {action} for {doc_name}\n\n{res}"})
                    # Re-run to show message
                    st.rerun()

    if st.button("Compare All Documents") and len(st.session_state.processed_docs) > 1:
        with st.spinner("Comparing documents..."):
            texts = [st.session_state.doc_text_store[name] for name in st.session_state.processed_docs]
            res = run_mcp_tool_sync("compare_documents", {"texts": texts, "filenames": st.session_state.processed_docs, "model": model_choice})
            st.session_state.messages.append({"role": "assistant", "content": f"### Document Comparison\n\n{res}"})
            st.rerun()

    st.markdown("---")
    if st.button("Export Chat to PDF") and st.session_state.messages:
        from fpdf import FPDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="Universal AI Knowledge Assistant - Chat Export", ln=True, align='C')
        pdf.ln(10)
        for msg in st.session_state.messages:
            role = "User" if msg["role"] == "user" else "Assistant"
            pdf.set_font("Arial", 'B', size=10)
            pdf.multi_cell(0, 10, txt=f"{role}:")
            pdf.set_font("Arial", size=10)
            pdf.multi_cell(0, 10, txt=msg["content"])
            pdf.ln(5)
        
        pdf_output = pdf.output(dest='S').encode('latin-1', 'replace')
        st.download_button(label="Download PDF", data=pdf_output, file_name="chat_export.pdf", mime="application/pdf")

# --- Main Interface ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "doc_text_store" not in st.session_state:
    st.session_state.doc_text_store = {}
if "processed_docs" not in st.session_state:
    st.session_state.processed_docs = []

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("citations"):
            with st.expander("Show Sources"):
                for cite in message["citations"]:
                    st.markdown(f"**{cite['source']}**")
                    st.caption(cite["preview"])

# Chat Input
if prompt := st.chat_input("Ask about your documents..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            # 1. Retrieve Context
            context = run_mcp_tool_sync("retrieve_context", {"query": prompt, "n_results": 5})
            
            # 2. Generate Answer
            answer_json = run_mcp_tool_sync("generate_ai_answer", {
                "prompt": prompt, 
                "context": context, 
                "model": model_choice
            })
            answer_data = json.loads(answer_json)
            
            if "error" in answer_data:
                st.error(answer_data.get("error", "Unknown error"))
                full_response = "I encountered an error while generating the answer."
                citations = []
            else:
                full_response = answer_data["answer"]
                # 3. Get Citations
                citations_json = run_mcp_tool_sync("get_citations", {"ai_response": answer_data})
                citations = json.loads(citations_json)

            st.markdown(full_response)
            if citations:
                with st.expander("Show Sources"):
                    for cite in citations:
                        st.markdown(f"**{cite['source']}**")
                        st.caption(cite['preview'])
            
            st.session_state.messages.append({
                "role": "assistant", 
                "content": full_response, 
                "citations": citations
            })

# Update processing block to populate state
if uploaded_files:
    # This was a button in previous version, let's make sure it populates state
    pass # Managed in the button block in actual file
