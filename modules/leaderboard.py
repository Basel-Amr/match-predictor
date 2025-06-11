import streamlit as st
from datetime import datetime
from controllers.players_controller import get_player_info
from controllers.manage_predictions_controller import fetch_all_players
from utils import fetch_one


def get_current_round():
    today = datetime.now().date().isoformat()
    round_data = fetch_one("""
        SELECT name FROM rounds
        WHERE start_date <= ? AND end_date >= ?
        """, (today, today))
    return round_data['name'] if round_data else "Unknown Round"


def render(player_id):
    st.markdown("## 🏆 Ultimate Leaderboard")

    # 1. Get Current Round
    current_round = get_current_round()

    # 2. Fetch and process all players
    players = fetch_all_players()
    leaderboard = []

    for p in players:
        info = get_player_info(p['id'])
        leaderboard.append({
            'id': p['id'],
            'username': info.get('username', 'Unknown'),
            'points': info.get('total_points', 0)
        })

    leaderboard.sort(key=lambda x: x['points'], reverse=True)

    # 3. Find current player rank and info
    current_info = get_player_info(player_id)
    current_points = current_info.get('total_points', 0)
    current_username = current_info.get('username', 'You')

    current_rank = next((i + 1 for i, p in enumerate(leaderboard) if p['id'] == player_id), None)

    # 4. Display Top Cards (Round, Rank, Points)
    st.markdown(f"""
        <div style="display: flex; justify-content: space-between; margin-bottom: 30px;">
            <div style="flex: 1; margin: 5px; background: linear-gradient(135deg, #4facfe, #00f2fe); 
                        color: white; padding: 20px; border-radius: 15px; text-align: center;">
                <div style="font-size: 22px;">📅 Round</div>
                <div style="font-size: 26px; font-weight: bold;">{current_round}</div>
            </div>
            <div style="flex: 1; margin: 5px; background: linear-gradient(135deg, #43e97b, #38f9d7); 
                        color: white; padding: 20px; border-radius: 15px; text-align: center;">
                <div style="font-size: 22px;">🏅 Your Rank</div>
                <div style="font-size: 26px; font-weight: bold;">#{current_rank if current_rank else '-'}</div>
            </div>
            <div style="flex: 1; margin: 5px; background: linear-gradient(135deg, #00c6ff, #0072ff); 
                        color: white; padding: 20px; border-radius: 15px; text-align: center;
                        box-shadow: 0 4px 15px rgba(0, 114, 255, 0.3);">
                <div style="font-size: 22px;">⭐ Your Points</div>
                <div style="font-size: 26px; font-weight: bold;">{current_points}</div>
            </div>

        </div>
    """, unsafe_allow_html=True)

    # 5. Display player blocks one by one
    st.markdown("### 🪄 Player Rankings")

    for idx, player in enumerate(leaderboard[:10], start=1):  # Top 10 only
        is_you = player['id'] == player_id
        background = (
            "linear-gradient(to right, #ffe082, #ffca28)" if is_you else
            "linear-gradient(to right, #e3f2fd, #90caf9)"
        )
        box_shadow = (
            "0 0 15px 4px rgba(255, 214, 0, 0.6)" if is_you else
            "0 2px 6px rgba(0,0,0,0.1)"
        )
        text_color = "#000000" if is_you else "#1a237e"
        border = "3px solid #fdd835" if is_you else "1px solid #90caf9"
        
        st.markdown(f"""
            <div style="
                background: {background};
                border: {border};
                padding: 18px;
                margin: 12px 0;
                border-radius: 14px;
                box-shadow: {box_shadow};
                color: {text_color};
                font-weight: bold;
                font-size: 17px;
            ">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="font-size: 20px;">🏅 #{idx}</div>
                    <div style="text-align: center; flex-grow: 1;">{player['username']}</div>
                    <div style="font-size: 18px;">🎯 {player['points']} pts</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
