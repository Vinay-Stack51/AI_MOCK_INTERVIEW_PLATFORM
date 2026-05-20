import streamlit as st

def render_global_css():
    # Static CSS with CSS variables — light mode is the default
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

:root {
  --primary-color: #667eea;
  --secondary-color: #764ba2;
  --bg-color: #ffffff;
  --text-main: #1e293b;
  --text-muted: #64748b;
  --card-bg: #ffffff;
  --card-border: #e2e8f0;

  --success: #10b981;
  --warning: #f59e0b;
  --error: #ef4444;

  --meet-bg: #202124;
  --meet-text: #e8eaed;
  --panel-bg: #1a1b1e;
  --panel-border: #3c4043;
}

html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }

/* Dashboard Cards */
.metric-card {
    background: var(--card-bg);
    border-radius: 14px;
    padding: 1.25rem;
    text-align: center;
    box-shadow: 0 4px 10px rgba(0,0,0,0.07);
    border-left: 4px solid var(--primary-color);
    border: 1px solid var(--card-border);
    transition: transform 0.2s;
    margin-bottom: 1rem;
}
.metric-card:hover { transform: translateY(-2px); }
.metric-value { font-size: 1.9rem; font-weight: 700; color: var(--text-main); }
.metric-label { font-size: 0.8rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px; margin-top:0.4rem; }

/* ── Badges ── */
.badge {
    display: inline-block; padding: 0.3rem 0.9rem; border-radius: 9999px;
    font-size: 0.72rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;
}
.badge-beginner     { background: rgba(251,191,36,0.2); color: #b45309; border: 1px solid rgba(251,191,36,0.3); }
.badge-intermediate { background: rgba(59,130,246,0.2); color: #1d4ed8; border: 1px solid rgba(59,130,246,0.3); }
.badge-advanced     { background: rgba(239,68,68,0.2); color: #b91c1c; border: 1px solid rgba(239,68,68,0.3); }
.badge-expert       { background: rgba(16,185,129,0.2); color: #047857; border: 1px solid rgba(16,185,129,0.3); }

/* Buttons */
.stButton > button {
    border-radius: 10px !important;
    font-weight: 600 !important;
    letter-spacing: 0.4px;
    transition: transform .2s, box-shadow .2s;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%) !important;
    color: white !important;
    border: none !important;
    box-shadow: 0 4px 8px rgba(102,126,234,0.3) !important;
}
.stButton > button[kind="primary"]:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 16px rgba(102,126,234,0.4) !important;
}

/* ── Meet header bar ── */
.meet-header {
    background: var(--meet-bg);
    color: white;
    padding: 0.75rem 1.5rem;
    border-radius: 12px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
}
.meet-title { font-size: 1rem; font-weight: 600; color: var(--meet-text); }
.meet-meta  { font-size: 0.85rem; color: #9aa0a6; }
.status-dot {
    display: inline-block; width:10px; height:10px;
    border-radius: 50%; margin-right: 6px;
}
.dot-live { background:var(--success); animation: pulse-dot 1.5s infinite; }
.dot-idle { background:#9aa0a6; }

@keyframes pulse-dot {
    0%,100% { opacity:1; transform:scale(1); }
    50% { opacity:.6; transform:scale(1.3); }
}

/* Hero Box */
.hero-box {
    background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
    padding:2.5rem 3rem; border-radius:20px; color:white;
    text-align:center; box-shadow:0 20px 40px rgba(102,126,234,0.3);
    margin: 1rem 0 2rem;
}
</style>
    """, unsafe_allow_html=True)

    # Dark mode override — only injected when user toggles dark theme in Settings
    if st.session_state.get('theme') == 'dark':
        st.markdown("""
<style>
:root {
  --bg-color: #0f172a;
  --text-main: #f8fafc;
  --text-muted: #94a3b8;
  --card-bg: #1e293b;
  --card-border: #334155;
  --meet-bg: #16181b;
}
[data-testid="stAppViewContainer"] { background-color: #0f172a !important; }
[data-testid="stHeader"] { background-color: #0f172a !important; }
[data-testid="stSidebar"] { background-color: #1e293b !important; }
[data-testid="stSidebar"] [data-testid="stMarkdown"] p,
[data-testid="stSidebar"] [data-testid="stMarkdown"] h2,
[data-testid="stSidebar"] [data-testid="stMarkdown"] h3 { color: #f8fafc !important; }
.stMarkdown p, .stMarkdown li, .stMarkdown h1, .stMarkdown h2,
.stMarkdown h3, .stMarkdown h4 { color: #f8fafc !important; }
label { color: #f8fafc !important; }
[data-testid="stForm"] { background-color: #1e293b !important; border-color: #334155 !important; }
input, textarea { background-color: #0f172a !important; color: #f8fafc !important; border-color: #334155 !important; }
[data-testid="stBottomBlockContainer"] { background-color: #0f172a !important; }
</style>
        """, unsafe_allow_html=True)


def inject_animations():
    from utils import get_typing_animation
    st.markdown(get_typing_animation(), unsafe_allow_html=True)

def render_sidebar():
    with st.sidebar:
        st.markdown("""
            <div style="text-align:center; padding:18px 10px;">
                <div style="background:linear-gradient(135deg,#667eea,#764ba2);
                            width:90px; height:90px; border-radius:50%; margin:0 auto 12px;
                            display:flex; align-items:center; justify-content:center;
                            box-shadow:0 8px 20px rgba(102,126,234,0.35);">
                    <span style="font-size:2.6rem; color:white;">🎯</span>
                </div>
                <h2 style="color:var(--text-main); margin:0; font-size:1.6rem;">Interview Coach</h2>
                <p style="color:var(--text-muted); margin:4px 0 0; font-size:0.85rem;">Professional Edition</p>
                <div style="background:linear-gradient(135deg,#667eea,#764ba2);
                            height:3px; width:50px; margin:12px auto 0; border-radius:3px;"></div>
            </div>
        """, unsafe_allow_html=True)
        st.markdown("---")

        if st.session_state.get('authenticated'):
            st.markdown("### 🧭 Navigation")
            pages = {
                "Dashboard": "dashboard",
                "Start Interview": "start_interview",
                "Interview Session": "session",
                "Performance Feedback": "feedback",
                "Interview History": "history",
                "Settings": "settings"
            }

            # Hide some pages from sidebar if not relevant at the moment
            if not st.session_state.get("interview_active"):
                pages.pop("Interview Session")
            if not st.session_state.get("interview_complete"):
                pages.pop("Performance Feedback")

            for label, page_key in pages.items():
                is_active = st.session_state.get("current_page") == page_key
                # Use plain streamlit buttons styled via css for sidebar items
                btn_type = "primary" if is_active else "secondary"
                icon = "▶" if is_active else "📄"
                if st.button(f"{icon} {label}", use_container_width=True, key=f"nav_{page_key}", type=btn_type):
                    if st.session_state.get("current_page") != page_key:
                        st.session_state.current_page = page_key
                        st.rerun()

            st.markdown("---")
            if st.button("Logout", use_container_width=True):
                from ui.state_manager import reset_interview
                reset_interview()
                st.session_state.authenticated = False
                st.session_state.current_user = None
                st.session_state.user_profile = {}
                st.session_state.current_page = 'auth'
                st.rerun()
