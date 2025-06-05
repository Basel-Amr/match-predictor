import streamlit as st
from controllers import manage_players_controller as mpc
from PIL import Image
import os
import hashlib

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
    header_cols = st.columns([1, 3, 3, 2, 1, 1, 1, 1, 1])
    headers = ["Avatar", "Username", "Email", "Role", "Points", "Leagues", "Cups", "Edit", "Delete"]
    for col, header in zip(header_cols, headers):
        col.markdown(f"**{header}**")

    # Show players list
    for player in players:
        cols = st.columns([1, 3, 3, 2, 1, 1, 1, 1, 1])  # avatar, username, email, role, points, leagues, cups, edit, delete

        with cols[0]:
            avatar_url = player.get("avatar_url")
            if avatar_url:
                try:
                    st.image(avatar_url, width=40)
                except Exception:
                    _show_default_avatar()
            else:
                _show_default_avatar()

        with cols[1]:
            st.write(player["username"])

        with cols[2]:
            st.write(player["email"])

        with cols[3]:
            st.write(player["role"])

        with cols[4]:
            st.write(player.get("points", 0))

        with cols[5]:
            st.write(player.get("leagues_won", 0))

        with cols[6]:
            st.write(player.get("cups_won", 0))

        with cols[7]:
            if st.button("✏️", key=f"edit_{player['id']}"):
                st.session_state["show_add_edit_modal"] = True
                st.session_state["editing_player"] = player

        with cols[8]:
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
    img_path = os.path.join(os.path.dirname(__file__), "..", "assets", "default_avatar.png")
    try:
        img = Image.open(img_path)
        st.image(img, width=40)
    except Exception:
        st.write("👤")  # fallback emoji

def show_add_edit_modal():
    player = st.session_state.get("editing_player")
    is_editing = player is not None

    st.markdown("---")
    st.header("Edit Player" if is_editing else "Add New Player")

    with st.form("player_form"):
        username = st.text_input("Username", value=player["username"] if is_editing else "")
        email = st.text_input("Email", value=player["email"] if is_editing else "")
        role = st.selectbox("Role", ["player", "admin"], index=0 if not is_editing else (1 if player["role"] == "admin" else 0))
        password = st.text_input("Password (leave blank to keep current)", type="password")
        avatar_file = st.file_uploader("Upload Avatar", type=["png", "jpg", "jpeg"])

        submitted = st.form_submit_button("Save")
        canceled = st.form_submit_button("Cancel")

        if submitted:
            password_hash = None
            if password:
                password_hash = hashlib.sha256(password.encode()).hexdigest()

            if is_editing:
                # Remove avatar_file param for now to avoid error
                success = mpc.update_player(player["id"], username, email, role, password_hash)
                if success:
                    st.success("Player updated!")
                else:
                    st.error("Failed to update player.")
            else:
                # Remove avatar_file param for now to avoid error
                new_id = mpc.add_player(username, email, role, password_hash)
                if new_id:
                    st.success("Player added!")
                else:
                    st.error("Failed to add player.")

            st.session_state["show_add_edit_modal"] = False
            st.rerun()

        if canceled:
            st.session_state["show_add_edit_modal"] = False
            st.rerun()
