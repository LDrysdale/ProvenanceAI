import os
from google.cloud import aiplatform
from google.oauth2 import service_account

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-pro-preview-0409")
SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "credentials/gcp-key.json")

credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE)

def gemini_generate(prompt: str) -> str:
    client = aiplatform.gapic.PredictionServiceClient(credentials=credentials)
    endpoint = f"projects/{PROJECT_ID}/locations/{LOCATION}/publishers/google/models/{GEMINI_MODEL}"
    
    instance = {"prompt": prompt}
    
    # Apply medium safety settings
    safety_settings = [
        {"category": "HARM_CATEGORY_DEROGATORY", "threshold": 3},
        {"category": "HARM_CATEGORY_TOXICITY", "threshold": 3},
        {"category": "HARM_CATEGORY_VIOLENCE", "threshold": 3},
        {"category": "HARM_CATEGORY_SEXUAL", "threshold": 3},
        {"category": "HARM_CATEGORY_MEDICAL", "threshold": 3},
        {"category": "HARM_CATEGORY_DANGEROUS", "threshold": 3},
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": 3},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": 3},
    ]
    
    parameters = {
        "temperature": 0.7,
        "maxOutputTokens": 2048,
        "topP": 0.95,
        "topK": 40,
        "safetySettings": safety_settings,
    }

    response = client.predict(
        endpoint=endpoint,
        instances=[instance],
        parameters=parameters,
    )

    return response.predictions[0]["content"]