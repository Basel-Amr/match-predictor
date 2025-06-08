from modules import under_update
import streamlit as st
from datetime import datetime
from controllers.manage_predictions_controller import (
    fetch_all_players,
    fetch_grouped_matches,
    fetch_predictions_for_player,
    upsert_prediction
)

def render():
    st.title("🧠 Manage Player Predictions")

    players = fetch_all_players()
    if not players:
        st.warning("No players available.")
        return

    player_usernames = {p['id']: p['username'] for p in players}
    selected_player_id = st.selectbox("Select Player", list(player_usernames.keys()), format_func=lambda x: player_usernames[x])

    grouped_matches = fetch_grouped_matches()
    player_predictions = fetch_predictions_for_player(selected_player_id)
    prediction_map = {(p['match_id']): p for p in player_predictions}

    for round_info in grouped_matches:
        round_name = round_info['round_name']
        st.markdown(f"### 🏁 Round: {round_name}")

        for league_name, matches in round_info['leagues'].items():
            st.markdown(f"#### ⚽ League: {league_name}")
            for match in matches:
                match_id = match['id']
                home_team = match['home_team_name']
                away_team = match['away_team_name']
                match_time = datetime.fromisoformat(match['match_datetime']).strftime("%Y-%m-%d %H:%M")
                status = match['status']

                col1, col2, col3 = st.columns([4, 2, 4])
                with col1:
                    st.text(f"{home_team} vs {away_team}")
                    st.caption(f"🕒 {match_time} | Status: {status}")

                pred = prediction_map.get(match_id)
                default_home = pred['predicted_home_score'] if pred else 0
                default_away = pred['predicted_away_score'] if pred else 0
                default_winner = pred['predicted_penalty_winner'] if pred else ""

                with col2:
                    home_score = st.number_input(f"🏠 {home_team}", min_value=0, value=default_home, key=f"home_{match_id}")
                    away_score = st.number_input(f"🏃 {away_team}", min_value=0, value=default_away, key=f"away_{match_id}")

                with col3:
                    if home_score == away_score:
                        penalty_winner = st.selectbox("Penalty Winner", ["", home_team, away_team],
                            index=["", home_team, away_team].index(default_winner) if default_winner else 0,
                            key=f"penalty_{match_id}")
                    else:
                        penalty_winner = ""

                    if st.button("💾 Save", key=f"save_{match_id}"):
                        upsert_prediction(
                            player_id=selected_player_id,
                            match_id=match_id,
                            predicted_home_score=home_score,
                            predicted_away_score=away_score,
                            predicted_penalty_winner=penalty_winner
                        )
                        st.success(f"Prediction saved for match {home_team} vs {away_team}")

                    if match['home_score'] is not None and match['away_score'] is not None:
                        match_result = f"{match['home_score']}-{match['away_score']}"
                        points = f"({pred['score']})" if pred else ""
                        st.markdown(f"✅ Match Result: {match_result} {points}")

