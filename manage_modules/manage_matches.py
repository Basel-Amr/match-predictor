# manage_modules/manage_matches.py
import streamlit as st
import os
from datetime import datetime
import sqlite3
# Add match part
from controllers.manage_matches_controller import get_all_leagues, get_teams_by_league, add_match, check_duplicate_match, get_round_id_by_date
# View match part
from controllers.manage_matches_controller import (fetch_rounds, fetch_matches_by_round, delete_match_by_id, 
                                                   update_match_partial, fetch_leagues, fetch_teams, 
                                                   change_match_status, insert_or_replace_leg, fetch_legs_by_match_id,
                                                   fetch_stage_by_id)
from controllers.manage_predictions_controller import update_scores_for_match
from itertools import groupby
from streamlit_autorefresh import st_autorefresh
from datetime import datetime, timedelta
from render_helpers.render_matches_managing import render_manage_matches_tab
from render_helpers.render_matches_viewer import (render_match_result, render_status_tag,
                                                 render_edit_match, render_view_matches_tab
                                                )
# Icons
MANAGE_ICON = "🛠️"
VIEW_ICON = "📅"
EDIT_ICON = "✏️"  # Pencil emoji for edit
DELETE_ICON = "🗑️"  # Trash can emoji for delete

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



