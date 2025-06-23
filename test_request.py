import requests

url = "http://127.0.0.1:8000/query"
data = {
    "text": "Tell me about the history of artificial intelligence and its key contributors."
}

response = requests.post(url, json=data)
print("Response:", response.json())
