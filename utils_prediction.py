from db import get_connection


def calculate_prediction_score(match, prediction):
    """
    Calculate score based on prediction and actual match result.
    If it's a cup match, we may need to check legs and penalties.
    """

    match_id = match['id']
    actual_home = match['home_score']
    actual_away = match['away_score']
    predicted_home = prediction['predicted_home_score']
    predicted_away = prediction['predicted_away_score']
    predicted_winner = prediction['predicted_penalty_winner']

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

    # --- Penalty winner logic ---
    conn = get_connection()
    cursor = conn.cursor()
    #cursor = db_connection.cursor()
    legs = cursor.execute("SELECT * FROM legs WHERE match_id = ?", (match_id,)).fetchall()

    if not legs:
        return score  # No legs found

    num_legs = len(legs)

    # If only one leg and it's a draw, check winner_team_id
    if num_legs == 1:
        leg = dict(legs[0])
        if outcome(leg['home_score'], leg['away_score']) == 'draw' and leg['winner_team_id']:
            # Fetch team name for winner_team_id
            winner_row = cursor.execute("SELECT name FROM teams WHERE id = ?", (leg['winner_team_id'],)).fetchone()
            if winner_row:
                actual_penalty_winner = winner_row[0]
                if predicted_winner and predicted_winner.lower() == actual_penalty_winner.lower():
                    score += 1

    # If two legs, check aggregate
    elif num_legs == 2:
        total_home = sum(leg['home_score'] for leg in legs)
        total_away = sum(leg['away_score'] for leg in legs)

        if outcome(total_home, total_away) == 'draw':
            # Use last leg winner_team_id
            last_leg = dict(sorted(legs, key=lambda l: l['leg_number'])[-1])
            if last_leg['winner_team_id']:
                winner_row = cursor.execute("SELECT name FROM teams WHERE id = ?", (last_leg['winner_team_id'],)).fetchone()
                if winner_row:
                    actual_penalty_winner = winner_row[0]
                    if predicted_winner and predicted_winner.lower() == actual_penalty_winner.lower():
                        score += 1

    return score