import streamlit as st
from modules import under_update
from auto_push_db import auto_push_db
from controllers.predictions_controllers import format_time_left, get_next_round_info
from send_email import send_reminder_email_to_all
from controllers.manage_predictions_controller import update_scores_for_match
from utils import fetch_all
def render():
    st.markdown("""
        <h2 style="text-align:center; color:#3b82f6; font-weight:700;">⚙️ Admin Tournament Tools</h2>
        <p style="text-align:center; color:gray;">Manage tournament operations and database tasks with ease</p>
        <hr style="border: 1px solid #ddd; margin-bottom: 2rem;">
    """, unsafe_allow_html=True)

    # Admin Control Panel Buttons (Centered Layout)
    col1, col2, col3, col4, col5, col6 = st.columns([1, 1, 1, 1, 1, 1])

    with col1:
        if st.button("🔄 Reset Tournament", help="This will reset all tournament data."):
            st.toast("⚠️ Reset Tournament is not active yet", icon="⚠️")

    with col2:
        if st.button("🛑 End Tournament", help="This will close the tournament permanently."):
            st.toast("⛔ End Tournament is not active yet", icon="⛔")

    with col3:
        if st.button("📤 Push Data", type="primary", help="Push current data to the remote database."):
            with st.spinner("🔄 Syncing with database..."):
                auto_push_db()
                st.success("✅ Data pushed to database successfully!")

    with col4:
        if st.button("📧 Send Reminder Emails", type="primary", help="Send reminder emails to all players."):
            with st.spinner("📨 Sending email reminders..."):
                round_name, deadline, match_time, match_count = get_next_round_info()
                send_reminder_email_to_all(round_name, deadline, match_time, match_count, "test")
                st.success("✅ Reminder emails sent successfully!")

    with col5:
        if st.button("🏆 Start the Cup", type="primary", help="Kick off the tournament with style!"):
            st.toast("⚠️ Start Cup is not active yet", icon="⚠️")
    
    with col6:
        if st.button("📊 Calculate Points", type="primary", help="This will calculate the score for all matches"):
            with st.spinner("🧮 Calculating points for all matches..."):
                try:
                    query = "SELECT id FROM matches"
                    matches = fetch_all(query)
                    count = 0

                    for match in matches:
                        match_id = match["id"]
                        update_scores_for_match(match_id)
                        count += 1

                    st.success(f"✅ Points successfully updated for {count} matches.")
                except Exception as e:
                    st.error(f"❌ Error while calculating points:\n{e}")
                    