import streamlit as st
from datetime import datetime
from controllers.players_controller import get_player_info
from controllers.manage_predictions_controller import fetch_all_players
from utils import fetch_one
import base64
import os

def get_current_round():
    today = datetime.now().date().isoformat()
    round_data = fetch_one("""
        SELECT name FROM rounds
        WHERE start_date <= ? AND end_date >= ?
        """, (today, today))
    return round_data['name'] if round_data else "Unknown Round"

AVATAR_FOLDER = os.path.join("Assets", "Avatars")  
DEFAULT_AVATAR_PATH = os.path.join("Assets", "default_avatar.png")



def _render_circular_avatar(img_path, size=50):
    try:
        with open(img_path, "rb") as f:
            img_bytes = f.read()
            b64_img = base64.b64encode(img_bytes).decode()

        avatar_html = f"""
        <div style="
            display: flex;
            justify-content: center;
            align-items: center;
            width: {size}px;
            height: {size}px;
            border-radius: 50%;
            overflow: hidden;
            border: 2px solid #4A90E2;
            box-shadow: 0 0 4px rgba(0,0,0,0.2);
        ">
            <img src="data:image/png;base64,{b64_img}" style="width: 100%; height: auto;" />
        </div>
        """
        st.markdown(avatar_html, unsafe_allow_html=True)
    except Exception:
        st.write("👤")

def get_avatar_html(img_path, size=45):
    try:
        with open(img_path, "rb") as f:
            img_bytes = f.read()
        b64_img = base64.b64encode(img_bytes).decode()
        return f"""
        <div style="
            width: {size}px;
            height: {size}px;
            border-radius: 50%;
            overflow: hidden;
            border: 2px solid #4A90E2;
            box-shadow: 0 0 4px rgba(0,0,0,0.2);
        ">
            <img src="data:image/png;base64,{b64_img}" style="width: 100%; height: 100%; object-fit: cover;" />
        </div>
        """
    except Exception:
        return "<div style='width: 45px; height: 45px; border-radius: 50%; background: #ccc;'></div>"


def render(player_id):
    st.markdown("## 🏆 Ultimate Leaderboard")

    current_round = get_current_round()
    players = fetch_all_players()
    leaderboard = []

    for p in players:
        info = get_player_info(p['id'])
        leaderboard.append({
            'id': p['id'],
            'username': info.get('username', 'Unknown'),
            'points': info.get('total_points', 0),
            'avatar_path': info.get('avatar_path')
        })

    leaderboard.sort(key=lambda x: x['points'], reverse=True)

    current_info = get_player_info(player_id)
    current_points = current_info.get('total_points', 0)
    current_username = current_info.get('username', 'You')
    avatar_path = current_info.get('avatar_path')
    current_rank = next((i + 1 for i, p in enumerate(leaderboard) if p['id'] == player_id), None)

    # === Top summary cards ===
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

    # === Leaderboard Cards ===
    st.markdown("### 🪄 Player Rankings")

    for idx, player in enumerate(leaderboard[:10], start=1):
        is_you = player['id'] == player_id
        background = (
            "linear-gradient(to right, #ffe082, #ffca28)" if is_you else
            "linear-gradient(to right, #e3f2fd, #90caf9)"
        )
        border = "3px solid #fdd835" if is_you else "1px solid #90caf9"
        medal = "🏅"

        box_shadow = (
            "0 0 15px 4px rgba(255, 214, 0, 0.6)" if is_you else
            "0 2px 6px rgba(0,0,0,0.1)"
        )
        text_color = "#000000" if is_you else "#1a237e"

        # Get avatar path
        avatar_filename = player.get("avatar_path")
        full_avatar_path = os.path.join(AVATAR_FOLDER, avatar_filename) if avatar_filename else DEFAULT_AVATAR_PATH

        with st.container():
            cols = st.columns([1, 1.2, 5, 2])  # Avatar, Rank, Username, Points

            with cols[0]:
                _render_circular_avatar(full_avatar_path, size=45)

            with cols[1]:
                st.markdown(f"""
                    <div style="background: {background}; border: {border}; padding: 10px;
                                border-radius: 10px; box-shadow: {box_shadow}; text-align: center;
                                color: {text_color}; font-weight: bold;">
                        {medal} #{idx}
                    </div>
                """, unsafe_allow_html=True)

            with cols[2]:
                st.markdown(f"""
                    <div style="background: {background}; border: {border}; padding: 10px;
                                border-radius: 10px; box-shadow: {box_shadow}; text-align: center;
                                color: {text_color}; font-weight: bold;">
                        {player['username']}
                    </div>
                """, unsafe_allow_html=True)

            with cols[3]:
                st.markdown(f"""
                    <div style="background: {background}; border: {border}; padding: 10px;
                                border-radius: 10px; box-shadow: {box_shadow}; text-align: center;
                                color: {text_color}; font-weight: bold;">
                        {player['points']} pts
                    </div>
                """, unsafe_allow_html=True)
