# controllers/manage_matches_controller.py
from db import get_connection
from datetime import datetime, timedelta
from utils import execute_query, fetch_one, fetch_all
import streamlit as st
import sqlite3
def execute_query(query, params=()):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    conn.commit()
    cursor.close()
    conn.close()


def fetch_all(query, params=()):
    """
    Fetch all rows for SELECT query.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        results = cursor.fetchall()
        return results
    except sqlite3.Error as e:
        print("SQL Error:", e)
        raise e
    finally:
        cursor.close()
        conn.close()

def fetch_one(query, params=()):
    """
    Fetch a single row for SELECT query.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        result = cursor.fetchone()
        return result
    except sqlite3.Error as e:
        print("SQL Error:", e)
        raise e
    finally:
        cursor.close()
        conn.close()

def execute_read_query(query, params=()):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        columns = [column[0] for column in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        conn.close()
        return results
    except Exception as e:
        print(f"[ERROR] Failed to execute read query: {e}")
        return []

def get_all_leagues():
    return fetch_all("SELECT id, name FROM leagues")

def get_teams_by_league(league_id):
    query = """
    SELECT t.id, t.name
    FROM teams t
    JOIN team_league tl ON t.id = tl.team_id
    WHERE tl.league_id = ?
    """
    return fetch_all(query, (league_id,))


def get_round_by_date(match_date):
    return fetch_one(
        "SELECT id FROM rounds WHERE start_date <= ? AND end_date >= ?", 
        (match_date, match_date)
    )
    


def is_match_duplicate(round_id, home_team_id, away_team_id):
    return fetch_one("""
        SELECT id FROM matches 
        WHERE round_id = ? AND home_team_id = ? AND away_team_id = ?
    """, (round_id, home_team_id, away_team_id)) is not None

def add_match(round_id, league_id, home_team_id, away_team_id, match_datetime, stage_id):
    query_check = """
        SELECT id FROM matches
        WHERE round_id = ? AND home_team_id = ? AND away_team_id = ?
        LIMIT 1;
    """
    existing = fetch_one(query_check, (round_id, home_team_id, away_team_id))
    print("DEBUG: existing match check result:", existing)

    if existing:
        return False, "⚠️ Match already exists for this round."

    query_insert = """
        INSERT INTO matches (round_id, league_id, home_team_id, away_team_id, match_datetime, stage_id)
        VALUES (?, ?, ?, ?, ?, ?);
    """
    execute_query(query_insert, (round_id, league_id, home_team_id, away_team_id, match_datetime, stage_id))
    return True, "✅ Match added successfully."





def check_duplicate_match(round_id, home_team_id, away_team_id):
    query = """
    SELECT 1 FROM matches
    WHERE round_id = ?
      AND home_team_id = ?
      AND away_team_id = ?
    LIMIT 1;
    """
    result = fetch_one(query, (round_id, home_team_id, away_team_id))
    return result is not None  # True if duplicate found

def get_week_saturday_to_friday(date_str):
    """
    Given a date string 'YYYY-MM-DD', returns (start_date, end_date) of
    the round week: Saturday to next Friday.
    """
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")

    # Find last Saturday
    # weekday(): Monday=0 ... Sunday=6
    days_since_saturday = (date_obj.weekday() - 5) % 7  # Saturday=5
    start_date = date_obj - timedelta(days=days_since_saturday)

    # End date = start_date + 6 days (Friday)
    end_date = start_date + timedelta(days=6)

    return start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")

def get_round_id_by_date(match_date):
    """
    Returns round_id where match_date fits between start_date and end_date.
    If no such round exists, create one automatically with a sequential round name (Round 1, Round 2, ...).
    """
    print(f"Looking for round containing date: {match_date}")

    query_find = """
    SELECT id, start_date, end_date FROM rounds
    WHERE start_date <= ? AND end_date >= ?
    LIMIT 1;
    """
    row = fetch_one(query_find, (match_date, match_date))
    if row:
        round_id = row['id'] if isinstance(row, dict) else row[0]
        print(f"Found existing round with ID: {round_id}, start_date: {row['start_date'] if isinstance(row, dict) else row[1]}, end_date: {row['end_date'] if isinstance(row, dict) else row[2]}")
        return round_id

    print("No existing round found, creating a new one.")

    start_date, end_date = get_week_saturday_to_friday(match_date)
    print(f"Calculated start_date: {start_date}, end_date: {end_date}")

    # Find max round number
    query_max_round = """
    SELECT name FROM rounds
    ORDER BY id DESC
    LIMIT 1;
    """
    last_round = fetch_one(query_max_round)
    if last_round:
        last_name = last_round['name'] if isinstance(last_round, dict) else last_round[0]
        print(f"Last round name found: {last_name}")
        try:
            last_number = int(last_name.split(" ")[1])
        except (IndexError, ValueError):
            last_number = 0
        next_number = last_number + 1
    else:
        print("No rounds found in database, starting at Round 1")
        next_number = 1

    round_name = f"Round {next_number}"
    print(f"Creating new round named: {round_name}")

    query_insert = """
    INSERT INTO rounds (name, start_date, end_date)
    VALUES (?, ?, ?);
    """
    try:
        execute_query(query_insert, (round_name, start_date, end_date))
    except Exception as e:
        print(f"Exception while inserting round: {e}")
        raise

    # Fetch again the newly inserted round id
    row = fetch_one(query_find, (match_date, match_date))
    if row:
        round_id = row['id'] if isinstance(row, dict) else row[0]
        print(f"Created new round with ID: {round_id} named '{round_name}'")
        return round_id
    else:
        print("Failed to find the round after insert.")
        raise Exception("Failed to create or fetch the round")


def fetch_rounds():
    query = """
        SELECT id, name 
        FROM rounds 
        ORDER BY start_date ASC
    """
    return fetch_all(query)

def rename_round(round_id, new_name):
    query = "UPDATE rounds SET name = ? WHERE id = ?"
    execute_query(query, (new_name, round_id))

def reorganize_rounds_by_date():
    rounds = fetch_all("SELECT id, name, start_date FROM rounds")
    round_with_matches = []

    for rnd in rounds:
        matches = fetch_matches_by_round(rnd['id'])

        if matches:
            try:
                # Use round's own start_date for sorting
                start_date = datetime.strptime(rnd['start_date'], "%Y-%m-%d")
                round_with_matches.append({
                    "id": rnd["id"],
                    "old_name": rnd["name"],
                    "start_date": start_date
                })
            except Exception as e:
                print(f"⛔ Error parsing start_date in round {rnd['name']}: {e}")
        else:
            # No matches, safe to delete
            delete_round(rnd["id"])
            print(f"🗑️ Deleted empty round: {rnd['name']}")

    # Sort rounds by start_date and rename
    round_with_matches.sort(key=lambda r: r["start_date"])
    for idx, rnd in enumerate(round_with_matches, start=1):
        new_name = f"Round {idx}"
        rename_round(rnd["id"], new_name)
        print(f"🔄 Renamed '{rnd['old_name']}' ➜ '{new_name}'")

    st.success("✅ Rounds have been safely renamed and cleaned up.")



def fetch_matches_by_round(round_id):
    query = """
        SELECT
            m.id,
            m.match_datetime,
            m.status,
            m.home_score,
            m.away_score,
            m.penalty_winner,

            home.id AS home_team_id,
            home.name AS home_team_name,
            home.logo_path AS home_team_logo,

            away.id AS away_team_id,
            away.name AS away_team_name,
            away.logo_path AS away_team_logo,

            l.id AS league_id,
            l.name AS league_name,
            l.logo_path AS league_logo,

            m.round_id,
            m.stage_id,
            s.name AS stage_name  -- get stage name

        FROM matches m
        JOIN teams home ON m.home_team_id = home.id
        JOIN teams away ON m.away_team_id = away.id
        JOIN leagues l ON m.league_id = l.id
        JOIN stages s ON m.stage_id = s.id  -- join stages table
        WHERE m.round_id = ?
        ORDER BY l.name ASC, m.match_datetime ASC
    """
    return fetch_all(query, (round_id,))



def delete_match_by_id(match_id):
    query = """
        DELETE FROM matches 
        WHERE id = ?
    """
    execute_query(query, (match_id,))
    
def delete_round(round_id):
    query = """
        DELETE FROM rounds 
        WHERE id = ?
    """
    execute_query(query, (round_id,))
    
def update_match_partial(match_id, match_datetime, status, home_score, away_score, penalty_winner=None):
    query = """
        UPDATE matches
        SET 
            match_datetime = ?,
            status = ?,
            home_score = ?,
            away_score = ?,
            penalty_winner = ?
        WHERE id = ?
    """
    params = (match_datetime, status, home_score, away_score, penalty_winner, match_id)
    execute_query(query, params)

def fetch_leagues():
    query = """
        SELECT id, name, logo_path
        FROM leagues
    """
    return fetch_all(query)



def fetch_teams():
    query = "SELECT id, name, logo_path FROM teams"
    return fetch_all(query)

def update_match_status(match_id, new_status):
    query = "UPDATE matches SET status = ? WHERE id = ?"
    execute_query(query, (new_status, match_id))


def change_match_status(match):
    match_time = datetime.fromisoformat(match['match_datetime'])
    now = datetime.now()

    if match['status'] == 'upcoming' and now >= match_time:
        update_match_status(match['id'], 'live')
        #match['status'] = 'live'  # reflect change in UI immediately

    elif match['status'] == 'live' and now >= match_time + timedelta(hours=3):
        update_match_status(match['id'], 'finished')
        #match['status'] = 'finished'  # reflect change in UI immediately
        
def fetch_legs_by_match_id(match_id):
    query = "SELECT * FROM legs WHERE match_id = ?"
    return execute_read_query(query, (match_id,))

def insert_or_replace_leg(match_id, leg_number, leg_date, home_score, away_score, can_draw, winner_team_id, notes):
    query = """
    INSERT OR REPLACE INTO legs (
        match_id, leg_number, leg_date,
        home_score, away_score,
        can_draw, winner_team_id, notes
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """
    params = (
        match_id, leg_number, leg_date,
        home_score, away_score, can_draw,
        winner_team_id, notes
    )
    execute_query(query, params)


def fetch_stage_by_id(stage_id):
    if stage_id is None:
        return None  # Avoid querying with None
    
    query = """
        SELECT id, name, must_have_winner, two_legs, can_be_draw
        FROM stages
        WHERE id = ?
        LIMIT 1;
    """
    result = fetch_one(query, (stage_id,))
    return result

def fetch_match_by_id(match_id):
    query = """
        SELECT *
        FROM matches
        WHERE id = ?
    """
    return fetch_one(query, (match_id,))

def fetch_team_by_id(team_id):
    query = """
        SELECT *
        FROM teams
        WHERE id = ?
    """
    return fetch_one(query, (team_id,))


def handle_two_leg_match_info(match_id):
    # Fetch two-leg tie data
    query = """
        SELECT first_leg_match_id, second_leg_match_id
        FROM two_legged_ties
        WHERE first_leg_match_id = ? OR second_leg_match_id = ?
    """
    result = fetch_one(query, (match_id, match_id))

    if not result:
        st.warning("⚠️ This match is marked as two-leg, but no tie data found.")
        return

    first_leg_id = result['first_leg_match_id']
    second_leg_id = result['second_leg_match_id']

    # Case: Current match is the first leg
    if match_id == first_leg_id:
        st.info("🕹️ This is the **First Leg** of a two-leg tie. Result will influence the second leg.")
    
    # Case: Current match is the second leg
    elif match_id == second_leg_id:
        first_leg = fetch_match_by_id(first_leg_id)

        if first_leg:
            home_team = fetch_team_by_id(first_leg['home_team_id'])['name']
            away_team = fetch_team_by_id(first_leg['away_team_id'])['name']
            home_score = first_leg['home_score']
            away_score = first_leg['away_score']

            st.markdown(
                f"""
                🧮 **Second Leg Match**
                <br>📊 First leg result: <span style='color:blue; font-weight:bold;'>{home_team} {home_score} - {away_score} {away_team}</span>
                """,
                unsafe_allow_html=True
            )
            return int(home_score), int(away_score)
        else:
            st.warning("⚠️ Unable to retrieve first leg match details.")
            return None, None