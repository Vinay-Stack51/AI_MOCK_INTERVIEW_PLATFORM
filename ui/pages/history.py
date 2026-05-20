import streamlit as st
import pandas as pd

def _safe_str(val, default='-'):
    """Return a safe string from a value that may be None."""
    if val is None:
        return default
    return str(val)

def _safe_level(val):
    """Format a performance level string safely."""
    if not val:
        return '-'
    return str(val).replace('_', ' ').title()

def render():
    st.markdown('<h1 style="color:var(--text-main); font-size:2.2rem; margin-bottom:1.5rem;">🕒 Interview History</h1>', unsafe_allow_html=True)
    
    user_id = st.session_state.current_user['id']
    
    recent_sessions = st.session_state.mysql_store.get_recent_interviews(user_id, limit=50)
    
    if not recent_sessions:
        st.markdown("""
            <div style="background:var(--card-bg); border:1px solid var(--card-border); border-radius:14px; padding:2.5rem; text-align:center; margin-top:1rem;">
                <div style="font-size:3rem; margin-bottom:1rem;">📋</div>
                <h3 style="color:var(--text-main); margin-bottom:0.5rem;">No Interviews Yet</h3>
                <p style="color:var(--text-muted);">Complete your first interview to see your history here.</p>
            </div>
        """, unsafe_allow_html=True)
        return

    st.markdown("### Past Attempts")
    
    df_data = []
    for s in recent_sessions:
        df_data.append({
            "Session ID": s.get('id', '-'),
            "Date": s.get('started_at', '-'),
            "Score": _safe_str(s.get('overall_score')),
            "Questions": _safe_str(s.get('total_questions'), '0'),
            "Level": _safe_level(s.get('performance_level'))
        })
        
    df = pd.DataFrame(df_data)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    st.markdown("### View Specific Report")
    st.markdown("<p style='color:var(--text-muted); font-size:0.9rem;'>Select a completed session below to view its detailed analytics report.</p>", unsafe_allow_html=True)
    
    completed_sessions = [s for s in recent_sessions if s.get('has_report')]
    if completed_sessions:
        options = {
            f"Session #{s['id']} on {s.get('started_at', '?')} (Score: {_safe_str(s.get('overall_score'))})": s['id']
            for s in completed_sessions
        }
        
        selected_session_lbl = st.selectbox("Select Session:", list(options.keys()))
        
        if st.button("📊 Load Report", type="primary", use_container_width=True):
            selected_id = options[selected_session_lbl]
            rep = st.session_state.mysql_store.get_session_report_json(selected_id)
            if rep:
                st.session_state.report = rep
                st.session_state.interview_complete = True
                # Restore answer history so the Question Review tab works
                answers = st.session_state.mysql_store.get_session_answers(selected_id)
                st.session_state.answer_history = answers if answers else []
                st.session_state.current_page = 'feedback'
                st.rerun()
            else:
                st.error("Report data could not be retrieved from database.")
    else:
        st.info("No completed interview reports available yet.")
