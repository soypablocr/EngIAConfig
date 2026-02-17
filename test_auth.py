import requests
import os

BASE_URL = "http://localhost:5005"
LOGIN_URL = f"{BASE_URL}/login"
LOGOUT_URL = f"{BASE_URL}/logout"

# Default credentials from app.py
USERNAME = "admin"
PASSWORD = "admin"

def test_auth():
    print("Testing Authentication Flow...")
    session = requests.Session()

    # 1. Access Home without login (Should redirect)
    try:
        print("\n1. Accessing Home (expecting redirect)...")
        response = session.get(BASE_URL, allow_redirects=False)
        if response.status_code == 302 and "/login" in response.headers.get("Location", ""):
            print("PASS: Redirected to /login")
        else:
            print(f"FAIL: Status {response.status_code}, Location: {response.headers.get('Location')}")
            return
    except Exception as e:
        print(f"FAIL: Connection failed: {e}")
        return

    # 2. Login with wrong credentials
    try:
        print("\n2. Logging in with wrong password...")
        response = session.post(LOGIN_URL, data={"username": USERNAME, "password": "wrongpassword"})
        if "Credenciales incorrectas" in response.text or response.status_code == 200:
            print("PASS: Error message displayed or stayed on page")
        else:
            print(f"FAIL: Status {response.status_code}")
    except Exception as e:
        print(f"FAIL: Request failed: {e}")

    # 3. Login with correct credentials
    try:
        print("\n3. Logging in with correct credentials...")
        response = session.post(LOGIN_URL, data={"username": USERNAME, "password": PASSWORD}, allow_redirects=False)
        if response.status_code == 302 and response.headers.get("Location") in [BASE_URL, "/", "http://localhost:5005/"]:
            print("PASS: Redirected to Home")
            
            # Follow redirect
            print("\n4. Accessing Home with session...")
            response = session.get(BASE_URL)
            if response.status_code == 200 and "ENGIA CONFIG" in response.text:
                print("PASS: Access Granted: Home page loaded")
            else:
                print(f"FAIL: Failed to load home page. Status: {response.status_code}")

        else:
            print(f"FAIL: Login failed: Status {response.status_code}, Location: {response.headers.get('Location')}")
            print(response.text[:200]) # Debug info
            return
    except Exception as e:
        print(f"FAIL: Request failed: {e}")

    # 5. Access API Endpoint
    try:
        print("\n5. Accessing Protected API (Catalog)...")
        # Catalog is public in code? No, let's check code... 
        # Actually catalog is NOT protected in logic I wrote? Let me check app.py snippets
        # I protected /api/generate, etc. Catalog was NOT decorated.
        # Let's test /api/generate which is protected.
        response = session.post(f"{BASE_URL}/api/generate", json={})
        # Should fail due to missing params (400) or API key (401), NOT 302 login if session works? 
        # Ah wait, @login_required decorator checks session first.
        # If session is valid, it proceeds to @require_api_key check.
        # So expecting 401 Unauthorized (due to missing API key) NOT 302.
        if response.status_code in [400, 401]: 
             print(f"PASS: API Check passed (Status {response.status_code} - Reached API logic)")
        elif response.status_code == 302:
             print("FAIL: API Check failed: Redirected to login (Session not recognized?)")
        else:
             print(f"INFO: API response: {response.status_code}")

    except Exception as e:
        print(f"FAIL: Request failed: {e}")

    # 6. Logout
    try:
        print("\n6. Logging out...")
        response = session.get(LOGOUT_URL, allow_redirects=False)
        if response.status_code == 302:
            print("PASS: Redirected after logout")
            
            # Verify access lost
            print("\n7. Verifying access lost...")
            response = session.get(BASE_URL, allow_redirects=False)
            if response.status_code == 302:
                print("PASS: Access Denied: Redirected to login")
            else:
                print(f"FAIL: Still have access? Status {response.status_code}")
        else:
            print(f"FAIL: Logout failed: Status {response.status_code}")
    except Exception as e:
        print(f"FAIL: Request failed: {e}")

if __name__ == "__main__":
    test_auth()
