import requests
import sqlite3
import os
import time

BASE_URL = "http://localhost:5005"
LOGIN_URL = f"{BASE_URL}/login"
LOGOUT_URL = f"{BASE_URL}/logout"
LOGS_URL = f"{BASE_URL}/admin/logs"
DB_PATH = "audit.db"

USERNAME = "admin"
PASSWORD = "admin"

def test_logging():
    print("Testing Audit Logs...")
    session = requests.Session()

    # 1. Login (Should generate a log)
    print("Performing Login...")
    session.post(LOGIN_URL, data={"username": USERNAME, "password": PASSWORD})

    # 2. Generate Config (Should generate a log)
    print("Generating Config...")
    session.post(f"{BASE_URL}/api/generate", json={
        "site_info": {"name": "Test Site", "location": "Test Loc", "customer": "Test Cust", "timezone": "UTC"},
        "device": {"vendor": "fortinet", "model": "60F", "firmware_version": "7.0.5"},
        "wan_interfaces": [{"interface_name": "wan1", "ip_address": "1.1.1.1", "subnet_mask": "255.255.255.0", "gateway": "1.1.1.254", "bandwidth_mbps": 100, "priority": "primary", "isp_name": "ISP1"}],
        "lan_interfaces": [{"interface_name": "lan", "ip_address": "192.168.1.1", "subnet_mask": "255.255.255.0", "dhcp_enabled": True, "dhcp_range_start": "192.168.1.10", "dhcp_range_end": "192.168.1.100"}],
        "services": {"dns_servers": ["8.8.8.8"], "ntp_servers": ["pool.ntp.org"]},
        "policy_template": "basic",
        "webfilter_categories": []
    }, headers={"X-API-Key": "test-key"})

    # 3. Magic Fill (Should generate a log)
    # Note: Requires API Key header
    print("Calling Magic Fill...")
    session.post(f"{BASE_URL}/api/magic-fill", 
                 json={"text": "Simple test"},
                 headers={"X-API-Key": "test-key"}
    )

    # 4. Verify DB
    print("\nVerifying Database content...")
    try:
        if not os.path.exists(DB_PATH):
            print(f"FAIL: Database file {DB_PATH} not found.")
            return

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM logs ORDER BY id DESC LIMIT 5")
        rows = cursor.fetchall()
        
        found_login = False
        found_generate = False
        
        print(f"Found {len(rows)} recent logs:")
        for row in rows:
            print(row)
            if "LOGIN" in row[3] and row[2] == USERNAME:
                found_login = True
            if "GENERATE_CONFIG" in row[3]:
                found_generate = True
                
        if found_login:
            print("PASS: Login log found.")
        else:
            print("FAIL: Login log NOT found.")

        if found_generate:
            print("PASS: Generate log found.")
        else:
            print("FAIL: Generate log NOT found.")
            
        conn.close()

    except Exception as e:
        print(f"Verification failed: {e}")

if __name__ == "__main__":
    test_logging()
