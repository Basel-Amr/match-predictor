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
    # Store relative path for portability
    return os.path.relpath(file_path, start="assets")

def execute_query(query, params=(), fetch_all=False, commit=False, return_lastrowid=False):
    conn = get_connection()
    conn.row_factory = sqlite3.Row  # lets you fetch rows as dicts
    cursor = conn.cursor()
    cursor.execute(query, params)

    result = None
    if fetch_all:
        result = [dict(row) for row in cursor.fetchall()]
    elif fetch_all is False and cursor.description is not None:
        result = dict(cursor.fetchone()) if cursor.fetchone() else None

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
        GROUP_CONCAT(l.name, ', ') AS leagues
    FROM teams t
    JOIN team_league tl ON t.id = tl.team_id
    JOIN leagues l ON tl.league_id = l.id
    GROUP BY t.id
    """
    return execute_query(query, fetch_all=True)




def add_team(name, league_ids, logo_path):
    if not league_ids:
        raise ValueError("At least one league must be selected")

    primary_league_id = league_ids[0]  # Use the first league ID for the teams table

    # Insert into teams table with one league_id
    query = "INSERT INTO teams (name, logo_path, league_id) VALUES (?, ?, ?)"
    team_id = execute_query(query, (name, logo_path, primary_league_id), commit=True, return_lastrowid=True)

    # Insert all selected leagues into team_leagues
    for league_id in league_ids:
        execute_query(
            "INSERT INTO team_league (team_id, league_id) VALUES (?, ?)",
            (team_id, league_id),
            commit=True
        )

    return team_id




def update_team(team_id, name, league_ids, logo=None):
    query = "UPDATE teams SET name = ?, logo_path = ? WHERE id = ?"
    execute_query(query, (name, logo, team_id), commit=True)

    # Delete existing associations
    execute_query("DELETE FROM team_league WHERE team_id = ?", (team_id,), commit=True)

    # Add new ones
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
