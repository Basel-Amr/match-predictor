import streamlit as st
from controllers import manage_players_controller as mpc
from utils import fetch_one
from PIL import Image
import os
import hashlib
AVATAR_FOLDER = os.path.join("Assets", "Avatars")  
DEFAULT_AVATAR_PATH = os.path.join("Assets", "default_avatar.png")

import base64

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


def render():
    st.title("⚽ Manage Players")

    # Search bar
    search_query = st.text_input("🔍 Search players by username or email", "")

    # Add player button triggers modal
    if st.button("➕ Add Player"):
        st.session_state["show_add_edit_modal"] = True
        st.session_state["editing_player"] = None

    # Fetch players filtered by search query
    players = mpc.get_players(search_query)

    # Display table header
    header_cols = st.columns([1, 3, 3, 2, 1, 1, 1, 2, 1, 1])
    headers = ["Avatar", "Username", "Email", "Role", "Points", "Leagues", "Cups", "Last Login", "Edit", "Delete"]
    for col, header in zip(header_cols, headers):
        col.markdown(f"**{header}**")

    # Show players list
    for player in players:
        cols = st.columns([1, 3, 3, 2, 1, 1, 1, 2, 1, 1])  # avatar, username, email, role, points, leagues, cups, last login, edit, delete

        with cols[0]:
            avatar_filename = player.get("avatar_path")
            full_avatar_path = os.path.join(AVATAR_FOLDER, avatar_filename) if avatar_filename else None

            if avatar_filename and os.path.exists(full_avatar_path):
                _render_circular_avatar(full_avatar_path)
            else:
                _render_circular_avatar(DEFAULT_AVATAR_PATH)



        with cols[1]:
            st.write(player["username"])

        with cols[2]:
            st.write(player["email"])

        with cols[3]:
            st.write(player["role"])

        with cols[4]:
            st.write(player.get("total_points", 0))

        with cols[5]:
            st.write(player.get("total_leagues_won", 0))

        with cols[6]:
            st.write(player.get("total_cups_won", 0))

        with cols[7]:
            last_login = player.get("last_login_at")
            st.write(last_login if last_login else "—")

        with cols[8]:
            if st.button("✏️", key=f"edit_{player['id']}"):
                st.session_state["show_add_edit_modal"] = True
                st.session_state["editing_player"] = player

        with cols[9]:
            confirm_key = f"confirm_del_{player['id']}"
            if st.session_state.get(confirm_key, False):
                st.warning(f"⚠️ Are you sure you want to delete **{player['username']}**?")
                col_yes, col_no = st.columns([1, 1])
                with col_yes:
                    if st.button("✅ Yes", key=f"yes_{player['id']}"):
                        if mpc.delete_player(player["id"]):
                            st.success("🗑️ Account deleted successfully.")
                        else:
                            st.error("❌ Failed to delete account.")
                        st.session_state[confirm_key] = False
                        st.rerun()
                with col_no:
                    if st.button("❌ No", key=f"no_{player['id']}"):
                        st.session_state[confirm_key] = False
                        st.rerun()
            else:
                if st.button("🗑️", key=f"del_{player['id']}"):
                    st.session_state[confirm_key] = True

    # Show add/edit modal if toggled
    if st.session_state.get("show_add_edit_modal", False):
        show_add_edit_modal()

def _show_default_avatar():
    try:
        img = Image.open(DEFAULT_AVATAR_PATH)
        st.image(img, width=40)
    except Exception:
        st.write("👤")  # fallback emoji


def show_add_edit_modal():
    player = st.session_state.get("editing_player")
    is_editing = player is not None

    st.markdown("---")
    st.header("Edit Player" if is_editing else "Add New Player")

    with st.form("player_form"):
        # --- Input Fields ---
        username = st.text_input("Username", value=player["username"] if is_editing else "")
        email = st.text_input("Email", value=player["email"] if is_editing else "")
        role = st.selectbox("Role", ["player", "admin"],
                            index=0 if not is_editing else (1 if player["role"] == "admin" else 0))
        password = st.text_input("Password (leave blank to keep current)", type="password")
        avatar_file = st.file_uploader("Upload Avatar", type=["png", "jpg", "jpeg"])

        # --- Achievement Fields (if editing) ---
        achievements = fetch_one("SELECT total_leagues_won, total_cups_won FROM achievements WHERE player_id = ?",
                                 (player["id"],)) if is_editing else None

        total_leagues_won = st.number_input("Leagues Won", min_value=0,
                                            value=achievements["total_leagues_won"] if achievements else 0)
        total_cups_won = st.number_input("Cups Won", min_value=0,
                                         value=achievements["total_cups_won"] if achievements else 0)

        # --- Form Submission ---
        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("Save")
        with col2:
            canceled = st.form_submit_button("Cancel")

    # --- After Form Submission ---
    if canceled:
        st.session_state["show_add_edit_modal"] = False
        st.session_state["editing_player"] = None  # Clear the current player being edited
        st.rerun()

    if submitted:
        if is_editing:
            success = mpc.update_player(player["id"], username, email, role, password)
            if success:
                mpc.update_achievements(player["id"], total_leagues_won, total_cups_won)
                st.success("Player and achievements updated!")
            else:
                st.error("Failed to update player.")
        else:
            new_id = mpc.add_player(username, email, role, password)
            if new_id:
                mpc.update_achievements(new_id, total_leagues_won, total_cups_won)
                st.success("Player and achievements added!")
            else:
                st.error("Failed to add player.")

        st.session_state["show_add_edit_modal"] = False
        st.session_state["editing_player"] = None
        st.rerun()
