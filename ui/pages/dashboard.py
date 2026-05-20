import streamlit as st
import pandas as pd
import html as _html
from ui.components import render_metric_card, plot_score_trend, plot_topic_performance

def _safe_level(val):
    if not val:
        return '-'
    return str(val).replace('_', ' ').title()

def _esc(value):
    return _html.escape(str(value), quote=True)

def render():
    st.markdown('<h1 style="color:var(--text-main); font-size:2.2rem; margin-bottom:0.5rem;">📊 Performance Dashboard</h1>', unsafe_allow_html=True)
    st.markdown('<p style="color:var(--text-muted); font-size:1rem; margin-bottom:1.5rem;">Your interview performance at a glance</p>', unsafe_allow_html=True)
    
    user_id = st.session_state.current_user['id']
    recent_sessions = st.session_state.mysql_store.get_recent_interviews(user_id, limit=20)
    
    completed_interviews = [s for s in recent_sessions if s.get('overall_score') is not None]
    
    if not completed_interviews:
        st.markdown("""
            <div style="background:linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%); 
                        padding:3rem; border-radius:20px; color:white; text-align:center; margin:1rem 0 2rem;">
                <div style="font-size:3rem; margin-bottom:1rem;">🎯</div>
                <h2 style="margin-bottom:0.5rem;">Welcome to AI Interview Coach</h2>
                <p style="opacity:0.9; font-size:1.05rem;">Complete your first mock interview to unlock performance analytics and progress tracking.</p>
            </div>
        """, unsafe_allow_html=True)
        if st.button("🚀 Start Your First Interview", type="primary", use_container_width=False):
            st.session_state.current_page = 'start_interview'
            st.rerun()
        return
        
    total_interviews = len(completed_interviews)
    avg_score = sum(s['overall_score'] for s in completed_interviews) / total_interviews
    
    # Try fetching the latest report for deeper analytics
    latest_report_id = completed_interviews[0]['id']
    latest_report = st.session_state.mysql_store.get_session_report_json(latest_report_id)
    
    highest_topic = "N/A"
    lowest_topic = "N/A"
    
    if latest_report and 'detailed_analysis' in latest_report:
        topics_data = latest_report['detailed_analysis'].get('by_topic', {})
        if topics_data:
            highest_topic = max(topics_data.items(), key=lambda x: x[1]['average_score'])[0].title()
            lowest_topic = min(topics_data.items(), key=lambda x: x[1]['average_score'])[0].title()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_metric_card("📝", str(total_interviews), "Total Interviews")
    with c2:
        render_metric_card("⭐", f"{avg_score:.1f}/10", "Average Score")
    with c3:
        render_metric_card("🔥", highest_topic, "Strongest Topic")
    with c4:
        render_metric_card("🔧", lowest_topic, "Weakest Topic")
        
    st.markdown("---")
    
    tab_overview, tab_recent = st.tabs(["📈 Latest Interview Deep-Dive", "📋 All Past Interviews"])
    
    with tab_overview:
        if latest_report and 'detailed_analysis' in latest_report:
            st.markdown(f"### Latest Interview Analytics (Session #{_esc(latest_report_id)})")
            col_chart1, col_chart2 = st.columns(2)
            with col_chart1:
                prog_data = latest_report['detailed_analysis'].get('progress_over_time')
                if prog_data:
                    plot_score_trend(prog_data)
            with col_chart2:
                topic_data = latest_report['detailed_analysis'].get('by_topic')
                if topic_data:
                    plot_topic_performance(topic_data)
        else:
            st.info("No detailed report available for the latest interview.")
            
    with tab_recent:
        df = pd.DataFrame([{
            "Session ID": s.get('id', '-'),
            "Date": s.get('started_at', '-'),
            "Score / 10": s.get('overall_score', '-'),
            "Performance Level": _safe_level(s.get('performance_level')),
            "Total Questions": s.get('total_questions', '-')
        } for s in completed_interviews])
        st.dataframe(df, use_container_width=True, hide_index=True)
