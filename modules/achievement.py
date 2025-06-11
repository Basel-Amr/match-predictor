from modules import under_update
from controllers.players_controller import get_player_info
from controllers.manage_predictions_controller import fetch_all_players
from controllers.achievements_controller import get_achievements_by_player_id
import streamlit as st

def display_achievements(achievements, is_you, username):
    background = (
        "linear-gradient(to right, #b9f6ca, #00e676)" if is_you else
        "linear-gradient(to right, #f1f8e9, #aed581)"
    )
    box_shadow = (
        "0 0 15px 4px rgba(0, 230, 118, 0.5)" if is_you else
        "0 2px 6px rgba(0,0,0,0.1)"
    )
    border = "3px solid #00c853" if is_you else "1px solid #aed581"
    text_color = "#1b5e20" if is_you else "#33691e"

    st.markdown(f"""
        <div style="
            background: {background};
            border: {border};
            padding: 18px;
            margin: 15px 0;
            border-radius: 14px;
            box-shadow: {box_shadow};
            color: {text_color};
            font-weight: bold;
            font-size: 17px;
        ">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>🏅 <b>{username}</b></div>
                <div>🥇 Leagues Won: <b>{achievements.get("total_leagues_won", 0)}</b></div>
                <div>🏆 Cups Won: <b>{achievements.get("total_cups_won", 0)}</b></div>
            </div>
        </div>
    """, unsafe_allow_html=True)


def render(player_id):
    st.markdown("<h2 style='text-align:center; color:#2e7d32;'>🌟 Player Achievements Hall of Fame 🌟</h2>", unsafe_allow_html=True)
    st.markdown("---")
    # Display current user's achievement squares at the top
    current_achievements = get_achievements_by_player_id(player_id)
    st.markdown(f"""
        <div style="display: flex; justify-content: center; gap: 30px; margin-bottom: 30px;">
            <div style="background-color: #e8f5e9; padding: 20px; border-radius: 15px; box-shadow: 0 4px 8px rgba(0,0,0,0.2); text-align: center; width: 160px;">
                <div style="font-size: 32px;">🥇</div>
                <div style="font-size: 18px; color: #1b5e20;"><b>Leagues Won</b></div>
                <div style="font-size: 24px; color: #388e3c;"><b>{current_achievements['total_leagues_won']}</b></div>
            </div>
            <div style="background-color: #fff3e0; padding: 20px; border-radius: 15px; box-shadow: 0 4px 8px rgba(0,0,0,0.2); text-align: center; width: 160px;">
                <div style="font-size: 32px;">🏆</div>
                <div style="font-size: 18px; color: #e65100;"><b>Cups Won</b></div>
                <div style="font-size: 24px; color: #ef6c00;"><b>{current_achievements['total_cups_won']}</b></div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    all_players = fetch_all_players()

    # Sort players by total trophies (leagues + cups) descending
    players_with_achievements = []
    for player in all_players:
        achievements = get_achievements_by_player_id(player["id"])
        total_trophies = achievements.get("total_leagues_won", 0) + achievements.get("total_cups_won", 0)
        players_with_achievements.append({
            "player_id": player["id"],
            "username": get_player_info(player["id"])["username"],
            "achievements": achievements,
            "total_trophies": total_trophies
        })

    # Sort and show top 10
    top_players = sorted(players_with_achievements, key=lambda x: x["total_trophies"], reverse=True)[:10]

    for player in top_players:
        is_you = player["player_id"] == player_id
        display_achievements(player["achievements"], is_you, player["username"])

    st.markdown("---")
    st.markdown("<p style='text-align:center; color:gray;'>Only the top 10 are shown. Win more trophies to rise up!</p>", unsafe_allow_html=True)
