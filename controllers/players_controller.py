import sqlite3
from db import get_connection  
import bcrypt
from PIL import Image

import os

def get_player_info(player_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT 
            id, 
            username, 
            email, 
            avatar_url, 
            created_at,
            (SELECT COALESCE(SUM(score), 0) FROM predictions WHERE player_id = players.id) AS total_points
        FROM players 
        WHERE id = ?
    """, (player_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "id": row[0],
        "username": row[1],
        "email": row[2],
        "avatar_url": row[3],
        "created_at": row[4],
        "total_points": row[5],
    }


def update_player_info(player_id, username, email, password, avatar_url):
    conn = get_connection()
    cur = conn.cursor()
    try:
        password_hash = None
        if password:
            # Hash with bcrypt
            salt = bcrypt.gensalt()
            password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

        if password_hash:
            cur.execute("""
                UPDATE players SET username=?, email=?, password_hash=?, avatar_url=?, updated_at=CURRENT_TIMESTAMP
                WHERE id=?
            """, (username, email, password_hash, avatar_url, player_id))
        else:
            cur.execute("""
                UPDATE players SET username=?, email=?, avatar_url=?, updated_at=CURRENT_TIMESTAMP
                WHERE id=?
            """, (username, email, avatar_url, player_id))

        conn.commit()
        return True
    except Exception as e:
        print("Error updating player:", e)
        return False
    finally:
        conn.close()

def delete_player(player_id):
    conn = get_connection()
    cur = conn.cursor()
    try:
        # Get avatar path from DB
        cur.execute("SELECT avatar_path FROM players WHERE id = ?", (player_id,))
        row = cur.fetchone()
        avatar_path = row[0] if row else None

        # Delete player from DB
        cur.execute("DELETE FROM players WHERE id = ?", (player_id,))
        conn.commit()

        # Normalize path and delete image
        if avatar_path:
            normalized_path = os.path.normpath(avatar_path)
            if os.path.exists(normalized_path):
                os.remove(normalized_path)
                print(f"✅ Deleted avatar: {normalized_path}")
            else:
                print(f"❌ Avatar path does not exist: {normalized_path}")

        return True
    except Exception as e:
        print("Error deleting player:", e)
        return False
    finally:
        conn.close()

def get_player_id_by_username(username):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM players WHERE username = ?", (username,))
    row = cur.fetchone()
    conn.close()
    if row:
        return row[0]
    return None


def save_avatar_image(player_id, image):
    """
    Save avatar image to 'assets/avatars/{player_id}.png' and update avatar_path in DB.

    Args:
        player_id (int): Player's ID.
        image (UploadedFile or PIL.Image.Image or bytes): The image to save.

    Returns:
        str: Relative path to the saved avatar image.
    """
    avatars_dir = os.path.join("assets", "avatars")
    if not os.path.exists(avatars_dir):
        os.makedirs(avatars_dir)

    save_path = os.path.join(avatars_dir, f"{player_id}.png")  # Save as PNG

    if isinstance(image, Image.Image):
        image.save(save_path, format="PNG")
    elif hasattr(image, "getbuffer"):  # Streamlit UploadedFile
        with open(save_path, "wb") as f:
            f.write(image.getbuffer())
    elif isinstance(image, bytes):
        with open(save_path, "wb") as f:
            f.write(image)
    else:
        raise ValueError("Unsupported image type")

    # Normalize path for DB storage
    normalized_path = save_path.replace("\\", "/")

    # ✅ Update the DB
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE players SET avatar_path = ? WHERE id = ?", (normalized_path, player_id))
        conn.commit()
    finally:
        conn.close()

    return normalized_path
