"""
User model — fetch, create, and manage users and their roles.
"""

from db.connection import fetch_one, fetch_all, execute_query


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
        SELECT u.user_id, u.username, u.status
        FROM users u
        WHERE u.distributor_id = %s
        ORDER BY u.username
        """,
        (distributor_id,)
    )
    
    for u in users:
        u["roles"] = get_user_roles(u["user_id"])
        
    return users


def create_user(distributor_id, username, password, role_name):
    """Create a new user and assign a role."""
    # 1. Ensure role exists or get its ID
    role_row = fetch_one("SELECT role_id FROM roles WHERE role_name = %s", (role_name,))
    if not role_row:
        # If role doesn't exist, normally we'd create it, but let's assume standard roles exist 
        # as per schema or we insert it.
        execute_query("INSERT IGNORE INTO roles (role_name) VALUES (%s)", (role_name,))
        role_row = fetch_one("SELECT role_id FROM roles WHERE role_name = %s", (role_name,))
        
    role_id = role_row["role_id"]

    # 2. Create the user
    execute_query(
        """
        INSERT INTO users (distributor_id, username, password, status)
        VALUES (%s, %s, %s, 'active')
        """,
        (distributor_id, username, password)
    )
    
    # Get the new user ID
    new_user = fetch_one("SELECT LAST_INSERT_ID() as new_id")
    user_id = new_user["new_id"]
    
    # 3. Assign role
    execute_query(
        """
        INSERT INTO user_roles (user_id, role_id)
        VALUES (%s, %s)
        """,
        (user_id, role_id)
    )
    
    return user_id

def update_user_status(user_id, status):
    """Activate or deactivate a user."""
    execute_query("UPDATE users SET status = %s WHERE user_id = %s", (status, user_id))
