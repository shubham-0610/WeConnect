import sqlite3

def get_connection():
    # This will create a local file "weconnect.db"
    return sqlite3.connect("weconnect.db")
