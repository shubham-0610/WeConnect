from Backend.database.connection import get_connection

def create_table():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            photo TEXT,  -- store image file path or URL
            reset_otp TEXT  -- store OTP for password reset
        )
    """)
    conn.commit()
    cur.close()
    conn.close()
