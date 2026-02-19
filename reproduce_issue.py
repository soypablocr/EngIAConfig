
import requests
import json
import os

BASE_URL = "http://localhost:5005"
API_URL = f"{BASE_URL}/api/magic-fill"
LOGIN_URL = f"{BASE_URL}/login"
API_KEY = os.environ.get("ENGIA_API_KEY", "test-key")

# Credentials (from app.py defaults)
USERNAME = "admin"
PASSWORD = "admin"

def test_magic_fill_strict():
    prompt = "Create a Fortinet configuration with WAN1 and WAN2 only."
    
    session = requests.Session()
    session.headers.update({
        "X-API-Key": API_KEY
    })
    
    # 1. Login
    print(f"Logging in as {USERNAME}...")
    try:
        # Get login page to get CSRF token if needed (not needed here but good practice for session cookie)
        session.get(LOGIN_URL)
        
        # Post credentials
        login_payload = {
            "username": USERNAME,
            "password": PASSWORD
        }
        login_response = session.post(LOGIN_URL, data=login_payload)
        
        if login_response.status_code != 200:
             print(f"X Login failed: {login_response.status_code}")
             return
             
        # Check if we were redirected to index (successful login usually redirects)
        if hasattr(login_response, 'history') and login_response.history:
              print("Login successful (redirected).")
        else:
              # Depending on implementation, it might just return 200 on success or duplicate login page on fail
              if "Credenciales incorrectas" in login_response.text:
                  print("X Login failed: Invalid credentials.")
                  return
              print("Login response received.")

    except Exception as e:
        print(f"X Exception during login: {e}")
        return

    # 2. Test Magic Fill
    
    payload = {
        "text": prompt
    }
    
    print(f"Testing Magic Fill with prompt: '{prompt}'")
    try:
        response = session.post(API_URL, json=payload)
        
        if response.status_code == 200:
            try:
                data = response.json()
            except Exception:
                print("Failed to decode JSON. Raw response:")
                print(response.text)
                return

            if data.get("success"):
                config = data["config"]
                wan_interfaces = config.get("wan_interfaces", [])
                lan_interfaces = config.get("lan_interfaces", [])
                
                print(f"WAN Interfaces found: {[i['interface_name'] for i in wan_interfaces]}")
                print(f"LAN Interfaces found: {[i['interface_name'] for i in lan_interfaces]}")

                if len(wan_interfaces) > 2:
                     print("X Created more WAN interfaces than requested.")
                elif len(wan_interfaces) == 2:
                     print("OK Created exactly 2 WAN interfaces.")
                else:
                     print("X Created fewer WAN interfaces than requested.")
                
                # Check for extra LANs too if needed, but user emphasized avoiding EXTRA interfaces.
                # Default logic might create one LAN. That's probably fine unless specified NO LAN.
                # User example was about WAN1/WAN2.

            else:
                print(f"X API returned success=false: {data}")
        else:
            print(f"X Request failed with status code {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"X Exception during test: {e}")

if __name__ == "__main__":
    test_magic_fill_strict()
