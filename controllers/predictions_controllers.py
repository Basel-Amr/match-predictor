from datetime import datetime, timedelta
import pytz  # if you're using timezone-aware times
import streamlit as st
import sqlite3
from utils import fetch_one, execute_query, fetch_all
from db import get_connection

# Functions resposilbe for deadline
def get_next_round_info():
    now = datetime.now()

    # Step 1: Get next round by comparing today with start_date
    round_row = fetch_one("""
        SELECT * FROM rounds
        WHERE start_date > ?
        ORDER BY start_date ASC
        LIMIT 1
    """, (now.isoformat(),))

    if not round_row:
        return None, None, None, None

    round_id = round_row["id"]
    round_name = round_row["name"]

    # Step 2: Get first match in the round
    match = fetch_one("""
        SELECT * FROM matches
        WHERE round_id = ?
        ORDER BY match_datetime ASC
        LIMIT 1
    """, (round_id,))

    if not match:
        return round_name, None, None, 0

    match_time = datetime.fromisoformat(match["match_datetime"])
    deadline = match_time - timedelta(hours=2)

    # Step 3: Count number of matches in the round
    match_count = fetch_one("""
        SELECT COUNT(*) as total_matches
        FROM matches
        WHERE round_id = ?
    """, (round_id,))["total_matches"]

    return round_name, deadline, match_time, match_count

def format_time_left(deadline):
    now = datetime.now()
    time_diff = deadline - now

    if time_diff.total_seconds() <= 0:
        return "Deadline passed!", "❌"

    if time_diff.total_seconds() < 3600:  # less than 1 hour
        minutes = int(time_diff.total_seconds() // 60)
        return f"{minutes} minute(s) left", "⏳"
    elif time_diff.total_seconds() < 36000:  # less than 10 hours
        hours = round(time_diff.total_seconds() / 3600, 1)
        return f"{hours} hour(s) left", "⏰"
    else:
        days = round(time_diff.total_seconds() / (3600 * 24), 1)
        return f"{days} day(s) left", "📅"

def get_predicted_match_count(round_name, player_id):
    # Step 1: Get round_id from round name
    round_query = "SELECT id FROM rounds WHERE name = ?"
    round_result = fetch_one(round_query, (round_name,))
    if not round_result:
        return 0  # Round not found

    round_id = round_result[0]

    # Step 2: Get all match_ids from this round
    match_ids_query = "SELECT id FROM matches WHERE round_id = ?"
    match_ids_result = fetch_all(match_ids_query, (round_id,))
    if not match_ids_result:
        return 0  # No matches in this round

    match_ids = [row[0] for row in match_ids_result]

    # Step 3: Count predictions made by this player for matches in this round
    placeholders = ','.join('?' for _ in match_ids)
    prediction_query = f"""
        SELECT COUNT(*) FROM predictions 
        WHERE player_id = ? AND match_id IN ({placeholders})
    """
    prediction_result = fetch_one(prediction_query, (player_id, *match_ids))
    return prediction_result[0] if prediction_result else 0


# functions responsible for fetching matches and rounds
def get_all_rounds():
    query = "SELECT id, name FROM rounds ORDER BY start_date ASC"
    return fetch_all(query)

def get_round_id_by_name(round_name):
    return fetch_one("SELECT id FROM rounds WHERE name = ?", (round_name,))[0]

def get_matches_by_round(round_id):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT matches.*,
               home_team.name AS home_team_name,
               away_team.name AS away_team_name,
               leagues.name AS league_name,
               stages.name AS stage_name
        FROM matches
        JOIN teams AS home_team ON matches.home_team_id = home_team.id
        JOIN teams AS away_team ON matches.away_team_id = away_team.id
        JOIN leagues ON matches.league_id = leagues.id
        LEFT JOIN stages ON matches.stage_id = stages.id
        WHERE matches.round_id = ?
        ORDER BY leagues.name ASC, match_datetime ASC
        """, (round_id,)
    )

    rows = cursor.fetchall()
    columns = [col[0] for col in cursor.description]

    conn.close()
    return [dict(zip(columns, row)) for row in rows]





def get_team_info(team_id):
    return fetch_one("SELECT name, logo_path FROM teams WHERE id = ?", (team_id,))

def get_user_prediction(player_id, match_id):
    query = """
        SELECT predicted_home_score, predicted_away_score, score
        FROM predictions
        WHERE player_id = ? AND match_id = ?
    """
    return fetch_one(query, (player_id, match_id))

def format_time_left_detailed(match_datetime_str):
    match_datetime = datetime.strptime(match_datetime_str, "%Y-%m-%d %H:%M:%S")
    now = datetime.now()
    delta = match_datetime - now

    days = delta.days
    seconds = delta.total_seconds()

    if seconds < 0:
        return f"📅 {match_datetime.strftime('%b %d, %Y')}"  # Match has passed

    if days == 0:
        if delta < timedelta(minutes=1):
            return f"⏱️ {int(seconds)} seconds left"
        elif delta < timedelta(hours=1):
            minutes = int(seconds // 60)
            return f"🟣 {minutes} minutes left"
        elif delta < timedelta(hours=10):
            hours = int(seconds // 3600)
            return f"🔵 {hours} hours left"
        else:
            return "🟢 Today"
    elif days == 1:
        return "🟡 Tomorrow"
    else:
        return f"📅 {match_datetime.strftime('%b %d, %Y')}"  # Show full date
    
def get_score_color(score):
    if score == 4:
        return "#27ae60"  # green
    elif score == 3:
        return "#2ecc71"
    elif score == 2:
        return "#f39c12"
    elif score == 1:
        return "#e67e22"
    else:
        return "#c0392b"
    
def get_match_timing_display(match_datetime_str, status):
    """
    Format the match timing and status display.

    Args:
        match_datetime_str (str): ISO format datetime string (e.g., '2025-06-08T16:00:00').
        status (str): Match status: 'upcoming', 'live', 'finished', 'cancelled'.

    Returns:
        dict: {
            'time': '16:00',
            'date': '08 Jun 2025',
            'time_left': '🟢 Today' or '⌛ 3h 20m left' or '✅ Finished'
        }
    """
    try:
        # Support ISO format with 'T'
        match_dt = datetime.fromisoformat(match_datetime_str)
    except ValueError:
        return {
            "time": "-",
            "date": "Invalid date",
            "time_left": "❓ Unknown time"
        }

    now = datetime.now()
    time_str = match_dt.strftime("%H:%M")
    date_str = match_dt.strftime("%d %b %Y")

    if status == "finished":
        time_left = "✅ Finished"
    elif status == "cancelled":
        time_left = "❌ Cancelled"
    elif status == "live":
        time_left = "📺 Live Now"
    elif match_dt < now:
        time_left = "⚠️ Match Started"
    else:
        delta = match_dt - now
        if delta < timedelta(minutes=1):
            time_left = "⏱️ Less than a minute"
        elif delta < timedelta(hours=1):
            minutes = int(delta.total_seconds() // 60)
            time_left = f"⏱️ {minutes} min left"
        elif delta < timedelta(hours=10):
            hours = int(delta.total_seconds() // 3600)
            mins = int((delta.total_seconds() % 3600) // 60)
            time_left = f"⌛ {hours}h {mins}m left"
        elif match_dt.date() == now.date():
            time_left = "🟢 Today"
        elif match_dt.date() == (now + timedelta(days=1)).date():
            time_left = "🕒 Tomorrow"
        else:
            time_left = f"📅 {date_str}"

    return {
        "time": time_str,
        "date": date_str,
        "time_left": time_left
    }
    
import sqlite3

def get_player_name(player_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT username FROM players WHERE id = ?", (player_id,))
    result = cursor.fetchone()

    conn.close()

    if result:
        return result[0]
    return "Unknown Player"

def get_prediction_deadline_for_round(round_id):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT MIN(match_datetime)
        FROM matches
        WHERE round_id = ?
    """, (round_id,))
    
    result = cursor.fetchone()
    conn.close()

    if result and result[0]:
        earliest_match_dt = datetime.fromisoformat(result[0])
        deadline = earliest_match_dt - timedelta(hours=2)
        return deadline
    else:
        return None