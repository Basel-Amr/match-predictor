# manage_modules/manage_matches.py
import streamlit as st
import os
from datetime import datetime
import sqlite3
# Add match part
from controllers.manage_matches_controller import get_all_leagues, get_teams_by_league, add_match, check_duplicate_match, get_round_id_by_date
# View match part
from controllers.manage_matches_controller import fetch_rounds, fetch_matches_by_round, delete_match_by_id, update_match_partial, fetch_leagues, fetch_teams, change_match_status, insert_or_replace_leg, fetch_legs_by_match_id
from itertools import groupby
from streamlit_autorefresh import st_autorefresh
from datetime import datetime, timedelta
# Icons
MANAGE_ICON = "🛠️"
VIEW_ICON = "📅"
EDIT_ICON = "✏️"  # Pencil emoji for edit
DELETE_ICON = "🗑️"  # Trash can emoji for delete

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


##----------------------------------------------------------------------------------------------------------------------##
def render_view_matches_tab():
    st.markdown(f'<div class="emoji-header">{VIEW_ICON} View Matches by Round</div>', unsafe_allow_html=True)
    st.info("Browse and filter scheduled matches based on league and round.")

    # ⚙️ Customizing refresh rate
    refresh_option = st.selectbox("⚙️ Auto Refresh Interval", ["15 sec", "30 sec", "1 min", "2 min", "5 min"])
    refresh_map = {
        "15 sec": 15 * 1000,
        "30 sec": 30 * 1000,
        "1 min": 60 * 1000,
        "2 min": 120 * 1000,
        "5 min": 300 * 1000
    }
    st_autorefresh(interval=refresh_map[refresh_option], key="match_view_autorefresh")

    rounds = fetch_rounds()
    if not rounds:
        st.warning("No rounds available.")
        return

    round_names = {r['name']: r['id'] for r in rounds}
    selected_round_name = st.selectbox("Select Round", list(round_names.keys()))
    selected_round_id = round_names[selected_round_name]

    matches = fetch_matches_by_round(selected_round_id)
    if not matches:
        st.info("No matches scheduled for this round.")
        return

    now = datetime.now()

    # 🌍 Set locale for localized date formatting (try user's OS locale)
    try:
        locale.setlocale(locale.LC_TIME, '')
    except:
        pass

    for league, group in groupby(matches, key=lambda m: m['league_name']):
        league_logo_path = next((g['league_logo'] for g in matches if g['league_name'] == league), None)

        st.markdown("<div style='display: flex; align-items: center; justify-content: center;'>", unsafe_allow_html=True)
        cols = st.columns([0.07, 0.93])
        with cols[0]:
            if league_logo_path:
                st.image(league_logo_path, width=30)
        with cols[1]:
            st.markdown(f"<h5 style='margin:0;padding:0;'>{league}</h5>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        for match in group:
            match_time = datetime.fromisoformat(match['match_datetime'])
            time_diff = match_time - now
            total_seconds_left = time_diff.total_seconds()
            hours_left = total_seconds_left / 3600
            minutes_left = int(total_seconds_left / 60)
            match_date = match_time.date()
            time_str = match_time.strftime('%I:%M %p')
            change_match_status(match)

            # 🧭 Display tag and live progress bar
            if 0 < minutes_left < 1:
                date_display = f"<span style='background:#fff3cd;color:#d63384;font-weight:bold;padding:6px 14px;border-radius:14px;font-size:1rem;'>⏰ less than one minute!</span>"
            elif 0 < hours_left <= 1:
                date_display = f"<span style='background:#fff3cd;color:#d63384;font-weight:bold;padding:6px 14px;border-radius:14px;font-size:1rem;'>⏰ {minutes_left} minutes left!</span>"
            elif 1 < hours_left <= 10:
                date_display = f"<span style='background:#ffeeba;color:#856404;font-weight:bold;padding:6px 14px;border-radius:14px;font-size:1rem;'>⏰ {int(hours_left)} hours left!</span>"
            elif match_date == now.date():
                date_display = f"<span style='background:#f8d7da;color:#721c24;font-weight:bold;padding:6px 14px;border-radius:14px;font-size:1rem;'>🔴 Today</span>"
            elif match_date == now.date() + timedelta(days=1):
                date_display = f"<span style='background:#d1ecf1;color:#0c5460;font-weight:bold;padding:6px 14px;border-radius:14px;font-size:1rem;'>🌙 Tomorrow</span>"
            else:
                date_display = match_time.strftime('%A, %B %d, %Y')

            # 🧭 Live countdown progress bar (within 12h)
            progress = None
            if 0 < hours_left <= 12:
                total = 12 * 3600
                current = total - total_seconds_left
                progress = float(current / total)

            home_logo_path = match['home_team_logo']
            away_logo_path = match['away_team_logo']

            st.markdown(
                """
                <div style='
                    background: linear-gradient(to right, #f8f9fa, #e9ecef);
                    border-radius: 18px;
                    padding: 20px;
                    margin: 15px 0;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
                    max-width: 900px;
                    margin-left: auto;
                    margin-right: auto;
                '>
                """, unsafe_allow_html=True
            )

            cols = st.columns([2.5, 5, 2.5, 1, 1])  # Home, Info, Away, Edit, Delete

            # Home Team
            with cols[0]:
                st.markdown("<div style='text-align:center;'>", unsafe_allow_html=True)
                if home_logo_path:
                    st.image(home_logo_path, width=45)
                st.markdown(
                    f"<div style='font-weight:600;margin-top:5px;'>{match['home_team_name']}</div>",
                    unsafe_allow_html=True
                )
                st.markdown("</div>", unsafe_allow_html=True)

            # Center Info (Time + Status + Result)
            with cols[1]:
                st.markdown(
                    f"""
                    <div style='
                        display: flex; 
                        flex-direction: column; 
                        justify-content: center; 
                        align-items: center; 
                        height: 100%; 
                        text-align: center;
                        padding: 5px;
                    '>
                        <div style='font-size:1.1rem;font-weight:bold;margin-bottom:4px;'>{time_str}</div>
                        <div style='margin:4px 0;'>{date_display}</div>
                        <div style='margin:6px 0;font-size:1rem;font-weight:bold;color:red;'>{render_match_result(match)}</div>
                        <div style='margin-top:4px;'>{render_status_tag(match['status'])}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            # Away Team
            with cols[2]:
                st.markdown("<div style='text-align:center;'>", unsafe_allow_html=True)
                if away_logo_path:
                    st.image(away_logo_path, width=45)
                st.markdown(
                    f"<div style='font-weight:600;margin-top:5px;'>{match['away_team_name']}</div>",
                    unsafe_allow_html=True
                )
                st.markdown("</div>", unsafe_allow_html=True)

            # Edit Button
            with cols[3]:
                st.markdown("<div style='display:flex;justify-content:center;'>", unsafe_allow_html=True)
                if st.button(EDIT_ICON, key=f"edit_match_{match['id']}"):
                    st.session_state.edit_match_id = match['id']
                    st.session_state.show_add_match_form = False
                st.markdown("</div>", unsafe_allow_html=True)

            # Delete Button
            with cols[4]:
                st.markdown("<div style='display:flex;justify-content:center;'>", unsafe_allow_html=True)
                if st.button(DELETE_ICON, key=f"delete_match_{match['id']}"):
                    delete_match_by_id(match['id'])
                    st.session_state.status_message = "Match deleted."
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

            # Inline edit form
            if st.session_state.get("edit_match_id") == match["id"]:
                render_edit_match(match)

            st.markdown("</div>", unsafe_allow_html=True)  # Close main match wrapper div
            st.markdown("<hr style='margin:10px 0;'>", unsafe_allow_html=True)






            
            
def render_edit_match(match):
    st.markdown("### ✏️ Edit Match")

    match_dt = datetime.fromisoformat(match['match_datetime'])

    # Fetch data
    rounds = {r['id']: r['name'] for r in fetch_rounds()}
    leagues_data = {l['id']: l for l in fetch_leagues()}
    league = leagues_data.get(match['league_id'])
    teams = {t['id']: t['name'] for t in fetch_teams()}

    if not league:
        st.error("League details not found.")
        return

    # Extract league rules
    can_draw = bool(league['can_be_draw'])
    two_legs = bool(league['two_legs'])
    must_have_winner = bool(league['must_have_winner'])

    with st.form(key=f"edit_form_{match['id']}"):
        st.text_input("Round", rounds.get(match['round_id'], "Unknown"), disabled=True)
        st.text_input("League", league['name'], disabled=True)
        st.text_input("Home Team", teams.get(match['home_team_id'], "Unknown"), disabled=True)
        st.text_input("Away Team", teams.get(match['away_team_id'], "Unknown"), disabled=True)

        date_input = st.date_input("Match Date", value=match_dt.date())
        time_input = st.time_input("Match Time", value=match_dt.time())
        combined_datetime = datetime.combine(date_input, time_input)

        status = st.selectbox("Status", ["upcoming", "live", "finished", "cancelled"],
                              index=["upcoming", "live", "finished", "cancelled"].index(match['status']))

        home_score = st.number_input("Home Score", value=match['home_score'], step=1)
        away_score = st.number_input("Away Score", value=match['away_score'], step=1)

        penalty_winner = None
        show_winner_dropdown = False

        if status == "finished" and home_score == away_score:
            if must_have_winner and not two_legs:
                show_winner_dropdown = True
                st.warning("⚠️ This match must have a winner (penalties).")
            elif must_have_winner and two_legs:
                all_legs = fetch_legs_by_match_id(match['id'])
                total_home = sum([leg['home_score'] or 0 for leg in all_legs])
                total_away = sum([leg['away_score'] or 0 for leg in all_legs])
                if total_home == total_away and len(all_legs) == 2:
                    show_winner_dropdown = True
                    st.warning("⚠️ Aggregate score is draw. You must select a penalty winner.")

        if show_winner_dropdown:
            penalty_winner = st.selectbox("🏆 Winner on Penalties", [
                ("", "Select Winner"),
                (match['home_team_id'], teams[match['home_team_id']]),
                (match['away_team_id'], teams[match['away_team_id']])
            ], format_func=lambda x: x[1] if x else "")

        submitted = st.form_submit_button("Save Changes")
        if submitted:
            if show_winner_dropdown and (not penalty_winner or penalty_winner[0] == ""):
                st.error("You must select a winner for a draw match that requires one.")
                return

            update_match_partial(
                match_id=match['id'],
                match_datetime=combined_datetime.isoformat(),
                status=status,
                home_score=home_score,
                away_score=away_score
            )

            # Compute winner for leg
            winner_team_id = None
            if status == "finished":
                if home_score > away_score:
                    winner_team_id = match['home_team_id']
                elif away_score > home_score:
                    winner_team_id = match['away_team_id']
                elif show_winner_dropdown and penalty_winner and penalty_winner[0] != "":
                    winner_team_id = penalty_winner[0]

            insert_or_replace_leg(
                match_id=match['id'],
                leg_number=1,
                leg_date=combined_datetime.isoformat(),
                home_score=home_score,
                away_score=away_score,
                can_draw=can_draw,
                winner_team_id=winner_team_id,
                notes="updated from match edit"
            )

            st.success("Match updated successfully with leg results!")
            st.session_state.edit_match_id = None
            st.rerun()






def render_status_tag(status):
    colors = {
        'upcoming': '#3498db',
        'live': '#e67e22',
        'finished': '#2ecc71',
        'cancelled': '#e74c3c'
    }
    icons = {
        'upcoming': '⏳',
        'live': '🔴',
        'finished': '✅',
        'cancelled': '❌'
    }
    return f"<span style='background:{colors[status]};color:white;padding:2px 8px;border-radius:5px;'>{icons[status]} {status.capitalize()}</span>"

def render_match_result(match):
    if match['home_score'] is not None and match['away_score'] is not None:
        home = match['home_score']
        away = match['away_score']
        if home > away:
            result = f"<span style='color:green;'>🏆 {home} - {away}</span>"
        elif home < away:
            result = f"<span style='color:red;'>{home} - {away} 🏆</span>"
        else:
            # Check for penalty winner
            legs = fetch_legs_by_match_id(match['id'])
            winner_team_id = None
            for leg in legs:
                if leg['winner_team_id']:
                    winner_team_id = leg['winner_team_id']
                    break

            if winner_team_id == match['home_team_id']:
                result = f"<span style='color:green;'>🤝 {home} - {away} (🏆 Home wins on penalties)</span>"
            elif winner_team_id == match['away_team_id']:
                result = f"<span style='color:red;'>🤝 {home} - {away} (🏆 Away wins on penalties)</span>"
            else:
                result = f"<span style='color:orange;'>🤝 {home} - {away}</span>"

        return f"<div style='font-size:1.5rem; font-weight:bold;'>{result}</div>"
    return "<div style='color:#888;'>Not Available</div>"



