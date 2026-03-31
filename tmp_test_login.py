import sys
import os
import hashlib
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from db.connection import fetch_one

def test_login():
    username = "svadmin"
    password = "admin123"
    
    hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()
    user = fetch_one(
        "SELECT user_id, username, password FROM users WHERE username = %s AND password = %s",
        (username, hashed_password)
    )
    if user:
        print(f"Login SUCCESS for {user['username']}")
    else:
        print("Login FAILED!")

if __name__ == "__main__":
    test_login()
