import streamlit as st
from controllers.manage_matches_controller import fetch_stage_by_id

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

def input_scores_and_penalty(match, prev_pred, can_be_draw, must_have_winner):
    default_home = prev_pred['predicted_home_score'] if prev_pred else 0
    default_away = prev_pred['predicted_away_score'] if prev_pred else 0
    default_penalty = prev_pred.get('predicted_penalty_winner', "None") if prev_pred else "None"

    predicted_home = st.number_input(
        "Predicted Home Score",
        min_value=0,
        max_value=20,
        step=1,
        value=default_home,
        key=f"ph_{match['id']}"
    )

    predicted_away = st.number_input(
        "Predicted Away Score",
        min_value=0,
        max_value=20,
        step=1,
        value=default_away,
        key=f"pa_{match['id']}"
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




