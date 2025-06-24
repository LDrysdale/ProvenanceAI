import requests

url = "http://localhost:8000/ask"
data = {
    "message": "hello",
    "context": ""
}

response = requests.post(url, data=data)
print(response.status_code)
print(response.json())
