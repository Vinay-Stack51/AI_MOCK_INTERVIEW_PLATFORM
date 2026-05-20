import streamlit as st
from datetime import datetime
from knowledge_base import KnowledgeBase
from question_selector import QuestionSelector
from answer_evaluator import AnswerEvaluator
from performance_report import PerformanceReport
from mysql_store import MySQLStore
from utils import get_difficulty_level

# Import advanced algorithm modules (upstream features)
try:
    from minimax_selector import MinimaxQuestionSelector
    MINIMAX_AVAILABLE = True
except ImportError:
    MINIMAX_AVAILABLE = False

try:
    from wumpus_interview import WumpusInterviewWorld
    WUMPUS_AVAILABLE = True
except ImportError:
    WUMPUS_AVAILABLE = False

try:
    from strips_planner import GoalStackPlanner, get_strips_actions, update_state_from_answers
    STRIPS_AVAILABLE = True
except ImportError:
    STRIPS_AVAILABLE = False

try:
    from prolog_kb import PrologKnowledgeBase
    PROLOG_AVAILABLE = True
except ImportError:
    PROLOG_AVAILABLE = False


def init_session_state():
    if 'initialized' not in st.session_state:
        st.session_state.initialized        = True
        st.session_state.kb                 = KnowledgeBase()
        st.session_state.selector           = QuestionSelector(st.session_state.kb)
        st.session_state.evaluator          = AnswerEvaluator(st.session_state.kb)
        st.session_state.reporter           = PerformanceReport()
        st.session_state.interview_active   = False
        st.session_state.interview_complete = False
        st.session_state.interview_stage    = 'idle'
        st.session_state.intro_spoken       = False
        st.session_state.current_question   = None
        st.session_state.question_history   = []
        st.session_state.answer_history     = []
        st.session_state.messages           = []
        st.session_state.report             = None
        st.session_state.last_played_q_id   = None
        st.session_state.interview_start_time = None
        st.session_state.mic_muted          = False
        st.session_state.cam_off            = False
        st.session_state.user_profile       = {}

        # Advanced algorithm state (from upstream)
        st.session_state.strips_planner      = None
        st.session_state.prolog_kb           = None
        st.session_state.planned_questions   = []

        st.session_state.mysql_store        = MySQLStore()
        ok, msg = st.session_state.mysql_store.initialize()
        st.session_state.db_ready           = ok
        st.session_state.db_message         = msg
        st.session_state.authenticated      = False
        st.session_state.current_user       = None
        st.session_state.current_session_id = None

        # UI routing state
        st.session_state.current_page       = 'auth'
        st.session_state.theme              = 'light'  # default theme

def reset_interview():
    st.session_state.interview_active    = False
    st.session_state.interview_complete  = False
    st.session_state.interview_stage     = 'idle'
    st.session_state.intro_spoken        = False
    st.session_state.current_question    = None
    st.session_state.question_history    = []
    st.session_state.answer_history      = []
    st.session_state.messages            = []
    st.session_state.report              = None
    st.session_state.last_played_q_id    = None
    st.session_state.interview_start_time = None
    st.session_state.mic_muted           = False
    st.session_state.cam_off             = False
    st.session_state.intro_message       = None
    st.session_state.wrapup_started      = False
    st.session_state.planned_questions   = []
    st.session_state.current_session_id  = None

    # Reset advanced algorithm state
    st.session_state.strips_planner      = None
    st.session_state.prolog_kb           = None

    for key in list(st.session_state.keys()):
        if str(key).startswith("instant_tip_") or str(key).startswith("tts_cache_"):
            st.session_state.pop(key, None)

    # Clear wumpus/minimax session objects
    for key in ['wumpus_world', 'minimax', 'wrapup_started', 'intro_message', 'instant_feedback']:
        if key in st.session_state:
            del st.session_state[key]

    st.session_state.selector.reset_history()

def get_elapsed_time() -> str:
    if not st.session_state.interview_start_time:
        return "00:00"
    delta = datetime.now() - st.session_state.interview_start_time
    mins  = int(delta.total_seconds() // 60)
    secs  = int(delta.total_seconds() % 60)
    return f"{mins:02d}:{secs:02d}"

def persist_completed_interview():
    if (st.session_state.db_ready and
        st.session_state.current_session_id and
        st.session_state.report):
        st.session_state.mysql_store.complete_interview_session(
            st.session_state.current_session_id,
            st.session_state.report
        )

def process_answer(answer_text: str):
    q = st.session_state.current_question
    if not q or not answer_text.strip():
        return

    feedback = st.session_state.evaluator.evaluate_answer(q['id'], answer_text)

    record = {
        "question_id" : q['id'],
        "question"    : q['question'],
        "answer"      : answer_text,
        "score"       : feedback["score"],
        "topic"       : q.get("topic", "general"),
        "difficulty"  : get_difficulty_level(q),
        "feedback"    : feedback,
        "timestamp"   : datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    st.session_state.answer_history.append(record)
    st.session_state.question_history.append(q['id'])

    # Save instant feedback to state
    st.session_state.instant_feedback = feedback

    if st.session_state.db_ready and st.session_state.current_session_id:
        st.session_state.mysql_store.save_answer_record(
            st.session_state.current_session_id, record
        )

    st.session_state.selector.update_performance(
        q['id'], feedback["score"], q.get("topic", "general")
    )

    total_q = 10
    if len(st.session_state.answer_history) < total_q:
        next_q = None

        # 0. Pre-planned syllabus path (CSP)
        if st.session_state.get("csp_toggle") and st.session_state.get("planned_questions"):
            next_q = st.session_state.planned_questions.pop(0)

        # 1. Wumpus World Mode (upstream algorithm)
        if not next_q and st.session_state.get("wumpus_mode") and WUMPUS_AVAILABLE:
            if 'wumpus_world' not in st.session_state:
                st.session_state.wumpus_world = WumpusInterviewWorld(
                    st.session_state.kb.get_all_questions(), st.session_state.user_profile
                )
            target_cell = st.session_state.wumpus_world.choose_next_cell()
            if target_cell:
                q_obj, effect = st.session_state.wumpus_world.move_agent(target_cell)
                next_q = q_obj
                if effect == "pit":
                    st.toast("⚫ Fell into a Pit! Score for this slot is 0 - skipping.", icon="⚠️")
                elif effect == "wumpus":
                    st.toast("💀 Wumpus Attack! Tricky question ahead.", icon="🔥")

        # 2. Adversarial Mode (Minimax α-β) (upstream algorithm)
        if not next_q and st.session_state.get("ai_adversarial_mode") and MINIMAX_AVAILABLE:
            if 'minimax' not in st.session_state:
                st.session_state.minimax = MinimaxQuestionSelector(st.session_state.kb)
            next_q = st.session_state.minimax.select_next_question(
                st.session_state.user_profile, st.session_state.answer_history
            )

        # 3. Dynamic Skill Mode (Default Best-First Search)
        if not next_q:
            next_q = st.session_state.selector.select_next_question(
                st.session_state.user_profile, st.session_state.answer_history
            )

            # If AI Enhanced, refine the question to match role exactly
            if st.session_state.get('ai_enhanced_mode', False) and next_q:
                from utils import call_gemini
                role = st.session_state.user_profile.get("target_role", "Software Engineer")
                chosen_skills = [s.lower() for s in st.session_state.user_profile.get("skills", [])]
                prompt = (
                    f"Rewrite this interview question to be specifically for a '{role}' candidate "
                    f"focusing only on these technologies: {', '.join(chosen_skills)}.\n"
                    f"Original Question: {next_q['question']}\n"
                    f"Keep it under 25 words. Response ONLY with the new question text."
                )
                dynamic_q = call_gemini(prompt, feature_name="Question Refinement")
                if dynamic_q:
                    next_q["question"] = dynamic_q

        # Update STRIPS State (upstream algorithm)
        if st.session_state.strips_planner and STRIPS_AVAILABLE:
            update_state_from_answers(st.session_state.strips_planner, st.session_state.answer_history)

        if next_q:
            st.session_state.current_question = next_q
            st.session_state.last_played_q_id = None
        else:
            st.session_state.interview_stage = 'wrapup'
            st.session_state.current_question = None
    else:
        st.session_state.interview_stage = 'wrapup'
        st.session_state.current_question = None
