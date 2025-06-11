from db import get_connection
from utils import fetch_one

def get_achievements_by_player_id(player_id: int) -> dict:
    query = """
        SELECT total_leagues_won, total_cups_won
        FROM achievements
        WHERE player_id = ?;
    """
    row = fetch_one(query, (player_id,))
    
    if row:
        return {
            "total_leagues_won": row["total_leagues_won"],
            "total_cups_won": row["total_cups_won"]
        }
    else:
        # Return default if player has no record yet
        return {
            "total_leagues_won": 0,
            "total_cups_won": 0
        }
