import sqlite3
import random
import string
from datetime import datetime

DB_NAME = 'passwords.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Table for access keys
    c.execute('''
        CREATE TABLE IF NOT EXISTS access_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE,
            duration INTEGER,
            created_at TEXT,
            used INTEGER DEFAULT 0
        )
    ''')

    # Table for user logs
    c.execute('''
        CREATE TABLE IF NOT EXISTS user_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip TEXT,
            action_time TEXT
        )
    ''')

    conn.commit()
    conn.close()

def generate_random_key(length=12):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def create_access_key(duration_days):
    key = generate_random_key()
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO access_keys (key, duration, created_at) VALUES (?, ?, ?)",
              (key, duration_days, datetime.utcnow().strftime("%Y-%m-%d")))
    conn.commit()
    conn.close()
    return key

def validate_access_key(key):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT duration, used FROM access_keys WHERE key=?", (key,))
    row = c.fetchone()
    if row and row[1] == 0:
        c.execute("UPDATE access_keys SET used=1 WHERE key=?", (key,))
        conn.commit()
        conn.close()
        return row[0]
    conn.close()
    return None

def log_user_activity(ip):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO user_logs (ip, action_time) VALUES (?, ?)",
              (ip, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()
