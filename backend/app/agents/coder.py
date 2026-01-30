import json
from .llm_client import get_llm_response

def write_code_agent(user_prompt: str, folder_structure: dict, current_file_path: str):
    system_prompt = """
You are an expert AI programmer.

You must generate or modify MULTIPLE files.

Your output MUST be a valid JSON array:

[
  {
    "file_name": "relative/path/file.py",
    "content": "FULL RAW CODE HERE"
  }
]

Rules:
- No explanations
- No markdown
- Output ONLY valid JSON
"""

    structure_str = json.dumps(folder_structure, indent=2)

    full_user_prompt = f"""
User request:
{user_prompt}

Project structure:
{structure_str}

Return all required files in JSON format.
"""

    response_data = get_llm_response(system_prompt, full_user_prompt)
    print('response in write a_code_agent:', response_data)
    # response_data is already a list
    if isinstance(response_data, list):
        return response_data
    
    print(response_data)
    # fallback if string
    return json.loads(response_data)
