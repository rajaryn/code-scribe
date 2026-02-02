from .llm_client import get_mathstral_latex

def enhance_latex(raw_text: str) -> str:
    """
    Refines raw voice transcription into professional LaTeX syntax 
    by calling the centralized Mathstral client.
    """
    try:
       
        latex_output = get_mathstral_latex(raw_text)
        
        
        return latex_output

    except Exception as e:
        print(f"Error in LaTeX Enhancer Agent: {e}")
        return raw_text

def format_as_block(latex_snippet: str) -> str:
    """
    Wraps the snippet in double-dollar signs for display math mode.
    """
    return f"$${latex_snippet}$$"

def format_as_inline(latex_snippet: str) -> str:
    """
    Wraps the snippet in single-dollar signs for inline math mode.
    """
    return f"${latex_snippet}$"