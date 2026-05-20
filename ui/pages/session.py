import streamlit as st
import time
import random
import html as _html
from utils import (
    text_to_speech_autoplay, speech_to_text, get_difficulty_level
)
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from ui.state_manager import *
from ui.components.media import render_avatar_panel, render_camera_pane

# Setup the audio recorder globally within the module scope
try:
    from audio_recorder_streamlit import audio_recorder
    AUDIO_RECORDER_AVAILABLE = True
except ImportError:
    AUDIO_RECORDER_AVAILABLE = False

TRANSITIONS = [
    "Okay, that's a good point. Let me ask you something else.",
    "Interesting, I like that answer. Moving on.",
    "Right, good. Let's shift gears a bit.",
    "Got it, thank you. Here's my next question for you.",
    "Alright, I appreciate that. Now let me ask you about something different.",
    "That's helpful context. Let me follow up with this.",
    "Good, I'm getting a clearer picture. Next question.",
    "Thank you for that. Let's continue.",
]

ACKNOWLEDGEMENTS = [
    "Mmhm, okay.", "Right, I see.", "Got it, thank you.",
    "Okay, noted.", "Alright.", "Sure, that makes sense.",
    "Good, thank you for that."
]

def _esc(value):
    return _html.escape(str(value), quote=True)

def render():
    if not st.session_state.interview_active:
        st.session_state.current_page = 'start_interview'
        st.rerun()
        return

    profile = st.session_state.user_profile
    cand_name = profile.get("name", "Candidate")
    q = st.session_state.current_question
    stage = st.session_state.interview_stage
    answered = len(st.session_state.answer_history)

    # ── Live stats & Meeting header bar ──
    mic_icon = "🔇" if st.session_state.mic_muted else "🎤"
    cam_icon = "📷" if st.session_state.cam_off   else "📹"
    safe_role = _esc(profile.get('target_role', ''))
    safe_cand_name = _esc(cand_name)
    st.markdown(f"""
        <div class="meet-header">
            <div>
                <span class="meet-title">
                    <span class="status-dot dot-live"></span>
                    AI Interview Session &mdash; {safe_role}
                </span><br>
                <span class="meet-meta">Candidate: {safe_cand_name} &nbsp;|&nbsp;
                    Q{answered + 1}/10 &nbsp;|&nbsp; &#9201; {get_elapsed_time()}
                </span>
            </div>
            <div style="display:flex;gap:18px;font-size:1.3rem;">
                <span>{mic_icon}</span>
                <span>{cam_icon}</span>
                <span style="color:var(--error);">&#9210;</span>
            </div>
        </div>""", unsafe_allow_html=True)

    prog = min(answered / 10, 1.0)
    st.progress(prog)

    # ── Intro Stage logic ──
    if stage == 'intro':
        if not st.session_state.intro_spoken:
            if 'intro_message' not in st.session_state:
                st.session_state.intro_message = None

                if st.session_state.get('ai_enhanced_mode', False):
                    from utils import call_gemini
                    prompt = (
                        f"You are an AI interview coach. Write a short 2-sentence welcome message "
                        f"for {cand_name} who is interviewing for a {profile.get('target_role', 'Software Engineer')} "
                        f"position at {profile.get('experience_level', 'entry')} level. "
                        f"Be warm, professional, and encouraging. No more than 40 words."
                    )
                    llm_greeting = call_gemini(prompt, feature_name="Feature 1: Voice Intro")
                    if llm_greeting:
                        st.session_state.intro_message = llm_greeting

            base_greeting = st.session_state.intro_message or (
                f"Hi {cand_name}, I'm an AI, your interviewer today. "
                f"Really glad you could make it. We'll be going through some {profile.get('target_role', 'Software Engineer')} questions today. "
                "Feel free to take your time with each answer. Ready to get started?"
            )

            full_greeting = (
                "Hello, can you hear me okay? Great. "
                "Give me just one second while I get everything ready. "
                + base_greeting
            )
            text_to_speech_autoplay(full_greeting)
            st.session_state.intro_spoken = True

        st.markdown("<br>", unsafe_allow_html=True)
        _, c2, _ = st.columns([1, 2, 1])
        with c2:
            if st.button("👉 I'm Ready — Ask First Question", width="stretch", type="primary", key="btn_ready"):
                text_to_speech_autoplay("Perfect, let's dive in. First question:")
                time.sleep(0.8)
                st.session_state.interview_stage = 'questions'
                st.rerun()

    # Render media panels
    col_avatar, col_cam = st.columns(2)
    with col_avatar:
        v_label = "Interviewer"
        voice_options = {
            "Professional Female (Jenny)": "en-US-JennyNeural",
            "Professional Male (Guy)": "en-US-GuyNeural",
            "Indian English Female (Neerja)": "en-IN-NeerjaNeural"
        }
        for label, val in voice_options.items():
            if val == st.session_state.get('selected_voice'):
                v_label = label
                break
        render_avatar_panel(v_label, st.session_state.mic_muted)

    with col_cam:
        render_camera_pane(cand_name, st.session_state.cam_off)

    # Meeting control bar
    st.markdown("")
    ctrl1, ctrl2, ctrl3, _ = st.columns([1, 1, 1, 3])
    with ctrl1:
        if st.button("🔇 Unmute" if st.session_state.mic_muted else "🎙️ Mute", key="mute_btn", type="secondary"):
            st.session_state.mic_muted = not st.session_state.mic_muted
            st.rerun()
    with ctrl2:
        if st.button("📷 Cam On" if st.session_state.cam_off else "📷 Cam Off", key="cam_btn", type="secondary"):
            st.session_state.cam_off = not st.session_state.cam_off
            st.rerun()
    with ctrl3:
        if st.button("🔴 End Interview", key="end_btn", type="primary"):
            with st.spinner("Generating your performance report…"):
                st.session_state.report = st.session_state.reporter.generate_report(
                    profile, st.session_state.answer_history
                )
            persist_completed_interview()
            st.session_state.interview_active   = False
            st.session_state.interview_complete = True
            st.session_state.interview_stage    = 'report'
            st.session_state.current_page       = 'feedback'
            st.rerun()

    st.markdown("---")

    # ── WRAPUP STAGE ──
    if stage == 'wrapup':
        if "wrapup_started" not in st.session_state:
            st.session_state.wrapup_started = True

            strongest_topic = "general concepts"
            if st.session_state.answer_history:
                topic_scores = {}
                for rec in st.session_state.answer_history:
                    t = rec.get("topic", "general")
                    if t not in topic_scores: topic_scores[t] = []
                    topic_scores[t].append(rec["score"])
                if topic_scores:
                    avgs = {t: sum(s)/len(s) for t, s in topic_scores.items()}
                    strongest_topic = max(avgs, key=avgs.get)

            closing1 = f"That was the last question, {cand_name}. Really appreciate your time today."
            closing2 = f"You had some strong moments, especially on {strongest_topic}. I'll put together your feedback report now."

            if st.session_state.get('ai_enhanced_mode', False):
                try:
                    from utils import call_gemini
                    prompt = (
                        f"You are an AI interview coach concluding an interview with {cand_name}. "
                        f"The candidate's strongest topic was {strongest_topic}. "
                        f"Write a warm 2-sentence closing statement celebrating their strong moments on that topic "
                        f"and letting them know you'll put together their feedback report now. Be extremely conversational."
                    )
                    llm_close = call_gemini(prompt, feature_name="Feature: Voice Closing")
                    if llm_close:
                        closing2 = llm_close
                except Exception:
                    pass

            full_closing = f"{closing1} {closing2}"
            text_to_speech_autoplay(full_closing)

        st.markdown("""
            <div style="background:linear-gradient(135deg,#065f46,#047857);
                        color:white;padding:2rem;border-radius:14px;text-align:center;margin:1rem 0;">
                <h3 style="margin:0 0 0.5rem;">🎉 All Questions Completed!</h3>
                <p style="margin:0;opacity:0.9;">Generating your comprehensive performance report…</p>
            </div>""", unsafe_allow_html=True)

        with st.spinner("🤖 Analysing all your answers…"):
            time.sleep(2)
            st.session_state.report = st.session_state.reporter.generate_report(
                profile, st.session_state.answer_history
            )
        persist_completed_interview()
        st.session_state.interview_active   = False
        st.session_state.interview_complete = True
        st.session_state.interview_stage    = 'report'
        st.session_state.current_page       = 'feedback'
        st.rerun()

    # ── QUESTIONS STAGE ──
    elif stage == 'questions' and q:

        if st.session_state.last_played_q_id != q['id']:
            if answered > 0:
                ack = random.choice(ACKNOWLEDGEMENTS)
                trans = random.choice(TRANSITIONS)
                combined = f"{ack} {trans} {q['question']}"
                text_to_speech_autoplay(combined)
            else:
                text_to_speech_autoplay(q['question'])
            st.session_state.last_played_q_id = q['id']

        if st.session_state.answer_history:
            last_record = st.session_state.answer_history[-1]
            last_q = last_record['question']
            sc = last_record['score']
            last_q_id = last_record['question_id']
            last_q_data = st.session_state.kb.get_question_by_id(last_q_id)

            sc_icon = "✅" if sc >= 7 else "⚠️" if sc >= 5 else "❌"
            sc_color = "var(--success)" if sc >= 7 else "var(--warning)" if sc >= 5 else "var(--error)"
            sc_text = "Good Answer" if sc >= 7 else "Needs Details" if sc >= 5 else "Needs Practice"

            fb = last_record['feedback']
            missing_c = len(fb.get('missing_concepts', []))
            total_concepts = len(last_q_data.get('concepts', [])) if last_q_data else 0
            matched_concepts = max(0, total_concepts - missing_c)

            ans_lower = last_record['answer'].lower()
            total_kw = len(last_q_data.get('keywords', [])) if last_q_data else 0
            matched_kw_count = sum(1 for k in last_q_data.get('keywords', []) if k.lower() in ans_lower) if last_q_data else 0

            st.markdown(f"""
            <div style="background:var(--card-bg); border:1px solid var(--card-border); border-radius:12px; padding:1.2rem; margin-bottom:1rem; box-shadow:0 4px 6px -1px rgba(0,0,0,0.1);">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 0.8rem;">
                    <span style="color:var(--text-main); font-size:1.1rem; font-weight:600;">Logic Score: {sc:.1f} / 10 {sc_icon}</span>
                    <span style="color:{sc_color}; font-weight:600;">{sc_text}</span>
                </div>
            """, unsafe_allow_html=True)
            st.progress(sc / 10.0)

            # --- Prolog Evaluation Row (upstream algorithm) ---
            if (st.session_state.get("prolog_kb_toggle") and
                st.session_state.get("prolog_kb") and
                hasattr(st.session_state.prolog_kb, 'available') and
                st.session_state.prolog_kb.available):
                p_eval = st.session_state.prolog_kb.evaluate_answer_prolog(last_q_id, last_record['answer'])
                st.markdown(f"""
                <div style="background: rgba(99, 102, 241, 0.05); padding: 1rem; border-radius:10px; border: 1px solid rgba(99, 102, 241, 0.2); margin-top: 0.8rem;">
                    <small style="color: var(--primary-color); text-transform: uppercase; font-weight: 800; letter-spacing: 1px;">🧠 Prolog Logical Verification</small><br/>
                    <div style="margin-top:0.5rem; font-size: 0.95rem;">
                        Matched: <code style="background:rgba(99,102,241,0.1); color:var(--primary-color); padding:2px 6px; border-radius:4px;">{_esc(p_eval['matched_keywords'])}</code> <br/>
                        Confidence: <b>{int(p_eval['score_component']*100)}%</b>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown(f"""
                <div style="display:flex; justify-content:space-between; margin-top: 0.8rem; font-size:0.9rem; color:var(--text-muted);">
                    <span>Keywords: {matched_kw_count}/{total_kw}</span>
                    <span>Concepts: {matched_concepts}/{total_concepts}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # --- Instant Coaching Tip (upstream feature) ---
            instant_key = f"instant_tip_{last_q_id}"
            if instant_key not in st.session_state:
                if st.button("💡 Get Instant Coaching Tip", key=f"btn_tip_{last_q_id}"):
                    with st.spinner("Getting your AI coaching tip..."):
                        strengths = fb.get("strengths") or []
                        suggestions = fb.get("suggestions") or []
                        missing_c_list = fb.get("missing_concepts") or []

                        did_well = strengths[0] if strengths else "You gave a reasonable starting answer."
                        if suggestions and len(suggestions) > 0:
                            improve_part = suggestions[0]
                        elif missing_c_list:
                            improve_part = (
                                "Next time, make sure you explicitly talk about: "
                                + ", ".join(missing_c_list[:3])
                                + "."
                            )
                        else:
                            improve_part = (
                                "You can make it even stronger by adding one concrete, real-world example "
                                "from your experience."
                            )
                        fallback_tip = f"{did_well} {improve_part}"

                        try:
                            from utils import call_gemini
                            prompt = (
                                "You are a friendly interview coach giving quick real-time advice.\n"
                                f"The candidate just answered this interview question: '{last_q}'\n"
                                f"Their answer was: '{last_record['answer']}'\n"
                                f"They scored {sc}/10.\n"
                                f"They correctly mentioned keywords based on this percentage: {matched_kw_count}/{total_kw}\n"
                                f"They missed these concepts: {missing_c_list}\n\n"
                                "Give ONE specific, actionable tip they can use RIGHT NOW to improve "
                                "this answer if asked again. Start with what they did right in one "
                                "short sentence, then give the improvement tip. Maximum 3 sentences total. "
                                "Be conversational and encouraging, like a friend helping you prep. "
                                "No bullet points, no headers."
                            )
                            tip = call_gemini(prompt, feature_name="Feature: Instant Tip")
                            st.session_state[instant_key] = tip or fallback_tip
                        except Exception:
                            st.session_state[instant_key] = fallback_tip
                    st.rerun()

            if instant_key in st.session_state:
                st.markdown(f"""
                <div style="background: rgba(255, 251, 235, 0.1); border-left: 4px solid var(--warning); padding:1.2rem; border-radius:12px; margin-bottom:1.5rem; border: 1px solid rgba(245,158,11,0.2);">
                    <div style="color:var(--warning); font-weight:700; margin-bottom:0.4rem; font-size:1rem; display:flex; align-items:center; gap:8px;">
                        <span>💡</span> Quick AI Coaching Tip
                    </div>
                    <div style="color:var(--text-main); font-size:0.95rem; line-height:1.5;">{_esc(st.session_state[instant_key])}</div>
                </div>
                """, unsafe_allow_html=True)

            # --- FOL Reasoning Trace (upstream algorithm) ---
            if st.session_state.get('fol_reasoning', True) and fb.get('fol_trace'):
                with st.expander("🔬 View First-Order Logic (FOL) Reasoning Trace", expanded=False):
                    trace_html = []
                    for t in fb['fol_trace']:
                        if "TRUE" in t: color = "var(--success)"
                        elif "PARTIAL" in t: color = "var(--warning)"
                        elif "FALSE" in t: color = "var(--error)"
                        else: color = "var(--primary-color)"
                        trace_html.append(f'<div style="color:{color}; font-family:monospace; margin-bottom:4px;">{_esc(t)}</div>')
                    st.markdown("".join(trace_html), unsafe_allow_html=True)

        # --- STRIPS Interview Plan Visualizer (upstream algorithm) ---
        if st.session_state.get("strips_planner") and STRIPS_AVAILABLE:
            with st.expander("📋 STRIPS Interview Plan Log", expanded=False):
                col_p, col_s = st.columns([2, 1])
                with col_p:
                    st.markdown(st.session_state.strips_planner.get_plan_html(), unsafe_allow_html=True)
                with col_s:
                    current_act = st.session_state.strips_planner.get_current_action(st.session_state.answer_history)
                    st.markdown(f"**Current Action:** `{current_act}`")
                    st.markdown(f"**World Facts:** `{list(st.session_state.strips_planner.state)}`")

        # --- Prolog Query Log (upstream algorithm) ---
        if st.session_state.get("prolog_kb_toggle") and st.session_state.get("prolog_kb"):
            with st.expander("📝 PROLOG Logical Verification Log", expanded=False):
                if hasattr(st.session_state.prolog_kb, 'get_prolog_query_log'):
                    for q_log in st.session_state.prolog_kb.get_prolog_query_log():
                        st.code(q_log, language="prolog")

        diff_level = get_difficulty_level(q)
        st.markdown(f"""
            <div style="text-align:center; font-size:1.1rem; color:var(--text-muted); font-weight:600; text-transform:uppercase; margin-bottom: 0.6rem; margin-top: 1rem;">
                Question {answered + 1} of 10
            </div>
        """, unsafe_allow_html=True)

        from ui.components.metrics import render_difficulty_badge
        safe_question = _esc(q['question'])
        safe_topic = _esc(q.get('topic', 'General').title())
        st.markdown(f"""
            <div style="background:var(--card-bg); color:var(--text-main); padding:1.8rem; border-radius:14px; text-align:center; box-shadow:0 10px 25px -5px rgba(0,0,0,0.1); border:1px solid var(--card-border); margin-bottom:1rem;">
                <div style="font-size:20px; font-weight:600; line-height:1.6; margin-bottom:1rem;">{safe_question}</div>
                <div style="display:inline-block; margin-top:0.4rem;">
                    {render_difficulty_badge(diff_level)}
                    <span style="font-size:0.8rem; color:var(--text-muted); margin-left:10px;">📌 Topic: {safe_topic}</span>
                </div>
            </div>""", unsafe_allow_html=True)

        # Progress dots
        dots_html = []
        for i in range(10):
            if i < len(st.session_state.answer_history):
                s = st.session_state.answer_history[i]['score']
                dot_color = "var(--success)" if s >= 7 else "var(--warning)" if s >= 5 else "var(--error)"
                dots_html.append(f'<div style="width:12px; height:12px; border-radius:50%; background:{dot_color};"></div>')
            elif i == answered:
                dots_html.append('<div style="width:12px; height:12px; border-radius:50%; background:var(--primary-color); box-shadow:0 0 8px rgba(102,126,234,0.6); animation: pulse 1.5s infinite;"></div>')
            else:
                dots_html.append('<div style="width:12px; height:12px; border-radius:50%; background:var(--card-border); border:1px solid #cbd5e1;"></div>')

        st.markdown(f"""<div style="display:flex; justify-content:center; gap:6px; margin-bottom:2rem;">{"".join(dots_html)}</div>""", unsafe_allow_html=True)

        st.markdown("#### 🎤 Your Answer")
        if st.session_state.mic_muted:
            st.warning("🔇 Your microphone is muted. Click **Unmute** in the controls above, then record.")

        voice_answer = None
        if not st.session_state.mic_muted:
            if AUDIO_RECORDER_AVAILABLE:
                st.markdown('<p style="color:var(--text-muted);font-size:0.9rem;">🔴 Click the button to record · speak your answer · click again to stop</p>', unsafe_allow_html=True)
                audio_bytes = audio_recorder(pause_threshold=3.0, sample_rate=16_000, key=f"audio_{answered}")
                if audio_bytes:
                    with st.spinner("🔄 Transcribing your answer…"):
                        voice_answer = speech_to_text(audio_bytes)
                    if voice_answer:
                        st.markdown(f"""
                            <div style="background:rgba(16,185,129,0.1);border:1px solid var(--success);
                                        border-radius:10px;padding:0.9rem;margin:0.5rem 0;">
                                <div style="color:var(--success);font-size:0.8rem;font-weight:600;">✅ Transcribed answer:</div>
                                <div style="color:var(--text-main);margin-top:4px;">{_esc(voice_answer)}</div>
                            </div>""", unsafe_allow_html=True)
                    else:
                        st.warning("⚠️ Could not transcribe. Please speak clearly or use the text box below.")
            else:
                st.info("Install `audio-recorder-streamlit` to enable voice answers.")

        st.markdown('<p style="color:var(--text-muted);font-size:0.84rem;">Or type your answer manually:</p>', unsafe_allow_html=True)
        col_txt, col_btn = st.columns([5, 1])
        with col_txt:
            typed_answer = st.text_area("Type your answer:", height=130, key=f"typed_{answered}", placeholder="Type a detailed answer here…", label_visibility="collapsed")
        with col_btn:
            st.write("")
            st.write("")
            submit_typed = st.button("📤 Submit", key=f"submit_{answered}", width="stretch", type="primary")

        final_answer = None
        if voice_answer:
            final_answer = voice_answer
        elif submit_typed and typed_answer.strip():
            final_answer = typed_answer.strip()
        elif submit_typed and not typed_answer.strip():
            st.warning("⚠️ Please type an answer or record your voice before submitting.")

        if final_answer:
            with st.spinner("📝 Saving your answer…"):
                process_answer(final_answer)
                time.sleep(0.5)
            st.rerun()

    if st.session_state.answer_history:
        with st.expander(f"📋 Answers so far ({len(st.session_state.answer_history)} recorded)", expanded=False):
            for i, rec in enumerate(st.session_state.answer_history, 1):
                st.markdown(f"**Q{i}:** {rec['question']}")
                st.markdown(f"*Your answer:* {rec['answer'][:200]}{'…' if len(rec['answer'])>200 else ''}")
                st.markdown("---")
