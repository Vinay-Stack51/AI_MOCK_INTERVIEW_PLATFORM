import streamlit as st

# Setup page config first
st.set_page_config(
    page_title="AI Interview Coach — Professional",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import dependencies after page config
from ui.state_manager import init_session_state
from ui.components.layout import render_global_css, render_sidebar, inject_animations
from ui.pages import auth, dashboard, start_interview, session, feedback, history, settings

# Initialize State
init_session_state()

# Global UI Setup
render_global_css()
inject_animations()

# Top level routing
current_page = st.session_state.get('current_page', 'auth')
authenticated = st.session_state.get('authenticated', False)

# Security redirect
if not authenticated and current_page != 'auth':
    st.session_state.current_page = 'auth'
    st.rerun()

# Side Navigation
render_sidebar()

# Render appropriate page module
if current_page == 'auth':
    auth.render()
elif current_page == 'dashboard':
    dashboard.render()
elif current_page == 'start_interview':
    start_interview.render()
elif current_page == 'session':
    session.render()
elif current_page == 'feedback':
    feedback.render()
elif current_page == 'history':
    history.render()
elif current_page == 'settings':
    settings.render()
else:
    st.error("Page not found. Please navigate from the sidebar.")

# Footer
st.markdown("---")
st.markdown("""
    <div style="text-align:center; padding:1.5rem; color:var(--text-muted); font-size:0.85rem;">
        <p style="margin:0;">🤖 AI Interview Coach — Professional Edition</p>
        <p style="font-size:0.78rem; margin-top:0.4rem;">
            Powered by Best-First Search · Forward-Chaining Evaluation · FOL Engine · STRIPS Planner<br>
        </p>
    </div>
""", unsafe_allow_html=True)
