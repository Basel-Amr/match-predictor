import os
import io
import base64
from PIL import Image
import streamlit as st
from streamlit_cropper import st_cropper
from controllers.players_controller import get_player_info, update_player_info, save_avatar_image, delete_player

def image_to_base64(img: Image.Image) -> str:
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

def render(player_id):
    st.markdown(
        """
        <style>
        /* Animate header */
        @keyframes fadeInSlide {
            0% {opacity: 0; transform: translateY(-20px);}
            100% {opacity: 1; transform: translateY(0);}
        }
        .animated-header {
            animation: fadeInSlide 1s ease forwards;
            font-size: 2.8rem;
            font-weight: 700;
            color: #2c3e50;
            text-align: center;
            margin-bottom: 1rem;
            font-family: 'Poppins', sans-serif;
        }
        /* Avatar container with rounded frame and shadow using background image */
        .avatar-frame {
            width: 160px;
            height: 160px;
            border-radius: 50%;
            overflow: hidden;
            box-shadow: 0 4px 12px rgba(0,0,0,0.25);
            margin: auto;
            border: 4px solid #3b82f6;
            transition: box-shadow 0.3s ease;
            background-position: center;
            background-repeat: no-repeat;
            background-size: cover;
            background-color: #eee;
        }
        .avatar-frame:hover {
            box-shadow: 0 8px 24px rgba(59,130,246,0.6);
        }
        /* Points box with gradient and glow */
        .points-box {
            background: linear-gradient(135deg, #3b82f6, #60a5fa);
            color: white;
            font-weight: 700;
            font-size: 2rem;
            border-radius: 15px;
            padding: 25px 30px;
            text-align: center;
            box-shadow: 0 0 15px rgba(59,130,246,0.6);
            margin: 15px auto;
            width: 180px;
            font-family: 'Poppins', sans-serif;
        }
        /* Buttons with icon and gradient */
        div.stButton > button {
            background: linear-gradient(135deg, #3b82f6, #60a5fa);
            color: white;
            font-weight: 600;
            padding: 10px 22px;
            border-radius: 8px;
            border: none;
            box-shadow: 0 4px 12px rgba(59,130,246,0.5);
            transition: all 0.3s ease;
            font-family: 'Poppins', sans-serif;
        }
        div.stButton > button:hover {
            background: linear-gradient(135deg, #2563eb, #3b82f6);
            box-shadow: 0 6px 20px rgba(59,130,246,0.8);
            cursor: pointer;
        }
        /* Input styling */
        input, textarea {
            font-family: 'Poppins', sans-serif !important;
            font-size: 1rem !important;
            padding: 8px !important;
        }
        </style>
        """, unsafe_allow_html=True)

    st.markdown('<div class="animated-header">⚽ My Profile ⚽</div>', unsafe_allow_html=True)

    player = get_player_info(player_id)
    if not player:
        st.error("Player info not found!")
        return

    col1, col2 = st.columns([1, 2])

    with col1:
        if not st.session_state.get("edit_mode", False):
            # Show avatar framed with CSS background-image to avoid black background
            avatar_path = player.get("avatar_url")
            if avatar_path and os.path.exists(avatar_path):
                img = Image.open(avatar_path)
                b64_img = image_to_base64(img)
                st.markdown(
                    f'<div class="avatar-frame" style="background-image: url(data:image/png;base64,{b64_img});"></div>',
                    unsafe_allow_html=True
                )
            else:
                # No avatar, show placeholder circle
                st.markdown(
                    '<div class="avatar-frame" style="display:flex;align-items:center;justify-content:center;color:#999;font-size:1.2rem;">No Avatar</div>',
                    unsafe_allow_html=True
                )
        else:
            # Edit mode: show only one uploader here
            uploaded_file = st.file_uploader("📸 Upload New Avatar", type=["png", "jpg", "jpeg"], key="avatar_uploader")
            cropped_img = None
            if uploaded_file:
                uploaded_file.seek(0)
                img = Image.open(uploaded_file)
                cropped_img = st_cropper(img, realtime_update=True, box_color="#3b82f6", aspect_ratio=(1, 1))
                st.image(cropped_img, width=160, caption="Preview cropped avatar")

    with col2:
        st.markdown(f"**👤 Name:** {player['username']}")
        st.markdown(f"**📧 Email:** {player['email']}")
        st.markdown(f'<div class="points-box">🏅 {player.get("total_points", 0)} Points</div>', unsafe_allow_html=True)
        st.markdown(f"**🗓️ Joined:** {player['created_at']}")

    # Edit toggle button
    if st.button("✏️ Edit Profile"):
        st.session_state.edit_mode = not st.session_state.get("edit_mode", False)
        # Clear upload & confirmation state when toggling off edit mode
        if not st.session_state.edit_mode:
            for key in ["avatar_uploader", "confirm_delete"]:
                if key in st.session_state:
                    del st.session_state[key]
        st.rerun()

    if st.session_state.get("edit_mode", False):
        st.subheader("✍️ Edit Your Information")

        new_username = st.text_input("👤 Name", value=player['username'])
        new_email = st.text_input("📧 Email", value=player['email'])
        new_password = st.text_input("🔑 Password", value="", type="password")

        # Use the cropped image from above uploader if present
        if 'cropped_img' not in locals():
            cropped_img = None

        if st.button("💾 Save Changes"):
            avatar_path = player.get("avatar_url", "")

            if cropped_img is not None:
                avatar_path = save_avatar_image(player_id, cropped_img)

            success = update_player_info(
                player_id,
                username=new_username,
                email=new_email,
                password=new_password if new_password else None,
                avatar_url=avatar_path
            )
            if success:
                st.success("✅ Profile updated successfully!")
                st.session_state.edit_mode = False
                st.session_state.username = new_username
                st.rerun()
            else:
                st.error("❌ Failed to update profile. Please try again.")

    # Delete account button and confirmation
    if st.button("🗑️ Delete My Account", key="delete_account"):
        st.session_state.show_confirm_delete = True

    if st.session_state.get("show_confirm_delete", False):
        confirmed = st.checkbox(
            "⚠️ Are you sure you want to delete your account? This action cannot be undone.",
            key="confirm_delete"
        )
        if confirmed:
            if st.button("🔥 Confirm Delete", key="confirm_delete_btn"):
                if delete_player(player_id):
                    st.success("🗑️ Account deleted successfully.")
                    for key in list(st.session_state.keys()):
                        del st.session_state[key]
                    return
                else:
                    st.error("❌ Failed to delete account.")
