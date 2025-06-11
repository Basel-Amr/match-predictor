import streamlit as st
from controllers.manage_matches_controller import fetch_stage_by_id
from utils import fetch_one

def select_player(match, player_options):
    st.markdown("### Enter Your Prediction")
    selected_player = st.selectbox(
        "Select Player",
        list(player_options.keys()),
        key=f"player_select_{match['id']}"
    )
    return selected_player, player_options[selected_player]

def fetch_and_get_prev_pred(selected_player_id, match_id, fetch_predictions_for_player):
    predictions = fetch_predictions_for_player(selected_player_id)
    pred_dict = {pred['match_id']: pred for pred in predictions}
    return pred_dict.get(match_id)

def input_scores_and_penalty(match, prev_pred, can_be_draw, must_have_winner,key_suffix=""):
    default_home = prev_pred['predicted_home_score'] if prev_pred else 0
    default_away = prev_pred['predicted_away_score'] if prev_pred else 0
    default_penalty = prev_pred.get('predicted_penalty_winner', "None") if prev_pred else "None"

    predicted_home = st.number_input(
        "Predicted Home Score",
        min_value=0,
        max_value=10,
        step=1,
        value=default_home,
        key=f"ph_{match['id']}_{key_suffix}"
    )

    predicted_away = st.number_input(
        "Predicted Away Score",
        min_value=0,
        max_value=10,
        step=1,
        value=default_away,
        key=f"pa_{match['id']}{key_suffix}"
    )

    is_draw = predicted_home == predicted_away

    if is_draw and can_be_draw and must_have_winner:
        penalty_options = ["None", match['home_team_name'], match['away_team_name']]
        if default_penalty not in penalty_options:
            default_penalty = "None"

        penalty_winner = st.selectbox(
            "Penalty Winner (required because match must have a winner)",
            penalty_options,
            index=penalty_options.index(default_penalty),
            key=f"penalty_{match['id']}"
        )
    else:
        st.markdown(
            "<i>Penalty winner selection is only needed for draw matches that must have a winner.</i>",
            unsafe_allow_html=True
        )
        penalty_winner = "None"

    return predicted_home, predicted_away, penalty_winner


def render_prediction_input(match, selected_player, selected_player_id, upsert_prediction, fetch_predictions_for_player):
    # Fetch the stage rules
    stage = fetch_stage_by_id(match["stage_id"])
    if not stage:
        st.error("Stage information not available.")
        return

    can_be_draw = stage['can_be_draw']
    must_have_winner = stage['must_have_winner']
    two_legs = stage['two_legs']

    # Skip two-leg matches for now
    if two_legs:
        st.info("Predictions for two-leg matches will be supported soon.")
        handle_two_leg_prediction(match, selected_player_id, upsert_prediction, fetch_predictions_for_player)
        return

    # Get previous prediction
    prev_pred = fetch_and_get_prev_pred(selected_player_id, match['id'], fetch_predictions_for_player)

    # Ask for score input and (maybe) penalty winner
    predicted_home, predicted_away, penalty_winner = input_scores_and_penalty(match, prev_pred,can_be_draw, must_have_winner)
    is_draw = predicted_home == predicted_away

    # Validate and save prediction
    cols_pred = st.columns([1, 1])
    if cols_pred[0].button("💾 Save Prediction", key=f"save_pred_{match['id']}"):
        if is_draw:
            if not can_be_draw:
                st.error("This match cannot end in a draw. Please adjust your prediction.")
                return
            elif must_have_winner:
                if penalty_winner == "None":
                    st.error("This match requires a winner. Please choose a penalty winner.")
                    return
            else:
                # Draw allowed and no winner required — ignore penalty winner
                penalty_winner = ""
        else:
            # If not a draw, ignore penalty winner
            penalty_winner = ""

        # Save
        winner = "" if penalty_winner == "" else penalty_winner
        upsert_prediction(selected_player_id, match['id'], predicted_home, predicted_away, winner)
        st.success("Prediction saved!")
        st.session_state.predict_match_id = None
        st.rerun()

    # Cancel button
    if cols_pred[1].button("❌ Cancel", key=f"cancel_pred_{match['id']}"):
        st.session_state.predict_match_id = None
        st.rerun()




def handle_two_leg_prediction(match, selected_player_id, upsert_prediction, fetch_predictions_for_player):
    st.subheader("🏆 Two-Leg Tie Prediction")

    # Step 1: Fetch two-leg tie record
    tie = fetch_one("""
        SELECT id, first_leg_match_id, second_leg_match_id 
        FROM two_legged_ties 
        WHERE first_leg_match_id = ? OR second_leg_match_id = ?
    """, (match['id'], match['id']))

    if not tie:
        st.error("Could not find two-leg tie information.")
        return

    is_first_leg = match['id'] == tie['first_leg_match_id']
    is_second_leg = match['id'] == tie['second_leg_match_id']

    # Step 2: First Leg
    if is_first_leg:
        st.info("This is the **first leg** of a two-legged tie.")
        prev_pred = fetch_and_get_prev_pred(selected_player_id, match['id'], fetch_predictions_for_player)
        predicted_home, predicted_away, _ = input_scores_and_penalty(
            match, prev_pred, can_be_draw=True, must_have_winner=False, key_suffix="leg1"
        )

        if st.button("💾 Save First Leg Prediction", key=f"save_leg1_{match['id']}"):
            upsert_prediction(selected_player_id, match['id'], predicted_home, predicted_away, "")
            st.success("First leg prediction saved!")
            st.session_state.predict_match_id = None
            st.rerun()

    # Step 3: Second Leg
    elif is_second_leg:
        st.info("This is the **second leg** of a two-legged tie.")

        leg1 = fetch_one("SELECT * FROM matches WHERE id = ?", (tie['first_leg_match_id'],))
        if not leg1 or leg1['home_score'] is None or leg1['away_score'] is None:
            st.warning("First leg result is not yet available.")
            return

        team1 = leg1['home_team_id']
        team2 = leg1['away_team_id']

        team1_name = fetch_one("SELECT name FROM teams WHERE id = ?", (team1,))['name']
        team2_name = fetch_one("SELECT name FROM teams WHERE id = ?", (team2,))['name']
        st.markdown(f"**First Leg Result:** {team1_name} {leg1['home_score']} - {leg1['away_score']} {team2_name}")

        prev_pred = fetch_and_get_prev_pred(selected_player_id, match['id'], fetch_predictions_for_player)
        
        # We don't know if penalties are needed yet
        predicted_home, predicted_away, _ = input_scores_and_penalty(
            match, prev_pred, can_be_draw=True, must_have_winner=False, key_suffix="leg2"
        )

        # Compute aggregate
        agg_team1 = leg1['home_score'] + predicted_away
        agg_team2 = leg1['away_score'] + predicted_home
        
        st.markdown(f"**Aggregate Result:** {team1_name} {agg_team1} - {agg_team2} {team2_name}")

        penalty_winner = ""
        if agg_team1 == agg_team2:
            st.warning("The tie is drawn on aggregate. Please choose a penalty winner.")
            penalty_winner = st.selectbox(
                "Penalty Winner (required because match must have a winner)",
                options=["None", team1_name, team2_name],
                key=f"penalty_winner_{match['id']}"
            )

            if penalty_winner == "None":
                st.error("You must select a penalty winner.")
                return

        if st.button("💾 Save Second Leg Prediction", key=f"save_leg2_{match['id']}"):
            winner = penalty_winner if agg_team1 == agg_team2 else (team1_name if agg_team1 > agg_team2 else team2_name)
            upsert_prediction(selected_player_id, match['id'], predicted_home, predicted_away, winner)
            st.success("Second leg prediction saved!")
            st.session_state.predict_match_id = None
            st.rerun()

