from app.agents.llm_client import get_llm_response
from app.file_operations import create_project_structure

def think_directory_structure(voice):
    system_prompt = """
    You are a JSON-only response engine.

    You will receive a user's spoken project description.
    You must detect project name.
    Generate a directory structure based on the detected project type.
    You must respond ONLY in this JSON format:

    {
    "project_name": "text",
    "project_structure": "array of strings"
    }


    If nothing matches, return:
    {
    "project_name": "",
    "project_structure": ""
    }

    Never explain.
    Never add text.
    Return only valid JSON.
    """
    user_prompt = f"Voice: {voice}"
    response = get_llm_response(system_prompt, user_prompt)

    project_name = response.get("project_name", "")
    project_structure = response.get("project_structure", "")

    return {
        "project_name": project_name,
        "project_structure": project_structure
    }

if __name__ == "__main__":
    voice = "i want to find the factorial of a number in c"
    result = think_directory_structure(voice)
    print("Planner output:", result)
    create_project_structure(result)