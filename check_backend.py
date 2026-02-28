import requests

try:
    response = requests.get("http://localhost:4444/")
    print(f"Backend Status: {response.status_code}")
except Exception as e:
    print(f"Backend Error: {e}")
