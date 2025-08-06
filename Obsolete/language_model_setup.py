from google.cloud import aiplatform_v1beta1

project = "your-gcp-project-id"
location = "us-central1"  # Gemini models are often region-locked
publisher_model = "models/gemini-1.5-pro-preview-0409"  # Update as needed

# Optional: Safety settings (moderate)
safety_settings = [
    aiplatform_v1beta1.types.SafetySetting(
        category=aiplatform_v1beta1.types.SafetySetting.Category.HARM_CATEGORY_HARASSMENT,
        threshold=aiplatform_v1beta1.types.SafetySetting.Threshold.BLOCK_MEDIUM_AND_ABOVE,
    ),
    aiplatform_v1beta1.types.SafetySetting(
        category=aiplatform_v1beta1.types.SafetySetting.Category.HARM_CATEGORY_HATE_SPEECH,
        threshold=aiplatform_v1beta1.types.SafetySetting.Threshold.BLOCK_MEDIUM_AND_ABOVE,
    ),
    aiplatform_v1beta1.types.SafetySetting(
        category=aiplatform_v1beta1.types.SafetySetting.Category.HARM_CATEGORY_SEXUALLY_EXPLICIT,
        threshold=aiplatform_v1beta1.types.SafetySetting.Threshold.BLOCK_MEDIUM_AND_ABOVE,
    ),
    aiplatform_v1beta1.types.SafetySetting(
        category=aiplatform_v1beta1.types.SafetySetting.Category.HARM_CATEGORY_DANGEROUS_CONTENT,
        threshold=aiplatform_v1beta1.types.SafetySetting.Threshold.BLOCK_MEDIUM_AND_ABOVE,
    ),
]

client = aiplatform_v1beta1.PredictionServiceClient()
endpoint = client._transport._host  # Normally: "us-central1-aiplatform.googleapis.com"

instances = [{
    "prompt": "Explain quantum computing in simple terms.",
}]

parameters = {
    "temperature": 0.7,
    "maxOutputTokens": 1024,
    "topP": 0.8,
    "topK": 40,
    "safetySettings": safety_settings,
}

response = client.predict(
    endpoint=f"https://{endpoint}/v1beta1/projects/{project}/locations/{location}/publishers/google/models/gemini-1.5-pro-preview-0409:predict",
    instances=instances,
    parameters=parameters,
)

print(response)
