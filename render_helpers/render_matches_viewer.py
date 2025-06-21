import streamlit as st
import os
from datetime import datetime
import sqlite3
# Add match part
from controllers.manage_matches_controller import get_all_leagues, get_teams_by_league, add_match, check_duplicate_match, get_round_id_by_date
# View match part
from controllers.manage_matches_controller import (fetch_rounds, fetch_matches_by_round, delete_match_by_id, 
                                                   update_match_partial, fetch_leagues, fetch_teams, 
                                                   change_match_status, insert_or_replace_leg, fetch_legs_by_match_id,
                                                   fetch_stage_by_id, handle_two_leg_match_info)
from controllers.manage_predictions_controller import update_scores_for_match
from itertools import groupby
from datetime import datetime, timedelta
from utils import fetch_one, execute_query
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

local_tz = ZoneInfo("Africa/Cairo")

# Icons
MANAGE_ICON = "🛠️"
VIEW_ICON = "📅"
EDIT_ICON = "✏️"  # Pencil emoji for edit
DELETE_ICON = "🗑️"  # Trash can emoji for delete



def render_match_result(match):
    match = dict(match)
    home = match.get('home_score')
    away = match.get('away_score')
    match_id = match.get('id')
    stage_info = match.get('stage') or {}
    home_team_id = match.get('home_team_id')
    away_team_id = match.get('away_team_id')
    penalty_winner = match.get('penalty_winner')

    trophy = "🏆"
    handshake = "🤝"
    penalty_icon = "🥅"
    first_leg_icon = "1️⃣"
    second_leg_icon = "2️⃣"
    agg_icon = "🧮"

    if home is None or away is None:
        return "<div style='color:#888; font-style:italic;'>No score yet</div>"

    # Check if it's a two-legged tie
    is_two_legs = stage_info.get("two_legs") if isinstance(stage_info, dict) else False

    if is_two_legs:
        tie_result = fetch_one(
            """
            SELECT first_leg_match_id, second_leg_match_id, winner_team_id
            FROM two_legged_ties
            WHERE first_leg_match_id = ? OR second_leg_match_id = ?
            """, (match_id, match_id)
        )

        if tie_result:
            is_first_leg = match_id == tie_result["first_leg_match_id"]
            is_second_leg = match_id == tie_result["second_leg_match_id"]
            winner_team_id = tie_result.get("winner_team_id")

            if is_first_leg:
                return (
                    f"<div style='font-size:1.4rem; color:#4a90e2;'>"
                    f"{first_leg_icon} First Leg: <strong>{home}</strong> - <strong>{away}</strong>"
                    f"</div>"
                )

            if is_second_leg:
                # Get first leg match from session
                first_leg_match = next((m for m in st.session_state.get("matches", [])
                                        if m.get("id") == tie_result["first_leg_match_id"]), None)

                if first_leg_match:
                    home1 = first_leg_match.get("home_score", 0)
                    away1 = first_leg_match.get("away_score", 0)

                    agg_home = home1 + away
                    agg_away = away1 + home

                    result_str = (
                        f"<div style='font-size:1.4rem; color:#4a90e2;'>"
                        f"{second_leg_icon} Second Leg: <strong>{home}</strong> - <strong>{away}</strong><br>"
                        f"{agg_icon} Aggregate: <strong>{agg_home}</strong> - <strong>{agg_away}</strong><br>"
                    )

                    if agg_home > agg_away or agg_away > agg_home:
                        result_str += f"{trophy} Winner: <strong>{agg_home} - {agg_away}</strong></div>"
                    elif winner_team_id == home_team_id:
                        result_str += f"{penalty_icon} Winner by penalties: <strong>{agg_home} - {agg_away}</strong></div>"
                    elif winner_team_id == away_team_id:
                        result_str += f"{penalty_icon} Winner by penalties: <strong>{agg_home} - {agg_away}</strong></div>"
                    else:
                        result_str += f"{handshake} Draw — Awaiting penalty result</div>"

                    return result_str

    # Regular One-leg Match
    if home > away:
        return (
            f"<div style='font-size:1.6rem; color:green; font-weight:bold;'>"
            f"{trophy} {home} - {away}"
            f"</div>"
        )
    elif away > home:
        return (
            f"<div style='font-size:1.6rem; color:red; font-weight:bold;'>"
            f"{home} - {away} {trophy}"
            f"</div>"
        )
    elif penalty_winner == home_team_id:
        return (
            f"<div style='font-size:1.6rem; color:green; font-weight:bold;'>"
            f"{penalty_icon} {home} - {away}"
            f"</div>"
        )
    elif penalty_winner == away_team_id:
        return (
            f"<div style='font-size:1.6rem; color:red; font-weight:bold;'>"
            f"{home} - {away} {penalty_icon}"
            f"</div>"
        )
    else:
        return (
            f"<div style='font-size:1.6rem; color:orange; font-weight:bold;'>"
            f"{home} - {away} {handshake}"
            f"</div>"
        )







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

def render_stage_tag(stage_name):
    # Just plain text with some padding and bold font
    return f"<span style='font-weight:bold; font-size:1.1rem; padding:2px 8px;'>{stage_name}</span>"

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

    stage_id = match['stage_id']
    if not stage_id:
        st.error("❌ Match is missing stage information.")
        return

    stage = fetch_stage_by_id(stage_id)
    if not stage:
        st.error("❌ Stage details not found.")
        return

    must_have_winner = stage['must_have_winner']
    two_legs = stage['two_legs']
    can_draw = stage['can_be_draw']

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

        penalty_winner_id = None
        show_winner_dropdown = False

        if two_legs:
            st.info("📢 This is a two-leg match. You may need to handle aggregate scoring.")

            # Use the existing function you wrote
            home_score_leg1, away_score_leg1, home_team, away_team = handle_two_leg_match_info(match['id'])

            if must_have_winner and status == "finished":
                # Only consider aggregate if this is the second leg
                tie_result = fetch_one(
                    """
                    SELECT first_leg_match_id, second_leg_match_id
                    FROM two_legged_ties
                    WHERE first_leg_match_id = ? OR second_leg_match_id = ?
                    """, (match['id'], match['id'])
                )

                if tie_result:
                    if match['id'] == tie_result['second_leg_match_id']:
                        # Aggregate score logic using leg1 + current inputs
                        total_home = home_score_leg1 + away_score
                        total_away = away_score_leg1 + home_score
                        st.markdown(f"""🧮 **Second Leg Match**
                        <br>📊 First leg result: <span style='color:blue; font-weight:bold;'>{home_team} {home_score_leg1} - {away_score_leg1} {away_team}</span>
                        """,
                        unsafe_allow_html=True
                        )
                        if total_home == total_away:
                            show_winner_dropdown = True
                            st.markdown(
                                    f"""
                                    <div style="background-color:#f1f3f4; padding:20px; border-radius:12px; border-left:6px solid #4a90e2;">
                                        <h3 style="margin-bottom:10px; color:#0f62fe;">🧮 <u>Aggregate Result</u></h3>
                                        <p style="font-size:22px; font-weight:600; color:#1f77b4; text-align:center;">
                                            🔢 <span style="font-size:26px;">{total_home}</span>
                                            &nbsp;–&nbsp;
                                            <span style="font-size:26px;">{total_away}</span>
                                        </p>
                                    </div>
                                    """,
                                    unsafe_allow_html=True
                                )


        elif must_have_winner and not two_legs and status == "finished" and home_score == away_score:
            show_winner_dropdown = True
            st.warning("⚠️ This match must have a winner (penalties).")

        if show_winner_dropdown:
            selected = st.selectbox(
                "🏆 Winner on Penalties",
                options=["", match['home_team_id'], match['away_team_id']],
                format_func=lambda x: "Select Winner" if x == "" else teams[x]
            )
            penalty_winner_id = selected if selected != "" else None

        submitted = st.form_submit_button("Save Changes")
        if submitted:
            if show_winner_dropdown and not penalty_winner_id:
                st.error("You must select a winner for a draw match that requires one.")
                return

            update_match_partial(
                match_id=match['id'],
                match_datetime=combined_datetime.isoformat(),
                status=status,
                home_score=home_score,
                away_score=away_score,
                penalty_winner=penalty_winner_id
            )

            update_scores_for_match(match['id'])
            tie = fetch_one(
            """
            SELECT id, first_leg_match_id, second_leg_match_id
            FROM two_legged_ties
            WHERE first_leg_match_id = ? OR second_leg_match_id = ?
            """, (match['id'], match['id'])
            )
            if tie:
                execute_query(
                """
                UPDATE two_legged_ties
                SET winner_team_id = ?
                WHERE id = ?
                """,
                (penalty_winner_id, tie['id'])
                )

            st.success("✅ Match updated successfully with leg results and predictions scored!")
            st.session_state.edit_match_id = None
            st.rerun()





            
def render_view_matches_tab():
    st.markdown(f'<div class="emoji-header">{VIEW_ICON} View Matches by Round</div>', unsafe_allow_html=True)
    st.info("Browse and filter scheduled matches based on league and round.")
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

        st.markdown(f"""
                <div style='
                    background: linear-gradient(90deg, #0d6efd, #6610f2);
                    color: white;
                    font-weight: bold;
                    font-size: 1.1rem;
                    padding: 10px 20px;
                    border-radius: 12px;
                    margin: 12px 0;
                    box-shadow: 0 2px 6px rgba(0,0,0,0.2);
                    display: inline-block;
                '>
                    🏆 {league}
                </div>
            """, unsafe_allow_html=True)
        
        for match in group:
            # Parse match time as UTC, then convert to Cairo time
            match_time_utc = datetime.fromisoformat(match['match_datetime']).replace(tzinfo=timezone.utc)
            match_time = match_time_utc.astimezone(local_tz)
            stage_name = str(match['stage_name'])
            now = datetime.now(timezone.utc).astimezone(local_tz)
            time_diff = match_time - now
            total_seconds_left = time_diff.total_seconds()
            hours_left = total_seconds_left / 3600
            minutes_left = int(total_seconds_left / 60)
            match_date = match_time.date()
            time_str = match_time.strftime('%I:%M %p')
            change_match_status(match)

            # 🧭 Display tag and live progress bar
            if 0 < minutes_left < 1:
                date_display = """
                    <span style='
                        background: linear-gradient(135deg, #fff3cd, #ffe8a1);
                        color: #d63384;
                        font-weight: bold;
                        padding: 8px 16px;
                        border-radius: 20px;
                        font-size: 1rem;
                        box-shadow: 0 0 8px rgba(255, 243, 205, 0.6);
                    '>⏰ Less than 1 min!</span>
                """
            elif 0 < hours_left <= 1:
                date_display = f"""
                    <span style='
                        background: linear-gradient(135deg, #fff3cd, #ffe8a1);
                        color: #d63384;
                        font-weight: bold;
                        padding: 8px 16px;
                        border-radius: 20px;
                        font-size: 1rem;
                        box-shadow: 0 0 8px rgba(255, 243, 205, 0.6);
                    '>⏰ {int(minutes_left)} min left</span>
                """
            elif 1 < hours_left <= 10:
                date_display = f"""
                    <span style='
                        background: linear-gradient(135deg, #ffeeba, #ffe49c);
                        color: #856404;
                        font-weight: bold;
                        padding: 8px 16px;
                        border-radius: 20px;
                        font-size: 1rem;
                        box-shadow: 0 0 6px rgba(255, 238, 186, 0.6);
                    '>⏰ {int(hours_left)} hours left</span>
                """
            elif (match_date == now.date() and hours_left> 0):
                date_display = """
                    <span style='
                        background: linear-gradient(135deg, #f8d7da, #f5b8c1);
                        color: #721c24;
                        font-weight: bold;
                        padding: 8px 16px;
                        border-radius: 20px;
                        font-size: 1rem;
                        box-shadow: 0 0 10px rgba(248, 215, 218, 0.6);
                    '>🔴 Today</span>
                """
            elif match_date == now.date() + timedelta(days=1):
                date_display = """
                    <span style='
                        background: linear-gradient(135deg, #d1ecf1, #a8d8e4);
                        color: #0c5460;
                        font-weight: bold;
                        padding: 8px 16px;
                        border-radius: 20px;
                        font-size: 1rem;
                        box-shadow: 0 0 10px rgba(209, 236, 241, 0.6);
                    '>🌙 Tomorrow</span>
                """
            else:
                date_display = f"""
                    <span style='
                        background: #f0f0f0;
                        color: #333;
                        font-weight: 500;
                        padding: 6px 14px;
                        border-radius: 14px;
                        font-size: 1rem;
                        box-shadow: 0 1px 4px rgba(0,0,0,0.1);
                    '>📅 {match_time.strftime('%A, %B %d, %Y')}</span>
                """
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
                        <div style='margin-top:4px;'>{render_stage_tag(match['stage_name'])}</div>
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