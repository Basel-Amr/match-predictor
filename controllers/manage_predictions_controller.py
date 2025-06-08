from db import get_connection
from utils import execute_query, fetch_one, fetch_all

def fetch_all_players():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username FROM players ORDER BY username")
    rows = cursor.fetchall()
    return [dict(zip([column[0] for column in cursor.description], row)) for row in rows]


def fetch_grouped_matches():
    conn = get_connection()
    cursor = conn.cursor()
    query = """
    SELECT m.id, m.round_id, r.name AS round_name, m.league_id, l.name AS league_name,
           ht.name AS home_team_name, at.name AS away_team_name,
           m.match_datetime, m.status, m.home_score, m.away_score
    FROM matches m
    JOIN rounds r ON m.round_id = r.id
    JOIN leagues l ON m.league_id = l.id
    JOIN teams ht ON m.home_team_id = ht.id
    JOIN teams at ON m.away_team_id = at.id
    ORDER BY r.start_date, l.name, m.match_datetime
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    matches = [dict(zip([column[0] for column in cursor.description], row)) for row in rows]

    grouped = {}
    for match in matches:
        round_name = match['round_name']
        league_name = match['league_name']
        grouped.setdefault(round_name, {}).setdefault(league_name, []).append(match)

    return [
        {
            'round_name': round_name,
            'leagues': leagues
        }
        for round_name, leagues in grouped.items()
    ]


def fetch_predictions_for_player(player_id):
    conn = get_connection()
    cursor = conn.cursor()
    query = """
    SELECT * FROM predictions WHERE player_id = ?
    """
    cursor.execute(query, (player_id,))
    rows = cursor.fetchall()
    return [dict(zip([column[0] for column in cursor.description], row)) for row in rows]


def upsert_prediction(player_id, match_id, predicted_home_score, predicted_away_score, predicted_penalty_winner):
    conn = get_connection()
    cursor = conn.cursor()

    # Check if exists
    cursor.execute("SELECT id FROM predictions WHERE player_id = ? AND match_id = ?", (player_id, match_id))
    exists = cursor.fetchone()

    if exists:
        query = """
        UPDATE predictions
        SET predicted_home_score = ?, predicted_away_score = ?, predicted_penalty_winner = ?, updated_at = CURRENT_TIMESTAMP
        WHERE player_id = ? AND match_id = ?
        """
        cursor.execute(query, (predicted_home_score, predicted_away_score, predicted_penalty_winner, player_id, match_id))
    else:
        query = """
        INSERT INTO predictions (player_id, match_id, predicted_home_score, predicted_away_score, predicted_penalty_winner)
        VALUES (?, ?, ?, ?, ?)
        """
        cursor.execute(query, (player_id, match_id, predicted_home_score, predicted_away_score, predicted_penalty_winner))
    
    conn.commit()
    conn.close()
    
def update_scores_for_match(match_id):
    # Get match details
    match_query = "SELECT * FROM matches WHERE id = ?;"
    match = fetch_one(match_query, (match_id,))
    
    if not match or match['home_score'] is None or match['away_score'] is None:
        return  # Match not finished

    # Optional: add penalty winner info if needed
    match['must_have_winner'] = 1  # <- Get from leagues if needed
    match['can_be_draw'] = 0       # <- same
    match['actual_penalty_winner'] = fetch_actual_penalty_winner(match_id)  # implement if needed

    # Get all predictions for that match
    pred_query = "SELECT * FROM predictions WHERE match_id = ?;"
    predictions = fetch_all(pred_query, (match_id,))

    for pred in predictions:
        score = calculate_prediction_score(match, pred)
        update_query = "UPDATE predictions SET score = ? WHERE id = ?;"
        execute_query(update_query, (score, pred['id']))