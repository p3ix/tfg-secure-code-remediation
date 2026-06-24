"""Variante segura de consulta SQL: parametrizada con placeholders.

No debe disparar la categoría `sql_injection` (B608).
"""

import sqlite3


def get_user(conn: sqlite3.Connection, user_id: str):
    cursor = conn.cursor()
    return cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchall()
