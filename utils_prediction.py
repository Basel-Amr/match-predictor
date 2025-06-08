def calculate_prediction_score(match, prediction):
    """
    match: dict with actual result and settings
    prediction: dict with predicted result
    Returns: integer score
    """

    actual_home = match['home_score']
    actual_away = match['away_score']
    predicted_home = prediction['predicted_home_score']
    predicted_away = prediction['predicted_away_score']
    predicted_winner = prediction.get('predicted_penalty_winner')

    if actual_home is None or actual_away is None:
        return 0  # Match not finished yet

    score = 0

    # Outcome logic
    def outcome(h, a):
        return 'home' if h > a else 'away' if h < a else 'draw'

    actual_result = outcome(actual_home, actual_away)
    predicted_result = outcome(predicted_home, predicted_away)

    # Full score
    if actual_home == predicted_home and actual_away == predicted_away:
        score = 3
    elif actual_result == predicted_result:
        score = 1

    # Add bonus if prediction includes penalty winner and it's needed
    if match.get('must_have_winner') == 1 and match.get('can_be_draw') == 0:
        actual_winner = match.get('actual_penalty_winner')
        if actual_result == 'draw' and actual_winner and predicted_winner:
            if predicted_winner.lower() == actual_winner.lower():
                score += 1

    return score
