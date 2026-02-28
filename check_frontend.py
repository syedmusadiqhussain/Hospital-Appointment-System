import requests

try:
    response = requests.get('http://127.0.0.1:8000/static/index.html')
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("Frontend is accessible!")
    else:
        print("Frontend is NOT accessible.")
except Exception as e:
    print(f"Error: {e}")
