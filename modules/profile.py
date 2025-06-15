import os
import io
import base64
from PIL import Image
import streamlit as st
from streamlit_cropper import st_cropper
from controllers.players_controller import get_player_info, update_player_info, save_avatar_image, delete_player
from streamlit_extras.metric_cards import style_metric_cards
import glob

def image_to_base64(img: Image.Image) -> str:
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()
AVATAR_FOLDER = "Assets/Avatars"

def render(player_id):
    st.markdown("""
        <style>
        .animated-header {
            animation: fadeInSlide 1s ease forwards;
            font-size: 2.8rem;
            font-weight: 700;
            color: #2c3e50;
            text-align: center;
            margin-bottom: 1rem;
            font-family: 'Poppins', sans-serif;
        }
        .avatar-frame {
            width: 160px;
            height: 160px;
            border-radius: 50%;
            overflow: hidden;
            box-shadow: 0 0 20px #60a5fa;
            margin: auto;
            border: 4px solid #3b82f6;
            background-position: center;
            background-repeat: no-repeat;
            background-size: cover;
            background-color: #eee;
            animation: glow 2s infinite alternate;
        }
        @keyframes glow {
            from { box-shadow: 0 0 10px #3b82f6; }
            to { box-shadow: 0 0 25px #60a5fa; }
        }
        img.avatar-thumb {
            border-radius: 50%;
            transition: 0.3s ease-in-out;
            margin-bottom: 5px;
        }
        img.avatar-thumb:hover {
            transform: scale(1.1);
            box-shadow: 0 0 12px rgba(59,130,246,0.8);
            cursor: pointer;
        }
        .avatar-card {
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 10px;
            background-color: #f3f4f6;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
            margin-bottom: 10px;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="animated-header">⚽ My Profile ⚽</div>', unsafe_allow_html=True)
    player = get_player_info(player_id)
    if not player:
        st.error("Player info not found!")
        return

    st.markdown(f"""
    <div style="
        text-align:center;
        font-size:1.8rem;
        font-weight:700;
        color:#6366f1;
        background-color:#f0f4ff;
        padding:0.75rem 1.25rem;
        border-radius:10px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        margin-bottom:1rem;
        font-family:'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    ">
        🏅 Your Global Rank: <span style="color:#3b82f6;"> {player['rank']}</span>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 3])

    with col1:
        selected = st.session_state.get("selected_avatar_name") or player.get("avatar_path")
        preview_path = os.path.join(AVATAR_FOLDER, selected) if selected and os.path.exists(os.path.join(AVATAR_FOLDER, selected)) else None

        if preview_path:
            img = Image.open(preview_path)
            b64 = image_to_base64(img)
            st.markdown(f"<div class='avatar-frame' style='background-image:url(data:image/png;base64,{b64});'></div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='avatar-frame' style='display:flex;align-items:center;justify-content:center;color:#999;'>No Avatar</div>", unsafe_allow_html=True)

        if st.session_state.get("edit_mode", False):
            st.markdown("### 🎨 Choose Your Avatar")
            files = sorted(glob.glob(os.path.join(AVATAR_FOLDER, "*.png")) + glob.glob(os.path.join(AVATAR_FOLDER, "*.jpg")))
            if not files:
                st.warning("Add avatar images to Assets/Avatars folder.")
            else:
                gallery_cols = st.columns(4)
                for idx, fpath in enumerate(files):
                    fname = os.path.basename(fpath)
                    img = Image.open(fpath).resize((100, 100))
                    b64 = image_to_base64(img)
                    border = "4px solid #3b82f6" if fname == st.session_state.get("selected_avatar_name") else "2px solid #ccc"
                    with gallery_cols[idx % 4]:
                        st.markdown(f"<div class='avatar-card'>", unsafe_allow_html=True)
                        if st.button("", key=f"sel_{fname}", help=fname):
                            st.session_state.selected_avatar_name = fname
                            st.rerun()
                        st.markdown(
                            f"<img class='avatar-thumb' src='data:image/png;base64,{b64}' style='width:100px;height:100px;border:{border};'/>",
                            unsafe_allow_html=True
                        )
                        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown(f"**👤 Name:** {player['username']}")
        st.markdown(f"**📧 Email:** {player['email']}")
        st.markdown(f"**🗓️ Joined:** {player['created_at']}")

    with col3:
        colA, colB, colC = st.columns(3)
        colA.metric("⭐ Points", player["total_points"])
        colB.metric("🏆 Leagues", player["total_leagues_won"])
        colC.metric("🥇 Cups", player["total_cups_won"])
        style_metric_cards(
            background_color="#ff9f9",
            border_left_color="#6366f1",
            border_color="#e5e7eb",
            border_radius_px=10,
            box_shadow=True,
        )

    # Toggle edit mode
    if st.button("✏️ Edit Profile"):
        st.session_state.edit_mode = not st.session_state.get("edit_mode", False)
        if not st.session_state.edit_mode:
            for key in ["selected_avatar_name", "confirm_delete"]:
                st.session_state.pop(key, None)
        st.rerun()

    # ============ 🔧 Edit Form ============ #
    if st.session_state.get("edit_mode", False):
        st.subheader("✍️ Edit Your Information")
        new_username = st.text_input("👤 Name", value=player['username'])
        new_email = st.text_input("📧 Email", value=player['email'])
        new_password = st.text_input("🔑 Password", value="", type="password")

        if st.button("💾 Save Changes"):
            new_avatar_name = st.session_state.get("selected_avatar_name", player.get("avatar_path"))

            success = update_player_info(
                player_id,
                username=new_username,
                email=new_email,
                password=new_password if new_password else None,
                avatar_path=new_avatar_name,
                avatar_url=f"/avatars/{new_avatar_name}" if new_avatar_name else None
            )

            if success:
                st.success("✅ Profile updated successfully!")
                st.session_state.edit_mode = False
                st.session_state.username = new_username
                st.session_state.pop("selected_avatar_name", None)
                st.rerun()
            else:
                st.error("❌ Failed to update profile. Please try again.")

    # Delete section
    if st.button("🗑️ Delete My Account", key="delete_account"):
        st.session_state.show_confirm_delete = True

    if st.session_state.get("show_confirm_delete", False):
        confirmed = st.checkbox("⚠️ Are you sure you want to delete your account? This action cannot be undone.", key="confirm_delete")
        if confirmed:
            if st.button("🔥 Confirm Delete", key="confirm_delete_btn"):
                if delete_player(player_id):
                    st.success("🗑️ Account deleted successfully.")
                    for key in list(st.session_state.keys()):
                        del st.session_state[key]
                    return
                else:
                    st.error("❌ Failed to delete account.")

