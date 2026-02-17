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
        response = requests.post(API_URL, headers=headers, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print("\n✅ Magic Fill Successful!")
                print("Generated Config:")
                print(json.dumps(data["config"], indent=2))
                
                # Basic Validation
                config = data["config"]
                if config.get("device", {}).get("vendor") == "fortinet":
                    print("✅ Vendor correctly inferred as Fortinet")
                else:
                    print("❌ Vendor inference failed")
                    
                if len(config.get("wan_interfaces", [])) >= 2:
                    print("✅ Created multiple WANs")
                else:
                    print("❌ Failed to create multiple WANs")
                    
                lans = config.get("lan_interfaces", [])
                guest_vlan = next((l for l in lans if l.get("vlan_id") == 20), None)
                if guest_vlan:
                    print("✅ Guest VLAN 20 found")
                else:
                    print("❌ Guest VLAN 20 not found")
            else:
                print(f"❌ API returned success=false: {data}")
        else:
            print(f"❌ Request failed with status code {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Exception during test: {e}")

if __name__ == "__main__":
    test_magic_fill()
