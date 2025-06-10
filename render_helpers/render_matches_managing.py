import streamlit as st
from datetime import datetime, timedelta
import uuid
# Add match part
from controllers.manage_matches_controller import (get_all_leagues, get_teams_by_league, add_match, check_duplicate_match, 
                                                   get_round_id_by_date)

from controllers.manage_leagues_controller import (
    save_uploaded_file,get_leagues,add_league, 
    update_league, delete_league,
     update_league, get_stages_by_league, 
     update_stage, delete_stage, add_stage
    )
from utils import (add_pending_match, display_pending_matches, save_pending_matches, clear_match_list, 
                   select_league, select_stage, select_teams, save_all_matches, 
                   validate_team_selection, add_match_to_list, handle_pending_matches, execute_query
                   )
# Icons
MANAGE_ICON = "🛠️"
VIEW_ICON = "📅"
EDIT_ICON = "✏️"  # Pencil emoji for edit
DELETE_ICON = "🗑️"  # Trash can emoji for delete

# Add match
# def render_manage_matches_tab():
#     st.markdown(
#         f'<div style="font-size:24px; font-weight:bold; margin-bottom:10px;">{MANAGE_ICON} Add / Edit / Delete Matches</div>',
#         unsafe_allow_html=True
#     )
#     st.info("Here you can manage all the matches for different rounds and stages of each league.")

#     # Initialize session state for pending matches
#     if "pending_matches" not in st.session_state:
#         st.session_state.pending_matches = []

#     # Load leagues
#     leagues = get_all_leagues()
#     league_names = [league['name'] for league in leagues]
#     league_name = st.selectbox("Select League", ["-- Select League --"] + league_names)

#     if league_name == "-- Select League --":
#         st.warning("Please select a league to start.")
#         return

#     # Get selected league_id
#     league_id = next((league['id'] for league in leagues if league['name'] == league_name), None)
#     if league_id is None:
#         st.error("Selected league not found.")
#         return

#     # Load stages for selected league
#     stages = get_stages_by_league(league_id)
#     stage_names = [stage['name'] for stage in stages]
#     stage_name = st.selectbox("Select Stage", ["-- Select Stage --"] + stage_names)

#     if stage_name == "-- Select Stage --":
#         st.warning("Please select a stage to start.")
#         return

#     stage_id = next((stage['id'] for stage in stages if stage['name'] == stage_name), None)

#     # Load teams for selected league
#     teams = get_teams_by_league(league_id)
#     team_names = [team['name'] for team in teams]

#     home_team = st.selectbox("Select Home Team", ["-- Select Home Team --"] + team_names)
#     away_team = st.selectbox("Select Away Team", ["-- Select Away Team --"] + team_names)

#     match_date = st.date_input("Match Date")
#     match_time = st.time_input("Match Time")
#     full_datetime = datetime.combine(match_date, match_time).strftime("%Y-%m-%d %H:%M:%S")

#     # Validate match entry
#     inputs_valid = True
#     if home_team == "-- Select Home Team --" or away_team == "-- Select Away Team --":
#         inputs_valid = False
#         st.warning("Please select both Home and Away teams.")
#     elif home_team == away_team:
#         inputs_valid = False
#         st.warning("Home team and Away team cannot be the same.")

#     # Add to session list
#     if inputs_valid and st.button("➕ Add Match to List"):
#         home_team_id = next((team['id'] for team in teams if team['name'] == home_team), None)
#         away_team_id = next((team['id'] for team in teams if team['name'] == away_team), None)

#         if home_team_id and away_team_id:
#             st.session_state.pending_matches.append({
#                 "league_id": league_id,
#                 "stage_id": stage_id,
#                 "home_team_id": home_team_id,
#                 "away_team_id": away_team_id,
#                 "home_team": home_team,
#                 "away_team": away_team,
#                 "datetime": full_datetime
#             })
#             st.success(f"Match {home_team} vs {away_team} added to list.")
#         else:
#             st.error("Team IDs could not be resolved.")

#     # Show pending matches
#     if st.session_state.pending_matches:
#         st.markdown("### 📝 Pending Matches to Add")
#         for i, match in enumerate(st.session_state.pending_matches):
#             st.write(f"{i+1}. {match['home_team']} vs {match['away_team']} | {match['datetime']}")

#         # Button to save all matches
#         if st.button("✅ Save All Matches"):
#             all_success = True
#             for match in st.session_state.pending_matches:
#                 # Determine round_id
#                 round_id = get_round_id_by_date(match['datetime'].split(" ")[0])
#                 if not round_id:
#                     st.error(f"❌ No round found for date {match['datetime']}")
#                     all_success = False
#                     continue

#                 if check_duplicate_match(round_id, match['home_team'], match['away_team']):
#                     st.warning(f"⚠️ Match {match['home_team']} vs {match['away_team']} already exists.")
#                     continue

#                 # Insert match
#                 success = add_match(round_id, match['league_id'], match['home_team_id'], match['away_team_id'], match['datetime'], match['stage_id'])
#                 if not success:
#                     st.error(f"❌ Failed to insert match: {match['home_team']} vs {match['away_team']}")
#                     all_success = False

#             if all_success:
#                 st.success("✅ All matches saved successfully!")
#                 st.session_state.pending_matches.clear()

#         # Button to clear list
#         if st.button("🗑️ Clear Match List"):
#             st.session_state.pending_matches.clear()
#             st.info("Match list cleared.")

def render_matches_header():
    st.markdown(
        f'<div style="font-size:24px; font-weight:bold; margin-bottom:10px;">{MANAGE_ICON} Add / Edit / Delete Matches</div>',
        unsafe_allow_html=True
    )
    st.info("Here you can manage all the matches for different rounds and stages of each league.")


def initialize_pending_matches():
    if "pending_matches" not in st.session_state:
        st.session_state.pending_matches = []

def add_match(league_id, stage_id, home_team_id, away_team_id, match_datetime):
    """
    Adds a match to the database and returns the inserted match ID.
    Automatically assigns the correct round_id based on the match date.
    """
    date_str = match_datetime.split(" ")[0]
    round_id = get_round_id_by_date(date_str)
    
    if not round_id:
        st.error(f"No round found for date: {date_str}")
        return None

    query = """
    INSERT INTO matches (round_id, league_id, home_team_id, away_team_id, match_datetime, stage_id)
    VALUES (?, ?, ?, ?, ?, ?)
    """
    cur = execute_query(query, (round_id, league_id, home_team_id, away_team_id, match_datetime, stage_id))
    return cur.lastrowid





def render_manage_matches_tab():
    render_matches_header()
    initialize_pending_matches()

    leagues = get_all_leagues()
    league_id, league_name = select_league(leagues)
    if not league_id:
        return

    stages = get_stages_by_league(league_id)
    stage_id, stage_name, two_legs = select_stage(stages)
    if not stage_id:
        return

    teams = get_teams_by_league(league_id)
    home_team, away_team = select_teams(teams)

    if validate_team_selection(home_team, away_team):

        if two_legs:
            st.markdown("### 🏟 First Leg")
            date1 = st.date_input("First Leg Date")
            time1 = st.time_input("First Leg Time")
            dt1 = datetime.combine(date1, time1).strftime("%Y-%m-%d %H:%M:%S")

            st.markdown("### 🏟 Second Leg")
            date2 = st.date_input("Second Leg Date")
            time2 = st.time_input("Second Leg Time")
            dt2 = datetime.combine(date2, time2).strftime("%Y-%m-%d %H:%M:%S")

            if st.button("➕ Add Two-Legged Match to List"):
                tie_id = str(uuid.uuid4())

                # First leg
                add_match_to_list(league_id, stage_id, home_team, away_team, dt1, teams, tie_id, "first")

                # Second leg with reversed teams
                add_match_to_list(league_id, stage_id, away_team, home_team, dt2, teams, tie_id, "second")

                st.success("✅ Two-legged tie added successfully.")
        else:
            match_date = st.date_input("Match Date")
            match_time = st.time_input("Match Time")
            full_datetime = datetime.combine(match_date, match_time).strftime("%Y-%m-%d %H:%M:%S")

            if st.button("➕ Add Match to List"):
                add_match_to_list(league_id, stage_id, home_team, away_team, full_datetime, teams)
                st.success("✅ Match added to pending list.")

    handle_pending_matches()
