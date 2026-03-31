import sys
import os
import hashlib

# Add project root to sys path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from db.connection import execute_query, fetch_all, fetch_one

def run_migration():
    print("Starting Users & Auth Migration...")
    
    # Check if 'email' column already exists in 'users'
    columns = fetch_all("SHOW COLUMNS FROM users LIKE 'email'")
    if not columns:
        print("Adding 'email' column to 'users' table...")
        execute_query("ALTER TABLE users ADD COLUMN email VARCHAR(100) UNIQUE AFTER username")
        print("'email' column added.")
    else:
        print("'email' column already exists.")
        
    # Process password hashing for existing users
    print("Checking for plaintext passwords in 'users' table to convert to SHA-256 hashes...")
    users = fetch_all("SELECT user_id, username, password FROM users")
    
    hashed_count = 0
    for u in users:
        # A rough heuristic to see if it's already a SHA-256 hash
        # sha256 hex string is exactly 64 characters long and only alphanumeric.
        pf = u['password']
        if len(pf) == 64 and pf.isalnum():
            # Already a hash
            continue
            
        print(f"Hashing plaintext password for user '{u['username']}'...")
        # Hash it using SHA-256
        new_hash = hashlib.sha256(pf.encode('utf-8')).hexdigest()
        
        execute_query("UPDATE users SET password = %s WHERE user_id = %s", (new_hash, u['user_id']))
        hashed_count += 1
        
    print(f"Finished. Hashed {hashed_count} user passwords.")
    print("Migration complete!")

if __name__ == "__main__":
    run_migration()
