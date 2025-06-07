# manage_modules/manage_matches.py
import streamlit as st
from datetime import datetime
from controllers.manage_matches_controller import get_all_leagues, get_teams_by_league, add_match, check_duplicate_match, get_round_id_by_date

# Icons
MANAGE_ICON = "🛠️"
VIEW_ICON = "📅"

def render():
    st.markdown("""
        <style>
        .title {
            font-size: 36px;
            font-weight: bold;
            color: #1f77b4;
            text-align: center;
            margin-bottom: 20px;
        }
        .tab-style {
            padding: 15px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            background-color: #f9f9f9;
            transition: all 0.3s ease-in-out;
        }
        .tab-style:hover {
            background-color: #eef6fb;
            border-color: #1f77b4;
        }
        .emoji-header {
            font-size: 24px;
            font-weight: bold;
            color: #444;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="title">⚽ Match Management Dashboard</div>', unsafe_allow_html=True)

    tabs = st.tabs([f"{MANAGE_ICON} Manage Matches", f"{VIEW_ICON} View Matches"])

    with tabs[0]:
        st.markdown('<div class="tab-style">', unsafe_allow_html=True)
        render_manage_matches_tab()
        st.markdown('</div>', unsafe_allow_html=True)

    with tabs[1]:
        st.markdown('<div class="tab-style">', unsafe_allow_html=True)
        render_view_matches_tab()
        st.markdown('</div>', unsafe_allow_html=True)


def render_manage_matches_tab():
    st.markdown(
        f'<div style="font-size:24px; font-weight:bold; margin-bottom:10px;">{MANAGE_ICON} Add / Edit / Delete Matches</div>',
        unsafe_allow_html=True
    )
    st.info("Here you can manage all the matches for different rounds and leagues.")

    # Load leagues for dropdown
    leagues = get_all_leagues()
    league_names = [league['name'] for league in leagues]
    league_name = st.selectbox("Select League", ["-- Select League --"] + league_names)

    if league_name == "-- Select League --":
        st.warning("Please select a league to start.")
        return

    # Get league_id for selected league
    league_id = next((league['id'] for league in leagues if league['name'] == league_name), None)
    if league_id is None:
        st.error("Selected league not found.")
        return

    # Load teams in league
    teams = get_teams_by_league(league_id)
    team_names = [team['name'] for team in teams]

    # Team selectors
    home_team = st.selectbox("Select Home Team", ["-- Select Home Team --"] + team_names)
    away_team = st.selectbox("Select Away Team", ["-- Select Away Team --"] + team_names)

    # Match datetime picker
    match_date = st.date_input("Select Match Date")
    match_time = st.time_input("Select Match Time")
    full_match_datetime = datetime.combine(match_date, match_time).strftime("%Y-%m-%d %H:%M:%S")

    # Validate inputs before enabling Add button
    inputs_valid = True
    if home_team == "-- Select Home Team --" or away_team == "-- Select Away Team --":
        inputs_valid = False
        st.warning("Please select both home and away teams.")
    elif home_team == away_team:
        inputs_valid = False
        st.warning("Home team and Away team cannot be the same.")

    if inputs_valid and st.button("Add Match"):
        # Get the round_id based on match_date (YYYY-MM-DD)
        round_id = get_round_id_by_date(match_date.strftime("%Y-%m-%d"))
        if round_id is None:
            st.error("No round found or created for the selected match date.")
            return

        # Check for duplicate match in the same round
        if check_duplicate_match(round_id, home_team, away_team):
            st.error("This match already exists in the selected round.")
            return

        # Get team IDs
        home_team_id = next((team['id'] for team in teams if team['name'] == home_team), None)
        away_team_id = next((team['id'] for team in teams if team['name'] == away_team), None)
        if home_team_id is None or away_team_id is None:
            st.error("Error finding team IDs. Please try again.")
            return

        # Add the match
        added = add_match(round_id, league_id, home_team_id, away_team_id, full_match_datetime)
        if added:
            st.success("Match added successfully!")
        else:
            st.error("Failed to add match. Please try again.")



def render_view_matches_tab():
    st.markdown(f'<div class="emoji-header">{VIEW_ICON} View Matches by Round</div>', unsafe_allow_html=True)
    st.info("Browse and filter scheduled matches based on league and round.")
    st.write("📅 Match viewing UI will go here...")
