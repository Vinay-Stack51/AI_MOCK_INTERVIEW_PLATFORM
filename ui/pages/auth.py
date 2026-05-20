import streamlit as st

def render():
    st.markdown("""
        <div style="text-align:center; padding:18px 10px; margin-top: 2rem;">
            <div style="background:linear-gradient(135deg,#667eea,#764ba2);
                        width:80px; height:80px; border-radius:50%; margin:0 auto 12px;
                        display:flex; align-items:center; justify-content:center;
                        box-shadow:0 8px 20px rgba(102,126,234,0.35);">
                <span style="font-size:2.4rem; color:white;">🎯</span>
            </div>
            <h1 style="color:var(--text-main); margin:0; font-size:2.2rem;">Welcome Back</h1>
            <p style="color:var(--text-muted); font-size:1.1rem;">Sign in to your AI Interview Coach account</p>
        </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if not st.session_state.db_ready:
            st.error(f"MySQL unavailable: {st.session_state.db_message}")
            st.caption("Set MYSQL_* values in .env and restart.")
            return

        login_tab, signup_tab, reset_tab = st.tabs(["Login", "Sign Up", "Reset Password"])

        with login_tab:
            with st.form("login_form", clear_on_submit=False):
                login_email = st.text_input("Email", key="login_email")
                login_password = st.text_input("Password", type="password", key="login_password")
                st.markdown("<br>", unsafe_allow_html=True)
                login_submit = st.form_submit_button("Login", use_container_width=True, type="primary")
                if login_submit:
                    ok, user, msg = st.session_state.mysql_store.authenticate_user(login_email, login_password)
                    if ok and user:
                        st.session_state.authenticated = True
                        st.session_state.current_user = user
                        db_profile = st.session_state.mysql_store.get_profile(user["id"])
                        if db_profile:
                            st.session_state.user_profile = db_profile
                        st.session_state.current_page = "dashboard"
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

        with signup_tab:
            with st.form("signup_form", clear_on_submit=False):
                signup_name = st.text_input("Full Name", key="signup_name")
                signup_email = st.text_input("Email", key="signup_email")
                signup_password = st.text_input("Password (min 8 chars)", type="password", key="signup_password")
                st.markdown("<br>", unsafe_allow_html=True)
                signup_submit = st.form_submit_button("Create Account", use_container_width=True, type="primary")
                if signup_submit:
                    if len(signup_password) < 8:
                        st.error("Password must be at least 8 characters.")
                    else:
                        ok, msg = st.session_state.mysql_store.create_user(signup_name, signup_email, signup_password)
                        if ok:
                            st.success(msg + " Please switch to the Login tab.")
                        else:
                            st.error(msg)

        with reset_tab:
            st.caption("Request a reset token, then use it to set a new password.")
            with st.form("reset_request_form"):
                r_email = st.text_input("Your account email", key="reset_req_email")
                r_req = st.form_submit_button("Request reset token", use_container_width=True)
                if r_req:
                    ok_t, token, msg_t = st.session_state.mysql_store.request_password_reset(r_email)
                    st.info(msg_t)
                    if ok_t and token:
                        st.code(token, language=None)

            st.markdown("---")
            with st.form("reset_complete_form"):
                c_email = st.text_input("Email", key="reset_cmp_email")
                c_token = st.text_input("Reset token", key="reset_cmp_token")
                c_pw = st.text_input("New password (min 8)", type="password", key="reset_cmp_pw")
                c_pw2 = st.text_input("Confirm new password", type="password", key="reset_cmp_pw2")
                c_sub = st.form_submit_button("Set new password", use_container_width=True, type="primary")
                if c_sub:
                    if c_pw != c_pw2:
                        st.error("Passwords do not match.")
                    else:
                        ok_r, msg_r = st.session_state.mysql_store.complete_password_reset(c_email, c_token, c_pw)
                        if ok_r:
                            st.success(msg_r)
                        else:
                            st.error(msg_r)
