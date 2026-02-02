from fastapi import FastAPI, Form, Request, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import os
import io
import shutil
from datetime import datetime

# Internal imports
from app.agents.planner import think_directory_structure
from app.agents.coder import write_code_agent, write_latex_code_agent
from app.agents.latex_agent import enhance_latex, format_as_block
from app.file_operations import create_project_structure
from faster_whisper import WhisperModel

app = FastAPI()

# --- 1. CONFIGURATION & PATHS ---
# Resolving paths relative to the project root (DevScribe/)
BASE_DIR = Path(__file__).resolve().parent.parent.parent
GENERATED_PROJECTS_DIR = BASE_DIR / "generated_projects"
CSS_DIR = BASE_DIR / "css"
JS_DIR = BASE_DIR / "js"
HTML_FILE = BASE_DIR / "index.html"
CODE_WRITE_HTML = BASE_DIR / "code_write.html"

# Ensure directories exist
GENERATED_PROJECTS_DIR.mkdir(exist_ok=True)

# Initialize Faster Whisper
# Note: Initializing here ensures it's ready when the app starts
whisper_model = WhisperModel("base", device="cpu", compute_type="int8")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 2. STATIC FILES ---
# Mount these BEFORE the catch-all to prevent HTML being served for JS/CSS
app.mount("/css", StaticFiles(directory=str(CSS_DIR)), name="css")
app.mount("/js", StaticFiles(directory=str(JS_DIR)), name="js")
app.mount("/preview_static", StaticFiles(directory=str(GENERATED_PROJECTS_DIR), html=True), name="preview_static")

# --- 3. API ENDPOINTS ---

@app.get("/api/list-projects")
@app.get("/api/list-projects/")
async def list_projects():
    projects = []
    if not GENERATED_PROJECTS_DIR.exists():
        return {"projects": []}
        
    for d in GENERATED_PROJECTS_DIR.iterdir():
        if d.is_dir():
            stats = d.stat()
            is_math = d.name.startswith("math_project_")
            projects.append({
                "name": d.name,
                "is_math": is_math,
                # Use raw timestamp for sorting
                "mtime": stats.st_mtime, 
                "last_modified": datetime.fromtimestamp(stats.st_mtime).strftime('%d %b, %H:%M'),
                "display_name": d.name.replace("math_project_", "Math: ").replace("_", " ")
            })
    
    # SORT BY TIME (Newest first) - This fixes the "stale" UI feeling
    projects.sort(key=lambda x: x['mtime'], reverse=True) 
    return {"projects": projects}

@app.delete("/api/delete-project/{folder_name}")
async def delete_project(folder_name: str):
    project_path = GENERATED_PROJECTS_DIR / folder_name
    if project_path.exists() and project_path.is_dir():
        shutil.rmtree(project_path)
        return {"status": "success"}
    return JSONResponse(status_code=404, content={"error": "Project not found"})



@app.post("/create-file-structure")
async def create_file_structure_endpoint(
    message: str = Form(...), 
    timestamp: str = Form(...), 
    is_math: bool = Form(False)
):
    if is_math:
        clean_ts = timestamp.replace(':', '-').replace('.', '-').replace(' ', '_')
        folder_name = f"math_project_{clean_ts}"
        project_path = GENERATED_PROJECTS_DIR / folder_name
        project_path.mkdir(parents=True, exist_ok=True)

        raw_latex = write_latex_code_agent(message, {}, "main.tex")
        refined_latex = enhance_latex(raw_latex) # Use your new agent
        
        # Wrap in delimiters so KaTeX sees it immediately
        final_content = format_as_block(refined_latex)
        with open(project_path / "main.tex", "w", encoding="utf-8") as f:
            f.write(final_content)

        return {"status": "success", "folder_name": folder_name, "is_math": True}

    planner_response = think_directory_structure(message)
    create_project_structure(planner_response)
    folder_name = planner_response.get("project_name", "untitled_project")
    return {"status": "success", "folder_name": folder_name, "is_math": False}

@app.post("/api/whisper-latex")
async def whisper_latex_transcription(request: Request):

    # 1. Transcribe audio using Faster Whisper
    audio_data = await request.body()
    segments, _ = whisper_model.transcribe(io.BytesIO(audio_data), beam_size=5)
    raw_text = " ".join([segment.text for segment in segments])

    # 2. Use the Enhancer Agent (Local Ollama) to refine the text
    refined_latex = enhance_latex(raw_text)
    return {"status": "success", "text": refined_latex.strip()}

@app.get("/render-latex/{folder_name}/{file_path:path}", response_class=HTMLResponse)
async def render_latex_view(folder_name: str, file_path: str):
    full_path = GENERATED_PROJECTS_DIR / folder_name / file_path
    if not full_path.exists():
        return "<h3>Error: File not found.</h3>"

    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return f"<h3>Error reading file: {e}</h3>"

    # We use a raw string for the HTML to avoid backslash hell
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>DevScribe Smart Preview: {file_path}</title>
        
        <script>
            window.MathJax = {{
                tex: {{
                    inlineMath: [['$', '$'], ['\\\\(', '\\\\)']],
                    displayMath: [['$$', '$$'], ['\\\\[', '\\\\]']],
                    processEscapes: true,
                    processEnvironments: true,
                    // Smart feature: ignores LaTeX document commands instead of breaking
                    tags: 'ams' 
                }},
                options: {{
                    renderActions: {{
                        addMenu: [] // Keeps the UI clean but smart
                    }}
                }},
                svg: {{
                    fontCache: 'global'
                }}
            }};
        </script>

        <script type="text/javascript" id="MathJax-script" async
          src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js">
        </script>

        <style>
            body {{ 
                background: #f0f2f5; 
                margin: 0; 
                padding: 40px; 
                font-family: 'Georgia', serif; 
            }}
            .paper {{ 
                max-width: 850px; 
                margin: 0 auto; 
                background: white; 
                padding: 60px; 
                border: 1px solid #d1d9e6; 
                box-shadow: 0 12px 24px rgba(0,0,0,0.05); 
                min-height: 100vh;
                line-height: 1.8;
                font-size: 1.1rem;
            }}
            /* Hide the raw LaTeX document commands from the user view */
            .paper {{ visibility: hidden; }}
            .mjx-container {{ visibility: visible !important; display: block; }}
        </style>
    </head>
    <body>
        <div class="paper" id="math-paper" style="visibility: visible;">
            {content}
        </div>
    </body>
    </html>
    """



@app.get("/api/folder-structure/{folder_name}")
async def get_folder_structure(folder_name: str):
    project_path = GENERATED_PROJECTS_DIR / folder_name
    if not project_path.exists():
        return JSONResponse(status_code=404, content={"error": "Project not found"})
    
    def build_tree(path: Path, parent_path: str = ""):
        items = []
        for entry in sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
            rel = f"{parent_path}/{entry.name}" if parent_path else entry.name
            if entry.is_dir():
                items.append({"name": entry.name, "type": "folder", "path": rel, "children": build_tree(entry, rel)})
            else:
                items.append({"name": entry.name, "type": "file", "path": rel})
        return items

    return {"project_name": folder_name, "structure": build_tree(project_path)}

@app.get("/api/file-content/{folder_name}/{file_path:path}")
async def get_file_content(folder_name: str, file_path: str):
    full_path = GENERATED_PROJECTS_DIR / folder_name / file_path
    if not full_path.exists(): return JSONResponse(status_code=404, content={"error": "Not found"})
    with open(full_path, 'r', encoding='utf-8') as f:
        return {"file_path": file_path, "content": f.read()}

@app.post("/api/save-file/{folder_name}/{file_path:path}")
async def save_file_content(folder_name: str, file_path: str, request: Request):
    full_path = GENERATED_PROJECTS_DIR / folder_name / file_path
    body = await request.json()
    with open(full_path, 'w', encoding='utf-8') as f:
        f.write(body.get("content", ""))
    return {"status": "success"}

@app.post("/api/write-code")
async def write_code(request: Request):
    body = await request.json()
    agent_response = write_code_agent(body.get("message"), body.get("folder_structure"), body.get("current_file_path"))
    return {"status": "success", "response": agent_response}



# --- 4. ROUTING & CATCH-ALL---

# --- 4. ROUTING & CATCH-ALL (The Hardened Version) ---

@app.get("/")
async def serve_root():
    return FileResponse(HTML_FILE)

@app.get("/{full_path:path}")
async def catch_all(full_path: str):
    # 1. EXPLICIT GUARD: If the path starts with 'api', 'css', or 'js', 
    # do NOT serve HTML. Force a 404. 
    # This stops the "Unexpected token <" error forever.
    if full_path.startswith(("api/", "css/", "js/", "preview_static/", "render-latex/")):
        return JSONResponse(
            status_code=404, 
            content={"error": f"Path '{full_path}' not found on server."}
        )

    # 2. Check if path is a generated project directory
    # (e.g., localhost:8000/math_project_2026...)
    project_path = GENERATED_PROJECTS_DIR / full_path
    if full_path and project_path.exists() and project_path.is_dir():
        return FileResponse(CODE_WRITE_HTML)
    
    # 3. Fallback for the Home Page
    # Only return index.html if it's not a broken asset/API request
    return FileResponse(HTML_FILE)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="localhost", port=8000, reload=True)