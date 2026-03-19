"""
Distributor model — fetch distributor profile data.
"""

from db.connection import fetch_one


def get_distributor_by_id(distributor_id):
    """Return full distributor profile dict or None."""
    return fetch_one(
        "SELECT * FROM distributors WHERE distributor_id = %s AND status = 'active'",
        (distributor_id,),
    )


def get_distributor_by_user_id(user_id):
    """Return distributor profile for the given user."""
    return fetch_one(
        """
        SELECT d.* FROM distributors d
        JOIN users u ON u.distributor_id = d.distributor_id
        WHERE u.user_id = %s AND d.status = 'active'
        """,
        (user_id,),
    )
