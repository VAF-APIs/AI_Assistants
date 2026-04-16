import streamlit as st
import os
import tempfile
from dotenv import load_dotenv

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_classic.chains import RetrievalQA

from langchain_community.llms import Ollama
from langchain_community.embeddings import OllamaEmbeddings
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings

# Load environment variables
load_dotenv()

st.set_page_config(page_title="Search Your PDF", page_icon="📄")
st.title("Search Your PDF App 📄🔍")
st.write("Upload a PDF and ask questions about it using Generative AI.")

# ==========================================
# Sidebar Configuration
# ==========================================
st.sidebar.title("Configuration")
provider = st.sidebar.radio("Select AI Provider:", ("Ollama", "OpenAI"))

if provider == "Ollama":
    st.sidebar.markdown("### Ollama Settings")
    default_base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
    default_model = os.environ.get("OLLAMA_MODEL_NAME", "llama3")
    default_embed = os.environ.get("OLLAMA_EMBED_MODEL_NAME", "nomic-embed-text")
    
    ollama_base_url = st.sidebar.text_input("Ollama Base URL", value=default_base_url)
    ollama_model = st.sidebar.text_input("LLM Model Name", value=default_model)
    ollama_embed_model = st.sidebar.text_input("Embeddings Model Name", value=default_embed)
    st.sidebar.info("Ensure Ollama is running locally with these models pulled.")
else:
    st.sidebar.markdown("### OpenAI Settings")
    # Load default from environment if available
    default_key = os.environ.get("OPENAI_API_KEY", "")
    openai_api_key = st.sidebar.text_input("OpenAI API Key", type="password", value=default_key)
    if not openai_api_key:
        st.sidebar.warning("Please provide an OpenAI API key to use OpenAI.")

# ==========================================
# Application Main Logic
# ==========================================
uploaded_file = st.file_uploader("Upload a PDF file", type="pdf")

if uploaded_file is not None:
    # Save the uploaded file to a temporary file
    # PyPDFLoader requires a file path to process the document
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_file_path = tmp_file.name

    try:
        st.info("Reading and processing the PDF...")
        
        # 1. Load the PDF
        loader = PyPDFLoader(tmp_file_path)
        documents = loader.load()

        # 2. Split the text into chunks
        # This prevents the LLM context window from being overloaded
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = text_splitter.split_documents(documents)
        st.success(f"PDF processed into {len(chunks)} chunks.")

        # 3. Initialize Embeddings and LLM based on chosen provider
        if provider == "Ollama":
            embeddings = OllamaEmbeddings(model=ollama_embed_model, base_url=ollama_base_url)
            llm = Ollama(model=ollama_model, base_url=ollama_base_url)
        else:
            if not openai_api_key:
                st.error("OpenAI API Key is required to proceed.")
                st.stop()
            os.environ["OPENAI_API_KEY"] = openai_api_key
            openai_model_name = os.environ.get("OPENAI_MODEL_NAME", "gpt-3.5-turbo")
            embeddings = OpenAIEmbeddings()
            llm = ChatOpenAI(model=openai_model_name, temperature=0)

        # 4. Create vector store
        st.info("Building the vector database (this might take a moment)...")
        # Chroma running without a persistent directory stores data in memory for this session
        vectorstore = Chroma.from_documents(chunks, embeddings)
        
        # 5. Question Answering System
        st.subheader("Ask a Question")
        user_question = st.text_input("What would you like to know about the uploaded document?")
        
        if user_question:
            # Create a retrieval chain using our language model and the vector store retriever
            qa_chain = RetrievalQA.from_chain_type(
                llm=llm,
                chain_type="stuff",
                retriever=vectorstore.as_retriever()
            )
            
            with st.spinner("Generating answer..."):
                # Invoke the chain to find the most relevant context and generate the answer
                response = qa_chain.invoke({"query": user_question})
                st.write("### Answer:")
                st.write(response["result"])
                
    except Exception as e:
        st.error(f"An error occurred: {e}")
    finally:
        # Guarantee cleanup of the temporary file to manage storage
        if os.path.exists(tmp_file_path):
            os.remove(tmp_file_path)
else:
    st.info("Please upload a PDF file to get started.")
