import requests

url = "http://127.0.0.1:8000/chat"
query = "Find me a cardiologist in Lahore"
response = requests.post(url, json={"query": query})
print(response.json())

query = "Find me a Dermatologist in Karachi"
response = requests.post(url, json={"query": query})
print(response.json())
