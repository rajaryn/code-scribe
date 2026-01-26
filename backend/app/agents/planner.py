from llm_client import api1

def create_directory_structure(voice):
    system_prompt = """
    You are a JSON-only response engine.

    You will receive a user's spoken project description.
    You must detect project type and project name.
    Generate a directory structure based on the detected project type.
    You must respond ONLY in this JSON format:

    {
    "project_type": number,
    "project_name": "text",
    "project_structure": "array of strings"
    }

    Project type mapping:
    1 = C or C++
    2 = HTML, CSS, JavaScript
    3 = HTML, CSS, JavaScript using Bootstrap

    If nothing matches, return:
    {
    "project_type": 0,
    "project_name": "",
    "project_structure": ""
    }

    Never explain.
    Never add text.
    Return only valid JSON.
    """
    user_prompt = f"Voice: {voice}"
    response = api1(system_prompt, user_prompt)

    project_type = response.get("project_type", 0)
    project_name = response.get("project_name", "")
    project_structure = response.get("project_structure", "")

    return {
        "project_type": project_type,
        "project_name": project_name,
        "project_structure": project_structure
    }


if __name__ == "__main__":
    voice = " i want to find the fsctorisl of a number in c++"
    print(create_directory_structure(voice))