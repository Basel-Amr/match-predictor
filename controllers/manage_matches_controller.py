# controllers/manage_matches_controller.py
from db import get_connection
from datetime import datetime, timedelta

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

def add_match(round_id, league_id, home_team_id, away_team_id, match_datetime):
    query_check = """
        SELECT id FROM matches
        WHERE round_id = ? AND home_team_id = ? AND away_team_id = ?
        LIMIT 1;
    """
    existing = fetch_one(query_check, (round_id, home_team_id, away_team_id))
    print("DEBUG: existing match check result:", existing)  # debug

    if existing:
        return False, "⚠️ Match already exists for this round."

    query_insert = """
        INSERT INTO matches (round_id, league_id, home_team_id, away_team_id, match_datetime)
        VALUES (?, ?, ?, ?, ?);
    """
    execute_query(query_insert, (round_id, league_id, home_team_id, away_team_id, match_datetime))
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
