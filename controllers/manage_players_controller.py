from db import get_connection
import hashlib
from utils import hash_password


def get_players(search=""):
    conn = get_connection()
    cur = conn.cursor()
    if search:
        cur.execute("SELECT id, username, email, role, avatar_url FROM players WHERE username LIKE ? OR email LIKE ?",
                    (f"%{search}%", f"%{search}%"))
    else:
        cur.execute("SELECT id, username, email, role, avatar_url FROM players")
    rows = cur.fetchall()
    conn.close()
    return [{"id": r[0], "username": r[1], "email": r[2], "role": r[3], "avatar_url": r[4]} for r in rows]

def add_player(username, email, role, password):
    conn = get_connection()
    cur = conn.cursor()
    password_hash = hash_password(password)
    cur.execute("INSERT INTO players (username, email, role, password_hash) VALUES (?, ?, ?, ?)",
                (username, email, role, password_hash))
    conn.commit()
    conn.close()

def update_player(player_id, username, email, role, password=None):
    conn = get_connection()
    cur = conn.cursor()
    if password:
        password_hash = hash_password(password)
        cur.execute("UPDATE players SET username=?, email=?, role=?, password_hash=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                    (username, email, role, password_hash, player_id))
    else:
        cur.execute("UPDATE players SET username=?, email=?, role=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                    (username, email, role, player_id))
    conn.commit()
    conn.close()

def delete_player(player_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM players WHERE id=?", (player_id,))
    conn.commit()
    conn.close()
