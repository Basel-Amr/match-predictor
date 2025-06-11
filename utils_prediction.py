from db import get_connection
from utils import fetch_one

def calculate_prediction_score(match, prediction):
    match_id = match['id']
    actual_home = match['home_score']
    actual_away = match['away_score']
    predicted_home = prediction['predicted_home_score']
    predicted_away = prediction['predicted_away_score']
    predicted_winner = prediction['predicted_penalty_winner']
    actual_penalty_winner_id = match['penalty_winner']

    if actual_home is None or actual_away is None:
        return 0  # Match not finished

    score = 0

    def outcome(h, a):
        return 'home' if h > a else 'away' if h < a else 'draw'

    actual_result = outcome(actual_home, actual_away)
    predicted_result = outcome(predicted_home, predicted_away)

    if actual_home == predicted_home and actual_away == predicted_away:
        score = 3
    elif actual_result == predicted_result:
        score = 1

    # 🔍 Convert actual_penalty_winner ID to team name for comparison
    actual_penalty_winner_name = None
    if actual_penalty_winner_id:
        team_row = fetch_one("SELECT name FROM teams WHERE id = ?", (actual_penalty_winner_id,))
        if team_row:
            actual_penalty_winner_name = team_row["name"]

    # ✅ Compare correctly
    if actual_penalty_winner_name and actual_penalty_winner_name == predicted_winner:
        score += 1  # Bonus point for correct penalty winner

    return score
