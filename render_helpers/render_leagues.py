import streamlit as st
from controllers.manage_leagues_controller import (
    save_uploaded_file,get_leagues,add_league, 
    update_league, delete_league,
     update_league, get_stages_by_league, 
     update_stage, delete_stage, add_stage
    )
from db import get_connection
LEAGUE_ICON = "🏆"
TEAM_ICON = "⚽"
EDIT_ICON = "✏️"
DELETE_ICON = "🗑️"
ADD_ICON = "➕"

def render_edit_league_form(league):
    st.subheader("Edit League")

    # --- Cancel button outside the form ---
    if st.button("Cancel Edit"):
        st.session_state.status_message = "Edit cancelled."
        st.session_state.show_edit_league_form = False
        st.rerun()

    # --- League Edit Form ---
    with st.form("edit_league_form"):
        name = st.text_input("League Name", league['name'])
        country = st.text_input("Country", league['country'])
        logo = st.file_uploader("Upload Logo (optional)", type=["png", "jpg", "jpeg"])
        # can_be_draw = st.checkbox("Can be Draw", value=league['can_be_draw'])
        # two_legs = st.checkbox("Two Legs", value=league['two_legs'])
        # must_have_winner = st.checkbox("Must Have Winner", value=league['must_have_winner'])

        submitted = st.form_submit_button("Update League")

        if submitted:
            update_league(league['id'], name, country, logo)
            st.session_state.status_message = "League updated successfully."
            st.session_state.show_edit_league_form = False
            st.rerun()

    # --- Stage Management ---
    st.divider()
    st.subheader("Manage Stages")

    stages = get_stages_by_league(league['id'])

    for stage in stages:
        with st.expander(f"Stage: {stage['name']} (Order: {stage['stage_order']})", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                new_name = st.text_input("Stage Name", stage['name'], key=f"stage_name_{stage['id']}")
                new_order = st.number_input("Stage Order", min_value=1, value=stage['stage_order'], key=f"stage_order_{stage['id']}")
            with col2:
                new_draw = st.checkbox("Can Be Draw", value=stage['can_be_draw'], key=f"stage_draw_{stage['id']}")
                new_legs = st.checkbox("Two Legs", value=stage['two_legs'], key=f"stage_legs_{stage['id']}")
                new_winner = st.checkbox("Must Have Winner", value=stage['must_have_winner'], key=f"stage_winner_{stage['id']}")

            update_btn = st.button("Update Stage", key=f"update_stage_btn_{stage['id']}")
            delete_btn = st.button("Delete Stage", key=f"delete_stage_btn_{stage['id']}")

            if update_btn:
                update_stage(stage['id'], new_name, new_order, new_draw, new_legs, new_winner)
                st.success("Stage updated.")
                st.rerun()

            if delete_btn:
                delete_stage(stage['id'])
                st.success("Stage deleted.")
                st.rerun()

    # --- Add New Stage Form ---
    st.markdown("### Add New Stage")
    with st.form("add_stage_form"):
        stage_name = st.text_input("Stage Name")
        stage_order = st.number_input("Stage Order", min_value=1)
        stage_draw = st.checkbox("Can Be Draw", value=True)
        stage_legs = st.checkbox("Two Legs")
        stage_winner = st.checkbox("Must Have Winner")

        stage_submitted = st.form_submit_button("Add Stage")

        if stage_submitted:
            add_stage(league['id'], stage_name, stage_order, stage_draw, stage_legs, stage_winner)
            st.success("New stage added.")
            st.rerun()

            
            
def render_add_league_form():
    st.subheader("Add New League with Stages")

    if "stages_list" not in st.session_state:
        st.session_state.stages_list = []

    # Render "Add Stage" button outside the form to avoid form confusion
    if st.button("Add Stage"):
        st.session_state.stages_list.append({
            "name": "",
            "order": len(st.session_state.stages_list) + 1,
            "can_be_draw": True,
            "two_legs": False,
            "must_have_winner": False
        })
        st.rerun()

    with st.form("add_league_form"):
        name = st.text_input("League Name")
        country = st.text_input("Country")
        logo = st.file_uploader("Upload Logo (optional)", type=["png", "jpg", "jpeg"])
        st.markdown("---")
        st.write("### Stages")

        # Render stages from session state
        for i, stage in enumerate(st.session_state.stages_list):
            with st.expander(f"Stage {i+1}: {stage['name']} (Order: {stage['order']})", expanded=True):
                new_name = st.text_input(f"Stage Name #{i+1}", value=stage['name'], key=f"stage_name_{i}")
                new_order = st.number_input(f"Stage Order #{i+1}", min_value=1, value=stage['order'], step=1, key=f"stage_order_{i}")
                new_can_be_draw = st.checkbox(f"Can be Draw #{i+1}", value=stage['can_be_draw'], key=f"stage_can_be_draw_{i}")
                new_two_legs = st.checkbox(f"Two Legs #{i+1}", value=stage['two_legs'], key=f"stage_two_legs_{i}")
                new_must_have_winner = st.checkbox(f"Must Have Winner #{i+1}", value=stage['must_have_winner'], key=f"stage_must_have_winner_{i}")

                # Update the session state with new inputs
                st.session_state.stages_list[i] = {
                    "name": new_name,
                    "order": new_order,
                    "can_be_draw": new_can_be_draw,
                    "two_legs": new_two_legs,
                    "must_have_winner": new_must_have_winner
                }

                if st.button(f"Remove Stage #{i+1}", key=f"remove_stage_{i}"):
                    st.session_state.stages_list.pop(i)
                    st.rerun()

        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("Add League with Stages")
        with col2:
            cancel = st.form_submit_button("Cancel")

        if submitted:
            if not name:
                st.error("League name is required!")
            elif any(not s['name'] for s in st.session_state.stages_list):
                st.error("All stages must have a name!")
            else:
                try:
                    add_league(name, country, logo)

                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("SELECT id FROM leagues WHERE name = ?", (name,))
                    league_id = cursor.fetchone()[0]
                    conn.close()

                    for stage in st.session_state.stages_list:
                        add_stage(
                            league_id,
                            stage["name"],
                            stage["order"],
                            stage["can_be_draw"],
                            stage["two_legs"],
                            stage["must_have_winner"]
                        )

                    st.success(f"League '{name}' with {len(st.session_state.stages_list)} stages added successfully.")
                    st.session_state.show_add_league_form = False
                    st.session_state.stages_list = []
                    st.rerun()

                except Exception as e:
                    st.error(f"Error adding league and stages: {e}")

        if cancel:
            st.session_state.show_add_league_form = False
            st.session_state.stages_list = []
            st.rerun()
            
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

            .logo-img {
                display: flex;
                align-items: center;
                justify-content: center;
                height: 100%;
            }

            .stButton > button {
                margin: auto;
                display: block;
            }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.markdown('<div class="league-container">', unsafe_allow_html=True)

    headers = ["Logo", "Name", "Country", EDIT_ICON, DELETE_ICON]
    cols = st.columns([1, 1, 1, 0.5, 0.5])
    for col, header in zip(cols, headers):
        col.markdown(f'<div class="table-header">{header}</div>', unsafe_allow_html=True)

    for league in leagues:
        st.markdown('<div class="league-row">', unsafe_allow_html=True)
        cols = st.columns([1, 1, 1, 0.5, 0.5])

        # Logo centered
        with cols[0]:
            if league.get("logo_path"):
                st.markdown('<div class="logo-img">', unsafe_allow_html=True)
                st.image(league["logo_path"], width=40)
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="centered">—</div>', unsafe_allow_html=True)

        # Text fields and flags
        cols[1].markdown(f'<div class="centered">{league["name"]}</div>', unsafe_allow_html=True)
        cols[2].markdown(f'<div class="centered">{league["country"]}</div>', unsafe_allow_html=True)

        # Action buttons centered
        with cols[3]:
            st.markdown('<div class="centered">', unsafe_allow_html=True)
            if st.button(EDIT_ICON, key=f"edit_league_{league['id']}"):
                st.session_state.edit_league_id = league['id']
                st.session_state.show_add_league_form = False
            st.markdown('</div>', unsafe_allow_html=True)

        with cols[4]:
            st.markdown('<div class="centered">', unsafe_allow_html=True)
            if st.button(DELETE_ICON, key=f"delete_league_{league['id']}"):
                delete_league(league['id'])
                st.session_state.status_message = "League deleted."
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)