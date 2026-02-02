import requests
import json
import re

OLLAMA_URL = "http://localhost:11434/api/chat"
CODING_MODEL = "qwen2.5-coder:7b"
LATEX_MODEL = "mathstral" # Ensure you have run: ollama pull mathstral

def clean_llm_json(text: str):
    text = text.strip()
    # Remove ```json or ``` wrappers
    text = re.sub(r"^```[a-zA-Z]*\n", "", text)
    text = re.sub(r"\n```$", "", text)
    return text.strip()

# --- EXISTING FUNCTION (for Structured JSON) ---
def get_llm_response(system_prompt, user_prompt):
    payload = {
        "model": CODING_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "stream": False,
        "temperature": 0.2,
        "format": "json" # Forces Ollama to return valid JSON
    }

    response = requests.post(OLLAMA_URL, json=payload)
    result = response.json()
    content = result["message"]["content"]
    cleaned = clean_llm_json(content)

    try:
        return json.loads(cleaned)
    except Exception as e:
        print("JSON parse failed. Cleaned text:\n", cleaned)
        raise ValueError("LLM did not return valid JSON") from e


def get_mathstral_latex(spoken_text: str):
    """
    Specifically for the LaTeX Enhancer. 
    It takes raw speech text and returns only the LaTeX code.
    """
    system_prompt = (
        "You are a LaTeX expert. Convert the spoken math into professional LaTeX code. "
        "Return ONLY the LaTeX snippet. No conversational text, no explanations."
    )
    
    payload = {
        "model": LATEX_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Convert to LaTeX: {spoken_text}"}
        ],
        "stream": False,
        "temperature": 0.1 # Low temperature for high precision math
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload)
        result = response.json()
        
        # Extract the content directly
        latex_snippet = result["message"]["content"].strip()
        
        # Remove any markdown code blocks (e.g., ```latex ... ```)
        latex_snippet = re.sub(r"```[a-zA-Z]*\n?", "", latex_snippet)
        latex_snippet = latex_snippet.replace("```", "").strip()
        
        return latex_snippet
    except Exception as e:
        print(f"Mathstral API Call failed: {e}")
        return spoken_text 