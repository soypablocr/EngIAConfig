import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

DB_NAME = "audit.db"
TEST_USER = "test_user_auth"
TEST_PASS = "password123"

def setup():
    # Clean up previous test
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE username = ?", (TEST_USER,))
        conn.commit()

def test_registration():
    print(f"1. Registering user '{TEST_USER}'...")
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        hashed_pw = generate_password_hash(TEST_PASS)
        cursor.execute(
            "INSERT INTO users (username, password_hash, is_authorized, created_at) VALUES (?, ?, 0, ?)",
            (TEST_USER, hashed_pw, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        conn.commit()
    print("   User registered in DB (Unauthorized).")

def test_login_unauthorized():
    print("2. Testing login (Unauthorized)...")
    with sqlite3.connect(DB_NAME) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (TEST_USER,))
        user = cursor.fetchone()
        
        if user and check_password_hash(user['password_hash'], TEST_PASS):
            if not user['is_authorized']:
                print("   SUCCESS: Login blocked (Pending Approval).")
            else:
                print("   FAILED: User should be unauthorized!")
        else:
            print("   FAILED: Credentials rejected incorrectly.")

def test_admin_approval():
    print("3. Approving user (Admin Action)...")
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET is_authorized = 1 WHERE username = ?", (TEST_USER,))
        conn.commit()
    print("   User authorized.")

def test_login_authorized():
    print("4. Testing login (Authorized)...")
    with sqlite3.connect(DB_NAME) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (TEST_USER,))
        user = cursor.fetchone()
        
        if user and user['is_authorized']:
             print("   SUCCESS: Login successful.")
        else:
             print("   FAILED: Login failed or user not authorized.")

if __name__ == "__main__":
    try:
        setup()
        test_registration()
        test_login_unauthorized()
        test_admin_approval()
        test_login_authorized()
        setup() # Cleanup
    except Exception as e:
        print(f"ERROR: {e}")
