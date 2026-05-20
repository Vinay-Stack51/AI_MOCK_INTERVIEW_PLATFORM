import streamlit as st

def get_difficulty_color(level: str) -> str:
    level = level.lower()
    if level == 'beginner': return "rgba(251,191,36,0.2)"
    if level == 'intermediate': return "rgba(59,130,246,0.2)"
    if level == 'advanced': return "rgba(239,68,68,0.2)"
    if level == 'expert': return "rgba(16,185,129,0.2)"
    return "transparent"

def render_difficulty_badge(level: str) -> str:
    level_lower = level.lower()
    return f'<span class="badge badge-{level_lower}">{level.title()}</span>'

def render_metric_card(icon: str, value: str, label: str):
    st.markdown(f"""
        <div class="metric-card">
            <div style="font-size:1.5rem;">{icon}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-label">{label}</div>
        </div>
    """, unsafe_allow_html=True)
