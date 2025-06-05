import streamlit as st
from controllers import manage_players_controller as mpc
from PIL import Image

def render():
    st.title("⚽ Manage Players")
    
    # Search bar
    search_query = st.text_input("🔍 Search players by username or email", "")
    
    # Add player button triggers a session state toggle for modal form
    if st.button("➕ Add Player"):
        st.session_state["show_add_edit_modal"] = True
        st.session_state["editing_player"] = None  # no editing, just adding
    
    # Fetch players (filtered by search query)
    players = mpc.get_players(search_query)
    
    # Show players list with edit/delete buttons
    for player in players:
        cols = st.columns([1, 3, 3, 2, 1, 1])  # avatar, username, email, role, edit, delete
        
        with cols[0]:
            if player["avatar_url"]:
                st.image(player["avatar_url"], width=40)
            else:
                st.write("👤")
        
        with cols[1]:
            st.write(player["username"])
        
        with cols[2]:
            st.write(player["email"])
        
        with cols[3]:
            st.write(player["role"])
        
        with cols[4]:
            if st.button("✏️", key=f"edit_{player['id']}"):
                st.session_state["show_add_edit_modal"] = True
                st.session_state["editing_player"] = player
        
        with cols[5]:
            if st.button("🗑️", key=f"del_{player['id']}"):
                mpc.delete_player(player["id"])
                st.success("🗑️ Account deleted successfully.")
                st.rerun()
    
    # Show add/edit modal if toggled
    if st.session_state.get("show_add_edit_modal", False):
        show_add_edit_modal()

def show_add_edit_modal():
    player = st.session_state.get("editing_player")
    is_editing = player is not None
    
    st.markdown("---")
    st.header("Edit Player" if is_editing else "Add New Player")
    
    with st.form("player_form"):
        username = st.text_input("Username", value=player["username"] if is_editing else "")
        email = st.text_input("Email", value=player["email"] if is_editing else "")
        role = st.selectbox("Role", ["player", "admin"], index=0 if not is_editing else (1 if player["role"]=="admin" else 0))
        password = st.text_input("Password", type="password")
        
        submitted = st.form_submit_button("Save")
        canceled = st.form_submit_button("Cancel")
        
        if submitted:
            if is_editing:
                mpc.update_player(player["id"], username, email, role, password)
                st.success("Player updated!")
            else:
                mpc.add_player(username, email, role, password)
                st.success("Player added!")
            st.session_state["show_add_edit_modal"] = False
            st.rerun()
        
        if canceled:
            st.session_state["show_add_edit_modal"] = False
            st.rerun()
