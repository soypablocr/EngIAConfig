import requests
import json
import os

API_URL = "http://localhost:5005/api/magic-fill"
API_KEY = os.environ.get("ENGIA_API_KEY", "test-key")

def test_magic_fill():
    prompt = "Create a Fortinet configuration for a site in Madrid with 2 WANs (Primary 1Gbps, Backup 500Mbps) and a Guest VLAN 20."
    
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY
    }
    
    payload = {
        "text": prompt
    }
    
    print(f"Testing Magic Fill with prompt: '{prompt}'")
    try:
        session = requests.Session()
        
        # 1. Login
        login_response = session.post("http://localhost:5005/login", 
                                    data={"username": "admin", "password": "ChangeMeNow!"},
                                    allow_redirects=False)
        
        if login_response.status_code not in [200, 302]:
            print(f"[FAIL] Login failed: {login_response.status_code}")
            return
            
        print("[OK] Login successful (Session created)")

        # 2. Magic Fill
        response = session.post(API_URL, headers=headers, json=payload)
        
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
        except json.JSONDecodeError:
            print("ERROR: Response is not valid JSON")
            print("Raw Response Text:")
            print(response.text)
            return

        if response.status_code == 200:
            if data.get("success"):
                print("\n[OK] Magic Fill Successful!")
                print("Generated Config:")
                print(json.dumps(data["config"], indent=2))
                
                # Basic Validation
                config = data["config"]
                if config.get("device", {}).get("vendor") == "fortinet":
                    print("[OK] Vendor correctly inferred as Fortinet")
                else:
                    print("[FAIL] Vendor inference failed")
                    
                if len(config.get("wan_interfaces", [])) >= 2:
                    print("[OK] Created multiple WANs")
                else:
                    print("[FAIL] Failed to create multiple WANs")
                    
                lans = config.get("lan_interfaces", [])
                guest_vlan = next((l for l in lans if l.get("vlan_id") == 20), None)
                if guest_vlan:
                    print("[OK] Guest VLAN 20 found")
                else:
                    print("[FAIL] Guest VLAN 20 not found")
            else:
                print(f"[FAIL] API returned success=false: {data}")
        else:
            print(f"[FAIL] Request failed with status code {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"[ERROR] Exception during test: {e}")

if __name__ == "__main__":
    test_magic_fill()
