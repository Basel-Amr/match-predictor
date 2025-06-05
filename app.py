import streamlit as st
from streamlit_option_menu import option_menu
import auth

from modules import profile, predictions, leaderboard, achievement, manage, cup

from controllers.players_controller import get_player_id_by_username

# Page Configuration
st.set_page_config(
    page_title="Football Cup Predictor",
    page_icon="⚽",
    layout="wide",  # wider layout for full-width text
    initial_sidebar_state="expanded"
)
st.markdown(
    """
    <style>
        [data-testid="stSidebarNav"] {
            display: none;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# 💡 Custom Font & Styling
st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@500&display=swap" rel="stylesheet">
    <style>
        html, body, [class*="css"] {
            font-family: 'Poppins', sans-serif;
        }
        .block-container {
            padding-top: 1rem;
            padding-left: 3rem;
            padding-right: 3rem;
        }
    </style>
""", unsafe_allow_html=True)
#https://media1.giphy.com/media/v1.Y2lkPTc5MGI3NjExMG5kNG8wOGlzNnhvYjEyMWlhc3dkcmlmeTN6MG91cTJmMWRvbDFmYyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/3ohA2TEUVTPWlzSD28/giphy.gif
# 🎞️ Football Animation
def show_animation():
    st.markdown(
        """
        <div style="text-align:center; margin-bottom: 25px;">
            <img src="https://media3.giphy.com/media/v1.Y2lkPTc5MGI3NjExYjFnbTd5Ymo0OG5va3d6cDI4OHl6ZnZtZTJjZ3U0aWVjbWliank0ayZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/dKdtyye7l5f44/giphy.gif" alt="Football Animation" width="300" />
        </div>
        """,
        unsafe_allow_html=True,
    )

# 🔐 Session State
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "role" not in st.session_state:
    st.session_state.role = "player"

# Main Dashboard (Tabs)
def main_page():
    show_tabs = ["Profile", "Predictions", "Leaderboard", "Achievement", "Cup"]
    icons = ["person-circle", "lightning", "trophy", "award", "trophy"]


    if st.session_state.role == "admin":
        show_tabs.append("Manage")
        icons.append("gear")

    selected_tab = option_menu(
        menu_title=None,
        options=show_tabs,
        icons=icons,
        orientation="horizontal",
        styles={
            "container": {
                "padding": "10px",
                "background-color": "#ffffff",
                "border-radius": "10px",
                "box-shadow": "0 4px 12px rgba(0, 0, 0, 0.1)"
            },
            "nav-link": {
                "font-size": "18px",
                "font-weight": "600",
                "text-align": "center",
                "color": "#1f2937",
                "margin": "0px 10px",
                "border-radius": "8px",
                "transition": "all 0.3s ease",
                "padding": "10px 18px",
            },
            "nav-link-selected": {
                "background": "linear-gradient(135deg, #3b82f6, #60a5fa)",
                "color": "white",
                "font-weight": "bold",
                "box-shadow": "0 0 10px rgba(59, 130, 246, 0.4)",
            }
        }
    )

    if selected_tab == "Profile":
        player_id = get_player_id_by_username(st.session_state.username)
        profile.render(player_id)
        #profile.render(st.session_state.username)
    elif selected_tab == "Predictions":
        predictions.render()
    elif selected_tab == "Leaderboard":
        leaderboard.render()
    elif selected_tab == "Achievement":
        achievement.render()
    elif selected_tab == "Cup":
        cup.render()
    elif selected_tab == "Manage":
        manage.render()

# App Execution
show_animation()

if not st.session_state.logged_in:
    nav_auth = option_menu(
        menu_title=None,
        options=["🔐 Login", "📝 Sign Up"],
        icons=["box-arrow-in-right", "person-plus"],
        default_index=0,
        orientation="horizontal",
        styles={
            "container": {
                "padding": "10px",
                "background-color": "#ffffff",
                "border-radius": "10px",
                "box-shadow": "0 4px 12px rgba(0, 0, 0, 0.1)"
            },
            "nav-link": {
                "font-size": "20px",
                "font-weight": "600",
                "text-align": "center",
                "color": "#1f2937",
                "margin": "0px 15px",
                "border-radius": "8px",
                "transition": "all 0.3s ease",
                "padding": "12px 20px",
            },
            "nav-link-selected": {
                "background": "linear-gradient(135deg, #3b82f6, #60a5fa)",
                "color": "white",
                "font-weight": "bold",
                "box-shadow": "0 0 10px rgba(59, 130, 246, 0.4)",
            }
        }
    )

    if nav_auth == "🔐 Login":
        auth.login()
    else:
        auth.signup()
else:
    main_page()
