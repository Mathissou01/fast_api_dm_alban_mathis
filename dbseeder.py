import sqlite3
from sqlite3 import Connection
import bcrypt

DATABASE_NAME = "chat.db"

def get_db_connection() -> Connection:
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def create_user(username: str, password: str, full_name: str = None, email: str = None):
    conn = get_db_connection()
    cursor = conn.cursor()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    cursor.execute("""
        INSERT INTO users (username, hashed_password, full_name, email)
        VALUES (?, ?, ?, ?)
    """, (username, hashed_password, full_name, email))
    conn.commit()
    conn.close()

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            hashed_password TEXT NOT NULL,
            full_name TEXT,
            email TEXT,
            disabled BOOLEAN DEFAULT FALSE
        )
    """)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()

    users = [
        {"username": "user1", "password": "password1", "full_name": "User One", "email": "user1@example.com"},
        {"username": "user2", "password": "password2", "full_name": "User Two", "email": "user2@example.com"},
        {"username": "user3", "password": "password3", "full_name": "User Three", "email": "user3@example.com"},
        {"username": "user4", "password": "password4", "full_name": "User Four", "email": "user4@example.com"},
    ]

    for user in users:
        create_user(user["username"], user["password"], user["full_name"], user["email"])
        print(f"Created user: {user['username']} with password: {user['password']}")
