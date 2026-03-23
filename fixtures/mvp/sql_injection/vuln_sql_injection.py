import sqlite3

def get_user(username: str):
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    query = f"SELECT * FROM users WHERE username = '{username}'"
    return cursor.execute(query).fetchall()
