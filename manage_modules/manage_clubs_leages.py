# from modules import under_update
# import streamlit as st
# def render():
#     under_update.under_update_view()

import streamlit as st
import controllers.manage_clubs_leagues_controller as controller


def render():
    st.title("🏆 Manage Clubs & Leagues")
    st.markdown("---")

    # 🔍 Search bar
    search_query = st.text_input("🔍 Search leagues by name or country")
    leagues = controller.get_leagues(search_query)

    if st.button("➕ Add League"):
        st.session_state["show_add_edit_league"] = True
        st.session_state["editing_league"] = None

    # Leagues Overview Table
    st.markdown("## 📋 Leagues Overview")
    if not leagues:
        st.info("No leagues found.")
        return

    cols = st.columns([1, 3, 2, 1, 1, 1, 1, 1, 1])
    headers = ["", "Name", "Country", "Draw?", "Two Legs?", "Must Have Winner?", "Teams", "Edit", "Delete"]
    for col, header in zip(cols, headers):
        col.markdown(f"**{header}**")

    for league in leagues:
        (
            id_, name, country, logo_path,
            can_be_draw, two_legs, must_have_winner, team_count
        ) = league

        c1, c2, c3, c4, c5, c6, c7, c8, c9 = st.columns([1, 3, 2, 1, 1, 1, 1, 1, 1])

        try:
            if logo_path and logo_path.lower().endswith((".png", ".jpg", ".jpeg")):
                c1.image(logo_path, width=40)
            else:
                c1.image("assets/default_league_logo.png", width=40)
        except Exception:
            st.warning(f"⚠️ Could not load logo for {name}. Showing default.")
            c1.image("assets/default_league_logo.png", width=40)

        c2.markdown(f"**{name}**")
        c3.markdown(country or "-")
        c4.markdown("✅" if can_be_draw else "❌")
        c5.markdown("✅" if two_legs else "❌")
        c6.markdown("✅" if must_have_winner else "❌")
        c7.markdown(str(team_count or 0))

        if c8.button("✏️", key=f"edit_league_{id_}"):
            st.session_state["show_add_edit_league"] = True
            st.session_state["editing_league"] = {
                "id": id_, "name": name, "country": country,
                "logo_path": logo_path,
                "can_be_draw": can_be_draw,
                "two_legs": two_legs,
                "must_have_winner": must_have_winner
            }

        confirm_key = f"confirm_delete_league_{id_}"
        if c9.button("🗑️", key=f"delete_league_{id_}"):
            st.session_state[confirm_key] = True

        if st.session_state.get(confirm_key, False):
            st.warning(f"⚠️ Are you sure you want to delete **{name}**?")
            col_yes, col_no = st.columns([1, 1])
            with col_yes:
                if st.button("✅ Yes", key=f"yes_league_{id_}"):
                    success = controller.delete_league(id_)
                    if success:
                        st.success(f"✅ Deleted league {name}")
                    else:
                        st.error("❌ Failed to delete league.")
                    st.session_state[confirm_key] = False
                    st.rerun()
            with col_no:
                if st.button("❌ No", key=f"no_league_{id_}"):
                    st.session_state[confirm_key] = False
                    st.rerun()

    if st.session_state.get("show_add_edit_league", False):
        st.markdown("---")
        league = st.session_state.get("editing_league")
        is_editing = league is not None

        st.header("Edit League" if is_editing else "Add New League")
        with st.form("league_form"):
            name = st.text_input("League Name", value=league["name"] if is_editing else "")
            country = st.text_input("Country", value=league["country"] if is_editing else "")
            logo_file = st.file_uploader("Upload Logo", type=["png", "jpg", "jpeg"])
            can_be_draw = st.checkbox("Can Be Draw", value=bool(league["can_be_draw"]) if is_editing else True)
            two_legs = st.checkbox("Two Legs", value=bool(league["two_legs"]) if is_editing else False)
            must_have_winner = st.checkbox("Must Have Winner", value=bool(league["must_have_winner"]) if is_editing else False)

            submitted = st.form_submit_button("Save")
            canceled = st.form_submit_button("Cancel")

            if submitted:
                if is_editing:
                    success = controller.update_league(
                        league["id"], name, country, logo_file,
                        can_be_draw, two_legs, must_have_winner
                    )
                    if success:
                        st.success("League updated!")
                else:
                    new_id = controller.add_league(
                        name, country, logo_file,
                        can_be_draw, two_legs, must_have_winner
                    )
                    if new_id:
                        st.success(f"League added with ID: {new_id}")
                st.session_state["show_add_edit_league"] = False
                st.rerun()
            elif canceled:
                st.session_state["show_add_edit_league"] = False
                st.rerun()

    st.markdown("---")
    st.markdown("_✨ Use the ➕ button above to add new leagues. You can also edit or delete any league._")

