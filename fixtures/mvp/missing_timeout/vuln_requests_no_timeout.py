import requests

def fetch_api_data() -> str:
    response = requests.get("https://api.example.com/data")
    return response.text
