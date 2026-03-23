import httpx

def fetch_api_data() -> str:
    response = httpx.get("https://api.example.com/data")
    return response.text
