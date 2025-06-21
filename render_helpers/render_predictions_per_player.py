from controllers.predictions_controllers import (
    format_time_left, get_next_round_info,
    get_all_rounds, get_round_id_by_name, get_matches_by_round, get_team_info, get_user_prediction, format_time_left_detailed,
    get_score_color, get_match_timing_display, get_player_name, get_prediction_deadline_for_round
)
from controllers.manage_matches_controller import change_match_status
import streamlit as st
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo  # Python 3.9+
from operator import itemgetter
from itertools import groupby
from manage_modules.manage_perdictions import render_prediction_result, render_status_tag, render_match_result
from render_helpers.render_matches_viewer import render_stage_tag
from controllers.manage_predictions_controller import (
    fetch_all_players,
    fetch_grouped_matches,
    fetch_predictions_for_player,
    upsert_prediction,
    fetch_match_by_id
)
from render_helpers.render_predictions import render_prediction_input
local_tz = ZoneInfo("Africa/Cairo")
def render_deadline(round_name, deadline_utc, match_count, number_of_predicted_matches=0):
    if not deadline_utc:
        st.warning("📅 No upcoming round or deadline found.")
        return

    now_local = datetime.now(timezone.utc).astimezone(local_tz)
    deadline_local = deadline_utc.astimezone(local_tz)
    print(deadline_local)
    time_left = deadline_local - now_local
    days = time_left.days
    hours, remainder = divmod(time_left.seconds, 3600)
    minutes, _ = divmod(remainder, 60)

    # Prediction percentage
    prediction_ratio = number_of_predicted_matches / match_count if match_count else 0
    progress_bar = int(prediction_ratio * 100)

    # Prediction color
    if prediction_ratio == 1:
        pred_color = "#2ecc71"
    elif prediction_ratio >= 0.75:
        pred_color = "#27ae60"
    elif prediction_ratio >= 0.5:
        pred_color = "#f1c40f"
    elif prediction_ratio >= 0.25:
        pred_color = "#e67e22"
    else:
        pred_color = "#e74c3c"

    # Time urgency color
    if time_left.total_seconds() < 3600:
        time_color = "#c62828"
    elif time_left.total_seconds() < 10 * 3600:
        time_color = "#f57c00"
    elif time_left.total_seconds() < 3 * 86400:
        time_color = "#fbc02d"
    else:
        time_color = "#1565c0"

    # --- UI ---
    st.markdown(f"""
    <div style='text-align: center; margin-bottom: 30px;'>
        <h2 style="color:#1f77b4;">⚡ Prediction Center ⚡</h2>
        <h3 style="margin-top: -10px;">🛡️ Next Round: <span style="color:#FFD700;">{round_name}</span></h3>
    </div>
    """, unsafe_allow_html=True)

    # Time Left Box
    st.markdown(f"""
    <div style="display: flex; justify-content: center; gap: 30px; margin-top: 20px;">
        <div style="text-align: center;">
            <div style="font-weight: bold; font-size: 16px;">D</div>
            <div style="background:{time_color}; color:white; padding:20px 10px; border-radius:12px;
                        font-size:22px; font-weight:bold; width:60px; margin-top:5px;">
                {days}
            </div>
        </div>
        <div style="text-align: center;">
            <div style="font-weight: bold; font-size: 16px;">H</div>
            <div style="background:{time_color}; color:white; padding:20px 10px; border-radius:12px;
                        font-size:22px; font-weight:bold; width:60px; margin-top:5px;">
                {hours}
            </div>
        </div>
        <div style="text-align: center;">
            <div style="font-weight: bold; font-size: 16px;">M</div>
            <div style="background:{time_color}; color:white; padding:20px 10px; border-radius:12px;
                        font-size:22px; font-weight:bold; width:60px; margin-top:5px;">
                {minutes}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Prediction Progress
    st.markdown(f"""
    <div style="margin-top: 30px; background: #f9f9f9; padding: 20px; border-radius: 15px;
                text-align: center; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
        <p style="font-size: 18px; color: black;"><strong>📋 Matches Predicted</strong></p>
        <p style="font-size: 22px; color:{pred_color}; font-weight: bold;">
            {number_of_predicted_matches} / {match_count}
        </p>
        <div style="background-color: #ddd; border-radius: 10px; overflow: hidden; height: 22px; margin-top: 10px;">
            <div style="width: {progress_bar}%; background-color: {pred_color}; height: 100%;
                        text-align: center; color: black; line-height: 22px; font-weight: bold;">
                {progress_bar}%
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)



def render_match_info(match_dt, status, home_score, away_score, prediction, match, return_html=False):
    status_clean = status.title().lower()
    pred_result = render_prediction_result(prediction,status_clean )
    status_tag = render_status_tag(status_clean)
    match_result = render_match_result(match)
    date_display = render_match_timing(match_dt)
    time_str = match_dt.strftime('%I:%M %p')
    change_match_status(match)

    # Default message
    prediction_display = "<b style='color: gray;'>Match not predicted yet.</b>"

    try:
        phs = prediction['predicted_home_score']
        pas = prediction['predicted_away_score']
        try: 
            penalty = prediction.get('predicted_penalty_winner', "")
        except:
            penalty = ""
        penalty_display = f" ({penalty} wins on pens)" if penalty else ""
        prediction_display = f"<b>Your Prediction:</b> {phs} - {pas}{penalty_display}<br>"

    except Exception:
        if status_clean == "finished":
            prediction_display = "<b style='color: red;'>⏰ Deadline passed. You didn’t make a prediction.</b>"
        else:
            prediction_display = "<b style='color: gray;'>Match not predicted yet.</b>"

    html = f"""
    <div style='text-align: center; padding: 5px;'>
        <div style='margin-top:4px;'>{render_stage_tag(match['stage_name'])}</div>
        <div style='font-size:1.1rem;font-weight:bold;margin-bottom:4px;'>{time_str}</div>
        <div style='margin:4px 0;'>{date_display}</div>
        <div style='margin:6px 0;font-size:1rem;font-weight:bold;color:red;'>{match_result}</div>
        <div style='margin:6px 0;font-size:1rem;font-weight:bold;color:red;'>{prediction_display}</div>
        <b>{pred_result}</b>
        <div style='margin-top:4px;'>{status_tag}</div>
    </div>
    """
    if return_html:
        return html
    else:
        st.markdown(html, unsafe_allow_html=True)



    
def render_match_card(match, player_id, round_id):
    match_id = match["id"]
    home_id = match["home_team_id"]
    away_id = match["away_team_id"]
    datetime_str = match["match_datetime"]
    status = match["status"]
    home_score = match["home_score"]
    away_score = match["away_score"]

    home_name, home_logo = get_team_info(home_id)
    away_name, away_logo = get_team_info(away_id)

    # Convert match time from string to datetime with timezone info
    match_dt = datetime.fromisoformat(datetime_str).replace(tzinfo=local_tz)

    prediction = get_user_prediction(player_id, match_id)
    selected_player_name = get_player_name(player_id)
    selected_player_id = player_id

    # Get the prediction deadline and current local time
    round_id = match["round_id"]  # ensure using correct round
    deadline_utc = get_prediction_deadline_for_round(round_id)
    deadline_local = deadline_utc.astimezone(local_tz) if deadline_utc else None
    now_local = datetime.now(timezone.utc).astimezone(local_tz)

    # Layout: Main Card
    st.markdown("<div style='margin-bottom: 20px;'>", unsafe_allow_html=True)
    cols = st.columns([2.5, 5, 2.5, 2])

    # Home Team
    with cols[0]:
        st.markdown("<div style='text-align:center;'>", unsafe_allow_html=True)
        if home_logo:
            st.image(home_logo, width=45)
        st.markdown(f"<div style='font-weight:600;margin-top:5px;'>{home_name}</div>", unsafe_allow_html=True)

    # Match Info Center
    with cols[1]:
        render_match_info(match_dt, status, home_score, away_score, prediction, match, return_html=False)

    # Away Team
    with cols[2]:
        st.markdown("<div style='text-align:center;'>", unsafe_allow_html=True)
        if away_logo:
            st.image(away_logo, width=45)
        st.markdown(f"<div style='font-weight:600;margin-top:5px;'>{away_name}</div>", unsafe_allow_html=True)

    # Prediction Button or Deadline Passed
    with cols[3]:
        if deadline_local and now_local < deadline_local:
            if st.button("🔮 Predict", key=f"predict_{match_id}", help="This Button is used to predict the result"):
                st.session_state.predict_match_id = match_id
                st.session_state.show_add_match_form = False
        else:
            st.markdown("<div style='color:red; font-weight:600;'>🚫 Deadline Passed</div>", unsafe_allow_html=True)

    # Show prediction input form if this match is selected
    if st.session_state.get("predict_match_id") == match_id:
        render_prediction_input(match, selected_player_name, selected_player_id, upsert_prediction, fetch_predictions_for_player)

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("<hr style='margin:10px 0;'>", unsafe_allow_html=True)





    
    
    
    
def render_rounds(player_id, round_name):
    # Fetch all rounds
    round_rows = get_all_rounds()
    round_dict = {r["name"]: r["id"] for r in round_rows}

    # Select default round
    selected_round_name = st.selectbox(
        "📅 Select a Round",
        list(round_dict.keys()),
        index=list(round_dict.keys()).index(round_name)
    )
    selected_round_id = round_dict[selected_round_name]

    # Fetch matches for selected round
    matches = get_matches_by_round(selected_round_id)

    st.markdown(f"## 🏟️ Matches in {selected_round_name}")

    if not matches:
        st.info("No matches found for this round.")
        return

    matches.sort(key=itemgetter('league_name'))
    for league, group in groupby(matches, key=itemgetter('league_name')):
        st.markdown(f"""🏆 {league}""", unsafe_allow_html=True)
        for match in group:
            render_match_card(match, player_id, selected_round_id)




def render_match_timing(match_time: datetime):
    # 🟡 Assume the match_time from DB is stored as local Cairo time (naive), so localize it properly
    if match_time.tzinfo is None:
        match_time = match_time.replace(tzinfo=local_tz)  # 👈 Don't assume UTC, use Cairo
    else:
        match_time = match_time.astimezone(local_tz)

    now = datetime.now(timezone.utc).astimezone(local_tz)

    time_left = match_time - now
    total_seconds_left = time_left.total_seconds()
    hours_left = total_seconds_left / 3600
    minutes_left = total_seconds_left / 60
    match_date = match_time.date()

    # Display logic
    if 0 < minutes_left < 1:
        date_display = "<span style='color: orange; font-weight: bold;'>⏰ Less than 1 min!</span>"
    elif 0 < hours_left <= 1:
        date_display = f"<span style='color: orange; font-weight: bold;'>⏰ {int(minutes_left)} min left</span>"
    elif 1 < hours_left <= 10:
        date_display = f"<span style='color: orange; font-weight: bold;'>⏰ {int(hours_left)} hours left</span>"
    elif match_date == now.date() and hours_left > 0:
        date_display = "<span style='color: red; font-weight: bold;'>🔴 Today</span>"
    elif match_date == now.date() + timedelta(days=1):
        date_display = "<span style='color: blue; font-weight: bold;'>🌙 Tomorrow</span>"
    else:
        date_display = f"<span>📅 {match_time.strftime('%A, %B %d, %Y')}</span>"

    return date_display
