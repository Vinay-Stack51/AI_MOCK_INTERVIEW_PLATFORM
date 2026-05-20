import streamlit as st


def login_user(email, password):
    if email and password:
        st.session_state.authenticated = True
        st.session_state.current_user = {
            "id": 1,
            "name": email.split("@")[0],
            "email": email
        }
        st.session_state.current_page = "dashboard"
        st.rerun()


def render():

    st.markdown("""
        <div style="text-align:center; padding:18px 10px; margin-top: 2rem;">
            <div style="background:linear-gradient(135deg,#667eea,#764ba2);
                        width:80px; height:80px; border-radius:50%;
                        margin:0 auto 12px;
                        display:flex; align-items:center; justify-content:center;
                        box-shadow:0 8px 20px rgba(102,126,234,0.35);">
                <span style="font-size:2.4rem; color:white;">🎯</span>
            </div>
            <h1 style="margin:0; font-size:2.2rem;">Welcome Back</h1>
            <p style="color:gray; font-size:1.1rem;">
                Sign in to your AI Interview Coach account
            </p>
        </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:

        store = st.session_state.get("mysql_store")
        db_ready = st.session_state.get("db_ready", False)

        # ---------------- SAFE MODE ----------------
        if store is None or not db_ready:
            st.warning("⚠ Running in DEMO mode (No database connected)")

            with st.form("demo_login"):
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                submit = st.form_submit_button("Login")

                if submit:
                    login_user(email, password)
                    st.success("Logged in (Demo Mode)")
            return

        # ---------------- REAL DB MODE ----------------
        login_tab, signup_tab, reset_tab = st.tabs([
            "Login", "Sign Up", "Reset Password"
        ])

        # ================= LOGIN =================
        with login_tab:
            with st.form("login_form"):
                email = st.text_input("Email", key="login_email")
                password = st.text_input("Password", type="password")

                submit = st.form_submit_button("Login", type="primary")

                if submit:
                    try:
                        ok, user, msg = store.authenticate_user(email, password)

                        if ok and user:
                            st.session_state.authenticated = True
                            st.session_state.current_user = user

                            profile = store.get_profile(user["id"])
                            if profile:
                                st.session_state.user_profile = profile

                            st.session_state.current_page = "dashboard"
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)

                    except Exception as e:
                        st.error(f"Login error: {str(e)}")

        # ================= SIGNUP =================
        with signup_tab:
            with st.form("signup_form"):
                name = st.text_input("Full Name")
                email = st.text_input("Email")
                password = st.text_input("Password (min 8 chars)", type="password")

                submit = st.form_submit_button("Create Account", type="primary")

                if submit:
                    if len(password) < 8:
                        st.error("Password must be at least 8 characters.")
                    else:
                        try:
                            ok, msg = store.create_user(name, email, password)

                            if ok:
                                st.success("Account created! Go to Login tab.")
                            else:
                                st.error(msg)

                        except Exception as e:
                            st.error(f"Signup error: {str(e)}")

        # ================= RESET =================
        with reset_tab:
            st.info("Reset password flow")

            with st.form("reset_request"):
                email = st.text_input("Email")
                submit = st.form_submit_button("Get Token")

                if submit:
                    try:
                        ok, token, msg = store.request_password_reset(email)
                        st.info(msg)

                        if token:
                            st.code(token)
                    except Exception as e:
                        st.error(f"Reset error: {str(e)}")

            with st.form("reset_complete"):
                email = st.text_input("Email")
                token = st.text_input("Token")
                new_pw = st.text_input("New Password", type="password")
                confirm_pw = st.text_input("Confirm Password", type="password")

                submit = st.form_submit_button("Reset Password")

                if submit:
                    if new_pw != confirm_pw:
                        st.error("Passwords do not match")
                    else:
                        try:
                            ok, msg = store.complete_password_reset(
                                email, token, new_pw
                            )

                            if ok:
                                st.success(msg)
                            else:
                                st.error(msg)

                        except Exception as e:
                            st.error(f"Reset error: {str(e)}")
