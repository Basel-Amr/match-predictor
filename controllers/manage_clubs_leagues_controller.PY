import os
import sqlite3
from uuid import uuid4
from typing import Optional, Tuple, List, Dict, Any
from PIL import Image
from db import get_connection

# -------------------------------
# 📁 Setup: Constants
# -------------------------------
LOGO_DIR = "assets/leagues"
TEAM_LOGO_DIR = "assets/clubs"
os.makedirs(TEAM_LOGO_DIR, exist_ok=True)

def save_uploaded_file(uploaded_file, upload_folder=LOGO_DIR):
    if uploaded_file is None:
        return None
    # Make sure upload folder exists
    os.makedirs(upload_folder, exist_ok=True)
    # Create a unique file name or use original filename
    file_path = os.path.join(upload_folder, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.read())
    return file_path

# -------------------------------
# 🔧 Helper Function: Save Logo
# -------------------------------
def save_logo(file):
    try:
        if not file:
            return None
        file_extension = os.path.splitext(file.name)[1]
        filename = f"{uuid.uuid4()}{file_extension}"
        path = os.path.join(TEAM_LOGO_DIR, filename)
        with open(path, "wb") as f:
            f.write(file.read())
        return path
    except Exception as e:
        print("[save_logo error]", e)
        return None



# -------------------------------
# ✅ TEAM CRUD FUNCTIONS
# -------------------------------

def add_team(name: str, league_ids: List[int], logo_file=None) -> Tuple[bool, str]:
    try:
        conn = get_connection()
        cursor = conn.cursor()

        logo_path = save_logo(logo_file) if logo_file else None

        # Insert into teams table
        cursor.execute("""
            INSERT INTO teams (name, logo_path)
            VALUES (?, ?)
        """, (name, logo_path))

        team_id = cursor.lastrowid  # Get the auto-incremented team ID

        # Insert into team_league mapping table
        for league_id in league_ids:
            cursor.execute("""
                INSERT INTO team_league (team_id, league_id)
                VALUES (?, ?)
            """, (team_id, league_id))

        conn.commit()
        return True, "✅ Team added successfully."
    except sqlite3.IntegrityError:
        return False, "❌ Team name already exists."
    except Exception as e:
        return False, f"❌ Error adding team: {e}"
    finally:
        conn.close()



def update_team(team_id: int, name: Optional[str] = None,
                league_id: Optional[int] = None,
                logo_file=None) -> Tuple[bool, str]:
    """
    Update an existing team's name, league, or logo.

    Args:
        team_id (int): ID of the team to update.
        name (str, optional): New name.
        league_id (int, optional): New league ID.
        logo_file (optional): New logo file.

    Returns:
        Tuple[bool, str]: Operation status and message.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        fields = []
        values = []

        if name:
            fields.append("name = ?")
            values.append(name)
        if league_id:
            fields.append("league_id = ?")
            values.append(league_id)
        if logo_file:
            logo_path = save_logo(logo_file)
            if logo_path:
                fields.append("logo_path = ?")
                values.append(logo_path)

        if not fields:
            return False, "⚠️ No fields to update."

        values.append(team_id)
        query = f"UPDATE teams SET {', '.join(fields)} WHERE id = ?"
        cursor.execute(query, values)

        conn.commit()
        return True, "✅ Team updated successfully."
    except Exception as e:
        return False, f"❌ Error updating team: {e}"
    finally:
        conn.close()


def delete_team(team_id: int) -> Tuple[bool, str]:
    """
    Delete a team by its ID.

    Args:
        team_id (int): ID of the team to delete.

    Returns:
        Tuple[bool, str]: Operation status and message.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM teams WHERE id = ?", (team_id,))
        conn.commit()

        if cursor.rowcount == 0:
            return False, "⚠️ Team not found."
        return True, "🗑️ Team deleted successfully."
    except Exception as e:
        return False, f"❌ Error deleting team: {e}"
    finally:
        conn.close()


def get_teams(search: str = "") -> List[Dict[str, Any]]:
    """
    Retrieve all teams, optionally filtered by name.

    Args:
        search (str): Optional search string.

    Returns:
        List of teams with league info.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        query = """
            SELECT t.id, t.name, t.logo_path, l.name AS league_name
            FROM teams t
            JOIN leagues l ON t.league_id = l.id
        """
        params = ()
        if search:
            query += " WHERE t.name LIKE ?"
            params = (f"%{search}%",)

        cursor.execute(query, params)
        rows = cursor.fetchall()

        return [
            {
                "id": row[0],
                "name": row[1],
                "logo_path": row[2],
                "league_name": row[3]
            }
            for row in rows
        ]
    except Exception as e:
        print(f"[get_teams error] {e}")
        return []
    finally:
        conn.close()


def get_team_by_id(team_id: int) -> Optional[Dict[str, Any]]:
    """
    Retrieve a single team by ID.

    Args:
        team_id (int): Team ID.

    Returns:
        Dictionary of team details or None.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, name, logo_path, league_id
            FROM teams WHERE id = ?
        """, (team_id,))
        row = cursor.fetchone()

        if row:
            return {
                "id": row[0],
                "name": row[1],
                "logo_path": row[2],
                "league_id": row[3]
            }
        return None
    except Exception as e:
        print(f"[get_team_by_id error] {e}")
        return None
    finally:
        conn.close()


# -------------------------------
# ✅ TEAM_LEAGUE MAPPING FUNCTIONS
# -------------------------------

def assign_team_to_league(team_id: int, league_id: int) -> Tuple[bool, str]:
    """
    Assign a team to a league (many-to-many).

    Args:
        team_id (int): Team ID.
        league_id (int): League ID.

    Returns:
        Tuple[bool, str]: Status and message.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR IGNORE INTO team_league (team_id, league_id)
            VALUES (?, ?)
        """, (team_id, league_id))

        conn.commit()
        return True, "✅ Team assigned to league."
    except Exception as e:
        return False, f"❌ Error assigning team to league: {e}"
    finally:
        conn.close()


def get_team_leagues(team_id: int) -> List[Dict[str, Any]]:
    """
    Get all leagues a team is assigned to.

    Args:
        team_id (int): Team ID.

    Returns:
        List of leagues.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT l.id, l.name
            FROM team_league tl
            JOIN leagues l ON tl.league_id = l.id
            WHERE tl.team_id = ?
        """, (team_id,))
        rows = cursor.fetchall()

        return [{"id": row[0], "name": row[1]} for row in rows]
    except Exception as e:
        print(f"[get_team_leagues error] {e}")
        return []
    finally:
        conn.close()


def remove_team_from_league(team_id: int, league_id: int) -> Tuple[bool, str]:
    """
    Remove a team from a league.

    Args:
        team_id (int): Team ID.
        league_id (int): League ID.

    Returns:
        Tuple[bool, str]: Status and message.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM team_league
            WHERE team_id = ? AND league_id = ?
        """, (team_id, league_id))

        conn.commit()
        if cursor.rowcount == 0:
            return False, "⚠️ Mapping not found."
        return True, "🗑️ Team removed from league."
    except Exception as e:
        return False, f"❌ Error removing team from league: {e}"
    finally:
        conn.close()

def get_leagues(search_query=""):
    conn = get_connection()
    cursor = conn.cursor()
    if search_query:
        cursor.execute("SELECT id, name, country, logo_path, can_be_draw, two_legs, must_have_winner FROM leagues WHERE name LIKE ?", (f"%{search_query}%",))
    else:
        cursor.execute("SELECT id, name, country, logo_path, can_be_draw, two_legs, must_have_winner FROM leagues")
    rows = cursor.fetchall()
    conn.close()
    leagues = []
    for row in rows:
        leagues.append({
            "id": row[0],
            "name": row[1],
            "country": row[2],
            "logo_path": row[3],
            "can_be_draw": bool(row[4]),
            "two_legs": bool(row[5]),
            "must_have_winner": bool(row[6])
        })
    return leagues


def add_league(name, country, logo, can_be_draw, two_legs, must_have_winner, upload_folder='static/uploads'):
    """
    Adds a new league to the database.
    
    Parameters:
    - name: str - league name
    - country: str - league country
    - logo: UploadedFile or str or None - uploaded file object or existing path
    - can_be_draw: bool
    - two_legs: bool
    - must_have_winner: bool
    - upload_folder: str - directory to save uploaded logos
    
    Returns: None
    """

    # Save uploaded logo file and get the path string
    logo_path = None
    if logo:
        # If logo is a file object (e.g. UploadedFile), save it to disk
        if hasattr(logo, 'read'):
            os.makedirs(upload_folder, exist_ok=True)
            file_path = os.path.join(upload_folder, logo.name)
            with open(file_path, "wb") as f:
                f.write(logo.read())
            logo_path = file_path
        else:
            # If logo is already a path string (no upload), just use it
            logo_path = logo

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO leagues (name, country, logo_path, can_be_draw, two_legs, must_have_winner) VALUES (?, ?, ?, ?, ?, ?)",
        (name, country, logo_path, int(can_be_draw), int(two_legs), int(must_have_winner))
    )
    conn.commit()
    conn.close()


def update_league(league_id, name, country, logo, can_be_draw, two_legs, must_have_winner):
    # Assuming you have a folder for logos
    conn = get_connection()
    cursor = conn.cursor()
    logo_path = None
    if logo is not None:
        # Save the file to disk, e.g., logos/league_<id>.png
        ext = os.path.splitext(logo.name)[1]  # e.g., ".png"
        logo_filename = f"league_{league_id}{ext}"
        logo_folder = "logos"
        os.makedirs(logo_folder, exist_ok=True)
        full_path = os.path.join(logo_folder, logo_filename)

        # Save the uploaded file's bytes to disk
        with open(full_path, "wb") as f:
            f.write(logo.getbuffer())

        logo_path = full_path  # This is the path string to store in DB

    # If logo is None, maybe keep the old logo_path or set to NULL
    # Retrieve existing logo_path if needed or handle accordingly

    cursor.execute(
        "UPDATE leagues SET name = ?, country = ?, logo_path = ?, can_be_draw = ?, two_legs = ?, must_have_winner = ? WHERE id = ?",
        (name, country, logo_path, int(can_be_draw), int(two_legs), int(must_have_winner), league_id)
    )
    conn.commit()


def delete_league(league_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM leagues WHERE id = ?", (league_id,))
    conn.commit()
    conn.close()    