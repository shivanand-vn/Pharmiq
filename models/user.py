"""
User model — fetch, create, and manage users and their roles.
"""

from db.connection import fetch_one, fetch_all, execute_query
import hashlib
import re

def _hash_password(raw_password):
    return hashlib.sha256(raw_password.encode('utf-8')).hexdigest()



def get_user_roles(user_id):
    """Return a list of role names for a user."""
    roles = fetch_all(
        """
        SELECT r.role_name
        FROM roles r
        JOIN user_roles ur ON r.role_id = ur.role_id
        WHERE ur.user_id = %s
        """,
        (user_id,)
    )
    return [r["role_name"] for r in roles]


def get_all_users_with_roles(distributor_id):
    """Return a list of all users and their roles for a distributor."""
    users = fetch_all(
        """
        SELECT u.user_id, u.username, u.email, u.name, u.mobile_no, u.status
        FROM users u
        WHERE u.distributor_id = %s
        ORDER BY u.username
        """,
        (distributor_id,)
    )
    
    for u in users:
        u["roles"] = get_user_roles(u["user_id"])
        
    return users


def _validate_user_input(name, mobile_no, username, email, password=None):
    if name and not re.match(r"^[a-zA-Z\s]{1,50}$", name):
        raise ValueError("Name should contain only letters and be under 50 characters.")
    if mobile_no and not re.match(r"^[6-9]\d{9}$", mobile_no):
        raise ValueError("Enter a valid 10-digit mobile number.")
    if len(username) < 3 or " " in username:
        raise ValueError("Username must be at least 3 characters with no spaces.")
    if not re.match(r"^[^@]+@[^@]+\.[^@]+$", email):
        raise ValueError("Enter a valid email address.")
    if password is not None:
        if len(password) < 6 or not re.search(r"[a-zA-Z]", password) or not re.search(r"\d", password):
            raise ValueError("Password must be at least 6 characters and contain letters and numbers.")

def create_user(requesting_role, distributor_id, username, role_name, email, password, name="", mobile_no="", status="active"):
    """Create a new user and assign a role."""
    if requesting_role != "Admin":
        raise PermissionError("Access denied. Admin privileges required.")

    username = username.strip().lower()
    email = email.strip()

    _validate_user_input(name, mobile_no, username, email, password)

    # Check existence
    existing = fetch_one("SELECT user_id FROM users WHERE username = %s OR email = %s", (username, email))
    if existing:
        raise ValueError("Username or Email already exists.")

    role_row = fetch_one("SELECT role_id FROM roles WHERE role_name = %s", (role_name,))
    if not role_row:
        execute_query("INSERT IGNORE INTO roles (role_name) VALUES (%s)", (role_name,))
        role_row = fetch_one("SELECT role_id FROM roles WHERE role_name = %s", (role_name,))
    role_id = role_row["role_id"]

    hashed_pw = _hash_password(password)

    execute_query(
        """
        INSERT INTO users (distributor_id, username, email, password, name, mobile_no, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (distributor_id, username, email, hashed_pw, name, mobile_no, status)
    )
    
    new_user = fetch_one("SELECT LAST_INSERT_ID() as new_id")
    user_id = new_user["new_id"]
    
    execute_query("INSERT INTO user_roles (user_id, role_id) VALUES (%s, %s)", (user_id, role_id))
    return user_id

def update_user(requesting_role, user_id, role_name, email, name="", mobile_no="", status="active", password=None):
    """Update existing user context."""
    if requesting_role != "Admin":
        raise PermissionError("Access denied. Admin privileges required.")

    email = email.strip()
    _validate_user_input(name, mobile_no, "dummy", email, password if password else None)

    existing = fetch_one("SELECT user_id FROM users WHERE email = %s AND user_id != %s", (email, user_id))
    if existing:
        raise ValueError("Email already exists for another user.")

    execute_query(
        "UPDATE users SET email = %s, name = %s, mobile_no = %s, status = %s WHERE user_id = %s",
        (email, name, mobile_no, status, user_id)
    )

    if password:
        execute_query("UPDATE users SET password = %s WHERE user_id = %s", (_hash_password(password), user_id))

    role_row = fetch_one("SELECT role_id FROM roles WHERE role_name = %s", (role_name,))
    if not role_row:
        execute_query("INSERT IGNORE INTO roles (role_name) VALUES (%s)", (role_name,))
        role_row = fetch_one("SELECT role_id FROM roles WHERE role_name = %s", (role_name,))
    
    execute_query("DELETE FROM user_roles WHERE user_id = %s", (user_id,))
    execute_query("INSERT INTO user_roles (user_id, role_id) VALUES (%s, %s)", (user_id, role_row["role_id"]))

def update_user_status(requesting_role, user_id, status):
    """Activate or deactivate a user."""
    if requesting_role != "Admin":
        raise PermissionError("Access denied. Admin privileges required.")
    execute_query("UPDATE users SET status = %s WHERE user_id = %s", (status, user_id))
