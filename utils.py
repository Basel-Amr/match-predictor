# utils.py
import hashlib
import bcrypt
import streamlit as st
from db import get_connection

def hash_password(password: str) -> bytes:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt())

def verify_password(password, hashed):
    if isinstance(hashed, str):
        hashed = hashed.encode('utf-8')
    return bcrypt.checkpw(password.encode('utf-8'), hashed)


def execute_query(query: str, params: tuple = ()):

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(query, params)
    conn.commit()
    return cur

def fetch_one(query: str, params: tuple = ()):
    cur = execute_query(query, params)
    return cur.fetchone()

def fetch_all(query: str, params: tuple = ()):
    cur = execute_query(query, params)
    return cur.fetchall()

def get_team_id_by_name(teams, team_name):
    return next((team['id'] for team in teams if team['name'] == team_name), None)

from controllers.manage_matches_controller import (get_all_leagues, get_teams_by_league, add_match, check_duplicate_match, 
                                                   get_round_id_by_date, reorganize_rounds_by_date)

def add_pending_match(league_id, stage_id, home_team, away_team, full_datetime, teams):
    home_team_id = get_team_id_by_name(teams, home_team)
    away_team_id = get_team_id_by_name(teams, away_team)

    if home_team_id is None or away_team_id is None:
        st.error("Team ID resolution failed.")
        return False

    st.session_state.pending_matches.append({
        "league_id": league_id,
        "stage_id": stage_id,
        "home_team_id": home_team_id,
        "away_team_id": away_team_id,
        "home_team": home_team,
        "away_team": away_team,
        "datetime": full_datetime
    })
    st.success(f"Match added: {home_team} vs {away_team} on {full_datetime}")
    return True


def display_pending_matches():
    st.markdown("### 📝 Pending Matches to Add")
    for i, match in enumerate(st.session_state.pending_matches):
        st.write(f"{i+1}. {match['home_team']} vs {match['away_team']} | {match['datetime']}")


def save_pending_matches():
    success = True
    for match in st.session_state.pending_matches:
        round_id = get_round_id_by_date(match["datetime"].split(" ")[0])
        if not round_id:
            st.error(f"❌ No round found for date: {match['datetime']}")
            success = False
            continue

        if check_duplicate_match(round_id, match["home_team"], match["away_team"]):
            st.warning(f"⚠️ Match {match['home_team']} vs {match['away_team']} already exists.")
            continue

        result = add_match(
            round_id, match["league_id"], match["home_team_id"],
            match["away_team_id"], match["datetime"], match["stage_id"]
        )
        if not result:
            success = False
    return success


def clear_match_list():
    st.session_state.pending_matches.clear()
    st.info("Match list cleared.")
    
######################################## Add Match two legs #########################
    
def select_league(leagues):
    league_names = [league['name'] for league in leagues]
    league_name = st.selectbox("Select League", ["-- Select League --"] + league_names)

    if league_name == "-- Select League --":
        st.warning("Please select a league to start.")
        return None, None

    league_id = next((league['id'] for league in leagues if league['name'] == league_name), None)
    if league_id is None:
        st.error("Selected league not found.")
    return league_id, league_name


def select_stage(stages):
    stage_names = [stage['name'] for stage in stages]
    stage_name = st.selectbox("Select Stage", ["-- Select Stage --"] + stage_names)

    if stage_name == "-- Select Stage --":
        st.warning("Please select a stage to continue.")
        return None, None, None

    selected_stage = next((stage for stage in stages if stage['name'] == stage_name), None)

    if selected_stage:
        return selected_stage['id'], selected_stage['name'], selected_stage.get('two_legs', 0)

    return None, None, None

def insert_two_legged_tie(first_leg_id, second_leg_id):
    query = """
    INSERT OR IGNORE INTO two_legged_ties (first_leg_match_id, second_leg_match_id)
    VALUES (?, ?)
    """
    execute_query(query, (first_leg_id, second_leg_id))

def add_match(round_id, league_id, home_team_id, away_team_id, match_datetime, stage_id):
    query = """
    INSERT INTO matches (round_id, league_id, home_team_id, away_team_id, match_datetime, stage_id)
    VALUES (?, ?, ?, ?, ?, ?)
    """
    params = (round_id, league_id, home_team_id, away_team_id, match_datetime, stage_id)
    try:
        cur = execute_query(query, params)
        return cur.lastrowid  # ✅ Return match ID directly
    except Exception as e:
        print("Error adding match:", e)
        return None



def select_teams(teams):
    team_names = [team['name'] for team in teams]
    home_team = st.selectbox("Select Home Team", ["-- Select Home Team --"] + team_names)
    away_team = st.selectbox("Select Away Team", ["-- Select Away Team --"] + team_names)
    return home_team, away_team

def validate_team_selection(home_team, away_team):
    if home_team == "-- Select Home Team --" or away_team == "-- Select Away Team --":
        st.warning("Please select both Home and Away teams.")
        return False
    elif home_team == away_team:
        st.warning("Home team and Away team cannot be the same.")
        return False
    return True


def add_match_to_list(league_id, stage_id, home_team, away_team, full_datetime, teams, tie_id=None, leg=None):
    home_team_id = next((team['id'] for team in teams if team['name'] == home_team), None)
    away_team_id = next((team['id'] for team in teams if team['name'] == away_team), None)

    if home_team_id and away_team_id:
        match = {
            "league_id": league_id,
            "stage_id": stage_id,
            "home_team_id": home_team_id,
            "away_team_id": away_team_id,
            "home_team": home_team,
            "away_team": away_team,
            "datetime": full_datetime
        }

        if tie_id and leg:
            match['tie_id'] = tie_id
            match['leg'] = leg

        st.session_state.pending_matches.append(match)
        st.success(f"Match {home_team} vs {away_team} added to list.")
    else:
        st.error("Team IDs could not be resolved.")

def handle_pending_matches():
    if not st.session_state.pending_matches:
        return

    st.markdown("### 📝 Pending Matches to Add")
    for i, match in enumerate(st.session_state.pending_matches):
        label = f"{match['home_team']} vs {match['away_team']} | {match['datetime']}"
        if match.get('leg'):
            label += f" ({match['leg'].capitalize()} Leg)"
        st.write(f"{i+1}. {label}")

    if st.button("✅ Save All Matches"):
        save_all_matches()

    if st.button("🗑️ Clear Match List"):
        st.session_state.pending_matches.clear()
        st.info("Match list cleared.")



def save_all_matches():
    all_success = True
    inserted_matches = []  # Stores (tie_id, leg, match_id)

    for match in st.session_state.pending_matches:
        round_id = get_round_id_by_date(match['datetime'].split(" ")[0])
        if not round_id:
            st.error(f"❌ No round found for date {match['datetime']}")
            all_success = False
            continue

        if check_duplicate_match(round_id, match['home_team'], match['away_team']):
            st.warning(f"⚠️ Match {match['home_team']} vs {match['away_team']} already exists.")
            continue

        match_id = add_match(
            round_id,
            match['league_id'],
            match['home_team_id'],
            match['away_team_id'],
            match['datetime'],
            match['stage_id']
        )

        if not match_id:
            st.error(f"❌ Failed to insert match: {match['home_team']} vs {match['away_team']}")
            all_success = False
        else:
            if 'tie_id' in match and 'leg' in match:
                inserted_matches.append((match['tie_id'], match['leg'], match_id))

    # Handle two-legged ties
    ties_grouped = {}
    for tie_id, leg, match_id in inserted_matches:
        if tie_id not in ties_grouped:
            ties_grouped[tie_id] = {}
        ties_grouped[tie_id][leg] = match_id

    for tie_id, legs in ties_grouped.items():
        if 'first' in legs and 'second' in legs:
            insert_two_legged_tie(legs['first'], legs['second'])
        else:
            st.warning(f"⚠️ Tie {tie_id} is incomplete — only one leg added.")

    if all_success:
        st.success("✅ All matches saved successfully!")
        st.session_state.pending_matches.clear()

def insert_two_legged_tie(first_leg_id, second_leg_id):
    try:
        connection = get_connection()  # Get the connection
        cursor = connection.cursor()   # Get the cursor from the connection
        cursor.execute("""
            INSERT INTO two_legged_ties (first_leg_match_id, second_leg_match_id)
            VALUES (?, ?)
        """, (first_leg_id, second_leg_id))
        connection.commit()  # Commit using the same connection
    except Exception as e:
        st.error(f"❌ Error saving two-legged tie: {e}")
