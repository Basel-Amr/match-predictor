import os
from typing import List, Dict
from db import get_connection
import sqlite3
from controllers.manage_leagues_controller import (
    save_uploaded_file,get_leagues,add_league, 
    update_league, delete_league
    )


LOGO_DIR = "assets/teams"
os.makedirs(LOGO_DIR, exist_ok=True)

def save_uploaded_file(uploaded_file, upload_folder=LOGO_DIR):
    if uploaded_file is None:
        return None

    os.makedirs(upload_folder, exist_ok=True)
    file_path = os.path.join(upload_folder, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.read())

    # Fix path: convert backslashes to slashes and add 'assets/' prefix
    relative_path = os.path.relpath(file_path, start="assets")
    normalized_path = f"assets/{relative_path.replace(os.sep, '/')}"
    return normalized_path



def execute_query(query, params=(), fetch_all=False, commit=False, return_lastrowid=False):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(query, params)

    result = None
    if fetch_all:
        result = [dict(row) for row in cursor.fetchall()]
    elif cursor.description is not None:
        fetched = cursor.fetchone()
        result = dict(fetched) if fetched else None

    if commit:
        conn.commit()

    if return_lastrowid:
        result = cursor.lastrowid

    cursor.close()
    conn.close()
    return result


def get_leagues_map():
    leagues = get_leagues()
    return {l['id']: l['name'] for l in leagues}


def get_teams():
    query = """
    SELECT 
        t.id, 
        t.name, 
        t.logo_path,
        t.nationality,
        GROUP_CONCAT(l.name, ', ') AS leagues
    FROM teams t
    JOIN team_league tl ON t.id = tl.team_id
    JOIN leagues l ON tl.league_id = l.id
    GROUP BY t.id
    """
    return execute_query(query, fetch_all=True)


def add_team(name, league_ids, logo_file, nationality="Europe"):
    if not league_ids:
        raise ValueError("At least one league must be selected")

    logo_path = save_uploaded_file(logo_file) if logo_file else None
    primary_league_id = league_ids[0]

    query = """
        INSERT INTO teams (name, logo_path, league_id, nationality)
        VALUES (?, ?, ?, ?)
    """
    team_id = execute_query(query, (name, logo_path, primary_league_id, nationality), commit=True, return_lastrowid=True)

    for league_id in league_ids:
        execute_query(
            "INSERT INTO team_league (team_id, league_id) VALUES (?, ?)",
            (team_id, league_id),
            commit=True
        )

    return team_id


def get_team_logo_path(team_id):
    result = execute_query("SELECT logo_path FROM teams WHERE id = ?", (team_id,), fetch_all=False)
    return result.get('logo_path') if result else None

def update_team(team_id, name, league_ids, logo_file=None, nationality="Europe"):
    logo_path = save_uploaded_file(logo_file) if logo_file else get_team_logo_path(team_id)

    query = "UPDATE teams SET name = ?, logo_path = ?, nationality = ? WHERE id = ?"
    execute_query(query, (name, logo_path, nationality, team_id), commit=True)

    execute_query("DELETE FROM team_league WHERE team_id = ?", (team_id,), commit=True)

    for league_id in league_ids:
        execute_query("INSERT INTO team_league (team_id, league_id) VALUES (?, ?)", (team_id, league_id), commit=True)



def delete_team(team_id: int) -> bool:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM teams WHERE id = ?", (team_id,))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"[delete_team error] {e}")
        return False
    finally:
        conn.close()

def get_team_by_id(team_id, conn):
    # Get basic team info
    team_data = conn.execute("SELECT id, name, logo_path, nationality FROM teams WHERE id=?", (team_id,)).fetchone()
    if not team_data:
        return None
    
    # Get league_ids from the team_league table (many-to-many)
    league_ids = [row[0] for row in conn.execute("SELECT league_id FROM team_league WHERE team_id=?", (team_id,)).fetchall()]

    return {
        "id": team_data[0],
        "name": team_data[1],
        "logo_path": team_data[2],
        "nationality": team_data[3],
        "league_ids": league_ids,
    }
