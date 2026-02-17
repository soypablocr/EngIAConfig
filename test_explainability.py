import requests
import json
import os

API_URL = "http://localhost:5005/api/magic-fill"
# Use a key that works or fallback
API_KEY = os.environ.get("ENGIA_API_KEY", "test-key")

# We need to authenticate first to get a session, or use API Key if the endpoint allows it.
# The endpoint is @login_required AND @require_api_key.
# So we need a session cookie AND an API key.

BASE_URL = "http://localhost:5005"
LOGIN_URL = f"{BASE_URL}/login"
USERNAME = "admin"
PASSWORD = "admin"

def test_explainability():
    print("Testing AI Explainability...")
    session = requests.Session()

    # 1. Login
    try:
        print("Logging in...")
        resp = session.post(LOGIN_URL, data={"username": USERNAME, "password": PASSWORD}, allow_redirects=True)
        if resp.status_code != 200:
            print(f"Login returned unexpected status: {resp.status_code}")
        
        # Verify login by checking if we are at index
        if "ENGIA CONFIG" not in resp.text:
             # Try following redirect if not followed
             if resp.history:
                 print("Login followed redirect.")
             else:
                 print("Login might have failed.")
    except Exception as e:
        print(f"Login failed: {e}")
        return

    # 2. Call Magic Fill
    prompt = "Create a robust firewall config for a financial institution."
    
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY
    }
    
    payload = {
        "text": prompt
    }
    
    print(f"Sending prompt: '{prompt}'")
    try:
        response = session.post(API_URL, headers=headers, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                config = data.get("config", {})
                explanation = config.get("explanation")
                
                if explanation:
                    print("\nPASS: Explanation received!")
                    print(f"Explanation: {explanation}")
                else:
                    print("\nFAIL: No explanation content found in config.")
                    print(json.dumps(config, indent=2))
            else:
                print(f"\nFAIL: API returned success=false: {data}")
        else:
            print(f"\nFAIL: HTTP {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_explainability()
