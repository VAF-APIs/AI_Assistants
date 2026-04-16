# AI Website Generator

This is a Streamlit-based web application that generates entire multi-page websites dynamically using locally run LLMs (Ollama) by default. It also supports cloud models like OpenAI and Google Gemini.

The app takes a single prompt (e.g., "Create a portfolio website for a freelance photographer") and iteratively generates all the necessary HTML, CSS (Bootstrap), and JavaScript files required to make the site fully functional and responsive. It also fetches dynamic images from Unsplash.

## Features

- **Multi-Model Support:** Uses Ollama (local) out of the box, with options for OpenAI and Gemini.
- **Dynamic File Generation:** Generates multi-page websites (e.g., `index.html`, `about.html`, `services.html`).
- **Real Images:** Integrates with the Unsplash API to pull contextually relevant placeholder images.
- **ZIP Download:** Packages the resulting generated files into an easy-to-download ZIP file.

## Step-by-Step Installation

### Prerequisites
1. **Python 3.9+**: Ensure you have Python installed on your system.
2. *(Optional)* **Ollama**: If you want to run this entirely locally (the default behavior), download and install [Ollama](https://ollama.com/).
3. *(Optional)* **Unsplash API Key**: Required for fetching real images. Get a free developer key at [Unsplash Developers](https://unsplash.com/developers).

### Step 1: Clone the Repository
Clone this directory and navigate into the `NEW` project folder (or wherever this project is hosted):
```bash
git clone <repository_url>
cd <repository_folder_name>
```

### Step 2: Set Up a Virtual Environment (Recommended)
It is highly recommended to isolate your dependencies using a Python virtual environment.
```bash
python -m venv venv

# On Mac/Linux:
source venv/bin/activate

# On Windows:
.\venv\Scripts\activate
```

### Step 3: Install Dependencies
Install all required Python libraries via `pip`.
```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables
Create a `.env` file in the root of the directory. You can copy the template provided:
```bash
# On Mac/Linux/Windows
cp .env.example .env
```
Open `.env` in your text editor and fill in your API keys:
- `UNSPLASH_API_KEY`: Highly recommended so the site fetches appropriate images.
- `OPENAI_API_KEY`: Only needed if you plan to use OpenAI models.
- `GEMINI_API_KEY`: Only needed if you plan to use Google Gemini models.

*Alternatively, the Streamlit UI provides a sidebar where you can paste these keys temporarily while the app is running!*

### Step 5: Start Ollama Server (If using Ollama)
If you are using the default local generation, make sure your Ollama instance is running in the background. It is also recommended to pull a good local model. For example:
```bash
ollama run llama3
```

### Step 6: Run the Application
Start the Streamlit development server using the following command:
```bash
streamlit run app.py
```

The application will launch in your default web browser at `http://localhost:8501`.

## How to Use

1. Open the app in your browser.
2. Open the left sidebar and select your preferred **AI Provider** and configure the Model Name (e.g., `llama3`, `gpt-4o`, `gemini-2.0-flash`).
3. Enter a descriptive prompt in the main chat input field outlining what type of website you want.
4. Watch the progress as the LLM decides the necessary pages, writes the HTML, styles with CSS, and integrates Unsplash images.
5. Once complete, click the **Download Generated Website** button to securely download the code!
