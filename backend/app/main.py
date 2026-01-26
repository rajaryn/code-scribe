from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

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


CSS_DIR = BASE_DIR / "css"
JS_DIR = BASE_DIR / "js"
HTML_FILE = BASE_DIR / "index.html"

# Validation: Create folders if they don't exist to prevent crashes
if not CSS_DIR.exists(): CSS_DIR.mkdir(exist_ok=True)
if not JS_DIR.exists(): JS_DIR.mkdir(exist_ok=True)

# 3. Static Mounts (Serve CSS and JS folders)
app.mount("/css", StaticFiles(directory=CSS_DIR), name="css")
app.mount("/js", StaticFiles(directory=JS_DIR), name="js")

# 4. Root Route (Serve index.html)
@app.get("/")
async def serve_root():
    print(f"Serving index.html from: {HTML_FILE}")
    if not HTML_FILE.exists():
        return {"error": "index.html not found in backend root"}
    return FileResponse(HTML_FILE)

# 5. Catch-All Route (Fallback for assets or SPA routing)
@app.get("/{full_path:path}")
async def catch_all(full_path: str):
    # Check if the requested file exists in the root (e.g., favicon.ico)
    potential_file = BASE_DIR / full_path
    if potential_file.exists() and potential_file.is_file():
        return FileResponse(potential_file)
    
    # Otherwise, default to index.html
    if HTML_FILE.exists():
        return FileResponse(HTML_FILE)
        
    return {"error": "File not found"}



if __name__ == "__main__":
    import uvicorn
    # Works because the script is already inside 'main.py'
    uvicorn.run("main:app", host="localhost", port=8000, reload=True)