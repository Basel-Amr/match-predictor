from db import get_connection
import hashlib
from utils import hash_password, execute_query
import streamlit as st

def get_players(search=""):
    conn = get_connection()
    cur = conn.cursor()

    query = """
        SELECT 
            p.id, 
            p.username, 
            p.email, 
            p.role, 
            p.avatar_url,
            p.last_login_at,
            IFNULL(SUM(pr.score), 0) AS total_points,
            IFNULL(a.total_leagues_won, 0),
            IFNULL(a.total_cups_won, 0)
        FROM players p
        LEFT JOIN predictions pr ON p.id = pr.player_id
        LEFT JOIN achievements a ON p.id = a.player_id
    """

    params = []
    if search:
        query += " WHERE p.username LIKE ? OR p.email LIKE ?"
        params = [f"%{search}%", f"%{search}%"]

    query += " GROUP BY p.id, p.username, p.email, p.role, p.avatar_url, p.last_login_at, a.total_leagues_won, a.total_cups_won"

    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()

    return [{
        "id": r[0],
        "username": r[1],
        "email": r[2],
        "role": r[3],
        "avatar_url": r[4],
        "last_login_at": r[5],
        "total_points": r[6],
        "total_leagues_won": r[7],
        "total_cups_won": r[8]
    } for r in rows]


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
    try:
        if password:
            password_hash = hash_password(password)
            cur.execute("UPDATE players SET username=?, email=?, role=?, password_hash=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                        (username, email, role, password_hash, player_id))
        else:
            cur.execute("UPDATE players SET username=?, email=?, role=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                        (username, email, role, player_id))
        conn.commit()
        return True  # ✅ Add this
    except Exception as e:
        print(f"❌ update_player error: {e}")
        return False  # ✅ Add error handling to reflect failure
    finally:
        conn.close()


def delete_player(player_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM players WHERE id=?", (player_id,))
    conn.commit()
    conn.close()

def update_achievements(player_id, total_leagues_won, total_cups_won):
    st.write(f"🔍 Updating achievements for player_id: {player_id}")
    st.write(f"🏆 Leagues Won: {total_leagues_won}, 🏆 Cups Won: {total_cups_won}")

    query = """
    INSERT INTO achievements (player_id, total_leagues_won, total_cups_won)
    VALUES (?, ?, ?)
    ON CONFLICT(player_id) DO UPDATE SET
        total_leagues_won = excluded.total_leagues_won,
        total_cups_won = excluded.total_cups_won,
        updated_at = CURRENT_TIMESTAMP;
    """
    try:
        execute_query(query, (player_id, total_leagues_won, total_cups_won))
        st.success("✅ Achievements updated in the database.")
        return True
    except Exception as e:
        st.error(f"❌ Error updating achievements: {e}")
        return False

