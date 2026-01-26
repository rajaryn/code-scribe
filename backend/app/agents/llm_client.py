import requests
import json

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen2.5-coder:7b"


def get_llm_response(system_prompt, user_prompt):
   

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "stream": False,
        "temperature": 0.2
    }

    response = requests.post(OLLAMA_URL, json=payload)
    result = response.json()

    try:
        content = result["message"]["content"]
        return json.loads(content)
    except:
        print("AI returned invalid JSON:", result)
        return {"project_type": 0, "project_name": ""}


