import os
import re
import json
import time
import shutil
import urllib.parse
import streamlit as st
import requests
from dotenv import load_dotenv

# Load environment variables from a .env file if it exists
load_dotenv()

# Define the main instructions provided to the Language Model exactly like the Django app.
# This dictates the strict output format required for generating fully functioning web assets.
SYSTEM_PROMPT = """
You are **ExpertWebDeveloper**, an AI specializing in creating **complete, professional web applications** based on user requirements.  

## **Your Role**  
- **End-to-End Development** – Generate fully functional web applications, ensuring all files are included.  
- **Detailed, Structured Code** – Deliver **well-structured HTML, Bootstrap CSS, and JavaScript**.  
- **Interactive & Responsive** – Implement smooth navigation, mobile responsiveness, and dynamic elements.  
- **Image Integration** - Use the provided image URLs in appropriate places throughout the application.

## **Development Guidelines**  
- **Fully Implemented Features** – No placeholders; generate all required sections.  
- **Bootstrap UI** – Use Bootstrap for grids, buttons, forms, and layouts.  
- **Component-Based Structure** – Keep JavaScript and CSS in separate files.  
- **Ensure Completeness** – If a file is incomplete, request additional content iteratively.  
- **Multi-Page Navigation** – Create multiple HTML pages based on requirements and implement proper navigation between them. All links must work between pages.
- **Image Integration** – Include image tags with URLs from Unsplash in appropriate places in the HTML files.

## **File Structure**  
- **index.html** – Homepage with main navigation and overview.
- **Additional HTML pages** – Created based on the specific application requirements.
- **styles/main.css** – Fully styled CSS (Bootstrap-based).  
- **js/app.js** – JavaScript logic for UI interactivity and image loading.  
- **js/data.js** – Sample data stored in an array format appropriate for the application.  
- **js/images.js** – Contains an array of Unsplash image URLs to be used throughout the application.

- **Important:**  
- Determine appropriate pages needed based on the user's request.
- Ensure all files are **fully generated** and **detailed**.
- Create a proper navigation bar that appears on all pages and links to each HTML file.
- Implement consistent header and footer sections across all pages.
- Ensure all links between pages use relative paths (e.g., href="about.html").
- NEVER use placeholder images like "https://via.placeholder.com/". Instead, use JavaScript to dynamically load Unsplash images.
- Continue iteration until all required files are complete.
- Only give code; don't give any additional content like preambles and explanations.
"""

# Streamlit application layout configuration
st.set_page_config(page_title="AI Website Generator", layout="wide")

# Sidebar Configuration for selecting the LLM engine and assigning corresponding keys
st.sidebar.header("Configuration")

# Standard dropdown allowing the user to select local or cloud-based LLMs
provider = st.sidebar.selectbox("Select AI Provider", ["Ollama", "OpenAI", "Gemini"])

# Dynamically render inputs required depending on the selected provider
if provider == "Ollama":
    model_name = st.sidebar.text_input("Ollama Model Name", value="llama3")
    ollama_base_url = st.sidebar.text_input("Ollama Base URL (or in .env)", value=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))
elif provider == "OpenAI":
    model_name = st.sidebar.text_input("OpenAI Model Name", value="gpt-4o")
    openai_key = st.sidebar.text_input("OpenAI API Key (or in .env)", value=os.getenv("OPENAI_API_KEY", ""), type="password")
elif provider == "Gemini":
    model_name = st.sidebar.text_input("Gemini Model Name", value="gemini-2.0-flash")
    gemini_key = st.sidebar.text_input("Gemini API Key (or in .env)", value=os.getenv("GEMINI_API_KEY", ""), type="password")

# Unsplash API key input required for generating real images during the web compilation
unsplash_key = st.sidebar.text_input("Unsplash API Key (or in .env)", value=os.getenv("UNSPLASH_API_KEY", ""), type="password")

# Initialize global Streamlit session state for tracking iterative conversation history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


def call_llm(messages, temperature=0.2):
    """
    Core abstraction function over different supported LLMs.
    Converts standard message lists into the specific format required by the chosen provider.
    """
    if provider == "Ollama":
        from ollama import Client
        client = Client(host=ollama_base_url)
        response = client.chat(model=model_name, messages=messages, options={"temperature": temperature})
        return response['message']['content']
        
    elif provider == "OpenAI":
        from openai import OpenAI
        client = OpenAI(api_key=openai_key)
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=temperature
        )
        return response.choices[0].message.content
        
    elif provider == "Gemini":
        import google.generativeai as genai
        genai.configure(api_key=gemini_key)
        
        # Reformats standard dict history into the schema expected by the Gemini SDK
        gemini_messages = []
        system_instructions = []
        for msg in messages:
            if msg['role'] == 'system':
                system_instructions.append(msg['content'])
            elif msg['role'] == 'user':
                gemini_messages.append({"role": "user", "parts": [msg['content']]})
            elif msg['role'] == 'assistant':
                gemini_messages.append({"role": "model", "parts": [msg['content']]})
                
        # Append system instructions dynamically directly into the first user prompt
        if system_instructions and gemini_messages:
            gemini_messages[0]["parts"][0] = "\n".join(system_instructions) + "\n\n" + gemini_messages[0]["parts"][0]

        model = genai.GenerativeModel(model_name)
        response = model.generate_content(gemini_messages)
        return response.text


def save_file(content: str, file_path: str, save_path: str, mode: str = "w") -> str:
    """
    Strips away any surrounding markdown blocks (```html, ```css, etc.) from the LLM 
    response, determines its location in the directory structure, and saves it locally.
    """
    try:
        # Regex execution to clean out code fences generated by LLMs natively
        content = re.sub(r"^\s*```(?:html|css|js|javascript|json)?\s*", "", content, flags=re.IGNORECASE | re.MULTILINE)
        content = re.sub(r"\s*```$", "", content, flags=re.MULTILINE)
        content = re.sub(r"^\s*'''(?:html|css|js|javascript|json)?\s*", "", content, flags=re.IGNORECASE | re.MULTILINE)
        content = re.sub(r"\s*'''$", "", content, flags=re.MULTILINE)
        
        full_path = os.path.join(save_path, file_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        with open(full_path, mode, encoding="utf-8") as file:
            file.write(content)
        return f"File saved: {file_path}"
    except Exception as e:
        return f"Error saving file: {str(e)}"


def fetch_unsplash_images(query, count=10):
    """
    Queries the Unsplash developer API to retrieve a requested number of high quality
    photos matching the prompt criteria for dynamic web embedding.
    """
    if not unsplash_key:
        return []
        
    encoded_query = urllib.parse.quote(query)
    url = f"https://api.unsplash.com/search/photos?query={encoded_query}&per_page={count}&client_id={unsplash_key}"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            images = []
            
            # Formats API endpoint result dictionaries into a simplified array
            for result in data.get("results", []):
                images.append({
                    "url": result.get("urls", {}).get("regular", ""),
                    "description": result.get("alt_description", "Image"),
                    "credit": {
                        "name": result.get("user", {}).get("name", "Unsplash User"),
                        "link": result.get("user", {}).get("links", {}).get("html", ""),
                    },
                })
            return images
    except Exception as e:
        st.error(f"Error fetching images: {str(e)}")
    return []


def determine_required_pages(user_request):
    """
    Orchestrates the very first prompt passed to the LLM. Analyzes the user's base 
    description to formulate a rigid JSON schema defining which HTML pages and image 
    queries the generator will run iteratively later.
    """
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f'''Based on this user request: "{user_request}", determine what HTML pages would be needed for a complete web application.
        Return your answer as a JSON object with the following format:
        {{
            "pages": [
                {{"name": "index.html", "description": "Homepage with..."}},
                {{"name": "page2.html", "description": "Page for..."}}
            ],
            "imageQueries": [
                "query1",
                "query2"
            ]
        }}
        Include at minimum an index.html and any other pages that would make sense for this application.
        Also include 3-5 image search queries relevant to the application that will be used to fetch images from Unsplash.
        CRITICAL: Reply ONLY with valid JSON. Do not include markdown blocks or any other text.'''
        }
    ]
    response = call_llm(messages).strip()
    
    # Strip away unneeded response context keeping only the core parsable JSON output
    if "{" in response and "}" in response:
        json_str = response[response.find("{"):response.rfind("}")+1]
        try:
            result_data = json.loads(json_str)
            return result_data.get("pages", []), result_data.get("imageQueries", ["web application"])
        except Exception:
            pass
            
    # Standard fallback configuration if parsing entirely fails
    return [
        {"name": "index.html", "description": "Homepage with main content"},
        {"name": "about.html", "description": "About page"}
    ], ["web application", "interface"]


# Main Streamlit UI components
st.title("AI Website Generator")
st.markdown("Enter a description of the website you want to build, and the AI will generate all the files and zip them for you.")

prompt = st.text_area("Website Requirements:", height=100, placeholder="e.g. Build a portfolio website for a nature photographer with a dark theme...")

# Core logic triggered when user dispatches generation
if st.button("Generate Website") and prompt:
    session_dir = "generated_website"
    
    # Clear out any previous compilation attempts ensuring a clean workspace
    if os.path.exists(session_dir):
        shutil.rmtree(session_dir)
    os.makedirs(session_dir)
    
    # Initialize the ongoing conversation history variable the LLM retains for page context
    history = [{"role": "system", "content": SYSTEM_PROMPT}]
    history.append({"role": "user", "content": f"I need you to create a multi-page web application based on this request: {prompt}."})
    
    # Live updating status container so user tracks exact operations
    with st.status("Starting Generation...", expanded=True) as status_box:
        
        # Step 1: Discover context
        st.write("Analyzing requirements to determine pages...")
        pages, image_queries = determine_required_pages(prompt)
        page_names = [p["name"] for p in pages]
        st.write(f"Pages to generate: {', '.join(page_names)}")
        
        # Step 2: Unsplash Image Integrations
        all_images = []
        if unsplash_key:
            st.write(f"Fetching images for queries: {', '.join(image_queries)}")
            for query in image_queries:
                images = fetch_unsplash_images(query, 5)
                all_images.extend(images)
            st.write(f"Fetched {len(all_images)} images.")
        else:
            st.warning("No Unsplash API Key provided. Images will not be populated correctly.")
        
        # Step 3: Hardcoded JS script writing 
        st.write("Generating JavaScript foundations...")
        
        # Images.js: Preloads image queries globally to assign upon native html load requests 
        images_js_content = f"""// Images fetched from Unsplash\nconst unsplashImages = {json.dumps(all_images, indent=2)};\n
function getRandomImage() {{ return unsplashImages[Math.floor(Math.random() * unsplashImages.length)]; }}
function getImageByIndex(index) {{ return unsplashImages[index % unsplashImages.length]; }}
document.addEventListener('DOMContentLoaded', function() {{
  const imgElements = document.querySelectorAll('[data-unsplash-img]');
  imgElements.forEach((element, index) => {{
    if(unsplashImages.length === 0) return;
    const img = getImageByIndex(index);
    element.src = img.url; element.alt = img.description;
    const attrElement = document.getElementById(element.id + '-attr');
    if (attrElement) attrElement.innerHTML = `Photo by <a href="${{img.credit.link}}" target="_blank">${{img.credit.name}}</a> on Unsplash`;
  }});
}});\n"""
        save_file(images_js_content, "js/images.js", session_dir)
        
        # App.js: Initializes standard active link navigations
        app_js_content = """function initApp() {\n  const currentPage = window.location.pathname.split('/').pop() || 'index.html';\n  document.querySelectorAll('.navbar-nav .nav-link').forEach(link => {\n    if (link.getAttribute('href') === currentPage) link.classList.add('active');\n  });\n}\ndocument.addEventListener('DOMContentLoaded', initApp);\n"""
        save_file(app_js_content, "js/app.js", session_dir)
        
        # Step 4: Iterative LLM prompts generating unique context-aware logic per page requirement
        page_list_str = ", ".join(page_names)
        files_to_generate = {}
        for page in pages:
            files_to_generate[page["name"]] = f"""Generate a complete {page["name"]} file for {page["description"]}. 
            Include a navigation bar with links to all pages: {page_list_str}.
            IMPORTANT: Use <img id="img-{page['name']}" data-unsplash-img src="" class="img-fluid" alt=""> and script tags for js/images.js and js/app.js at the end of body. DO NOT use placeholder URLs."""
            
        files_to_generate["styles/main.css"] = f"Generate a fully styled CSS file using Bootstrap for all pages: {page_list_str}."
        files_to_generate["js/data.js"] = f"Generate sample JSON data inside a variable for the application: {prompt}."
        
        # Loops locally tracking responses and flushing code block output to directories
        for file_name, instruction in files_to_generate.items():
            st.write(f"Generating {file_name}...")
            history.append({"role": "user", "content": instruction})
            
            response_text = call_llm(history)
            
            history.append({"role": "assistant", "content": response_text})
            save_result = save_file(response_text, file_name, session_dir)
            st.write(save_result)
        
        status_box.update(label="Website Generation Complete!", state="complete", expanded=False)
        
    st.success("All files generated successfully!")
    
    # Step 5: Wrap artifacts in zip and prepare a native Streamlit download trigger
    zip_path = "website_archive"
    shutil.make_archive(zip_path, 'zip', session_dir)
    
    with open(f"{zip_path}.zip", "rb") as fp:
        btn = st.download_button(
            label="Download Generated Website",
            data=fp,
            file_name="website.zip",
            mime="application/zip"
        )
