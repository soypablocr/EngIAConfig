import requests
import json

url = "http://127.0.0.1:5005/api/chat"
headers = {"Content-Type": "application/json"}

# Test 1: General Greeting
data1 = {
    "message": "Hello there",
    "context": {}
}

try:
    print("Testing Greeting...")
    response1 = requests.post(url, json=data1, headers=headers)
    print(f"Status Code: {response1.status_code}")
    print(f"Response: {response1.json()}")
except Exception as e:
    print(f"Error: {e}")

print("-" * 20)

# Test 2: Complex Question (Requires LLM)
data2 = {
    "message": "Explain the difference between SD-WAN and MPLS in one sentence.",
    "context": {"vendor": "Fortinet"}
}

try:
    print("Testing LLM Question...")
    response2 = requests.post(url, json=data2, headers=headers)
    print(f"Status Code: {response2.status_code}")
    print(f"Response: {response2.json()}")
except Exception as e:
    print(f"Error: {e}")
