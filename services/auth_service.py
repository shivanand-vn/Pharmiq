"""
Auth Service - Handles OTP generation, sending via Brevo SMTP, and password resets.
"""

import os
import random
import time
import threading
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import bcrypt
import hashlib
from dotenv import load_dotenv
from db.connection import fetch_one, execute_query

load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = os.getenv("SMTP_PORT")
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")

# In-memory OTP storage
# Format: { user_id: {"otp": "123456", "expiry": timestamp, "attempts": 0} }
OTP_STORE = {}

# Constants
OTP_EXPIRY_MINUTES = 5
MAX_OTP_ATTEMPTS = 3


def generate_otp():
    """Generate a 6-digit numeric OTP."""
    return str(random.randint(100000, 999999))


def store_otp(user_id, otp):
    """Store the OTP with an expiry time and attempt count."""
    expiry_time = time.time() + (OTP_EXPIRY_MINUTES * 60)
    OTP_STORE[user_id] = {
        "otp": otp,
        "expiry": expiry_time,
        "attempts": 0
    }


def send_email_otp(email, otp):
    """Send an OTP email asynchronously using Brevo SMTP."""
    def send_task():
        try:
            if not all([SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, SENDER_EMAIL]):
                print("[Auth Service] SMTP configuration missing. Cannot send email.")
                return

            port = int(SMTP_PORT)
            
            # Construct email
            msg = MIMEMultipart()
            msg['From'] = SENDER_EMAIL
            msg['To'] = email
            msg['Subject'] = "Password Reset OTP"
            
            body = f"Your OTP for password reset is: {otp}\nValid for {OTP_EXPIRY_MINUTES} minutes. Do not share this code.\n\nThis is a System generated mail do not reply to it.\n\nRegards,\nDevelopment team - Pharmiq "
            msg.attach(MIMEText(body, 'plain'))
            
            # Connect to SMTP server
            server = smtplib.SMTP(SMTP_HOST, port)
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
            server.quit()
            print(f"[Auth Service] OTP email sent successfully to {email}")
        except Exception as e:
            print(f"[Auth Service] Failed to send OTP email: {e}")

    thread = threading.Thread(target=send_task, daemon=True)
    thread.start()


def initiate_password_reset(email):
    """
    Check if an email exists by checking users and distributors tables.
    If exists, generate an OTP, store it, and send it.
    """
    import re
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        return {"status": "error", "message": "Invalid email format."}
        
    try:
        user = fetch_one(
            """
            SELECT u.user_id, COALESCE(u.email, d.email) as matched_email, u.username
            FROM users u
            JOIN distributors d ON u.distributor_id = d.distributor_id
            WHERE u.email = %s OR (d.email = %s AND (u.email IS NULL OR u.email = ''))
            ORDER BY u.user_id ASC
            LIMIT 1
            """,
            (email, email)
        )
        
        if user and user.get("matched_email"):
            user_id = user["user_id"]
            matched_email = user["matched_email"]
            
            otp = generate_otp()
            store_otp(user_id, otp)
            send_email_otp(matched_email, otp)
            
            # Return user_id so the UI knows which user is trying to reset
            # (Note: Returning user_id internally is fine, UI won't expose it)
            return {"status": "success", "user_id": user_id, "message": "OTP sent"}
        
        # Return error if user not found or no email
        return {"status": "error", "message": "No account found or missing email."}
    except Exception as e:
        print(f"[Auth Service] initiate_password_reset error: {e}")
        return {"status": "error", "message": "An error occurred."}


def verify_otp(user_id, input_otp):
    """
    Validate the OTP. Checks for correctness, expiry, and max attempts.
    """
    if user_id not in OTP_STORE:
        return {"status": "error", "message": "No active OTP session found or session expired."}
        
    session = OTP_STORE[user_id]
    
    if time.time() > session["expiry"]:
        del OTP_STORE[user_id]
        return {"status": "error", "message": "OTP has expired. Please request a new one."}
        
    if session["attempts"] >= MAX_OTP_ATTEMPTS:
        del OTP_STORE[user_id]
        return {"status": "error", "message": "Maximum attempts reached. Please request a new OTP."}
        
    if session["otp"] == input_otp.strip():
        # Valid OTP
        # Do not delete yet, we need the session to be valid to allow password reset
        # Or mark as verified
        session["verified"] = True
        return {"status": "success", "message": "OTP verified successfully."}
    else:
        session["attempts"] += 1
        remaining = MAX_OTP_ATTEMPTS - session["attempts"]
        return {"status": "error", "message": f"Invalid OTP. {remaining} attempts remaining."}


def reset_password(user_id, new_password):
    """
    Hash the new password using bcrypt and update the database.
    Invalidate the OTP session after success.
    """
    if user_id not in OTP_STORE or not OTP_STORE[user_id].get("verified"):
        return {"status": "error", "message": "Unauthorized password reset attempt."}
        
    try:
        # Generate bcrypt hash
        hashed_pw = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        execute_query("UPDATE users SET password = %s WHERE user_id = %s", (hashed_pw, user_id))
        
        # Clean up OTP session
        del OTP_STORE[user_id]
        return {"status": "success", "message": "Password reset successfully."}
    except Exception as e:
        print(f"[Auth Service] reset_password error: {e}")
        return {"status": "error", "message": "Database error during password reset."}


def verify_password(stored_password, input_password):
    """
    Helper function to verify password.
    Checks if stored_password is a bcrypt hash (starts with $2b$ or $2a$), 
    if not, falls back to SHA-256 for backward compatibility.
    """
    if stored_password.startswith('$2b$') or stored_password.startswith('$2a$'):
        return bcrypt.checkpw(input_password.encode('utf-8'), stored_password.encode('utf-8'))
    else:
        # Fallback to legacy SHA-256
        hashed_input = hashlib.sha256(input_password.encode('utf-8')).hexdigest()
        return stored_password == hashed_input
