import os
from pathlib import Path

# Define where projects should be created
BASE_DIR = Path(__file__).resolve().parent.parent.parent / "generated_projects"

def create_project_structure(project_data: dict):
    """
    Reads the Planner's JSON dictionary and creates the files on disk.
    Expected Input:
    {
        "project_type": 1,
        "project_name": "factorial_calculator",
        "project_structure": ["main.cpp", "README.md"]
    }
    """
    project_name = project_data.get("project_name", "untitled_project")
    file_list = project_data.get("project_structure", [])

    # 1. Create the project root folder
    project_path = BASE_DIR / project_name
    try:
        project_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {project_path}")
    except Exception as e:
        return {"status": "error", "message": f"Failed to create dir: {e}"}

    created_files = []
    print(file_list)

    # 2. Loop through the file list and create each file
    for file_name in file_list:
        full_path = project_path / file_name
        
        # Ensure subdirectories exist (e.g., if file is "src/main.c")
        full_path.parent.mkdir(parents=True, exist_ok=True)
         # Create the actual empty file
        try:
            full_path.touch()
            created_files.append(str(full_path))
            print(f"✓ Created file: {full_path}")
        except Exception as e:
            print(f"✗ Failed to create {file_name}: {e}")

    return {
        "status": "success",
        "path": str(project_path),
        "files_created": created_files
    }

