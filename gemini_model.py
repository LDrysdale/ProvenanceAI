import os
import traceback
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-pro")
CREDENTIALS_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

if not CREDENTIALS_PATH or not os.path.exists(CREDENTIALS_PATH):
    raise ValueError("Missing or invalid GOOGLE_APPLICATION_CREDENTIALS path in environment variables.")

# The SDK will automatically use the credentials JSON from the environment variable
# No need to call genai.configure(api_key=...)

def gemini_generate(prompt: str, max_output_tokens: int = 2048, temperature: float = 0.7) -> str:
    """
    Sends a prompt to Gemini and returns the generated text.
    Uses the google.generativeai SDK with a service account JSON.
    """
    try:
        print("\n[DEBUG] Initializing Gemini client...")
        print(f"[DEBUG] Model: {GEMINI_MODEL}")
        print(f"[DEBUG] Prompt length: {len(prompt)} characters")
        print(f"[DEBUG] Parameters: max_output_tokens={max_output_tokens}, temperature={temperature}")

        # Medium safety settings
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"}
        ]

        model = genai.GenerativeModel(GEMINI_MODEL)

        print("[DEBUG] Sending request to Gemini API...")
        response = model.generate_content(
            prompt,
            generation_config={
                "max_output_tokens": max_output_tokens,
                "temperature": temperature,
                "top_p": 0.95,
                "top_k": 40
            },
            safety_settings=safety_settings
        )

        if hasattr(response, "text") and response.text:
            output = response.text.strip()
        else:
            output = str(response)

        print("[DEBUG] Gemini API call succeeded.")
        return output

    except Exception as e:
        print("\n[ERROR] Gemini API call failed:", e)
        traceback.print_exc()
        return "Error: Gemini model generation failed"
