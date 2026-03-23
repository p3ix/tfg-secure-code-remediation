import requests

def fetch_data() -> str:
    response = requests.get("https://example.com", verify=False)
    return response.text
