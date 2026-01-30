from fastapi import FastAPI, Form, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from app.agents.planner import think_directory_structure
from app.agents.coder import write_code_agent
from app.file_operations import create_project_structure
import os

app = FastAPI()

# 1. CORS Setup (Good practice to keep)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
 
# 2. Define Paths
# Points to the root folder 'devscribe-backend'
BASE_DIR = Path(__file__).resolve().parent.parent.parent
GENERATED_PROJECTS_DIR = BASE_DIR / "generated_projects"

CSS_DIR = BASE_DIR / "css"
JS_DIR = BASE_DIR / "js"
HTML_FILE = BASE_DIR / "index.html"
CODE_WRITE_HTML = BASE_DIR / "code_write.html"

# Validation: Create folders if they don't exist to prevent crashes
if not CSS_DIR.exists(): CSS_DIR.mkdir(exist_ok=True)
if not JS_DIR.exists(): JS_DIR.mkdir(exist_ok=True)
if not GENERATED_PROJECTS_DIR.exists(): GENERATED_PROJECTS_DIR.mkdir(exist_ok=True)

# 3. Static Mounts (Serve CSS and JS folders)
app.mount("/css", StaticFiles(directory=CSS_DIR), name="css")
app.mount("/js", StaticFiles(directory=JS_DIR), name="js")
# Serve generated projects as static websites
app.mount(
    "/preview",
    StaticFiles(directory=GENERATED_PROJECTS_DIR, html=True),
    name="preview",
)

# 4. Root Route (Serve index.html)
@app.get("/")
async def serve_root():
    print(f"Serving index.html from: {HTML_FILE}")
    if not HTML_FILE.exists():
        return {"error": "index.html not found in backend root"}
    return FileResponse(HTML_FILE)

# 5. API endpoint to get folder structure
@app.get("/api/folder-structure/{folder_name}")
async def get_folder_structure(folder_name: str):
    """
    Returns the folder structure for a given project
    """
    project_path = GENERATED_PROJECTS_DIR / folder_name
    
    if not project_path.exists():
        return JSONResponse(
            status_code=404,
            content={"error": f"Project '{folder_name}' not found"}
        )
    
    def build_tree(path: Path, parent_path: str = ""):
        """Recursively build folder tree structure"""
        items = []
        
        try:
            # Get all items in directory, sorted (folders first, then files)
            entries = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
            
            for entry in entries:
                relative_path = f"{parent_path}/{entry.name}" if parent_path else entry.name
                
                if entry.is_dir():
                    items.append({
                        "name": entry.name,
                        "type": "folder",
                        "path": relative_path,
                        "children": build_tree(entry, relative_path)
                    })
                else:
                    items.append({
                        "name": entry.name,
                        "type": "file",
                        "path": relative_path
                    })
        except PermissionError:
            pass
        
        return items
    
    structure = build_tree(project_path)
    
    return {
        "project_name": folder_name,
        "structure": structure
    }

# 6. API endpoint to get file content
@app.get("/api/file-content/{folder_name}/{file_path:path}")
async def get_file_content(folder_name: str, file_path: str):
    """
    Returns the content of a specific file
    """
    full_path = GENERATED_PROJECTS_DIR / folder_name / file_path
    
    if not full_path.exists() or not full_path.is_file():
        return JSONResponse(
            status_code=404,
            content={"error": "File not found"}
        )
    
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return {
            "file_path": file_path,
            "content": content
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to read file: {str(e)}"}
        )

# 7. Catch-All Route (Modified to serve code_write.html for project routes)
@app.get("/{full_path:path}")
async def catch_all(full_path: str):
    # Check if it's a project route (e.g., /project_name)
    if "/" not in full_path:  # Single path segment
        project_path = GENERATED_PROJECTS_DIR / full_path
        if project_path.exists() and project_path.is_dir():
            # Serve code_write.html for project routes
            if CODE_WRITE_HTML.exists():
                return FileResponse(CODE_WRITE_HTML)
    
    # Check if the requested file exists in the root (e.g., favicon.ico)
    potential_file = BASE_DIR / full_path
    if potential_file.exists() and potential_file.is_file():
        return FileResponse(potential_file)
    
    # Otherwise, default to index.html
    if HTML_FILE.exists():
        return FileResponse(HTML_FILE)
        
    return {"error": "File not found"}

@app.post("/api/save-file/{folder_name}/{file_path:path}")
async def save_file_content(folder_name: str, file_path: str, request: Request):
    """Saves content to a specific file"""
    full_path = GENERATED_PROJECTS_DIR / folder_name / file_path
    
    if not full_path.exists() or not full_path.is_file():
        return JSONResponse(
            status_code=404,
            content={"error": "File not found"}
        )
    
    try:
        # Get JSON body
        body = await request.json()
        content = body.get("content", "")
        
        # Write content to file
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return {
            "status": "success",
            "message": "File saved successfully",
            "file_path": file_path
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to save file: {str(e)}"}
        )



@app.post("/api/write-code")
async def write_code(request: Request):
    """
    Receives a user's request, the current file context, and folder structure,
    then uses an agent to generate code.
    """
    try:
        body = await request.json()
        message = body.get("message", "")
        current_file_path = body.get("current_file_path", "")
        folder_structure = body.get("folder_structure", {})

        # print("=" * 50)
        # print("Received data for /api/write-code:")
        # print(f"  - Message: {message}")
        # print(f"  - Current File: {current_file_path}")
        # # print(f"  - Folder Structure: {folder_structure}") # Can be very long
        # print("=" * 50)

        # Pass the context to the coding agent
        agent_response = write_code_agent(message, folder_structure, current_file_path)

        # print(agent_response)
  
        # For now, just return the agent's response
        return {
            "status": "success",
            "response": agent_response
        }
    except Exception as e:
        print(f"Error in /api/write-code: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to process code generation request"}
        )

@app.post("/create-file-structure")
async def create_file_structure_endpoint(message: str = Form(...), timestamp: str = Form(...)):
    print("=" * 50)
    print("POST Variables Received:")
    print("=" * 50)
    print(f"message: {message}")
    print(f"timestamp: {timestamp}")
    print("=" * 50)
    
    # Step 1: Get directory structure from planner
    planner_response = think_directory_structure(message)
    print("\n" + "=" * 50)
    print("Planner Response:")
    print("=" * 50)
    print(planner_response)
    print("=" * 50 + "\n")
    
    # Step 2: Create the project structure
    creation_result = create_project_structure(planner_response)
    print("\n" + "=" * 50)
    print("File Creation Result:")
    print("=" * 50)
    print(creation_result)
    print("=" * 50 + "\n")
    
    # Extract folder name from planner response
    folder_name = planner_response.get("project_name", "untitled_project")
    
    return {
        "status": creation_result.get("status", "error"),
        "folder_name": folder_name,
        "message": f"Project '{folder_name}' created successfully" if creation_result.get("status") == "success" else "Failed to create project",
        "details": {
            "project_path": creation_result.get("path", ""),
            "files_created": creation_result.get("files_created", [])
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="localhost", port=8000, reload=True)