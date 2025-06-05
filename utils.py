# utils.py
import hashlib
import bcrypt

def hash_password(password: str) -> bytes:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt())

def verify_password(password, hashed):
    if isinstance(hashed, str):
        hashed = hashed.encode('utf-8')
    return bcrypt.checkpw(password.encode('utf-8'), hashed)


def execute_query(query: str, params: tuple = ()):
    from db import get_connection
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(query, params)
    conn.commit()
    return cur

def fetch_one(query: str, params: tuple = ()):
    cur = execute_query(query, params)
    return cur.fetchone()

def fetch_all(query: str, params: tuple = ()):
    cur = execute_query(query, params)
    return cur.fetchall()
