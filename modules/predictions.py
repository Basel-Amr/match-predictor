from modules import under_update
from controllers.predictions_controllers import format_time_left, get_next_round_info, get_predicted_match_count
from render_helpers.render_predictions_per_player import render_deadline, render_rounds
import streamlit as st
from streamlit_autorefresh import st_autorefresh

def render(player_id):
    st.markdown("## ⚽ Prediction Center")

    round_name, deadline, match_time, match_count = get_next_round_info()
    number_of_perdicted_matches = get_predicted_match_count(round_name, player_id)

    # Impressive header
    render_deadline(round_name, deadline, match_count, number_of_perdicted_matches)

    # Show all the rounds and matches
    render_rounds(player_id, round_name)
