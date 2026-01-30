import requests
import json
import re

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen2.5-coder:7b"

def clean_llm_json(text: str):
    text = text.strip()
    # Remove ```json or ``` wrappers
    text = re.sub(r"^```[a-zA-Z]*\n", "", text)
    text = re.sub(r"\n```$", "", text)
    return text.strip()

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

    print("AI raw response:", result)

    content = result["message"]["content"]

    cleaned = clean_llm_json(content)

    try:
        return json.loads(cleaned)
    except Exception as e:
        print("JSON parse failed. Cleaned text:\n", cleaned)
        raise ValueError("LLM did not return valid JSON") from e
