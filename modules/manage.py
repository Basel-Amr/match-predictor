import streamlit as st
from streamlit_option_menu import option_menu
from manage_modules import manage_player, manage_clubs_leages, manage_matches, manage_perdictions, manage_cup, manage_tournment
def show_animation():
    st.markdown(
        """
        <div style="text-align:center; margin-bottom: 25px;">
            <img src="https://media1.giphy.com/media/v1.Y2lkPTc5MGI3NjExMG5kNG8wOGlzNnhvYjEyMWlhc3dkcmlmeTN6MG91cTJmMWRvbDFmYyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/3ohA2TEUVTPWlzSD28/giphy.gif" alt="Football Animation" width="300" />
        </div>
        """,
        unsafe_allow_html=True,
    )
def render():
    # Animated Header (Using a GIF)
    show_animation()

    # Navigation Tabs
    sub_tab = option_menu(
        menu_title=None,
        options=[
            "Manage Players", 
            "Manage Clubs & Leagues", 
            "Manage Matches", 
            "Manage Prediction", 
            "Manage Cup", 
            "Manage Tournament"
        ],
        icons=[
            "people-fill", 
            "shield-shaded", 
            "calendar2-week", 
            "graph-up", 
            "award", 
            "trophy"
        ],
        orientation="horizontal",
        styles={
            "container": {
                "padding": "10px",
                "background-color": "#f0f4f8",
                "border-radius": "8px"
            },
            "nav-link": {
                "font-size": "16px",
                "font-weight": "600",
                "margin": "0px 6px",
                "border-radius": "8px",
                "padding": "10px 18px",
                "color": "#1f2937"
            },
            "nav-link-selected": {
                "background-color": "#3b82f6",
                "color": "white",
                "font-weight": "bold",
                "box-shadow": "0 0 8px rgba(59, 130, 246, 0.4)",
            }
        }
    )

    # Subsection Render
    if sub_tab == "Manage Players":
        st.markdown("### 👥 Manage Players")
        st.success("Here you can **add**, **update**, or **delete** player accounts and avatars.")
        manage_player.render()

    elif sub_tab == "Manage Clubs & Leagues":
        st.markdown("### 🏟️ Manage Clubs & Leagues")
        st.info("Add or update football clubs, assign them to leagues, and maintain hierarchy.")
        manage_clubs_leages.render()
    elif sub_tab == "Manage Matches":
        st.markdown("### 📅 Manage Matches")
        st.warning("Organize upcoming fixtures, set results, and update live match data.")
        manage_matches.render()
    elif sub_tab == "Manage Prediction":
        st.markdown("### 🔮 Manage Predictions")
        st.info("Control user prediction logic, evaluate scores, and audit prediction history.")
        manage_perdictions.render()
    elif sub_tab == "Manage Cup":
        st.markdown("### 🏆 Manage Cup")
        st.success("Setup cup rules, teams, knockout stages, and update match outcomes.")
        manage_cup.render()
    elif sub_tab == "Manage Tournament":
        st.markdown("### 🎯 Manage Tournament")
        st.warning("Design and organize league or group tournaments with scheduling and stats.")
        manage_tournment.render()