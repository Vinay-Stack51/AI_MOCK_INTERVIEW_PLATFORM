import streamlit as st
from datetime import datetime
import html as _html

def _esc(value):
    return _html.escape(str(value), quote=True)

def render():
    st.markdown('<h1 style="color:var(--text-main); font-size:2.2rem; margin-bottom:1.5rem;">⚙️ Settings & Profile</h1>', unsafe_allow_html=True)

    col_profile, col_pref = st.columns([2, 1])

    with col_profile:
        st.markdown("### 👤 Your Profile")
        with st.form("profile_form", clear_on_submit=False):
            st.markdown("##### 📋 Personal Information")
            ca, cb = st.columns(2)
            with ca:
                name = st.text_input("Full Name *", value=st.session_state.user_profile.get("name",""))
            with cb:
                email = st.text_input("Email *", value=st.session_state.user_profile.get("email",""))

            st.markdown("##### 🎯 Career Goals")
            target_role = st.selectbox("Target Role *", [
                "Software Engineer", "Data Scientist", "Backend Developer",
                "Frontend Developer", "DevOps Engineer", "Data Analyst",
                "Machine Learning Engineer", "Full Stack Developer",
                "Cloud Architect", "Product Manager", "QA Engineer"
            ])

            experience = st.radio("Experience Level *", [
                "Entry Level (0-2 years)", "Mid Level (3-5 years)",
                "Senior Level (5+ years)", "Lead/Manager (8+ years)"
            ], index=0, horizontal=False)

            st.markdown("##### 💻 Skills")
            cc, cd = st.columns(2)
            skills = st.session_state.user_profile.get("skills", [])
            with cc:
                langs = st.multiselect("Languages", ["Python","Java","JavaScript","C++","C#","Go","Rust","PHP"],
                                    default=[s for s in skills if s in ["Python","Java","JavaScript","C++","C#","Go","Rust","PHP"]])
                dbs   = st.multiselect("Databases", ["SQL","MongoDB","PostgreSQL","MySQL","Redis"],
                                    default=[s for s in skills if s in ["SQL","MongoDB","PostgreSQL","MySQL","Redis"]])
            with cd:
                fws   = st.multiselect("Frameworks", ["React","Django","Flask","Spring","Angular","TensorFlow"],
                                    default=[s for s in skills if s in ["React","Django","Flask","Spring","Angular","TensorFlow"]])
                tools = st.multiselect("Tools", ["AWS","Docker","Kubernetes","Git","Linux","Jenkins"],
                                    default=[s for s in skills if s in ["AWS","Docker","Kubernetes","Git","Linux","Jenkins"]])

            all_skills = langs + dbs + fws + tools

            _, c_mid, _ = st.columns([1,2,1])
            with c_mid:
                submitted = st.form_submit_button("🚀 SAVE PROFILE", use_container_width=True, type="primary")

            if submitted:
                errors = []
                if not name:  errors.append("Name is required")
                if not email or "@" not in email: errors.append("Valid email required")
                if len(all_skills) < 1: errors.append("Select at least 1 skill")
                if errors:
                    for e in errors: st.error(f"❌ {e}")
                else:
                    st.session_state.user_profile = {
                        "name": name, "email": email,
                        "target_role": target_role,
                        "experience_level": experience.split("(")[0].strip().lower(),
                        "skills": all_skills, "profile_complete": True,
                        "registration_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    ok, msg = st.session_state.mysql_store.save_profile(
                        st.session_state.current_user["id"], st.session_state.user_profile
                    )
                    if not ok:
                        st.error(msg)
                    else:
                        st.success("✅ Profile saved!")
                        st.balloons()
                        
    with col_pref:
        # Account info card
        user = st.session_state.current_user
        st.markdown(f"""
            <div style="background:var(--card-bg); padding:1.25rem; border-radius:12px; border:1px solid var(--card-border); margin-bottom:1rem;">
                <p style="color:var(--text-muted); font-size:0.75rem; text-transform:uppercase; letter-spacing:0.5px; margin-bottom:0.5rem;">Signed in as</p>
                <p style="color:var(--text-main); font-weight:600; font-size:1.1rem; margin:0;">{_esc(user.get('name', 'User'))}</p>
                <p style="color:var(--text-muted); font-size:0.85rem; margin:0.2rem 0 0;">{_esc(user.get('email', ''))}</p>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("### 🎨 Theme")
        current_theme = st.session_state.get('theme', 'light')
        new_dark = st.checkbox("🌙 Enable Dark Mode", value=(current_theme == 'dark'))
        if new_dark:
            st.session_state.theme = 'dark'
        else:
            st.session_state.theme = 'light'

        st.markdown("---")
        st.markdown("### 🔒 Change Password")
        with st.form("change_password_form"):
            cur_pw = st.text_input("Current password", type="password", key="chg_cur")
            new_pw = st.text_input("New password (min 8 chars)", type="password", key="chg_new")
            new_pw2 = st.text_input("Confirm new password", type="password", key="chg_new2")
            if st.form_submit_button("Update Password", use_container_width=True, type="primary"):
                if new_pw != new_pw2:
                    st.error("New passwords do not match.")
                elif len(new_pw) < 8:
                    st.error("Password must be at least 8 characters.")
                elif not st.session_state.db_ready:
                    st.error("Database not ready.")
                else:
                    ok_chg, msg_chg = st.session_state.mysql_store.change_password(
                        st.session_state.current_user["id"], cur_pw, new_pw
                    )
                    if ok_chg:
                        st.success(msg_chg)
                    else:
                        st.error(msg_chg)
