"""
MySQL connection helpers for PharmIQ.
"""

import mysql.connector
from mysql.connector import Error
from db.config import DB_CONFIG


def get_connection():
    """Return a new MySQL connection using DB_CONFIG."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        print(f"[DB] Connection error: {e}")
        raise


def execute_query(query, params=None, commit=True):
    """Execute an INSERT / UPDATE / DELETE query. Returns lastrowid."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(query, params or ())
        if commit:
            conn.commit()
        return cursor.lastrowid
    except Error as e:
        conn.rollback()
        print(f"[DB] Query error: {e}")
        raise
    finally:
        cursor.close()
        conn.close()


def execute_many(query, data_list, commit=True):
    """Execute a batch INSERT with executemany."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.executemany(query, data_list)
        if commit:
            conn.commit()
        return cursor.lastrowid
    except Error as e:
        conn.rollback()
        print(f"[DB] Batch query error: {e}")
        raise
    finally:
        cursor.close()
        conn.close()


def fetch_all(query, params=None):
    """Execute a SELECT and return all rows as list of dicts."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(query, params or ())
        return cursor.fetchall()
    except Error as e:
        print(f"[DB] Fetch error: {e}")
        raise
    finally:
        cursor.close()
        conn.close()


def fetch_one(query, params=None):
    """Execute a SELECT and return a single row as dict or None."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(query, params or ())
        return cursor.fetchone()
    except Error as e:
        print(f"[DB] Fetch error: {e}")
        raise
    finally:
        cursor.close()
        conn.close()


def init_database():
    """Create the pharmiq database if it doesn't exist, then run schema."""
    import os

    # First connect without specifying the database
    config_no_db = {k: v for k, v in DB_CONFIG.items() if k != "database"}
    try:
        conn = mysql.connector.connect(**config_no_db)
        cursor = conn.cursor()
        cursor.execute(
            f"CREATE DATABASE IF NOT EXISTS `{DB_CONFIG['database']}` "
            f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )
        conn.commit()
        cursor.close()
        conn.close()
    except Error as e:
        print(f"[DB] Could not create database: {e}")
        raise

    # Now run the schema file
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    if os.path.exists(schema_path):
        conn = get_connection()
        cursor = conn.cursor()
        try:
            with open(schema_path, "r", encoding="utf-8") as f:
                sql = f.read()
            # Execute each statement separately
            for statement in sql.split(";"):
                stmt = statement.strip()
                if stmt:
                    cursor.execute(stmt)
            conn.commit()
            print("[DB] Schema initialized successfully.")
        except Error as e:
            conn.rollback()
            print(f"[DB] Schema error: {e}")
            raise
        finally:
            cursor.close()
            conn.close()

    # Run seed data
    seed_path = os.path.join(os.path.dirname(__file__), "seed_data.sql")
    if os.path.exists(seed_path):
        conn = get_connection()
        cursor = conn.cursor()
        try:
            with open(seed_path, "r", encoding="utf-8") as f:
                sql = f.read()
            for statement in sql.split(";"):
                stmt = statement.strip()
                if stmt:
                    cursor.execute(stmt)
            conn.commit()
            print("[DB] Seed data loaded successfully.")
        except Error as e:
            conn.rollback()
            print(f"[DB] Seed data error (may already exist): {e}")
        finally:
            cursor.close()
            conn.close()
