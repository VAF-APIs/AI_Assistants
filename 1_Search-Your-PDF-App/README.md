# Search Your PDF App 📄🔍

Build a Streamlit application where you can upload a PDF and ask questions about its content. This app uses LangChain, and it supports both local models (Ollama) and cloud models (OpenAI). 

## Features
- **PDF Upload and Processing**: Automatically extract and split text from PDF documents.
- **Provider Switching**: Choose seamlessly between Ollama (default) and OpenAI for your Generative AI needs.
- **Local Privacy**: Using Ollama allows your documents to remain securely on your local machine.

## Prerequisites

- **Python**: Version 3.8 or higher.
- **Ollama**: To use the local default models, ensure you have [Ollama installed](https://ollama.com/download) and running. You will need to pull the models specified in the app:
  ```bash
  ollama pull llama3
  ollama pull nomic-embed-text
  ```
- **OpenAI API Key** (optional): Needed only if you opt to use OpenAI via the sidebar interface.

## Installation

1. **Clone the repository** (or navigate to the folder):
   ```bash
   cd 1_Search-Your-PDF-App
   ```

2. **Create a virtual environment (recommended)**:
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On Mac/Linux
   source venv/bin/activate
   ```

3. **Install the dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables**:
   Copy `.env.example` to `.env` to pre-configure your models, base URLs, or OpenAI API key. This makes configuration easier for developers to adjust without touching the code or UI:
   ```bash
   # On Windows
   copy .env.example .env
   # On Mac/Linux
   cp .env.example .env
   ```

## Running the Application

Start the Streamlit application using the following command:
```bash
streamlit run app.py
```

## How to Use
1. Once the Streamlit interface opens in your browser, look at the sidebar on the left.
2. Select your AI Provider (`Ollama` or `OpenAI`).
3. If using `OpenAI`, enter your API Key.
4. Upload a target PDF document using the file uploader.
5. Wait briefly for the text extraction and vector database generation.
6. Type a question relative to the document into the prompt text box to receive an AI-generated answer.

## Dependencies Overview
- `streamlit` - For building the interactive Web UI.
- `langchain` - A framework for interacting with LLM APIs and managing QA chains.
- `chromadb` - A vector database for storing the embeddings of different text chunks.
- `pypdf` - To safely and reliably read PDF documents.
