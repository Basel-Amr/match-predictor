# manage_modules/manage_matches.py

import streamlit as st

# Icons
MANAGE_ICON = "🛠️"
VIEW_ICON = "📅"

def render():
    st.markdown("""
        <style>
        .title {
            font-size: 36px;
            font-weight: bold;
            color: #1f77b4;
            text-align: center;
            margin-bottom: 20px;
        }
        .tab-style {
            padding: 15px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            background-color: #f9f9f9;
            transition: all 0.3s ease-in-out;
        }
        .tab-style:hover {
            background-color: #eef6fb;
            border-color: #1f77b4;
        }
        .emoji-header {
            font-size: 24px;
            font-weight: bold;
            color: #444;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="title">⚽ Match Management Dashboard</div>', unsafe_allow_html=True)

    tabs = st.tabs([f"{MANAGE_ICON} Manage Matches", f"{VIEW_ICON} View Matches"])

    with tabs[0]:
        st.markdown('<div class="tab-style">', unsafe_allow_html=True)
        render_manage_matches_tab()
        st.markdown('</div>', unsafe_allow_html=True)

    with tabs[1]:
        st.markdown('<div class="tab-style">', unsafe_allow_html=True)
        render_view_matches_tab()
        st.markdown('</div>', unsafe_allow_html=True)


def render_manage_matches_tab():
    st.markdown(f'<div class="emoji-header">{MANAGE_ICON} Add / Edit / Delete Matches</div>', unsafe_allow_html=True)
    st.info("Here you can manage all the matches for different rounds and leagues.")
    st.success("🧠 Upcoming: Smart autofill, validation, and round auto-grouping")
    st.write("🔧 Match management UI will go here...")


def render_view_matches_tab():
    st.markdown(f'<div class="emoji-header">{VIEW_ICON} View Matches by Round</div>', unsafe_allow_html=True)
    st.info("Browse and filter scheduled matches based on league and round.")
    st.write("📅 Match viewing UI will go here...")
