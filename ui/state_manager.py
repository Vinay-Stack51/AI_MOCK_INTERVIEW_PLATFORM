import streamlit as st
from datetime import datetime

from knowledge_base import KnowledgeBase
from question_selector import QuestionSelector
from answer_evaluator import AnswerEvaluator
from performance_report import PerformanceReport
from mysql_store import MySQLStore


def init_session_state():

    if "initialized" in st.session_state:
        return

    # ---------------- CORE OBJECTS ----------------
    st.session_state.initialized = True

    st.session_state.kb = KnowledgeBase()
    st.session_state.selector = QuestionSelector(st.session_state.kb)
    st.session_state.evaluator = AnswerEvaluator(st.session_state.kb)
    st.session_state.reporter = PerformanceReport()

    # ---------------- INTERVIEW STATE ----------------
    st.session_state.interview_active = False
    st.session_state.interview_complete = False
    st.session_state.interview_stage = "idle"
    st.session_state.intro_spoken = False

    st.session_state.current_question = None
    st.session_state.question_history = []
    st.session_state.answer_history = []
    st.session_state.messages = []
    st.session_state.report = None

    st.session_state.last_played_q_id = None
    st.session_state.interview_start_time = None

    st.session_state.mic_muted = False
    st.session_state.cam_off = False

    st.session_state.user_profile = {}

    # ---------------- ADVANCED ALGO STATE ----------------
    st.session_state.strips_planner = None
    st.session_state.prolog_kb = None
    st.session_state.planned_questions = []

    # ---------------- MYSQL SAFE INIT ----------------
    try:
        st.session_state.mysql_store = MySQLStore()
        if st.session_state.mysql_store.enabled:
            ok, msg = st.session_state.mysql_store.initialize()
            st.session_state.db_ready = ok
            st.session_state.db_message = msg
        else:
            st.session_state.db_ready = True   # 🔥 IMPORTANT FIX
            st.session_state.db_message = "Running in demo mode (No DB)"
    except Exception as e:
        st.session_state.mysql_store = None
        st.session_state.db_ready = False
        st.session_state.db_message = str(e)

    # ---------------- AUTH ----------------
    st.session_state.authenticated = False
    st.session_state.current_user = None
    st.session_state.current_session_id = None

    # ---------------- UI STATE ----------------
    st.session_state.current_page = "auth"
    st.session_state.theme = "light"


def reset_interview():

    st.session_state.interview_active = False
    st.session_state.interview_complete = False
    st.session_state.interview_stage = "idle"

    st.session_state.current_question = None
    st.session_state.question_history = []
    st.session_state.answer_history = []
    st.session_state.messages = []
    st.session_state.report = None

    st.session_state.last_played_q_id = None
    st.session_state.interview_start_time = None

    st.session_state.mic_muted = False
    st.session_state.cam_off = False

    st.session_state.intro_message = None
    st.session_state.wrapup_started = False
    st.session_state.planned_questions = []
    st.session_state.current_session_id = None

    # reset advanced modules
    st.session_state.strips_planner = None
    st.session_state.prolog_kb = None

    # remove cached keys
    for key in list(st.session_state.keys()):
        if str(key).startswith("tts_cache_") or str(key).startswith("instant_tip_"):
            st.session_state.pop(key, None)

    st.session_state.selector.reset_history()


def get_elapsed_time() -> str:
    if not st.session_state.interview_start_time:
        return "00:00"

    delta = datetime.now() - st.session_state.interview_start_time
    mins = int(delta.total_seconds() // 60)
    secs = int(delta.total_seconds() % 60)

    return f"{mins:02d}:{secs:02d}"


def persist_completed_interview():
    if (
        st.session_state.get("db_ready")
        and st.session_state.get("current_session_id")
        and st.session_state.get("report")
        and st.session_state.get("mysql_store")
    ):
        st.session_state.mysql_store.complete_interview_session(
            st.session_state.current_session_id,
            st.session_state.report
        )


def process_answer(answer_text: str):

    q = st.session_state.current_question
    if not q or not answer_text.strip():
        return

    feedback = st.session_state.evaluator.evaluate_answer(q["id"], answer_text)

    record = {
        "question_id": q["id"],
        "question": q["question"],
        "answer": answer_text,
        "score": feedback["score"],
        "topic": q.get("topic", "general"),
        "difficulty": q.get("difficulty", "beginner"),
        "feedback": feedback,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    st.session_state.answer_history.append(record)
    st.session_state.question_history.append(q["id"])
    st.session_state.instant_feedback = feedback

    if st.session_state.get("db_ready") and st.session_state.get("current_session_id"):
        st.session_state.mysql_store.save_answer_record(
            st.session_state.current_session_id,
            record
        )

    st.session_state.selector.update_performance(
        q["id"], feedback["score"], q.get("topic", "general")
    )

    total_q = 10

    if len(st.session_state.answer_history) >= total_q:
        st.session_state.interview_stage = "wrapup"
        st.session_state.current_question = None
        return

    next_q = st.session_state.selector.select_next_question(
        st.session_state.user_profile,
        st.session_state.answer_history
    )

    st.session_state.current_question = next_q
    st.session_state.last_played_q_id = None
