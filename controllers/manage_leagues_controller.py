import os
from typing import List, Dict
from db import get_connection

LOGO_DIR = "assets/leagues"
os.makedirs(LOGO_DIR, exist_ok=True)

def save_uploaded_file(uploaded_file, upload_folder=LOGO_DIR):
    if uploaded_file is None:
        return None
    os.makedirs(upload_folder, exist_ok=True)
    file_path = os.path.join(upload_folder, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.read())
    return file_path

def get_leagues(search_query="") -> List[Dict]:
    conn = get_connection()
    cursor = conn.cursor()
    if search_query:
        cursor.execute("SELECT id, name, country, logo_path FROM leagues WHERE name LIKE ?", (f"%{search_query}%",))
    else:
        cursor.execute("SELECT id, name, country, logo_path FROM leagues")
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "id": row[0],
            "name": row[1],
            "country": row[2],
            "logo_path": row[3]
        } for row in rows
    ]

def add_league(name, country, logo):
    logo_path = None
    if logo:
        if hasattr(logo, 'read'):
            os.makedirs(LOGO_DIR, exist_ok=True)
            file_path = os.path.join(LOGO_DIR, logo.name)
            with open(file_path, "wb") as f:
                f.write(logo.read())
            logo_path = file_path
        else:
            logo_path = logo

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO leagues (name, country, logo_path) VALUES (?, ?, ?)",
        (name, country, logo_path)
    )
    conn.commit()
    conn.close()

def update_league(league_id, name, country, logo):
    conn = get_connection()
    cursor = conn.cursor()

    logo_path = None
    if logo:
        if hasattr(logo, 'read'):
            os.makedirs(LOGO_DIR, exist_ok=True)
            file_path = os.path.join(LOGO_DIR, logo.name)
            with open(file_path, "wb") as f:
                f.write(logo.read())
            logo_path = file_path
        else:
            logo_path = logo

    update_fields = ["name = ?", "country = ?"]
    values = [name, country]

    if logo_path:
        update_fields.append("logo_path = ?")
        values.append(logo_path)

    values.append(league_id)
    query = f"UPDATE leagues SET {', '.join(update_fields)} WHERE id = ?"
    cursor.execute(query, values)
    conn.commit()
    conn.close()

def delete_league(league_id: int) -> bool:
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM leagues WHERE id = ?", (league_id,))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"[delete_league error] {e}")
        return False
    finally:
        conn.close()


# --- Stage Controller ---

def get_stages_by_league(league_id: int) -> List[Dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, name, stage_order, can_be_draw, two_legs, must_have_winner 
        FROM stages 
        WHERE league_id = ? 
        ORDER BY stage_order ASC
    """, (league_id,))
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "id": row[0],
            "name": row[1],
            "stage_order": row[2],
            "can_be_draw": bool(row[3]),
            "two_legs": bool(row[4]),
            "must_have_winner": bool(row[5])
        } for row in rows
    ]

def add_stage(league_id, name, stage_order, can_be_draw, two_legs, must_have_winner):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO stages (league_id, name, stage_order, can_be_draw, two_legs, must_have_winner)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (league_id, name, stage_order, int(can_be_draw), int(two_legs), int(must_have_winner)))
    conn.commit()
    conn.close()

def update_stage(stage_id, name, stage_order, can_be_draw, two_legs, must_have_winner):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE stages 
        SET name = ?, stage_order = ?, can_be_draw = ?, two_legs = ?, must_have_winner = ?
        WHERE id = ?
    """, (name, stage_order, int(can_be_draw), int(two_legs), int(must_have_winner), stage_id))
    conn.commit()
    conn.close()

def delete_stage(stage_id: int) -> bool:
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM stages WHERE id = ?", (stage_id,))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"[delete_stage error] {e}")
        return False
    finally:
        conn.close()
