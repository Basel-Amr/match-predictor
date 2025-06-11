import streamlit as st
from modules import under_update
from auto_push_db import auto_push_db

def render():
    st.markdown("""
        <h2 style="text-align:center; color:#3b82f6; font-weight:700;">⚙️ Admin Tournament Tools</h2>
        <p style="text-align:center; color:gray;">Manage tournament utilities and database functions</p>
        <hr style="border: 1px solid #ddd;">
    """, unsafe_allow_html=True)

    # Layout: Centered buttons with style
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        if st.button("🌀 Reset Tournament", help="This will reset all tournament data"):
            st.toast("⚠️ Reset Tournament is not active yet", icon="⚠️")

    with col2:
        if st.button("🚨 End Tournament", help="This will close the tournament permanently"):
            st.toast("⛔ End Tournament is not active yet", icon="⛔")

    with col3:
        if st.button("📤 Push to Database", type="primary", help="Push all current data to the remote database"):
            with st.spinner("Pushing data..."):
                auto_push_db()
                st.success("✅ Data pushed to database successfully!")
