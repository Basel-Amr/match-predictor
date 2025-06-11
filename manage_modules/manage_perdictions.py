from modules import under_update
import streamlit as st
from datetime import datetime, timedelta
from controllers.manage_predictions_controller import (
    fetch_all_players,
    fetch_grouped_matches,
    fetch_predictions_for_player,
    upsert_prediction,
    fetch_match_by_id
)
from controllers.manage_matches_controller import (fetch_rounds, fetch_matches_by_round, delete_match_by_id, update_match_partial, 
                                                   fetch_leagues, fetch_teams, change_match_status, insert_or_replace_leg, 
                                                   fetch_legs_by_match_id)
from itertools import groupby
from render_helpers.render_predictions import render_prediction_input
MANAGE_ICON = "🛠️"
VIEW_ICON = "📅"
EDIT_ICON = "✏️"  # Pencil emoji for edit
DELETE_ICON = "🗑️"  # Trash can emoji for delete

def render_prediction_result(pred, match_status):
    if match_status.lower() != "finished":
        return """
            <div style='color: #6c757d; font-weight: 500; text-align:center; animation: fadeIn 0.6s;'>
                ⏳ <span style='font-size: 1.1em;'>Match in Progress</span><br>
                <b>Points will be revealed after the final whistle! ⚽</b>
            </div>
        """

    if pred is None:
        return """
            <div style='color: #adb5bd; font-weight: 500; text-align:center; animation: fadeIn 0.6s;'>
                ❌ <span style='font-size: 1.1em;'>No Prediction Made</span><br>
                <b>+0 pts</b>
            </div>
        """

    try:
        score = pred.get('score', 0)
    except AttributeError:
        try:
            score = pred['score']
        except (TypeError, KeyError):
            score = 0

    if score == 0:
        color, emoji, text, pts = "#dc3545", "❌", "Missed it!", "+0 pts"
    elif score == 1:
        color, emoji, text, pts = "#fd7e14", "⚠️", "Close Call!", "+1 pt"
    elif score == 2:
        color, emoji, text, pts = "#0dcaf0", "👍", "Good Guess!", "+2 pts"
    elif score == 3:
        color, emoji, text, pts = "#20c997", "👌", "Great Work!", "+3 pts"
    else:
        color, emoji, text, pts = "#6f42c1", "🎯", "Perfect Prediction!", "+4 pts"

    return f"""
        <div style='color: {color}; font-weight: 500; animation: popFade 0.6s; text-align:center;'>
            {emoji} <span style='font-size: 1.1em;'>{text} <b>{pts}</b></span>
        </div>
    """



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
    color = colors.get(status, '#6c757d')
    icon = icons.get(status, '❔')
    return f"<span style='background:{color};color:white;padding:4px 10px;border-radius:5px;font-weight:600;font-size:0.9em;'>{icon} {status.capitalize()}</span>"

def render_match_result(match):
    if match['home_score'] is not None and match['away_score'] is not None:
        home = match['home_score']
        away = match['away_score']

        # Access 'date' safely without .get()
        match_date = match['date'] if 'date' in match.keys() else ''

        trophy = "🏆"
        handshake = "🤝"
        penalty_icon = "⚽️"

        date_html = f"<div style='text-align:center; font-size: 1rem; font-weight: 600; color:#555; margin-bottom: 0.3rem;'>{match_date}</div>" if match_date else ""
        if home > away:
            # Home win
            result = f"<span style='color:green; font-weight:bold;'>Actual Score: {home} - {away} {trophy}</span>"
        elif home < away:
            # Away win
            result = f"<span style='color:red; font-weight:bold;'>Actual Score: {trophy} {home} - {away}</span>"
        else:
            # Draw — check penalties
            legs = fetch_legs_by_match_id(match['id'])
            winner_team_id = None
            for leg in legs:
                if leg.get('winner_team_id'):
                    winner_team_id = leg['winner_team_id']
                    break

            if winner_team_id == match['home_team_id']:
                result = f"<span style='color:green; font-weight:bold;'>{home} - {away} {handshake} {penalty_icon} {trophy}</span>"
            elif winner_team_id == match['away_team_id']:
                result = f"<span style='color:red; font-weight:bold;'>{trophy} {penalty_icon} {handshake} {home} - {away}</span>"
            else:
                # True draw, no penalty winner
                result = f"<span style='color:orange; font-weight:bold;'>{home} - {away} {handshake}</span>"

        return f"<div style='font-size:1.4rem; text-align:center;'>{date_html}{result}</div>"

    return "<div style='color:#888; font-style:italic; text-align:center;'>No score yet</div>"


def render():
    rounds = fetch_rounds()
    if not rounds:
        st.warning("No rounds available.")
        return

    round_names = {r['name']: r['id'] for r in rounds}
    selected_round_name = st.selectbox("Select Round", list(round_names.keys()))
    selected_round_id = round_names[selected_round_name]

    players = fetch_all_players()
    player_options = {p['username']: p['id'] for p in players}
    selected_player_name = st.selectbox("Select Player", list(player_options.keys()))
    selected_player_id = player_options[selected_player_name]

    predictions = fetch_predictions_for_player(selected_player_id)
    pred_dict = {pred['match_id']: pred for pred in predictions}

    matches = fetch_matches_by_round(selected_round_id)
    if not matches:
        st.info("No matches scheduled for this round.")
        return

    now = datetime.now()
    try:
        locale.setlocale(locale.LC_TIME, '')
    except:
        pass

    for league, group in groupby(matches, key=lambda m: m['league_name']):
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
            '>🏆 {league}</div>
        """, unsafe_allow_html=True)

        for match in group:
            match_time = datetime.fromisoformat(match['match_datetime'])
            time_diff = match_time - now
            total_seconds_left = time_diff.total_seconds()
            hours_left = total_seconds_left / 3600
            minutes_left = int(total_seconds_left / 60)
            match_date = match_time.date()
            time_str = match_time.strftime('%I:%M %p')
            change_match_status(match)

            if 0 < minutes_left < 1:
                date_display = "<span style='color: orange; font-weight: bold;'>⏰ Less than 1 min!</span>"
            elif 0 < hours_left <= 1:
                date_display = f"<span style='color: orange; font-weight: bold;'>⏰ {int(minutes_left)} min left</span>"
            elif 1 < hours_left <= 10:
                date_display = f"<span style='color: orange; font-weight: bold;'>⏰ {int(hours_left)} hours left</span>"
            elif (match_date == now.date() and hours_left> 0):
                date_display = "<span style='color: red; font-weight: bold;'>🔴 Today</span>"
            elif match_date == now.date() + timedelta(days=1):
                date_display = "<span style='color: blue; font-weight: bold;'>🌙 Tomorrow</span>"
            else:
                date_display = f"<span>📅 {match_time.strftime('%A, %B %d, %Y')}</span>"

            progress_html = ""
            if 0 < hours_left <= 12:
                total = 12 * 3600
                current = total - total_seconds_left
                progress = float(current / total)
                progress_percent = int(progress * 100)
                progress_html = f"""<div style='background:#ddd; height:6px; border-radius:3px;'>
                                        <div style='width: {progress_percent}%; background:#0d6efd; height:6px; border-radius:3px;'></div>
                                    </div>"""

            st.markdown("<div style='margin-bottom: 20px;'>", unsafe_allow_html=True)
            cols = st.columns([2.5, 5, 2.5, 2])

            with cols[0]:
                st.markdown("<div style='text-align:center;'>", unsafe_allow_html=True)
                if match['home_team_logo']:
                    st.image(match['home_team_logo'], width=45)
                st.markdown(f"<div style='font-weight:600;margin-top:5px;'>{match['home_team_name']}</div>", unsafe_allow_html=True)

            with cols[1]:
                match_result = render_match_result(match)
                status_tag = render_status_tag(match['status'])
                prediction_html = ""
                pred = pred_dict.get(match['id'])
                pred_result = render_prediction_result(pred,match['status'] )
                if pred:
                    pred_home = str(pred['predicted_home_score'])
                    pred_away = str(pred['predicted_away_score'])
                    pred_penalty = str(pred['predicted_penalty_winner']) or ""
                    score = str(pred['score']) if match['status'].lower() == "finished" else "Pending"
                else: 
                    pred_home = "None"
                    pred_away = "None"
                    pred_penalty = ""
                # Only show penalty section if there's a penalty winner
                penalty_text = f" | Penalty: {pred_penalty}" if pred_penalty not in [None, "", "None"] else ""
                    
                st.markdown(f"""
                <div style='text-align: center; padding: 5px;'>
                    <div style='font-size:1.1rem;font-weight:bold;margin-bottom:4px;'>{time_str}</div>
                    <div style='margin:4px 0;'>{date_display}</div>
                    <div style='margin:6px 0;font-size:1rem;font-weight:bold;color:red;'>{match_result}</div>
                    <div style='margin-top:4px;'>{status_tag}</div>
                    <b>Your Prediction:</b> {pred_home} - {pred_away}{penalty_text}<br>
                    <b>{pred_result}</b>
                </div>
            """, unsafe_allow_html=True)


            with cols[2]:
                st.markdown("<div style='text-align:center;'>", unsafe_allow_html=True)
                if match['away_team_logo']:
                    st.image(match['away_team_logo'], width=45)
                st.markdown(f"<div style='font-weight:600;margin-top:5px;'>{match['away_team_name']}</div>", unsafe_allow_html=True)

            with cols[3]:
                if st.button("🔮 Predict", key=f"predict_{match['id']}"):
                    st.session_state.predict_match_id = match['id']
                    st.session_state.show_add_match_form = False

            if st.session_state.get("predict_match_id") == match["id"]:
                render_prediction_input(match, selected_player_name, selected_player_id, upsert_prediction, fetch_predictions_for_player)

            st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("<hr style='margin:10px 0;'>", unsafe_allow_html=True)



