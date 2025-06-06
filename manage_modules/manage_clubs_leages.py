import streamlit as st
# from controllers.manage_clubs_leagues_controller import (
#     get_leagues, add_league, update_league, delete_league,
#     get_teams, add_team, update_team, delete_team
# )
from controllers.manage_leagues_controller import (
    save_uploaded_file,get_leagues,add_league, 
    update_league, delete_league
    )
from controllers.manage_teams_controller import (
    get_teams, add_team, update_team, delete_team
)
                            
LEAGUE_ICON = "🏆"
TEAM_ICON = "⚽"
EDIT_ICON = "✏️"
DELETE_ICON = "🗑️"
ADD_ICON = "➕"

# CSS styles for coloring tables, headers, tabs, and buttons
def local_css():
    st.markdown(
        """
        <style>
        /* Sidebar title color */
        .css-1d391kg .css-1v3fvcr {
            font-weight: 700;
            font-size: 1.8rem;
            color: #1f77b4;
        }

        /* Page title */
        .page-title {
            color: #1f77b4;
            font-weight: 700;
            font-size: 2.8rem;
            margin-bottom: 0.3rem;
        }

        /* Leagues header background */
        .league-header {
            background-color: #eaf2ff;
            color: #1f4e79;
            font-weight: 700;
            padding: 10px 14px;
            border-radius: 8px;
            text-align: center;
            font-size: 1.1rem;
            border: 2px solid #1f77b4;
            margin-bottom: 10px;
        }

        /* Teams header background */
        .team-header {
            background-color: #fff0e5;
            color: #c46200;
            font-weight: 700;
            padding: 10px 14px;
            border-radius: 8px;
            text-align: center;
            font-size: 1.1rem;
            border: 2px solid #c46200;
            margin-bottom: 10px;
        }

        /* Table header cells */
        .table-header {
            background-color: #d0e1ff;
            color: #003366;
            font-weight: 700;
            padding: 8px 12px;
            border-radius: 6px;
            text-align: center;
            font-size: 1rem;
            border: 1.5px solid #a0b9ff;
        }

        .table-header-team {
            background-color: #ffe5cc;
            color: #994d00;
            font-weight: 700;
            padding: 8px 12px;
            border-radius: 6px;
            text-align: center;
            font-size: 1rem;
            border: 1.5px solid #ffbb88;
        }

        /* Table rows hover effect */
        .stDataFrame table tbody tr:hover {
            background-color: #f0f8ff !important;
        }

        /* Buttons with colors and bigger fonts */
        .stButton > button {
            border-radius: 8px;
            padding: 8px 18px;
            font-weight: 600;
            font-size: 1.1rem;
            cursor: pointer;
        }

        /* Add League button */
        .add-league-button > button {
            background-color: #1f77b4;
            color: white;
            border: none;
            width: 100%;
            margin-top: 12px;
        }
        .add-league-button > button:hover {
            background-color: #155d8a;
            color: #e0e0e0;
        }

        /* Add Team button */
        .add-team-button > button {
            background-color: #c46200;
            color: white;
            border: none;
            width: 100%;
            margin-top: 12px;
        }
        .add-team-button > button:hover {
            background-color: #8a4100;
            color: #e0e0e0;
        }

        /* Form container styling */
        .form-container {
            border: 2px solid #ccc;
            padding: 16px;
            border-radius: 10px;
            background-color: #f9f9f9;
            margin-top: 15px;
            margin-bottom: 30px;
        }

        /* Sidebar radio buttons styling for bigger tabs */
        div[data-baseweb="radio"] > label > div:first-child {
            font-size: 1.4rem !important;
            font-weight: 700 !important;
            color: #444 !important;
        }
        </style>
        """, unsafe_allow_html=True,
    )
def render_league_management():
    st.markdown(f'<h1 class="page-title">{LEAGUE_ICON} League Management</h1>', unsafe_allow_html=True)

    if st.session_state.status_message:
        st.success(st.session_state.status_message)
        st.session_state.status_message = ""

    leagues = get_leagues()
    render_league_list(leagues)

    if st.session_state.edit_league_id:
        league = next((l for l in leagues if l['id'] == st.session_state.edit_league_id), None)
        if league:
            render_edit_league_form(league)

    if st.button(f"{ADD_ICON} Add New League", key="add_league_btn"):
        st.session_state.show_add_league_form = True
        st.session_state.edit_league_id = None

    if st.session_state.show_add_league_form:
        render_add_league_form()

def render_league_list(leagues):
    st.markdown(
        """
        <style>
            .league-container {
                margin: auto;
                width: 90%;
                padding: 20px;
            }
           
            .table-header {
                font-weight: bold;
                font-size: 16px;
                padding-bottom: 5px;
                border-bottom: 2px solid #999;
                text-align: center;
            }
            .centered {
                text-align: center;
                display: flex;
                align-items: center;
                justify-content: center;
                height: 100%;
            }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.markdown('<div class="league-container">', unsafe_allow_html=True)

    headers = ["Logo", "Name", "Country", "Can be draw", "Two legs", "Must have winner", EDIT_ICON, DELETE_ICON]
    cols = st.columns([1, 1, 1, 1, 1, 1, 0.5, 0.5])
    for col, header in zip(cols, headers):
        col.markdown(f'<div class="table-header">{header}</div>', unsafe_allow_html=True)

    for league in leagues:
        st.markdown('<div class="league-row">', unsafe_allow_html=True)
        cols = st.columns([1, 1, 1, 1, 1, 1, 0.5, 0.5])

        # Logo
        with cols[0]:
            if league.get("logo_path"):
                st.image(league["logo_path"], width=40)
            else:
                st.markdown('<div class="centered">—</div>', unsafe_allow_html=True)

        # Text fields and flags
        cols[1].markdown(f'<div class="centered">{league["name"]}</div>', unsafe_allow_html=True)
        cols[2].markdown(f'<div class="centered">{league["country"]}</div>', unsafe_allow_html=True)
        cols[3].markdown(f'<div class="centered">{"✅" if league["can_be_draw"] else "❌"}</div>', unsafe_allow_html=True)
        cols[4].markdown(f'<div class="centered">{"✅" if league["two_legs"] else "❌"}</div>', unsafe_allow_html=True)
        cols[5].markdown(f'<div class="centered">{"✅" if league["must_have_winner"] else "❌"}</div>', unsafe_allow_html=True)

        # Action buttons
        if cols[6].button(EDIT_ICON, key=f"edit_league_{league['id']}"):
            st.session_state.edit_league_id = league['id']
            st.session_state.show_add_league_form = False

        if cols[7].button(DELETE_ICON, key=f"delete_league_{league['id']}"):
            delete_league(league['id'])
            st.session_state.status_message = "League deleted."
            st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


def render_add_league_form():
    st.markdown("### Add New League")
    with st.form("add_league_form"):
        name = st.text_input("Name")
        country = st.text_input("Country")
        logo_path = st.file_uploader("Upload Logo", type=["png", "jpg", "jpeg"])
        can_be_draw = st.checkbox("Can be draw")
        two_legs = st.checkbox("Two legs")
        must_have_winner = st.checkbox("Must have winner")

        if st.form_submit_button("Add League"):
            add_league(name, country, logo_path, can_be_draw, two_legs, must_have_winner)
            st.session_state.status_message = "League added successfully."
            st.session_state.show_add_league_form = False
            st.rerun()

def render_edit_league_form(league):
    st.markdown("### Edit League")
    with st.form(f"edit_league_form_{league['id']}"):
        name = st.text_input("Name", league["name"])
        country = st.text_input("Country", league["country"])
        logo_path = st.text_input("Logo Path", league.get("logo_path", ""))
        can_be_draw = st.checkbox("Can be draw", league["can_be_draw"])
        two_legs = st.checkbox("Two legs", league["two_legs"])
        must_have_winner = st.checkbox("Must have winner", league["must_have_winner"])

        if st.form_submit_button("Update League"):
            update_league(league["id"], name, country, logo_path, can_be_draw, two_legs, must_have_winner)
            st.session_state.status_message = "League updated successfully."
            st.session_state.edit_league_id = None
            st.rerun()

def render_team_management():
    # Add custom styling and container
    st.markdown(
        """
        <style>
            .league-container {
                margin: auto;
                width: 90%;
                padding: 20px;
            }
            .table-header {
                font-weight: bold;
                font-size: 16px;
                padding-bottom: 5px;
                border-bottom: 2px solid #999;
                text-align: center;
            }
            .centered {
                text-align: center;
                display: flex;
                align-items: center;
                justify-content: center;
                height: 100%;
            }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.markdown(f'<h1 class="page-title">{TEAM_ICON} Team Management</h1>', unsafe_allow_html=True)

    if st.session_state.get('status_message'):
        st.success(st.session_state.status_message)
        st.session_state.status_message = ""

    leagues = get_leagues()
    teams = get_teams()

    render_team_list(teams, leagues)

    if st.session_state.get('edit_team_id'):
        team = next((t for t in teams if t['id'] == st.session_state.edit_team_id), None)
        if team:
            render_edit_team_form(team, leagues)

    if st.button(f"{ADD_ICON} Add New Team", key="add_team_btn"):
        st.session_state.show_add_team_form = True
        st.session_state.edit_team_id = None

    if st.session_state.get('show_add_team_form'):
        render_add_team_form(leagues)


def render_team_list(teams, leagues):
    st.markdown('<div class="league-container">', unsafe_allow_html=True)

    headers = ["Logo", "Name", "Leagues", EDIT_ICON, DELETE_ICON]
    cols = st.columns([1, 3, 3, 0.5, 0.5])
    for col, header in zip(cols, headers):
        col.markdown(f'<div class="table-header">{header}</div>', unsafe_allow_html=True)

    for team in teams:
        st.markdown('<div class="row-spacer"></div>', unsafe_allow_html=True)
        cols = st.columns([1, 3, 3, 0.5, 0.5])

        # Logo
        with cols[0]:
            st.markdown('<div class="centered">', unsafe_allow_html=True)
            if team.get("logo_path"):
                st.image(team["logo_path"], width=40)
            else:
                st.write("—")
            st.markdown('</div>', unsafe_allow_html=True)

        # Name
        with cols[1]:
            st.markdown('<div class="centered">', unsafe_allow_html=True)
            st.write(team["name"])
            st.markdown('</div>', unsafe_allow_html=True)

        # Leagues
        leagues_raw = team.get("leagues", [])
        if isinstance(leagues_raw, str):
            leagues_list = [l.strip() for l in leagues_raw.split(",") if l.strip()]
        else:
            leagues_list = leagues_raw

        leagues_html = " ".join(
            f'<span style="background-color:#0078D7; color:white; padding:2px 6px; border-radius:4px; margin-right:4px; font-size:12px;">{league}</span>'
            for league in leagues_list
        )
        with cols[2]:
            st.markdown('<div class="centered">', unsafe_allow_html=True)
            st.markdown(leagues_html or "N/A", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # Edit button
        with cols[3]:
            st.markdown('<div class="centered">', unsafe_allow_html=True)
            if st.button(EDIT_ICON, key=f"edit_team_{team['id']}"):
                st.session_state.edit_team_id = team['id']
                st.session_state.show_add_team_form = False
            st.markdown('</div>', unsafe_allow_html=True)

        # Delete button
        with cols[4]:
            st.markdown('<div class="centered">', unsafe_allow_html=True)
            if st.button(DELETE_ICON, key=f"delete_team_{team['id']}"):
                delete_team(team['id'])
                st.session_state.status_message = "Team deleted."
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)






def render_add_team_form(leagues):
    st.markdown("### Add New Team")
    with st.form("add_team_form"):
        name = st.text_input("Name")
        league_options = {f"{l['name']} ({l['country']})": l['id'] for l in leagues}
        selected_leagues = st.multiselect("Leagues", options=list(league_options.keys()))
        logo_file = st.file_uploader("Upload Logo (optional)", type=['png', 'jpg', 'jpeg'])

        if st.form_submit_button("Add Team"):
            league_ids = [league_options[league] for league in selected_leagues]
            logo_path = save_uploaded_file(logo_file) if logo_file else None
            add_team(name, league_ids, logo_path)
            st.session_state.status_message = "Team added successfully."
            st.session_state.show_add_team_form = False
            st.rerun()


def render_edit_team_form(team, leagues):
    st.markdown("### Edit Team")
    with st.form(f"edit_team_form_{team['id']}"):
        name = st.text_input("Name", team["name"])
        league_options = {f"{l['name']} ({l['country']})": l['id'] for l in leagues}

        # Determine the current leagues display strings for the multiselect default
        current_leagues_ids = [l['id'] for l in leagues if l['id'] in team.get('league_ids', [])]
        current_leagues_display = [k for k, v in league_options.items() if v in current_leagues_ids]

        selected_leagues = st.multiselect("Leagues", options=list(league_options.keys()), default=current_leagues_display)
        logo_file = st.file_uploader("Upload Logo (optional)", type=['png', 'jpg', 'jpeg'])

        if st.form_submit_button("Update Team"):
            league_ids = [league_options[league] for league in selected_leagues]
            logo_path = save_uploaded_file(logo_file) if logo_file else team.get("logo_path")
            update_team(team["id"], name, league_ids, logo_path)
            st.session_state.status_message = "Team updated successfully."
            st.session_state.edit_team_id = None
            st.rerun()


# Icons
LEAGUE_ICON = "🏆"
TEAM_ICON = "👕"

def local_css():
    st.markdown("""
        <style>
            .centered-title {
                text-align: center;
                font-size: 32px;
                font-weight: bold;
                color: #1f77b4;
                margin-bottom: 30px;
            }
            .tab-container {
                margin-top: 20px;
            }
            .stTabs [role="tab"] {
                border: 2px solid #d1d1d1;
                padding: 10px;
                margin-right: 8px;
                border-radius: 5px 5px 0 0;
                background-color: #f0f2f6;
                font-weight: 600;
                color: #333;
                transition: all 0.3s ease-in-out;
            }
            .stTabs [role="tab"][aria-selected="true"] {
                background-color: #1f77b4;
                color: white;
                border-color: #1f77b4;
            }
        </style>
    """, unsafe_allow_html=True)

def render():
    local_css()

    # Centered page title
    st.markdown('<div class="centered-title">⚽ Football Prediction Admin Panel</div>', unsafe_allow_html=True)

    # Session state defaults
    if "status_message" not in st.session_state:
        st.session_state.status_message = ""
    if "show_add_league_form" not in st.session_state:
        st.session_state.show_add_league_form = False
    if "edit_league_id" not in st.session_state:
        st.session_state.edit_league_id = None
    if "show_add_team_form" not in st.session_state:
        st.session_state.show_add_team_form = False
    if "edit_team_id" not in st.session_state:
        st.session_state.edit_team_id = None

    # Centered tabs in the body instead of sidebar
    st.markdown('<div class="tab-container">', unsafe_allow_html=True)
    tabs = st.tabs([f"{LEAGUE_ICON} Leagues", f"{TEAM_ICON} Teams"])
    st.markdown('</div>', unsafe_allow_html=True)

    with tabs[0]:
        render_league_management()

    with tabs[1]:
        render_team_management()
