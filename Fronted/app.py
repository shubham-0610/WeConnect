import streamlit as st
import base64
import os
import sys
from pathlib import Path

# --- Ensure project root is in sys.path ---
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from Backend.database.table import create_table
from Backend.auth import (
    signup_user, login_user, update_photo,
    generate_otp, send_otp_email, set_reset_otp, verify_otp, reset_password,
    get_all_users, send_friend_request, get_friend_requests,
    respond_to_request, get_friends, send_message, get_messages
)

# Ensure tables exist
create_table()

# --- Helper function to show circular image ---
def show_circular_image(image_path, size=150):
    with open(image_path, "rb") as f:
        data = f.read()
    encoded = base64.b64encode(data).decode()
    st.markdown(
        f"""
        <div style="display:flex; justify-content:center; align-items:center;">
            <img src="data:image/png;base64,{encoded}" 
                 style="border-radius:50%; width:{size}px; height:{size}px; object-fit:cover;">
        </div>
        """,
        unsafe_allow_html=True
    )

# --- Helper function to render chat bubbles ---
def render_message(sender, content, timestamp, is_self=False):
    bubble_color = "#DCF8C6" if is_self else "#FFFFFF"  # greenish for self, white for others
    align = "flex-end" if is_self else "flex-start"
    text_align = "right" if is_self else "left"

    st.markdown(
        f"""
        <div style="display:flex; justify-content:{align}; margin:5px;">
            <div style="
                background-color:{bubble_color};
                padding:10px;
                border-radius:10px;
                max-width:70%;
                text-align:{text_align};
                box-shadow:0px 1px 2px rgba(0,0,0,0.2);
                font-family:Arial, sans-serif;
            ">
                <div style="font-size:13px; font-weight:bold; color:#075E54;">{sender}</div>
                <div style="font-size:14px; margin-top:2px;">{content}</div>
                <div style="font-size:10px; color:gray; margin-top:4px;">{timestamp}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

# --- App Title ---
st.title("🌐 WeConnect")

# --- Session state setup ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None

if "reset_stage" not in st.session_state:
    st.session_state.reset_stage = "request"
    st.session_state.username_reset = None

# --- Dashboard after login ---
if st.session_state.logged_in and st.session_state.user:
    user = st.session_state.user
    st.success(f"🎉 Welcome to WeConnect, {user[2]}!")  # username

    # Tabs inside dashboard
    dash_tab1, dash_tab2, dash_tab3 = st.tabs(["Profile", "Friends", "Chat"])

    # --- Profile Tab ---
    with dash_tab1:
        st.subheader("User Profile")
        st.write(f"Name: {user[1]}")
        st.write(f"Username: {user[2]}")
        st.write(f"Email: {user[3]}")

        if user[4]:
            show_circular_image(user[4], size=120)
        else:
            st.info("No photo uploaded yet.")

        uploaded_file = st.file_uploader("Upload Profile Photo", type=["jpg", "png", "jpeg"])
        if uploaded_file is not None:
            os.makedirs("uploads", exist_ok=True)
            photo_path = f"uploads/{user[2]}_{uploaded_file.name}"
            with open(photo_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            success, msg = update_photo(user[2], photo_path)
            if success:
                st.success(msg)
                st.session_state.user = (user[0], user[1], user[2], user[3], photo_path)
                st.rerun()

        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.user = None
            st.rerun()

    # --- Friends Tab ---
    with dash_tab2:
        st.subheader("All Users")
        users = get_all_users(user[2])
        for u in users:
            if st.button(f"Send Request to {u[1]}", key=f"req_{u[0]}"):
                send_friend_request(user[0], u[0])
                st.success(f"Friend request sent to {u[1]}")

        st.subheader("Incoming Requests")
        requests = get_friend_requests(user[0])
        for r in requests:
            st.write(f"Request from {r[1]} - Status: {r[2]}")
            if r[2] == "pending":
                if st.button(f"Approve {r[1]}", key=f"appr_{r[0]}"):
                    respond_to_request(r[0], "approved")
                    st.success(f"You are now friends with {r[1]}")
                if st.button(f"Decline {r[1]}", key=f"decl_{r[0]}"):
                    respond_to_request(r[0], "declined")
                    st.info(f"Declined request from {r[1]}")

        st.subheader("Friends List")
        friends = get_friends(user[0])
        for f in friends:
            st.write(f[0])

    # --- Chat Tab ---
    with dash_tab3:
        st.subheader("Chat with Friends")
        friends = get_friends(user[0])
        friend_names = [f[0] for f in friends]
        selected_friend = st.selectbox("Select a friend to chat", friend_names)
        if selected_friend:
            st.write(f"Chat with {selected_friend}")
            # Find friend_id
            all_users = get_all_users(user[2]) + [(user[0], user[2])]
            friend_id = [u[0] for u in all_users if u[1] == selected_friend][0]
            msgs = get_messages(user[0], friend_id)
            for m in msgs:
                sender, content, timestamp = m
                is_self = (sender == user[2])
                render_message(sender, content, timestamp, is_self)

            msg_input = st.text_input("Type a message...")
            if st.button("Send Message"):
                send_message(user[0], friend_id, msg_input)
                st.success("Message sent!")
                st.rerun()

# --- Signup/Login/Reset Password ---
else:
    tab1, tab2, tab3 = st.tabs(["Signup", "Login", "Reset Password"])

    with tab1:
        st.header("Create Account")
        name = st.text_input("Enter Name")
        username = st.text_input("Enter Username")
        email = st.text_input("Enter Email")
        password = st.text_input("Enter Password", type="password")

        if st.button("Signup"):
            success, message = signup_user(name, username, email, password)
            if success:
                st.success(f"Welcome to WeConnect! 🎉 {message}")
            else:
                st.error(message)

    with tab2:
        st.header("Login")
        login_username = st.text_input("Enter Username", key="login_username")
        login_password = st.text_input("Enter Password", type="password", key="login_password")

        if st.button("Login"):
            success, user = login_user(login_username, login_password)
            if success:
                st.session_state.logged_in = True
                st.session_state.user = user
                st.rerun()
            else:
                st.error("Invalid credentials")

    with tab3:
        st.header("Reset Password")

        if st.session_state.reset_stage == "request":
            username = st.text_input("Enter your username")
            email = st.text_input("Enter your registered email")
            if st.button("Send OTP"):
                otp = generate_otp()
                if set_reset_otp(username, otp):
                    success, msg = send_otp_email(email, otp)
                    if success:
                        st.session_state.reset_stage = "otp"
                        st.session_state.username_reset = username
                        st.success("OTP has been sent to your email. Please check your inbox.")
                    else:
                        st.error(msg)
                else:
                    st.error("User not found or error setting OTP.")

        elif st.session_state.reset_stage == "otp":
            otp_input = st.text_input("Enter the 6-digit OTP")
            if st.button("Verify OTP"):
                if verify_otp(st.session_state.username_reset, otp_input):
                    st.session_state.reset_stage = "newpass"
                    st.success("OTP verified! Please enter new password.")
                else:
                    st.error("Invalid OTP. Try again.")

        elif st.session_state.reset_stage == "newpass":
            new_pass = st.text_input("Enter new password", type="password")
            confirm_pass = st.text_input("Confirm new password", type="password")
            if st.button("Reset Password"):
                if new_pass == confirm_pass:
                    success, msg = reset_password(st.session_state.username_reset, new_pass)
                    if success:
                        st.success(msg)
                        st.session_state.reset_stage = "request"
                    else:
                        st.error(msg)
                else:
                    st.error("Passwords do not match.")
