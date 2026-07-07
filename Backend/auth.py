from Backend.database.connection import get_connection
import random
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv
import os

load_dotenv()  # Load environment variables from .env file

def signup_user(name, username, email, password):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO users (name, username, email, password) VALUES (?, ?, ?, ?)",
            (name, username, email, password)
        )
        conn.commit()
        return True, "Signup successful!"
    except Exception as e:
        return False, f"Error: {e}"
    finally:
        cur.close()
        conn.close()


def login_user(username, password):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT id, name, username, email, photo FROM users WHERE username = ? AND password = ?",
            (username, password)
        )
        user = cur.fetchone()
        if user:
            return True, user  # return full user record
        else:
            return False, None
    except Exception as e:
        return False, f"Error: {e}"
    finally:
        cur.close()
        conn.close()


def update_photo(username, photo_path):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "UPDATE users SET photo = ? WHERE username = ?",
            (photo_path, username)
        )
        conn.commit()
        return True, "Photo updated successfully!"
    except Exception as e:
        return False, f"Error: {e}"
    finally:
        cur.close()
        conn.close()



def generate_otp():
    return str(random.randint(100000, 999999))

def send_otp_email(to_email, otp):
    # Gmail account credentials
    sender_email = os.getenv("GMAIL_USER")  # Your Gmail address
    app_password = os.getenv("GMAIL_APP_PASSWORD")  # generated from Google Account → Security → App Passwords

    msg = MIMEText(f"Your WeConnect password reset OTP is: {otp}")
    msg["Subject"] = "WeConnect Password Reset OTP"
    msg["From"] = sender_email
    msg["To"] = to_email

    try:
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(sender_email, app_password)
        server.sendmail(sender_email, [to_email], msg.as_string())
        server.quit()
        return True, "OTP sent successfully!"
    except Exception as e:
        return False, f"Error sending email: {e}"

def set_reset_otp(username, otp):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE users SET reset_otp = ? WHERE username = ?", (otp, username))
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        cur.close()
        conn.close()

def verify_otp(username, otp):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT reset_otp FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row and row[0] == otp

def reset_password(username, new_password):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE users SET password = ?, reset_otp = NULL WHERE username = ?", (new_password, username))
        conn.commit()
        return True, "Password reset successfully!"
    except Exception as e:
        return False, f"Error: {e}"
    finally:
        cur.close()
        conn.close()


def get_all_users(exclude_username):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, username FROM users WHERE username != ?", (exclude_username,))
    users = cur.fetchall()
    conn.close()
    return users

def send_friend_request(sender_id, receiver_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO friend_requests (sender_id, receiver_id) VALUES (?, ?)", (sender_id, receiver_id))
    conn.commit()
    conn.close()
    return True

def get_friend_requests(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT fr.id, u.username, fr.status
        FROM friend_requests fr
        JOIN users u ON fr.sender_id = u.id
        WHERE fr.receiver_id = ?
    """, (user_id,))
    requests = cur.fetchall()
    conn.close()
    return requests

def respond_to_request(request_id, status):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE friend_requests SET status = ? WHERE id = ?", (status, request_id))
    conn.commit()
    conn.close()
    return True

def get_friends(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT u.username
        FROM friend_requests fr
        JOIN users u ON fr.sender_id = u.id
        WHERE fr.receiver_id = ? AND fr.status = 'approved'
        UNION
        SELECT u.username
        FROM friend_requests fr
        JOIN users u ON fr.receiver_id = u.id
        WHERE fr.sender_id = ? AND fr.status = 'approved'
    """, (user_id, user_id))
    friends = cur.fetchall()
    conn.close()
    return friends

def send_message(sender_id, receiver_id, content):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO messages (sender_id, receiver_id, content) VALUES (?, ?, ?)", (sender_id, receiver_id, content))
    conn.commit()
    conn.close()
    return True

def get_messages(user_id, friend_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT u.username, m.content, m.timestamp
        FROM messages m
        JOIN users u ON m.sender_id = u.id
        WHERE (m.sender_id = ? AND m.receiver_id = ?)
           OR (m.sender_id = ? AND m.receiver_id = ?)
        ORDER BY m.timestamp ASC
    """, (user_id, friend_id, friend_id, user_id))
    msgs = cur.fetchall()
    conn.close()
    return msgs
