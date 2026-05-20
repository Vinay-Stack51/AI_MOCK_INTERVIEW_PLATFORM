import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import html as _html
from datetime import datetime
from ui.components.metrics import render_metric_card, render_difficulty_badge
from ui.components.charts import plot_score_trend, plot_topic_performance, plot_difficulty_breakdown

def _esc(value):
    return _html.escape(str(value), quote=True)


def _score_color(sc):
    if sc >= 7: return "#10b981"
    if sc >= 5: return "#f59e0b"
    return "#ef4444"

def _score_label(sc):
    if sc >= 8.5: return "Excellent"
    if sc >= 7: return "Good"
    if sc >= 5: return "Average"
    if sc >= 3: return "Below Average"
    return "Needs Work"

def _priority_icon(p):
    return {"high": "🔴", "medium": "🟡", "low": "🟢", "critical": "⚡"}.get(p, "🔵")

def _priority_color(p):
    return {"high": "#ef4444", "medium": "#f59e0b", "low": "#10b981", "critical": "#8b5cf6"}.get(p, "#667eea")

def _hex_to_rgba(hex_color, alpha):
    """Convert a hex color string to rgba() with the given alpha (0-1)."""
    h = hex_color.lstrip('#')
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def render():
    if not st.session_state.interview_complete or not st.session_state.report:
        st.session_state.current_page = 'dashboard'
        st.rerun()
        return

    report = st.session_state.report
    score = report['summary']['overall_score']
    perf_level = report['summary']['performance_level']
    sc = _score_color(score)

    # ── Hero Banner ──
    st.balloons()
    st.markdown(f"""
        <div style="background:linear-gradient(135deg,#065f46 0%,#047857 50%,#059669 100%);
                    padding:2.5rem; border-radius:20px; color:white; text-align:center; margin:0.5rem 0 2rem;
                    box-shadow:0 20px 40px rgba(5,150,105,0.3);">
            <h1 style="font-size:2.2rem;margin:0 0 0.5rem; font-weight:700;">🎉 Interview Complete!</h1>
            <p style="opacity:0.9;margin:0; font-size:1.1rem;">
                Comprehensive performance analysis for
                <strong>{_esc(report['user_profile'].get('name','Candidate'))}</strong>
            </p>
            <div style="margin-top:1.5rem; display:inline-block; background:rgba(255,255,255,0.15); padding:0.8rem 2.5rem; border-radius:14px; backdrop-filter:blur(4px);">
                <div style="font-size:2.8rem; font-weight:800; letter-spacing:-1px;">{score}<span style="font-size:1.2rem; opacity:0.7;">/10</span></div>
                <div style="font-size:0.85rem; text-transform:uppercase; letter-spacing:1px; opacity:0.85; margin-top:0.2rem;">{_score_label(score)}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # ── AI Summary Card ──
    if "llm_summary" in report:
        st.markdown(f"""
            <div style="background:linear-gradient(135deg, rgba(102,126,234,0.08), rgba(118,75,162,0.08));
                        border:1px solid rgba(102,126,234,0.2); padding:1.5rem; border-radius:14px; margin-bottom:1.5rem; position:relative;">
                <div style="display:flex; align-items:center; gap:0.6rem; margin-bottom:0.8rem;">
                    <span style="font-size:1.3rem;">✨</span>
                    <span style="color:var(--primary-color); font-weight:700; font-size:1rem;">AI Coach Summary</span>
                </div>
                <p style="color:var(--text-main); margin:0; font-size:1.05rem; line-height:1.7;">{_esc(report['llm_summary'])}</p>
            </div>
        """, unsafe_allow_html=True)

    # ── KPI Row ──
    mc1, mc2, mc3, mc4 = st.columns(4)
    with mc1:
        render_metric_card("⭐", f"<span style='color:{sc}'>{score}/10</span>", f"Overall · {perf_level.replace('_',' ').title()}")
    with mc2:
        render_metric_card("📝", str(report['summary']['total_questions']), "Questions Answered")
    with mc3:
        render_metric_card("✅", f"{report['summary']['completion_rate']}%", "Completion Rate")
    with mc4:
        render_metric_card("💪", str(len(report['detailed_analysis']['strongest_topics'])), "Strength Areas")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Tabs ──
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Summary", "📋 Question Review", "📈 Analytics",
        "📚 Learning Path", "🎯 Report & Export"
    ])

    # ═══════════════════════════════════════════════════════
    # TAB 1 — SUMMARY
    # ═══════════════════════════════════════════════════════
    with tab1:
        st.markdown("### 📊 Topic-wise Performance")
        plot_topic_performance(report['detailed_analysis']['by_topic'])

        st.markdown("---")
        col_s, col_w = st.columns(2)
        with col_s:
            st.markdown("### ✅ Your Strengths")
            for s in report['detailed_analysis']['strongest_topics']:
                pct = int(s['score'] * 10)
                st.markdown(f"""
                    <div style="background:var(--card-bg); border:1px solid var(--card-border); padding:1rem 1.25rem; border-radius:12px; margin:0.5rem 0;">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.5rem;">
                            <strong style="color:var(--text-main); font-size:1rem;">🟢 {_esc(s['topic'].title())}</strong>
                            <span style="color:#10b981; font-weight:700; font-size:1.1rem;">{s['score']}/10</span>
                        </div>
                        <div style="background:rgba(16,185,129,0.1); border-radius:8px; height:8px; overflow:hidden;">
                            <div style="background:linear-gradient(90deg,#10b981,#34d399); height:100%; width:{pct}%; border-radius:8px; transition:width 0.5s;"></div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

        with col_w:
            st.markdown("### 🔧 Areas to Improve")
            for w in report['detailed_analysis']['weakest_topics']:
                pct = int(w['score'] * 10)
                wc = _score_color(w['score'])
                st.markdown(f"""
                    <div style="background:var(--card-bg); border:1px solid var(--card-border); padding:1rem 1.25rem; border-radius:12px; margin:0.5rem 0;">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.5rem;">
                            <strong style="color:var(--text-main); font-size:1rem;">🔴 {_esc(w['topic'].title())}</strong>
                            <span style="color:{wc}; font-weight:700; font-size:1.1rem;">{w['score']}/10</span>
                        </div>
                        <div style="background:rgba(239,68,68,0.1); border-radius:8px; height:8px; overflow:hidden;">
                            <div style="background:linear-gradient(90deg,#ef4444,#f87171); height:100%; width:{pct}%; border-radius:8px; transition:width 0.5s;"></div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════
    # TAB 2 — QUESTION REVIEW (redesigned)
    # ═══════════════════════════════════════════════════════
    with tab2:
        st.markdown("### 📋 Question-by-Question Breakdown")
        if not st.session_state.answer_history:
            st.info("No answers were recorded.")
        else:
            total_qs = len(st.session_state.answer_history)

            for i, rec in enumerate(st.session_state.answer_history, 1):
                qsc = rec.get("score", 0)
                fb = rec.get("feedback", {}) or {}
                qsc_color = _score_color(qsc)
                qsc_label = _score_label(qsc)
                diff = rec.get("difficulty", "beginner")
                topic = rec.get("topic", "general")

                with st.expander(f"Q{i}  ·  {topic.title()}  ·  Score: {qsc}/10  ·  {qsc_label}", expanded=(i == 1)):

                    # Question header card
                    st.markdown(f"""
                        <div style="background:linear-gradient(135deg, #1e293b, #334155); color:white;
                                    padding:1.2rem 1.5rem; border-radius:12px; margin-bottom:1rem;">
                            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.8rem;">
                                <span style="font-size:0.78rem; text-transform:uppercase; letter-spacing:0.5px; opacity:0.7;">
                                    Question {i} of {total_qs}
                                </span>
                                <div style="display:flex; gap:0.5rem; align-items:center;">
                                    {render_difficulty_badge(diff)}
                                    <span style="font-size:0.78rem; opacity:0.6; margin-left:4px;">📌 {topic.title()}</span>
                                </div>
                            </div>
                            <div style="font-size:1.1rem; font-weight:500; line-height:1.6;">{_esc(rec.get('question', ''))}</div>
                        </div>
                    """, unsafe_allow_html=True)

                    # Score + progress ring
                    col_score, col_detail = st.columns([1, 3])
                    with col_score:
                        pct = int(qsc * 10)
                        st.markdown(f"""
                            <div style="background:var(--card-bg); border:1px solid var(--card-border); border-radius:14px;
                                        padding:1.5rem; text-align:center;">
                                <div style="font-size:2.5rem; font-weight:800; color:{qsc_color};">{qsc}<span style="font-size:1rem; opacity:0.5;">/10</span></div>
                                <div style="font-size:0.8rem; color:var(--text-muted); margin-top:0.3rem; text-transform:uppercase; letter-spacing:0.5px;">{qsc_label}</div>
                                <div style="background:rgba(0,0,0,0.06); border-radius:8px; height:6px; margin-top:0.8rem; overflow:hidden;">
                                    <div style="background:{qsc_color}; height:100%; width:{pct}%; border-radius:8px;"></div>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)

                    with col_detail:
                        # Your answer
                        raw_ans = (rec.get("answer") or "").strip()
                        st.markdown("**💬 Your Answer**")
                        if not raw_ans:
                            st.caption("_No response detected._")
                        else:
                            st.markdown(f"""
                                <div style="background:var(--card-bg); border:1px solid var(--card-border);
                                            padding:1rem; border-radius:10px; font-size:0.95rem; color:var(--text-main); line-height:1.6;">
                                    {_esc(raw_ans)}
                                </div>
                            """, unsafe_allow_html=True)

                    # AI Feedback section
                    if "llm_feedback" in fb:
                        st.markdown(f"""
                            <div style="background:linear-gradient(135deg, rgba(102,126,234,0.06), rgba(118,75,162,0.06));
                                        border:1px solid rgba(102,126,234,0.15); padding:1.2rem; border-radius:12px; margin:0.8rem 0;">
                                <div style="display:flex; align-items:center; gap:0.5rem; margin-bottom:0.6rem;">
                                    <span style="font-size:1.1rem;">✨</span>
                                    <span style="color:var(--primary-color); font-weight:600; font-size:0.9rem;">AI Coach Feedback</span>
                                </div>
                                <p style="color:var(--text-main); margin:0; font-size:0.95rem; line-height:1.65;">{_esc(fb['llm_feedback'])}</p>
                            </div>
                        """, unsafe_allow_html=True)

                    # Strengths / Weaknesses / Suggestions grid
                    strengths = fb.get("strengths") or []
                    weaknesses = fb.get("weaknesses") or []
                    suggestions = fb.get("suggestions") or []
                    missing = fb.get("missing_concepts") or []

                    fcol1, fcol2 = st.columns(2)
                    with fcol1:
                        if strengths:
                            st.markdown(f"""
                                <div style="background:rgba(16,185,129,0.06); border:1px solid rgba(16,185,129,0.15);
                                            padding:1rem; border-radius:10px; margin:0.4rem 0;">
                                    <div style="color:#10b981; font-weight:600; font-size:0.85rem; margin-bottom:0.5rem;">✅ What you did well</div>
                                    {''.join(f'<div style="color:var(--text-main); font-size:0.9rem; padding:0.2rem 0;">• {_esc(s)}</div>' for s in strengths)}
                                </div>
                            """, unsafe_allow_html=True)

                    with fcol2:
                        if weaknesses or missing:
                            items_html = ''.join(f'<div style="color:var(--text-main); font-size:0.9rem; padding:0.2rem 0;">• {_esc(w)}</div>' for w in weaknesses)
                            if missing:
                                items_html += f'<div style="color:var(--text-main); font-size:0.9rem; padding:0.2rem 0;">• <strong>Missed:</strong> {_esc(", ".join(missing))}</div>'
                            st.markdown(f"""
                                <div style="background:rgba(239,68,68,0.06); border:1px solid rgba(239,68,68,0.15);
                                            padding:1rem; border-radius:10px; margin:0.4rem 0;">
                                    <div style="color:#ef4444; font-weight:600; font-size:0.85rem; margin-bottom:0.5rem;">🔧 Areas to improve</div>
                                    {items_html}
                                </div>
                            """, unsafe_allow_html=True)

                    if suggestions:
                        st.markdown(f"""
                            <div style="background:rgba(251,191,36,0.06); border:1px solid rgba(251,191,36,0.15);
                                        padding:1rem; border-radius:10px; margin:0.4rem 0;">
                                <div style="color:#f59e0b; font-weight:600; font-size:0.85rem; margin-bottom:0.5rem;">💡 Suggestions</div>
                                {''.join(f'<div style="color:var(--text-main); font-size:0.9rem; padding:0.2rem 0;">• {_esc(s)}</div>' for s in suggestions)}
                            </div>
                        """, unsafe_allow_html=True)

                    # Ideal answer
                    ideal = fb.get("ideal_answer") or {}
                    key_points = ideal.get("key_points") or []
                    example = ideal.get("example") or ""
                    if key_points or example:
                        with st.expander("🎯 View Ideal Answer Outline"):
                            if key_points:
                                for p in key_points:
                                    st.markdown(f"- {p}")
                            if example:
                                st.code(example)

    # ═══════════════════════════════════════════════════════
    # TAB 3 — ANALYTICS
    # ═══════════════════════════════════════════════════════
    with tab3:
        col_l, col_r = st.columns(2)
        with col_l:
            st.markdown("### 📈 Score Progression")
            plot_score_trend(report['detailed_analysis']['progress_over_time'])
        with col_r:
            st.markdown("### 📊 Difficulty Breakdown")
            plot_difficulty_breakdown(report['detailed_analysis']['by_difficulty'])

        # Radar chart for topic spread
        st.markdown("---")
        st.markdown("### 🕸️ Topic Competency Radar")
        topic_dict = report['detailed_analysis']['by_topic']
        if topic_dict:
            topics = [t.title() for t in topic_dict.keys()]
            scores = [d['average_score'] for d in topic_dict.values()]
            # Close the radar by repeating the first value
            topics_closed = topics + [topics[0]]
            scores_closed = scores + [scores[0]]

            fig = go.Figure()
            fig.add_trace(go.Scatterpolar(
                r=scores_closed, theta=topics_closed,
                fill='toself',
                fillcolor='rgba(102,126,234,0.15)',
                line=dict(color='#667eea', width=2),
                marker=dict(size=6, color='#667eea'),
                name='Your Score'
            ))
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(visible=True, range=[0, 10], tickfont=dict(size=10)),
                    bgcolor='rgba(0,0,0,0)'
                ),
                showlegend=False,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                height=400,
                margin=dict(t=30, b=30, l=60, r=60)
            )
            st.plotly_chart(fig, use_container_width=True)

    # ═══════════════════════════════════════════════════════
    # TAB 4 — LEARNING PATH (redesigned)
    # ═══════════════════════════════════════════════════════
    with tab4:
        st.markdown("### 📚 Your Personalised Learning Path")
        st.markdown("<p style='color:var(--text-muted); font-size:0.95rem; margin-bottom:1.5rem;'>Generated using A* Search algorithm to find the optimal study sequence.</p>", unsafe_allow_html=True)

        learning_path = report.get('learning_path', [])

        # Render the optimal plan summary card first (if exists)
        summary_phase = None
        study_phases = []
        for phase in learning_path:
            if phase.get('phase') == 'optimal_plan':
                summary_phase = phase
            else:
                study_phases.append(phase)

        if summary_phase:
            st.markdown(f"""
                <div style="background:linear-gradient(135deg, rgba(139,92,246,0.1), rgba(102,126,234,0.1));
                            border:1px solid rgba(139,92,246,0.2); padding:1.5rem; border-radius:14px; margin-bottom:1.5rem;">
                    <div style="display:flex; align-items:center; gap:0.6rem; margin-bottom:0.6rem;">
                        <span style="font-size:1.3rem;">⚡</span>
                        <span style="color:#8b5cf6; font-weight:700; font-size:1.1rem;">Optimal Study Plan</span>
                    </div>
                    <p style="color:var(--text-main); margin:0; font-size:1rem; line-height:1.6;">
                        <strong>{_esc(summary_phase['goal'])}</strong> — Estimated <strong>{_esc(summary_phase['estimated_time'])}</strong> of focused study.
                    </p>
                </div>
            """, unsafe_allow_html=True)

        # ── Learning path timeline ──
        for idx, phase in enumerate(study_phases):
            p_color = _priority_color(phase.get('priority', 'medium'))
            p_icon = _priority_icon(phase.get('priority', 'medium'))
            is_last = idx == len(study_phases) - 1

            shadow_color = _hex_to_rgba(p_color, 0.25)
            badge_bg = _hex_to_rgba(p_color, 0.08)
            badge_border = _hex_to_rgba(p_color, 0.19)

            # Escape data to prevent HTML breakage
            phase_title = _html.escape(phase.get('phase', '').title())
            priority_title = _html.escape(phase.get('priority', '').title())
            focus_title = _html.escape(phase.get('focus', '').title())
            goal_text = _html.escape(phase.get('goal', ''))
            time_text = _html.escape(phase.get('estimated_time', ''))

            connector = ''
            if not is_last:
                connector = f'<div style="width:2px;flex:1;background:linear-gradient(to bottom,{p_color},var(--card-border));margin:4px 0;"></div>'

            # Build the card as a single compact HTML string (no HTML comments)
            card_html = (
                f'<div style="display:flex;gap:1rem;margin-bottom:0;">'
                f'<div style="display:flex;flex-direction:column;align-items:center;min-width:40px;">'
                f'<div style="width:36px;height:36px;border-radius:50%;background:{p_color};'
                f'display:flex;align-items:center;justify-content:center;font-size:0.85rem;color:white;font-weight:700;'
                f'box-shadow:0 4px 12px {shadow_color};">{idx + 1}</div>'
                f'{connector}'
                f'</div>'
                f'<div style="background:var(--card-bg);border:1px solid var(--card-border);border-left:4px solid {p_color};'
                f'padding:1.2rem 1.5rem;border-radius:12px;flex:1;margin-bottom:1rem;'
                f'box-shadow:0 2px 8px rgba(0,0,0,0.04);">'
                f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.5rem;">'
                f'<span style="color:var(--text-main);font-weight:600;font-size:1rem;">'
                f'{p_icon} {phase_title} Phase</span>'
                f'<span style="background:{badge_bg};color:{p_color};border:1px solid {badge_border};'
                f'padding:3px 12px;border-radius:20px;font-size:0.72rem;font-weight:600;text-transform:uppercase;">'
                f'{priority_title} Priority</span>'
                f'</div>'
                f'<div style="color:var(--text-main);font-size:0.95rem;margin-bottom:0.3rem;">'
                f'<strong>Focus:</strong> {focus_title}</div>'
                f'<div style="color:var(--text-main);font-size:0.95rem;margin-bottom:0.3rem;">'
                f'<strong>Goal:</strong> {goal_text}</div>'
                f'<div style="color:var(--text-muted);font-size:0.83rem;margin-top:0.5rem;">'
                f'⏱ Estimated time: {time_text}</div>'
                f'</div>'
                f'</div>'
            )
            st.markdown(card_html, unsafe_allow_html=True)

        # Resources section
        resources = report.get('resources', [])
        if resources:
            st.markdown("---")
            st.markdown("### 📖 Recommended Resources")
            res_cols = st.columns(min(len(resources), 3))
            for idx, r in enumerate(resources):
                col_idx = idx % min(len(resources), 3)
                type_icon = {"tutorial": "📘", "documentation": "📄", "practice": "🏋️", "interactive": "💻", "guide": "📋"}.get(r.get('type', '').lower(), "📘")
                with res_cols[col_idx]:
                    st.markdown(f"""
                        <a href="{_esc(r['url'])}" target="_blank" style="text-decoration:none; display:block;">
                            <div style="background:var(--card-bg); border:1px solid var(--card-border); padding:1rem; border-radius:12px;
                                        margin-bottom:0.8rem; transition:transform 0.2s, box-shadow 0.2s; cursor:pointer;"
                                 onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 6px 16px rgba(0,0,0,0.08)';"
                                 onmouseout="this.style.transform='none'; this.style.boxShadow='none';">
                                <div style="font-size:1.5rem; margin-bottom:0.5rem;">{type_icon}</div>
                                <div style="color:var(--primary-color); font-weight:600; font-size:0.9rem; margin-bottom:0.3rem;">{_esc(r['name'])}</div>
                                <div style="color:var(--text-muted); font-size:0.75rem; text-transform:uppercase; letter-spacing:0.5px;">{_esc(r.get('type','Resource').title())}</div>
                            </div>
                        </a>
                    """, unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════
    # TAB 5 — REPORT & EXPORT
    # ═══════════════════════════════════════════════════════
    with tab5:
        st.markdown("### 💡 Personalised Recommendations")
        for idx, rec_text in enumerate(report['recommendations'], 1):
            st.markdown(f"""
                <div style="background:var(--card-bg); border:1px solid var(--card-border); padding:1rem 1.25rem;
                            border-radius:10px; margin:0.5rem 0; display:flex; align-items:flex-start; gap:0.8rem;">
                    <div style="background:rgba(102,126,234,0.1); color:var(--primary-color); font-weight:700;
                                width:28px; height:28px; border-radius:50%; display:flex; align-items:center; justify-content:center;
                                font-size:0.8rem; flex-shrink:0; margin-top:2px;">{idx}</div>
                    <div style="color:var(--text-main); font-size:0.95rem; line-height:1.5;">{_esc(rec_text)}</div>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("### ⏭️ Immediate Next Steps")
        for step in report['next_steps']:
            st.markdown(f"""
                <div style="background:rgba(16,185,129,0.06); border:1px solid rgba(16,185,129,0.15); padding:0.9rem 1.25rem;
                            border-radius:10px; margin:0.4rem 0; display:flex; align-items:center; gap:0.6rem;">
                    <span style="color:#10b981; font-size:1.1rem;">→</span>
                    <span style="color:var(--text-main); font-size:0.95rem;">{_esc(step)}</span>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("### 📥 Export Report")
        col_dl1, col_dl2 = st.columns(2)
        with col_dl1:
            report_json = json.dumps(report, indent=2, default=str)
            st.download_button(
                label="📥 Download Full Report (JSON)",
                data=report_json,
                file_name=f"interview_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True,
                type="primary"
            )
        with col_dl2:
            if st.button("🔄 Start New Interview", use_container_width=True, type="secondary"):
                st.session_state.current_page = 'start_interview'
                st.rerun()
