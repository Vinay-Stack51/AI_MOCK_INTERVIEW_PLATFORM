import streamlit as st
from datetime import datetime
from ui.state_manager import (
    reset_interview, STRIPS_AVAILABLE, PROLOG_AVAILABLE,
    MINIMAX_AVAILABLE, WUMPUS_AVAILABLE
)
from interview_planner_csp import ConstraintSatisfactionPlanner

# Import STRIPS planner for session initialization
try:
    from strips_planner import GoalStackPlanner, get_strips_actions
except ImportError:
    pass

try:
    from prolog_kb import PrologKnowledgeBase
except ImportError:
    pass

def render():
    st.markdown('<h1 style="color:var(--text-main); font-size:2.2rem; margin-bottom:1.5rem;">🚀 Start Interview</h1>', unsafe_allow_html=True)

    if not st.session_state.user_profile.get("profile_complete", False):
        st.warning("Please complete your profile in the Settings menu before starting an interview.")
        if st.button("Go to Settings", type="primary"):
            st.session_state.current_page = 'settings'
            st.rerun()
        return

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("""
            <div style="background:var(--card-bg); padding:1.5rem; border-radius:14px; border:1px solid var(--card-border); margin-bottom:1.5rem;">
                <h3 style="color:var(--text-main); margin-top:0;">Configure Your Session</h3>
                <p style="color:var(--text-muted); font-size:0.95rem;">Select your interview parameters and preferences below.</p>
            </div>
        """, unsafe_allow_html=True)

        with st.container():
            st.markdown("### 🧠 Core Settings")
            st.checkbox("⚙️ Use Pre-Planned Syllabus (CSP & Backtracking)", value=False, key="csp_toggle")
            st.checkbox("⚡ Enable AI-Enhanced Mode (Gemini)", value=False, key="ai_enhanced_mode")

            st.markdown("### 🔬 Advanced Algorithm Settings")
            if MINIMAX_AVAILABLE:
                st.checkbox("🎮 Adversarial Mode (Minimax α-β)",
                    value=False, key="ai_adversarial_mode",
                    help="AI will try to pick the hardest questions to challenge you.")
            if WUMPUS_AVAILABLE:
                st.checkbox("🌍 Wumpus World Mode",
                    value=False, key="wumpus_mode",
                    help="Navigate a 4x4 grid of logical mystery before each question.")
            st.checkbox("🔬 FOL Reasoning Engine",
                value=True, key="fol_reasoning",
                help="Use First-Order Logic predicates for evaluation.")
            if PROLOG_AVAILABLE:
                st.checkbox("🧠 Use PROLOG Knowledge Base (Unit V)",
                    value=False, key="prolog_kb_toggle",
                    help="Bridge to SWI-Prolog for data retrieval.")

            st.markdown("### 🎙️ Voice Settings")
            voice_options = {
                "Professional Female (Jenny)": "en-US-JennyNeural",
                "Professional Male (Guy)": "en-US-GuyNeural",
                "Indian English Female (Neerja)": "en-IN-NeerjaNeural"
            }
            selected_label = st.selectbox(
                "Choose AI voice:",
                options=list(voice_options.keys()),
                index=0
            )
            st.session_state.selected_voice = voice_options[selected_label]

            if st.button("🔊 Test Voice", use_container_width=False):
                from utils import text_to_speech_autoplay
                text_to_speech_autoplay(f"Hello! This is a test of the {selected_label} voice.")

    with col2:
        st.markdown("""
            <div style="background:linear-gradient(135deg,var(--primary-color) 0%,var(--secondary-color) 100%); color:white; padding:1.5rem; border-radius:14px; box-shadow:0 10px 25px rgba(102,126,234,0.3); text-align:center;">
                <h3 style="margin-top:0;">Ready to begin?</h3>
                <p style="font-size:0.9rem; margin-bottom:1.5rem; opacity:0.9;">Ensure your camera and microphone are ready.</p>
            </div>
        """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("🚀 START NEW INTERVIEW", use_container_width=True, type="primary"):
            reset_interview()

            first_q = None
            if st.session_state.get("csp_toggle"):
                planner = ConstraintSatisfactionPlanner(st.session_state.kb)
                planned = planner.generate_interview_plan()
                if not planned:
                    st.warning("CSP planner could not find a valid plan. Switching to Best-First Search.")
                    import time; time.sleep(2.5)
                    first_q = st.session_state.selector.select_next_question(st.session_state.user_profile, [])
                    st.session_state.planned_questions = []
                else:
                    st.session_state.planned_questions = planned
                    first_q = st.session_state.planned_questions.pop(0)
            else:
                first_q = st.session_state.selector.select_next_question(
                    st.session_state.user_profile, []
                )

            st.session_state.current_question    = first_q
            st.session_state.interview_active    = True
            st.session_state.interview_stage     = 'intro'
            st.session_state.interview_start_time = datetime.now()

            # Initialize STRIPS Planner (upstream algorithm)
            if STRIPS_AVAILABLE:
                initial_state = {"session_started"}
                goal_state = {"session_closed", "report_generated", "advanced_assessed"}
                st.session_state.strips_planner = GoalStackPlanner(initial_state, goal_state, get_strips_actions())
                st.session_state.strips_planner.plan_interview()

            # Initialize Prolog KB if toggled (upstream algorithm)
            if st.session_state.get("prolog_kb_toggle") and PROLOG_AVAILABLE:
                st.session_state.prolog_kb = PrologKnowledgeBase()

            if st.session_state.db_ready and st.session_state.current_user:
                st.session_state.current_session_id = st.session_state.mysql_store.create_interview_session(
                    st.session_state.current_user["id"], st.session_state.interview_start_time
                )

            st.session_state.current_page = 'session'
            st.rerun()
